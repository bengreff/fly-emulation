"""s27 (fly2): apply the N12 second-check pass rules (DECISIONS 23 Oct 03:34) to runs/s27/dlmn_splay_{A,B}_{fit,c0}.json.

The mean over ordered pairs equals the mean over unordered pairs of the two directions' average, so the registered
"12 same-side / 16 cross-side pairs" (unordered counts) and the probe's 24 / 32 ordered pairs give the same means.
Writes runs/s27/dlmn_splay_score.json.

    .venv/bin/python scripts/probes/s27_dlmn_splay_score.py
"""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np

D = Path(__file__).resolve().parents[2] / "runs" / "s27"


def load(c: str, arm: str) -> dict:
    r = json.loads((D / f"dlmn_splay_{c}_{arm}.json").read_text())
    rates = list(r["rate_hz"].values())
    return {"same": r["same_side_frac_mean"], "same_sem": r["same_side_frac_sem"], "cross": r["cross_side_frac_mean"],
            "n_same": len(r["same_pairs"]), "n_cross": len(r["cross_pairs"]),
            "rate_min": min(rates), "rate_mean": float(np.mean(rates)), "rate_max": max(rates),
            "isi_cv_mean": float(np.mean(r["isi_cv"])), "gap_pairs": r["gap_pairs"]}


def main() -> None:
    v = {c: {arm: load(c, arm) for arm in ("fit", "c0")} for c in ("A", "B")}
    a, b = v["A"], v["B"]
    rules = {
        "A_same_below_0.18": a["fit"]["same"] < 0.18,
        "A_same_0.02_below_c0": a["fit"]["same"] <= a["c0"]["same"] - 0.02,
        "A_cross_in_0.17_0.23": 0.17 <= a["fit"]["cross"] <= 0.23,
        "B_same_below_0.20": b["fit"]["same"] < 0.20,
        "B_same_0.02_below_c0": b["fit"]["same"] <= b["c0"]["same"] - 0.02,
    }
    out = {"values": v, "rules": rules,
           "A_pass": all(x for k, x in rules.items() if k.startswith("A")),
           "B_pass": all(x for k, x in rules.items() if k.startswith("B")),
           "falsified": a["fit"]["same"] >= a["c0"]["same"] or b["fit"]["same"] >= b["c0"]["same"],
           "rates_in_3_12_hz": all(3 <= v[c][m]["rate_min"] and v[c][m]["rate_max"] <= 12 for c in v for m in v[c])}
    out["row_proposed_done"] = out["A_pass"] and out["B_pass"]
    (D / "dlmn_splay_score.json").write_text(json.dumps(out, indent=1))
    print(json.dumps(out, indent=1))


if __name__ == "__main__":
    main()
