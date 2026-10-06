"""Figure for the whole-leg compression check: force against strut compression for the model's passive
left middle leg (arms from leg_compression.py), with the measured living-leg stiffness of Oeftger et al.
2026 (13.1 +- 7.97 uN/mm, mean +- SD, n 11) as a line and band. Writes runs/s12/legk/legk.png.

    uv run python scripts/probes/leg_compression_plot.py
"""
from __future__ import annotations

import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402

D = Path(__file__).resolve().parents[2] / "runs/s12/legk"
ARMS = {"m9r": "free tarsus, other legs present", "m9r_locked": "tarsi locked, other legs present",
        "m9r_solo": "free tarsus, other legs removed", "m9r_solo_locked": "tarsi locked, other legs removed"}


def main() -> None:
    fig, axs = plt.subplots(1, 2, figsize=(11, 4))
    x = np.linspace(0, 1.3, 50)
    for ax in axs[:1]:
        ax.fill_between(x, (13.1 - 7.97) * x, (13.1 + 7.97) * x, color="0.6", alpha=0.25,
                        label="measured living leg, mean +- SD")
        ax.plot(x, 13.1 * x, color="k", lw=1.5)
    for arm, lab in ARMS.items():
        f = D / f"{arm}.json"
        if not f.exists():
            continue
        j = json.load(open(f))
        load = [r for r in j["rows"] if not r.get("unloaded")]
        un = [r for r in j["rows"] if r.get("unloaded")][0]
        c = [r["compression_mm"] for r in load]
        F = [r["force_uN"] for r in load]
        line, = axs[0].plot(c, F, "o-", ms=3, label=f"model: {lab}")
        axs[0].plot([c[-1], un["compression_mm"]], [F[-1], 0], ":", color=line.get_color())
        axs[1].plot(F, [r["femur_tibia"] - load[0]["femur_tibia"] for r in load], "o-", ms=3,
                    color=line.get_color(), label=f"femur-tibia, {lab}")
        axs[1].plot(F, [r["coxa_trochanter"] - load[0]["coxa_trochanter"] for r in load], "s--", ms=3,
                    color=line.get_color(), alpha=0.6)
    axs[0].set_xlabel("strut compression, coxa to tarsus5 (mm)")
    axs[0].set_ylabel("force along the strut (uN)")
    axs[0].set_ylim(0, 13)
    axs[0].legend(fontsize=7, loc="upper left")
    axs[0].set_title("Compression (dotted: after 1 s unloaded)", fontsize=9)
    for s, lab in ((-3.3, "measured femur-tibia slope, -3.3 to -5.3 deg/uN"), (-5.3, None)):
        axs[1].plot([0, 2], [0, 2 * s], color="k", lw=1.2, label=lab)
    axs[1].plot([0, 2], [0, 12.0], color="k", lw=1.2, ls="--",
                label="measured coxa-trochanter, +6.0 deg/uN (sign convention unknown)")
    axs[1].set_xlim(0, 4.2)
    axs[1].set_xlabel("force (uN)")
    axs[1].set_ylabel("angle change (deg)")
    axs[1].legend(fontsize=6, loc="lower left")
    axs[1].set_title("Joint angles under load (solid femur-tibia, dashed coxa-trochanter; black measured)", fontsize=9)
    fig.suptitle("Passive left middle leg (m9r body, actuators at zero) against Oeftger et al. 2026 "
                 "(decapitated living flies)", fontsize=9)
    fig.tight_layout()
    fig.savefig(D / "legk.png", dpi=90)


if __name__ == "__main__":
    main()
