"""Which current drives a cell outside the reversal bounds (weki, 9 Nov 2026; read-only diagnosis, NO FIT).

Runs one battery condition (`vitals.run`, the code on PYTHONPATH) and records, for the named cells, at every body
exchange step: V at the step's start and end, and each current brain.step holds fixed over the step (every
mechanism's I_pA, the Layers' sensory, modulator and homeostatic currents, extra_pA). A current computed from V at the
step's start and held for the step is explicit; for a conductance g on a cell of capacitance C over a step dt it
alternates in sign every step once g dt / C passes about 2 (derived: the explicit-Euler bound). Prints, per current,
its range and its correlation with V's step-to-step alternation after the onset.

Usage: python scripts/worm/fit/cell_current_diag.py COND SECONDS OUTDIR SEED CELL [CELL ...]
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np

from wormemu import brain as B
from wormemu.fit import vitals

cond, secs, out, seed, cells = sys.argv[1], float(sys.argv[2]), Path(sys.argv[3]), int(sys.argv[4]), sys.argv[5:]
out.mkdir(parents=True, exist_ok=True)
rec = {"t_ms": [], "v0": [], "v1": []}
_step = B.Brain.step


def step(self, obs=None, dt_ms=1.0):
    if not hasattr(self, "_weki_idx"):
        self._weki_idx = np.array([list(self.cell_names).index(c) for c in cells], int)
        L = self.layers
        for name in ("sensory_current", "modulator_current", "homeostatic_current"):
            f = getattr(L, name)

            def wrap(*a, _f=f, _n=name, **k):
                x = _f(*a, **k)
                rec.setdefault(_n, []).append(np.asarray(x, float)[self._weki_idx] if np.ndim(x) else
                                              np.full(len(cells), float(x)))
                return x
            setattr(L, name, wrap)
        for m in self.mechs:
            f = m.step

            def wrap_m(ctx, dt, _f=f, _n=type(m).__module__.split(".")[-1] + "." + type(m).__name__):
                r = _f(ctx, dt)
                x = r.get("I_pA") if isinstance(r, dict) else None
                rec.setdefault("mech:" + _n, []).append(np.zeros(len(cells)) if x is None else
                                                        np.asarray(x, float)[self._weki_idx])
                return r
            m.step = wrap_m
    idx = self._weki_idx
    rec["t_ms"].append(self.t)
    rec["v0"].append(self._read(self._pv)[idx])
    rec["extra_pA"] = rec.get("extra_pA", []) + [np.asarray(self.extra_pA, float)[idx] if np.ndim(self.extra_pA)
                                                  else np.full(len(cells), float(self.extra_pA))]
    r = _step(self, obs, dt_ms)
    rec["v1"].append(self._read(self._pv)[idx])
    return r


B.Brain.step = step
res = vitals.run(None, cond, secs, out, seed=seed)
arr = {k: np.asarray(v, float) for k, v in rec.items()}
np.savez_compressed(out / "currents.npz", cells=np.array(cells), **{k.replace(":", "__"): v for k, v in arr.items()})
print("physical", res["physicality"]["physical"], "worst", res["physicality"].get("v_out_worst"))
v = arr["v0"]
lo = np.flatnonzero((v < res["physicality"]["E_lo_mV"] - 1).any(axis=1))
print("steps", len(v), "first out-of-bounds step", (lo[0], arr["t_ms"][lo[0]]) if len(lo) else None)
alt = np.sign(np.diff(v, axis=0))
for j, c in enumerate(cells):
    w = slice(lo[0], None) if len(lo) else slice(None)
    flips = float(np.mean(alt[w][1:, j] * alt[w][:-1, j] < 0)) if len(lo) else float("nan")
    print(f"{c}: V range after onset {v[w, j].min():.1f} to {v[w, j].max():.1f} mV; dV sign flips every step "
          f"{100 * flips:.0f} % of steps")
    for k, x in arr.items():
        if k in ("t_ms", "v0", "v1") or x.ndim != 2:
            continue
        xs = x[w, j]
        if not np.any(xs):
            continue
        cc = np.corrcoef(xs, v[w, j])[0, 1] if np.std(xs) > 0 and np.std(v[w, j]) > 0 else float("nan")
        print(f"   {k:40s} {xs.min():10.2f} to {xs.max():10.2f} pA  corr with V {cc:+.2f}")
