"""wneuro item 1: the adoption check's figure (adopt_near.py's docstring). The vulval 5-HT organs_egglaying reads and
its SER-7 occupancy against time, off and nicholson, food and nofood; the pool part dashed.

Usage: python adopt_near_fig.py OFF_DIR NICHOLSON_DIR OUT.png
"""
from __future__ import annotations

import sys
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402


def main(off, nich, png):
    fig, ax = plt.subplots(2, 2, figsize=(11, 6), sharex=True)
    for j, cond in enumerate(("food", "nofood")):
        for d, lab, col in ((off, "off", "0.4"), (nich, "nicholson", "C3")):
            f = Path(d) / f"{cond}_vulva5ht.npz"
            if not f.exists():
                continue
            z = np.load(f)
            t, c, pool = z["t_ms"] / 1000.0, z["c5_nM"], z["pool_nM"]
            ax[0, j].plot(t, c, color=col, lw=0.8, label=f"{lab}: read")
            ax[0, j].plot(t, pool, color=col, lw=0.8, ls="--", label=f"{lab}: pool part")
            ax[1, j].plot(t, c / (c + 30.0), color=col, lw=0.8, label=lab)
        ax[0, j].set_title(cond)
        ax[0, j].set_ylabel("vulval 5-HT read (nM)")
        ax[1, j].set_ylabel("SER-7 occupancy (EC50 30 nM, Hill 1)")
        ax[1, j].set_xlabel("bio s")
        ax[1, j].axvline(5.0, color="k", lw=0.5, ls=":")
        ax[0, j].legend(fontsize=7)
        ax[1, j].legend(fontsize=7)
    fig.suptitle("amine_synaptic adoption check: vulval 5-HT and SER-7 occupancy (settle 5 s dotted)")
    fig.tight_layout()
    fig.savefig(png, dpi=110)
    print(png)


if __name__ == "__main__":
    main(*sys.argv[1:4])
