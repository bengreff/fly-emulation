"""Aggregate run metrics and render the figures for the session report."""
from __future__ import annotations

import json
import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[1]
RUNS = REPO / "runs"
FIGS = REPO / "docs" / "figures"
FIGS.mkdir(parents=True, exist_ok=True)

# Measured reference values, Azevedo et al. 2020, eLife 56754.
SLOW_MN_REST_HZ = 30.0

plt.rcParams.update({
    "figure.dpi": 160, "font.size": 8, "axes.spines.top": False,
    "axes.spines.right": False, "axes.linewidth": 0.6,
    "xtick.major.width": 0.6, "ytick.major.width": 0.6, "savefig.bbox": "tight",
})
C = {"baseline": "#267655", "silence_i1i2": "#d4831f", "shuffle": "#8b2f5f",
     "dna02": "#2f6f8b", "no_stim": "#8a8a8a"}


def load_conditions() -> pd.DataFrame:
    rows = []
    for d in sorted(RUNS.glob("pugliese-*-n16-papertol")):
        m = d / "metrics.csv"
        if not m.exists():
            continue
        cond = d.name.split("-")[1:-2]
        cond = "-".join(cond) if cond else d.name
        df = pd.read_csv(m)
        df["condition"] = cond
        rows.append(df)
    return pd.concat(rows, ignore_index=True) if rows else pd.DataFrame()


def load_sweep(sweep_dir: Path) -> pd.DataFrame:
    rows = []
    for d in sorted(sweep_dir.glob("pugliese-baseline-n*-papertol-e*i*")):
        m = d / "metrics.csv"
        if not m.exists():
            continue
        tag = d.name.split("-e")[-1]
        scale = float(tag.split("i")[0])
        df = pd.read_csv(m)
        df["scale"] = scale
        rows.append(df)
    return pd.concat(rows, ignore_index=True) if rows else pd.DataFrame()


def fig_conditions(df: pd.DataFrame) -> None:
    order = [c for c in ["baseline", "silence_i1i2", "shuffle", "dna02", "no_stim"]
             if c in set(df.condition)]
    metrics = [
        ("oscillation_score_mn", "motor-neuron rhythmicity", None),
        ("oscillation_freq_hz_mn", "rhythm frequency (Hz)", None),
        ("n_active_mn", "active motor neurons (of 144)", None),
        ("mn_peak_rate_max_hz", "peak motor-neuron rate (Hz)", SLOW_MN_REST_HZ),
    ]
    fig, axes = plt.subplots(1, 4, figsize=(9.2, 2.3))
    for ax, (col, label, ref) in zip(axes, metrics):
        vals = [df.loc[df.condition == c, col].dropna().values for c in order]
        for i, (c, v) in enumerate(zip(order, vals)):
            if len(v) == 0:
                continue
            ax.scatter(np.random.default_rng(i).normal(i, 0.07, len(v)), v, s=6,
                       color=C.get(c, "k"), alpha=0.65, edgecolors="none", zorder=3)
            ax.hlines(np.mean(v), i - 0.28, i + 0.28, color=C.get(c, "k"), lw=1.8, zorder=4)
        if ref is not None:
            ax.axhline(ref, ls="--", lw=0.9, color="#c0392b", zorder=2)
            ax.text(len(order) - 0.45, ref * 1.06, "slow MN at rest, measured",
                    color="#c0392b", fontsize=6, ha="right")
            ax.set_yscale("log")
        ax.set_xticks(range(len(order)))
        ax.set_xticklabels([o.replace("silence_i1i2", "silence\nI1+I2").replace("_", "\n")
                            for o in order], fontsize=6.5)
        ax.set_title(label, fontsize=8)
        ax.margins(x=0.12)
    fig.suptitle("Connectome VNC model under descending stimulation: conditions and controls",
                 fontsize=9, y=1.06)
    fig.savefig(FIGS / "conditions.png")
    plt.close(fig)


def fig_traces() -> None:
    pairs = [("baseline", "pugliese-baseline-n16-papertol"),
             ("shuffle", "pugliese-shuffle-n16-papertol")]
    avail = [(n, RUNS / d / "R_replicate0.npz") for n, d in pairs
             if (RUNS / d / "R_replicate0.npz").exists()]
    if not avail:
        return
    fig, axes = plt.subplots(1, len(avail), figsize=(4.6 * len(avail), 2.6), squeeze=False)
    for ax, (name, p) in zip(axes[0], avail):
        d = np.load(p)
        R, t, mn = d["R"], d["t"], d["mn_idx"]
        act = mn[R[mn].max(1) > 0]
        order = act[np.argsort(-R[act].max(1))][:12]
        for k, i in enumerate(order):
            ax.plot(t, R[i] + k * 1.2 * max(1.0, R[order].max()), lw=0.7,
                    color=C[name], alpha=0.9)
        ax.set_xlim(0.3, 1.2)
        ax.set_xlabel("time (s)")
        ax.set_yticks([])
        ax.set_title(f"{name}: {len(act)} active motor neurons, "
                     f"peak {R[act].max():.1f} Hz" if len(act) else name, fontsize=8)
    fig.suptitle("Motor-neuron output. Real connectome (left) versus degree-matched shuffle (right)",
                 fontsize=9, y=1.04)
    fig.savefig(FIGS / "traces.png")
    plt.close(fig)


def fig_sweep(df: pd.DataFrame) -> None:
    if df.empty:
        return
    g = df.groupby("scale")
    x = np.array(sorted(df.scale.unique()))
    fig, axes = plt.subplots(1, 3, figsize=(8.4, 2.4))
    specs = [("oscillation_score_mn", "motor-neuron rhythmicity", None),
             ("mn_peak_rate_max_hz", "peak motor-neuron rate (Hz)", SLOW_MN_REST_HZ),
             ("n_active_mn", "active motor neurons (of 144)", None)]
    for ax, (col, label, ref) in zip(axes, specs):
        mu = g[col].mean().reindex(x)
        sd = g[col].std(ddof=1).reindex(x).fillna(0)
        ax.plot(x, mu, "-o", ms=3, lw=1.2, color="#267655")
        ax.fill_between(x, mu - sd, mu + sd, color="#267655", alpha=0.18, lw=0)
        if ref is not None:
            ax.axhline(ref, ls="--", lw=0.9, color="#c0392b")
            ax.text(x[0], ref * 1.12, "measured slow MN at rest", color="#c0392b", fontsize=6)
            ax.set_yscale("log")
        ax.axvline(0.03, ls=":", lw=0.9, color="k")
        ax.text(0.031, ax.get_ylim()[0], " published value", fontsize=6, rotation=90, va="bottom")
        ax.set_xscale("log")
        ax.set_xlabel("global synaptic scale")
        ax.set_title(label, fontsize=8)
    fig.suptitle("Can any global synaptic scale give both the rhythm and physiological rates?",
                 fontsize=9, y=1.06)
    fig.savefig(FIGS / "sweep.png")
    plt.close(fig)


def main() -> None:
    sweep_dir = Path(sys.argv[1]) if len(sys.argv) > 1 else RUNS
    cond = load_conditions()
    if not cond.empty:
        fig_conditions(cond)
        summary = cond.groupby("condition").agg(
            reps=("replicate", "count"),
            rhythmicity=("oscillation_score_mn", "mean"),
            rhythmicity_sd=("oscillation_score_mn", "std"),
            freq_hz=("oscillation_freq_hz_mn", "mean"),
            active_mn=("n_active_mn", "mean"),
            active_all=("n_active", "mean"),
            mn_peak_hz=("mn_peak_rate_max_hz", "max"),
        ).round(3)
        summary.to_csv(REPO / "docs" / "conditions_summary.csv")
        print(summary.to_string())
    fig_traces()
    sw = load_sweep(sweep_dir)
    if not sw.empty:
        fig_sweep(sw)
        s = sw.groupby("scale").agg(
            reps=("replicate", "count"),
            rhythmicity=("oscillation_score_mn", "mean"),
            freq_hz=("oscillation_freq_hz_mn", "mean"),
            active_mn=("n_active_mn", "mean"),
            active_all=("n_active", "mean"),
            mn_peak_hz=("mn_peak_rate_max_hz", "max"),
            net_peak_hz=("max_rate_hz", "max"),
        ).round(3)
        s.to_csv(REPO / "docs" / "sweep_summary.csv")
        print("\n" + s.to_string())
    print("\nfigures ->", FIGS)


if __name__ == "__main__":
    main()
