"""Figure for visual_flash.py runs: type-mean traces to full-field flashes, one line per arm, laid out as
Behnia et al. 2014 Fig. 2, with the recorded peak deflections (figure estimates) written on each panel.

    uv run python scripts/probes/visual_flash_plot.py --runs runs/s12/vision/flash_B.json \
        runs/s12/vision/flash_RTc.json --labels B,RTc --png docs/media/s12_vision_flash.png
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402

PANELS = ["R1-R6", "L1", "L2", "Mi1", "Tm3", "Tm1", "Tm2", "Mi4", "Mi9", "T4a", "T5a", "CT1", "HSN", "VS"]
# Behnia et al. 2014 Fig. 2, read, figure estimates against the 10 mV scale bar (full-field flash from dark)
RECORDED = {"Mi1": "recorded: ON about +20 mV", "Tm3": "recorded: ON about +15 mV",
            "Tm1": "recorded: ON dip, OFF about +15-20 mV", "Tm2": "recorded: ON dip, OFF about +15-20 mV"}


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--runs", nargs="+", required=True)
    ap.add_argument("--labels", default="")
    ap.add_argument("--png", required=True)
    a = ap.parse_args()
    data = [json.loads(Path(r).read_text()) for r in a.runs]
    labels = a.labels.split(",") if a.labels else [Path(r).stem for r in a.runs]
    panels = [p for p in PANELS if p in data[0]["trace"]]
    ncol = 4
    nrow = int(np.ceil(len(panels) / ncol))
    fig, axes = plt.subplots(nrow, ncol, figsize=(4.2 * ncol, 2.6 * nrow), constrained_layout=True)
    for ax, ty in zip(axes.flat, panels):
        for d, lab in zip(data, labels):
            t = np.asarray(d["t_ms"]) / 1000.0
            v = np.asarray(d["trace"][ty])
            r = d["res"][ty]
            ax.plot(t, v, lw=1.0, label=lab if r["graded"] else f"{lab} spiking, {r['rate_hz']:.0f} Hz")
        for on, dur in data[0]["meta"]["flashes_ms"]:
            ax.axvspan(on / 1000.0, (on + dur) / 1000.0, color="gold", alpha=0.25, lw=0)
        ax.set_title(ty, fontsize=9)
        if ty in RECORDED:
            ax.text(0.01, 0.97, RECORDED[ty], transform=ax.transAxes, va="top", fontsize=7, color="crimson")
        ax.tick_params(labelsize=7)
        ax.legend(fontsize=6, loc="lower right")
    for ax in list(axes.flat)[len(panels):]:
        ax.axis("off")
    fig.supxlabel("s after the dark settle (gold: full-field flash, intensity 0 to 1)", fontsize=9)
    fig.supylabel("type-mean membrane potential (mV)", fontsize=9)
    fig.suptitle("Full-field flashes from darkness, open loop, no body (Behnia et al. 2014 Fig. 2 stimulus)")
    Path(a.png).parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(a.png, dpi=110)


if __name__ == "__main__":
    main()
