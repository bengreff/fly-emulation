"""Score the s20 MB resting-rate fit once against Huang et al. 2024 Fig. 1 (DECISIONS 22 Oct 22:23).

Data readout as registered: per trial, rate = len(DetectedSpikes) / (t[-1] - t[0]); trials averaged within a fly;
per type, the median across flies and the 10th-90th percentile across flies. Model readout: the per-type mean rate at
sigma*, averaged over seeds 12 and 13, locked in runs/s20/mb/model_readout.json before this script first ran.
Per-type pass: model inside [min(P10, median/2), max(P90, 2 x median)]. Test set: the 9 types other than PPL105 and
MBON14; pass if >= 6 of 9.
"""
from __future__ import annotations

import io
import json
import re
import zipfile
from collections import defaultdict
from pathlib import Path

import numpy as np
import scipy.io as sio

ROOT = Path(__file__).resolve().parents[2]
ZIP = ROOT / "data/raw/huang2024/Figure1.zip"
MODEL = ROOT / "runs/s20/mb/model_readout.json"
OUT = ROOT / "runs/s20/mb/huang_score.json"
DIR2KEY = {"PPL1-v1": "PPL1-γ1", "PPL1-v2": "PPL1-γ2", "PPL1-a`3": "PPL1-α′3", "PPL1-a2": "PPL1-α2", "PPL1-a3": "PPL1-α3",
           "MBON-v1": "MBON-γ1", "MBON-v2": "MBON-γ2", "MBON-a`2": "MBON-α′2", "MBON-a3": "MBON-α3",
           "MBON-a`3m": "MBON-α′3m", "MBON-a2sc": "MBON-α2sc"}
FIT = {"PPL1-α2", "MBON-α3"}


def main() -> None:
    z = zipfile.ZipFile(ZIP)
    trials = defaultdict(lambda: defaultdict(list))        # type -> fly -> [rate]
    dur_check = []
    for n in z.namelist():
        if not n.endswith(".mat") or n.startswith("__MACOSX"):
            continue
        d = n.split("/")[1]
        fly = re.search(r"_Fly(\d+)_Trial", n).group(1)
        m = sio.loadmat(io.BytesIO(z.read(n)), squeeze_me=True)
        t = np.asarray(m["t"], dtype=float)
        k = np.atleast_1d(m["DetectedSpikes"]).size
        dur = t[-1] - t[0]
        dur_check.append(dur / (t.size / float(m["imagingRate"])))
        trials[DIR2KEY[d]][fly].append(k / dur)
    dc = np.array(dur_check)
    assert np.all(np.abs(dc - 1) < 0.01), f"t is not in seconds: ratio {dc.min():.4f}-{dc.max():.4f}"
    model = json.loads(MODEL.read_text())["model_hz"]
    rows, n_pass = {}, 0
    for key, flies in trials.items():
        per_fly = np.array([np.mean(v) for v in flies.values()])
        med, p10, p90 = np.median(per_fly), np.percentile(per_fly, 10), np.percentile(per_fly, 90)
        lo, hi = min(p10, med / 2), max(p90, 2 * med)
        mhz = model[key]["mean"]
        ok = bool(lo <= mhz <= hi)
        test = key not in FIT
        n_pass += ok and test
        rows[key] = {"model_type": model[key]["type"], "model_hz": mhz, "n_flies": int(per_fly.size),
                     "n_trials": int(sum(len(v) for v in flies.values())), "median_hz": med, "p10": p10, "p90": p90,
                     "band": [lo, hi], "pass": ok, "role": "test" if test else "fit (cross-study check)",
                     "ratio_model_over_median": mhz / med if med > 0 else None}
    res = {"test_pass_count": int(n_pass), "test_n": 9, "verdict": "PASS" if n_pass >= 6 else "FAIL",
           "duration_ratio_range": [float(dc.min()), float(dc.max())], "types": rows}
    OUT.write_text(json.dumps(res, indent=1, ensure_ascii=False))
    for k, r in sorted(rows.items()):
        print(f"{k:11s} {r['model_type']:7s} model {r['model_hz']:6.2f}  data median {r['median_hz']:6.2f} "
              f"[P10 {r['p10']:5.2f}, P90 {r['p90']:5.2f}] band [{r['band'][0]:5.2f}, {r['band'][1]:5.2f}] "
              f"flies {r['n_flies']:2d}  {'PASS' if r['pass'] else 'fail'}  ({r['role']})")
    print(f"test set: {n_pass} of 9 -> {res['verdict']}")


if __name__ == "__main__":
    main()
