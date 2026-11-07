"""Rows 18 and 19: slow intracellular signalling and activity-dependent channel expression (PLAN rows 18, 19;
docs/worm/research/PORT_SOURCES_NEURAL.md N6, N7).

Row 18, slow states. No published worm model of any of these cascades exists (PORT_SOURCES N6); the port target is
N6's nested form, one bounded first-order state per (pathway, cell set):
    S' = (S_inf - S)/tau,   S_inf in [0, 1] from the pathway's input,   effect factor = 1 + e S   (e >= -1)
Inputs: "depol" / "hyperpol" = the cell's sustained voltage change from its own set point (its mean voltage over
the first set_s seconds), as a fraction of act_dv_mV, clipped to [0, 1]; "starved" = 1 - energy_fraction (B2's
output, absent = fed = 0); "fed" = energy_fraction (absent = 1). States start at 0, the context-driven ones (daf16,
daf7) at their steady state for the context when the set point is taken.
    egl4       AWC     hyperpol (odour lowers AWC cGMP: EGL-4 enters the nucleus)  -> AWC release down (adaptation)
    cmk1_fast  AFD     depol (warming)                                             -> AFD release down
    cmk1_slow  AFD     depol                                                       -> AFD release down
    glr1       every cell with a GLR-class synapse onto it, depol (CMK-1 feedback on GLR-1 transcription)
                                                                                   -> rec_glr down
    daf16      every neuron, starved (insulin falls, DAF-16 enters the nucleus) -> outputs daf16_nuclear (read by
               mech.learning as the starvation signal)
    daf7       ASI, fed (DAF-7 TGF-beta expression follows food) -> outputs daf7 (its DAF-1 targets are not wired)
    creb       every neuron, depol (CRH-1/CREB, activity-driven) -> outputs creb (read by mech.learning: consolidation)
The release stand-ins for EGL-4 and CMK-1 are inferred: the measured effect is on the sensory neuron's transduction
(AWC adaptation; AFD's threshold T*AFD), which lives in the sensory model; the module also exports the states
(outputs slow_states) for it. Form: states (default) / off. The old lumped layer (brain_layers.slow_gain, a slow AWC
odour-current gain) is retired: it multiplies a current inside the lumped sensory code, which a module cannot
reach; egl4 is its replacement.

Row 19, homeostatic channel tuning. Rule ported: O'Leary, Williams, Franci and Marder 2014 Neuron 82:809 (integral
control from a calcium error; the 2013 PNAS paper's rule family, PORT_SOURCES N7 (a) 2):
    tau_i m_i' = (Ca_tgt - Ca)/Ca_tgt,   tau_g d_i' = (1 + m_i) - d_i,   d_i in [d_lo, d_hi]
d_i multiplies channel i's somatic density (g_scale dens_<i>). Ca is the cell's own Ca, Ca_tgt its own set point
(mean Ca over the first set_s seconds: each neuron type keeps the state development gave it; inferred). UNC-2's
tau follows the C. elegans CaV2 self-tuning measurements (PMC11363341: no change after 1 h of stimulation, a
measurable fall after more than 2 h); EGL-19's and SHL-1's are guessed. Forms: oleary (default) / lumped (the old
brain_layers bias current toward a voltage target, reproduced exactly) / off.
"""
from __future__ import annotations

import numpy as np

from wormemu.brain_layers import Spec

MECHANISMS = [
    ("slow_signalling", "Slow intracellular states (EGL-4/PKG, CMK-1 fast and slow, GLR-1 trafficking, insulin/DAF-16, "
     "DAF-7, CRH-1/CREB), first-order and bounded, scaling release and receptor densities", "plasticity", "states"),
    ("homeostasis", "Activity-dependent channel density tuning (O'Leary integral control on a calcium error; UNC-2 "
     "self-tuning over hours)", "plasticity", "oleary"),
]
FORMS = {"slow_signalling": ("states", "off"), "homeostasis": ("oleary", "lumped", "off")}
M, H = "slow_signalling", "homeostasis"


def form(mid, v):
    v = FORMS[mid][0] if v in ("on", True) else ("off" if v in (False, None) else v)
    if v not in FORMS[mid]:
        raise ValueError(f"{mid} form {v!r} not in {FORMS[mid]}")
    return v


# (id, cells (None = every neuron; "glr" = cells receiving GLR-class synapses), input, effect target or None)
PATHWAYS = [
    ("egl4", ("AWCL", "AWCR"), "hyperpol", "release"),
    ("cmk1_fast", ("AFDL", "AFDR"), "depol", "release"),
    ("cmk1_slow", ("AFDL", "AFDR"), "depol", "release"),
    ("glr1", "glr", "depol", "rec_glr"),
    ("daf16", None, "starved", None),
    ("daf7", ("ASIL", "ASIR"), "fed", None),
    ("creb", None, "depol", None),
]
HOMEO_CHANNELS = ("unc2", "egl19", "shl1")
L2002 = "L'Etoile et al. 2002 Neuron 36:1079 (nuclear EGL-4::GFP visible after 80 min of odour)"
YU = "Yu et al. 2014 Neuron 84:919 (CMK-1, AFD threshold reset: 2-3 min and 3-5 h components, 15 to 25 C shift)"
U2 = "PMC11363341, PNAS 2024 121:e2404969121 (UNC-2 abundance: no change after 1 h, a fall after > 2 h)"
OL = "O'Leary et al. 2014 Neuron 82:809"


def _s(sid, mod, units, t, lo, hi, src, label, applies, **kw):
    return Spec(sid, mod, units, t, lo, hi, src, label, grain="pathway", applies_to=applies, **kw)


SPECS = [
    _s("slow_set_s", M, "s", 2.0, 0.5, 20.0, "averaging window for each cell's own set point (voltage, Ca) at the "
       "start of a run; the states are neutral at the set point", "guessed", "every neuron"),
    _s("slow_act_dv_mV", M, "mV", 10.0, 3.0, 30.0, "voltage change from the set point that saturates a pathway's "
       "activity input", "guessed", "every slow-state pathway"),
    _s("egl4_tau_min", M, "min", 80.0, 30.0, 180.0, L2002, "inferred", "AWCL, AWCR",
       notes="time to visible translocation taken as the relaxation time"),
    _s("egl4_effect", M, "1", -0.7, -0.9, -0.2, "release cut at full EGL-4 adaptation; the old lumped layer's AWC "
       "gain floor 0.3", "guessed", "AWCL, AWCR"),
    _s("cmk1_fast_tau_min", M, "min", 2.5, 2.0, 3.0, YU, "measured", "AFDL, AFDR"),
    _s("cmk1_slow_tau_h", M, "h", 4.0, 3.0, 5.0, YU, "measured", "AFDL, AFDR"),
    _s("cmk1_fast_effect", M, "1", -0.3, -0.6, 0.0, "AFD output cut by the fast CMK-1 component (stands in for the "
       "threshold shift)", "guessed", "AFDL, AFDR"),
    _s("cmk1_slow_effect", M, "1", -0.3, -0.6, 0.0, "as the fast component's", "guessed", "AFDL, AFDR"),
    _s("glr1_tau_h", M, "h", 2.0, 0.5, 8.0, "GLR-1 transcription and trafficking; PMC4963118 (CMK-1 couples GLR-1 "
       "to its own transcription; time course not opened)", "guessed", "cells receiving GLR-class synapses"),
    _s("glr1_effect", M, "1", -0.5, -0.8, 0.0, "GLR-1 conductance cut at full activity (negative feedback)", "guessed",
       "cells receiving GLR-class synapses"),
    _s("daf16_tau_h", M, "h", 1.0, 0.25, 6.0, "DAF-16 nuclear entry under starvation (minutes to hours)", "guessed",
       "every neuron"),
    _s("daf7_tau_h", M, "h", 6.0, 1.0, 24.0, "daf-7 expression in ASI follows food over hours (Ren et al. 1996 "
       "Science 274:1389, qualitative)", "guessed", "ASIL, ASIR"),
    _s("creb_tau_h", M, "h", 2.0, 0.5, 8.0, "CRH-1/CREB activation by sustained activity", "guessed", "every neuron"),
    _s("homeo_unc2_tau_h", H, "h", 3.0, 1.0, 10.0, U2, "inferred", "every neuron",
       notes="1 h: no change, > 2 h: a fall; 3 h is the integrator time at a 100% Ca error"),
    _s("homeo_egl19_tau_h", H, "h", 6.0, 1.0, 24.0, f"{OL}: channels differ in tau_i; guessed", "guessed",
       "every neuron"),
    _s("homeo_shl1_tau_h", H, "h", 4.0, 1.0, 24.0, f"{OL}: channels differ in tau_i; guessed", "guessed",
       "every neuron"),
    _s("homeo_tau_g_h", H, "h", 1.0, 0.1, 10.0, f"{OL}: mRNA to channel low-pass", "guessed", "every neuron"),
    _s("homeo_d_lo", H, "1", 0.25, 0.0, 1.0, "lowest density multiplier", "guessed", "every neuron"),
    _s("homeo_d_hi", H, "1", 4.0, 1.0, 10.0, "highest density multiplier (C. elegans channel levels vary several-fold "
       "between types, CeNGEN)", "guessed", "every neuron"),
]


def relax(S, target, tau_ms, dt):
    return target + (S - target) * np.exp(-dt / tau_ms)


class Mech:
    def __init__(self, brain, params, toggles):
        self.p, self.brain = params, brain
        self.f = form(M, toggles.get(M, "off"))
        self.fh = form(H, toggles.get(H, "off"))
        names = brain.cell_names
        self.n = len(names)
        self.neuron = np.isfinite(np.asarray(brain.layers.pos))
        idx = brain.idx
        glr = np.zeros(self.n, bool)
        if getattr(brain, "wsyn", None):
            from wormemu import mech
            k = mech.RECEPTOR_CLASSES.index("glr")
            for _, _, post, c in brain.wsyn:
                glr[post] |= c == k
        self.mask = {}
        for pid, cells, _, _ in PATHWAYS:
            if cells is None:
                m = self.neuron.copy()
            elif cells == "glr":
                m = glr & self.neuron
            else:
                m = np.zeros(self.n, bool)
                m[[idx[c] for c in cells if c in idx]] = True
            self.mask[pid] = m
        self.reset()

    def reset(self):
        self.t = 0.0
        self.vsum, self.csum, self.nset = np.zeros(self.n), np.zeros(self.n), 0
        self.v0 = self.c0 = None
        self.started = False
        self.S = {pid: np.zeros(self.n) for pid, *_ in PATHWAYS}
        self.m = {c: np.zeros(self.n) for c in HOMEO_CHANNELS}
        self.d = {c: np.ones(self.n) for c in HOMEO_CHANNELS}
        self.ih = np.zeros(self.n)

    def _setpoint(self, v, ca, dt):
        if self.v0 is not None:
            return True
        self.vsum += v * dt
        self.csum += ca * dt
        self.nset += dt
        if self.t >= 1000.0 * self.p["slow_set_s"]:
            self.v0, self.c0 = self.vsum / self.nset, np.maximum(self.csum / self.nset, 1e-6)
        return False

    def step(self, ctx, dt_ms):
        p, v, ca = self.p, ctx.v, ctx.ca
        self.t += dt_ms
        res, out, g = {}, {}, {}
        if self.fh == "lumped":                          # brain_layers.homeostatic_current, verbatim
            q = self.brain.layers.p
            self.ih = self.ih + self.neuron * q["homeo_gain_pA_per_mV"] * (q["homeo_target_mV"] - v) * dt_ms / (
                1000.0 * q["homeo_tau_s"])
            self.ih = np.clip(self.ih, -q["homeo_max_pA"], q["homeo_max_pA"])
            res["I_pA"] = self.ih.copy()
        ready = self._setpoint(v, ca, dt_ms)
        if not ready:
            return res
        if self.f == "states":
            e = ctx.outputs.get("energy_fraction")
            fed = 1.0 if e is None else float(np.clip(e, 0.0, 1.0))
            a = np.clip((v - self.v0) / p["slow_act_dv_mV"], -1.0, 1.0)
            inp = {"depol": np.maximum(a, 0.0), "hyperpol": np.maximum(-a, 0.0),
                   "starved": np.full(self.n, 1.0 - fed), "fed": np.full(self.n, fed)}
            tau = {"egl4": 6e4 * p["egl4_tau_min"], "cmk1_fast": 6e4 * p["cmk1_fast_tau_min"],
                   "cmk1_slow": 3.6e6 * p["cmk1_slow_tau_h"], "glr1": 3.6e6 * p["glr1_tau_h"],
                   "daf16": 3.6e6 * p["daf16_tau_h"], "daf7": 3.6e6 * p["daf7_tau_h"],
                   "creb": 3.6e6 * p["creb_tau_h"]}
            first = not self.started
            self.started = True
            for pid, _, kind, target in PATHWAYS:
                m = self.mask[pid]
                S = self.S[pid]
                if first and kind in ("starved", "fed"):     # context states start at their steady state
                    S[m] = inp[kind][m]
                S[m] = relax(S[m], inp[kind][m], tau[pid], dt_ms)
                if target is not None:
                    g[target] = g.get(target, 1.0) * (1.0 + p[f"{pid}_effect"] * S)
            out["daf16_nuclear"] = self.S["daf16"].copy()
            out["creb"] = self.S["creb"].copy()
            out["daf7"] = self.S["daf7"].copy()
            out["slow_states"] = {pid: float(self.S[pid][self.mask[pid]].max()) if self.mask[pid].any() else 0.0
                                  for pid, *_ in PATHWAYS}
        if self.fh == "oleary":
            err = (self.c0 - ca) / self.c0 * self.neuron
            for c in HOMEO_CHANNELS:
                self.m[c] += err * dt_ms / (3.6e6 * p[f"homeo_{c}_tau_h"])
                self.d[c] = np.clip(relax(self.d[c], 1.0 + self.m[c], 3.6e6 * p["homeo_tau_g_h"], dt_ms),
                                    p["homeo_d_lo"], p["homeo_d_hi"])
                g[f"dens_{c}"] = self.d[c].copy()
            out["homeo"] = {f"d_{c}_{k}": float(f(self.d[c][self.neuron])) for c in HOMEO_CHANNELS
                            for k, f in (("min", np.min), ("max", np.max))}
        if g:
            res["g_scale"] = {k: (np.asarray(x, float) * np.ones(self.n)) for k, x in g.items()}
        if out:
            res["out"] = out
        return res
