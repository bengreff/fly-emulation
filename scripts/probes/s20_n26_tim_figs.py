"""s20 N26 CRY-TIM refit figures (training targets only; nothing at ZT21, which is held out).

    .venv/bin/python scripts/probes/s20_n26_tim_figs.py   # -> docs/media/s20_n26_tim_{prc,tim}.png
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402

sys.path.insert(0, str(Path(__file__).resolve().parent))
from s20_n26_tim import Organs, tim_params  # noqa: E402
from flyemu.internal_state import TIM_DD, tim_dd  # noqa: E402

R = Path("runs/s20/n26/tim")
OUT = Path("docs/media")
BLUE, ORANGE, GRAY, INK, MUTED = "#2a78d6", "#eb6834", "#a8a7a2", "#0b0b0b", "#52514e"
VARS = {"v1_ctau0.1": "V1 tau_c 0.1 h", "v3_trec0.43": "V3 tau_rec 0.43 h", "v4_noct20": "V4 no CT20 point",
        "v5_tang0.03": "V5 Tang 3%", "v2_ctau2": "V2 tau_c 2 h (fails)"}


def load(name: str) -> dict:
    return json.loads((R / f"{name}.json").read_text())


def params(d: dict) -> dict:
    r = d["result"]
    p = tim_params(**d["fixed"], **d["fitted"], cry_rate_per_lux_h=r["cry_rate_per_lux_h"],
                   tim_kdeg_per_h=r["tim_kdeg_per_h"])
    if d.get("tim_dd"):
        p["tim_dd"] = tuple(tuple(x) for x in d["tim_dd"])
    return p


def style(ax, title):
    ax.set_title(title, fontsize=10, color=INK, loc="left")
    ax.grid(color="#e6e5e0", lw=0.6)
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)
    ax.tick_params(colors=MUTED, labelsize=8)


def prc_fig(pri: dict, var: dict) -> None:
    fig, axs = plt.subplots(1, 3, figsize=(13.5, 4.0))
    ax = axs[0]
    for n, d in var.items():
        y = d["result"]["prc60_full"]
        ct = np.array(sorted(int(k) for k in y)); v = np.array([y[str(c)] for c in ct])
        ax.plot(ct, v, color=ORANGE if n == "v2_ctau2" else GRAY, lw=1.0, ls="--" if n == "v2_ctau2" else "-",
                label=VARS[n] if n == "v2_ctau2" else None)
    ax.plot([], [], color=GRAY, lw=1.0, label="variants V1, V3-V5 (pass)")
    y = pri["result"]["prc60_full"]
    ct = np.array(sorted(int(k) for k in y)); v = np.array([y[str(c)] for c in ct])
    ax.plot(ct, v, color=BLUE, lw=2, marker="o", ms=4, label="model, primary fit")
    ax.errorbar([15], [-4.05], yerr=[0.18], fmt="s", color=INK, ms=7, capsize=3,
                label="Kistenpfennig 2012, CT15 (training)")
    ax.plot([18.5], [0], marker="D", color=INK, ms=7, ls="none", label="measured zero crossing CT18.5 (training)")
    ax.axhline(0, color=MUTED, lw=0.8)
    ax.set_xlabel("pulse time (CT, h; DD)", fontsize=9); ax.set_ylabel("phase shift (h, + advance)", fontsize=9)
    ax.set_xticks(range(0, 25, 3)); ax.legend(fontsize=7, frameon=False, loc="lower left")
    style(ax, "A. DD PRC, 60 min 1000 lux")

    ax = axs[1]
    y = pri["result"]["prc5_full"]
    ct = np.array(sorted(int(k) for k in y)); v = np.array([y[str(c)] for c in ct])
    ax.plot(ct, v, color=BLUE, lw=2, marker="o", ms=4, label="model DD PRC, 5 min 1500 lux")
    ax.errorbar([15], [-3.1], yerr=[0.35], fmt="s", color=INK, ms=7, capsize=3,
                label="Lamba 2014 ZT15 (LD assay, training)")
    ax.plot([15], [pri["result"]["ld15"]], marker="^", color=BLUE, ms=8, ls="none", mec="white",
            label="model, same LD assay")
    ax.axhline(0, color=MUTED, lw=0.8)
    ax.set_xlabel("pulse time (CT, h)", fontsize=9); ax.set_xticks(range(0, 25, 3))
    ax.legend(fontsize=7, frameon=False, loc="upper left")
    style(ax, "B. 5 min pulse (Lamba ZT21 measurement held out)")

    ax = axs[2]
    m = pri["result"]["dd15_by_min"]
    mins = np.array(sorted(float(k) for k in m)); v = np.array([m[k] for k in sorted(m, key=float)])
    ax.plot(mins, v, color=BLUE, lw=2, marker="o", ms=5, label="model, CT15 DD, 1000 lux")
    ax.errorbar([5], [-3.1], yerr=[0.35], fmt="s", color=INK, ms=7, capsize=3, label="Lamba 5 min (LD, y w, 25 C)")
    ax.errorbar([60], [-4.05], yerr=[0.18], fmt="D", color=INK, ms=7, capsize=3,
                label="Kistenpfennig 60 min (DD, w1118, 20 C)")
    old = {5: -0.26, 60: -4.00}
    ax.plot(list(old), list(old.values()), color=ORANGE, lw=1.2, ls="--", marker="x", ms=7,
            label="s10 one-point pull, k = 1 (F-S20-1)")
    ax.set_xscale("log"); ax.set_xticks([1, 5, 15, 30, 60, 120]); ax.set_xticklabels(["1", "5", "15", "30", "60", "120"])
    ax.axhline(0, color=MUTED, lw=0.8)
    ax.set_xlabel("pulse length (min)", fontsize=9); ax.legend(fontsize=7, frameon=False, loc="lower left")
    style(ax, "C. Delay vs pulse length at CT15")
    fig.tight_layout(); fig.savefig(OUT / "s20_n26_tim_prc.png", dpi=130); plt.close(fig)


def tim_fig(pri: dict) -> None:
    p = params(pri)
    fig, axs = plt.subplots(1, 3, figsize=(13.5, 4.0))
    # A: DD - model T against the read profile
    o = Organs(p=p, z=complex(1.0, 0.0), cry=0.0, tim=tim_dd(0.0, p.get("tim_dd")))
    o.step(48 * 3600.0, light_lux=0.0)
    ct, tt = [], []
    for _ in range(24 * 6):
        o.step(600.0, light_lux=0.0); ct.append(o.ct_h); tt.append(o.tim)
    ct = np.array(ct); order = np.argsort(ct)
    ax = axs[0]
    ax.plot(ct[order], np.array(tt)[order], color=BLUE, lw=2, label="model TIM, DD day 3")
    x, y = zip(*TIM_DD)
    ax.plot(x, y, "s", color=INK, ms=6, label="Shafer 2002 Fig. 6D read (s-LNv, DD1)")
    ax.set_xlabel("CT (h)", fontsize=9); ax.set_ylabel("TIM / DD peak", fontsize=9); ax.set_xticks(range(0, 25, 3))
    ax.legend(fontsize=7, frameon=False, loc="upper left")
    style(ax, "A. TIM in DD follows the read profile")
    # B: LD - T and c over the last two entrained days
    o = Organs(p=p)
    ons = []
    for _ in range(20):
        ons.append(o.ct_h)
        o.step(12 * 3600.0, light_lux=1000.0); o.step(12 * 3600.0, light_lux=0.0)
    ons.append(o.ct_h)
    t, T, C = [], [], []
    for i in range(2 * 24 * 6):
        lux = 1000.0 if (i // 72) % 2 == 0 else 0.0
        o.step(600.0, light_lux=lux); t.append((i + 1) / 6.0); T.append(o.tim); C.append(o.cry)
    ax = axs[1]
    for d0 in (0, 24):
        ax.axvspan(d0, d0 + 12, color="#fbf3d5", lw=0)
    ax.plot(t, T, color=BLUE, lw=2, label="TIM")
    ax.plot(t, C, color=ORANGE, lw=1.2, label="active CRY")
    ax.set_xlabel("ZT (h; shaded = lights on, 1000 lux)", fontsize=9); ax.set_xticks(range(0, 49, 6))
    ax.set_xticklabels([str(z % 24) for z in range(0, 49, 6)])
    ax.legend(fontsize=7, frameon=False, loc="center left", bbox_to_anchor=(0.0, 0.55))
    style(ax, "B. 12:12 LD, days 21-22")
    # C: entrainment
    ax = axs[2]
    w = (np.array(ons) + 12.0) % 24.0 - 12.0
    ax.plot(range(len(w)), w, color=BLUE, lw=2, marker="o", ms=4, label="model CT at lights-on")
    ax.axhspan(-2, 2, color="#eaf2fc", lw=0, label="registered band (CT 0 +- 2 h)")
    ax.set_xlabel("LD day (from CT 0 at the first lights-on)", fontsize=9); ax.set_ylabel("CT at lights-on (h)", fontsize=9)
    ax.legend(fontsize=7, frameon=False)
    style(ax, "C. Entrainment from CT 0")
    fig.tight_layout(); fig.savefig(OUT / "s20_n26_tim_tim.png", dpi=130); plt.close(fig)


if __name__ == "__main__":
    pri = load("primary")
    var = {n: load(n) for n in VARS}
    prc_fig(pri, var)
    tim_fig(pri)
    print("wrote", OUT / "s20_n26_tim_prc.png", OUT / "s20_n26_tim_tim.png")
