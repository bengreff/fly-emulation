"""Figures and the touch effect for the brain.py runs (docs/worm/BRAIN_PORT.md section 3).

    python plot_brain_runs.py RUN_DIR [NOSTIM_DIR]

Writes RUN_DIR/traces.png. With the matching no-stimulus run, also writes RUN_DIR/touch_effect.json: per neuron the
largest |V(stim) - V(no stim)| over 2-4 s (runs are deterministic, so this is the touch input's effect alone).
"""
import json
import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

TOUCH = ["ALML", "ALMR", "AVM", "PLML", "PLMR"]
SHOW = ["PLML", "ALML", "AVAL", "AVBL", "AVDL", "PVCL", "DVA", "RIML", "AIYL", "AWCL", "VB05", "DA05"]
MUSC = ["dBWML1", "dBWML9", "dBWML17", "dBWMR1", "dBWMR9", "dBWMR17", "vBWML1", "vBWML9", "vBWML17", "vBWMR1",
        "vBWMR9", "vBWMR17"]


def main():
    d = Path(sys.argv[1])
    r, s = np.load(d / "run.npz"), json.loads((d / "summary.json").read_text())
    names, V, mus = list(r["names"]), r["V"], r["is_muscle"]
    t = np.arange(V.shape[1]) / 1000.0 + 0.001
    ix = {n: i for i, n in enumerate(names)}
    neur = np.where(~mus)[0]
    nostim = Path(sys.argv[2]) if len(sys.argv) > 2 else None
    n_pan = 4 if nostim else 3
    fig, ax = plt.subplots(n_pan, 1, figsize=(11, 3.2 * n_pan + 2.4),
                           gridspec_kw=dict(height_ratios=[2.2] + [1] * (n_pan - 1)))
    order = neur[np.argsort(V[neur, 1000:2000].mean(1))]
    im = ax[0].imshow(V[order], aspect="auto", cmap="RdBu_r", vmin=-80, vmax=40,
                      extent=[0, t[-1], len(order), 0], interpolation="nearest")
    for x in (2, 4):
        ax[0].axvline(x, color="k", lw=0.8, ls="--")
    fig.colorbar(im, ax=ax[0], label="soma V (mV)", pad=0.01)
    ax[0].set_ylabel("302 neurons (sorted by mean V 1-2 s)")
    tg = s["toggles"]
    ax[0].set_title(f"{d.name}: literature_overrides={tg['literature_overrides']}, wiring={tg['wiring']}, "
                    f"layers off; +20 pA touch neurons 2-4 s\n{s['above_m20_at_6s']} neurons above -20 mV at 6 s; "
                    f"{s['wall_s_per_bio_s']} s wall per bio-s (measured)", fontsize=10)
    for n in SHOW:
        ax[1].plot(t, V[ix[n]], lw=0.8, label=n)
    ax[1].set_ylabel("V (mV)")
    ax[1].legend(ncol=6, fontsize=7, loc="lower center")
    for n in MUSC:
        ax[2].plot(t, V[ix[n]], lw=0.8, label=n)
    ax[2].set_ylabel("muscle V (mV)")
    ax[2].legend(ncol=6, fontsize=7, loc="lower right")
    if nostim:
        r0 = np.load(nostim / "run.npz")
        assert list(r0["names"]) == names
        dV = V - r0["V"]
        eff = np.abs(dV[:, 2000:4000]).max(1)
        other = [i for i in neur if names[i] not in TOUCH]
        top = sorted(other, key=lambda i: -eff[i])[:10]
        out = dict(run=d.name, n_neurons_moved_1mV=int((eff[other] >= 1.0).sum()),
                   n_neurons_moved_5mV=int((eff[other] >= 5.0).sum()),
                   n_muscles_moved_1mV=int((eff[mus] >= 1.0).sum()),
                   top10=[[names[i], round(float(eff[i]), 2)] for i in top],
                   touch_cells=[[n, round(float(eff[ix[n]]), 2)] for n in TOUCH])
        (d / "touch_effect.json").write_text(json.dumps(out, indent=1))
        print(json.dumps(out))
        for i in top[:8]:
            ax[3].plot(t, dV[i], lw=0.8, label=names[i])
        ax[3].set_ylabel("V(stim) - V(no stim) (mV)")
        ax[3].set_title(f"touch effect: {out['n_neurons_moved_1mV']} unstimulated neurons move >= 1 mV "
                        f"({out['n_neurons_moved_5mV']} >= 5 mV), {out['n_muscles_moved_1mV']} muscles", fontsize=9)
        ax[3].legend(ncol=4, fontsize=7, loc="upper right")
    ax[-1].set_xlabel("time (s)")
    for a in ax[1:]:
        a.set_xlim(0, t[-1])
    fig.tight_layout()
    fig.savefig(d / "traces.png", dpi=90)


if __name__ == "__main__":
    main()
