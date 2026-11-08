"""Row 13: the pharynx as muscle cells driven by the pharyngeal nervous system; pumps counted from muscle Ca.

    membrane   Sherman & Harel 2024 (PNAS 121:e2302660121; code github.com/DanaSherman/CelegansPharynx, GPLv3):
               CCA-1 (m^2 h, Na + Ca), EGL-19 (m^2 f, Na + Ca, f inactivated by shell Ca), EXP-2 (m^4 h^4, with
               separate deactivation / de-inactivation kinetics while V falls), leak; GHK Ca flux into a 2 %-radius
               shell, radial diffusion to the core, clearance to rest (tau 50 ms). Fitted (genetic algorithm) to the
               TB muscle's intracellular AP (their Table 3). NEURON: nmodl/organs/sh_pharynx.mod.
    cells      the 20 pharyngeal muscles (interface.PHARYNX_MUSCLES) and the 9 marginal cells, one compartment each,
               built here (the brain has only neurons and body-wall muscles). The paper's 1-D finite-element cable
               is replaced by these compartments; each muscle gets 1/20 of the whole pharynx's capacitance
               (Shtonda & Avery 2005, 362.6 pF). Marginal cells are passive.
    coupling   Cook 2019's gap junctions: pm-pm and pm-marginal at one per-contact conductance (EAT-5 innexin,
               Starich 1996: eat-5 desynchronises corpus and terminal bulb; value guessed), neuron-pm at the ledger's
               shared neuron gap per contact.
    synapses   Cook 2019's chemical synapses onto pm and marginal cells, at the ledger's shared NMJ conductance per
               contact on the brain's graded synapse; sign from the brain's sign rule, except M3 (glutamate onto the
               AVR-15 GluCl: inhibitory; Dent et al. 1997, Raizen & Avery 1994). MC reaches the muscle through the
               marginal cells it synapses on (Cook) and their gaps. NSM's release sites are not fast synapses: its 5-HT
               reaches the muscle through the brain's well-mixed monoamine layer, on SER-7 (pharyngeal muscle
               expression: Hobson et al. 2006), with the layer's ec50 and gain for that receptor.
    force      Sherman & Harel's MLCK rate K1 = K1_A Ca^4 / (K1_B^4 + Ca^4) on the core Ca, normalised by K1_A: the
               nested reduced form of their cross-bridge model (their actin-myosin cycle is not ported).
    pumps      one pump = the metacorpus (pm4) mean activation rising above pump_on and then falling below pump_off;
               no clock. The EPG is reported as the mean dV/dt over the muscles (Raizen & Avery 1994: the EPG is
               dominated by the capacitive current; E spike positive, R spike negative).

Nested simpler forms: pharynx = sherman2024 (default) | clock (brain_layers' lumped pump oscillator, verbatim) | off.
The id pharynx is brain_layers' id, so this module takes that toggle over.
"""
from __future__ import annotations

import numpy as np

from wormemu.brain_layers import Spec
from wormemu.interface import PHARYNX_MUSCLES

SH = "Sherman & Harel 2024 PNAS 121:e2302660121 (code: DanaSherman/CelegansPharynx, gene.cc / Params.h / main.cc)"
SA = "Shtonda & Avery 2005 J Exp Biol 208:2177, as quoted by Palyanov et al. 2017 bioRxiv 228650 (not opened)"
COOK = "Cook et al. 2019 Nature 571:63 (SI 5 adjacency, pharynx)"
OLD = "brain_layers lumped pump oscillator (the nested simpler form)"

MECHANISMS = [
    ("pharynx", "Pharynx: Sherman & Harel 2024 muscle cells on Cook wiring, pumps from Ca (nested: lumped clock)",
     "organ", "sherman2024"),
]

MARGINAL = ["mc1DL", "mc1DR", "mc1V", "mc2DL", "mc2DR", "mc2V", "mc3DL", "mc3DR", "mc3V"]
M3 = ("M3L", "M3R")
NSM = ("NSML", "NSMR")
METACORPUS = [i for i, n in enumerate(PHARYNX_MUSCLES) if n.startswith("pm4")]

_P = "pharynx"
_G = "pharyngeal muscle"
_FIT = "fitted by the authors' genetic algorithm to TB AP features; range guessed (0.5-2x, or +-10 mV)"
_SET = "set by the authors in Params.h / main.cc, not fitted; range guessed"


def _sh(pid, unit, v, lo=None, hi=None, notes=_FIT, label="published_fit"):
    if lo is None:
        lo, hi = (v - 10.0, v + 10.0) if unit == "mV" else sorted((0.5 * v, 2.0 * v))
    return Spec(pid, _P, unit, v, lo, hi, source=SH, label=label, grain="class", applies_to=_G, notes=notes)


SPECS = [
    # conductances and permeabilities (gene.cc "known"; the flat-metacorpus g_egl19_na)
    _sh("ph_sh_g_cca1_na", "mS/cm2", 2.5),
    _sh("ph_sh_p_cca1_ca", "code units", 0.009, notes=_FIT + "; times the GHK term it is used as uA/cm2 (main.cc)"),
    _sh("ph_sh_g_egl19_na", "mS/cm2", 0.1509, notes=_FIT + "; flat-metacorpus geometry value (spherical: 0.1523)"),
    _sh("ph_sh_p_egl19_ca", "code units", 0.001, notes=_FIT + "; used as uA/cm2 with the GHK term"),
    _sh("ph_sh_g_exp2", "mS/cm2", 0.8),
    _sh("ph_sh_g_l", "mS/cm2", 0.057651, notes=_SET + " (main.cc g_l)", label="published_fit"),
    _sh("ph_sh_v_l", "mV", -73.0, -76.0, -70.0, "leak reversal = the TB interpump potential, -73 +- 1 mV (Table 3)",
        "measured"),
    _sh("ph_sh_v_na", "mV", 69.0, 50.0, 80.0, _SET),
    _sh("ph_sh_v_k", "mV", -82.0, -95.0, -75.0, _SET),
    # CCA-1 gates
    _sh("ph_sh_cca1_minf_a2", "1", 1.0, 0.5, 1.0),
    _sh("ph_sh_cca1_minf_v0", "mV", -30.0, notes=_FIT + "; S&H moved CCA-1's peak to -20 mV to get the AP shape"),
    _sh("ph_sh_cca1_minf_dv", "mV/e", 5.0, 2.5, 10.0),
    _sh("ph_sh_cca1_mtau_a1", "ms", 2.7),
    _sh("ph_sh_cca1_mtau_a2", "ms", 22.3),
    _sh("ph_sh_cca1_mtau_v0", "mV", -52.0),
    _sh("ph_sh_cca1_mtau_dv", "mV/e", -8.0, -16.0, -4.0),
    _sh("ph_sh_cca1_mtau_deact", "ms", 1.0),
    _sh("ph_sh_cca1_hinf_v0", "mV", -76.0),
    _sh("ph_sh_cca1_hinf_dv", "mV/e", -4.0, -8.0, -2.0),
    _sh("ph_sh_cca1_htau_a1", "ms", 1.0),
    _sh("ph_sh_cca1_htau_a2", "ms", 250.0),
    _sh("ph_sh_cca1_htau_v0", "mV", 0.0),
    _sh("ph_sh_cca1_htau_dv", "mV/e", -4.5, -9.0, -2.25),
    # EGL-19 gates
    _sh("ph_sh_egl19_minf_v0", "mV", 5.6),
    _sh("ph_sh_egl19_minf_dv", "mV/e", 7.5),
    _sh("ph_sh_egl19_mtau_a1", "ms", 0.5455),
    _sh("ph_sh_egl19_mtau_a2", "ms", 0.9635),
    _sh("ph_sh_egl19_mtau_v0", "mV", 8.5),
    _sh("ph_sh_egl19_mtau_dv", "mV/e", 3.0),
    _sh("ph_sh_egl19_finf_a1", "1", 0.8, 0.4, 1.0),
    _sh("ph_sh_egl19_finf_ca05", "M", 1.3e-4),
    _sh("ph_sh_egl19_finf_dca", "M/e", -5e-6, -1e-5, -2.5e-6),
    _sh("ph_sh_egl19_ftau_a1", "ms", 5.0),
    _sh("ph_sh_egl19_ftau_a2", "ms", 50.0),
    _sh("ph_sh_egl19_ftau_ca05", "M", 1e-4),
    _sh("ph_sh_egl19_ftau_dca", "M/e", 1e-5),
    # EXP-2 gates
    _sh("ph_sh_exp2_minf_v0", "mV", -15.5),
    _sh("ph_sh_exp2_minf_dv", "mV/e", 7.0),
    _sh("ph_sh_exp2_mtau_a1", "ms", 15.0),
    _sh("ph_sh_exp2_mtau_a2", "ms", 730.0),
    _sh("ph_sh_exp2_mtau_v0", "mV", -20.0),
    _sh("ph_sh_exp2_mtau_dv", "1/mV^pow", -0.15, -0.3, -0.075),
    _sh("ph_sh_exp2_mtau_pow", "1", 0.8, 0.4, 1.6),
    _sh("ph_sh_exp2_mdeact_a1", "ms", 65.0),
    _sh("ph_sh_exp2_mdeact_a2", "ms", 75.2),
    _sh("ph_sh_exp2_mdeact_v0", "mV", -83.9),
    _sh("ph_sh_exp2_mdeact_dv", "mV/e", -3.4, -6.8, -1.7),
    _sh("ph_sh_exp2_hinf_v0", "mV", -5.0),
    _sh("ph_sh_exp2_hinf_dv", "mV/e", -1.0, -2.0, -0.5),
    _sh("ph_sh_exp2_htau_a1", "ms", 0.3),
    _sh("ph_sh_exp2_htau_a2", "ms", 18.0),
    _sh("ph_sh_exp2_htau_v0", "mV", -60.0),
    _sh("ph_sh_exp2_htau_dv", "mV/e", -20.0, -40.0, -10.0),
    _sh("ph_sh_exp2_hdeinact", "ms", 1.0),
    # Ca
    _sh("ph_sh_ca_tau_ms", "ms", 50.0, 10.0, 300.0, _FIT + "; range = the GA's search box"),
    _sh("ph_sh_ca_out_M", "M", 0.003, 0.001, 0.01, _SET + " (bath Ca)"),
    _sh("ph_sh_ca_rest_M", "M", 5e-8, 2e-8, 1.5e-7, _SET),
    _sh("ph_sh_ca_diff_cm2_s", "cm2/s", 3.5e-6, 1e-6, 7e-6, _SET + " (cytoplasmic Ca diffusion)"),
    _sh("ph_sh_shell_frac", "1", 0.02, 0.01, 0.05, _SET + " (shell thickness / radius)"),
    _sh("ph_sh_gas_R", "J/(mol K)", 8.68815102, 8.314, 8.7,
        _SET + ": the code's value of R (sic; the true gas constant is 8.314), kept because the fit used it"),
    _sh("ph_sh_temp_K", "K", 295.65, 293.0, 298.0, "recording temperature, 22.5 C", "measured"),
    Spec("ph_radius_um", _P, "um", 10.0, 5.0, 20.0, source=SH + " (geometry: corpus ~10 um, TB ~20 um outer radius)",
         label="inferred", grain="class", applies_to=_G, notes="one radius for every compartment's shell geometry"),
    Spec("ph_area_um2", _P, "um2", 1813.0, 1000.0, 4000.0, source=SA, label="derived", grain="class", applies_to=_G,
         notes="whole-pharynx C 362.6 +- 36.8 pF at 1 uF/cm2 = 36,260 um2, split evenly over the 20 muscles"),
    Spec("ph_cm_uF_cm2", _P, "uF/cm2", 1.0, 0.8, 1.2, source=SH, label="published_fit", grain="class",
         applies_to=_G, notes="Params.h CM"),
    # MLCK activation (the cross-bridge model's first step)
    _sh("ph_sh_k1_b_M", "M", 5.2e-5, 2.6e-5, 1.04e-4, _SET + " (MLCK-Ca dissociation constant; TB value is 1.2e-5)"),
    _sh("ph_sh_k1_hill", "1", 4.0, 2.0, 4.0, _SET + " (Ca^4 in calcK1)"),
    # coupling and cells the paper does not have
    Spec("ph_gap_nS_per_contact", _P, "nS", 5.0, 0.5, 50.0, source=COOK, label="guessed", grain="class",
         applies_to="pm-pm and pm-marginal gaps", notes="EAT-5 innexin coupling; strong enough that neighbours fire "
         "together (eat-5 desynchronises corpus and TB, Starich et al. 1996); no measured junctional conductance"),
    Spec("ph_marginal_area_um2", _P, "um2", 500.0, 100.0, 2000.0, source="guessed", label="guessed",
         grain="class", applies_to="marginal cells", notes="passive compartment; leak density = the muscles'"),
    Spec("ph_m3_inhibitory", _P, "1", 1.0, 1.0, 1.0, source="Dent et al. 1997 EMBO J 16:5867; Raizen & Avery 1994",
         label="measured", grain="class", applies_to="M3 -> pharyngeal muscle",
         notes="M3 glutamate opens the AVR-15 GluCl (IPSPs in the muscle); overrides the brain's sign rule"),
    Spec("ph_ser7_on_muscle", _P, "1", 1.0, 0.0, 1.0, source="Hobson et al. 2006 Genetics 172:159 (ser-7 reporter "
         "in pharyngeal muscle)", label="inferred", grain="class", applies_to=_G,
         notes="the muscle takes the brain monoamine layer's serotonin>ser-7 occupancy times its ser-7 gain"),
    # pump detector
    Spec("ph_pump_on", _P, "1", 0.5, 0.2, 0.8, source="guessed", label="guessed", grain="global",
         applies_to="pump count", notes="pm4 mean activation must exceed this ..."),
    Spec("ph_pump_off", _P, "1", 0.2, 0.05, 0.4, source="guessed", label="guessed", grain="global",
         applies_to="pump count", notes="... and then fall below this for one pump"),
]

# brain_layers' pump-clock templates (the nested clock form reads the layer's own values when it has them)
_OLD = {"pump_rate_food_hz": 4.3, "pump_rate_nofood_hz": 0.3, "pump_duration_ms": 170.0, "pump_food_od0": 0.2}

MOD = {"g_cca1_na": "ph_sh_g_cca1_na", "p_cca1_ca": "ph_sh_p_cca1_ca", "g_egl19_na": "ph_sh_g_egl19_na",
       "p_egl19_ca": "ph_sh_p_egl19_ca", "g_exp2": "ph_sh_g_exp2", "g_l": "ph_sh_g_l", "v_l": "ph_sh_v_l",
       "v_na": "ph_sh_v_na", "v_k": "ph_sh_v_k",
       "cm_A2": "ph_sh_cca1_minf_a2", "cm_v0": "ph_sh_cca1_minf_v0", "cm_dv": "ph_sh_cca1_minf_dv",
       "cmt_A1": "ph_sh_cca1_mtau_a1", "cmt_A2": "ph_sh_cca1_mtau_a2", "cmt_v0": "ph_sh_cca1_mtau_v0",
       "cmt_dv": "ph_sh_cca1_mtau_dv", "cmt_deact": "ph_sh_cca1_mtau_deact",
       "ch_v0": "ph_sh_cca1_hinf_v0", "ch_dv": "ph_sh_cca1_hinf_dv", "cht_A1": "ph_sh_cca1_htau_a1",
       "cht_A2": "ph_sh_cca1_htau_a2", "cht_v0": "ph_sh_cca1_htau_v0", "cht_dv": "ph_sh_cca1_htau_dv",
       "em_v0": "ph_sh_egl19_minf_v0", "em_dv": "ph_sh_egl19_minf_dv", "emt_A1": "ph_sh_egl19_mtau_a1",
       "emt_A2": "ph_sh_egl19_mtau_a2", "emt_v0": "ph_sh_egl19_mtau_v0", "emt_dv": "ph_sh_egl19_mtau_dv",
       "ef_A1": "ph_sh_egl19_finf_a1", "ef_ca05": "ph_sh_egl19_finf_ca05", "ef_dca": "ph_sh_egl19_finf_dca",
       "eft_A1": "ph_sh_egl19_ftau_a1", "eft_A2": "ph_sh_egl19_ftau_a2", "eft_ca05": "ph_sh_egl19_ftau_ca05",
       "eft_dca": "ph_sh_egl19_ftau_dca",
       "xm_v0": "ph_sh_exp2_minf_v0", "xm_dv": "ph_sh_exp2_minf_dv", "xmt_A1": "ph_sh_exp2_mtau_a1",
       "xmt_A2": "ph_sh_exp2_mtau_a2", "xmt_v0": "ph_sh_exp2_mtau_v0", "xmt_dv": "ph_sh_exp2_mtau_dv",
       "xmt_pow": "ph_sh_exp2_mtau_pow", "xmd_A1": "ph_sh_exp2_mdeact_a1", "xmd_A2": "ph_sh_exp2_mdeact_a2",
       "xmd_v0": "ph_sh_exp2_mdeact_v0", "xmd_dv": "ph_sh_exp2_mdeact_dv",
       "xh_v0": "ph_sh_exp2_hinf_v0", "xh_dv": "ph_sh_exp2_hinf_dv", "xht_A1": "ph_sh_exp2_htau_a1",
       "xht_A2": "ph_sh_exp2_htau_a2", "xht_v0": "ph_sh_exp2_htau_v0", "xht_dv": "ph_sh_exp2_htau_dv",
       "xht_deinact": "ph_sh_exp2_hdeinact",
       "rgas": "ph_sh_gas_R", "temp_k": "ph_sh_temp_K", "ca_out": "ph_sh_ca_out_M", "ca_rest": "ph_sh_ca_rest_M",
       "tau_ca": "ph_sh_ca_tau_ms", "vrest": "ph_sh_v_l"}


def ca_geometry(q):
    """(shell area/volume in 1/cm, shell -> core exchange rate in 1/ms per shell volume, shell/core volume) for a
    cylinder of radius ph_radius_um with a shell of ph_sh_shell_frac of the radius: radial diffusion over half the
    radius, the lumped form of S&H's shell/core finite elements (derived)."""
    r = q["ph_radius_um"] * 1e-4                        # cm
    f = q["ph_sh_shell_frac"]
    vs = 1.0 - (1.0 - f) ** 2                           # shell volume / (pi r^2 L)
    av = 2.0 / (vs * r)
    k = q["ph_sh_ca_diff_cm2_s"] / (f * r * 0.5 * r) * 1e-3
    return av, k, vs / (1.0 - vs)


def configure(sec, q):
    for seg in sec:
        m = seg.sh_pharynx
        for name, pid in MOD.items():
            setattr(m, name, float(q[pid]))
        m.shell_av, m.k_sc, m.vs_vc = ca_geometry(q)


def activation(ca_M, q):
    """S&H's MLCK rate over its maximum: Ca^n / (K1_B^n + Ca^n) on the core Ca (M)."""
    n = q["ph_sh_k1_hill"]
    c = np.maximum(ca_M, 0.0) ** n
    return c / (q["ph_sh_k1_b_M"] ** n + c)


def defaults():
    q = {s.id: s.template for s in SPECS}
    q.update(_OLD)
    return q


def make_cell(h, q, name="pm"):
    """One pharyngeal-muscle compartment: a cylinder with L = diam and lateral area ph_area_um2."""
    sec = h.Section(name=name)
    sec.nseg = 1
    sec.L = sec.diam = float(np.sqrt(q["ph_area_um2"] / np.pi))
    sec.cm = q["ph_cm_uF_cm2"]
    sec.insert("sh_pharynx")
    configure(sec, q)
    return sec


def ap_protocol(h, q, amp_pA, dt=0.1, t_on=50.0, dur=40.0, t_end=600.0):
    """The row 13 unit check: an isolated compartment at rest, one current step. (t, V, core Ca) arrays."""
    sec = make_cell(h, q, "pm_check")
    st = h.IClamp(sec(0.5))
    st.delay, st.dur, st.amp = t_on, dur, amp_pA / 1000.0
    h.dt, h.secondorder = dt, 0
    tv, vv = h.Vector().record(h._ref_t), h.Vector().record(sec(0.5)._ref_v)
    cv = h.Vector().record(sec(0.5).sh_pharynx._ref_cac)
    h.finitialize(q["ph_sh_v_l"])
    while h.t < t_end - 1e-9:
        h.fadvance()
    out = np.array(tv), np.array(vv), np.array(cv)
    del st
    return out


def ap_features(t, v, t_on=50.0):
    """S&H Table 3 features: rest before the step, peak, duration above -40 mV, plateau mean (V > 0 from 20 ms
    after the peak), undershoot (minimum after the AP), maximal upstroke (mV/ms)."""
    dt = t[1] - t[0]
    rest = float(v[np.searchsorted(t, t_on) - 1])
    above = t[v > -40.0]
    k = int(np.argmax(v))
    pl = (t > t[k] + 20.0) & (v > 0.0)
    after = t > (above.max() if len(above) else t_on)
    return dict(rest=rest, peak=float(v.max()), t_peak=float(t[k]),
                duration=float(above.max() - above.min()) if len(above) else 0.0,
                plateau=float(v[pl].mean()) if pl.any() else float("nan"),
                undershoot=float(v[after].min()) if after.any() else float("nan"),
                upstroke=float(np.diff(v).max() / dt))


# --- the mechanism ------------------------------------------------------------------------------------------------
class Mech:
    """Builds the pharyngeal muscle and marginal cells, their Cook gaps and synapses; steps 5-HT, Ca -> activation,
    pumps and the EPG. The nested clock form runs brain_layers' oscillator instead and builds nothing."""

    def __init__(self, brain, params, toggles):
        self.brain = brain
        q = defaults()
        q.update(getattr(getattr(brain, "layers", None), "p", None) or {})
        q.update({k: float(v) for k, v in params.items() if np.isscalar(v)})
        self.q = q
        self.form = toggles.get("pharynx", "sherman2024")
        assert self.form in ("sherman2024", "clock", "off")
        self.n_pm = len(PHARYNX_MUSCLES)
        self.n_syn = self.n_gap = 0
        if self.form == "sherman2024":
            self._build()
        self.reset()

    def _build(self):
        from wormemu.mech import organs_nrn
        b, q = self.brain, self.q
        h = b.h
        organs_nrn.load_organ_mods(h)
        self.names = list(PHARYNX_MUSCLES) + MARGINAL
        self.sec = {}
        for n in PHARYNX_MUSCLES:
            self.sec[n] = make_cell(h, q, f"pharynx_{n}")
        for n in MARGINAL:
            s = h.Section(name=f"pharynx_{n}")
            s.nseg, s.cm = 1, q["ph_cm_uF_cm2"]
            s.L = s.diam = float(np.sqrt(q["ph_marginal_area_um2"] / np.pi))
            s.insert("pas")
            s.g_pas, s.e_pas = q["ph_sh_g_l"] * 1e-3, q["ph_sh_v_l"]      # mS/cm2 -> S/cm2
            self.sec[n] = s
        st, mine = b.st, set(self.names)
        nm = st.names
        g_pm = q["ph_gap_nS_per_contact"] / 1000.0
        sv = b.spec.v
        g_nn = float(np.median(sv("gap_strength_per_pair").to_numpy(float))) / 1000.0
        g_nmj = float(np.median(sv("nmj_strength_per_pair").to_numpy(float)))
        for i, j, n in st.gap:
            a, c = nm[i], nm[j]
            if a in mine and c in mine:
                b._gap(self.sec[a](0.5), self.sec[c](0.5), n * g_pm, "gap_pharynx")
            elif (a in mine) != (c in mine):
                other, me = (c, a) if a in mine else (a, c)
                if other in b.idx and not b.is_muscle[b.idx[other]]:
                    b._gap(b.soma[b.idx[other]](0.5), self.sec[me](0.5), n * g_nn, "gap_pharynx_neuron")
                else:
                    continue                             # epithelial e3 cells: not modelled
            self.n_gap += 1
        for i, j, n in st.chem:
            a, c = nm[i], nm[j]
            if c not in mine or a not in b.idx or a in NSM:
                continue
            inh = (a in M3 and q["ph_m3_inhibitory"] > 0.5) or b._inhibitory(a, c)
            w = g_nmj * n / (b._g_syn(inh) * 1000.0)
            b._syn(b.soma[b.idx[a]](0.5), self.sec[c](0.5), w, inh, "syn_pharynx")
            self.n_syn += 1
        self.stim = []
        for n in PHARYNX_MUSCLES:
            c = h.IClamp(self.sec[n](0.5))
            c.delay, c.dur, c.amp = 0.0, 1e12, 0.0
            self.stim.append(c)
        self._ser = self._serotonin_on_muscle()
        k = len(PHARYNX_MUSCLES)
        self._pv, self._pc = h.PtrVector(k), h.PtrVector(k)
        for x, n in enumerate(PHARYNX_MUSCLES):
            self._pv.pset(x, self.sec[n](0.5)._ref_v)
            self._pc.pset(x, self.sec[n](0.5).sh_pharynx._ref_cac)
        self._buf = h.Vector(k)

    def _serotonin_on_muscle(self):
        """(index of serotonin in the monoamine layer's concentrations, ec50 nM, gain pA) or None."""
        b = self.brain
        if self.q["ph_ser7_on_muscle"] <= 0 or getattr(b, "layers", None) is None:
            return None
        try:
            ligs = list(b.spec.v("ma_release_nM_per_s").index)
            ec50 = float(b.spec.v("ma_ec50_nM")["serotonin>ser-7"])
            gain = float(b.spec.v("ma_gain_pA")["ser-7"])
        except KeyError:
            return None
        return ligs.index("serotonin"), ec50, gain

    def reset(self):
        self.pumps_total, self.in_pump = 0, False
        self.phase, self.act = 0.0, np.zeros(self.n_pm)
        self.v_prev = self.T = None
        if self.form == "sherman2024":
            for s in self.sec.values():
                s(0.5).v = self.q["ph_sh_v_l"]
            for c in self.stim:
                c.amp = 0.0

    def _gather(self, pv):
        pv.gather(self._buf)
        return self._buf.as_numpy().copy()

    def clock(self, food_od, dt, q10=1.0):
        """brain_layers.Layers.pharynx, verbatim (the rate x temperature's pump factor, row 25): (activation, pumps
        completed this step)."""
        p = self.q
        f = food_od / (food_od + p["pump_food_od0"])
        rate = (p["pump_rate_nofood_hz"] + (p["pump_rate_food_hz"] - p["pump_rate_nofood_hz"]) * f) * q10
        self.phase += rate * dt / 1000.0
        done = int(self.phase)
        self.phase -= done
        self.pumps_total += done
        x = self.phase * 1000.0 / max(rate, 1e-9)
        a = np.sin(np.pi * x / p["pump_duration_ms"]) if x < p["pump_duration_ms"] else 0.0
        return float(max(a, 0.0)), done

    def step(self, ctx, dt_ms):
        if self.form == "off":
            return {"out": {"pumps": 0, "pharynx_activation": np.zeros(self.n_pm)}}
        if self.form == "clock":
            a, done = self.clock(ctx.obs.get("head", {}).get("food_OD", 0.0), dt_ms,
                                 ctx.outputs.get("q10", {}).get("pump", 1.0))
            return {"out": {"pumps": done, "pharynx_activation": np.full(self.n_pm, a),
                            "pharynx_pumps_total": self.pumps_total}}
        q = self.q
        T = ctx.outputs.get("temperature_C") if hasattr(ctx, "outputs") else None
        if T is not None and T != self.T:   # the GHK Ca fluxes at the worm's temperature (row 25; else 295.65 K)
            for n in PHARYNX_MUSCLES:
                self.sec[n](0.5).sh_pharynx.temp_k = T + 273.15
            self.T = T
        if self._ser is not None and getattr(self.brain.layers, "ma_c", None) is not None:
            k, ec50, gain = self._ser
            c = float(self.brain.layers.ma_c[k])
            amp = gain * c / (c + ec50) / 1000.0                 # pA -> nA
            if amp != self.stim[0].amp:
                for s in self.stim:
                    s.amp = amp
        v = self._gather(self._pv)
        ca = self._gather(self._pc)
        self.act = activation(ca, q)
        epg = 0.0 if self.v_prev is None else float(np.mean(v - self.v_prev) / dt_ms)
        self.v_prev = v
        a4 = float(self.act[METACORPUS].mean())
        done = 0
        if not self.in_pump and a4 > q["ph_pump_on"]:
            self.in_pump = True
        elif self.in_pump and a4 < q["ph_pump_off"]:
            self.in_pump, done = False, 1
            self.pumps_total += 1
        return {"out": {"pumps": done, "pharynx_activation": self.act.copy(), "pharynx_v_mV": v,
                        "pharynx_ca_core_uM": ca * 1e6, "pharynx_epg_mV_per_ms": epg,
                        "pharynx_pumps_total": self.pumps_total}}
