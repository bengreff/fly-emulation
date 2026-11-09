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
fewer quanta rather than smaller ones; the Mg block is outside gd. Draws come from the brain's noise seed
(Experiment.noise_seed; None = the worm's seed, the template worm: 0), rebuilt at reset, so a reset replays the same
noise. Forms: quantal (default) / off (qn = 1, the deterministic synapse).

Channel noise (row 26's other half): port of Linaro, Storace and Giugliano 2011 (PLoS Comput Biol 7:e1001102), the
diffusion approximation in its conductance form. The gating variables stay deterministic; each channel population's
conductance gets a sum of Ornstein-Uhlenbeck terms carrying the exact second-order statistics of N independent
channels at the current voltage. A channel is open when all its independent two-state gates are (p = prod x_k^n_k),
so its open-state autocovariance is
    C(t) = prod_k (x_k^2 + x_k (1 - x_k) e^(-t/tau_k))^n_k - p^2 = sum over nonzero j of W_j e^(-r_j t),
    W_j = prod_k C(n_k, j_k) x_k^(2(n_k - j_k)) (x_k (1 - x_k))^j_k,   r_j = sum_k j_k / tau_k
(Linaro's product-of-covariances rule: 7 terms for m^3 h, 4 for n^4). Each term is an OU process of variance
Gmax gamma W_j (Gmax = density x soma area, gamma the unit conductance, so N = Gmax / gamma) and time constant 1/r_j,
with x = the mod's x_inf and tau its time constant at the current voltage (RANGE values; SHL-1's scaled as in its
DERIVATIVE block). Weighted forms (SHL-1 0.7 hf + 0.3 hs, KQT-3, EGL-36) are subpopulations. The terms are
integrated exactly over each brain step (the OU process and its integral, Gillespie 1996 Phys Rev E 54:2084) and
injected at the soma as the step-mean current -dG (V - E), with V the soma voltage at the step's start. Validity:
somatic channels only (BAAIWorm puts every active channel in the soma); gates independent (the SLO channels' m and
the coupled CaV's hcav taken as independent); voltage held over the 1 ms step. NCA has no gate in the model, so no
noise. Neurons only (muscle membranes are B2's). Unit conductances are guessed per channel family. Forms: diffusion
(default) / off.
"""
from __future__ import annotations

import itertools
from math import comb

import numpy as np

from wormemu import mech
from wormemu.brain_layers import Spec

MECHANISMS = [("quantal_noise", "Quantal (vesicle) release noise at chemical synapses", "synapse", "quantal"),
              ("channel_noise", "Ion channel noise at each neuron's soma (diffusion approximation, Linaro 2011)",
               "channel", "diffusion")]
FORMS = ("quantal", "off")
CFORMS = ("diffusion", "off")
M, C = "quantal_noise", "channel_noise"
LIU = "Liu, Hollopeter and Jorgensen 2009 PNAS 106:10823 (PMC2705609)"
LINARO = "Linaro, Storace and Giugliano 2011 PLoS Comput Biol 7:e1001102"


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

# unit conductance per channel family (pS): template, lo, hi, the homologue family it is guessed from. No C. elegans
# single-channel recordings were opened for these; the papers that would pin them are named.
UNIT = {
    "slo1": (150.0, 50.0, 300.0, "BK family; C. elegans SLO-1 single channels (Wang et al. 2001 Neuron 32:867)"),
    "slo2": (100.0, 40.0, 200.0, "Slo2 family; C. elegans SLO-2 (Yuan et al. 2000 Nat Neurosci 3:771)"),
    "egl2": (8.0, 2.0, 20.0, "EAG family (Weinshenker et al. 1999 J Neurosci 19:9831 for EGL-2)"),
    "shl1": (6.0, 2.0, 15.0, "Kv4 family (Fawcett et al. 2006 J Biol Chem 281:30725 for SHL-1)"),
    "kqt3": (5.0, 1.0, 20.0, "KCNQ family (Wei et al. 2005 Neuron 46:? for KQT-3: not opened)"),
    "kvs1": (10.0, 3.0, 30.0, "Kv family (Bianchi et al. 2003 Nat Neurosci 6:1145 for KVS-1)"),
    "irk": (25.0, 5.0, 40.0, "Kir2 family"),
    "egl36": (15.0, 5.0, 30.0, "Kv3 family (Johnstone et al. 1997 Neuron 19:151 for EGL-36)"),
    "shk1": (10.0, 3.0, 25.0, "Kv1 family (Fawcett et al. 2006 for SHK-1)"),
    "kcnl": (10.0, 4.0, 20.0, "SK family"),
    "egl19": (5.0, 2.0, 25.0, "CaV1 family in physiological Ca (larger in Ba); C. elegans muscle EGL-19 single "
              "channels not found"),
    "unc2": (5.0, 2.0, 20.0, "CaV2 family"),
    "cca1": (5.0, 2.0, 10.0, "CaV3 family (Steger et al. 2005 J Neurosci 25:? for CCA-1: not opened)"),
}
for _f, (_t, _lo, _hi, _src) in UNIT.items():
    SPECS.append(Spec(f"chnoise_{_f}_pS", C, "pS", _t, _lo, _hi, f"single-channel conductance, {_src}; sets the "
                      f"channel count N = density x soma area / unit conductance ({LINARO})", "guessed",
                      grain="channel", applies_to=f"every neuron with {_f}"))

# BAAIWorm channel mod -> (unit-conductance family, subpopulations [(weight, [(x_inf, tau, power, tau scale)])], E)
_MH = [(1.0, [("minf", "tm", 1, 1.0), ("hinf", "th", 1, 1.0)])]
_M = [(1.0, [("minf", "tm", 1, 1.0)])]
_SLO = [(1.0, [("minf", "tm", 1, 1.0), ("hcavinf", "thcav", 1, 1.0)])]
CHANNEL_GATES = {
    "slo1_unc2": ("slo1", _SLO, -80.0), "slo1_egl19": ("slo1", _SLO, -80.0),
    "slo2_unc2": ("slo2", _SLO, -80.0), "slo2_egl19": ("slo2", _SLO, -80.0),
    "egl2": ("egl2", _M, -80.0), "irk": ("irk", _M, -80.0),
    "shl1": ("shl1", [(0.7, [("minf", "tm", 3, 0.4), ("hfinf", "thf", 1, 0.08)]),
                      (0.3, [("minf", "tm", 3, 0.4), ("hsinf", "ths", 1, 0.3)])], -80.0),
    "kqt3": ("kqt3", [(0.3, [("minf", "tmf", 1, 1.0), ("winf", "tw", 1, 1.0), ("sinf", "ts", 1, 1.0)]),
                      (0.7, [("minf", "tms", 1, 1.0), ("winf", "tw", 1, 1.0), ("sinf", "ts", 1, 1.0)])], "ek"),
    "unc2": ("unc2", _MH, 60.0), "kvs1": ("kvs1", _MH, -80.0), "egl19": ("egl19", _MH, 60.0),
    "shk1": ("shk1", _MH, -80.0),
    "egl36": ("egl36", [(0.33, [("mfinf", "tmf", 1, 1.0)]), (0.36, [("mminf", "tmm", 1, 1.0)]),
                        (0.39, [("msinf", "tms", 1, 1.0)])], -80.0),
    "cca1": ("cca1", [(1.0, [("minf", "tm", 2, 1.0), ("hinf", "th", 1, 1.0)])], 60.0),
    "kcnl": ("kcnl", [(1.0, [("cai", "a", 1, 1.0)])], -80.0),     # minf = cai/(kca + cai), tm = a (GLOBALs)
}


def form(v):
    v = "off" if v in (False, None) else v
    if v not in FORMS:
        raise ValueError(f"quantal_noise form {v!r} not in {FORMS}")
    return v


def cform(v):
    v = "diffusion" if v in ("on", True) else ("off" if v in (False, None) else v)
    if v not in CFORMS:
        raise ValueError(f"channel_noise form {v!r} not in {CFORMS}")
    return v


def terms(powers):
    """The nonzero exponent vectors j of the open-state autocovariance expansion for gates with these powers, and
    their binomial factors: (J (T, K), binom (T,))."""
    J = np.array([j for j in itertools.product(*[range(n + 1) for n in powers]) if any(j)], int)
    return J, np.array([np.prod([comb(n, k) for n, k in zip(powers, j)]) for j in J], float)


def weights(x, tau, powers, J, binom):
    """x, tau: (K, cells) gate values and time constants (ms). Returns W (cells, T), the term variances per channel
    (sum = p - p^2), and r (cells, T), their rates (1/ms)."""
    n = np.asarray(powers)
    a, b = (x * x).T[:, None, :], (x * (1 - x)).T[:, None, :]
    W = binom[None] * np.prod(a ** (n - J)[None] * b ** J[None], axis=2)
    return W, (J[None] / tau.T[:, None, :]).sum(axis=2)


def ou_step(y, s2, tau, dt, z1, z2):
    """Exact update over dt of OU terms (stationary variance s2, time constant tau) and their mean over the step
    (the process and its integral, Gillespie 1996 Phys Rev E 54:2084); z1, z2 standard normals."""
    u = dt / tau
    e, om = np.exp(-u), -np.expm1(-u)
    v1 = s2 * -np.expm1(-2 * u)
    cov = s2 * tau * om * om
    f = np.where(u < 1e-2, (2 / 3) * u ** 3 - 0.5 * u ** 4 + (7 / 30) * u ** 5, 2 * u - 3 + 4 * e - e * e)
    k = np.divide(cov, v1, out=np.zeros_like(cov), where=v1 > 0)
    n1 = np.sqrt(np.maximum(v1, 0.0)) * z1
    X = y * tau * om + k * n1 + np.sqrt(np.maximum(s2 * tau * tau * f - k * cov, 0.0)) * z2
    return y * e + n1, X / dt


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


class Quantal:
    def __init__(self, brain, params, toggles):
        self.p, self.brain = params, brain
        self.on = form(toggles.get(M, "off")) == "quantal"
        self.shot, self._bound = None, False

    def _bind(self):
        """Every wsyn synapse, the organ modules' too: they append theirs to brain.wsyn after noise is built (REGISTRY
        order), so the list is read at the first reset, when every module exists (Brain.step refuses to run before)."""
        self._bound = True
        brain, params = self.brain, self.p
        w = getattr(brain, "wsyn", None) or []
        if not (w and self.on):
            return
        from wormemu.mech import receptors
        rp = getattr(brain, "_rk_p", None) or mech.params_for(receptors, brain.spec)
        cls = [None if c < 0 else mech.RECEPTOR_CLASSES[c] for _, _, _, c in w]
        gq = [quantal_g_uS(params, rp, c) for c in cls]
        tau = [float(pp.tau_off) if pp.mode >= 1 else params["noise_event_tau_ms"] for pp, *_ in w]
        seed = getattr(brain, "noise_seed", getattr(getattr(brain, "spec", None), "seed", None))
        self.shot = Shot(gq, tau, params["noise_amp_cv"], [0 if seed is None else int(seed), 26])
        h = brain.h
        self.gd, self.qn = h.PtrVector(len(w)), h.PtrVector(len(w))
        for i, (pp, *_) in enumerate(w):
            self.gd.pset(i, pp._ref_gd)
            self.qn.pset(i, pp._ref_qn)
        self.buf = h.Vector(len(w))
        post = np.array([j for _, _, j, _ in w])
        self.to_muscle = (post >= 0) & np.asarray(brain.is_muscle)[np.maximum(post, 0)]   # post -1: an organ cell
        self.n_muscle = max(1, int(np.asarray(brain.is_muscle).sum()))

    def reset(self):
        if not self._bound:
            self._bind()
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


class Channel:
    """Channel noise at every neuron's soma (module docstring). Gate values are read from the mods each step."""

    def __init__(self, brain, params, toggles):
        self.on = cform(toggles.get(C, "off")) == "diffusion"
        self.groups, self.brain = [], brain
        if not self.on or not getattr(brain, "soma", None):
            return
        from wormemu.brain import GB
        h = brain.h
        musc = np.asarray(brain.is_muscle, bool)
        self.n = len(brain.soma)
        seed = getattr(brain, "noise_seed", getattr(getattr(brain, "spec", None), "seed", None))
        self.seed = [0 if seed is None else int(seed), 26, 1]
        self.n_channels = np.zeros(self.n)
        for ch, (fam, subs, E) in CHANNEL_GATES.items():
            cells = [i for i, s in enumerate(brain.soma) if not musc[i] and h.ismembrane(ch, sec=s)]
            if not cells:
                continue
            seg = [brain.soma[i](0.5) for i in cells]
            gam = params[f"chnoise_{fam}_pS"] / 1000.0                        # nS
            gb = h.PtrVector(len(cells))
            for k, sg in enumerate(seg):
                gb.pset(k, getattr(sg, f"_ref_{GB.get(ch, f'gb{ch}')}_{ch}"))
            # gb acts as S/cm2 (NEURON reads density currents as mA/cm2, whatever the mod's UNITS block says), so
            # Gmax (nS) = gb x area (um2) x 10
            area = np.array([sg.area() for sg in seg]) * 10.0
            Ev = np.array([sg.ek for sg in seg]) if E == "ek" else np.full(len(cells), E)
            g = dict(ch=ch, cells=np.array(cells), gb=gb, area=area, E=Ev, gam=gam, subs=[])
            for w, gates in subs:
                ptr = []
                for xi, ti, _, _ in gates:
                    if ch == "kcnl":
                        px = h.PtrVector(len(cells))
                        for k, sg in enumerate(seg):
                            px.pset(k, sg._ref_cai)
                        ptr.append((px, None))
                        continue
                    pv = []
                    for nm in (xi, ti):
                        q = h.PtrVector(len(cells))
                        for k, sg in enumerate(seg):
                            q.pset(k, getattr(sg, f"_ref_{nm}_{ch}"))
                        pv.append(q)
                    ptr.append(tuple(pv))
                pw = [n for _, _, n, _ in gates]
                J, binom = terms(pw)
                g["subs"].append(dict(w=w, ptr=ptr, pw=pw, scale=np.array([sc for *_, sc in gates])[:, None],
                                      J=J, binom=binom, y=None))
            self.groups.append(g)
        self.buf = {}
        self.reset()

    def _read(self, pv):
        n = int(pv.size())
        if n not in self.buf:
            self.buf[n] = self.brain.h.Vector(n)
        pv.gather(self.buf[n])
        return self.buf[n].as_numpy().copy()

    def reset(self):
        if not self.groups:
            return
        self.rng = np.random.default_rng(self.seed)
        h = self.brain.h
        self.kca, self.ka = float(h.kca_kcnl), float(h.a_kcnl)                # kcnl's GLOBALs (always compiled)
        self.n_channels[:] = 0.0
        for g in self.groups:
            for sb in g["subs"]:
                sb["y"] = None
            self.n_channels[g["cells"]] += self._read(g["gb"]) * g["area"] * sum(sb["w"] for sb in g["subs"]) \
                / g["gam"]

    def gates(self, g, sb):
        xs, ts = [], []
        for pv in sb["ptr"]:
            if pv[1] is None:                                                 # kcnl: from Ca
                ca = self._read(pv[0])
                xs.append(ca / (self.kca + ca))
                ts.append(np.full(len(ca), self.ka))
            else:
                xs.append(self._read(pv[0]))
                ts.append(self._read(pv[1]))
        return np.clip(np.array(xs), 0.0, 1.0), np.maximum(np.array(ts) * sb["scale"], 1e-6)

    def step(self, ctx, dt_ms):
        if not self.groups:
            return {}
        I = np.zeros(self.n)
        for g in self.groups:
            gmax = self._read(g["gb"]) * g["area"]                            # nS (area carries the x10)
            dG = np.zeros(len(g["cells"]))
            for sb in g["subs"]:
                x, tau = self.gates(g, sb)
                W, r = weights(x, tau, sb["pw"], sb["J"], sb["binom"])
                s2 = (sb["w"] * gmax * g["gam"])[:, None] * W                 # nS^2
                z0, z1, z2 = (self.rng.standard_normal(W.shape) for _ in range(3))
                if sb["y"] is None:
                    sb["y"] = np.sqrt(s2) * z0                                # start stationary
                sb["y"], m = ou_step(sb["y"], s2, 1.0 / r, dt_ms, z1, z2)
                dG += m.sum(axis=1)
            I[g["cells"]] -= dG * (ctx.v[g["cells"]] - g["E"])                # nS x mV = pA, inward positive
        nn = ~np.asarray(self.brain.is_muscle, bool)
        return {"I_pA": I, "out": {C: dict(I_rms_pA=float(np.sqrt(np.mean(I[nn] ** 2))),
                                           channels_median=float(np.median(self.n_channels[nn])))}}


class Mech:
    def __init__(self, brain, params, toggles):
        self.q = Quantal(brain, params, toggles)
        self.c = Channel(brain, params, toggles)

    def reset(self):
        self.q.reset()
        self.c.reset()

    def step(self, ctx, dt_ms):
        r, rc = self.q.step(ctx, dt_ms), self.c.step(ctx, dt_ms)
        if rc:
            r = dict(r) if r else {}
            r["I_pA"] = rc["I_pA"]
            r.setdefault("out", {}).update(rc["out"])
        return r
