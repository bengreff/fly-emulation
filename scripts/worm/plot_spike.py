"""The spike figure: current-clamp fits (train and held-out steps), held-out voltage-clamp I-V against the
population, and the training loss. Reads <fitdir>/fit_<model>.npz/json and eval.npz/json.

usage: plot_spike.py <fitdir> <out.png>
"""
import json, os, sys
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

fitdir, out = sys.argv[1], sys.argv[2]
TRAIN, HELD = [0, 2, 4, 6, 8, 10], [1, 3, 5, 7, 9]
AMPS = np.arange(-15, 36, 5)
ev = json.load(open(os.path.join(fitdir, "eval.json")))
ez = np.load(os.path.join(fitdir, "eval.npz"))
models = [m for m in ("cengen", "pub") if os.path.exists(os.path.join(fitdir, f"fit_{m}.npz"))]
fig = plt.figure(figsize=(16, 4.2 * (len(models) + 1)))
gs = fig.add_gridspec(len(models) + 1, 3)
for r, m in enumerate(models):
    z = np.load(os.path.join(fitdir, f"fit_{m}.npz"))
    j = json.load(open(os.path.join(fitdir, f"fit_{m}.json")))
    t = z["grid"] / 1e3
    nt = min(t.size, z["Vfit"].shape[1], z["Vd"].shape[1])
    t = t[:nt]
    for c, (sel, name) in enumerate(((TRAIN, "train"), (HELD, "held out"))):
        ax = fig.add_subplot(gs[r, c])
        cols = plt.cm.viridis(np.linspace(0, 0.9, len(sel)))
        for k, col in zip(sel, cols):
            ax.plot(t, z["Vd"][k, :nt], color="0.6", lw=0.6)
            ax.plot(t, z["Vfit"][k, :nt], color=col, lw=1.0, label=f"{AMPS[k]:+d} pA ({j['rmse_mV'][str(AMPS[k])]:.1f} mV)")
        ax.set_xlim(0, 8); ax.set_xlabel("time (s)"); ax.set_ylabel("V soma (mV)")
        mean = j["train_mean_rmse_mV"] if c == 0 else j["held_mean_rmse_mV"]
        ax.set_title(f"{m}: {name} steps, mean RMSE {mean:.2f} mV (grey = data)", fontsize=10)
        ax.legend(fontsize=7, loc="upper right")
    ax = fig.add_subplot(gs[r, 2])
    h = np.sqrt(np.array(z["hist"]))
    ax.semilogy(np.nanmin(h, axis=1), color="k", lw=1.2, label="best start")
    ax.semilogy(h, color="0.7", lw=0.4)
    ax.set_xlabel("iteration"); ax.set_ylabel("train RMSE (mV)")
    ax.set_title(f"{m}: training loss, {h.shape[1]} starts (grey) and best (black)", fontsize=10)
for c, (kind, key) in enumerate((("steady state", "ss"), ("peak", "pk"))):
    ax = fig.add_subplot(gs[len(models), c])
    d = ez["iv_ss"] if key == "ss" else ez["iv_peak"]
    ok = d[:, 1] >= 5
    ax.errorbar(d[ok, 0], d[ok, 2], yerr=2 * d[ok, 3] * np.sqrt(d[ok, 1]), fmt="o", color="k", ms=4, capsize=2,
                label="data mean +/- 2 SD (n >= 5)")
    ax.plot(d[~ok, 0], d[~ok, 2], "o", mfc="none", color="k", ms=4, label="data, n < 5 (not scored)")
    for m, col in zip(models, ("C0", "C1")):
        f = ev[m]["vc_dt0.1"]["ss" if key == "ss" else "peak"]["frac_inside"]
        ax.plot(ez["vc_v"], ez[f"{m}_vc_dt0.1_{key}"], "-", color=col, lw=1.5, label=f"{m} fit ({100 * f:.0f}% inside)")
    for e, ls in ((60, ":"), (127, "--")):
        if f"pub_eca{e}_{key}" in ez:
            nm = f"published_eCa{60.0 if e == 60 else 127.59}"
            f = ev[nm]["vc_dt0.1"]["ss" if key == "ss" else "peak"]["frac_inside"]
            ax.plot(ez["vc_v"], ez[f"pub_eca{e}_{key}"], ls, color="0.4", lw=1, label=f"published model, E_Ca {e} ({100 * f:.0f}%)")
    ax.axhline(0, color="0.85", lw=0.5)
    ax.set_xlabel("step voltage (mV)"); ax.set_ylabel("current (pA)")
    ax.set_title(f"held-out voltage clamp, {kind} (blind; bar: >= 80% inside)", fontsize=10)
    ax.legend(fontsize=7)
ax = fig.add_subplot(gs[len(models), 2])
if "vc_t" in ez and models:
    m = models[0]
    I = ez[f"{m}_vc_I"]
    for k in range(0, I.shape[0], 2):
        ax.plot(ez["vc_t"] - 1100, I[k], lw=0.6, color=plt.cm.coolwarm(k / max(1, I.shape[0] - 1)))
    ax.set_xlim(-20, 520); ax.set_xlabel("time from step onset (ms)"); ax.set_ylabel("ionic current (pA)")
    ax.set_title(f"{m}: predicted voltage-clamp currents, -120 to +40 mV", fontsize=10)
fig.suptitle("Spike: AIY multicompartment model (Virtual Worm morphology, Nicoletti 2024 kinetics) fitted to Naudin 2022 "
             "current clamp; voltage clamp predicted blind", fontsize=11)
fig.tight_layout()
fig.savefig(out, dpi=110)
print("saved", out)
