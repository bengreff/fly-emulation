"""Figure for motion_grating.py runs: per-type modulation and T4/T5 direction responses, one row per arm.

    uv run python scripts/probes/motion_grating_plot.py --runs runs/s12/vision/grating_m9c.json \
        runs/s12/vision/grating_T.json --labels B,T --png docs/media/s12_vision_grating.png
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402

DIRS = ["az+", "az-", "el+", "el-"]


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--runs", nargs="+", required=True)
    ap.add_argument("--labels", default="")
    ap.add_argument("--png", required=True)
    a = ap.parse_args()
    data = [json.loads(Path(r).read_text()) for r in a.runs]
    labels = a.labels.split(",") if a.labels else [Path(r).stem for r in a.runs]
    types = list(data[0]["res"]["static"])
    t45 = [t for t in types if t[:2] in ("T4", "T5")]

    fig, axes = plt.subplots(3, 1, figsize=(15, 4 + 2.0 * len(data) * 3), constrained_layout=True)
    # 1: per-cell F1 (each cell's modulation at the grating frequency, averaged over the type), max over
    # directions, with the static grating's per-cell F1 below it as the noise floor
    f1 = np.array([row for d in data for row in
                   ([max(d["res"][k][t]["f1_cell_mv"] for k in DIRS) for t in types],
                    [d["res"]["static"][t]["f1_cell_mv"] for t in types])])
    im = axes[0].imshow(np.log10(np.maximum(f1, 1e-3)), aspect="auto", cmap="viridis", vmin=-3, vmax=1)
    axes[0].set_title("per-cell modulation at the grating frequency (log10 mV): max over 4 directions, "
                      "and the static grating (noise floor)")
    for i in range(f1.shape[0]):
        for j in range(len(types)):
            axes[0].text(j, i, f"{f1[i, j]:.2g}", ha="center", va="center", fontsize=6,
                         color="w" if f1[i, j] < 0.3 else "k")
    fig.colorbar(im, ax=axes[0], shrink=0.8)
    # 2: mean shift from the static grating (mV), each direction, T4/T5 and their inputs
    cols = [t for t in types if t in ("L1", "L2", "Mi1", "Tm3", "Mi4", "Mi9", "Tm1", "Tm2", "Tm4", "Tm9", "CT1",
                                      "Am1", "HSN", "HSE", "HSS", "H2", "HST")] + t45
    dv = np.array([[d["res"][k][t]["v_mv"] - d["res"]["static"][t]["v_mv"] for t in cols]
                   for d in data for k in DIRS])
    lim = max(0.05, float(np.abs(dv).max()))
    im2 = axes[1].imshow(dv, aspect="auto", cmap="RdBu_r", vmin=-lim, vmax=lim)
    axes[1].set_title("mean potential shift from the static grating (mV), rows: arm x direction")
    fig.colorbar(im2, ax=axes[1], shrink=0.8)
    # 3: spike rate shift (Hz) for the same cells
    dr = np.array([[d["res"][k][t]["rate_hz"] - d["res"]["static"][t]["rate_hz"] for t in cols]
                   for d in data for k in DIRS])
    liml = max(0.5, float(np.abs(dr).max()))
    im3 = axes[2].imshow(dr, aspect="auto", cmap="PuOr_r", vmin=-liml, vmax=liml)
    axes[2].set_title("spike rate shift from the static grating (Hz; graded cells are always 0)")
    fig.colorbar(im3, ax=axes[2], shrink=0.8)
    for ax, xs in ((axes[0], types), (axes[1], cols), (axes[2], cols)):
        ax.set_xticks(range(len(xs)))
        ax.set_xticklabels(xs, rotation=70, fontsize=7)
    axes[0].set_yticks(range(f1.shape[0]))
    axes[0].set_yticklabels([f"{lab} {k}" for lab in labels for k in ("grating", "static")], fontsize=7)
    rl = [f"{lab} {k}" for lab in labels for k in DIRS]
    for ax in axes[1:]:
        ax.set_yticks(range(len(rl)))
        ax.set_yticklabels(rl, fontsize=7)
    fig.suptitle("Drifting grating (30 deg, 1 Hz) straight onto the photoreceptors, no body, open loop")
    Path(a.png).parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(a.png, dpi=110)


if __name__ == "__main__":
    main()
