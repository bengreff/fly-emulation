"""MN pool rasters for the bypass assay (s13): one panel per S2/S3 run, leg MN pools (rows, grouped by leg) x time,
colour = pool rate in 1 ms bins smoothed over 10 ms. Optionally, a chain run (bypass_s3_chain.py traces) adds the
oscillator cells' membrane potential for one neuromere underneath. Look at this before calling any pass.

    uv run python scripts/probes/bypass_rasters.py runs/s13/bypass/s2/s2_DNg100_40mv_traces.npz ... --out x.png \
        [--chain runs/s13/bypass/s3/chain_A_25mv_traces.npz ... --seg T2L]
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402

LEG_ORDER = ("lf", "lm", "lh", "rf", "rm", "rh")
CELL_COLOURS = {"E1": "#0072B2", "E2": "#D55E00", "I1": "#009E73", "A007": "#CC79A7"}   # Okabe-Ito, validated


def override_text(r: dict) -> str:
    """The run's overrides for a panel title; long lists (s16: one per class) are summarised."""
    ov = r.get("overrides", {})
    if len(ov) > 3:
        return f"{len(ov)} overrides (values {', '.join(sorted({f'{v:g}' for v in ov.values()}))})"
    return ", ".join(f"{k}={v:g}" for k, v in ov.items()) or "no overrides"


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("traces", nargs="*")
    ap.add_argument("--out", required=True)
    ap.add_argument("--chain", action="append", default=[])
    ap.add_argument("--seg", default="T2L")
    ap.add_argument("--t0", type=float, default=200.0)
    ap.add_argument("--t1", type=float, default=1300.0)
    a = ap.parse_args()
    n = len(a.traces) + len(a.chain)
    fig, axs = plt.subplots(n, 1, figsize=(11, 2.6 * n), squeeze=False)
    for ax, f in zip(axs[:, 0], a.traces):
        z = np.load(f)
        names = [str(x) for x in z["pool_names"]]
        leg = [nm[:2] if nm[:2] in LEG_ORDER else nm.split()[0] for nm in names]
        order = sorted(range(len(names)), key=lambda i: (LEG_ORDER.index(leg[i]) if leg[i] in LEG_ORDER else 9, names[i]))
        pr = z["pool_rate"][:, order].astype(float)
        k = np.ones(10) / 10
        pr = np.array([np.convolve(pr[:, i], k, mode="same") for i in range(pr.shape[1])])
        i0, i1 = int(a.t0), min(int(a.t1), pr.shape[1])
        im = ax.imshow(pr[:, i0:i1], aspect="auto", cmap="Blues", interpolation="nearest",
                       extent=(i0, i1, pr.shape[0], 0), vmin=0, vmax=max(pr[:, i0:i1].max(), 1e-3))
        j = Path(f.replace("_traces.npz", ".json"))
        title = Path(f).stem
        if j.exists():
            r = json.loads(j.read_text())
            title = (f"{r['type']} {r['drive_mv']:g} mV, {override_text(r)}"
                     f"  |  MN {r['rates_hz']['leg_mn_drive']} Hz, rhythmic pools {len(r['rhythmic_pools'])}, "
                     f"alternating {len(r['alternating_pools'])}  ->  {'PASS' if r['passes'] else 'fail'}")
        ax.set_title(title, fontsize=8, loc="left")
        bounds = [0] + [sum(1 for i in order if leg[i] == lg) for lg in LEG_ORDER]
        ticks = np.cumsum(bounds)
        for t in ticks[1:-1]:
            ax.axhline(t, color="#888888", lw=0.5)
        ax.set_yticks([(ticks[i] + ticks[i + 1]) / 2 for i in range(6)], LEG_ORDER, fontsize=7)
        ax.tick_params(axis="x", labelsize=7)
        ax.axvline(300, color="#444444", lw=0.8, ls="--")
        cb = fig.colorbar(im, ax=ax, pad=0.01, fraction=0.02)
        cb.set_label("pool spikes / ms", fontsize=7); cb.ax.tick_params(labelsize=6)
    for ax, f in zip(axs[len(a.traces):, 0], a.chain):
        z = np.load(f)
        lab = [str(x) for x in z["labels"]]
        V = z["V"]
        for i, nm in enumerate(lab):
            role, sg = nm.split()
            if sg == a.seg and role in CELL_COLOURS:
                ax.plot(np.arange(V.shape[0]), V[:, i], color=CELL_COLOURS[role], lw=1.2, label=role)
        ax.axhline(-45, color="#888888", lw=0.6, ls=":"); ax.text(2, -44.6, "threshold", fontsize=6, color="#555555")
        ax.set_ylabel("V (mV, 1 ms mean)", fontsize=7)
        j = Path(f.replace("_traces.npz", ".json"))
        ovs = ""
        if j.exists():
            r = json.loads(j.read_text())
            ovs = f"{r['type']} {r['drive_mv']:g} mV, {override_text(r)}, DN {r['stim_hz']} Hz"
        ax.set_title(f"oscillator cells, {a.seg}: {ovs} ({Path(f).stem})", fontsize=8, loc="left")
        ax.legend(fontsize=7, frameon=False, ncol=4, loc="upper right")
        ax.tick_params(labelsize=7)
        for s_ in ("top", "right"):
            ax.spines[s_].set_visible(False)
    axs[-1, 0].set_xlabel("time (ms)", fontsize=7)
    fig.tight_layout()
    fig.savefig(a.out, dpi=110)
    print(a.out)


if __name__ == "__main__":
    main()
