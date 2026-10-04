"""Session 12 B (F-MUSCLE-MH-1 open item): does TTMn reach the mid-leg CTr Hill
muscle as well as the B15 TTM twitch hook? If so the TTM is counted twice.

Builds the working organism and reports, for each TTMn row, the Hill muscle it is
joined to and its share of that muscle's activation weight (force-weighted mean).

    uv run python scripts/probes/ttm_double_count.py [--profile m9w]
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "src"))
from flyemu.organism import Organism  # noqa: E402
from flyemu.profiles import WORKING_PROFILE  # noqa: E402


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--profile", default=WORKING_PROFILE)
    ap.add_argument("--set", action="append", default=[])
    a = ap.parse_args()
    ov = {k: float(v) for k, v in (s.split("=") for s in a.set)}
    org = Organism(policy="minimal", profile=a.profile, seed=0, overrides=ov)
    h, nm = org.hill, org.nm
    types = org.conn.neurons.type.to_numpy().astype(str)
    out = {"profile": a.profile, "ttm_hook": org.ttm is not None, "rows": []}
    for k, row in enumerate(nm.mn_index):
        if types[row] != "TTMn":
            continue
        mu = int(h.mn_muscle[k])
        r = {"mn_row": int(row), "instance": str(org.conn.neurons.instance.to_numpy()[row]),
             "hill_muscle": None if mu < 0 else f"{h.p.joint[mu]} dir {h.p.direction[mu]:+.0f}",
             "weight": float(h.w[k])}
        if mu >= 0:
            members = np.flatnonzero(h.mn_muscle == mu)
            r["weight_share"] = round(float(h.w[k] / h.W[mu]), 4)
            r["pool_members"] = int(len(members))
            r["pool_types"] = sorted(set(types[np.asarray(nm.mn_index)[members]].tolist()))
            r["F0_uN"], r["r_mm"] = float(h.p.F0[mu]), float(h.p.r[mu])
        out["rows"].append(r)
    print(json.dumps(out, indent=1))


if __name__ == "__main__":
    main()
