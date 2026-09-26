"""Open-loop reflex arc: drive one leg's flexion-tuned claw (or all FeCO) afferents
with Poisson kicks and read that leg's tibia MN pools and first-order targets.

    uv run python scripts/probes/reflex_arc.py [--leg lm] [--hz 40] [--scale 1.0]
"""
import argparse
import json
import sys

import numpy as np
import pandas as pd

sys.path.insert(0, "src")
from flyemu.organism import Organism  # noqa: E402
from flyemu.profiles import WORKING_PROFILE  # noqa: E402


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--leg", default="lm")
    ap.add_argument("--hz", type=float, default=40.0)
    ap.add_argument("--ms", type=float, default=500.0)
    ap.add_argument("--set", action="append", default=[])
    ap.add_argument("--which", default="claw_flexion")
    a = ap.parse_args()
    ov = {k: float(v) for k, v in (s.split("=") for s in a.set)}
    org = Organism(policy="minimal", profile=WORKING_PROFILE, min_synapses=5, overrides=ov)
    aff, n = org.aff, org.conn.neurons
    tab = pd.read_csv("data/params/proprio_assignment.csv", comment="#").set_index("type")
    typ = n.type.fillna("").to_numpy()[aff.rows]
    dirn = pd.Series(typ).map(tab.direction).fillna("").to_numpy()
    if a.which == "claw_flexion":
        sel = (aff.leg == a.leg) & (aff.subtype == "claw") & (dirn == "flexion")
    else:
        sel = (aff.leg == a.leg) & (aff.subtype != "")
    stim = aff.rows[sel]
    side = {"l": "L", "r": "R"}[a.leg[0]]; nm = {"f": "T1", "m": "T2", "h": "T3"}[a.leg[1]]
    t = n.type.fillna("")
    pools = {k: np.flatnonzero((t.str.startswith(k) & (n.somaNeuromere == nm) & (n.somaSide == side)).to_numpy())
             for k in ["Ti flexor", "Acc. ti flexor", "Ti extensor"]}
    rng = np.random.default_rng(0)
    dt = org.timestep_ms
    cnt = np.zeros(org.conn.n)
    for s in range(int(a.ms / dt)):
        fire = stim[rng.random(stim.size) < a.hz * dt / 1000]
        sp = org.net.step(kick=(fire, org.kick_mv))
        cnt[sp] += 1
    hz = cnt / (a.ms / 1000)
    # first-order targets of the stimulated afferents
    first = pd.Series(hz).groupby(t.to_numpy()).mean()
    active = (hz > 1)
    df = pd.DataFrame({"type": t, "hz": hz, "active": active})
    top = df[active & ~np.isin(np.arange(len(df)), stim)].groupby("type").hz.agg(["size", "mean"]).sort_values("size", ascending=False).head(12)
    print(json.dumps({"leg": a.leg, "stimulated": int(stim.size), "stim_hz_obs": round(float(hz[stim].mean()), 1),
                      "pools_hz": {k: round(float(hz[v].mean()), 2) for k, v in pools.items()},
                      "n_active_other": int(active.sum() - (hz[stim] > 1).sum()), "overrides": ov}))
    print(top.to_string())


if __name__ == "__main__":
    main()
