"""Figures for the control experiments: drive targets, glutamate sign,
transmitter uncertainty, and phasic sensory drive."""
from __future__ import annotations

import re
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
SLOW_MN_REST_HZ = 30.0

plt.rcParams.update({
    "figure.dpi": 160, "font.size": 8, "axes.spines.top": False,
    "axes.spines.right": False, "axes.linewidth": 0.6,
    "xtick.major.width": 0.6, "ytick.major.width": 0.6, "savefig.bbox": "tight",
})
GREEN, PLUM, RED, BLUE = "#267655", "#8b2f5f", "#c0392b", "#2f6f8b"


def load(pattern: str) -> pd.DataFrame:
    rows = []
    for d in sorted(RUNS.glob(pattern)):
        for name in ("metrics.csv", "metrics_partial.csv"):
            f = d / name
            if f.exists():
                try:
                    df = pd.read_csv(f)
                except Exception:
                    break
                df["run"] = d.name
                rows.append(df)
                break
    return pd.concat(rows, ignore_index=True) if rows else pd.DataFrame()


def fig_drive_targets() -> None:
    """Unmatched versus threshold-matched drive, by target population."""
    df = load("pugliese-baseline-n8-papertol-*S*")
    if df.empty:
        return
    df = df[df.run.str.contains("papertol") & ~df.run.str.contains("probe|test|tm1|tm2")]
    if df.empty:
        return
    def parse(r):
        amp = float(re.search(r"-S([\d.]+)", r).group(1))
        tgt = "random interneurons" if "rand" in r else (
              "bristles" if "bris" in r else "proprioceptors")
        return amp, tgt, "thrmatch" in r
    meta = df.run.map(parse)
    df["amp"] = [m[0] for m in meta]
    df["target"] = [m[1] for m in meta]
    df["matched"] = [m[2] for m in meta]
    amps = sorted(df.amp.unique())
    amps = [a for a in amps if a in (5.0, 12.5)]
    if not amps:
        return
    fig, axes = plt.subplots(1, len(amps), figsize=(3.2 * len(amps), 2.9), squeeze=False)
    colors = {"proprioceptors": GREEN, "random interneurons": PLUM, "bristles": BLUE}
    for ax, amp in zip(axes[0], amps):
        sub = df[df.amp == amp]
        groups, labels, cols = [], [], []
        for matched in (False, True):
            for tgt in ("proprioceptors", "random interneurons", "bristles"):
                v = sub[(sub.matched == matched) & (sub.target == tgt)]["oscillation_score_mn"]
                if len(v) == 0:
                    continue
                groups.append(v.values)
                labels.append(f"{tgt}\n{'matched' if matched else 'flat'}")
                cols.append(colors[tgt])
        for i, (v, c) in enumerate(zip(groups, cols)):
            ax.scatter(np.random.default_rng(i).normal(i, .07, len(v)), v, s=8,
                       color=c, alpha=.7, edgecolors="none", zorder=3)
            ax.hlines(v.mean(), i - .3, i + .3, color=c, lw=2, zorder=4)
        ax.axhline(0.836, ls="--", lw=.9, color="#888")
        ax.text(len(groups) - .5, .86, "undriven baseline", fontsize=6,
                color="#666", ha="right")
        ax.set_xticks(range(len(labels)))
        ax.set_xticklabels(labels, fontsize=6, rotation=30, ha="right",
                           rotation_mode="anchor")
        ax.set_ylim(-.05, 1.0)
        ax.set_ylabel("motor-neuron rhythmicity" if amp == amps[0] else "")
        ax.set_title(f"drive amplitude {amp:g}", fontsize=8)
    fig.suptitle("Flat current exaggerates the sensory pathway; matching each cell's "
                 "threshold removes the difference", fontsize=8.5, y=1.04)
    fig.savefig(FIGS / "drive_targets.png")
    plt.close(fig)


def fig_glutamate() -> None:
    df = load("pugliese-baseline-n8-papertol-glu*")
    if df.empty:
        return
    df["glu"] = df.run.map(lambda r: float(re.search(r"-glu(-?[\d.]+)", r).group(1)))
    g = df.groupby("glu")
    x = np.array(sorted(df.glu.unique()))
    fig, ax = plt.subplots(figsize=(4.4, 2.7))
    mu = g["oscillation_score_mn"].mean().reindex(x)
    sd = g["oscillation_score_mn"].std(ddof=1).reindex(x).fillna(0)
    ax.plot(x, mu, "-o", ms=4, lw=1.4, color=GREEN)
    ax.fill_between(x, mu - sd, mu + sd, color=GREEN, alpha=.18, lw=0)
    ax.axvline(0.03, ls=":", lw=1, color="k")
    ax.text(0.029, .95, "published", fontsize=6.5, rotation=90, va="top", ha="right")
    ax.axvline(0, ls="-", lw=.7, color="#999")
    ax.set_xlabel("glutamate multiplier   (positive = inhibitory, negative = excitatory)")
    ax.set_ylabel("motor-neuron rhythmicity")
    ax.set_ylim(-.05, 1.0)
    ax.set_title("Glutamatergic cells are 24% of the network\nand 41% of its inhibition",
                 fontsize=8.5)
    fig.savefig(FIGS / "glutamate.png")
    plt.close(fig)


def fig_nt_uncertainty() -> None:
    res = load("pugliese-baseline-n24-papertol-ntsample*")
    fix = load("pugliese-baseline-n16-papertol")
    if res.empty or fix.empty:
        return
    fig, ax = plt.subplots(figsize=(4.4, 2.7))
    bins = np.linspace(0, 1, 21)
    ax.hist(fix["oscillation_score_mn"], bins=bins, color=GREEN, alpha=.75,
            label=f"most-likely labels, as published (n={len(fix)})")
    ax.hist(res["oscillation_score_mn"], bins=bins, color=PLUM, alpha=.65,
            label=f"sign resampled from the classifier (n={len(res)})")
    ax.set_xlabel("motor-neuron rhythmicity")
    ax.set_ylabel("replicates")
    ax.legend(frameon=False, fontsize=6.5)
    ax.set_title("Does the rhythm survive the connectome's own\nannotation uncertainty?",
                 fontsize=8.5)
    fig.savefig(FIGS / "nt_uncertainty.png")
    plt.close(fig)


def fig_phasic_sweep() -> None:
    """F12: does the timing of sensory drive matter? Built from the recovered CSV."""
    f = REPO / "data" / "derived" / "phasic_sweep.csv"
    if not f.exists():
        return
    df = pd.read_csv(f)
    g = df.groupby("freq_hz")
    x = np.array(sorted(df.freq_hz.unique()))
    mu = g["oscillation_score_mn"].mean().reindex(x)
    sd = g["oscillation_score_mn"].std(ddof=1).reindex(x).fillna(0)
    fig, ax = plt.subplots(figsize=(4.8, 2.8))
    ph = x > 0
    ax.plot(x[ph], mu[ph], "-o", ms=4, lw=1.4, color=GREEN, label="rhythmic sensory drive")
    ax.fill_between(x[ph], (mu - sd)[ph], (mu + sd)[ph], color=GREEN, alpha=.18, lw=0)
    if (x == 0).any():
        ax.axhline(float(mu[x == 0].iloc[0]), ls="-.", lw=1.1, color=PLUM,
                   label="tonic drive, same mean")
    ax.axhline(0.836, ls="--", lw=1.1, color="#666", label="undriven baseline")
    ax.set_ylim(-.05, 1.0)
    ax.set_xlabel("sensory modulation frequency (Hz)")
    ax.set_ylabel("motor-neuron rhythmicity")
    ax.legend(frameon=False, fontsize=6.5, loc="center right")
    ax.set_title("Matched mean drive, different timing.\nNo frequency restores the rhythm.",
                 fontsize=8.5)
    fig.savefig(FIGS / "phasic_sweep.png")
    plt.close(fig)


def main() -> None:
    fig_drive_targets()
    fig_glutamate()
    fig_nt_uncertainty()
    fig_phasic_sweep()
    print("figures ->", FIGS)
    for p in sorted(FIGS.glob("*.png")):
        print("  ", p.name)


if __name__ == "__main__":
    main()
