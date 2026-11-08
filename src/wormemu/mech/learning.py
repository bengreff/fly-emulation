"""Row 24 (part): slow associative states (PLAN row 24; docs/worm/research/PORT_SOURCES_NEURAL.md N3).

No paradigm has a published model or time constant (PORT_SOURCES N3: "the literature constants were not found to
exist at the needed resolution"), so the port is N3's recommended shared structure: one bounded association state
per paradigm, raised by the pairing of a sensory neuron's activity with a context signal and decaying by itself,
    A' = drive (1 - A)/tau_learn - A/tau_forget,   drive in [0, 1],   A in [0, 1],
read out as a factor 1 + e A on the identified cell's output:
    salt      ASER activity x starvation    -> ASER release down. Salt + starvation turns attraction to aversion
              (Saeki et al. 2001 J Exp Biol 204:1757); through INS-1/DAF-2/PI3K (Tomioka et al. 2006 Neuron 51:613)
              and DAG/PKC-1 in ASER (Adachi et al. 2010 EMBO J 29:3163; Ohno et al. 2014 Science 345:313). The
              measured effect is a switch of ASER's output; the release cut is the bounded stand-in (inferred).
    thermo    AFD activity x starvation     -> AFD release down. Starvation at a temperature abolishes the move to it
              (Mohri et al. 2005 Genetics 169:1437; Kodama et al. 2006 PNAS 103:4012, INS-1 from AIA).
    pathogen  pathogen exposure             -> ADF serotonin release up (Zhang, Lu and Bargmann 2005 Nature 438:179:
              training on PA14 raises tph-1 expression in ADF; MOD-1 in AIY/AIZ/RIA reads it, row 7's mod1 class).
Context signals: starvation = mech.slow_signalling's DAF-16 nuclear state (insulin) when that module runs, else
1 - energy_fraction (B2; absent = fed); pathogen = outputs['pathogen_exposure'] (0 to 1; mech/pathogen provides it, off by default,
so the pathogen state stays 0 unless an experiment sets hours on PA14). Activity = the cell's depolarisation from its own
set point (slow_signalling's set-point rule and template values), as a fraction of slow_act_dv_mV. A fed worm with no pathogen keeps
every state at 0: neutral. Every number is guessed except where noted. Form: on (default) / off.
"""
from __future__ import annotations

import numpy as np

from wormemu.brain_layers import Spec
from wormemu.mech import slow_signalling as SS

SET = {s.id: s.template for s in SS.SPECS if s.id in ("slow_set_s", "slow_act_dv_mV")}   # shared rule (templates;
# a Mech reads this worm's values of the two, so the shared numbers stay one number)

MECHANISMS = [
    ("associative", "Slow associative states: salt (ASER, starvation), thermotaxis (AFD, starvation), pathogen "
     "(ADF serotonin)", "plasticity", "on"),
]
M = "associative"
# (id, cells, context, effect target)
PARADIGMS = [
    ("salt", ("ASER",), "starved", "release"),
    ("thermo", ("AFDL", "AFDR"), "starved", "release"),
    ("pathogen", ("ADFL", "ADFR"), "pathogen", "ma_release_scale"),
]
SRC = {"salt": "classic protocol: 1 h of salt + starvation (Saeki 2001; Tomioka 2006)",
       "thermo": "starvation-conditioning protocols of hours (Mohri 2005)",
       "pathogen": "4 h PA14 training (Zhang 2005)"}


def _s(sid, units, t, lo, hi, src, applies, label="guessed", **kw):
    return Spec(sid, M, units, t, lo, hi, src, label, grain="paradigm", applies_to=applies, **kw)


SPECS = []
for _p, _cells, _, _ in PARADIGMS:
    _a = ", ".join(_cells)
    SPECS += [
        _s(f"assoc_{_p}_learn_tau_min", "min", 30.0 if _p == "salt" else (60.0 if _p == "thermo" else 120.0),
           5.0, 600.0, SRC[_p] + "; the state reaches most of its value within the training time", _a),
        _s(f"assoc_{_p}_forget_tau_min", "min", 60.0 if _p != "pathogen" else 480.0, 10.0, 2880.0,
           "decay without the pairing; salt and thermotaxis memories fade within hours, pathogen avoidance lasts "
           "longer (guessed)", _a),
    ]
SPECS += [
    _s("assoc_salt_effect", "1", -0.6, -0.95, -0.1, "ASER output cut at full association", "ASER"),
    _s("assoc_thermo_effect", "1", -0.5, -0.95, -0.1, "AFD output cut at full association", "AFDL, AFDR"),
    _s("assoc_pathogen_effect", "1", 1.0, 0.2, 3.0, "ADF serotonin release raised at full association (tph-1::GFP "
       "rises after training, Zhang 2005)", "ADFL, ADFR"),
]


class Mech:
    def __init__(self, brain, params, toggles):
        self.p, self.brain = params, brain
        self.n = len(brain.cell_names)
        self.cells = {pid: [brain.idx[c] for c in cells if c in brain.idx] for pid, cells, _, _ in PARADIGMS}
        from wormemu import mech
        sp = getattr(brain, "spec", None)
        self.set = SET if sp is None else {k: float(mech.params_for(SS, sp)[k]) for k in SET}
        self.reset()

    def reset(self):
        self.t, self.vsum, self.v0 = 0.0, np.zeros(self.n), None
        self.A = {pid: 0.0 for pid, *_ in PARADIGMS}

    def step(self, ctx, dt_ms):
        p = self.p
        self.t += dt_ms
        if self.v0 is None:
            self.vsum += ctx.v * dt_ms
            if self.t >= 1000.0 * self.set["slow_set_s"]:
                self.v0 = self.vsum / self.t
            return {}
        o = ctx.outputs
        if o.get("daf16_nuclear") is not None:
            starved = float(np.max(o["daf16_nuclear"]))
        else:
            e = o.get("energy_fraction")
            starved = 0.0 if e is None else float(np.clip(1.0 - e, 0.0, 1.0))
        ctxs = {"starved": starved, "pathogen": float(np.clip(o.get("pathogen_exposure", 0.0), 0.0, 1.0))}
        a = np.clip((ctx.v - self.v0) / self.set["slow_act_dv_mV"], 0.0, 1.0)
        g = {"release": np.ones(self.n)}
        ms = np.ones(self.n)
        for pid, _, c, target in PARADIGMS:
            ix = self.cells[pid]
            act = float(a[ix].mean()) if ix and c == "starved" else 1.0
            drive = act * ctxs[c]
            A = self.A[pid]
            phi = ctx.outputs.get("q10", {}).get("enzyme", 1.0)
            A += dt_ms * phi / 6e4 * (drive * (1 - A) / p[f"assoc_{pid}_learn_tau_min"]
                                      - A / p[f"assoc_{pid}_forget_tau_min"])
            self.A[pid] = A = float(np.clip(A, 0.0, 1.0))
            f = 1.0 + p[f"assoc_{pid}_effect"] * A
            if target == "release":
                g["release"][ix] *= f
            else:
                ms[ix] *= f
        res = {"g_scale": g, "out": {"associative": dict(self.A)}}
        if not np.all(ms == 1.0):
            res["out"]["ma_release_scale"] = ms
        return res
