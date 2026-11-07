"""Row 26 (part): quantal release noise at every wsyn synapse (docs/worm/research/PORT_SOURCES_NEURAL.md N9).

Port of Liu, Hollopeter and Jorgensen 2009 (PNAS 106:10823, PMC2705609): at the NMJ, ACh motor neurons release
quanta tonically at rest (26.3 +- 5.4 /s, 17.6 +- 0.9 pA at -60 mV; Fig. 3E), and the rate falls (10.2 /s) and rises
(35.3 /s) with the motor neuron's voltage: graded release IS a voltage-graded vesicle rate. So the noise is the shot
noise of each synapse's own graded release, with the mean unchanged; a fixed-rate mini generator added on top would
double-count the mean. Per wsyn synapse i, each step:
    lambda_i = gd_i / (g_q,i tau_i)                     vesicles per ms implied by the deterministic conductance gd
    g_q,i   = q_pA / (E_lacr - hold_mV) * gamma_i/gamma_lacr     quantal peak conductance: Liu's NMJ quantum
                                                        (derived), scaled by the class's single-channel conductance
                                                        (same receptor count per quantum: inferred)
    tau_i   = the class's tau_off (graded mode 0: Liu's evoked decay, 5.6 ms)
    G_i  <- G_i e + g_q,i (tau/dt)(1 - e) A,  A = sum of N ~ Poisson(lambda dt) amplitudes, each gamma (mean 1, CV)
    Gm_i <- Gm_i e + gd_i (1 - e),            e = exp(-dt/tau)    (Gm = E[G] given the rate history, exactly)
    qn_i  = G_i / Gm_i                         the synapse's conductance is gd_i qn_i (nmodl/wsyn.mod)
Each vesicle's arrival is averaged over the step (the (tau/dt)(1 - e) factor), which keeps E[qn] = 1 exactly at any
step; the variance is within 1% of Campbell's continuous lambda g_q^2 (1 + CV^2) tau/2 for dt <= tau/5. Validity:
brain steps up to about tau/3 (1 ms against tau 5-25 ms); postsynaptic factors (recgain, desensitization) count as
fewer quanta rather than smaller ones; the Mg block is outside gd. Draws come from the worm's seed (the template
worm: 0), rebuilt at reset, so a reset replays the same noise. Forms: quantal (default) / off (qn = 1, the
deterministic synapse). Channel noise (row 26's other half) is not modelled.
"""
from __future__ import annotations

import numpy as np

from wormemu import mech
from wormemu.brain_layers import Spec

MECHANISMS = [("quantal_noise", "Quantal (vesicle) release noise at chemical synapses", "synapse", "quantal")]
FORMS = ("quantal", "off")
M = "quantal_noise"
LIU = "Liu, Hollopeter and Jorgensen 2009 PNAS 106:10823 (PMC2705609)"


def _s(sid, units, t, lo, hi, src, label, **kw):
    return Spec(sid, M, units, t, lo, hi, src, label, grain="global", applies_to="every wsyn synapse", **kw)


SPECS = [
    _s("noise_quantal_pA", "pA", 17.6, 15.8, 19.4, LIU + " Fig. 3E: mEPSC amplitude 17.6 +- 0.9 pA (mean +- SEM) at "
       "the NMJ, muscle clamped at -60 mV; range +- 2 SEM", "measured"),
    _s("noise_hold_mV", "mV", -60.0, -60.0, -60.0, LIU + ": the holding potential of the amplitude above (a condition "
       "of the measurement; with rec_lacr_erev_mV it gives the quantal conductance, 0.248 nS)", "measured"),
    _s("noise_event_tau_ms", "ms", 5.6, 4.8, 6.4, LIU + " Fig. 2C: evoked NMJ current decay 5.6 +- 0.4 ms (+- 2 SEM); "
       "the quantum's decay at graded-mode (BAAIWorm) synapses, which have no receptor class", "measured"),
    _s("noise_amp_cv", "1", 0.3, 0.1, 0.6, "per-quantum amplitude CV; Liu 2009 gives only the population SEM. 0.3 is "
       "typical of single-site quantal variability (guessed)", "guessed"),
]


def form(v):
    v = "off" if v in (False, None) else v
    if v not in FORMS:
        raise ValueError(f"quantal_noise form {v!r} not in {FORMS}")
    return v


def quantal_g_uS(p, rp, cls):
    """Quantal peak conductance (uS) for receptor class `cls` (None: graded mode, the L-AChR value)."""
    g = p["noise_quantal_pA"] / abs(float(rp["rec_lacr_erev_mV"]) - p["noise_hold_mV"]) / 1000.0   # pA/mV = nS
    if cls is not None:
        g *= float(rp[f"rec_{cls}_gamma_pS"]) / float(rp["rec_lacr_gamma_pS"])
    return g


class Shot:
    """The shot-noise state for n synapses (numpy; the reference the brain uses)."""

    def __init__(self, gq, tau, cv, seed):
        self.gq, self.tau, self.cv, self.seed = np.asarray(gq, float), np.asarray(tau, float), float(cv), seed
        self.reset()

    def reset(self):
        self.rng = np.random.default_rng(self.seed)
        self.G = self.Gm = None
        self.n_ves, self.a_sum = 0, 0.0

    def step(self, gd, dt):
        gd = np.maximum(np.asarray(gd, float), 0.0)
        if self.G is None:
            self.G, self.Gm = gd.copy(), gd.copy()
        e = np.exp(-dt / self.tau)
        lam = gd / (self.gq * self.tau)                       # vesicles per ms
        N = self.rng.poisson(lam * dt)
        A = N.astype(float)
        k = N > 0
        if self.cv > 0 and k.any():
            A[k] = self.rng.gamma(N[k] / self.cv ** 2, self.cv ** 2)
        self.n_ves += int(N.sum())
        self.a_sum += float(A.sum())
        self.G = self.G * e + self.gq * (self.tau / dt) * (1 - e) * A
        self.Gm = self.Gm * e + gd * (1 - e)
        ok = self.Gm > 1e-15
        qn = np.ones_like(gd)
        qn[ok] = self.G[ok] / self.Gm[ok]
        self.G[~ok] = self.Gm[~ok]
        return qn, lam


class Mech:
    def __init__(self, brain, params, toggles):
        self.p, self.brain = params, brain
        self.on = form(toggles.get(M, "off")) == "quantal"
        w = getattr(brain, "wsyn", None) or []
        self.shot = None
        if not (w and self.on):
            return
        from wormemu.mech import receptors
        rp = getattr(brain, "_rk_p", None) or mech.params_for(receptors, brain.spec)
        cls = [None if c < 0 else mech.RECEPTOR_CLASSES[c] for _, _, _, c in w]
        gq = [quantal_g_uS(params, rp, c) for c in cls]
        tau = [float(pp.tau_off) if pp.mode >= 1 else params["noise_event_tau_ms"] for pp, *_ in w]
        seed = getattr(getattr(brain, "spec", None), "seed", None)
        self.shot = Shot(gq, tau, params["noise_amp_cv"], [0 if seed is None else int(seed), 26])
        h = brain.h
        self.gd, self.qn = h.PtrVector(len(w)), h.PtrVector(len(w))
        for i, (pp, *_) in enumerate(w):
            self.gd.pset(i, pp._ref_gd)
            self.qn.pset(i, pp._ref_qn)
        self.buf = h.Vector(len(w))
        post = np.array([j for _, _, j, _ in w])
        self.to_muscle = np.asarray(brain.is_muscle)[post]
        self.n_muscle = max(1, int(np.asarray(brain.is_muscle).sum()))
        self.reset()

    def reset(self):
        if self.shot is not None:
            self.shot.reset()
            self.qn.scatter(self.brain.h.Vector(np.ones(len(self.shot.gq))))

    def step(self, ctx, dt_ms):
        if self.shot is None:
            return {}
        self.gd.gather(self.buf)
        qn, lam = self.shot.step(self.buf.as_numpy().copy(), dt_ms)
        self.qn.scatter(self.brain.h.Vector(qn))
        return {"out": {"quantal_noise": dict(
            vesicles_per_s=float(lam.sum() * 1000.0), qn_sd=float(qn.std()),
            nmj_vesicles_per_s_per_muscle=float(lam[self.to_muscle].sum() * 1000.0 / self.n_muscle))}}
