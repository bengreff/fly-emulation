"""s25 figure: DA-only restoration in network against Hattori et al. 2017 Fig 6F.

Left: recovery after n DAN stimulations, Hattori figure estimates +- SEM and +- 2 SEM bands (pre-registered),
the analytic fit R(n) = 1 - (1 - r)^(S n), and each seed's in-network recovery (MBON16/17 with PPL104).
Right: Hige 2015 Fig 3D forward CS+ ratio with r on, per seed, against the 0.06-0.14 band.

    .venv/bin/python scripts/probes/s25_restore_figure.py [--dir runs/s25/restore]
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

N = np.array([1, 3, 6, 10])
Y = np.array([0.08, 0.18, 0.33, 0.40])
SEM = np.array([0.05, 0.07, 0.06, 0.06])
R, S = 0.00289, 20


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dir", type=Path, default=Path("runs/s25/restore"))
    a = ap.parse_args()
    fig, (ax, bx) = plt.subplots(1, 2, figsize=(10, 4), gridspec_kw={"width_ratios": [2, 1]})
    ax.fill_between(N, Y - 2 * SEM, Y + 2 * SEM, color="0.85", label="Hattori ± 2 SEM (pass band)")
    ax.errorbar(N, Y, SEM, fmt="ko", capsize=3, label="Hattori 2017 Fig 6F (figure estimate)")
    n = np.linspace(0, 10, 101)
    ax.plot(n, 1 - (1 - R) ** (S * n), "b-", lw=1, label=f"analytic fit r {R}, S {S}")
    for p in sorted(a.dir.glob("hattori_s*.json")):
        rows = json.loads(p.read_text())["restore"]["rows"]
        ax.plot([x["n"] for x in rows], [x["recovery"] for x in rows], ".-", alpha=0.7,
                label=f"network, seed {p.stem.split('_s')[1]}")
    ax.set_xlabel("DAN stimulations (10 pulses of 50 ms at 7 Hz each)")
    ax.set_ylabel("recovery of depressed KC->MBON-α'3 weight")
    ax.set_title("PPL1-α'3 alone restores MBON-α'3 input")
    ax.legend(fontsize=7)
    seeds, cp = [], []
    for p in sorted(a.dir.glob("hige_fwd_s*.json")):
        d = json.loads(p.read_text())
        seeds.append(int(p.stem.split("_s")[1]))
        cp.append(next(x for x in d["result"] if x["set"] == "cs_plus")["charge_ratio"])
    bx.axhspan(0.06, 0.14, color="0.85", label="pass band")
    bx.axhline(0.10, color="k", lw=0.8, label="Hige 2015 Fig 3D")
    bx.plot(seeds, cp, "bo", label="network, r on")
    bx.set_ylim(0, 0.3)
    bx.set_xticks(seeds)
    bx.set_xlim(min(seeds, default=12) - 0.5, max(seeds, default=15) + 0.5)
    bx.set_xlabel("seed")
    bx.set_ylabel("CS+ charge ratio, MBON-γ1pedc>α/β")
    bx.set_title("Regression: forward pairing")
    bx.legend(fontsize=7)
    fig.tight_layout()
    out = a.dir / "fig_s25_restore.png"
    fig.savefig(out, dpi=120)
    print(out)


if __name__ == "__main__":
    main()
