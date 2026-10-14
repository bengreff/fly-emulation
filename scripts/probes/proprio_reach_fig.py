"""Figure for step R (reach gate): rate at each hop from the lm FeCO afferents to the lm tibia MNs, and the tibia MNs'
distance to threshold, during imposed flexion and extension (brain off, m10f0). Reads proprio_reach.py outputs.

    uv run python scripts/probes/proprio_reach_fig.py runs/s13/proprio/reach_loc docs/media/s13_fly2_reach.png
"""
import json
import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402

C = {"flexing": "#2a78d6", "extending": "#eb6834"}        # reference categorical slots 1 and 2
INK, MUTED, GRID = "#0b0b0b", "#52514e", "#e4e3df"
EXT, FLEX = "trochanterfemur-tibia-pitch +1", "trochanterfemur-tibia-pitch -1"


def hops(r):
    a, loc, p = r["afferent_hz_per_cell"], r["localisation"], r["pools_hz_per_mn"]
    rows = [("hook_flex afferents", a["hook_flex"], f"n {a['hook_flex']['n']}"),
            ("hook_ext afferents", a["hook_ext"], f"n {a['hook_ext']['n']}"),
            ("claw afferents", a["claw"], f"n {a['claw']['n']}")]
    for k, lab in (("first_order", "first-order targets"), (f"premotor {EXT}", "premotor, extensor pool"),
                   (f"premotor {FLEX}", "premotor, flexor pool")):
        v = loc[k]
        rows.append((lab, v["mean_hz"], f"{v['n_active']}/{v['n']} active, {v['n_modulated']} mod."))
    rows += [("tibia extensor MNs", p[EXT], f"n {p[EXT]['n']}"), ("tibia flexor MNs", p[FLEX], f"n {p[FLEX]['n']}")]
    return rows


def main() -> None:
    d, out = Path(sys.argv[1]), Path(sys.argv[2])
    arms = [json.loads((d / f"clamp_lm_g{g}.json").read_text()) for g in (8, 40)]
    ctrl = json.loads((d.parent / "reach" / "clamp_lm_zero.json").read_text())
    fig, ax = plt.subplots(2, 2, figsize=(12, 8.5), gridspec_kw={"height_ratios": [1.3, 1]})
    for c, r in enumerate(arms):
        a = ax[0, c]
        rows = hops(r)
        y = np.arange(len(rows))[::-1]
        for yy, (lab, v, note) in zip(y, rows):
            a.plot([v["flexing"], v["extending"]], [yy, yy], color=GRID, lw=2, zorder=1)
            for b, dy in (("flexing", 0.12), ("extending", -0.12)):
                a.scatter(v[b], yy + dy, s=60, color=C[b], edgecolor="white", linewidth=2, zorder=3)
            a.text(1.02, yy, note, transform=a.get_yaxis_transform(), va="center", fontsize=8, color=MUTED)
        a.set_yticks(y, [x[0] for x in rows], fontsize=9, color=INK)
        a.set_xscale("symlog", linthresh=1.0)
        a.set_xlim(-0.2, 150)
        a.set_xlabel("rate per cell (Hz, symlog)", color=MUTED)
        a.axvline(ctrl["pools_hz_per_mn"][FLEX]["flexing"], color=MUTED, ls=":", lw=1)
        a.set_title(f"afferent gain {r['gain_mv']:g} mV: rate at each hop",
                    fontsize=10, color=INK, loc="left")
        a.grid(axis="x", color=GRID, lw=0.8)
        a.spines[["top", "right"]].set_visible(False)
        g = ax[1, c]
        gap = r["tibia_mn_gap_to_threshold_mv"]
        xs, labs = [], []
        for k, (pool, lab) in enumerate(((EXT, "ext"), (FLEX, "flex"))):
            for i, row in enumerate(gap[pool]):
                x0 = len(xs)
                for b, j, dx in (("flexing", 1, -0.15), ("extending", 2, 0.15)):
                    g.scatter(x0 + dx, row[j], s=40, color=C[b], edgecolor="white", linewidth=1.5, zorder=3)
                xs.append(x0); labs.append(f"{lab[0].upper()}{i + 1}")
        g.set_xticks(xs, labs, fontsize=8, color=MUTED)
        g.set_ylim(0, 20)
        g.set_ylabel("mean gap to threshold (mV)", color=MUTED)
        g.set_title("tibia MNs: mean distance below threshold", fontsize=10, color=INK, loc="left")
        g.grid(axis="y", color=GRID, lw=0.8)
        g.spines[["top", "right"]].set_visible(False)
    h = [plt.Line2D([], [], marker="o", ls="", color=C[b], markersize=8, label=lab)
         for b, lab in (("flexing", "imposed flexion"), ("extending", "imposed extension"))]
    h.append(plt.Line2D([], [], ls=":", color=MUTED, label="flexor MN rate, afferents zeroed"))
    fig.legend(handles=h, loc="upper center", ncol=3, frameon=False, fontsize=9, bbox_to_anchor=(0.5, 0.945))
    fig.suptitle("Step R: leg proprioception does not reach the leg MNs with the brain off\n"
                 "(m10f0, seed 12, lm femur-tibia clamped 0.4 rad at 2 Hz; E = extensor MN, F = flexor MN)",
                 y=0.995, fontsize=11, color=INK)
    fig.tight_layout(rect=(0, 0, 1, 0.91), w_pad=8)
    fig.savefig(out, dpi=110, facecolor="#fcfcfb")
    print(out)


if __name__ == "__main__":
    main()
