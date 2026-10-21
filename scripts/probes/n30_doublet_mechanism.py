"""N30 doublet diagnosis (fly2, 21 Oct; diagnostic only, nothing adopted): why one PSI spike gives the DLMn axon
two spikes. A replica of lif.py's two-compartment update for one listed cell with one axon input (voltages
relative to rest; threshold 7 mV, reset to rest, refractory 2 ms, tau_s 5 ms, dt 0.1 ms, as DLMn under m10f),
the input weight set so the passive soma peak is the measured 4.71 mV (as `_unitary_psp_weights`).

Arms (each changes one thing):
  base        as built
  no_back     the axon does not see the soma (kappa_a * Vs dropped from the axon's target): ping-pong test
  cut_syn     the synaptic current is removed at the first axon spike: synaptic-tail test
  t_ref scan  the smallest refractory period that gives one spike
  tau_s scan  the largest synaptic decay that gives one spike (weight recalibrated at each)
  ahp scan    the smallest reset below rest (an AHP stand-in) that gives one spike at t_ref 2
and the decomposition of the axon's target potential when the refractory period ends:
  syn part  = I_a / (1 + kappa_a),  soma part = kappa_a Vs / (1 + kappa_a).

    .venv/bin/python scripts/probes/n30_doublet_mechanism.py
"""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
DT, GAP, PSP = 0.1, 7.0, 4.71


def soma_peak_per_unit(q, rho, tau_m, tau_s):
    ka, ks = rho / q, rho / (1.0 - q)
    dv, da, ds = np.exp(-DT / tau_m), np.exp(-DT * (1.0 + ka) / tau_m), np.exp(-DT / tau_s)
    i, va, vs, peak = 1.0, 0.0, 0.0, 0.0
    for _ in range(int(200 / DT)):
        vinf = (i + ka * vs) / (1.0 + ka)
        va, vs = vinf + (va - vinf) * da, vs * dv + ks * (va - vs) * (1.0 - dv)
        peak = max(peak, vs)
        i *= ds
    return peak


def run(q=0.07, rho=1.6, tau_m=20.0, tau_s=5.0, t_ref=2.0, v_reset=0.0, back=True, cut_syn=False,
        t_end=40.0):
    w = PSP / soma_peak_per_unit(q, rho, tau_m, tau_s)
    ka, ks = rho / q, rho / (1.0 - q)
    dv, da, ds = np.exp(-DT / tau_m), np.exp(-DT * (1.0 + ka) / tau_m), np.exp(-DT / tau_s)
    i, va, vs, ref_until = 0.0, 0.0, 0.0, -1.0
    spikes, decomp, tr = [], None, []
    for k in range(int(t_end / DT)):
        t = k * DT
        i = i * ds + (w if k == 0 else 0.0)
        vinf = (i + (ka * vs if back else 0.0)) / (1.0 + ka)
        va, vs = vinf + (va - vinf) * da, vs * dv + ks * (va - vs) * (1.0 - dv)
        if spikes and decomp is None and t >= ref_until:
            decomp = {"t_ms": round(t, 2), "syn_part_mv": i / (1.0 + ka),
                      "soma_part_mv": (ka * vs if back else 0.0) / (1.0 + ka), "vs_mv": vs}
        if t < ref_until:
            va = v_reset
        elif va >= GAP:
            spikes.append(round(t, 2))
            va, ref_until = v_reset, t + t_ref
            if cut_syn:
                i = 0.0
        tr.append((t, vs, va, i / (1.0 + ka)))
    return {"spikes": spikes, "n": len(spikes), "w": w, "decomp": decomp, "trace": np.array(tr)}


def smallest(f, grid):
    for x in grid:
        if f(x) == 1:
            return float(x)
    return None


def main() -> None:
    sets = {"registered (q 0.07, rho 1.6)": (0.07, 1.6), "option B class (q 0.104, rho 3.80)": (0.104, 3.80),
            "option B MN5 L (q 0.156, rho 2.03)": (0.156, 2.03), "corner (q 0.012, rho 0.13)": (0.012, 0.13)}
    out = {}
    for name, (q, rho) in sets.items():
        r = {"base": run(q, rho), "no_back": run(q, rho, back=False), "cut_syn": run(q, rho, cut_syn=True)}
        row = {k: {"n": v["n"], "spikes_ms": v["spikes"]} for k, v in r.items()}
        row["decomp_at_ref_end"] = r["base"]["decomp"]
        row["min_t_ref_ms"] = smallest(lambda x: run(q, rho, t_ref=x)["n"], np.arange(2.0, 15.01, 0.1))
        row["max_tau_s_ms"] = next((float(x) for x in np.arange(5.0, 0.19, -0.1)
                                    if run(q, rho, tau_s=x)["n"] == 1), None)
        row["min_ahp_mv"] = smallest(lambda x: run(q, rho, v_reset=-x)["n"], np.arange(0.0, 40.01, 0.5))
        row["tau_m_4.4"] = {"n": run(q, rho, tau_m=4.4)["n"], "spikes_ms": run(q, rho, tau_m=4.4)["spikes"]}
        out[name] = row
        print(name, json.dumps(row, default=float), flush=True)
    p = ROOT / "runs" / "s21" / "n30_doublet_mechanism.json"
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(out, indent=1, default=float))
    figure(ROOT / "docs" / "media" / "s21_fly2_n30_doublet.png")


def figure(path: Path) -> None:
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    fig, axs = plt.subplots(1, 3, figsize=(15, 4.2), sharey=True)
    for ax, (title, kw) in zip(axs, (("as built (q 0.07, rho 1.6)", {}),
                                     ("axon blind to the soma (no ping-pong)", {"back": False}),
                                     ("synaptic current cut at the first spike", {"cut_syn": True}))):
        r = run(**kw)
        t, vs, va, syn = r["trace"].T
        ax.plot(t, va, color="#c0392b", lw=1.2, label="axon V")
        ax.plot(t, vs, color="#2471a3", lw=1.2, label="soma V")
        ax.plot(t, syn, color="#7f8c8d", lw=1.0, ls="--", label="axon target from the synapse alone")
        ax.axhline(GAP, color="k", lw=0.6, ls=":", label="threshold (7 mV)")
        for s in r["spikes"]:
            ax.axvline(s, color="#c0392b", lw=0.6, alpha=0.5)
        ax.set_xlim(0, 15)
        ax.set_title(f"{title}: {r['n']} spike(s)", fontsize=9)
        ax.set_xlabel("ms after the PSI EPSC starts")
    axs[0].set_ylabel("mV above rest")
    axs[0].legend(fontsize=7)
    fig.suptitle("N30 doublet: pair replica (tau_m 20, tau_s 5, t_ref 2, reset to rest, soma peak 4.71 mV)",
                 fontsize=10)
    fig.tight_layout()
    fig.savefig(path, dpi=130)


if __name__ == "__main__":
    main()
