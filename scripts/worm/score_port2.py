"""Scores run port2 (W1_RIM_AFD.md, Q2): B1 match, B2 must-differ, R0 default path unchanged; draws port2.png."""
import glob, json, os, sys
import numpy as np
R = sys.argv[1]
HOME = os.path.expanduser("~/worm-spike")


def pair(n):
    vn = np.load(f"{R}/{n}.npz")["v"]
    vj = np.load(f"{R}/{n}_jx.npy")
    k = min(vn.shape[1], vj.shape[1])
    return vn[:, :k], vj[:, :k]


names = sorted(os.path.basename(f)[:-5] for f in glob.glob(f"{R}/*_dt0.[14].json"))  # configs, not score.json
out, b1 = {"B1": {}}, True
for n in names:
    vn, vj = pair(n)
    rms = np.sqrt(np.mean((vj - vn) ** 2, axis=1))
    ok = bool(np.all(rms <= 0.01) and np.all(np.isfinite(vj)))
    b1 &= ok
    out["B1"][n] = {"worst_rms_mV": float(rms.max()), "max_abs_mV": float(np.abs(vj - vn).max()), "pass": ok,
                    "rest_nrn_mV": round(float(vn[3, int(900 / json.load(open(f"{R}/{n}.json"))["dt"])]), 2)}
lo = np.load(f"{R}/leak_only_dt0.4.npz")["v"]
out["B2"] = {}
for n in names:
    if n.startswith("iso_") and n.endswith("dt0.4"):
        vn = np.load(f"{R}/{n}.npz")["v"]
        eff = float(np.mean(np.sqrt(np.mean((vn - lo) ** 2, axis=1))))
        out["B2"][n[4:-6]] = {"effect_rms_mV": round(eff, 2), "pass": eff >= 1.0}
out["R0"] = {}
for n in ("aiy_pub", "all_test"):
    d = float(np.abs(np.load(f"{R}/r0_{n}_jx.npy") - np.load(f"{HOME}/ref/{n}_jx.npy")).max())
    out["R0"][n] = {"max_abs_mV": d, "pass": d <= 1e-9}
out["pass"] = {"B1": b1, "B2": all(x["pass"] for x in out["B2"].values()), "R0": all(x["pass"] for x in out["R0"].values())}
print(json.dumps(out, indent=1))

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
fig, ax = plt.subplots(1, 3, figsize=(16, 4.6))
vn, vj = pair("rim_pub_dt0.4")
t = np.arange(vn.shape[1]) * 0.4 / 1000
for k in range(vn.shape[0]):
    ax[0].plot(t, vn[k], color="0.6", lw=2.2)
    ax[0].plot(t, vj[k], color="C3", lw=0.7, ls="--")
ax[0].set(xlabel="time (s)", ylabel="V (mV)", title="published RIM model: NEURON (grey) vs Jaxley (red dashed)")
for j, dt in enumerate(("0.4", "0.1")):
    ns = [n for n in names if n.endswith(f"dt{dt}")]
    ax[1].scatter(np.arange(len(ns)) + 0.15 * j, [max(out["B1"][n]["worst_rms_mV"], 1e-16) for n in ns], label=f"dt {dt} ms", s=22)
ax[1].axhline(0.01, color="k", ls=":", label="bar 0.01 mV")
ax[1].set_yscale("log")
ns04 = [n[:-6] for n in names if n.endswith("dt0.4")]
ax[1].set_xticks(range(len(ns04)), ns04, rotation=60, fontsize=7)
ax[1].set(ylabel="worst-sweep RMS, Jaxley - NEURON (mV)", title="B1: match per configuration")
ax[1].legend(fontsize=7)
ch = list(out["B2"])
ax[2].bar(range(len(ch)), [out["B2"][c]["effect_rms_mV"] for c in ch], color="C2")
ax[2].axhline(1.0, color="k", ls=":", label="bar 1 mV")
ax[2].set_xticks(range(len(ch)), ch, rotation=45)
ax[2].set(ylabel="RMS change vs leak only (mV)", title="B2: each channel changes the trace")
ax[2].legend(fontsize=7)
fig.tight_layout()
fig.savefig(f"{R}/port2.png", dpi=110)
