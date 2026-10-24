"""s29 (fly2): the viewed figure for a frontier move. Compares a candidate stage's 60 s smoke (smoke_live.py
--rates-out npz + json) with the current frontier's, against the smoke bands of 21 Oct 21:35 and the
resting-rate reference groups of rest_vs_reference.py (single published numbers widened x2, guessed).

    uv run python scripts/probes/s29_smoke_compare_fig.py runs/s29/smk/smoke_m10f5_s12 \
        runs/s29/smk/smoke_m10f5n7_s12 runs/s29/smk/smoke_m10f5s29_s12 runs/s29/smk/s29_smoke_compare.png

Each run argument is a path prefix: <prefix>.json and <prefix>_rates.npz. The first is the reference.
"""
import json
import sys

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

sys.path.insert(0, "src")
from flyemu.connectome import load_tables

*runs, out = sys.argv[1:]
nrn, _ = load_tables()
cc = pd.read_csv("data/model/classes.csv", keep_default_na=False)
circ_of = dict(zip(cc.type, cc.circuit_class))


def load(prefix):
    z = np.load(prefix + "_rates.npz")
    d = json.load(open(prefix + ".json"))
    hz = pd.Series(z["hz"].astype(float), index=z["body_id"])
    return d, hz


data = [load(p) for p in runs]
ids = data[0][1].index
for d, hz in data[1:]:
    assert hz.index.equals(ids), "runs must share the neuron order"
n = nrn.set_index("bodyId").reindex(ids)
t = n["type"].fillna("").astype(str)
circ = t.map(circ_of).fillna("")
# (label, mask, measured low, high) from rest_vs_reference.py; nan = no number
G = [
    ("ORN", t.str.startswith("ORN_"), 1, 30),
    ("uPN (AL_PN)", circ == "AL_PN", 0.4, 8.8),
    ("AL LN", circ == "AL_LN", 1.8, 7.4),
    ("KC", circ == "KC", 0.0, 0.5),
    ("MBON14", t == "MBON14", 6, 24),
    ("P-EN", t.str.startswith("PEN_"), 2.4, 5.4),
    ("DN1a", t == "DN1a", 6, 12),
    ("GRN (gust.)", circ == "sensory_gustatory", 0.0, 3.0),
]
names = [r.split("/")[-1].replace("smoke_", "").replace("_s12", "") for r in runs]

fig, ax = plt.subplots(1, 3, figsize=(17, 5.2), gridspec_kw=dict(width_ratios=[1.5, 1, 0.9]))
w = 0.8 / len(data)
for gi, (lab, m, lo, hi) in enumerate(G):
    if not np.isnan(lo):
        ax[0].add_patch(plt.Rectangle((gi - 0.45, max(lo, 1e-3)), 0.9, hi - max(lo, 1e-3), color="0.88", zorder=0))
    for k, (d, hz) in enumerate(data):
        v = float(hz[m.to_numpy()].mean())
        ax[0].bar(gi - 0.4 + w * (k + 0.5), max(v, 1e-3), w, color=f"C{k}", label=names[k] if gi == 0 else None)
ax[0].set_yscale("log")
ax[0].set_ylim(1e-3, 100)
ax[0].set_xticks(range(len(G)))
ax[0].set_xticklabels([g[0] for g in G], rotation=30, ha="right")
ax[0].set_ylabel("mean rate over 59.5 s (Hz)")
ax[0].set_title("group means; grey = published resting range (x2 widened where single)")
ax[0].legend(fontsize=8)

ref = data[0][1]
pn = (circ == "AL_PN").to_numpy()
for k, (d, hz) in enumerate(data[1:], start=1):
    x, y = ref.to_numpy() + 0.01, hz.to_numpy() + 0.01
    ax[1].scatter(x[~pn], y[~pn], s=2, color=f"C{k}", alpha=0.25, label=f"{names[k]}: other")
    ax[1].scatter(x[pn], y[pn], s=6, color="k" if k == 1 else "m", alpha=0.6, label=f"{names[k]}: AL_PN")
ax[1].plot([0.01, 100], [0.01, 100], "k:", lw=0.8)
ax[1].set_xscale("log")
ax[1].set_yscale("log")
ax[1].set_xlabel(f"{names[0]} rate + 0.01 (Hz)")
ax[1].set_ylabel("candidate rate + 0.01 (Hz)")
ax[1].set_title("per neuron, candidate vs reference")
ax[1].legend(fontsize=7, markerscale=3)

lines = ["smoke bands (21 Oct 21:35):", "whole brain 0.162-0.486 Hz", "active 0.014-0.042", "no runaway, no NaN", ""]
for nm, (d, hz) in zip(names, data):
    r = d["rates"]
    ok = (0.162 <= r["whole_brain_hz"] <= 0.486 and 0.014 <= r["frac_active"] <= 0.042
          and d["runaway_at_ms"] is None and not d["nan_state"])
    lines += [f"{nm}: {r['whole_brain_hz']:.4f} Hz, active {r['frac_active']:.4f}",
              f"   runaway {d['runaway_at_ms']}, NaN {d['nan_state']}, MuJoCo warn {d['mujoco_warnings']}",
              f"   thorax z {d['thorax_z_mm']['final']} mm, wall {d['wall_s']} s -> {'PASS' if ok else 'FAIL'}", ""]
ax[2].axis("off")
ax[2].text(0, 1, "\n".join(lines), va="top", family="monospace", fontsize=8.5)
fig.suptitle("fly2 s29: 60 s smoke S, seed 12, candidate stages vs the m10f frontier")
fig.tight_layout()
fig.savefig(out, dpi=110)
print("wrote", out)
for lab, m, lo, hi in G:
    print(lab, [round(float(hz[m.to_numpy()].mean()), 3) for _, hz in data], (lo, hi))
