"""Figure for item 3 (wbody2, 8 Nov 2026): ring Ca of the isolated intestine, 600 s at dt 0.5 ms, at the defaults and
at the one in-range set that passes intestine_wave_probe.py (not adopted). -> runs/worm/wbody2/intestine_waves.png"""
import json
import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "src"))
from wormemu.mech import organs_intestine as I  # noqa: E402

probe = json.loads((ROOT / "runs/worm/wbody2/intestine_wave_probe.json").read_text())
sets = [("defaults (fail: 1 of 11 waves reach int2)", {})]
sets += [(f"probe set {k + 1} (pass at 0.5 ms; not adopted)", c["values"])
         for k, c in enumerate(probe["confirmed_0p5ms"]) if c["ok"]][:1]
fig, axs = plt.subplots(len(sets), 1, figsize=(12, 3.2 * len(sets)), sharex=True)
for ax, (name, v) in zip(np.atleast_1d(axs), sets):
    q = I.defaults()
    q.update(v)
    t, C, _, _ = I.run_isolated(q, 600.0, 0.5)
    for r in range(1, 10):
        ax.plot(t, C[:, I.RING == r].mean(1) + 0.0 * r, lw=0.8, color=plt.cm.viridis((r - 1) / 8), label=f"ring {r}")
    ax.set_title(name, fontsize=10)
    ax.set_ylabel("Ca (uM)")
np.atleast_1d(axs)[0].legend(ncol=9, fontsize=7, loc="upper right")
np.atleast_1d(axs)[-1].set_xlabel("time (s)")
fig.tight_layout()
out = ROOT / "runs/worm/wbody2/intestine_waves.png"
fig.savefig(out, dpi=110)
print(out)
