"""Shared pieces of the sensory transduction modules (audit row 17, wbody, night of 6 Nov 2026). Not registered.

Each senses_* module takes over one or more of brain_layers' sens_* toggles (same ids). The toggle's values:
    "cascade"  the published transduction model (the template worm's default)
    "lumped"   brain_layers' one-transform layer for that modality, run here unchanged (the nested simpler form;
               test: it reproduces the lumped layer exactly, scripts/worm/senses_checks.py)
    "off"      no sensory input from that modality

The cascades act on the NEURON cells through SensG point processes (src/wormemu/nmodl/senses/sens_g.mod): one
conductance with a reversal potential per (cell, channel class) at the soma, set each step from the cascade's open
probability, so NEURON integrates the current implicitly. The displayed sensory current is g (E - v) at the step's
starting voltage (out['sens_I_pA']).
"""
from __future__ import annotations

import numpy as np

from wormemu.brain_layers import Spec

CASCADE, LUMPED = "cascade", "lumped"
FORMS = (CASCADE, LUMPED, "off")


def spec(id, mech, unit, template, lo, hi, label, source, applies_to="", grain="global", notes="", lit=""):
    assert lo <= template <= hi, (id, lo, template, hi)
    return Spec(id, mech, unit, float(template), float(lo), float(hi), source=source, label=label, lit=lit,
                grain=grain, applies_to=applies_to or "whole worm", notes=notes)


def head(ctx, ch, default=0.0):
    return float(ctx.obs["head"].get(ch, default))


def tail(ctx, ch, default=0.0):
    return float(ctx.obs["tail"].get(ch, default))


def form(toggles, tid):
    """The toggle's form; "on" (the brain's generic value) means the cascade."""
    v = toggles.get(tid, CASCADE)
    return {"on": CASCADE, True: CASCADE, False: "off", None: "off"}.get(v, v)


def lumped_current(brain, ids, obs, dt_ms):
    """brain_layers' sensory layer for these toggles only (the nested 'lumped' form). The layer keeps its state per
    channel, so running it here for some modalities and in the brain for the rest gives the lumped layer's numbers.
    Every non-sensory mechanism stays as the brain has it (glia scales the amphid currents, slow_signalling the
    AWC gain), the other sensory modalities are left to whoever runs them."""
    L = brain.layers
    saved = L.on
    L.on = {m for m in saved if not m.startswith("sens_")} | set(ids)
    try:
        return L.sensory_current(obs, dt_ms)
    finally:
        L.on = saved


class Conductance:
    """One SensG point process at the soma of each listed cell (cells absent from this brain are skipped)."""

    def __init__(self, brain, cells, e_mV):
        h = brain.h
        self.h, self.e = h, float(e_mV)
        self.cells = [c for c in cells if c in brain.idx]
        self.idx = np.array([brain.idx[c] for c in self.cells], int)
        self.pp = []
        for i in self.idx:
            pp = h.SensG(brain.soma[i](0.5))
            pp.e, pp.g = self.e, 0.0
            self.pp.append(pp)
        self.pv = h.PtrVector(max(len(self.pp), 1))
        for k, pp in enumerate(self.pp):
            self.pv.pset(k, pp._ref_g)
        self.g_nS = np.zeros(len(self.pp))

    def __len__(self):
        return len(self.pp)

    def set(self, g_nS):
        """Set every cell's conductance (nS, one per cell in self.cells order)."""
        g = np.clip(np.asarray(g_nS, float), 0.0, None)
        if len(self.pp) and not np.array_equal(g, self.g_nS):
            self.pv.scatter(self.h.Vector(g * 1e-3))      # nS -> uS
        self.g_nS = g

    def current_pA(self, v, n_cells):
        """The current into each cell (pA, inward positive) at voltage v (mV, all cells): g (E - v)."""
        I = np.zeros(n_cells)
        if len(self.pp):
            np.add.at(I, self.idx, self.g_nS * (self.e - v[self.idx]))
        return I

    def reset(self):
        self.set(np.zeros(len(self.pp)))


def hill(x, k, n):
    x = np.maximum(np.asarray(x, float), 0.0)
    return x ** n / (x ** n + k ** n)
