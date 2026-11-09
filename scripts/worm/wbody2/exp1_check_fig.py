"""Figure for the EXP-1 port check (exp1_check.py): int9 Ca, DVB V, enteric V, activation and expulsions per run.

Usage: python exp1_check_fig.py OUT.png TAG [TAG ...]   (reads runs/worm/wbody2/exp1_check_TAG.{json,npz})
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

OUT = Path(__file__).resolve().parents[3] / "runs/worm/wbody2"
MUSCLES = ("mu_intL", "mu_intR", "mu_anal", "mu_sph")


def main():
    png, tags = sys.argv[1], sys.argv[2:]
    fig, ax = plt.subplots(4, len(tags), figsize=(5.5 * len(tags), 9), sharex=True, squeeze=False)
    for c, tag in enumerate(tags):
        z = np.load(OUT / f"exp1_check_{tag}.npz")
        r = json.loads((OUT / f"exp1_check_{tag}.json").read_text())
        t = z["t"]
        ax[0, c].plot(t, z["int9_ca"], "k", lw=0.8)
        ax[0, c].axhline(0.3, color="0.6", ls=":", lw=0.8)
        ax[0, c].set_title(f"{tag}: form {r['form']}, DVB drive {r['drive']}, bar 2 {r['bar2']}", fontsize=9)
        ax[0, c].set_ylabel("int9 Ca, mean L/R (uM)")
        ax[1, c].plot(t, z["dvb_v"], "C3", lw=0.8)
        ax[1, c].set_ylabel("DVB V (mV, 50 ms samples)")
        for k, m in enumerate(MUSCLES):
            ax[2, c].plot(t, z["enteric_v"][:, k], lw=0.6, label=m)
        ax[2, c].set_ylabel("enteric muscle V (mV, 50 ms\nsamples: 4 Hz spikes alias)")
        ax[2, c].legend(fontsize=7, loc="upper right", ncol=4)
        ax[3, c].plot(t, z["enteric_act"][:, :3].mean(axis=1), "C2", lw=0.8, label="detector input (mean of 3)")
        ax[3, c].axhline(0.5, color="C3", ls="--", lw=0.8, label="on 0.5")
        ax[3, c].axhline(0.2, color="C0", ls="--", lw=0.8, label="off 0.2")
        for e in z["expulsions_s"]:
            ax[3, c].axvline(e, color="m", lw=1.2)
        for s in z["dvb_spike_peaks_s"]:
            for a in ax[:, c]:
                a.axvline(s, color="C3", lw=0.4, alpha=0.4)
        ax[3, c].set_ylim(0, 1)
        ax[3, c].set_ylabel("enteric activation")
        ax[3, c].set_xlabel("time (s); red lines DVB spike peaks, magenta expulsions")
        ax[3, c].legend(fontsize=7, loc="upper right")
    fig.tight_layout()
    fig.savefig(png, dpi=110)


if __name__ == "__main__":
    main()
