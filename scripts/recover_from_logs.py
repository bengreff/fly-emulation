"""Recover per-replicate readouts from run logs when a run was killed before
writing metrics.csv. Parses the progress lines the runners print."""
from __future__ import annotations
import re, sys
from pathlib import Path
import pandas as pd

PAT = re.compile(
    r"rep\s+(\d+):\s+active=\s*(\d+)\s+activeMN=\s*(\d+)\s+oscMN=([\d.]+)\s+fMN=([\d.]+)Hz")
# phasic_sensory.py prints a different line shape
PAT_PHASIC = re.compile(
    r"rep\s+(\d+):\s+activeMN=\s*(\d+)\s+osc=([\d.]+)\s+f=([\d.]+)Hz\s+peakMN=([\d.]+)Hz")

def parse(path: Path, **extra) -> list[dict]:
    rows = []
    for line in path.read_text(errors="ignore").splitlines():
        m = PAT.search(line)
        if m:
            rows.append(dict(replicate=int(m[1]), n_active=int(m[2]),
                             n_active_mn=int(m[3]),
                             oscillation_score_mn=float(m[4]),
                             oscillation_freq_hz_mn=float(m[5]), **extra))
            continue
        m = PAT_PHASIC.search(line)
        if m:
            rows.append(dict(replicate=int(m[1]), n_active_mn=int(m[2]),
                             oscillation_score_mn=float(m[3]),
                             oscillation_freq_hz_mn=float(m[4]),
                             mn_peak_rate_median_hz=float(m[5]), **extra))
    return rows

def main() -> None:
    out, rows = Path(sys.argv[1]), []
    root = Path(sys.argv[2])
    pattern = sys.argv[3] if len(sys.argv) > 3 else "sweep_*.log"
    key = sys.argv[4] if len(sys.argv) > 4 else "scale"
    for f in sorted(root.glob(pattern)):
        rows += parse(f, **{key: float(f.stem.split("_")[-1])})
    if rows:
        df = pd.DataFrame(rows)
        df.to_csv(out, index=False)
        print(df.groupby(key).agg(
            reps=("replicate", "count"),
            active_mn=("n_active_mn", "mean"),
            rhythmicity=("oscillation_score_mn", "mean"),
            freq_hz=("oscillation_freq_hz_mn", "mean")).round(3).to_string())
        print("\nwrote", out)

if __name__ == "__main__":
    main()
