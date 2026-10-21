"""s14 arm B calibration: after-depolarisation (ADP) of the rhythm-core E1/E2 cells, single cells, no synapses.

DIAGNOSTIC. No insect central-interneuron ADP amplitude or decay has been measured (docs/research/s14_burst_ranges.md).
What is measured is the burst a rhythmic insect interneuron makes: 2-6 spikes at 160-380 Hz (cricket singing-CPG
interneurons, Schoeneich et al. 2012, Brain and Behavior, PMC3500458, full text; 2-6 spikes per injected
depolarisation). So the two
ADP values (`cell_type:core_rhythm_exc|adp_mv`, `|adp_tau_ms`) are chosen here, on single cells, before any network run,
by a rule written down first (DECISIONS 20 Oct, s14 pre-registration):

  - protocol: each of the 12 E1 (IN17A001) and E2 (INXXX466) cells, with its own model constants and rung-1 channels
    from the profile (m10f0), unconnected, no noise; a +10 mV kick at t0 fires one spike; count the spikes that follow;
  - admissible (a, tau): median over cells of spikes per burst (trigger included) in [2, 6], median intra-burst rate
    (spikes - 1) / (last - first spike) in [160, 380] Hz, and the burst ends: no spike 60-150 ms after the trigger in
    any cell, and no spike before the trigger (rest stays silent);
  - selected: the admissible pair whose median burst is closest to 4 spikes; ties go to the smaller a, then smaller tau.

Arm B' (persistent inward current) is the same protocol with adp 0 and the cells' NaP density x `--nap-scales`;
its selected scale is the admissible one closest to 4 spikes, ties to the smaller scale.

    uv run python scripts/probes/s14_burst_calib.py --out runs/s14/calib/adp_grid.json
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "src"))
from flyemu import channels, connectome, lif, percell, profiles  # noqa: E402
from flyemu.connectome import Connectome  # noqa: E402
from flyemu.registry import Policy, Registry  # noqa: E402

DT = 0.1
T0, T_END = 200.0, 400.0
KICK_MV = 10.0


def core_constants(profile: str) -> dict:
    """The model's per-cell constants for the E1/E2 cells, as the profile builds them."""
    reg = Registry(Policy.MINIMAL)
    profiles.apply(reg, profile)
    conn = connectome.build(reg, min_synapses=profiles.WORKING_MIN_SYNAPSES)
    p = lif.default_params(reg, conn, timestep_ms=DT)
    idx = np.flatnonzero(percell.core_rhythm_mask(conn))
    b = lambda x: np.broadcast_to(np.asarray(x, np.float32), (conn.n,))[idx].astype(float).tolist()
    c = {"bodyId": conn.neurons.bodyId.to_numpy()[idx].tolist(), "type": conn.neurons.type.to_numpy()[idx].tolist(),
         "tau_m": b(p.tau_m), "v_rest": b(p.v_rest), "v_th": b(p.v_th), "v_reset": b(p.v_reset), "t_ref": b(p.t_ref),
         "spont": b(p.spont_mv), "adapt_mv": b(p.adapt_mv), "tau_adapt": b(p.tau_adapt)}
    ich = p.intrinsic
    c["g"] = {k: ich.g[k][idx].astype(float).tolist() for k in channels.CHANNELS}
    c["ca_per_spike"] = ich.ca_per_spike[idx].astype(float).tolist()
    c["ca_tau"] = float(ich.ca_tau)
    return c


def run_grid(c: dict, pairs: list[tuple[float, float, float]]) -> list[dict]:
    """All (adp_mv, adp_tau_ms, nap_scale) triples x 12 cells in one unconnected network."""
    k = len(c["bodyId"])
    n = k * len(pairs)
    rep = lambda key: np.tile(np.asarray(c[key], np.float32), len(pairs))
    nrn = pd.DataFrame({"bodyId": np.tile(c["bodyId"], len(pairs)), "type": np.tile(c["type"], len(pairs)),
                        "predictedNt": "acetylcholine", "superclass": "x", "class": "x"})
    conn = Connectome(nrn, np.zeros(n + 1, np.int64), np.zeros(0, np.int32), np.zeros(0, np.float32),
                      np.zeros(n, np.float32), np.zeros(0, np.float32))
    g = {ch: np.tile(np.asarray(v, np.float32), len(pairs)) for ch, v in c["g"].items()}
    g["NaP"] = g["NaP"] * np.repeat(np.array([s for *_, s in pairs], np.float32), k)
    ich = channels.Intrinsic(g=g,
                             ca_per_spike=rep("ca_per_spike"), dt=DT, ca_tau=c["ca_tau"])
    adp = np.repeat(np.array([a for a, _, _ in pairs], np.float32), k)
    tau = np.repeat(np.array([t for _, t, _ in pairs], np.float32), k)
    p = lif.LIFParams(rep("tau_m"), rep("v_rest"), rep("v_th"), rep("v_reset"), rep("t_ref"), 5.0,
                      np.ones(n, np.int64), 0.0, True, graded=np.zeros(n, bool), intrinsic=ich,
                      spont_mv=rep("spont"), adapt_mv=rep("adapt_mv"), tau_adapt=rep("tau_adapt"),
                      adp_mv=adp if adp.any() else None, tau_adp=tau)
    net = lif.Network(conn, p, DT)
    times = [[] for _ in range(n)]
    allc = np.arange(n)
    for s in range(int(T_END / DT)):
        t = s * DT
        sp = net.step(kick=(allc, KICK_MV) if s == int(T0 / DT) else None)
        for i in sp:
            times[i].append(t)
    out = []
    for j, (a, t, sc) in enumerate(pairs):
        cells = []
        for i in range(j * k, (j + 1) * k):
            ts = np.array(times[i])
            pre = int((ts < T0).sum())
            post = ts[ts >= T0]
            burst = post[post < T0 + 60.0]
            late = int(((post >= T0 + 60.0) & (post < T0 + 150.0)).sum())
            rate = (len(burst) - 1) / ((burst[-1] - burst[0]) / 1000.0) if len(burst) > 1 else 0.0
            cells.append({"pre": pre, "burst": int(len(burst)), "rate_hz": float(rate), "late": late,
                          "dur_ms": float(burst[-1] - burst[0]) if len(burst) > 1 else 0.0})
        nb = np.median([x["burst"] for x in cells])
        rr = np.median([x["rate_hz"] for x in cells])
        ends = all(x["late"] == 0 for x in cells) and all(x["pre"] == 0 for x in cells)
        adm = bool(2 <= nb <= 6 and 160 <= rr <= 380 and ends)
        out.append({"adp_mv": a, "adp_tau_ms": t, "nap_scale": sc, "median_burst": float(nb), "median_rate_hz": float(rr),
                    "ends": ends, "admissible": adm, "by_type": {
                        ty: {"burst": [x["burst"] for x, tt in zip(cells, c["type"]) if tt == ty],
                             "rate_hz": [round(x["rate_hz"]) for x, tt in zip(cells, c["type"]) if tt == ty]}
                        for ty in sorted(set(c["type"]))}})
    return out


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--profile", default="m10f0")
    ap.add_argument("--amps", default="0,2,4,6,8,10,12,14,16,20,24")
    ap.add_argument("--taus", default="5,10,20,40")
    ap.add_argument("--nap-scales", default="1.5,2,3,4,6,8,10")
    ap.add_argument("--constants", default=str(REPO / "runs/s14/calib/core_constants.json"))
    ap.add_argument("--out", default=str(REPO / "runs/s14/calib/adp_grid.json"))
    a = ap.parse_args()
    cp = Path(a.constants)
    if cp.exists():
        c = json.loads(cp.read_text())
    else:
        c = core_constants(a.profile)
        cp.parent.mkdir(parents=True, exist_ok=True)
        cp.write_text(json.dumps(c, indent=1))
    fl = lambda s: [float(x) for x in s.split(",")]
    adp_pairs = [(x, t, 1.0) for x in fl(a.amps) for t in fl(a.taus)]
    nap_pairs = [(0.0, 20.0, s) for s in fl(a.nap_scales)]
    grid = run_grid(c, adp_pairs + nap_pairs)
    adm = [g for g in grid if g["admissible"] and g["nap_scale"] == 1.0 and g["adp_mv"] > 0]
    sel = min(adm, key=lambda g: (abs(g["median_burst"] - 4), g["adp_mv"], g["adp_tau_ms"])) if adm else None
    adm_n = [g for g in grid if g["admissible"] and g["adp_mv"] == 0]
    sel_n = min(adm_n, key=lambda g: (abs(g["median_burst"] - 4), g["nap_scale"])) if adm_n else None
    for g in grid:
        print(f"a {g['adp_mv']:5.1f} tau {g['adp_tau_ms']:4.0f} nap x{g['nap_scale']:4.1f}: burst "
              f"{g['median_burst']:4.1f} rate {g['median_rate_hz']:5.0f} Hz ends {g['ends']} adm {g['admissible']}")
    print("selected B:", None if sel is None else (sel["adp_mv"], sel["adp_tau_ms"]),
          " selected B':", None if sel_n is None else sel_n["nap_scale"])
    Path(a.out).parent.mkdir(parents=True, exist_ok=True)
    Path(a.out).write_text(json.dumps({"profile": a.profile, "kick_mv": KICK_MV, "grid": grid, "selected": sel, "selected_nap": sel_n,
                                       "constants_summary": {k: c[k] for k in ("type", "tau_m", "v_rest", "v_th",
                                                                               "t_ref", "spont")}}, indent=1))


if __name__ == "__main__":
    main()
