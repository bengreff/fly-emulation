"""s16 octopamine-state arms (DECISIONS 21 Oct 02:28 pre-registration, 02:35 operational form).

`sets` expands data/params/octopamine_state.csv to the run overrides for one arm; `check` builds the network with them
and applies the per-cell bound (exit 1 on any breach, so the runner skips the arm).

    python scripts/probes/s16_oa.py sets OA4                       # prints: --set class:<c>|tonic_drive=<v> ...
    python scripts/probes/s16_oa.py check OA4 --out runs/s16/oa/check_OA4.json
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[2]
TABLE = REPO / "data" / "params" / "octopamine_state.csv"
REST_MAX, GAP_MIN = -45.0, 2.0      # n2_v_rest upper end; n2c_vth gap (DECISIONS 02:28)


def overrides(arm: str) -> dict[str, float]:
    t = pd.read_csv(TABLE, comment="#")
    t = t[t.arm == arm]
    return {f"class:{c}|tonic_drive": float(v) for c, v in zip(t["class"], t.value)}


def check(arm: str, profile: str, seed: int) -> dict:
    sys.path.insert(0, str(REPO / "src"))
    from flyemu import lif
    from flyemu.organism import Organism
    ov = overrides(arm)
    org = Organism(policy="minimal", profile=profile, min_synapses=5, overrides=ov, seed=seed)
    missing = sorted(k for k in ov if k not in org.reg._reqs)
    cls = lif.circuit_classes(org.conn)
    shift = pd.Series(cls).map({k.split("|")[0][6:]: v for k, v in ov.items()}).fillna(0.0).to_numpy(np.float32)
    net = org.net
    on = np.flatnonzero(shift != 0)
    v_rest, v_leak, v_th = net.v_rest[on], net.v_leak[on], net.v_th[on]
    spont1 = net.spont[on]                   # includes the class tonic drive
    d = shift[on]
    # 1: as registered, the rest parameter plus the shift
    r1 = v_rest + d
    b1 = (r1 > REST_MAX) | (v_th - r1 < GAP_MIN)
    # 2: the steady state without synaptic input, v_leak + spont, for cells below threshold at baseline
    s0 = v_leak + (spont1 - d)
    s1 = v_leak + spont1
    supra0 = s0 >= v_th
    b2 = ~supra0 & ((s1 > REST_MAX) | (v_th - s1 < GAP_MIN))
    pre = ~supra0 & (v_th - s0 < GAP_MIN)
    typ = org.conn.neurons.type.fillna("").to_numpy(str)[on]

    def rows(mask):
        return [{"cell": int(on[i]), "type": typ[i], "class": cls[on[i]], "v_rest": float(v_rest[i]),
                 "v_th": float(v_th[i]), "steady0": float(s0[i]), "steady1": float(s1[i])}
                for i in np.flatnonzero(mask)[:50]]
    gap1 = v_th - s1
    out = {
        "arm": arm, "profile": profile, "seed": seed, "keys": len(ov), "missing_keys": missing,
        "cells_shifted": int(on.size), "classes_shifted": int(np.unique(cls[on]).size),
        "bound1_breaches": int(b1.sum()), "bound2_breaches": int(b2.sum()),
        "bound2_breaches_already_within_2mv_at_baseline": int((b2 & pre).sum()),
        "suprathreshold_at_baseline": int(supra0.sum()),
        "suprathreshold_types": sorted(set(typ[supra0].tolist())),
        "v_rest_range": [float(v_rest.min()), float(v_rest.max())], "v_th_range": [float(v_th.min()), float(v_th.max())],
        "spont_baseline_range": [float((spont1 - d).min()), float((spont1 - d).max())],
        "min_gap_after_subthreshold": float(gap1[~supra0].min()) if (~supra0).any() else None,
        "breach_cells": rows(b1 | b2),
    }
    out["passes"] = not missing and out["bound1_breaches"] == 0 and out["bound2_breaches"] == 0
    return out


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("cmd", choices=("sets", "check"))
    ap.add_argument("arm")
    ap.add_argument("--profile", default="m10f0")
    ap.add_argument("--seed", type=int, default=12)
    ap.add_argument("--out", default="")
    a = ap.parse_args()
    if a.cmd == "sets":
        print(" ".join(f"--set {k}={v:g}" for k, v in overrides(a.arm).items()))
        return
    res = check(a.arm, a.profile, a.seed)
    if a.out:
        Path(a.out).write_text(json.dumps(res, indent=1))
    print(json.dumps({k: v for k, v in res.items() if k != "breach_cells"}, indent=1))
    sys.exit(0 if res["passes"] else 1)


if __name__ == "__main__":
    main()
