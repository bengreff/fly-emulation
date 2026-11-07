"""Each neuron's bulk Ca pool sized from its own morphology (PLAN row 6).

Nicoletti et al. 2019 PLoS ONE 14:e0218738 Eq. 28 and its 2024 port (caintra1.mod, PLoS ONE 19:e0298105):
    d[Ca]/dt = -f I_Ca/(2 F V_cell) - ([Ca] - [Ca]eq)/tau_Ca,
with I_Ca the whole-cell Ca current (mech/capool's total_current form feeds the whole-soma current: BAAIWorm's Ca
channels are all on the soma) and V_cell the cell's own volume: 2024 gives every fitted cell its NeuroMorpho
whole-cell volume (AIY 7.42 um3, RIM 10.94, AVAL 129.6, AVAR 129.08, VA5 48.07, VB6 58.54, VD5 51.3) where BAAIWorm
uses one value for every neuron (31.16 um3, Nicoletti 2019's AWC). Here each neuron's V_cell is its own volume in
the BAAIWorm morphology (the hoc sections the brain builds; derived, no new number). The nanodomain half of the
scheme (SLO-1/2 gated by the Ca at EGL-19 / UNC-2 mouths) is BAAIWorm's slo*_egl19 / slo*_unc2 mods, unchanged.

Forms (nested): ca_pool_volume
  whole_cell (default)  V_cell = the whole cell (soma and neurites), as Nicoletti's one-compartment cells
  soma                  V_cell = the soma alone, the compartment the Ca enters (Ca diffuses about 1 um in
                        tau_Ca = 50 ms at a buffered D near 13 um2/s, Allbritton et al. 1992 Science 258:1812,
                        less than a soma's width); not Nicoletti's choice
  fixed                 the ledger's one capool_vcell for every neuron (BAAIWorm as ported); "off" is the same
Validity: one well-mixed pool per cell; no Ca in the neurites; f, tau_Ca, [Ca]eq stay the ledger's ca_pool values.
Muscles are excluded (their pool is B2's).
"""
from __future__ import annotations

from wormemu.mech import capool

MECHANISMS = [
    ("ca_pool_volume", "Each neuron's bulk Ca pool sized by its own volume in the BAAIWorm morphology (Nicoletti "
     "2024: per-cell volume) instead of one V_cell for all (nested: soma, fixed)", "channel", "whole_cell"),
]
FORMS = ("whole_cell", "soma", "fixed", "off")
SPECS: list = []


def volumes(brain, i):
    """(whole-cell, soma) volume of cell i in um3, from the hoc sections."""
    whole = sum(seg.volume() for sec in brain.cells[i].all for seg in sec)
    soma = sum(seg.volume() for seg in brain.soma[i])
    return whole, soma


class Mech:
    """Rescales each neuron's vcell once at build (after capool); the mod does the rest."""

    def __init__(self, brain, params, toggles):
        form = toggles.get("ca_pool_volume", "off")
        if form not in FORMS:
            raise ValueError(f"ca_pool_volume form {form!r} not in {FORMS}")
        units = toggles.get("ca_pool_units", "off")
        self.v_cell = {}
        if form in ("fixed", "off"):
            return
        for i, sec in enumerate(brain.soma):
            if brain.is_muscle[i]:
                continue
            whole, soma = volumes(brain, i)
            v = whole if form == "whole_cell" else soma
            area = sum(seg.area() for seg in sec)
            for seg in sec:
                m = getattr(seg, "cainternm", None)
                if m is None:
                    continue
                # capool's convention: total_current stores V_cell / (10 A_soma); off stores V_cell
                v_ledger = m.vcell * (capool.MA_CM2_TO_PA_UM2 * area if units == "total_current" else 1.0)
                m.vcell = m.vcell * v / v_ledger
                self.v_cell[brain.cell_names[i]] = v

    def reset(self):
        pass

    def step(self, ctx, dt_ms):
        return {}
