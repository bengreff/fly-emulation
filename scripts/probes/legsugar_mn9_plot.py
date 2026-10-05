"""Figure for F-TASTE-LEG-1 (trace): fraction of the shortest-path cells in each layer that fire more than in
the control (> control + 2.5 Hz), GRN layer 0 to MN9 layer 3, for each test condition.

Inputs: runs/s12/legsugar/trace_s12.json (layers, from legsugar_mn9_trace.py report), the closed-loop runs
(run_c1, run_inj_all, run_inj_fore against run_c0) and the open-loop Shiu-parameter assay
(runs/assay-legsugar_mn9-m2-s12/rates.npz, 100 and 200 Hz against 0 Hz, mean of 2 trials).

    uv run python scripts/probes/legsugar_mn9_plot.py
"""
from __future__ import annotations

import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402

REPO = Path(__file__).resolve().parents[2]
D = REPO / "runs/s12/legsugar"


def main() -> None:
    r = json.load(open(D / "trace_s12.json"))
    n = 167111
    layer = np.full(n, -1)
    for c in r["cells"]:
        layer[c["row"]] = c["layer"]
    tr = r["dynamics"]
    # layers 0 and 3 from the stored per-layer counts; rows of the middle layers from `cells`
    C = np.load(D / "run_c0_s12.npz")["hz"]
    R = np.load(REPO / "runs/assay-legsugar_mn9-m2-s12/rates.npz")
    b0 = (R["real_0_0"] + R["real_0_1"]) / 2
    conds = {
        "patch 1 M, closed loop (m9r)": (np.load(D / "run_c1_s12.npz")["hz"], C, tr["shortest_path_layers"]),
        "all 54 leg GRNs injected (m9r)": (np.load(D / "run_inj_all_s12.npz")["hz"], C, r["inject"]["all"]["layers"]),
        "foreleg GRNs injected (m9r)": (np.load(D / "run_inj_fore_s12.npz")["hz"], C, r["inject"]["fore"]["layers"]),
        "Shiu params, 100 Hz, open loop (m2)": ((R["real_100_0"] + R["real_100_1"]) / 2, b0, None),
        "Shiu params, 200 Hz, open loop (m2)": ((R["real_200_0"] + R["real_200_1"]) / 2, b0, None),
    }
    fig, ax = plt.subplots(figsize=(8, 4.2))
    for name, (s, c0, lay) in conds.items():
        up = s > c0 + 2.5
        y = []
        for k in range(4):
            if k in (1, 2):
                rows = np.flatnonzero(layer == k)
                y.append(up[rows].mean())
            elif lay is not None:
                y.append(lay[k]["n_up"] / lay[k]["n"])
            else:
                y.append(1.0 if k == 0 else 0.0)        # m2: GRNs are the Poisson-driven cells; MN9_L 0 Hz
        ax.plot(range(4), y, "o-", label=name)
    ax.set_xticks(range(4), ["leg sugar GRNs\n(50 on path)", "layer 1\n(27 cells)", "layer 2\n(32 cells)", "MN9 L/R"])
    ax.set_ylabel("fraction of cells above control + 2.5 Hz")
    ax.set_ylim(-0.03, 1.05)
    ax.set_title("Leg sugar to MN9 (seed 12): activity stops between layer 1 and layer 2")
    ax.legend(fontsize=8, loc="upper right")
    fig.tight_layout()
    out = REPO / "docs/media/s12_legsugar_mn9_trace.png"
    fig.savefig(out, dpi=90)
    print(out)


if __name__ == "__main__":
    main()
