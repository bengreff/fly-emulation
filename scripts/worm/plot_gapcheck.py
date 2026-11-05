"""The gap-junction check figure (docs/worm/GAPCHECK.md): the 8-cell AIY chain at 20 nS and dt 0.1 ms, NEURON
(LinearMechanism) against the three Jaxley forms, and the error of each form over time.

usage: plot_gapcheck.py <traces.npz> <check.log> <out.png>
"""
import json, sys
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

z = np.load(sys.argv[1])
rows = [json.loads(l) for l in open(sys.argv[2]) if l.startswith('{"case"')]
DT, NCOMP = 0.1, 3
ref = z["nrn"]
nt = min(ref.shape[1], *(z[k].shape[1] for k in ("ImplicitGap", "Gap", "ExplicitGap")))
t = np.arange(nt) * DT
fig, ax = plt.subplots(1, 3, figsize=(18, 4.8))
for c, col in zip((0, 3, 7), ("C0", "C1", "C2")):
    i = c * NCOMP + 1
    ax[0].plot(t, ref[i, :nt], color=col, lw=2.5, alpha=0.4, label=f"NEURON, cell {c}")
    ax[0].plot(t, z["ImplicitGap"][i, :nt], color=col, lw=1, label=f"ImplicitGap, cell {c}")
    ax[0].plot(t, z["Gap"][i, :nt], color=col, lw=1, ls=":", label=f"Gap (half-implicit), cell {c}")
ax[0].set(xlabel="time (ms)", ylabel="middle compartment v (mV)", title="AIY chain, 20 nS, dt 0.1 ms (a = 2.0)")
ax[0].legend(fontsize=7, ncol=1)
for k, col in (("ImplicitGap", "k"), ("Gap", "C3"), ("ExplicitGap", "C4")):
    d = np.abs(z[k][:, :nt] - ref[:, :nt]).max(axis=0)
    d = np.where(np.isfinite(d), d, 1e30)
    ax[1].semilogy(t, np.maximum(d, 1e-16), color=col, label=k)
ax[1].axhline(0.01, color="grey", ls="--", label="bar B1, 0.01 mV")
ax[1].set(xlabel="time (ms)", ylabel="max |v - v_NEURON| over compartments (mV)", ylim=(1e-16, 1e20),
          title="error against NEURON, same dt")
ax[1].legend(fontsize=8)
for form, mk in (("ImplicitGap", "o"), ("Gap", "s"), ("ExplicitGap", "^")):
    for case, col in (("P", "C0"), ("C", "C1")):
        r = [x for x in rows if x["case"] == case and f"{form}_vs_nrn_mV" in x and x["g_nS"] > 0]
        a = [x["a_per_step"] for x in r]
        e = [min(x[f"{form}_vs_nrn_mV"], 1e20) for x in r]
        ax[2].loglog(a, np.maximum(e, 1e-16), mk, color=col, ms=7, mfc="none" if form != "ImplicitGap" else col,
                     label=f"{form}, {case}")
ax[2].axhline(0.01, color="grey", ls="--")
ax[2].set(xlabel="a = dt g / C per step", ylabel="max error against NEURON (mV)", ylim=(1e-16, 1e20),
          title="every case (errors over 1e20 mV, blow-ups, drawn at 1e20)")
ax[2].legend(fontsize=7, ncol=2)
fig.tight_layout()
fig.savefig(sys.argv[3], dpi=110)
print("wrote", sys.argv[3])
