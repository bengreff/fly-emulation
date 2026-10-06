"""Firing rate against step drive for one unconnected central cell under a profile's rung-1 channels (diagnostic).

Built for the leg sugar route (DECISIONS 23:12): every cell on it carries the class-prior channel set
fitted on slow leg MNs (mRNA factor 1). This simulates single cells with a central cell's LIF constants
(default: Roundup under m9r, tau_m 20 ms, rest -52 mV, threshold gap 7 mV, t_ref 2.2 ms) and the profile's
gbar values at factor 1, with any channel set to 0, for 1 s steps of constant drive (mV = I x Rin;
derived). Reports the mean rate over the step, the first 100 ms and the last 100 ms. No noise, no synapses.

    uv run python scripts/probes/central_fi.py --profile m9r --drives 0,2,4,8,12,16,24,32 \
        --arms all,BK,Kv2,SK,AHP,A,none --png docs/media/s12_central_fi.png
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))
from flyemu import channels, lif, profiles  # noqa: E402
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
    a = ap.parse_args()
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
