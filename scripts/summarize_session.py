"""Aggregate every run in runs/ (and runs_pc/) into the session summary tables."""
from __future__ import annotations

import json
import re
from pathlib import Path

import pandas as pd

REPO = Path(__file__).resolve().parents[1]
COLS = ["oscillation_score_mn", "oscillation_freq_hz_mn", "n_active_mn",
        "n_active", "mn_peak_rate_median_hz", "mn_peak_rate_max_hz"]


def load_all(*dirs: Path) -> pd.DataFrame:
    rows = []
    for d in dirs:
        if not d.exists():
            continue
        for run in sorted(d.glob("*")):
            m = run / "metrics.csv"
            if not m.exists():
                m = run / "metrics_partial.csv"
            if not m.exists():
                continue
            try:
                df = pd.read_csv(m)
            except Exception:
                continue
            df["run"] = run.name
            prov = list(run.glob("*.provenance.json"))
            if prov:
                try:
                    p = json.loads(prov[0].read_text())
                    df["condition"] = p.get("condition", "")
                    notes = p.get("condition_notes", {}) or {}
                    df["drive_target"] = notes.get("drive_target", "")
                    df["n_scaffolds"] = len(p.get("scaffolds", []))
                except Exception:
                    pass
            rows.append(df)
    return pd.concat(rows, ignore_index=True) if rows else pd.DataFrame()


def tag(run: str) -> str:
    if "-ntsample" in run: return "transmitter resampled"
    if "-glu" in run: return "glutamate sign"
    if "-rand" in run: return "drive: random interneurons"
    if "-bris" in run: return "drive: bristles"
    if re.search(r"-S[\d.]+$", run) or re.search(r"-S[\d.]+-", run): return "drive: proprioceptors"
    if "-e" in run and "i" in run.split("-e")[-1]: return "synaptic scale"
    if run.startswith("phasic-"): return "phasic sensory"
    return "condition"


def main() -> None:
    df = load_all(REPO / "runs", REPO / "runs_pc" / "runs")
    if df.empty:
        print("no runs found")
        return
    df["family"] = df["run"].map(tag)
    # keep only paper-tolerance runs for the headline tables
    paper = df[df["run"].str.contains("papertol") | df["run"].str.startswith("phasic-")]
    have = [c for c in COLS if c in paper.columns]
    g = (paper.groupby(["family", "run"])
              .agg(reps=("replicate", "count"),
                   **{c: (c, "mean") for c in have})
              .round(3).reset_index())
    out = REPO / "docs" / "all_runs_summary.csv"
    g.to_csv(out, index=False)
    for fam, sub in g.groupby("family"):
        print(f"\n=== {fam} ===")
        cols = ["run", "reps", "oscillation_score_mn", "oscillation_freq_hz_mn",
                "n_active_mn", "mn_peak_rate_median_hz"]
        cols = [c for c in cols if c in sub.columns]
        print(sub[cols].to_string(index=False))
    print(f"\n{len(df)} replicate rows across {df.run.nunique()} runs -> {out}")


if __name__ == "__main__":
    main()
