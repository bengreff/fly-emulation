"""s20 fly2 N30 figure: the two-compartment DLMn after one GF spike (gate runs) and the GF->DLM latency
at the central values and the four (q, rho) bracket corners, against the two measured ranges.

Reads runs/s20/fly2/{gate_passive,gate_spiking,latency,corner_*}.json; writes the figure path given.
Plots measured results only; no fitting.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402

REPO = Path(__file__).resolve().parents[2]
RUN = REPO / "runs/s20/fly2"
AUGUSTIN = (1.36, 1.849)      # spent (F-GJ-3)
RYGLEWSKI = (1.43, 2.27)      # held out until this call (1.85 +/- 0.21 ms, read as SD, mean +/- 2 SD)


def dlm_ab(rep):
    return [(int(i), c) for i, c in rep["trace"].items() if c["type"] == "DLMn a, b"]


def main(out: Path):
    gp, gs = (json.loads((RUN / f"gate_{k}.json").read_text()) for k in ("passive", "spiking"))
    dt = 0.1
    fig, ax = plt.subplots(1, 3, figsize=(15, 4.2))
    for k, (rep, title) in enumerate(((gp, "gate: axon spike disabled"), (gs, "spiking on"))):
        a = ax[k]
        for i, c in dlm_ab(rep)[:1]:
            t = np.arange(len(c["v_trace"])) * dt
            a.plot(t, c["v_trace"], color="C0", label=f"soma (peak {c['v_max'] - c['v_before']:.2f} mV)")
            a.plot(t, c["axon_trace"], color="C3", label=f"axon (peak {c['axon_v_max'] - c['v_before']:.2f} mV)")
            for s in c["spike_steps"]:
                a.axvline(s * dt, color="C3", lw=0.6, ls=":")
            a.axhline(c["v_th"] if c["v_th"] < 0 else -45.0, color="k", lw=0.6, ls="--", label="threshold -45 mV")
            a.axhline(c["v_before"] + 4.71, color="C0", lw=0.6, ls=":", label="rest + 4.71 mV (measured EPSP)")
            a.set_title(f"DLMn a, b cell {i}, {title}\nspikes in window: {len(c['spike_steps'])}", fontsize=9)
        a.set_xlabel("ms after GF kick")
        a.set_ylabel("mV")
        a.legend(fontsize=7, loc="lower right")
    a = ax[2]
    rows = [("central\nq 0.07 rho 1.6", RUN / "latency.json")]
    rows += [(f"q {q}\nrho {r}", RUN / f"corner_q{q}_r{r}.json") for q in ("0.012", "0.15") for r in ("0.13", "25")]
    a.axhspan(*RYGLEWSKI, color="C2", alpha=0.18, label="Ryglewski 2014 (held out)")
    a.axhspan(*AUGUSTIN, color="C1", alpha=0.18, label="Augustin 2017 (spent)")
    for j, (lab, f) in enumerate(rows):
        if not f.exists():
            continue
        d = json.loads(f.read_text())["arms"]["gaps_on"]["types"]["DLMn a, b"]
        m = d["muscle_ms_median"]
        if m is not None:
            a.plot(j, m, "o", color="k")
        a.annotate(f"follow {d['follow_fraction']:.2f}\n{d['spikes_per_window_mean']:.2f} sp/GF",
                   (j, (m if m is not None else 1.25)), textcoords="offset points", xytext=(0, 8),
                   ha="center", fontsize=7)
    a.set_xticks(range(len(rows)), [r[0] for r in rows], fontsize=7)
    a.set_ylim(1.2, 3.0)
    a.set_xlim(-0.6, len(rows) - 0.4)
    a.text(0.02, 0.86, "passive pair (derived): the axon peak crosses\nthreshold only for rho < ~4 at any q in 0.012-0.15",
           transform=a.transAxes, fontsize=7, va="top")
    a.set_ylabel("median GF -> DLM muscle latency (ms)")
    a.set_title("DLMn a, b, gaps on, seed 1, 20 trials", fontsize=9)
    a.legend(fontsize=7, loc="upper right")
    fig.suptitle("N30 two-compartment DLMn (PSI on the axon), m10f + measured NT + measured unitary PSP", fontsize=10)
    fig.tight_layout()
    out.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out, dpi=130)
    print("wrote", out)


if __name__ == "__main__":
    main(Path(sys.argv[1]))
