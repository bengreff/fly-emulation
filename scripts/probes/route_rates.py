"""Rates of named cell types across finished assay runs, per stimulus rate (diagnostic, no simulation).

Reads each run's rates.npz (body_id, real_{rate}_{trial}) and the male-cns neuron table, and prints
for every type (or instance name, e.g. MN9_L) the per-cell rate averaged over trials, plus the type mean, at each stimulus rate.

    uv run python scripts/probes/route_rates.py --runs runs/assay-legsugar3_mn9-m2-ffi_sil \
        runs/assay-legsugar3_mn9-m9r-ffi_sil --types AN17A002,GNG578,GNG143,GNG108,MN9 --rates 100,200
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[2]


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--runs", nargs="+", required=True)
    ap.add_argument("--types", required=True)
    ap.add_argument("--rates", default="100,200")
    ap.add_argument("--out", default="")
    ap.add_argument("--png", default="", help="heatmap of type means at each --png-rate, one row per run")
    ap.add_argument("--png-rate", default="200")
    ap.add_argument("--labels", default="", help="comma-separated row labels for --png (default: run names)")
    ap.add_argument("--title", default="")
    a = ap.parse_args()
    nrn = pd.read_parquet(REPO / "data/cache/male_cns_neurons.parquet", columns=["bodyId", "type", "instance"])
    types = [t for t in a.types.split(",") if t]
    res = {}
    for run in a.runs:
        z = np.load(Path(run) / "rates.npz")
        bid = z["body_id"]
        res[run] = {}
        for r in a.rates.split(","):
            ks = sorted(k for k in z.files if k.startswith(f"real_{r}_"))
            if not ks:
                continue
            mean = pd.Series(np.mean([z[k] for k in ks], axis=0), index=bid)
            row = {}
            for t in types:
                sub = nrn[nrn.type == t]
                if sub.empty:                       # fall back to an instance name such as MN9_L
                    sub = nrn[nrn.instance == t]
                v = mean.reindex(sub.bodyId).to_numpy()
                row[t] = {"cells": [None if np.isnan(x) else round(float(x), 1) for x in v],
                          "mean": round(float(np.nanmean(v)), 1) if np.isfinite(v).any() else None}
            res[run][r] = row
    for run, by in res.items():
        print(run)
        for r, row in by.items():
            print(f"  {r:>4} Hz  " + "  ".join(f"{t} {row[t]['mean']}" for t in types))
    if a.out:
        Path(a.out).write_text(json.dumps(res, indent=1))
    if a.png:
        plot(res, types, a)


def plot(res: dict, types: list[str], a) -> None:
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    runs = list(res)
    labels = [x for x in a.labels.split(",") if x] or [Path(r).name for r in runs]
    rates = a.png_rate.split(",")                 # one panel per stimulus rate
    fig, axes = plt.subplots(len(rates), 1, figsize=(1.0 * len(types) + 4, (0.4 * len(runs) + 1.6) * len(rates)),
                             squeeze=False)
    for ax, rate in zip(axes[:, 0], rates):
        m = np.array([[np.nan if (v := res[r].get(rate, {}).get(t, {}).get("mean")) is None else v
                       for t in types] for r in runs], dtype=float)
        im = ax.imshow(np.log10(1 + m), cmap="viridis", vmin=0, vmax=np.log10(1 + max(150, np.nanmax(m))), aspect="auto")
        for i in range(m.shape[0]):
            for j in range(m.shape[1]):
                if np.isfinite(m[i, j]):
                    ax.text(j, i, f"{m[i, j]:.1f}", ha="center", va="center", fontsize=8,
                            color="white" if np.log10(1 + m[i, j]) < 1.4 else "black")
        ax.set_xticks(range(len(types)), types, rotation=30, ha="right")
        ax.set_yticks(range(len(runs)), labels)
        ax.set_title((a.title + ": " if a.title else "") + f"mean rate (Hz) at {rate} Hz stimulus", fontsize=9)
        fig.colorbar(im, ax=ax, label="log10(1 + Hz)")
    fig.tight_layout()
    Path(a.png).parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(a.png, dpi=130)

if __name__ == "__main__":
    main()
