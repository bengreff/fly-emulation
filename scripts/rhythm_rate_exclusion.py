"""Finding F15: does any simulation produce both a rhythm and usable motor output?

Pools every replicate of every run in `runs/` that recorded both readouts, and
reports the exclusion at a range of thresholds so the conclusion can be checked
without trusting a single cut point.

    uv run python scripts/rhythm_rate_exclusion.py
"""
from __future__ import annotations

import glob
import os
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[1]
NEED = ["oscillation_score_mn", "mn_peak_rate_median_hz"]
SLOW_MN_REST_HZ = 30.0   # Azevedo et al. 2020, slow tibia-flexor unit at rest


def load_all(runs: Path) -> pd.DataFrame:
    rows = []
    for d in sorted(glob.glob(str(runs / "*/"))):
        for name in ("metrics.csv", "metrics_partial.csv"):
            f = os.path.join(d, name)
            if os.path.exists(f):
                try:
                    x = pd.read_csv(f)
                except Exception:
                    break
                x["run"] = os.path.basename(d.rstrip("/"))
                rows.append(x)
                break
    if not rows:
        return pd.DataFrame()
    df = pd.concat(rows, ignore_index=True)
    if not all(c in df.columns for c in NEED):
        return pd.DataFrame()
    return df.dropna(subset=NEED)


def main() -> None:
    df = load_all(REPO / "runs")
    if df.empty:
        print("no runs with both readouts found")
        return
    print(f"{len(df)} replicate simulations with both readouts, "
          f"across {df.run.nunique()} runs\n")

    print("For each motor-rate floor, the best rhythmicity any simulation reached:")
    for hz in (2, 5, 10, 15, 20, 30, 50):
        sub = df[df.mn_peak_rate_median_hz > hz]
        if not len(sub):
            continue
        i = sub.oscillation_score_mn.idxmax()
        ctrl = " <- scrambled-connectome CONTROL" if "shuffle" in sub.loc[i, "run"] else ""
        print(f"  rate > {hz:2d} Hz : n={len(sub):3d}  best rhythmicity "
              f"{sub.oscillation_score_mn.max():.3f}{ctrl}")

    print("\nFor each rhythmicity floor, the best motor rate any simulation reached:")
    for r in (0.3, 0.4, 0.5, 0.6, 0.8):
        sub = df[df.oscillation_score_mn > r]
        if not len(sub):
            continue
        i = sub.mn_peak_rate_median_hz.idxmax()
        ctrl = " <- scrambled-connectome CONTROL" if "shuffle" in sub.loc[i, "run"] else ""
        print(f"  rhythmicity > {r:.1f} : n={len(sub):3d}  best rate "
              f"{sub.mn_peak_rate_median_hz.max():6.2f} Hz{ctrl}")

    both = df[(df.oscillation_score_mn > 0.5) &
              (df.mn_peak_rate_median_hz > SLOW_MN_REST_HZ / 3)]
    real = both[~both.run.str.contains("shuffle")]
    print(f"\nSimulations that are clearly rhythmic (> 0.5) AND fire above "
          f"{SLOW_MN_REST_HZ/3:.0f} Hz: {len(both)}")
    print(f"  of those, excluding the scrambled-connectome control: {len(real)}")
    if len(real):
        print(real[["run"] + NEED].to_string(index=False))
    else:
        print("  none. This is finding F15.")


if __name__ == "__main__":
    main()
