"""Temperature (audit row 25, wbody, night of 6 Nov 2026): the worm's temperature from the world, and Q10 factors.

The worm's temperature follows the local temperature at its head (obs['head']['temperature_C'], the world field)
with the thermal time constant of a 25 um water cylinder, tau = r^2 / alpha = (25 um)^2 / 0.14 mm^2/s, about
4.5 ms (derived): at the brain's exchange interval it is effectively the local temperature.

Each class of rate gets a factor phi = Q10 ** ((T - T_ref) / 10), published as out['q10'] = {class: phi} and
out['temperature_C'] for every module to read (ctx.outputs, updated in place, so modules after this one in REGISTRY
read this step's value):
    gating       channel gating and transduction-channel rates (senses_touch, senses_chem TRPV, senses_proprio), and
                 every compiled channel's gates (RATE_MODS: BAAIWorm's, Nicoletti's, du_bwm's, AWA's)
    conductance  single-channel conductance: applied here to every BAAIWorm channel density and the leak, per cell,
                 through g_scale
    enzyme       biochemical cascades (senses_chem's Usuyama cGMP network runs on a time axis scaled by phi; the slow
                 states, homeostasis and learning integrate on the same scaled time)
    synapse      transmitter release, receptor and short-term plasticity kinetics (RATE_MODS: wsyn, BAAIWorm's
                 synapses)
    pump         pharyngeal pumping: the pharyngeal muscle gates (RATE_MODS: sh_pharynx), the lumped clock's rate
    dmp_clock    the defecation motor program period (temperature compensated, Iwasaki et al. 1995; Q10 1): the
                 intestine's IP3R oscillator and the nested timer run on a time axis scaled by phi
Compiled mods get the factor through a GLOBAL tadj (1 by default) that multiplies the listed state equations of
their DERIVATIVE block. patch_mod adds it while brain._neuron copies the mods to the build, so the vendored files
stay verbatim and at tadj = 1 the build is the unpatched one; this module sets tadj_<suffix> whenever T moves.
Not scaled (no class yet): Ca clearance in the Ca pools (cainternm, du_bwm's cad, sh_pharynx's shell), neuromod's
diffusion and release, the c302 muscle mods (they read NEURON's celsius, set once from ion_celsius).
T_ref is the temperature the ported models' data were taken at (room temperature, ~20 C). Toggle "temperature":
"q10" (template) | "off" (every factor 1, the worm at T_ref: the neutral form; at T = T_ref the two are identical).
"""
from __future__ import annotations

import re

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


# mod file stem -> (rate class, the states to scale; None = every state equation; "own" = the mod declares tadj)
_GATES = ("cca1", "egl19", "egl2", "egl36", "irk", "kcnl", "kqt3", "kvs1", "shk1", "shl1", "slo1_egl19", "slo1_unc2",
          "slo2_egl19", "slo2_unc2", "unc2", "exp2", "kqt1", "slo1iso", "slo2iso", "unc103", "awa_liu2018")
_SYNS = ("wsyn", "neuron_to_neuron_exc_syn", "neuron_to_neuron_inh_syn", "exc_syn_advance", "inh_syn_advance")
RATE_MODS = {**{m: ("gating", None) for m in _GATES}, **{m: ("synapse", None) for m in _SYNS},
             "du_bwm": ("gating", ("m", "h", "n", "p", "kr", "ps")), "sh_pharynx": ("pump", "own")}
_HEAD = re.compile(r"^(\s*(?:SUFFIX|POINT_PROCESS)\s+(\w+).*)$", re.M)
_EQ = re.compile(r"^(\s*)(\w+)'\s*=\s*(.*?)\s*(:.*)?$")


def mod_suffix(text):
    return _HEAD.search(text).group(2)


def patch_mod(stem, text):
    """The mod's text with tadj multiplying its rate-class state equations (unchanged if not in RATE_MODS)."""
    if stem not in RATE_MODS or RATE_MODS[stem][1] == "own":
        return text
    states = RATE_MODS[stem][1]
    text = _HEAD.sub(lambda m: m.group(1) + "\n    GLOBAL tadj", text, count=1)
    text = re.sub(r"^(PARAMETER\s*\{)", "\\1\n    tadj = 1", text, count=1, flags=re.M)
    out, inside, n = [], False, 0
    for line in text.split("\n"):
        if re.match(r"^\s*DERIVATIVE\s+\w+\s*\{", line):
            inside = True
        elif inside and re.match(r"^\}", line):
            inside = False
        m = _EQ.match(line) if inside else None
        if m and (states is None or m.group(2) in states):
            line = f"{m.group(1)}{m.group(2)}' = tadj * ({m.group(3)})" + (f" {m.group(4)}" if m.group(4) else "")
            n += 1
        out.append(line)
    if not n:
        raise ValueError(f"{stem}: no state equation patched")
    return "\n".join(out)


def factors(T, p):
    d = (T - p["temp_ref_C"]) / 10.0
    return {c: float(p[f"temp_q10_{c}"] ** d) for c in CLASSES}


class Mech:
    def __init__(self, brain, params, toggles):
        self.b, self.p = brain, params
        self.n = len(brain.cell_names)
        h = getattr(brain, "h", None)
        # (NEURON global, rate class) for every patched mod this build has
        self._tadj = [] if h is None else [(f"tadj_{sfx}", c) for sfx, c in getattr(brain, "rate_mods", {}).items()
                                           if hasattr(h, f"tadj_{sfx}")]
        self._h = h
        self.reset()

    def reset(self):
        self.T = None
        self._gs, self._phi_g, self._q = None, None, None

    def step(self, ctx, dt_ms):
        p = self.p
        T_loc = float(ctx.obs["head"].get("temperature_C", p["temp_ref_C"]))
        self.T = T_loc if self.T is None else T_loc + (self.T - T_loc) * np.exp(-dt_ms / p["temp_tau_ms"])
        q = factors(self.T, p)
        if q != self._q:
            self._q = q
            for name, c in self._tadj:
                setattr(self._h, name, q[c])
        if q["conductance"] != self._phi_g:                 # rebuild the multipliers only when T moves
            self._phi_g = q["conductance"]
            x = np.full(self.n, self._phi_g)
            self._gs = {nm: x for nm in G_SCALE_NAMES}
        return dict(g_scale=self._gs, out={"temperature_C": self.T, "q10": q})
