"""Figure for probe_hsn_vm2.json: 5-HT at the vm2 receptor against HSN's release rate, with SER-7 and SER-1 EC50s.

Left: far field (the pool at HSNL's bin), the template geometry's read, and the 512-point geometry box (median and max).
Right: at the template release (1e5 molecules/s per unit drive), C over the box against the two strongest coordinates.

Usage: python plot_hsn_vm2.py -> runs/worm/wneuro/probe_hsn_vm2.png
"""
from __future__ import annotations

import json
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
from scipy.stats import qmc  # noqa: E402

ROOT = Path(__file__).resolve().parents[3]
r = json.loads((ROOT / "runs/worm/wneuro/probe_hsn_vm2.json").read_text())
rows = r["by_release"]
rel = np.array([x["release"] for x in rows])
e7, e1 = r["ec50_ser7_nM"], r["ec50_ser1_nM"]

fig, ax = plt.subplots(1, 2, figsize=(12, 4.6))
a = ax[0]
a.loglog(rel, [x["far_nM"] for x in rows], "k-", label="far field (pool, bins)")
a.loglog(rel, [x["C_template_nM"] for x in rows], "b-o", ms=3, label="template geometry")
a.loglog(rel, [x["C_box_median_nM"] for x in rows], "g--", label="geometry box median")
a.loglog(rel, [x["C_box_max_nM"] for x in rows], "g-", label="geometry box max")
a.axhline(e7, color="r", ls=":", label=f"SER-7 EC50 {e7:g} nM")
a.axhline(e1, color="m", ls=":", label=f"SER-1 EC50 {e1:g} nM")
a.axvline(1e5, color="0.6", lw=0.8)
a.set_xlabel("ma_release_per_s (molecules/s per unit drive)")
a.set_ylabel("5-HT at the vm2 receptor, nM (steady upper bound)")
a.set_title("HSN onto vm2: near field over its bounded gaps")
a.legend(fontsize=7, loc="upper left")

# rebuild the same Sobol points to colour the template-release box
keys = list(r["template_geometry"])
U = qmc.Sobol(len(keys), scramble=True, seed=0).random(512)
t = next(x for x in rows if np.isclose(x["release"], 1e5))
C = np.array(t["C_box"])
ir, ia = keys.index("hsn_vm2_site_receptor_um"), keys.index("ecs_alpha")
rr = 0.02 * (1.0 / 0.02) ** U[:, ir]
al = 0.09 * (1.0 / 0.09) ** U[:, ia]
b = ax[1]
sc = b.scatter(rr, al, c=np.log10(C), s=10, cmap="viridis")
hit = C >= e7
b.scatter(rr[hit], al[hit], facecolors="none", edgecolors="r", s=40, label=f"reaches SER-7 ({hit.sum()} of 512)")
b.set_xscale("log")
b.set_yscale("log")
b.set_xlabel("hsn_vm2_site_receptor_um (guessed, 0.02-1)")
b.set_ylabel("ecs_alpha (guessed, 0.09-1)")
b.set_title("template release 1e5: geometry box, colour log10 C (nM)")
plt.colorbar(sc, ax=b)
b.legend(fontsize=7, loc="upper right")
fig.tight_layout()
out = ROOT / "runs/worm/wneuro/probe_hsn_vm2.png"
fig.savefig(out, dpi=110)
print(out)
