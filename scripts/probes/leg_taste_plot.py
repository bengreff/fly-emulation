"""Sheet for `leg_taste_dose.py` runs: per-type drive and rate against sucrose, switch 0 and 1,
with Ling et al. 2014's tarsal sugar GRN rate at 100 mM (about 50-55 Hz, secondary read) and the
tarsus-5 contact fraction per leg.

    uv run python scripts/probes/leg_taste_plot.py [--dir runs/s12/legtaste]
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
SHOW = ("LgLG4", "LgAG2", "WG2", "LgAG1", "LgLG1a", "LgLG3")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dir", default=str(REPO / "runs" / "s12" / "legtaste"))
    ap.add_argument("--seed", type=int, default=12)
    a = ap.parse_args()
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    d = Path(a.dir)
    R = {}
    for f in sorted(d.glob(f"legtaste_src*_c*_s{a.seed}.json")):
        J = json.loads(f.read_text()); R[(J["source"], J["conc_M"])] = J
    fig, ax = plt.subplots(1, 4, figsize=(19, 4.2))
    for src, ls in ((0, ":"), (1, "-")):
        cs = sorted(c for s, c in R if s == src)
        for i, ty in enumerate(SHOW):
            col = f"C{i}"
            ax[0].plot(cs, [R[(src, c)]["by_type"][ty]["drive_max_mv"] for c in cs], ls, marker="o", color=col,
                       label=ty if src == 1 else None)
            ax[1].plot(cs, [R[(src, c)]["by_type"][ty]["hz_mean"] for c in cs], ls, marker="o", color=col)
            ax[2].plot(cs, [R[(src, c)]["by_type"][ty].get("hz_per_contact_s") or float("nan") for c in cs], ls, marker="o", color=col)
    ax[0].axhline(7.0, color="k", lw=0.8, ls="--", label="threshold (7 mV above rest)")
    for k in (1, 2):
        ax[k].axhspan(25, 110, xmin=0, xmax=1, color="tab:green", alpha=0.08)
        ax[k].plot([0.1], [52.5], "k*", ms=12, label="Ling 2014, 100 mM (secondary)" if k == 1 else None)
    ax[0].set_title("max drive (mV); dotted switch 0, solid switch 1"); ax[1].set_title("mean rate over all cells (Hz)")
    ax[2].set_title("rate per second of own-leg tarsus contact (Hz)")
    for k in range(3):
        ax[k].set_xlabel("sucrose (M)")
    ax[0].legend(fontsize=7); ax[1].legend(fontsize=7)
    J = R.get((1, 0.1)) or next(iter(R.values()))
    tf = J.get("tarsus5_contact_frac", {})
    ax[3].bar(list(tf), list(tf.values()), color="tab:gray")
    ax[3].set_ylim(0, 1); ax[3].set_title("tarsus 5 contact fraction, 100-400 ms (switch 1, 100 mM)")
    fig.suptitle(f"m9f leg/wing taste GRNs on a sucrose patch, seed {a.seed} "
                 "(green band: pre-registered 25-110 Hz)")
    fig.tight_layout(); fig.savefig(d / "leg_taste.png", dpi=85); plt.close(fig)
    print(d / "leg_taste.png")


if __name__ == "__main__":
    main()
