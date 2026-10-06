"""Dose curves from route_rates.py JSON files: type mean rate against stimulus rate, one panel per type
(diagnostic, no simulation).

Each --curve is LABEL=FILE[,FILE...]: the route_rates --out JSON files whose runs together make one curve
(for example a dose split over two runs). Use --off-curve for the post-stimulus window (route_rates
--window off_real); it is drawn dashed in the same colour.

    uv run python scripts/probes/route_dose_plot.py --types MN9_L,GNG108,AN01B004 \
        --curve near=runs/s12/spec/d1.json --off-curve near=runs/s12/spec/d1_off.json --png out.png
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path


def load(spec: str) -> tuple[str, dict]:
    label, files = spec.split("=", 1)
    pts: dict = {}
    for f in files.split(","):
        for by in json.loads(Path(f).read_text()).values():
            for rate, row in by.items():
                for t, v in row.items():
                    if v["mean"] is not None:
                        pts.setdefault(t, {})[float(rate)] = v["mean"]
    return label, pts


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--types", required=True)
    ap.add_argument("--curve", action="append", default=[], metavar="LABEL=FILE[,FILE]")
    ap.add_argument("--off-curve", action="append", default=[], metavar="LABEL=FILE[,FILE]")
    ap.add_argument("--mark", default="", help="comma-separated stimulus rates to mark with vertical lines")
    ap.add_argument("--title", default="")
    ap.add_argument("--png", required=True)
    a = ap.parse_args()
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    import matplotlib.ticker
    types = a.types.split(",")
    cols = 4
    rows = -(-len(types) // cols)
    fig, axes = plt.subplots(rows, cols, figsize=(3.2 * cols, 2.6 * rows), squeeze=False)
    on = [load(s) for s in a.curve]
    off = dict(load(s) for s in a.off_curve)
    colours = plt.rcParams["axes.prop_cycle"].by_key()["color"]
    for k, t in enumerate(types):
        ax = axes[k // cols, k % cols]
        for c, (label, pts) in enumerate(on):
            p = sorted(pts.get(t, {}).items())
            if p:
                ax.plot([x for x, _ in p], [y for _, y in p], "o-", color=colours[c], label=f"{label}, during")
            q = sorted(off.get(label, {}).get(t, {}).items())
            if q:
                ax.plot([x for x, _ in q], [y for _, y in q], "s--", color=colours[c], mfc="none",
                        label=f"{label}, 1 s after")
        for m in [float(x) for x in a.mark.split(",") if x]:
            ax.axvline(m, color="0.7", lw=0.8)
        ax.set_xscale("log")
        xs = sorted({x for _, pts in on for x in pts.get(t, {})})
        ax.set_xticks(xs, [f"{x:g}" for x in xs])
        ax.xaxis.set_minor_formatter(matplotlib.ticker.NullFormatter())
        ax.set_ylim(bottom=0)
        ax.set_title(t, fontsize=9)
        ax.set_xlabel("GRN input (Hz)", fontsize=8)
        ax.set_ylabel("mean rate (Hz)", fontsize=8)
        ax.tick_params(labelsize=7)
    for k in range(len(types), rows * cols):
        axes[k // cols, k % cols].axis("off")
    axes[0, 0].legend(fontsize=7)
    if a.title:
        fig.suptitle(a.title, fontsize=10)
    fig.tight_layout()
    Path(a.png).parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(a.png, dpi=130)
    print(a.png)


if __name__ == "__main__":
    main()
