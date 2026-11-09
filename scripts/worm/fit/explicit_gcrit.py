"""Where an explicit conductance makes a cell alternate (weki, 9 Nov 2026; toy, read-only diagnosis, NO FIT).

brain.step holds every module's I_pA over the body exchange step (4.0 or 4.5 ms: 8 or 9 NEURON steps of 0.5 ms),
computed from V at the step's start. A module current g (E - V) is then explicit in V. This toy builds the named neuron
on the template worm (Brain(cells=...) still builds the glia, epithelial and vulval-muscle sections; no body, no module
steps, no other neuron), puts
g (E - V_start) on each soma's IClamp per exchange step exactly as brain.step does, and bisects g for the onset of the
battery's alternation rule (vitals.alternation >= ALT_STEPS over 300 steps), or the mods' solver failing on the
swing. One cell per process (NEURON keeps what it builds; a cell built with others may be wired to them). E = -41 mV, the level the egg-laying
current pulled HSN to in seed 1 (measured, night file 01:04).

Falsifier (written before the first run): the full model went unstable at 1.99 nS on HSN from a -17 mV state. If
the toy's HSNL threshold at rest is above 1.99 nS the toy misses what set that onset (the depolarised state's
channels, the neighbours) and its numbers are not used for other cells.

Usage: python scripts/worm/fit/explicit_gcrit.py CELL [E_mV]   (a body-wall muscle by its BWM name, e.g. dBWML22; PBO-5's
E is 0 mV). SEED=<int> builds that sample_worm draw instead of the template. On older code without
vitals.alternation (f8e7699), the 9 Nov 01:40 run used a copy with the function inlined.
"""
from __future__ import annotations

import os
import sys

import numpy as np

from wormemu.brain import DT_MS, Brain, sample_worm
from wormemu.fit import vitals

STEPS, SETTLE_MS = 300, 1000.0
cells = sys.argv[1:2]
E_MV = float(sys.argv[2]) if len(sys.argv) > 2 else -41.0
b = Brain(sample_worm(int(os.environ["SEED"]) if os.environ.get("SEED") else None), cells=cells)
h = b.h
b.reset()
idx = [list(b.cell_names).index(c) for c in cells]


def cap_pF(c):
    hoc = b._baai[c]                                                # a muscle's sections carry BAAIWorm's name
    return sum(seg.area() * seg.cm * 1e-2 for sec in h.allsec() if sec.name().startswith(hoc + "[") for seg in sec)


def soma_pF(k):
    return sum(seg.area() * seg.cm * 1e-2 for seg in b.soma[k])


def settle():
    h.finitialize(-50.0)
    for k in idx:
        b.stim[k].amp = 0.0
    for _ in range(int(SETTLE_MS / DT_MS)):
        h.fadvance()


def run(g_nS, dt_ms):
    """V per exchange step [STEPS, cells] with g (E - V_start) held over each step (g the same on every cell)."""
    settle()
    n_int = int(round(dt_ms / DT_MS))
    V = np.empty((STEPS, len(idx)))
    for s in range(STEPS):
        v = b._read(b._pv)[idx]
        V[s] = v
        for j, k in enumerate(idx):
            b.stim[k].amp = g_nS * (E_MV - v[j]) / 1000.0          # nS x mV = pA -> nA
        for _ in range(n_int):
            h.fadvance()
    return V


def unstable(g, dt, j):
    try:
        V = run(g, dt)
    except RuntimeError:                                            # the mods' solver fails on the blown-up swing
        return True
    return vitals.alternation(V[:, [j]])[0] >= vitals.ALT_STEPS or not np.isfinite(V[:, j]).all()


settle()
rest = b._read(b._pv)[idx]
print(f"E {E_MV} mV, steps {STEPS}, NEURON dt {DT_MS} ms")
for j, c in enumerate(cells):
    C = cap_pF(c)
    row = [f"{c:7s} C {C:6.2f} pF (soma {soma_pF(idx[j]):5.2f}), rest {rest[j]:6.1f} mV"]
    for dt in (4.0, 4.5):
        lo, hi = 0.0, 50.0
        if not unstable(hi, dt, j):
            row.append(f"dt {dt}: stable to {hi} nS")
            continue
        for _ in range(14):
            mid = 0.5 * (lo + hi)
            lo, hi = (lo, mid) if unstable(mid, dt, j) else (mid, hi)
        row.append(f"dt {dt}: g_crit {hi:6.3f} nS (g dt / C {hi * dt / C:5.2f})")
    print("; ".join(row))
