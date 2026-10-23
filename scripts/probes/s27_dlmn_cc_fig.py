"""s27 (fly2): figure for the DLMn c-f coupling fit (F-S27-1), from the saved s27_dlmn_cc runs.

Left: the first 20 ms pulse into DLMn c-f 31456 (R side) at c 0.0266, its three same-side partners and one
opposite-side cell, each relative to the unstimulated twin; the uncoupled run's partner trace for comparison.
Right: clean-pair CC against c (s27_dlmn_cc_baseline.py), with Hurkey 2023 Fig 2f's pair-count mean and s.d. band.
Writes runs/s27/dlmn_cc_fig.png.

    .venv/bin/python scripts/probes/s27_dlmn_cc_fig.py
"""
from __future__ import annotations

import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402

REPO = Path(__file__).resolve().parents[2]
D = REPO / "runs" / "s27"
SETTLE, PULSE, GAP = 1000, 200, 800          # steps of 0.1 ms, as in s27_dlmn_cc.py
TARGET, BAND = 0.0143, (0.0073, 0.026)       # Hurkey 2023 Fig 2f pair-count mean, +- s.d.


def main() -> None:
    meta = json.load(open(D / "dlmn_cc_c0.0266.json"))["meta"]
    cf, side = meta["cf"], meta["side_cf"]
    dv = np.load(D / "dlmn_cc_c0.0266_dv.npy")
    dv0 = np.load(D / "dlmn_cc_uncoupled_dv.npy")
    t = (np.arange(SETTLE - 100, SETTLE + PULSE + GAP) - SETTLE) * 0.1          # ms from pulse onset
    sl = slice(SETTLE - 100, SETTLE + PULSE + GAP)
    fig, (a1, a2) = plt.subplots(1, 2, figsize=(11, 4.2))
    a1.plot(t, dv[sl, 0], "k", lw=1.5, label=f"pre {cf[0]} (R), pulsed")
    ax2 = a1.twinx()
    for i in range(1, len(cf)):
        if side[i] == "R":
            ax2.plot(t, dv[sl, i], lw=1, label=f"partner {cf[i]} (R)")
    ax2.plot(t, dv[sl, cf.index(36444)], "0.6", lw=1, ls="--", label="36444 (L, not coupled)")
    ax2.plot(t, dv0[sl, 1], "r:", lw=1.2, label=f"{cf[1]} with c = 0")
    a1.set_xlabel("ms from pulse onset")
    a1.set_ylabel("pre dV (mV)")
    ax2.set_ylabel("partner dV (mV)")
    lo, hi = a1.get_ylim()
    ax2.set_ylim(lo * 0.02, hi * 0.02)                                          # partner axis = pre axis x 0.02
    a1.legend(loc="upper left", fontsize=7)
    ax2.legend(loc="upper right", fontsize=7)
    a1.set_title("20 ms pulse, c 0.0266 (seed 12, unstimulated twin subtracted)", fontsize=9)

    rows = [r for r in json.load(open(D / "dlmn_cc_baseline.json")) if not r["tag"].endswith("r")]
    c = np.array([r["coupling"] for r in rows])
    m = np.array([r["pulse_cc_mean"] for r in rows])
    lo_ = np.array([r["pulse_cc_min"] for r in rows])
    hi_ = np.array([r["pulse_cc_max"] for r in rows])
    a2.axhspan(*BAND, color="0.9", label="Hurkey Fig 2f s.d. band")
    a2.axhline(TARGET, color="0.4", ls="--", label="target 0.0143 (pair-count mean)")
    a2.axhline(0.023, color="0.6", ls=":", lw=1, label="strong 0.023 / weak 0.010")
    a2.axhline(0.010, color="0.6", ls=":", lw=1)
    a2.errorbar(c, m, yerr=[m - lo_, hi_ - m], fmt="o", color="k", capsize=3, label="model, clean pairs (min-max)")
    k = np.polyfit(c, m, 1)
    cc = np.linspace(0, 0.036, 50)
    a2.plot(cc, np.polyval(k, cc), "k-", lw=0.6)
    a2.axvline(0.0266, color="C3", lw=0.8, label="fitted c 0.0266")
    a2.set_xlabel("c (junction / partner leak conductance)")
    a2.set_ylabel("pulse CC (post peak / pre peak)")
    a2.set_xlim(0, 0.036)
    a2.set_ylim(0, 0.03)
    a2.legend(fontsize=7, loc="upper left")
    a2.set_title("DLMn c-f CC vs coupling", fontsize=9)
    fig.tight_layout()
    out = D / "dlmn_cc_fig.png"
    fig.savefig(out, dpi=130)
    print(out)


if __name__ == "__main__":
    main()
