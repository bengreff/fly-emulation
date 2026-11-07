"""Temperature (audit row 25, wbody, night of 6 Nov 2026): the worm's temperature from the world, and Q10 factors.

The worm's temperature follows the local temperature at its head (obs['head']['temperature_C'], the world field)
with the thermal time constant of a 25 um water cylinder, tau = r^2 / alpha = (25 um)^2 / 0.14 mm^2/s, about
4.5 ms (derived): at the brain's exchange interval it is effectively the local temperature.

Each class of rate gets a factor phi = Q10 ** ((T - T_ref) / 10), published as out['q10'] = {class: phi} and
out['temperature_C'] for every module to read (ctx.outputs, updated in place, so modules after this one in REGISTRY
read this step's value):
    gating       channel gating and transduction-channel rates (senses_touch, senses_chem TRPV, senses_proprio)
    conductance  single-channel conductance: applied here to every BAAIWorm channel density and the leak, per cell,
                 through g_scale (BAAIWorm's mods have no temperature term, so their gating is not scaled)
    enzyme       biochemical cascades (senses_chem's Usuyama cGMP network runs on a time axis scaled by phi)
    synapse      transmitter release and receptor kinetics (for wbrain's receptors module; not applied here)
    pump         pharyngeal pumping rate (for the organ modules; not applied here)
    dmp_clock    the defecation motor program period (temperature compensated, Iwasaki et al. 1995; Q10 1)
T_ref is the temperature the ported models' data were taken at (room temperature, ~20 C). Toggle "temperature":
"q10" (template) | "off" (every factor 1, the worm at T_ref: the neutral form; at T = T_ref the two are identical).
"""
from __future__ import annotations

import numpy as np

from wormemu.mech import G_SCALE_NAMES
from wormemu.mech.senses_base import spec

MECHANISMS = [("temperature", "Temperature: the worm's temperature from the world field, Q10 factors on rates",
               "physics", "q10")]
TM = "temperature"
CLASSES = ("gating", "conductance", "enzyme", "synapse", "pump", "dmp_clock")
SPECS = [
    spec("temp_ref_C", TM, "C", 20, 18, 23, "inferred",
         "the ported models' recordings were at room temperature (Liu et al. 2018; O'Hagan et al. 2005; BAAIWorm's "
         "fits to patch data)"),
    spec("temp_tau_ms", TM, "ms", 4.5, 1, 20, "derived",
         "r^2 / alpha with r 25 um (Sanzeni et al. 2019 Fig 1) and alpha 0.14 mm^2/s (water)"),
    spec("temp_q10_gating", TM, "1", 3.0, 2.0, 4.0, "guessed",
         "none opened for C. elegans; Hille 2001's general range for channel gating"),
    spec("temp_q10_conductance", TM, "1", 1.5, 1.2, 1.6, "guessed",
         "none opened for C. elegans; Hille 2001's general range for open-channel conductance"),
    spec("temp_q10_enzyme", TM, "1", 2.5, 2.0, 3.0, "guessed", "none opened: typical enzyme-cascade Q10"),
    spec("temp_q10_synapse", TM, "1", 2.0, 1.5, 3.0, "guessed", "none opened"),
    spec("temp_q10_pump", TM, "1", 2.0, 1.5, 3.0, "guessed",
         "none opened: pharyngeal pumping rises with temperature (Q10 not found in a free source)"),
    spec("temp_q10_dmp_clock", TM, "1", 1.0, 0.9, 1.2, "measured",
         "Iwasaki, Liu & Thomas 1995 PNAS 92:10317 (a temperature-compensated ultradian clock)",
         notes="period about constant over the cultivation range; the exact Q10 was not opened"),
]


def factors(T, p):
    d = (T - p["temp_ref_C"]) / 10.0
    return {c: float(p[f"temp_q10_{c}"] ** d) for c in CLASSES}


class Mech:
    def __init__(self, brain, params, toggles):
        self.b, self.p = brain, params
        self.n = len(brain.cell_names)
        self.reset()

    def reset(self):
        self.T = None
        self._gs, self._phi_g = None, None

    def step(self, ctx, dt_ms):
        p = self.p
        T_loc = float(ctx.obs["head"].get("temperature_C", p["temp_ref_C"]))
        self.T = T_loc if self.T is None else T_loc + (self.T - T_loc) * np.exp(-dt_ms / p["temp_tau_ms"])
        q = factors(self.T, p)
        if q["conductance"] != self._phi_g:                 # rebuild the multipliers only when T moves
            self._phi_g = q["conductance"]
            x = np.full(self.n, self._phi_g)
            self._gs = {nm: x for nm in G_SCALE_NAMES}
        return dict(g_scale=self._gs, out={"temperature_C": self.T, "q10": q})
