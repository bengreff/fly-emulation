"""Figures for the ported MetaWorm runs: midline snapshots in the bending plane, centroid path, curvature kymograph.

Usage: metaworm_figs.py RUN [RUN ...]   (RUN = prefix name in runs/worm/metaworm/, e.g. p2 p3_final)
Writes docs/worm/figures/metaworm_<RUN>.png.
"""
from __future__ import annotations

import sys
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))
from wormemu.body import metaworm as mw  # noqa: E402

REPO = Path(__file__).resolve().parents[2]
RUNS = REPO / "runs" / "worm" / "metaworm"
FIG = REPO / "docs" / "worm" / "figures"


def own_plane(P: np.ndarray) -> np.ndarray:
    """Points [n, 3] -> [n, 2] in their own principal plane (the body tumbles in 3D: no gravity, no floor)."""
    c = P - P.mean(0)
    _, _, vt = np.linalg.svd(c, full_matrices=False)
    return c @ vt[:2].T


def figure(name: str):
    rec = mw.load(RUNS / name)
    fr = mw.Frame(rec["meta"], rec["X"][0])
    L = fr.length
    mid = fr.midline(rec["X"])  # [T, n, 3]
    t = rec["t"]
    s, k = fr.curvature(rec["X"])

    fig, ax = plt.subplots(1, 3, figsize=(16, 5))
    snaps = np.linspace(len(t) // 5, len(t) - 1, 8).astype(int)
    for i, j in enumerate(snaps):
        c = plt.cm.viridis(i / (len(snaps) - 1))
        q = own_plane(mid[j]) / L + [0, -0.5 * i]
        ax[0].plot(q[:, 0], q[:, 1], color=c, lw=2, label=f"t={t[j]:.1f}s")
        ax[0].plot(q[0, 0], q[0, 1], "o", color=c, ms=4)
    ax[0].set_aspect("equal")
    ax[0].set_title(f"{name}: midline snapshots (dot = head)\neach in its own bending plane, offset down")
    ax[0].set_xlabel("L")
    ax[0].legend(fontsize=7)
    path = own_plane(np.concatenate([mid.mean(1), mid[:, 0]])) / L
    cen, head = path[: len(t)], path[len(t):]
    ax[1].plot(cen[:, 0], cen[:, 1], "k-", lw=1)
    ax[1].plot(head[:, 0], head[:, 1], "r-", lw=0.5, alpha=0.6, label="head tip")
    ax[1].set_aspect("equal")
    ax[1].set_title("centroid path (black), head path (red),\nin the path's own principal plane (L)")
    ax[1].legend(fontsize=7)
    im = ax[2].imshow(k.T, aspect="auto", origin="lower", extent=[t[0], t[-1], s[0], s[-1]], cmap="RdBu_r",
                      vmin=-np.percentile(np.abs(k), 98), vmax=np.percentile(np.abs(k), 98))
    ax[2].set_xlabel("t (s)")
    ax[2].set_ylabel("s (0 = head)")
    ax[2].set_title("dorsoventral curvature kappa*L (dorsal +)")
    plt.colorbar(im, ax=ax[2])
    fig.tight_layout()
    FIG.mkdir(parents=True, exist_ok=True)
    out = FIG / f"metaworm_{name}.png"
    fig.savefig(out, dpi=90)
    plt.close(fig)
    print(out)


if __name__ == "__main__":
    for n in sys.argv[1:]:
        figure(n)
