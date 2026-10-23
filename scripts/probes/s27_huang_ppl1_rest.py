"""s27 (fly2): N21 candidate (b), do any PPL1 compartments' DANs rest near test R's ~0.0015 Hz? Huang 2024 (spent).

Huang et al. 2024 Fig. 1 voltage imaging (Zenodo 10998457, data/raw/huang2024/Figure1.zip), released to fly2 by
the Director on 23 Oct 03:25 after fly scored it once (F-S21-1). Same readout as fly's s21_mb_huang_score.py: per
trial, rate = spikes / duration; trials averaged within a fly. Here: per PPL1 type, the per-fly minimum, P10 and
median, and how many flies rest below 0.1 Hz. Writes runs/s27/huang_ppl1_rest.json.

    .venv/bin/python scripts/probes/s27_huang_ppl1_rest.py
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
PPL1 = {"PPL1-v1": "PPL1-γ1", "PPL1-v2": "PPL1-γ2", "PPL1-a`3": "PPL1-α′3", "PPL1-a2": "PPL1-α2", "PPL1-a3": "PPL1-α3"}
R_BOUND_HZ = 0.0015          # test R: N21 is resting-safe only below about this DAN rate (F-S26-1)


def main() -> None:
    z = zipfile.ZipFile(ZIP)
    trials = defaultdict(lambda: defaultdict(list))
    for n in z.namelist():
        if not n.endswith(".mat") or n.startswith("__MACOSX"):
            continue
        d = n.split("/")[1]
        if d not in PPL1:
            continue
        fly = re.search(r"_Fly(\d+)_Trial", n).group(1)
        m = sio.loadmat(io.BytesIO(z.read(n)), squeeze_me=True)
        t = np.asarray(m["t"], dtype=float)
        trials[PPL1[d]][fly].append(np.atleast_1d(m["DetectedSpikes"]).size / (t[-1] - t[0]))
    out = {}
    for key, flies in sorted(trials.items()):
        r = np.array([np.mean(v) for v in flies.values()])
        out[key] = {"n_flies": int(r.size), "min_hz": float(r.min()), "p10_hz": float(np.percentile(r, 10)),
                    "median_hz": float(np.median(r)), "max_hz": float(r.max()),
                    "flies_below_0p1hz": int(np.sum(r < 0.1)), "min_over_R_bound": float(r.min() / R_BOUND_HZ)}
        print(key, {k: round(v, 2) if isinstance(v, float) else v for k, v in out[key].items()})
    d = ROOT / "runs" / "s27"
    d.mkdir(parents=True, exist_ok=True)
    (d / "huang_ppl1_rest.json").write_text(json.dumps(out, ensure_ascii=False, indent=1))


if __name__ == "__main__":
    main()
