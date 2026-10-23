"""s27 (fly2): re-score s27_dlmn_cc runs with each response taken from its value at stimulus onset.

A DLMn pulsed in an earlier trial still carries a slow undershoot (about -0.04 mV) when the next trial starts, which
biased the first scoring low for those partners. Here every peak is measured from the cell's own dv at onset,
and only clean pairs count: those whose partner had not yet been stimulated in the run (each pair once).

    .venv/bin/python scripts/probes/s27_dlmn_cc_baseline.py c0.02 c0.03 c0.0334
    .venv/bin/python scripts/probes/s27_dlmn_cc_baseline.py --directions c0.0266 c0.0266r   # vs a --reverse run
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np

REPO = Path(__file__).resolve().parents[2]
SETTLE, PULSE, GAP = 1000, 200, 800


def score(tag: str) -> dict:
    r = json.loads((REPO / "runs" / "s27" / f"dlmn_cc_{tag}.json").read_text())
    dv = np.load(REPO / "runs" / "s27" / f"dlmn_cc_{tag}_dv.npy")
    side = np.array(r["meta"]["side_cf"])
    n = len(side)
    pulse, ahp, pre_pk = {}, {}, []
    for j in range(n):
        s0 = SETTLE + j * (PULSE + GAP)
        w = dv[s0:s0 + PULSE + GAP, :n] - dv[s0 - 1, :n]
        pk = w.max(axis=0)
        pre_pk.append(float(pk[j]))
        s1 = SETTLE + (n + j) * (PULSE + GAP)
        w2 = dv[s1 + 1:s1 + PULSE + GAP, :n] - dv[s1 - 1, :n]
        lo = w2.min(axis=0)
        for i in range(n):
            if i != j and side[i] == side[j]:
                pulse[(j, i)] = float(pk[i] / pk[j])
                ahp[(j, i)] = float(lo[i] / lo[j])
    asym = [abs(v - pulse[(i, j)]) / max(v, pulse[(i, j)]) for (j, i), v in pulse.items() if j < i]
    # clean pairs: the partner had not yet been stimulated in this run (its own slow undershoot is absent)
    p = np.array([v for (j, i), v in pulse.items() if j < i])
    a = np.array([v for (j, i), v in ahp.items() if j < i])
    return {"tag": tag, "coupling": r["coupling"], "pulse_cc_mean": float(p.mean()), "pulse_cc_min": float(p.min()),
            "pulse_cc_max": float(p.max()), "clean_pairs": int(p.size), "direction_asym_max_all": float(max(asym)),
            "ahp_cc_mean": float(a.mean()), "ahp_cc_min": float(a.min()), "ahp_cc_max": float(a.max()),
            "pre_pulse_peak_mv": float(np.mean(pre_pk)),
            "stim_spikes": len(r["stim_spikes"]), "ctl_spikes": len(r["ctl_spikes"])}


def clean_by_cell(tag: str) -> dict:
    """{(pre cell id, post cell id): clean pulse CC} for one run."""
    r = json.loads((REPO / "runs" / "s27" / f"dlmn_cc_{tag}.json").read_text())
    dv = np.load(REPO / "runs" / "s27" / f"dlmn_cc_{tag}_dv.npy")
    cf, side = r["meta"]["cf"], r["meta"]["side_cf"]
    n, out = len(cf), {}
    for j in range(n):
        s0 = SETTLE + j * (PULSE + GAP)
        pk = (dv[s0:s0 + PULSE + GAP, :n] - dv[s0 - 1, :n]).max(axis=0)
        for i in range(j + 1, n):
            if side[i] == side[j]:
                out[(cf[j], cf[i])] = float(pk[i] / pk[j])
    return out


def directions(fwd: str, rev: str) -> dict:
    """Each same-side pair read cleanly in both directions: forward run (index order) against the --reverse run."""
    a, b = clean_by_cell(fwd), clean_by_cell(rev)
    rows = [(p, q, a[(p, q)], b[(q, p)]) for (p, q) in a if (q, p) in b]
    d = [abs(x - y) / max(x, y) for _, _, x, y in rows]
    return {"fwd": fwd, "rev": rev, "pairs": len(rows), "max_rel_diff": float(max(d)), "mean_rel_diff": float(np.mean(d)),
            "rows": [{"a": p, "b": q, "cc_a_to_b": x, "cc_b_to_a": y} for p, q, x, y in rows]}


if __name__ == "__main__":
    if sys.argv[1] == "--directions":
        o = directions(sys.argv[2], sys.argv[3])
        (REPO / "runs" / "s27" / "dlmn_cc_directions.json").write_text(json.dumps(o, indent=1))
        print(json.dumps({k: v for k, v in o.items() if k != "rows"}))
        for row in o["rows"]:
            print(row)
        sys.exit(0)
    out = [score(t) for t in sys.argv[1:]]
    (REPO / "runs" / "s27" / "dlmn_cc_baseline.json").write_text(json.dumps(out, indent=1))
    for o in out:
        print(json.dumps({k: (round(v, 5) if isinstance(v, float) else v) for k, v in o.items()}))
