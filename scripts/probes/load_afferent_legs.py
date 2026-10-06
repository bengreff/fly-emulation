"""Why the lh load afferents are silent (F-STAND-3): per leg, the strain signal the campaniform
channel reads, and per load afferent its type, drive, LIF constants, recurrent input and rate.
Dead fly (no motor output) dropped from the standing placement, as in standing_rest.py --dead.

    uv run python scripts/probes/load_afferent_legs.py [--ms 300 --seed 12]
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "src"))
LEGS = ("lf", "lm", "lh", "rf", "rm", "rh")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--ms", type=float, default=300.0)
    ap.add_argument("--seed", type=int, default=12)
    ap.add_argument("--out", default=str(REPO / "runs" / "s12" / "stand3"))
    a = ap.parse_args()
    from flyemu.organism import Organism
    from flyemu.profiles import WORKING_PROFILE
    from flyemu.deadfly import place_standing
    org = Organism(policy="minimal", profile=WORKING_PROFILE, min_synapses=5, seed=a.seed,
                   overrides={"motor_unit:all|force_per_spike": 10.0})
    place_standing(org.body)
    aff, n = org.aff, org.conn.neurons
    silent = np.zeros(0, dtype=np.int64)
    steps = int(a.ms / org.timestep_ms)
    strain = np.zeros((steps, len(LEGS)))
    rows = {L: np.asarray(aff.rows[(aff.leg == L) & (aff.channel == "load")]) for L in LEGS}
    allrows = np.concatenate([rows[L] for L in LEGS])
    drive = np.zeros((steps, len(allrows)))
    vm = np.zeros((steps, len(allrows)))
    counts = np.zeros(org.conn.n)
    for s in range(steps):
        obs = org.body.observe()
        seg = np.linalg.norm(obs["segment_load"][:, 3:], axis=-1)
        strain[s] = [seg[aff.load_bodies[L]].sum() if L in aff.load_bodies else np.nan for L in LEGS]
        d = org.sense(s, obs)
        drive[s] = d[allrows]
        spk = org.net.step(external_mv=d)
        counts[spk] += 1
        vm[s] = np.asarray(org.net.v)[allrows]
        org.motor_step(silent)
    p = org.net.params

    def arr(x):
        return np.broadcast_to(np.asarray(x, float), (org.conn.n,))
    sel = (aff.channel == "load")
    out = dict(seed=a.seed, ms=a.ms, profile=WORKING_PROFILE,
               strain_mean_by_leg={L: round(float(strain[:, i].mean()), 3) for i, L in enumerate(LEGS)},
               strain_end_by_leg={L: round(float(strain[-1, i]), 3) for i, L in enumerate(LEGS)},
               load_bodies={L: int(len(aff.load_bodies.get(L, []))) for L in LEGS},
               gain_mv=sorted(set(np.round(aff.gain_mv[sel], 3).tolist())),
               baseline_mv=sorted(set(np.round(aff.baseline_mv[sel], 3).tolist())),
               cells=[])
    k = 0
    for L in LEGS:
        for r in rows[L]:
            out["cells"].append(dict(
                leg=L, row=int(r), bodyId=int(n.bodyId.iloc[r]), type=str(n.type.iloc[r]),
                subclass=str(n.subclass.iloc[r]), drive_mean_mv=round(float(drive[:, k].mean()), 2),
                v_mean_minus_rest=round(float(np.nanmean(vm[:, k]) - arr(p.v_rest)[r]), 2),
                th_minus_rest=round(float((arr(p.v_th) - arr(p.v_rest))[r]), 2),
                tau_m=round(float(arr(p.tau_m)[r]), 2), hz=round(float(counts[r] / (a.ms / 1e3)), 1)))
            k += 1
    Path(a.out).mkdir(parents=True, exist_ok=True)
    (Path(a.out) / f"load_afferent_legs_s{a.seed}.json").write_text(json.dumps(out, indent=1))
    print(json.dumps({k: v for k, v in out.items() if k != "cells"}))
    for c in out["cells"]:
        print(c)


if __name__ == "__main__":
    main()
