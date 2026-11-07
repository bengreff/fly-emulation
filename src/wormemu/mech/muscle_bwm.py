"""Row 12: the body-wall muscle as a spiking cell, its gap junctions, its Ca and its force (activation).

    membrane   Du, Crodelle et al. 2025 (PLOS Comput Biol 21:e1012318; code github.com/XuexingDu/C.elegans-Muscle,
               CC-BY 4.0, Muscle_cell_model.ipynb, the final wild-type cell): EGL-19 (m^2 h), SHK-1 (n^4), SLO-2
               (Ca-gated, m_inf^3 p), a Kr (ERG-like, UNC-103) current, the NCA Na leak and a leak, every reversal
               but SLO-2's and Kr's shifted by V_th; one Ca shell with linear clearance. Fitted to whole-cell current
               clamp of wild-type BWM (simulation-based inference); fires Ca action potentials at 15-30 pA.
               NEURON: nmodl/organs/du_bwm.mod on BAAIWorm's 20 x 5 um muscle cylinder, BAAIWorm's passive leak set
               to zero, cm set so the cell has Du's 22 pF. CPU reference: DuMuscle (numpy, the paper's integrator).
    gaps       Liu et al. 2006 (J Biol Chem 281:7881): BWM-BWM junctional conductance "350 pS or less", independent
               of Vm; Cook 2019's 96 muscle-muscle contacts (the ledger's bwm_gap elements) at one conductance.
    Ca         the Du shell's Ca (model units: mM by the SLO-2 binding constant's units).
    force      Boyle, Berri and Cohen 2012 (Front Comput Neurosci 6:10): "muscles respond as leaky integrators with a
               characteristic time scale of tau_M = 100 ms"; here tau_M da/dt = Hill(Ca) - a, the Hill on the Du Ca
               (n and K_half guessed). Output: act_add (95, BWM_NAMES order).

Nested simpler forms (toggle values):
    muscle_ca          du2025 (default) | sigmoid (the old lumped V -> Ca on the passive muscle) | off
    muscle_activation  bbc2012 (default) | rise_decay (the old two-time-constant Hill) | off
    bwm_membrane       du2025 (default) | off (BAAIWorm's passive muscle, or c302's with the brain's muscle_active)
    bwm_gap_liu        on (default) | off
The ids muscle_ca and muscle_activation are brain_layers' ids, so this module takes those toggles over.
"""
from __future__ import annotations

import numpy as np

from wormemu.brain_layers import Spec
from wormemu.interface import BWM_NAMES

DU = "Du, Crodelle et al. 2025 PLOS Comput Biol 21:e1012318 (code: XuexingDu/C.elegans-Muscle, Muscle_cell_model)"
LIU = "Liu, Chen and Wang 2006 J Biol Chem 281:7881 (BWM gap junctions, Gj <= 350 pS)"
BBC = "Boyle, Berri and Cohen 2012 Front Comput Neurosci 6:10 (Table 3, tau_M = 100 ms)"
OLD = "brain_layers lumped muscle layer (the nested simpler form)"

MECHANISMS = [
    ("bwm_membrane", "Body-wall muscle membrane: Du/Crodelle 2025 spiking HH (EGL-19, SHK-1, SLO-2, Kr, NCA, leak)",
     "muscle", "du2025"),
    ("muscle_ca", "BWM Ca: Du 2025 Ca shell (nested: lumped sigmoid of V)", "muscle", "du2025"),
    ("muscle_activation", "BWM Ca -> activation: Boyle-Berri-Cohen 2012 leaky integrator (nested: rise/decay Hill)",
     "muscle", "bbc2012"),
    ("bwm_gap_liu", "BWM-BWM gap junctions (Cook 2019 contacts, Liu 2006 conductance)", "muscle", "on"),
]

_M = "bwm_membrane"
_G = "body-wall muscle"


def _du(pid, unit, v, lo, hi, notes="", label="published_fit"):
    return Spec(pid, _M, unit, v, lo, hi, source=DU, label=label, grain="class", applies_to=_G, notes=notes)


_FIT = "fitted to WT current clamp (SBI); range 0.5-2x the fit, guessed (the prior box is in S1 Table, not opened)"
_SET = "set by the authors in the model code, not fitted; range guessed"
SPECS = [
    _du("bwm_du_gca_nS", "nS", 19.8, 9.9, 39.6, _FIT),
    _du("bwm_du_gk_nS", "nS", 37.0, 18.5, 74.0, _FIT),
    _du("bwm_du_gslo2_nS", "nS", 3.6, 1.8, 7.2, _SET, "published_fit"),
    _du("bwm_du_gkr_nS", "nS", 3.2, 1.6, 6.4, _SET),
    _du("bwm_du_gna_nS", "nS", 0.1, 0.05, 0.2, _SET),
    _du("bwm_du_gl_nS", "nS", 0.1, 0.05, 0.2, _FIT),
    _du("bwm_du_gm_nS", "nS", 0.0, 0.0, 0.1, "M current p_max: 0 in the final WT fit (0.1 the class default)"),
    _du("bwm_du_c_pF", "pF", 22.0, 11.0, 44.0, _FIT),
    _du("bwm_du_vth_mV", "mV", 10.0, 0.0, 20.0, "voltage shift; " + _FIT),
    _du("bwm_du_eca_mV", "mV", 60.0, 40.0, 80.0, "before the V_th shift; " + _SET),
    _du("bwm_du_ek_mV", "mV", -40.0, -60.0, -20.0, "SHK-1 and M use EK + V_th, SLO-2 and Kr EK itself; " + _SET),
    _du("bwm_du_ena_mV", "mV", 15.0, 0.0, 30.0, "before the V_th shift; " + _SET),
    _du("bwm_du_el_mV", "mV", -24.0, -40.0, -10.0, "before the V_th shift; " + _SET),
    _du("bwm_du_slo2_alpha", "1/(ms mM2)", 43.0, 29.0, 58.0,
        "SLO-2 Ca binding; the code's 43, the paper's text 58 (range spans both)"),
    _du("bwm_du_slo2_beta", "1/ms", 0.09, 0.045, 0.18, "SLO-2 unbinding; " + _SET),
    _du("bwm_du_slo2_phi", "1", 0.04, 0.02, 0.08, "SLO-2 gate rate factor; " + _SET),
    _du("bwm_du_phi_m", "1", 1.2, 0.6, 2.4, "EGL-19 activation rate factor; " + _SET),
    _du("bwm_du_phi_n", "1", 1.2, 0.6, 2.4, "SHK-1 activation rate factor; " + _SET),
    _du("bwm_du_tau_h_ms", "ms", 24.0, 12.0, 48.0, "EGL-19 inactivation; " + _SET),
    _du("bwm_du_tau_kr_ms", "ms", 62.0, 31.0, 124.0, "Kr gate; " + _SET),
    _du("bwm_du_ca_influx", "mM/(ms pA)", 1.5e-5, 0.75e-5, 3.0e-5, "Ca shell: dCa = -k I_Ca - (Ca - Ca0)/tau; " + _SET),
    _du("bwm_du_ca_tau_ms", "ms", 1 / 0.075, 6.67, 26.7, "Ca shell clearance (the code's rate 0.075/ms); " + _SET),
    _du("bwm_du_ca0_mM", "mM", 0.001, 0.0001, 0.01, "Ca shell rest; " + _SET),
    _du("bwm_du_input_scale", "1", 0.75, 0.5, 1.0,
        "the code divides injected current by this (a seal/space-clamp factor); used only for the unit check"),
    Spec("bwm_gap_liu_nS", "bwm_gap_liu", "nS", 0.2, 0.05, 0.35, source=LIU, label="inferred", grain="class",
         applies_to=_G, notes="one conductance for every Cook BWM-BWM contact; Liu 2006 measured <= 350 pS (whole "
         "Gj per pair, voltage-independent at small Vj); template inside, guessed"),
    Spec("bwm_act_tau_ms", "muscle_activation", "ms", 100.0, 50.0, 200.0, source=BBC, label="published_fit",
         lit="F9", grain="class", applies_to=_G, notes="Boyle 2012 Table 3 tau_M (a model value set from the "
         "literature they cite); one time constant for rise and fall"),
    Spec("bwm_act_hill", "muscle_activation", "1", 2.0, 1.0, 4.0, label="guessed", lit="F7", grain="class",
         applies_to=_G, notes="Hill of Du-shell Ca -> activation"),
    Spec("bwm_act_khalf_mM", "muscle_activation", "mM", 0.014, 0.002, 0.05, label="guessed", grain="class",
         applies_to=_G, notes="Du-shell Ca at half activation; set (before any closed loop) to the mean shell Ca of a "
         "cell firing at 15 and 20 pA in the unit-check run (0.012, 0.016 mM), not to any behaviour"),
]

# nested forms reuse brain_layers' own specs (mca_*, mact_*), read from params when present
_OLD = {"mca_vhalf_mV": -20.0, "mca_k_mV": 5.0, "mca_max_uM": 1.0, "mact_hill": 2.0, "mact_khalf_uM": 0.5,
        "mact_tau_rise_ms": 50.0, "mact_tau_decay_ms": 100.0}


def _sig(x):
    return 1.0 / (1.0 + np.exp(-x))


# --- the CPU reference: Du's equations as published, the paper's exponential-Euler integrator ----------------
class DuMuscle:
    """n Du/Crodelle muscles in numpy. step(I_pA, dt) advances by dt ms with injected current I_pA (already divided
    by the input scale if reproducing the paper's protocol). State: V, m, h, n, p, kr, ps (SLO-2), ca (mM)."""

    def __init__(self, n, params=None):
        q = {s.id: s.template for s in SPECS}
        q.update({k: v for k, v in (params or {}).items() if k in q})
        self.q = q
        self.n = n
        self.reset()

    def reset(self, v0=-30.0):
        n = self.n
        self.V = np.full(n, v0)
        self.m, self.h, self.nk = np.full(n, 0.01), np.full(n, 0.6), np.full(n, 0.99)
        self.p, self.kr, self.ps, self.ca = np.full(n, 0.2), np.zeros(n), np.zeros(n), np.zeros(n)

    # currents in pA (conductances nS, mV)
    def currents(self, V, m, h, nk, p, kr, ps):
        q = self.q
        vt = q["bwm_du_vth_mV"]
        ica = q["bwm_du_gca_nS"] * m ** 2 * h * (V - vt - q["bwm_du_eca_mV"])
        ik = q["bwm_du_gk_nS"] * nk ** 4 * (V - vt - q["bwm_du_ek_mV"])
        im = q["bwm_du_gm_nS"] * p * (V - vt - q["bwm_du_ek_mV"])
        islo2 = q["bwm_du_gslo2_nS"] * _sig((V + 33.4) / 3.2) ** 3 * ps * (V - q["bwm_du_ek_mV"])
        ina = q["bwm_du_gna_nS"] * (V - vt - q["bwm_du_ena_mV"])
        ikr = q["bwm_du_gkr_nS"] * (1 - kr) * 0.5 * (1 + np.tanh((V - vt + 42) / 5.0)) * (V - q["bwm_du_ek_mV"])
        il = q["bwm_du_gl_nS"] * (V - vt - q["bwm_du_el_mV"])
        return ica, ik + im + islo2 + ikr, ina + il

    def rates(self, V):
        """(inf, tau) for m, h, n, p, kr at V."""
        q = self.q
        u = V - q["bwm_du_vth_mV"]
        tm = (0.4 + 0.7 / (np.exp(-(u + 5) / 15) + np.exp((u + 5) / 15))) / q["bwm_du_phi_m"]
        mi = _sig((u + 8) / 8.6)
        hi = 0.42 * _sig(-(u + 11) / 2) + 0.28
        ni = 0.5 * (np.tanh((u + 15.2) / 36.22) + 1)
        tn = (1.18 + 511.78 / (1 + np.exp((u + 89.3) / 21.92))) / q["bwm_du_phi_n"]
        pi = _sig((u + 45) / 10)
        tp = 4000 / (3.38 * np.exp((u + 45) / 20) + np.exp(-(u + 45) / 20))
        kri = 0.5 * (1 + np.tanh((u + 42) / 5.0))
        return (mi, tm), (hi, q["bwm_du_tau_h_ms"]), (ni, tn), (pi, tp), (kri, q["bwm_du_tau_kr_ms"])

    def step(self, I_pA, dt):
        q = self.q
        V = self.V
        C = q["bwm_du_c_pF"]

        def f(v):
            a, b, c = self.currents(v, self.m, self.h, self.nk, self.p, self.kr, self.ps)
            return (-a - b - c + I_pA) / C

        f0 = f(V)
        J = (f(V + 1e-4) - f0) / 1e-4
        J = np.where(np.abs(J) < 1e-12, -1e-12, J)
        Vn = V + np.expm1(J * dt) / J * f0
        (mi, tm), (hi, th), (ni, tn), (pi, tp), (kri, tkr) = self.rates(V)
        e = lambda x, xi, tau: xi + (x - xi) * np.exp(-dt / tau)
        self.m, self.h, self.nk = e(self.m, mi, tm), e(self.h, hi, th), e(self.nk, ni, tn)
        self.p, self.kr = e(self.p, pi, tp), e(self.kr, kri, tkr)
        c2 = q["bwm_du_slo2_alpha"] * self.ca ** 2
        c3 = c2 + q["bwm_du_slo2_beta"]
        self.ps = e(self.ps, c2 / c3, 1.0 / (q["bwm_du_slo2_phi"] * c3))
        ica, _, _ = self.currents(V, self.m, self.h, self.nk, self.p, self.kr, self.ps)
        # the code integrates Ca with the gates already advanced (its update order: h, m, n, p, ps, then Ca)
        tau = q["bwm_du_ca_tau_ms"]
        cinf = q["bwm_du_ca0_mM"] - q["bwm_du_ca_influx"] * ica * tau
        self.ca = e(self.ca, cinf, tau)
        self.V = Vn
        return Vn


# the code's initial state (Muscle_cell_model: V -30 + N(0,1) noise, here without the noise). The cell has no stable
# rest: from this state it sits near -31 mV for ~300 ms, then depolarises and fires on its own from ~1.5 s (numpy
# reference, zero input: 19 spikes in 5 s); the net steady-state current crosses zero only at -2.4 mV.
INIT = dict(v=-30.0, m=0.01, h=0.6, n=0.99, p=0.2, kr=0.0, ps=0.0, cad=0.0)


def du_step_protocol(amps_pA=(30.0, 25.0, 20.0, 15.0), dt=0.1, t_on=57.8, t_off=257.8, t_end=500.0, params=None):
    """The paper's current-clamp protocol (Muscle_cell_model cell 2): V (n_t, n_amps), shell Ca, and time (ms)."""
    m = DuMuscle(len(amps_pA), params)
    amps = np.asarray(amps_pA, float) / m.q["bwm_du_input_scale"]
    nt = int(round(t_end / dt))
    V, ca = np.empty((nt, len(amps))), np.empty((nt, len(amps)))
    for k in range(nt):
        t = k * dt
        m.step(np.where((t >= t_on) & (t < t_off), amps, 0.0), dt)
        V[k], ca[k] = m.V, m.ca
    return V, ca, np.arange(nt) * dt


def upcrossings(v, thr=0.0):
    return int(np.sum((v[:-1] < thr) & (v[1:] >= thr)))


# --- NEURON ---------------------------------------------------------------------------------------------------
MOD = {"gca": "bwm_du_gca_nS", "gk": "bwm_du_gk_nS", "gm": "bwm_du_gm_nS", "gslo2": "bwm_du_gslo2_nS",
       "gkr": "bwm_du_gkr_nS", "gna": "bwm_du_gna_nS", "gl": "bwm_du_gl_nS", "vth": "bwm_du_vth_mV",
       "eca": "bwm_du_eca_mV", "ek": "bwm_du_ek_mV", "ena": "bwm_du_ena_mV", "el": "bwm_du_el_mV",
       "alpha": "bwm_du_slo2_alpha", "beta": "bwm_du_slo2_beta", "phi": "bwm_du_slo2_phi", "phi_m": "bwm_du_phi_m",
       "phi_n": "bwm_du_phi_n", "tau_h": "bwm_du_tau_h_ms", "tau_kr": "bwm_du_tau_kr_ms",
       "kca": "bwm_du_ca_influx", "tau_ca": "bwm_du_ca_tau_ms", "ca0": "bwm_du_ca0_mM"}


def configure(sec, q, area):
    """Set du_bwm's parameters on every segment of sec from the spec values q (whole-cell, so each segment gets its
    share of the area)."""
    for seg in sec:
        m = seg.du_bwm
        for name, pid in MOD.items():
            setattr(m, name, float(q[pid]))
        m.area_um2 = area


# --- the mechanism ------------------------------------------------------------------------------------------------
class Mech:
    """Builds the Du membrane on every body-wall muscle soma, the Liu gaps, and steps Ca -> activation."""

    def __init__(self, brain, params, toggles):
        self.brain = brain
        q = {s.id: s.template for s in SPECS}
        q.update(_OLD)
        q.update({k: float(v) for k, v in params.items() if np.isscalar(v)})
        self.q = q
        self.mem = toggles.get("bwm_membrane", "du2025")
        self.ca_form = toggles.get("muscle_ca", "du2025")
        self.act_form = toggles.get("muscle_activation", "bbc2012")
        self.gaps = toggles.get("bwm_gap_liu", "on")
        assert self.mem in ("du2025", "off") and self.ca_form in ("du2025", "sigmoid", "off")
        assert self.act_form in ("bbc2012", "rise_decay", "off") and self.gaps in ("on", "off")
        if self.ca_form == "du2025" and self.mem != "du2025":
            raise ValueError("muscle_ca=du2025 reads the Du membrane's Ca shell: needs bwm_membrane=du2025")
        if self.mem == "du2025" and getattr(brain, "mact", False):
            raise ValueError("bwm_membrane=du2025 and muscle_active (c302's muscle) both on: pick one membrane")
        if self.gaps == "on" and toggles.get("bwm_coupling") == "on":
            raise ValueError("bwm_gap_liu and bwm_coupling both on: the same 96 Cook muscle gaps twice")
        h = brain.h
        self.bwm = np.asarray(brain.bwm)
        self.have = self.bwm >= 0
        self.n_gaps = 0
        if self.mem == "du2025":
            from wormemu.mech import organs_nrn
            organs_nrn.load_organ_mods(h)
            self._pca = h.PtrVector(int(self.have.sum()))
            k = 0
            for i in self.bwm[self.have]:
                sec = brain.soma[i]
                for seg in sec:
                    if h.ismembrane("pas", sec=sec):
                        seg.pas.g = 0.0              # Du's leak replaces BAAIWorm's
                sec.insert("du_bwm")
                area = organs_nrn.area_um2(sec)
                configure(sec, q, area)
                sec.cm = q["bwm_du_c_pF"] * 100.0 / area     # pF over um2 -> uF/cm2
                self._pca.pset(k, sec(0.5).du_bwm._ref_cad)
                k += 1
            self._buf = h.Vector(int(self.have.sum()))
        if self.gaps == "on":
            g_uS = q["bwm_gap_liu_nS"] / 1000.0
            for e in brain.spec.values["bwm_gap"].index:
                a, b = e.split("-")
                if a in brain.idx and b in brain.idx:
                    brain._gap(brain.segs[brain.idx[a]][0][0], brain.segs[brain.idx[b]][0][0], g_uS, "gap_bwm_liu")
                    self.n_gaps += 1
        self.reset()

    def reset(self):
        """Muscles to Du's initial state (call after the brain's finitialize, which starts every cell at its V_INIT):
        v and the du_bwm states set in place, so no other mechanism is re-initialised."""
        self.act = np.zeros(len(BWM_NAMES))
        self.ca = np.zeros(len(BWM_NAMES))
        if self.mem == "du2025":
            for i in self.bwm[self.have]:
                for seg in self.brain.soma[i]:
                    seg.v = INIT["v"]
                    for k, x in INIT.items():
                        if k != "v":
                            setattr(seg.du_bwm, k, x)

    def _read_ca(self, v_bwm):
        q = self.q
        if self.ca_form == "du2025":
            self._pca.gather(self._buf)
            ca = np.zeros(len(BWM_NAMES))
            ca[self.have] = self._buf.as_numpy()
            return ca                                       # mM (the Du shell)
        if self.ca_form == "sigmoid":
            return q["mca_max_uM"] * _sig((v_bwm - q["mca_vhalf_mV"]) / q["mca_k_mV"])     # uM
        return np.zeros(len(BWM_NAMES))

    def activation(self, ca, dt):
        q = self.q
        if self.act_form == "bbc2012":
            n = q["bwm_act_hill"]
            k = q["bwm_act_khalf_mM"] if self.ca_form == "du2025" else q["mact_khalf_uM"]
            target = ca ** n / (ca ** n + k ** n)
            self.act = target + (self.act - target) * np.exp(-dt / q["bwm_act_tau_ms"])
        elif self.act_form == "rise_decay":                 # brain_layers' form, verbatim
            n = q["mact_hill"]
            k = q["bwm_act_khalf_mM"] if self.ca_form == "du2025" else q["mact_khalf_uM"]
            target = ca ** n / (ca ** n + k ** n)
            tau = np.where(target > self.act, q["mact_tau_rise_ms"], q["mact_tau_decay_ms"])
            self.act = self.act + (target - self.act) * np.minimum(1.0, dt / tau)
        else:
            self.act = np.zeros(len(BWM_NAMES))
        return self.act

    def step(self, ctx, dt_ms):
        v = np.asarray(ctx.v)
        vb = np.where(self.have, v[np.maximum(self.bwm, 0)], -30.0 if self.mem == "du2025" else -65.0)
        self.ca = self._read_ca(vb)
        act = self.activation(self.ca, dt_ms)
        out = {"bwm_activation": act.copy()}
        if self.ca_form == "du2025":
            out["bwm_ca_mM"] = self.ca.copy()
        return {"act_add": act.copy(), "out": out}
