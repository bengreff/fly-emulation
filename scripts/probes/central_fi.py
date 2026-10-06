"""Firing rate against step drive for one unconnected central cell under a profile's rung-1 channels (diagnostic).

Built for the leg sugar route (DECISIONS 23:12): every cell on it carries the class-prior channel set
fitted on slow leg MNs (mRNA factor 1). This simulates single cells with a central cell's LIF constants
(default: Roundup under m9r, tau_m 20 ms, rest -52 mV, threshold gap 7 mV, t_ref 2.2 ms) and the profile's
gbar values at factor 1, with any channel set to 0, for 1 s steps of constant drive (mV = I x Rin;
derived). Reports the mean rate over the step, the first 100 ms and the last 100 ms. No noise, no synapses.

--cell-type T (s12, DECISIONS 23:56) takes T's own constants from the model build instead and runs a
published current-step protocol: currents (pA) map to drive as I x Rin x k (soma-to-initiation-zone
transfer), and each arm is calibrated so its passive deflection at --calib-pa equals that mapping.

    uv run python scripts/probes/central_fi.py --profile m9r --drives 0,2,4,8,12,16,24,32 \
        --arms all,BK,Kv2,SK,AHP,A,none --png docs/media/s12_central_fi.png
    uv run python scripts/probes/central_fi.py --profile m9c --cell-type MBON14 --arms all,BK,none \
        --out runs/s12/ffi/mbon14_fi_m9c.json --png docs/media/s12_mbon14_fi.png
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))
from flyemu import channels, connectome, lif, profiles  # noqa: E402
from flyemu.connectome import Connectome  # noqa: E402
from flyemu.registry import Policy, Registry  # noqa: E402

DT = 0.1
GROUPS = {"all": [], "none": list(channels.CHANNELS), "AHP": ["BK", "Kv2", "SK"], "subK": ["A", "M"]}


def fake_conn(n: int) -> Connectome:
    nrn = pd.DataFrame({"bodyId": -1 - np.arange(n), "type": "__central_probe__",
                        "predictedNt": "acetylcholine", "superclass": "x", "class": "x"})
    return Connectome(nrn, np.zeros(n + 1, np.int64), np.zeros(0, np.int32), np.zeros(0, np.float32),
                      np.zeros(n, np.float32), np.zeros(0, np.float32))


def run(profile: str, off: list[str], drives: np.ndarray, a) -> dict:
    reg = Registry(Policy.MINIMAL)
    reg.overrides["cell_type:all|intrinsic_channels"] = 0.0 if off == list(channels.CHANNELS) else 1.0
    for c in off:
        reg.overrides[f"channel:{c}|gbar"] = 0.0
    profiles.apply(reg, profile)
    n = len(drives)
    conn = fake_conn(n)
    ich = channels.from_registry(reg, conn, timestep_ms=DT)
    f = lambda v: np.full(n, v, np.float32)
    p = lif.LIFParams(f(a.tau_m), f(a.v_rest), f(a.v_rest + a.gap), f(a.v_rest), f(a.t_ref), 5.0,
                      np.ones(n, np.int64), 0.0, True, graded=np.zeros(n, bool), intrinsic=ich)
    net = lif.Network(conn, p, DT)
    drive = drives.astype(np.float32)
    cnt = {k: np.zeros(n) for k in ("on", "early", "late")}
    for s in range(int(1500 / DT)):
        t = s * DT
        sp = net.step(external_mv=np.where(500 <= t < 1500, drive, 0.0).astype(np.float32))
        if sp.size:
            if 500 <= t < 1500: cnt["on"][sp] += 1
            if 500 <= t < 600: cnt["early"][sp] += 1
            if 1400 <= t < 1500: cnt["late"][sp] += 1
    g = {c: round(float(ich.g[c][0]), 4) for c in channels.CHANNELS} if ich is not None else {}
    return {"g": g, "on_hz": cnt["on"].tolist(), "early_hz": (cnt["early"] / 0.1).tolist(),
            "late_hz": (cnt["late"] / 0.1).tolist()}


# Hafez et al. 2023 eLife 12:e77578, Fig. 1 supp. 1C (MBON-alpha3, 400 ms steps): figure estimate, my
# reading by eye, about +-1 Hz and +-1 pA. Points where the plotted line changes slope.
HAFEZ_FI = {"cell 1": [(2, 0), (6, 5), (8, 5), (12, 10), (14, 10), (18, 15), (24, 15), (26, 17.5), (30, 17.5), (32, 20)],
            "cell 2": [(-6, 0), (0, 7.5), (2, 12.5), (8, 20), (10, 25), (12, 25), (16, 35), (20, 35), (24, 40),
                       (26, 45), (28, 45), (32, 50)],
            "cell 3": [(-2, 0), (6, 10), (8, 15), (12, 20), (16, 20), (20, 25), (24, 25), (26, 27.5), (28, 27.5),
                       (30, 30), (32, 30)]}


def cell_constants(profile: str, cell_type: str) -> tuple[dict, pd.DataFrame]:
    """The model's own per-cell constants for one type (profile as built)."""
    reg = Registry(Policy.MINIMAL)
    profiles.apply(reg, profile)
    conn = connectome.build(reg, min_synapses=profiles.WORKING_MIN_SYNAPSES)
    p = lif.default_params(reg, conn, timestep_ms=DT)
    idx = np.flatnonzero(conn.neurons.type.fillna("").to_numpy() == cell_type)
    assert len(idx), cell_type
    b = lambda x: np.broadcast_to(np.asarray(x, np.float32), (conn.n,))[idx].astype(float)
    c = {"tau_m": b(p.tau_m), "v_rest": b(p.v_rest), "v_th": b(p.v_th), "v_reset": b(p.v_reset),
         "t_ref": b(p.t_ref), "spont": b(p.spont_mv), "adapt_mv": b(p.adapt_mv), "tau_adapt": b(p.tau_adapt), "noise_mv": float(p.noise_mv)}
    if p.intrinsic is not None:
        c["g"] = {k: p.intrinsic.g[k][idx].astype(float).tolist() for k in channels.CHANNELS}
        c["channel_source"] = p.intrinsic.source[idx].tolist() if p.intrinsic.source is not None else None
    return c, conn.neurons.iloc[idx][["bodyId", "type"]].reset_index(drop=True)


def run_protocol(profile: str, off: list[str], c: dict, cells: pd.DataFrame, k: int, a) -> dict:
    """One model cell (row k of `cells`) under the current-step protocol, calibrated passively."""
    reg = Registry(Policy.MINIMAL)
    reg.overrides["cell_type:all|intrinsic_channels"] = 0.0 if off == list(channels.CHANNELS) else 1.0
    for ch in off:
        reg.overrides[f"channel:{ch}|gbar"] = 0.0
    profiles.apply(reg, profile)
    cur = np.array([float(x) for x in a.currents_pa.split(",")])
    n = len(cur) + 1                      # last cell: passive calibration at a fixed drive
    nrn = pd.DataFrame({"bodyId": np.full(n, cells.bodyId[k]), "type": cells.type[k],
                        "predictedNt": "acetylcholine", "superclass": "x", "class": "x"})
    conn = Connectome(nrn, np.zeros(n + 1, np.int64), np.zeros(0, np.int32), np.zeros(0, np.float32),
                      np.zeros(n, np.float32), np.zeros(0, np.float32))
    ich = channels.from_registry(reg, conn, timestep_ms=DT)
    f = lambda key: np.full(n, c[key][k], np.float32)
    p = lif.LIFParams(f("tau_m"), f("v_rest"), f("v_th"), f("v_reset"), f("t_ref"), 5.0,
                      np.ones(n, np.int64), 0.0, True, graded=np.zeros(n, bool), intrinsic=ich,
                      spont_mv=f("spont"), adapt_mv=f("adapt_mv"), tau_adapt=f("tau_adapt"))
    calib_mv = -5.0
    # pass 1: the passive deflection per mV of drive (model "Rin" in leak units) at rest, this arm
    net = lif.Network(conn, p, DT)
    t0, t1 = 500.0, 500.0 + a.step_ms
    for s in range(int(t1 / DT)):
        net.step(external_mv=np.full(n, calib_mv if s * DT >= t0 else 0.0, np.float32))
        if s == int(t0 / DT) - 1:
            v0 = float(net.v[-1])
    rin_rel = (float(net.v[-1]) - v0) / calib_mv
    mv_per_pa = a.rin_gohm * a.k_transfer / rin_rel        # drive per pA so that dV(I) = I x Rin x k
    drive = np.append(cur * mv_per_pa, 0.0).astype(np.float32)
    net = lif.Network(conn, p, DT)
    cnt = np.zeros(n); early = np.zeros(n); late = np.zeros(n); pre = np.zeros(n)
    for s in range(int(t1 / DT)):
        t = s * DT
        sp = net.step(external_mv=np.where(t >= t0, drive, 0.0).astype(np.float32))
        if sp.size:
            if t >= t0: cnt[sp] += 1
            if t0 <= t < t0 + 100: early[sp] += 1
            if t1 - 100 <= t: late[sp] += 1
            if t0 - 400 <= t < t0: pre[sp] += 1
    hz = cnt[:-1] / (a.step_ms / 1000.0)
    on = np.flatnonzero(hz > 0)
    onset = float(cur[on[0]]) if len(on) else None
    i_max = int(np.argmax(cur))
    slope = (hz[i_max] / (cur[i_max] - onset)) if onset is not None and cur[i_max] > onset else 0.0
    return {"cell": int(cells.bodyId[k]), "rin_rel": round(rin_rel, 4), "mv_per_pa": round(mv_per_pa, 4),
            "rest_hz": float(pre[-1] / 0.4), "currents_pa": cur.tolist(), "hz": hz.round(2).tolist(),
            "early_hz": (early[:-1] / 0.1).tolist(), "late_hz": (late[:-1] / 0.1).tolist(),
            "onset_pa": onset, "hz_at_max": float(hz[i_max]), "slope_hz_per_pa": round(float(slope), 3)}


def main_cell(a) -> None:
    c, cells = cell_constants(a.profile, a.cell_type)
    print(a.cell_type, "cells", cells.bodyId.tolist(), {kk: np.round(v, 3).tolist() for kk, v in c.items()
                                                       if kk not in ("g", "channel_source", "noise_mv")},
          "noise", c["noise_mv"], "channel source", c.get("channel_source"))
    res = {"profile": a.profile, "cell_type": a.cell_type, "constants": {kk: (v.tolist() if isinstance(v, np.ndarray)
           else v) for kk, v in c.items()}, "rin_gohm": a.rin_gohm, "k_transfer": a.k_transfer,
           "step_ms": a.step_ms, "measured_fi": HAFEZ_FI, "arms": {}}
    for arm in a.arms.split(","):
        off = GROUPS.get(arm, [arm])
        res["arms"][arm] = [run_protocol(a.profile, off, c, cells, k, a) for k in range(len(cells))]
        for r in res["arms"][arm]:
            print(f"{arm:>5} cell {r['cell']}: Rin_rel {r['rin_rel']:.3f}, {r['mv_per_pa']:.3f} mV/pA, rest "
                  f"{r['rest_hz']:.1f} Hz, onset {r['onset_pa']} pA, {r['hz_at_max']:.1f} Hz at max, slope "
                  f"{r['slope_hz_per_pa']:.2f} Hz/pA, late/early at max {r['late_hz'][-1]:.0f}/{r['early_hz'][-1]:.0f}")
    if a.out:
        Path(a.out).parent.mkdir(parents=True, exist_ok=True)
        Path(a.out).write_text(json.dumps(res, indent=1))
    if a.png:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
        fig, ax = plt.subplots(figsize=(6.5, 4.5))
        for name, pts in HAFEZ_FI.items():
            x, y = zip(*pts)
            ax.plot(x, y, "k-", lw=1.2, alpha=0.6, label="Hafez 2023 (figure estimate)" if name == "cell 1" else None)
        cols = {"all": "C0", "BK": "C3", "none": "C2"}
        for arm, rows in res["arms"].items():
            lab = {"all": f"{a.profile} as is", "none": "rung 1 off"}.get(arm, f"{arm} off")
            for j, r in enumerate(rows):
                ax.plot(r["currents_pa"], r["hz"], "o-", ms=2.5, color=cols.get(arm), alpha=0.8,
                        label=lab if j == 0 else None)
        ax.set(xlabel="injected current (pA)", ylabel=f"mean rate over {a.step_ms:.0f} ms step (Hz)",
               title=f"{a.cell_type} (MBON-α3): model vs recording; {a.rin_gohm} GΩ × k {a.k_transfer}")
        ax.legend(fontsize=7)
        fig.tight_layout()
        fig.savefig(a.png, dpi=130)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--profile", default=profiles.WORKING_PROFILE)
    ap.add_argument("--drives", default="0,2,4,6,8,10,12,16,20,24,32,40")
    ap.add_argument("--arms", default="all,BK,Kv2,SK,AHP,A,M,h,none",
                    help="all = profile as is; a channel name = that channel off; AHP, subK = groups off; none = rung 1 off")
    ap.add_argument("--tau-m", type=float, default=20.0)
    ap.add_argument("--v-rest", type=float, default=-52.0)
    ap.add_argument("--gap", type=float, default=7.0)
    ap.add_argument("--t-ref", type=float, default=2.2)
    ap.add_argument("--out", default="")
    ap.add_argument("--png", default="")
    ap.add_argument("--cell-type", default="", help="use this type's own model constants and a current-step protocol")
    ap.add_argument("--currents-pa", default=",".join(str(x) for x in range(-26, 34, 2)))
    ap.add_argument("--step-ms", type=float, default=400.0)
    ap.add_argument("--rin-gohm", type=float, default=1.7, help="measured input resistance (GOhm)")
    ap.add_argument("--k-transfer", type=float, default=0.55, help="soma-to-initiation-zone steady transfer")
    a = ap.parse_args()
    if a.cell_type:
        main_cell(a)
        return
    drives = np.array([float(x) for x in a.drives.split(",")])
    res = {"profile": a.profile, "cell": {"tau_m": a.tau_m, "v_rest": a.v_rest, "gap": a.gap, "t_ref": a.t_ref},
           "drives_mV": drives.tolist(), "arms": {}}
    for arm in a.arms.split(","):
        off = GROUPS.get(arm, [arm])
        res["arms"][arm] = run(a.profile, off, drives, a)
        r = res["arms"][arm]
        print(f"{arm:>5} " + " ".join(f"{d:g}:{h:.0f}" for d, h in zip(drives, r["on_hz"]))
              + "   late/early at max " + f"{r['late_hz'][-1]:.0f}/{r['early_hz'][-1]:.0f}")
    if a.out:
        Path(a.out).write_text(json.dumps(res, indent=1))
    if a.png:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
        fig, ax = plt.subplots(1, 2, figsize=(10, 4))
        for arm, r in res["arms"].items():
            lab = {"all": f"{a.profile} as is", "none": "rung 1 off"}.get(arm, f"{arm} off")
            ax[0].plot(drives, r["on_hz"], "o-", ms=3, label=lab)
            ax[1].plot(drives, r["late_hz"], "o-", ms=3, label=lab)
        ax[0].set(xlabel="step drive (mV = I x Rin)", ylabel="mean rate over 1 s step (Hz)",
                  title=f"single central cell, {a.profile} class-prior channels")
        ax[1].set(xlabel="step drive (mV)", ylabel="rate in last 100 ms (Hz)", title="adapted rate")
        ax[0].legend(fontsize=7)
        fig.tight_layout()
        fig.savefig(a.png, dpi=130)


if __name__ == "__main__":
    main()
