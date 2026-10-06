"""Figure for rung 8 step 1 (N29): antennal-lobe rates around the odour step, switch off against on.

Inputs: runs/s12/stp/al_{off,on}_s{seed}.npz from stp_al.py. One column per group (ORN, uPN, LN), one
line per seed and switch value; the odour starts at 1500 ms (grey line). Writes runs/s12/stp/al_step.png.

    uv run python scripts/probes/stp_al_plot.py --seeds 12 13 14
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402

D = Path(__file__).resolve().parents[2] / "runs/s12/stp"


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--seeds", type=int, nargs="+", default=[12, 13, 14])
    a = ap.parse_args()
    groups = ["ORN", "uPN", "LN"]
    fig, axs = plt.subplots(1, 3, figsize=(12, 3.6), sharex=True)
    for arm, col in (("off", "0.45"), ("on", "tab:red")):
        for s in a.seeds:
            f = D / f"al_{arm}_s{s}.npz"
            if not f.exists():
                continue
            z, j = np.load(f), json.load(open(D / f"al_{arm}_s{s}.json"))
            for ax, g in zip(axs, groups):
                lab = (f"switch {'1' if arm == 'on' else '0'}" if s == a.seeds[0] else None)
                ax.plot(z["t_ms"], z[g], color=col, lw=1, label=lab)
                tr = j[g]["transience"]
                ax.text(0.98, 0.62 - 0.065 * (a.seeds.index(s) + (3 if arm == "on" else 0)),
                        f"s{s} {arm}: transience {tr}", transform=ax.transAxes, ha="right", va="top",
                        fontsize=7, color=col)
    for ax, g in zip(axs, groups):
        ax.axvline(1500, color="0.8", lw=0.8)
        ax.set_title(f"{g} (mean per cell)")
        ax.set_xlabel("time (ms); odour from 1500 ms")
    axs[0].set_ylabel("rate (Hz, 50 ms bins)")
    axs[0].legend(loc="upper left", fontsize=8)
    fig.suptitle("Rung 8 step 1: ORN->PN and ORN->LN short-term depression (Nagel 2015, 2016 fits), m9r, "
                 "closed loop at rest", fontsize=9)
    fig.tight_layout()
    fig.savefig(D / "al_step.png", dpi=90)


if __name__ == "__main__":
    main()
