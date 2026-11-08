"""Row 24 (part): short-term synaptic plasticity and tap habituation at every wsyn synapse (PLAN row 24;
docs/worm/research/PORT_SOURCES_NEURAL.md N2). The states live in src/wormemu/nmodl/wsyn.mod; this module sets
their parameters per synapse and reports them. numpy_reference() is the CPU path of the same equations.

Model ported: Dittman, Kreitzer and Regehr 2000 J Neurosci 20:1374 (facilitation F driven by a residual-calcium
trace, depletion D with recovery accelerated by a second calcium trace), which nests Tsodyks and Markram 1997 PNAS
94:719 (constant recovery). C. elegans synapses release in a graded way, so the per-spike jumps become rates
driven by BAAIWorm's release fraction s (0 to 1):
    cF' = s - cF/tauF                  residual Ca for facilitation, as ms of full release
    cD' = s - cD/tauD                  residual Ca for recovery
    F = F1 + (1 - F1) cF/(cF + KF)     release probability, F1 at rest
    krec = k0 + (kmax - k0) cD/(cD + KD)
    x' = (1 - x) krec - beta F s x     the release sites' vesicle resource (1 = full)
    z' = (1 - z)/tau_h - beta_h s z    a slow second resource, only at the touch cells' output synapses (tap
                                       habituation, Rankin lineage; PORT_SOURCES N2 (c): habituation as depression
                                       at the touch-cell synapses)
    q = x z F/F1                       quantal content relative to rest; multiplies the synapse's conductance in
                                       every wsyn mode (each vesicle saturates its own receptors, so the current
                                       scales with the number released, not with the cleft concentration)
Every state starts at its steady state for the initial presynaptic voltage: graded release is tonic, so at rest
x and z sit below 1. q is relative to that initial resting state (the ported conductances, like the experiments'
first responses, describe the synapse at rest), so a synapse that stays at its initial voltage is the row 7
synapse; one that sits more depolarised transmits less. With beta = beta_h = 0 and F1 = 1, q = 1 exactly.

Grains: the cholinergic values (fitted to Liu, Hollopeter and Jorgensen 2009 PNAS 106:10823, NMJ: depression,
no facilitation) also serve glutamate and the amine-gated classes (same UNC-13/UNC-18 release machinery: inferred
transplant, PORT_SOURCES N2 (a)); GABA has its own (Liu 2009: little depression, initial facilitation; guessed).

Toggle stp: dittman_regehr (default) / tsodyks_markram (kmax = k0: constant recovery) / depression (also F1 = 1: no
facilitation) / off (beta = 0, F1 = 1: q = 1 exactly, the row 7 synapse). Toggle habituation: on (default) / off
(beta_h = 0). Neither has a target when receptor_kinetics is off (BAAIWorm's own synapse mods).
"""
from __future__ import annotations

import math

import numpy as np

from wormemu import mech
from wormemu.brain_layers import Spec

MECHANISMS = [
    ("stp", "Short-term synaptic depression and facilitation at every chemical synapse (graded Dittman-Regehr "
     "form; nests Tsodyks-Markram, depression only)", "synapse", "dittman_regehr"),
    ("habituation", "Tap habituation: a slow release resource at the touch cells' output synapses", "synapse", "on"),
]
FORMS = ("dittman_regehr", "tsodyks_markram", "depression", "off")
TOUCH = ("ALML", "ALMR", "AVM", "PLML", "PLMR", "PVM")         # Chalfie et al. 1985 touch receptor neurons
GRAINS = ("ach", "gaba")
WSYN_KEYS = ("F1", "tauF", "KF", "beta", "k0", "kmax", "KD", "tauD", "beta_h", "tau_h")
LIU = "Liu, Hollopeter and Jorgensen 2009 PNAS 106:10823 (PMC2705609)"
FIT = (f"fitted by us (scripts/worm/stp_fit.py, 6 Nov 2026) to {LIU} 1 Hz and 5 Hz ACh trains (tau 0.58, 0.09 s; "
       "steady state about 50%); 0.2, 10 and 20 Hz held out")
M = "stp"


def form(v):
    v = "dittman_regehr" if v in ("on", True) else ("off" if v in (False, None) else v)
    if v not in FORMS:
        raise ValueError(f"stp form {v!r} not in {FORMS}")
    return v


def _g(grain, applies):
    return dict(grain=f"transmitter ({grain})", applies_to=applies)


ACH = "presynaptic release of every non-GABA wsyn synapse (acetylcholine, glutamate, amines)"
GABA = "presynaptic release of GABA wsyn synapses"
SPECS = [
    Spec("stp_ach_beta_per_ms", M, "1/ms", 0.09384, 0.005, 1.0, FIT, "inferred", **_g("ach", ACH),
         notes="vesicle depletion rate at full release; fit residuals in runs/worm/night_wbrain/row24_fit.json"),
    Spec("stp_ach_k0_per_s", M, "1/s", 0.01, 0.01, 2.0, FIT, "inferred", **_g("ach", ACH),
         notes="resting recovery rate; the 1 and 5 Hz fit does not identify it (normalised amplitudes) and leaves it on the "
               "lower bound; it sets the resting occupancy (x 0.30 at -60 mV, 0.10 at -40 mV), which q normalises at the "
               "initial voltage; Liu 2009's 0.2 Hz train (held out) is the constraint"),
    Spec("stp_ach_kmax_per_s", M, "1/s", 2.812, 0.2, 50.0, FIT, "inferred", **_g("ach", ACH),
         notes="Ca-accelerated recovery rate"),
    Spec("stp_ach_tauD_ms", M, "ms", 79.67, 20.0, 5000.0, FIT, "inferred", **_g("ach", ACH),
         notes="decay of the recovery Ca trace"),
    Spec("stp_ach_KD_ms", M, "ms", 20.0, 2.0, 200.0, "half-activation of Ca-accelerated recovery, as ms of full "
         "release (about one pulse's release); fixed before the fit", "guessed", **_g("ach", ACH)),
    Spec("stp_ach_F1", M, "1", 1.0, 0.3, 1.0, f"{LIU}: ACh NMJ trains show no facilitation", "inferred",
         **_g("ach", ACH), notes="resting release probability relative to its maximum; 1 = no facilitation"),
    Spec("stp_ach_tauF_ms", M, "ms", 100.0, 10.0, 1000.0, "facilitation trace decay; unused while F1 = 1; "
         "Dittman et al. 2000 report tens to hundreds of ms at vertebrate synapses", "guessed", **_g("ach", ACH)),
    Spec("stp_ach_KF_ms", M, "ms", 20.0, 2.0, 200.0, "facilitation half-activation, as ms of full release; unused "
         "while F1 = 1", "guessed", **_g("ach", ACH)),
    Spec("stp_gaba_beta_per_ms", M, "1/ms", 0.01, 0.0005, 0.5, f"{LIU}: GABA trains 'no or only slight "
         "depression at 1 Hz and 5 Hz'; no time constants given", "guessed", **_g("gaba", GABA)),
    Spec("stp_gaba_k0_per_s", M, "1/s", 0.01, 0.01, 2.0, "the ACh grain's fitted value (shared release machinery)", "guessed",
         **_g("gaba", GABA)),
    Spec("stp_gaba_kmax_per_s", M, "1/s", 2.812, 0.2, 50.0, "as the ACh grain's", "guessed", **_g("gaba", GABA)),
    Spec("stp_gaba_tauD_ms", M, "ms", 79.67, 20.0, 5000.0, "as the ACh grain's", "guessed", **_g("gaba", GABA)),
    Spec("stp_gaba_KD_ms", M, "ms", 20.0, 2.0, 200.0, "as the ACh grain's", "guessed", **_g("gaba", GABA)),
    Spec("stp_gaba_F1", M, "1", 0.5, 0.1, 1.0, f"{LIU}: GABA currents facilitate at first at high frequency; "
         "the size is not given", "guessed", **_g("gaba", GABA)),
    Spec("stp_gaba_tauF_ms", M, "ms", 100.0, 10.0, 1000.0, "Dittman et al. 2000: tens to hundreds of ms", "guessed",
         **_g("gaba", GABA)),
    Spec("stp_gaba_KF_ms", M, "ms", 20.0, 2.0, 200.0, "about one pulse's release", "guessed", **_g("gaba", GABA)),
    Spec("hab_beta_per_ms", "habituation", "1/ms", 0.005, 0.0005, 0.05, "slow-resource depletion at full release: "
         "a 20 ms release uses about 10%; Rankin lineage habituation decrements (PORT_SOURCES N2, reported) not "
         "converted to a rate", "guessed", grain="touch cells", applies_to="output synapses of " + ", ".join(TOUCH)),
    Spec("hab_tau_s", "habituation", "s", 600.0, 60.0, 3600.0, "spontaneous recovery from tap habituation over "
         "minutes to tens of minutes (Rankin and Broster 1992 Behav Neurosci; Rose and Rankin 2001 Learn Mem "
         "8:63), point value not retrieved", "guessed", grain="touch cells",
         applies_to="output synapses of " + ", ".join(TOUCH)),
]


def wsyn_params(p, grain, stp="dittman_regehr", hab=True, touch=False):
    """wsyn's plasticity parameters (mod units: ms, 1/ms) for one synapse."""
    f = form(stp)
    q = {k: float(p[f"stp_{grain}_{k}"]) for k in ("F1", "tauF_ms", "KF_ms", "beta_per_ms", "k0_per_s",
                                                    "kmax_per_s", "KD_ms", "tauD_ms")}
    out = dict(F1=q["F1"], tauF=q["tauF_ms"], KF=q["KF_ms"], beta=q["beta_per_ms"], k0=q["k0_per_s"] / 1000.0,
               kmax=q["kmax_per_s"] / 1000.0, KD=q["KD_ms"], tauD=q["tauD_ms"], beta_h=0.0,
               tau_h=float(p["hab_tau_s"]) * 1000.0)
    if f in ("tsodyks_markram", "depression"):
        out["kmax"] = out["k0"]
    if f == "depression":
        out["F1"] = 1.0
    if f == "off":
        out.update(beta=0.0, F1=1.0)
    if hab and touch:
        out["beta_h"] = float(p["hab_beta_per_ms"])
    return out


def _cn(y, A, B, dt):
    """NEURON cnexp step of y' = A + B y (scalars)."""
    return y + A * dt if B == 0 else y + (1.0 - math.exp(dt * B)) * (-A / B - y)


def numpy_reference(vpre, dt, w, rel, rec, v0=-60.0):
    """CPU path of wsyn mode 2 with plasticity, one synapse, postsynaptic voltage clamped.
    vpre: presynaptic voltage per step (mV); w: wsyn_params(...); rel: dict delta, k, Vth; rec: receptors.site_params;
    v0: presynaptic voltage at initialisation (NEURON's finitialize). Returns g/gmax per step and q."""
    s = 1 / (1 + math.exp((rel["Vth"] - v0) / rel["delta"]))
    T = rec["tmax"] * s
    a = 1 / (1 + (rec["ec50"] / T) ** rec["hill"]) if T > 0 else 0.0
    r, d = a, (a * (1 - rec["ss"]) if rec["tau_des"] > 0 else 0.0)
    cF, cD = s * w["tauF"], s * w["tauD"]                       # steady state at v0, as wsyn's INITIAL
    F = w["F1"] + (1 - w["F1"]) * cF / (cF + w["KF"])
    krec = w["k0"] + (w["kmax"] - w["k0"]) * cD / (cD + w["KD"])
    x, z = krec / (krec + w["beta"] * F * s), 1 / (1 + w["beta_h"] * s * w["tau_h"])
    q0 = x * z * F / w["F1"]
    G, Q = np.zeros(len(vpre)), np.zeros(len(vpre))
    for i, vp in enumerate(vpre.tolist()):
        sinf = 1 / (1 + math.exp((rel["Vth"] - vp) / rel["delta"]))
        tau = (1 - sinf) / rel["k"]
        T = rec["tmax"] * s
        a = 1 / (1 + (rec["ec50"] / T) ** rec["hill"]) if T > 0 else 0.0
        tau_r = rec["tau_off"] + (rec["tau_rise"] - rec["tau_off"]) * a
        if rec["tau_des"] > 0:
            tau_d, dinf = rec["tau_des"], r * (1 - rec["ss"])
            if dinf < d:
                tau_d = rec["tau_des"] * rec.get("des_rec_ratio", 1.0)
        else:
            tau_d, dinf = 1e9, 0.0
        F = w["F1"] + (1 - w["F1"]) * cF / (cF + w["KF"])
        krec = w["k0"] + (w["kmax"] - w["k0"]) * cD / (cD + w["KD"])
        sr = s
        s = _cn(s, sinf / tau, -1 / tau, dt) if tau > 0 else sinf
        r = _cn(r, a / tau_r, -1 / tau_r, dt)
        d = _cn(d, dinf / tau_d, -1 / tau_d, dt)
        x = _cn(x, krec, -(krec + w["beta"] * F * sr), dt)
        z = _cn(z, 1 / w["tau_h"], -(1 / w["tau_h"] + w["beta_h"] * sr), dt)
        cF = _cn(cF, sr, -1 / w["tauF"], dt)
        cD = _cn(cD, sr, -1 / w["tauD"], dt)
        Fn = w["F1"] + (1 - w["F1"]) * cF / (cF + w["KF"])
        Q[i] = x * z * Fn / w["F1"] / q0
        G[i] = r * (1 - d) * Q[i]
    return G, Q


class Mech:
    """Sets every wsyn's plasticity parameters at build; reports the resource states each step."""

    def __init__(self, brain, params, toggles):
        self.p, self.brain = params, brain
        f, hab = form(toggles.get("stp", "off")), toggles.get("habituation", "off") != "off"
        self.pv = None
        w = getattr(brain, "wsyn", None) or []
        if not w:
            return
        from wormemu.mech import receptors
        names, cls = brain.cell_names, mech.RECEPTOR_CLASSES
        touch = {brain.idx[c] for c in TOUCH if c in brain.idx}
        h = brain.h
        self.pv = {k: h.PtrVector(len(w)) for k in ("x", "z", "q")}
        self.touch = np.array([pre in touch for _, pre, _, _ in w])
        for i, (pp, pre, _, c) in enumerate(w):
            lg = receptors.CLASSES[cls[c]][0] if c >= 0 else ("gaba" if pp.erev < -40 else "acetylcholine")
            for k, v in wsyn_params(params, "gaba" if lg == "gaba" else "ach", f, hab, pre in touch).items():
                setattr(pp, k, v)
            self.pv["x"].pset(i, pp._ref_x)
            self.pv["z"].pset(i, pp._ref_z)
            self.pv["q"].pset(i, pp._ref_q)
        self.buf = h.Vector(len(w))
        self.form, self.names = f, names

    def reset(self):
        pass

    def _read(self, k):
        self.pv[k].gather(self.buf)
        return self.buf.as_numpy().copy()                  # the buffer is shared

    def step(self, ctx, dt_ms):
        if self.pv is None:
            return {}
        x, z, q = self._read("x"), self._read("z"), self._read("q")
        out = dict(stp_x_mean=float(x.mean()), stp_x_min=float(x.min()), stp_q_mean=float(q.mean()),
                   stp_q_min=float(q.min()), stp_q_max=float(q.max()))
        if self.touch.any():
            out["hab_z_min"] = float(z[self.touch].min())
        return {"out": {"plasticity": out}}
