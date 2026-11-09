"""Published single-cell models that replace a cell's BAAIWorm membrane (MECHANISMS_AUDIT row 5; wbrain2, 9 Nov 2026).

AVL: Jiang J, Su Y, Zhang R, Li H, Tao L, Liu Q (2022) Nat Commun 13:2783 (PMC9120479, CC-BY), the AVL model of
the Supplementary Methods with Supplementary Table 1's WT column, ported as `nmodl/cells/jiang22_avl.mod` (the
equations there). BAAIWorm gives AVL and DVB the set fitted to AIYL (set 2, shared by 80 cells), which cannot fire
DVB's Ca action potential (docs/worm/night/2026-11-08_wbrain2.md, "DVB results and classification").

DVB: no published DVB model. `dvb_membrane jiang22_noexp2` borrows AVL's model with g_EXP2 0: Jiang's Discussion,
"no EXP-2 currents were detected in DVB as shown in Fig. S2b". The nearest published system, labelled inferred; not
a DVB fit.

Toggles (each default baaiworm = the cell exactly as before this module):
    avl_membrane   baaiworm | jiang22
    dvb_membrane   baaiworm | jiang22_noexp2
    jiang22_egl36_weights  printed (Eq. 50: fast 0.33) | code (base/AVLModel.m: 0.31); the m and s weights agree

Under a Jiang form, build_cell inserts the mod in every section of the cell with densities g_nS x cm / (1000 x C_pF)
S/cm2 (every g/C ratio kept, the AWA precedent in mech/senses_chem), and sets that cell's somatic BAAIWorm and
library channel densities and every section's pas leak to 0 before the brain gathers its conductance targets, so
no g_scale can bring them back. Synapses and gap junctions are untouched. Validity: an isopotential cell (the
neurites carry the same g/C); the injected current that gives Jiang's response scales with the cell's own C
(AVL about 17.4 pF, DVB about 7.2 pF in BAAIWorm's morphology, against 5 pF); the rates are Jiang's at their
recording temperature and are not scaled by row 25; the Ca current feeds BAAIWorm's Ca pool (cainternm) and the
GCaMP readout, while the model's own currents ignore Ca (as published).

AFD: Naudin L, Jimenez Laredo JL, Liu Q, Corson N (2022) PLoS ONE 17:e0268380 (PMC9106219, CC-BY), the I_Ca,p +
I_Kir + I_K,t + I_L model of S1 Table with S2 Table's multi-objective AFD column, ported as `nmodl/cells/
naudin22_afd.mod`. BAAIWorm's AFD fit has no inward rectifier (gbirk 0), so the cell falls to about -227 mV at
-15 pA where the recording (Naudin's own data, FIT2's training sweep) holds -91; Naudin's Kir supplies that branch.
The single-objective column is not ported (the authors reject it for AFD). Toggle `afd_membrane` baaiworm
(default) | naudin22, for AFDL and AFDR together (one class-level set). Same swap and g/C transfer as Jiang's; the
cGMP thermosensory cascade (mech/senses_chem) is added after this module and is untouched. Validity: as Jiang's;
Naudin's taus and C are converted from their decisecond units (x 100), and the fit absorbed whatever thermosensory
current was open at the recording's bath temperature, so with sens_thermo on that current may count twice.
"""
from __future__ import annotations

from wormemu.mech.senses_base import spec

MECHANISMS = [
    ("avl_membrane", "AVL membrane: Jiang et al. 2022's AVL model (UNC-2, EGL-19, CCA-1, SHL-1, EGL-36, EXP-2, NCA, "
     "leak) instead of BAAIWorm's set fitted to AIYL", "channel", "baaiworm"),
    ("dvb_membrane", "DVB membrane: Jiang et al. 2022's AVL model without EXP-2 (none detected in DVB), the nearest "
     "published system, instead of BAAIWorm's set fitted to AIYL", "channel", "baaiworm"),
    ("jiang22_egl36_weights", "Jiang 2022 EGL-36 fast-component weight: 0.33 as printed (Eq. 50) or 0.31 as in the "
     "authors' code", "channel", "printed"),
    ("afd_membrane", "AFD membrane: Naudin et al. 2022's AFD model (Ca, inward rectifier K, transient K, leak; "
     "multi-objective fit) instead of BAAIWorm's AFD fit, which has no inward rectifier", "channel", "baaiworm"),
]
FORMS = {"avl_membrane": ("baaiworm", "jiang22"), "dvb_membrane": ("baaiworm", "jiang22_noexp2"),
         "jiang22_egl36_weights": ("printed", "code"), "afd_membrane": ("baaiworm", "naudin22")}
CELL = {"AVL": ("avl_membrane", "jiang22"), "DVB": ("dvb_membrane", "jiang22_noexp2"),
        "AFDL": ("afd_membrane", "naudin22"), "AFDR": ("afd_membrane", "naudin22")}
MOD = "j22avl"
N22MOD = "n22afd"

SRC = ("Jiang, Su, Zhang, Li, Tao and Liu 2022 Nat Commun 13:2783 (PMC9120479), Supplementary Methods and "
       "Supplementary Table 1, WT; code github.com/taolab302/AVL-Modeling @ d8303f3 (base/AVLParameters.m)")
DVB_SRC = SRC + "; DVB: Discussion, 'no EXP-2 currents were detected in DVB as shown in Fig. S2b'"

# Table 1, WT: whole-cell conductances (nS) by cell
G_NS = {"g_UNC2": 1.0, "g_EGL19": 0.75, "g_CCA1": 0.25, "g_SHL1": 4.0, "g_EGL36": 1.35, "g_EXP2": 3.1,
        "g_NCA": 0.02, "g_L": 0.27}
# the other Table 1 numbers: name -> (value, unit, kind); kind v = a half-(in)activation or centre voltage, s = a
# slope, t = a time, e = a reversal, x = anything else (a rate, a factor, a weight)
KIN = {
    "v_Ca": (100.0, "mV", "e"), "v_K": (-84.0, "mV", "e"), "v_L": (-60.0, "mV", "e"), "v_Na": (30.0, "mV", "e"),
    "m_a": (0.1, "1/(ms mV)", "x"), "m_b": (25.0, "mV", "v"), "m_c": (10.0, "mV", "s"), "m_d": (0.4, "1/ms", "x"),
    "m_e": (-25.0, "mV", "v"), "m_f": (18.0, "mV", "s"), "h_a": (0.01, "1/ms", "x"), "h_b": (-50.0, "mV", "v"),
    "h_c": (10.0, "mV", "s"), "h_d": (0.03, "1/ms", "x"), "h_e": (-17.0, "mV", "v"), "h_f": (17.0, "mV", "s"),
    "s_1": (2.9, "ms", "t"), "s_2": (-4.8, "mV", "v"), "s_3": (6.0, "mV", "s"), "s_4": (1.9, "ms", "t"),
    "s_5": (-8.6, "mV", "v"), "s_6": (30.0, "mV", "s"), "s_7": (2.3, "ms", "t"), "s_8": (0.4, "1", "x"),
    "s_9": (44.6, "ms", "t"), "s_10": (-33.0, "mV", "v"), "s_11": (5.0, "mV", "s"), "s_12": (36.4, "ms", "t"),
    "s_13": (18.7, "mV", "v"), "s_14": (3.7, "mV", "s"), "s_15": (43.1, "ms", "t"),
    "q_1": (-4.4, "mV", "v"), "q_2": (7.5, "mV", "s"), "q_3": (1.43, "1", "x"), "q_4": (14.9, "mV", "v"),
    "q_5": (12.0, "mV", "s"), "q_6": (0.14, "1", "x"), "q_7": (5.96, "1", "x"), "q_8": (-20.5, "mV", "v"),
    "q_9": (8.1, "mV", "s"), "q_10": (0.6, "1", "x"),
    "c_1": (-43.32, "mV", "v"), "c_2": (7.6, "mV", "s"), "c_3": (40.0, "ms", "t"), "c_4": (-62.5, "mV", "v"),
    "c_5": (-12.6, "mV", "s"), "c_6": (0.7, "ms", "t"), "d_1": (-58.0, "mV", "v"), "d_2": (7.0, "mV", "s"),
    "d_3": (280.0, "ms", "t"), "d_4": (-60.7, "mV", "v"), "d_5": (8.5, "mV", "s"), "d_6": (19.8, "ms", "t"),
    "v_1": (-6.8, "mV", "v"), "v_2": (14.1, "mV", "s"), "a_m": (1.4, "ms", "t"), "b_m": (-17.5, "mV", "v"),
    "c_m": (12.9, "mV", "s"), "d_m": (-3.7, "mV", "v"), "e_m": (6.5, "mV", "s"), "f_m": (0.2, "ms", "t"),
    "v_3": (-33.1, "mV", "v"), "v_4": (8.3, "mV", "s"), "a_hf": (5.9, "ms", "t"), "b_hf": (-8.2, "mV", "v"),
    "c_hf": (2.9, "mV", "s"), "d_hf": (2.73, "ms", "t"), "a_hs": (84.2, "ms", "t"), "b_hs": (-7.7, "mV", "v"),
    "c_hs": (2.4, "mV", "s"), "d_hs": (11.9, "ms", "t"),
    "e_1": (63.0, "mV", "v"), "e_2": (28.5, "mV", "s"), "t_f": (13.0, "ms", "t"), "t_m": (63.0, "ms", "t"),
    "t_s": (355.0, "ms", "t"), "w36_m": (0.36, "1", "x"), "w36_s": (0.39, "1", "x"),
    "p_1": (0.0241, "1/ms", "x"), "p_2": (0.0408, "1/mV", "x"), "p_3": (0.0091, "1/ms", "x"),
    "p_4": (0.030, "1/mV", "x"), "p_5": (0.0372, "1/ms", "x"), "p_6": (0.31, "1/ms", "x"),
    "p_7": (0.0376, "1/ms", "x"), "p_8": (0.0472, "1/mV", "x"), "p_9": (0.0015, "1/ms", "x"),
    "p_10": (0.0703, "1/mV", "x"), "p_11": (0.2177, "1/ms", "x"), "p_12": (0.03, "1/mV", "x"),
    "p_13": (0.0313, "1/ms", "x"), "p_14": (0.1418, "1/mV", "x"), "p_15": (8.7204e-06, "1/ms", "x"),
    "p_16": (1.4011e-06, "1/mV", "x"),
}
W36F = {"printed": 0.33, "code": 0.31}

N22_SRC = ("Naudin, Jimenez Laredo, Liu and Corson 2022 PLoS ONE 17:e0268380 (PMC9106219), S1 Table (the I_Ca,p + "
           "I_Kir + I_K,t + I_L model) and S2 Table (multi-objective AFD column)")
# S2 Table, multi-objective, AFD: name -> (value here, unit here, kind, as printed); taus and C are printed in
# deciseconds (Methods: a 50 ds sweep sampled every 0.004 ds = 0.4 ms) and so C in pA ds/mV = 100 pF (derived)
N22_G = {"g_Ca": 6.7, "g_Kir": 2.32, "g_K": 28.01, "g_L": 0.004}
N22_KIN = {
    "e_Ca": (23.61, "mV", "e", "23.61"), "e_K": (-79.26, "mV", "e", "-79.26"), "e_L": (-89.43, "mV", "e", "-89.43"),
    "vh_mCa": (-3.65, "mV", "v", "-3.65"), "k_mCa": (7.25, "mV", "s", "7.25"),
    "vh_Kir": (-86.19, "mV", "v", "-86.19 (V1/2 hKir)"), "k_Kir": (-9.01, "mV", "s", "-9.01 (khKir)"),
    "vh_mK": (-2.54, "mV", "v", "-2.54"), "k_mK": (8.44, "mV", "s", "8.44"),
    "vh_hK": (-64.19, "mV", "v", "-64.19"), "k_hK": (-29.36, "mV", "s", "-29.36"),
    "tau_mCa": (562.0, "ms", "t", "5.62 ds"), "tau_mK": (0.01, "ms", "t", "0.0001 ds"),
    "tau_hK": (4.5, "ms", "t", "0.045 ds"),
}
N22_C_PF = 6.6                                           # printed 0.066 (pA ds/mV)


def _range(val, kind):
    if kind in ("v", "e"):
        lo, hi, note = val - 10, val + 10, "range +/- 10 mV (guessed)"
    elif kind == "s":
        lo, hi = sorted((val / 2, val * 2))
        note = "slope; range x/2 to x2 (guessed)"
        if abs(val) / 2 < 1.5:                                 # rules.yaml voltage_slope's 1.5 mV floor
            lo, hi = (1.5, hi) if val > 0 else (lo, -1.5)
            note = "slope; range x/2 to x2 (guessed), clipped at 1.5 mV (rules.yaml voltage_slope)"
    elif kind == "t":
        lo, hi, note = val / 3, val * 3, "time constant; range x/3 to x3 (guessed)"
        if val / 3 < 0.01:                                     # rules.yaml tau_gate's 0.01 ms floor
            lo, note = 0.01, "time constant; range x/3 to x3 (guessed), clipped at 0.01 ms (rules.yaml tau_gate)"
    else:
        lo, hi = sorted((val / 2, val * 2))
        note = "range x/2 to x2 (guessed)"
    return lo, hi, note


def _kin_spec(name, val, unit, kind):
    lo, hi, note = _range(val, kind)
    return spec(f"j22_{name}", "avl_membrane", unit, val, lo, hi, "published_fit", SRC,
                "AVL (and DVB under dvb_membrane jiang22_noexp2)",
                notes=f"jiang22_avl.mod GLOBAL {name}; {note}")


def _n22_specs():
    out = [spec("n22_C_pF", "afd_membrane", "pF", N22_C_PF, N22_C_PF / 2, N22_C_PF * 2, "published_fit", N22_SRC,
                "AFDL, AFDR", grain="class",
                notes="the model's capacitance, printed 0.066 in pA ds/mV (x 100 = pF, derived from the decisecond "
                      "time unit); converts its nS to S/cm2 (g/C kept); range x/2 to x2 (guessed)")]
    for g, x in N22_G.items():
        out.append(spec(f"n22_{g}", "afd_membrane", "nS", x, x / 2, x * 2, "published_fit", N22_SRC, "AFDL, AFDR",
                        grain="class", notes="whole-cell conductance of the n22_C_pF cell; range x/2 to x2 (guessed)"))
    for n, (v, u, k, printed) in N22_KIN.items():
        lo, hi, note = _range(v, k)
        out.append(spec(f"n22_{n}", "afd_membrane", u, v, lo, hi, "published_fit", N22_SRC, "AFDL, AFDR",
                        grain="class", notes=f"naudin22_afd.mod GLOBAL {n}, printed {printed}; {note}"))
    return out


def _g_specs():
    out = []
    for g, x in G_NS.items():
        out.append(spec(f"j22_AVL_{g}", "avl_membrane", "nS", x, x / 2, x * 2, "published_fit", SRC, "AVL",
                        grain="cell", notes="whole-cell conductance of the C_pF cell; range x/2 to x2 (guessed)"))
    for g, x in G_NS.items():
        if g == "g_EXP2":
            out.append(spec(f"j22_DVB_{g}", "dvb_membrane", "nS", 0.0, 0.0, x, "inferred", DVB_SRC, "DVB",
                            grain="cell", notes="0: no EXP-2 current detected in DVB (Jiang Fig. S2b); upper end "
                                                "AVL's value (guessed)"))
        else:
            out.append(spec(f"j22_DVB_{g}", "dvb_membrane", "nS", x, x / 2, x * 2, "inferred", DVB_SRC, "DVB",
                            grain="cell", notes="AVL's value (Jiang Table 1), borrowed: no published DVB model; "
                                                "range x/2 to x2 (guessed)"))
    return out


SPECS = ([spec("j22_C_pF", "avl_membrane", "pF", 5.0, 2.5, 10.0, "published_fit", SRC,
               "AVL (and DVB under dvb_membrane jiang22_noexp2)",
               notes="the model's capacitance (Table 1); converts its nS to S/cm2 (g/C kept); range x/2 to x2 "
                     "(guessed)")]
         + [_kin_spec(n, v, u, k) for n, (v, u, k) in KIN.items()]
         + [spec("j22_w36_f", "jiang22_egl36_weights", "1", W36F["printed"], 0.31, 0.33, "published_fit", SRC,
                 "AVL (and DVB)", notes="EGL-36 fast weight as printed (Eq. 50); the code's 0.31 is the other form; "
                                        "range the two"),
            spec("j22_w36_f_code", "jiang22_egl36_weights", "1", W36F["code"], 0.31, 0.33, "published_fit", SRC,
                 "AVL (and DVB)", notes="EGL-36 fast weight in base/AVLModel.m (jiang22_egl36_weights code)")]
         + _g_specs() + _n22_specs())


def form(toggles, tid):
    v = toggles.get(tid, MECHANISMS[[m[0] for m in MECHANISMS].index(tid)][3])
    if v not in FORMS[tid]:
        raise ValueError(f"{tid} form {v!r} not in {FORMS[tid]}")
    return v


def jiang_cells(toggles):
    """The cells whose membrane is Jiang's under these toggles."""
    return [c for c, (tid, on) in CELL.items() if on.startswith("jiang22") and form(toggles, tid) == on]


def naudin_cells(toggles):
    """The cells whose membrane is Naudin's under these toggles."""
    return [c for c, (tid, on) in CELL.items() if on == "naudin22" and form(toggles, tid) == on]


def build_cell(brain, name, obj, params, toggles):
    """Swap one cell's membrane for Jiang's or Naudin's (see the module docstring). Returns {g name: S/cm2 at cm 1}
    or {}."""
    jiang = name in jiang_cells(toggles)
    if not jiang and name not in naudin_cells(toggles):
        return {}
    from wormemu.brain import GB
    from wormemu.mech import CHANNEL_NAMES
    h = brain.h
    for ch in CHANNEL_NAMES:
        if h.ismembrane(ch, sec=obj.Soma):
            for seg in obj.Soma:
                setattr(getattr(seg, ch), GB.get(ch, f"gb{ch}"), 0.0)
    mod, C = (MOD, float(params["j22_C_pF"])) if jiang else (N22MOD, float(params["n22_C_pF"]))
    gs = {g: float(params[f"j22_{name}_{g}"]) for g in G_NS} if jiang else \
        {g: float(params[f"n22_{g}"]) for g in N22_G}
    put = {g: x / (1000.0 * C) for g, x in gs.items()}
    for sec in obj.all:
        sec.insert(mod)
        for seg in sec:
            if hasattr(seg, "pas"):
                seg.pas.g = 0.0                                  # the model's own leak replaces BAAIWorm's
            for g, x in gs.items():
                setattr(getattr(seg, mod), g, x * seg.cm / (1000.0 * C))   # nS of a C-pF cell -> S/cm2
    at = "jiang_cells" if jiang else "naudin_cells"
    setattr(brain, at, getattr(brain, at, {}))
    getattr(brain, at)[name] = put
    return put


class Mech:
    """Writes the kinetic Specs (and Jiang's EGL-36 weights) into the mod GLOBALs; nothing per step."""

    def __init__(self, brain, params, toggles):
        j, n = bool(jiang_cells(toggles)), bool(naudin_cells(toggles))
        self.on = j or n
        h = brain.h
        if j:
            for k in KIN:
                setattr(h, f"{k}_{MOD}", float(params[f"j22_{k}"]))
            w = form(toggles, "jiang22_egl36_weights")
            setattr(h, f"w36_f_{MOD}", float(params["j22_w36_f" if w == "printed" else "j22_w36_f_code"]))
        if n:
            for k in N22_KIN:
                setattr(h, f"{k}_{N22MOD}", float(params[f"n22_{k}"]))

    def reset(self):
        pass

    def step(self, ctx, dt_ms):
        return {}
