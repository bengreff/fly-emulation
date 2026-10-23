"""s27 (fly2): figure for the N12 second check (Hurkey 2023 splay), from runs/s27/dlmn_splay_{A,B}_{fit,c0}.json.

Top: same-side pairwise phase histograms (20 bins), fitted vs c = 0, per condition, with the uniform level.
Bottom: near-zero-phase fraction per pair (same side, cross side) per arm, with the registered thresholds.
Writes runs/s27/dlmn_splay_fig.png.

    .venv/bin/python scripts/probes/s27_dlmn_splay_fig.py
"""
from __future__ import annotations

import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402

D = Path(__file__).resolve().parents[2] / "runs" / "s27"
COND = {"A": ("A: independent input only", 0.18), "B": ("B: shared 50 Hz + independent 150 Hz", 0.20)}


def main() -> None:
    fig, ax = plt.subplots(2, 2, figsize=(11, 7.5))
    for j, (c, (title, thr)) in enumerate(COND.items()):
        r = {arm: json.loads((D / f"dlmn_splay_{c}_{arm}.json").read_text()) for arm in ("fit", "c0")}
        a = ax[0, j]
        x = (np.arange(20) + 0.5) / 20
        for arm, col, lab in (("c0", "0.5", "c = 0 (shakB KD analogue)"), ("fit", "C0", "fitted c 0.0266")):
            h = np.asarray(r[arm]["same_side_phase_hist20"], float)
            a.step(x, h / h.sum() * 20, where="mid", color=col, lw=2, label=lab)
        a.axhline(1.0, color="k", ls=":", lw=1, label="uniform")
        a.axvspan(0, 0.1, color="r", alpha=0.08)
        a.axvspan(0.9, 1, color="r", alpha=0.08)
        a.set_xlim(0, 1)
        a.set_xlabel("partner spike phase in reference ISI (same-side pairs)")
        a.set_ylabel("density")
        a.set_title(title, fontsize=10)
        a.legend(fontsize=8)
        b = ax[1, j]
        for k, arm in enumerate(("fit", "c0")):
            for m, (key, col) in enumerate((("same_pairs", "C0"), ("cross_pairs", "C1"))):
                f = [p[2] for p in r[arm][key]]
                xs = k * 3 + m + np.random.default_rng(0).uniform(-0.15, 0.15, len(f))
                b.plot(xs, f, "o", color=col, alpha=0.6, ms=4)
                b.plot([k * 3 + m - 0.3, k * 3 + m + 0.3], [np.mean(f)] * 2, color="k", lw=2)
        b.axhline(0.2, color="k", ls=":", lw=1)
        b.axhline(thr, color="r", ls="--", lw=1)
        b.set_xticks([0, 1, 3, 4], ["fit same", "fit cross", "c0 same", "c0 cross"])
        b.set_ylabel("fraction with phase < 0.1 or > 0.9")
        rates = np.mean(list(r["fit"]["rate_hz"].values()))
        b.set_title(f"pairs (fitted arm mean rate {rates:.1f} Hz); red: registered same-side threshold", fontsize=9)
    fig.suptitle("N12 second check: Hurkey 2023 splay gap with the fitted DLMn junction (no refit), m10f5 seed 12, 18 s")
    fig.tight_layout()
    fig.savefig(D / "dlmn_splay_fig.png", dpi=110)


if __name__ == "__main__":
    main()
