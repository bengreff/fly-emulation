"""Figure for implicit_g_check (inbox 01:45): per term, the small-g response (dV = V(g) - V(0), 0.5 nS) under the
reference (explicit at 0.5 ms), explicit and implicit at 4.5 ms; and V at the top of the range under both forms.

Usage: python implicit_g_fig.py RUNDIR OUT.png
"""
import json
import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402

TERMS = {"lgc55": ("LGC-55 on HSNL", 5.0), "vmcat": ("vm cation on vm1 (first vm muscle)", 14.0),
         "pbo5": ("PBO-5/6 on dBWML22", 20.0)}
T_ON = 999.0


def load(d, term, g, form, dt):
    x = json.loads((Path(d) / f"{term}_g{g:g}_{form}_dt{dt:g}.json").read_text())
    return np.array(x["t_ms"]), np.array(x["v_mV"], float)[:, 0]


def main():
    d, out = sys.argv[1], sys.argv[2]
    fig, ax = plt.subplots(3, 2, figsize=(12, 9))
    for r, (term, (name, gtop)) in enumerate(TERMS.items()):
        a = ax[r, 0]
        for form, dt, c, lab in (("explicit", 0.5, "k", "reference: explicit, 0.5 ms step"),
                                 ("explicit", 4.5, "tab:red", "explicit, 4.5 ms (old)"),
                                 ("implicit", 4.5, "tab:blue", "implicit, 4.5 ms (fix)")):
            t, v = load(d, term, 0.5, form, dt)
            _, z = load(d, term, 0.0, form, dt)
            a.plot((t - T_ON) / 1000.0, v - z, c, lw=1.0 if c == "k" else 0.8, label=lab,
                   ls="-" if c != "tab:blue" else "--")
        a.set_xlim(-0.05, 0.4)
        a.set_ylabel("dV (mV)")
        a.set_title(f"{name}: 0.5 nS on at 0, response")
        if r == 0:
            a.legend(fontsize=8)
        a = ax[r, 1]
        for form, c in (("explicit", "tab:red"), ("implicit", "tab:blue")):
            t, v = load(d, term, gtop, form, 4.5)
            a.plot((t - T_ON) / 1000.0, np.clip(v, -150, 100), c, lw=0.8, label=f"{form}, 4.5 ms")
        a.set_xlim(-0.05, 0.6)
        a.set_ylim(-155, 105)
        a.set_ylabel("V (mV, clipped to -150..100)")
        a.set_title(f"{name}: {gtop:g} nS (top of range or 2x), V")
        if r == 0:
            a.legend(fontsize=8)
    for a in ax[-1]:
        a.set_xlabel("time from g on (s)")
    fig.suptitle("Organ conductances: explicit current vs NEURON point process (implicit), wbody2 9 Nov 2026")
    fig.tight_layout()
    fig.savefig(out, dpi=110)


if __name__ == "__main__":
    main()
