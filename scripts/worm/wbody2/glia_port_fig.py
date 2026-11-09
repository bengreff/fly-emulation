"""Figure for the glia port check (runs/worm/wbody2/glia_port_check.json): zero-input ending K+ and check_glia's
clamp recovery under the four forms (glia_k_load leak | channels x glia_v0_window first | settled)."""
import json
import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402

ROOT = Path(__file__).resolve().parents[3]
r = json.loads((ROOT / "runs/worm/wbody2/glia_port_check.json").read_text())
col = {"leak/first": "C0", "leak/settled": "C1", "channels/first": "C2", "channels/settled": "C3"}
fig, ax = plt.subplots(1, 3, figsize=(15, 4.2))
for k, z in r["zero"].items():
    t = np.array(z["trace"]["t_s"])
    ax[0].plot(t, z["trace"]["k_left_mM"], col[k], label=f"{k}: max |dev| {z['max_abs_dev_mM']:.3f} mM")
    ax[0].plot(t, z["trace"]["k_right_mM"], col[k], ls=":", lw=1)
ax[0].axhspan(4.95, 5.05, color="0.85", zorder=0, label="bar: bath 5 mM +/- 0.05")
ax[0].set(xlabel="time (s)", ylabel="ending K+ (mM)", title="zero input (solid left, dotted right)", ylim=(4.5, 6.2))
ax[0].legend(fontsize=7)
for i, sel in ((1, ("leak/first", "leak/settled")), (2, ("channels/first", "channels/settled"))):
    for k in sel:
        c = r["check"][k]
        for tr, ls, lab in ((c["trace_wt"], "-", "wt"), (c["trace_null"], "--", "null")):
            ax[i].plot(tr["t_s"], tr["k_left_mM"], col[k], ls=ls,
                       label=f"{k} {lab}: tau {c[lab]['tau_recovery_s']} s" if True else None)
    ax[i].axhline(10.2, color="k", lw=0.8, ls=":", label="ceiling 10.2 mM")
    ax[i].axvspan(3, 4, color="0.9", zorder=0)
    ax[i].set(xlabel="time (s)", ylabel="left ending K+ (mM)", xlim=(2, 14),
              title="check_glia clamp 3-4 s (bar tau 3.4-4.0 s, null >= 1.24x)")
    ax[i].legend(fontsize=7)
fig.tight_layout()
out = ROOT / "runs/worm/wbody2/glia_port_check.png"
fig.savefig(out, dpi=110)
print(out)
