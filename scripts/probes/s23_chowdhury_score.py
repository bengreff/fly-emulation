"""s23 N25 Chowdhury 2023 score (DECISIONS 23 Oct 00:53 rule; locked predictions 23 Oct 23:52). Dryad needs a login
or a bot check, so the registered fallback is used: a blind figure read of Fig. 1 (Sonnet reader, 24 Oct;
`docs/research/s23_chowdhury_fig1_read.md`), with its read uncertainty added. Fig. 1 shows box plots, so group means
and SEMs are estimated from the quartiles (Wan et al. 2014: mean (q1 + m + q3) / 3, SD IQR / 1.35); medians and
panel K's means are reported as alternatives, and panel J (which disagrees with panel I for the 20 s arm) as a
sensitivity reading.

    python3 scripts/probes/s23_chowdhury_score.py   # -> runs/s23/n25/chowdhury_score.json
"""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np

# (Q1, median, Q3) in min, n. C = 6 h, F = 12 h, I = 24 h (ctrl and the 20 s arm); J-left = the 20 s arm by duration
BOX = {"6": {"ctrl": ((-3.4, 59.2, 95.6), 44), "f20": ((97.1, 181.5, 252.2), 62), "J20": ((128.6, 193.5, 278.9), 62)},
       "12": {"ctrl": ((-11.7, 29.6, 92.9), 32), "f20": ((67.9, 143.9, 219.3), 64), "J20": ((78.7, 128.6, 219.7), 64)},
       "24": {"ctrl": ((11.4, 58.2, 107.1), 64), "f20": ((149.5, 195.7, 275.5), 32), "J20": ((66.9, 101.2, 141.1), 32)}}
K24 = {"f20": 213.1, "ctrl": 49.8}   # panel K points, 24 h, raw post - pre (bar type not stated)
READ = 4.0   # read uncertainty of a difference of two box reads (each +-2.2-2.9 min)
DUR = ("6", "12", "24")
PREDS = {"B (scored)": (69.3, 114.4, 139.9), "A": (57.0, 100.0, 125.4), "s22 locked": (99.7, 150.2, 174.3),
         "s22 T5-amended": (70, 111, 131), "00:34 mode 1": (142, 139, 138), "00:34 V3": (175, 195, 212),
         "00:34 mode 0": (19, -22, 49)}


def est(q, n):
    q1, m, q3 = q
    return (q1 + m + q3) / 3, (q3 - q1) / 1.35 / np.sqrt(n), m


def main() -> None:
    out = {}
    for reading, fk in (("C/F/I, box means", "f20"), ("C/F/I, medians", "f20"), ("J, box means", "J20")):
        spans = {}
        for d in DUR:
            mf, sf, medf = est(*BOX[d][fk])
            mc, sc, medc = est(*BOX[d]["ctrl"])
            c = (medf - medc) if "medians" in reading else (mf - mc)
            se = float(np.hypot(sf, sc))
            spans[d] = {"rebound": round(c, 1), "sem": round(se, 1), "lo": round(c - 2 * se - READ, 1),
                        "hi": round(c + 2 * se + READ, 1)}
        out[reading] = {"spans": spans}
    se24 = out["C/F/I, box means"]["spans"]["24"]["sem"]
    c = K24["f20"] - K24["ctrl"]
    out["K means (24 h only)"] = {"spans": {"24": {"rebound": round(c, 1), "sem": se24,
                                                   "lo": round(c - 2 * se24 - READ, 1),
                                                   "hi": round(c + 2 * se24 + READ, 1)}}}
    for v in out.values():
        v["inside"] = {p: {d: bool(v["spans"][d]["lo"] <= x[i] <= v["spans"][d]["hi"])
                           for i, d in enumerate(DUR) if d in v["spans"]} for p, x in PREDS.items()}
    for r in ("C/F/I, box means", "J, box means"):
        s = out[r]["spans"]
        out[r]["ordering_24_minus_6"] = {"diff": round(s["24"]["rebound"] - s["6"]["rebound"], 1),
                                         "two_comb_sem": round(2 * float(np.hypot(s["24"]["sem"], s["6"]["sem"])), 1)}
    Path("runs/s23/n25").mkdir(parents=True, exist_ok=True)
    Path("runs/s23/n25/chowdhury_score.json").write_text(json.dumps({"box": BOX, "K24": K24, "read_unc": READ,
                                                                     "preds": PREDS, "out": out}, indent=1))
    for r, v in out.items():
        print(r, {d: (s["rebound"], s["lo"], s["hi"]) for d, s in v["spans"].items()}, v.get("ordering_24_minus_6", ""))
        for p, ins in v["inside"].items():
            print("   ", p, ins)


if __name__ == "__main__":
    main()
