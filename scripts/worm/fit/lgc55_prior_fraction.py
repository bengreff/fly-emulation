"""Fraction of sample_worm draws whose LGC-55 conductance on HSN exceeds the explicit-step threshold (weki, 9 Nov 2026).

Derived, no simulation: g_eff at the first egg = egg_lgc55_g_nS x Hill(egg_uv1_tyr_uM_per_egg; rec_lgc55_ec50_uM,
rec_lgc55_hill); later eggs add tyramine, so egg_lgc55_g_nS itself (full occupancy) is the upper bound. Thresholds
1.22 / 1.31 nS are the template HSNL's at 4.5 / 4.0 ms (scripts/worm/fit/explicit_gcrit.py); a draw's own capacitance
shifts its threshold, which this ignores.
"""
import numpy as np
from wormemu.brain import sample_worm
N = 400
g1, keys = [], ("egg_lgc55_g_nS", "egg_uv1_tyr_uM_per_egg", "rec_lgc55_ec50_uM", "rec_lgc55_hill")
s0 = sample_worm(None)
print("template", {k: s0.v(k) for k in keys})
for s in range(1, N + 1):
    w = sample_worm(s)
    g, tyr, ec, n = (float(w.v(k)) for k in keys)
    g1.append(g * tyr ** n / (tyr ** n + ec ** n))
g1 = np.array(g1)
for th in (1.22, 1.31):
    print(f"N {N}: first-egg g_eff > {th} nS in {np.mean(g1 > th):.3f}; quartiles {np.percentile(g1, [25, 50, 75]).round(3)}")
print("seed 1 g_eff", round(g1[0], 3))
gm = np.array([float(sample_worm(s).v("egg_lgc55_g_nS")) for s in range(1, N + 1)])
print(f"g_max > 1.22 nS (full occupancy, the upper bound) in {np.mean(gm > 1.22):.3f}")
