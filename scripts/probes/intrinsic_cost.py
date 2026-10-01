"""Whole-CNS cost and state of fidelity rung 1 (intrinsic conductances), session 11.

Builds the working organism with and without `cell_type:all|intrinsic_channels`,
steps the brain only (no body) for --steps under the same declared stimulus
(sugar GRNs LB3b/LB3c kicked at 100 Hz Poisson, fixed draw) and reports wall time per
step, spikes per superclass, cells whose resting intrinsic conductance was
capped, and density sources (type mRNA / hemilineage mRNA / prior).

    uv run python scripts/probes/intrinsic_cost.py [--steps 3000] [--out X.json]
"""
import argparse
import json
import sys
import time

import numpy as np

sys.path.insert(0, "src")
from flyemu.organism import Organism  # noqa: E402
from flyemu.profiles import WORKING_PROFILE  # noqa: E402


def run(on: bool, steps: int, seed: int):
    org = Organism(policy="minimal", profile=WORKING_PROFILE, min_synapses=5, seed=seed,
                   overrides={"cell_type:all|intrinsic_channels": float(on)})
    net, n = org.net, org.conn.n
    typ = org.conn.neurons.type.fillna("").to_numpy()
    sugar = np.flatnonzero(np.isin(typ, ["LB3b", "LB3c"]))   # sugar GRNs as in assay_pathways sugar_mn9
    rng = np.random.default_rng(seed)
    sc = org.conn.neurons.superclass.fillna("none").to_numpy()
    cnt = np.zeros(n, np.int64)
    t0 = time.perf_counter()
    for _ in range(steps):
        k = sugar[rng.random(sugar.size) < 100 * net.timestep_ms / 1000]
        sp = net.step(kick=(k, 68.75) if k.size else None)
        cnt[sp] += 1
    wall = time.perf_counter() - t0
    out = {"on": on, "steps": steps, "ms_per_step": round(1000 * wall / steps, 3), "n_sugar": int(sugar.size),
           "spikes_by_superclass": {s: int(cnt[sc == s].sum()) for s in np.unique(sc)},
           "cells_over_50hz": int((cnt / (steps * net.timestep_ms / 1000) > 50).sum())}
    if on and net.ich is not None:
        out["n_capped"] = net.ich.n_capped
        out["source_counts"] = {k: int(v) for k, v in zip(("prior", "hemilineage", "type"),
                                                           np.bincount(net.ich.source, minlength=3))}
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--steps", type=int, default=3000)
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--out", default="")
    a = ap.parse_args()
    res = [run(False, a.steps, a.seed), run(True, a.steps, a.seed)]
    res.append({"cost_ratio": round(res[1]["ms_per_step"] / res[0]["ms_per_step"], 2)})
    print(json.dumps(res, indent=1))
    if a.out:
        with open(a.out, "w") as f:
            json.dump(res, f, indent=1)


if __name__ == "__main__":
    main()
