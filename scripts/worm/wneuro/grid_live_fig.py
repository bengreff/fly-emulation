"""Figure for grid_live.py: 5-HT the egg-laying organ reads at the vulva, 5-HT MC reads, and MC's SER-7 Gs, four vs bins,
off and on food (runs/worm/wneuro/grid_live_<grid>_<food>.json -> grid_live.png)."""
import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

D = Path(__file__).resolve().parents[3] / "runs" / "worm" / "wneuro"
fig, ax = plt.subplots(1, 3, figsize=(15, 4))
for (g, col), f, ls in [((g, c), f, l) for g, c in (("four", "#888888"), ("bins", "#d1495b"))
                        for f, l in (("0.0", ":"), ("1.02", "-"))]:
    r = json.loads((D / f"grid_live_{g}_{f}.json").read_text())
    t = r["trace"]["t"]
    for a, k in zip(ax, ("vulva_organ", "read_MCL", "MC_gs")):
        a.plot(t, r["trace"][k], ls, color=col, label=f"{g}, food {f}")
for a, ttl, yl in zip(ax, ("5-HT at the vulva (organs_egglaying's read)", "5-HT as MCL reads it", "MCL SER-7 Gs"),
                      ("nM", "nM", "Gs")):
    a.set_title(ttl)
    a.set_xlabel("bio s")
    a.set_ylabel(yl)
ax[0].legend(fontsize=8)
fig.tight_layout()
fig.savefig(D / "grid_live.png", dpi=110)
