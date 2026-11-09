"""Chemical, thermal, gas, light and food senses as transduction cascades (audit row 17, wbody, night of 6 Nov 2026).

Takes over brain_layers' sens_salt, sens_odor_attract, sens_repellent, sens_thermo, sens_o2, sens_co2, sens_light and
sens_food toggles (forms: "cascade" default, "lumped" = the old one-transform layer exactly, "off"), and adds
awa_membrane ("liu2018" default, "baaiworm" = BAAIWorm's AWA channels as before) and awa_kir (Liu's inward rectifier:
"smooth_min" default, "as_printed" = the equation as printed, inward at every voltage; DEBUG_TRIAGE line 7).

What each cell runs (the world reaches the brain only here, through BodyToBrain's head/tail channels):

  cGMP cascade, Usuyama et al. 2012 (senses_cgmp, the published AWC network, one copy per cell):
    AWC   isoamyl alcohol, benzaldehyde, butanone (AWCL only, as brain_layers) as the published Odorant input:
          published (AWC is the model's cell). Odour ON lowers cGMP and Ca, removal gives the rebound.
    AWB   2-nonanone, octanol as Odorant (inferred: AWB is an odour-OFF cell, Ha et al. 2010 Neuron 68:1173; the
          lumped layer's +1 sign was the opposite; the literature wins).
    ASER  NaCl as Odorant (inferred: ASER is a salt-OFF cell, Suzuki et al. 2008 Nature 454:114, through GCY-22
          and TAX-2/TAX-4; borrowing the published OFF branch is the inferred part).
    ASEL  NaCl up via the cyclase rate (GCY-14 class receptor guanylyl cyclase; Ortiz et al. 2009): ON cell.
    AFD   temperature via the cyclase rate (GCY-8/18/23), sigmoid around T* (Ramot et al. 2008, Takeishi 2016):
          ON above T*. T* shifts by ctx.outputs['afd_Tstar_shift_C'] when a plasticity module writes it. Each AFD's
          catalytic rate is also multiplied by ctx.outputs['afd_gc_scale'][cell] (mech/glia: amphid sheath KCC-3
          sets the Cl- at AFD's ending, which inhibits GCY-8; Singhvi et al. 2016), 1 where absent.
    URX, AQR, PQR  O2 up via the cyclase rate (soluble GCY-35/36; Zimmer et al. 2009, Busch et al. 2012).
    BAG   O2 down (GCY-31/33) and CO2 up (receptor GC GCY-9; Hallem et al. 2011) via the cyclase rate.
    ASJ, ASK, ASH, AWB, ASI  light via LITE-1 -> G protein -> DAF-11/ODR-1 cyclases (Ward et al. 2008, Liu et al.
          2010) via the cyclase rate.
    The cyclase route (stimulus multiplies the catalytic rate constants of reactions 4.2.x.2 by 1 + A a, a in
    [0, 1]) is the inferred template for receptor guanylyl cyclase cells; the cascade's own Ca feedback adapts it.
    Output: CNG (TAX-2/TAX-4) conductance g = g_CNG Po on the soma, reversal E_CNG.

  Receptor -> G protein -> TRPV channel template (inferred structure; OSM-9/OCR-2 cells, Tobin et al. 2002,
  Hilliard et al. 2005 for ASH adaptation): ASH (octanol, glycerol, copper, quinine), ADL (octanol, copper),
  PHA/PHB (SDS, tail), AWA front end (diacetyl through ODR-10 -> OSM-9; Sengupta 1996, Larsch 2015), and food
  (NSM through DEL-3/DEL-7, Rhoades et al. 2019; ADF, ASI, ASJ). Per cell: occupancy r = min(1, sum c/(c + K)),
  G' = (r - G)/tau_G, D' = (G - D)/tau_D, Po = G (1 - phi D), g = g_TRPV Po, reversal E_TRPV.

  AWA membrane, Liu et al. 2018 (nmodl/senses/awa_liu2018.mod, every Table S4 WT number as a Spec): inserted in
  every AWA section with the whole-cell conductances turned into densities that keep each g/C ratio; BAAIWorm's
  AWA somatic channels and leak are scaled to 0 and the neurites' passive leak removed (Liu's leak replaces them).

Integration: cGMP cascade semi-implicit with h 0.25 ms (the step the AWC unit check passed with LSODA), TRPV
template exact exponential per brain step; conductances set before fadvance (NEURON integrates them implicitly).
At reset the cascades are relaxed for 30 s to the first step's stimuli.
"""
from __future__ import annotations

import numpy as np

from wormemu.brain_layers import AMPHID
from wormemu.mech import senses_cgmp
from wormemu.mech.senses_base import CASCADE, LUMPED, Conductance, form, hill, lumped_current, spec

TOGGLES = ("sens_salt", "sens_odor_attract", "sens_repellent", "sens_thermo", "sens_o2", "sens_co2", "sens_light",
           "sens_food")
MECHANISMS = [
    ("sens_salt", "Salt: ASER salt-OFF and ASEL salt-ON cGMP cascades (Usuyama 2012 network)", "sensory", CASCADE),
    ("sens_odor_attract", "Attractive odours: AWC cGMP cascade (Usuyama 2012), AWA ODR-10 -> OSM-9 front end",
     "sensory", CASCADE),
    ("sens_repellent", "Repellents: ASH/ADL/PHA/PHB TRPV template, AWB odour-OFF cGMP cascade", "sensory", CASCADE),
    ("sens_thermo", "Temperature: AFD GCY-8/18/23 cGMP cascade around T*", "sensory", CASCADE),
    ("sens_o2", "Oxygen: URX/AQR/PQR GCY-35/36 (O2 up), BAG GCY-31/33 (O2 down) cGMP cascades", "sensory", CASCADE),
    ("sens_co2", "Carbon dioxide: BAG GCY-9 cGMP cascade", "sensory", CASCADE),
    ("sens_light", "Light: LITE-1 -> DAF-11/ODR-1 cGMP cascade in ASJ, ASK, ASH, AWB, ASI", "sensory", CASCADE),
    ("sens_food", "Food: NSM DEL-3/7, ADF, ASI, ASJ receptor-channel template", "sensory", CASCADE),
    ("awa_membrane", "AWA membrane: calcium action potentials (Liu et al. 2018)", "sensory", "liu2018"),
    ("awa_kir", "AWA inward rectifier: gKir times the smooth minimum of (v - vK) and I0, as in the authors' code "
     "(Liu et al. 2018; as printed it is inward at every voltage)", "sensory", "smooth_min"),
]
AWA_KIR = ("smooth_min", "as_printed")

LIU_SRC = ("Liu Q, Kidd PB, Dobosiewicz M, Bargmann CI 2018 Cell 175:57, Table S4 WT (bioRxiv 10.1101/359935, CC-BY; "
           "docs/worm/research/liu2018_tableS4.jpg)")
# Table S4, WT: (spec suffix, mod parameter, value, unit, kind) ; kind g = whole-cell nS (converted to density)
LIU = [("C_pF", None, 1.5, "pF", "c"), ("gCa", "gCa", 0.1, "nS", "g"), ("vCa", "vCa", 120.0, "mV", "v"),
       ("f", "f", 0.4, "1", "x"), ("tc1", "tc1", 1.0, "ms", "t"), ("tc2", "tc2", 160.0, "ms", "t"),
       ("vc1", "vc1", -21.6, "mV", "v"), ("dvc1", "dvc1", 9.17, "mV", "s"), ("vc2", "vc2", 16.2, "mV", "v"),
       ("dvc2", "dvc2", -16.1, "mV", "s"), ("vc3", "vc3", 23.0, "mV", "v"), ("dvc3", "dvc3", 24.0, "mV", "s"),
       ("c0", "c0", 0.55, "1", "x"), ("vK", "vK", -84.0, "mV", "v"), ("gK1", "gK1", 1.5, "nS", "g"),
       ("vK1", "vK1", 2.0, "mV", "v"), ("dvK1", "dvK1", 10.0, "mV", "s"), ("tK1", "tK1", 30.0, "ms", "t"),
       ("gK2", "gK2", 1.0, "nS", "g"), ("vK2", "vK2", 13.0, "mV", "v"), ("dvK2", "dvK2", 20.0, "mV", "s"),
       ("tK2", "tK2", 1000.0, "ms", "t"), ("gK3", "gK3", 0.1, "nS", "g"), ("vK3", "vK3", -25.0, "mV", "v"),
       ("dvK3", "dvK3", 5.0, "mV", "s"), ("tK3", "tK3", 1000.0, "ms", "t"), ("gKr", "gKr", 0.39, "nS", "g"),
       ("vKr1", "vKr1", -42.0, "mV", "v"), ("dvKr1", "dvKr1", 5.0, "mV", "s"), ("vKr2", "vKr2", -42.0, "mV", "v"),
       ("dvKr2", "dvKr2", 5.0, "mV", "s"), ("tKr", "tKr", 1800.0, "ms", "t"), ("gKa", "gKs", 0.91, "nS", "g"),
       ("vKa1", "vKs1", -52.0, "mV", "v"), ("dvKa1", "dvKs1", 20.0, "mV", "s"), ("vKa2", "vKs2", -32.0, "mV", "v"),
       ("dvKa2", "dvKs2", 4.0, "mV", "s"), ("tKa1", "tKs1", 27000.0, "ms", "t"),
       ("tKa2", "tKs2", 3000.0, "ms", "t"), ("gKir", "gKir", 0.8, "nS", "g"), ("I0", "I0", 5.0, "mV", "x"),
       ("beta", "beta", 5.0, "mV", "x"), ("gL", "gL", 0.25, "nS", "g"), ("vL", "vL", -65.0, "mV", "v")]
_SHK1 = {"gCa": 0.13, "gK1": 0.0, "gK2": 2.0, "gKr": 0.77, "gKa": 1.98}   # Table S4's shk-1 fit: the ranges' ends


def _liu_spec(sfx, val, unit, kind):
    if kind == "g":
        alt = _SHK1.get(sfx, val)
        lo, hi = min(val, alt) / 2, max(val, alt) * 2
        note = "whole-cell conductance; range: x/2 below and x2 above the WT and shk-1 fits (guessed)"
    elif kind == "v":
        lo, hi, note = val - 10, val + 10, "range +/- 10 mV (guessed)"
    elif kind == "s":
        lo, hi = sorted((val / 2, val * 2))
        note = "slope; range x/2 to x2 (guessed)"
    elif kind == "t":
        lo, hi, note = val / 3, val * 3, "time constant; range x/3 to x3 (guessed)"
    elif kind == "c":
        return spec("awa_liu_C_pF", "awa_membrane", unit, val, 0.5, 3.0, "measured", LIU_SRC, "AWAL, AWAR",
                    notes="AWA whole-cell capacitance in the fit (Liu 2018 recordings); range guessed")
    else:
        lo, hi, note = val / 2, val * 2, "range x/2 to x2 (guessed)"
        if sfx == "I0":
            note += ("; Table S4 lists I0 as a 5.0 pA saturated current, but the authors' code (github.com/wormwhisperer/"
                     "CElegansAWAActionPotentialAnalysis, gKI) adds it to v in mV: the Kir saturates at gKir I0 = 4 pA")
    return spec(f"awa_liu_{sfx}", "awa_membrane", unit, val, lo, hi, "published_fit", LIU_SRC, "AWAL, AWAR",
                notes=note)


G = "guessed"
INF = "inferred"
CELLS_LIGHT = ("ASJL", "ASJR", "ASKL", "ASKR", "ASHL", "ASHR", "AWBL", "AWBR", "ASIL", "ASIR")
# Odorant-input (OFF) channels: toggle -> [(channel, side, cells, c_ref spec id)]
OFF_IN = {
    "sens_odor_attract": [("isoamyl_alcohol_uM", "head", ("AWCL", "AWCR"), "sens_awc_iaa_ref_uM"),
                          ("benzaldehyde_uM", "head", ("AWCL", "AWCR"), "sens_awc_bzd_ref_uM"),
                          ("butanone_uM", "head", ("AWCL",), "sens_awc_but_ref_uM")],
    "sens_repellent": [("nonanone_uM", "head", ("AWBL", "AWBR"), "sens_awb_non_ref_uM"),
                       ("octanol_uM", "head", ("AWBL", "AWBR"), "sens_awb_oct_ref_uM")],
    "sens_salt": [("nacl_mM", "head", ("ASER",), "sens_aser_nacl_ref_mM")],
}
# TRPV-template channels: toggle -> [(channel, side, cells, K spec id)]
TRPV_IN = {
    "sens_odor_attract": [("diacetyl_uM", "head", ("AWAL", "AWAR"), "sens_awa_dia_K_uM")],
    "sens_repellent": [("octanol_uM", "head", ("ASHL", "ASHR", "ADLL", "ADLR"), "sens_ash_oct_K_uM"),
                       ("glycerol_mM", "head", ("ASHL", "ASHR"), "sens_ash_gly_K_mM"),
                       ("copper_mM", "head", ("ASHL", "ASHR", "ADLL", "ADLR"), "sens_ash_cu_K_mM"),
                       ("quinine_mM", "head", ("ASHL", "ASHR"), "sens_ash_qui_K_mM"),
                       ("sds_mM", "tail", ("PHAL", "PHAR", "PHBL", "PHBR"), "sens_ph_sds_K_mM")],
    "sens_food": [("food_OD", "head", ("ADFL", "ADFR", "ASIL", "ASIR", "ASJL", "ASJR", "NSML", "NSMR"),
                   "sens_food_K_OD")],
}

SPECS = [_liu_spec(s, v, u, k) for s, _, v, u, k in LIU] + senses_cgmp.network_specs(
    "AWC (published); inferred template for ASE, AWB, AFD, URX, AQR, PQR, BAG and the light cells",
    "sens_odor_attract") + [
    spec("sens_cng_g_nS", "sens_odor_attract", "nS", 1.0, 0.1, 10.0, G, "no whole-cell CNG conductance measured in these cells",
         "cGMP cascade cells", grain="global",
         notes="g = g_CNG Po; Po at rest 0.065 (published model). Would be pinned by whole-cell TAX-4 current "
               "recordings in AWC/ASE (none found free)"),
    spec("sens_cng_E_mV", "sens_odor_attract", "mV", 0.0, -10.0, 20.0, INF,
         "TAX-2/TAX-4 are nonselective cation CNG channels (Komatsu et al. 1996 Neuron 17:707)", "cGMP cascade cells"),
    spec("sens_awc_iaa_ref_uM", "sens_odor_attract", "uM", 920.0, 9.2, 9200.0, G,
         "1e-4 dilution of isoamyl alcohol (9.2 M neat), a common imaging dose", "AWCL, AWCR",
         notes="isoamyl alcohol at which the input equals the published Dose (Odorant 1000); linear in c"),
    spec("sens_awc_bzd_ref_uM", "sens_odor_attract", "uM", 980.0, 9.8, 9800.0, G,
         "1e-4 dilution of benzaldehyde (9.8 M neat)", "AWCL, AWCR"),
    spec("sens_awc_but_ref_uM", "sens_odor_attract", "uM", 1100.0, 11.0, 11000.0, G,
         "1e-4 dilution of 2-butanone (11 M neat)", "AWCL"),
    spec("sens_awb_non_ref_uM", "sens_repellent", "uM", 580.0, 5.8, 5800.0, G,
         "1e-4 dilution of 2-nonanone (5.8 M neat); Ha et al. 2010 used 1e-2 to 1e-4 dilutions", "AWBL, AWBR"),
    spec("sens_awb_oct_ref_uM", "sens_repellent", "uM", 6300.0, 63.0, 63000.0, G,
         "1e-3 dilution of 1-octanol (6.3 M neat)", "AWBL, AWBR"),
    spec("sens_aser_nacl_ref_mM", "sens_salt", "mM", 50.0, 5.0, 200.0, G,
         "the 50 mM NaCl step of Suzuki et al. 2008", "ASER"),
    spec("sens_gc_gain", "sens_thermo", "1", 3.0, 0.5, 20.0, G, "no cyclase activity ratio measured in vivo",
         "ASEL, AFD, URX, AQR, PQR, BAG, light cells",
         notes="A in kcat x (1 + A a): the fold rise of the cyclases' catalytic rate at full stimulus"),
    spec("sens_asel_nacl_K_mM", "sens_salt", "mM", 25.0, 1.0, 200.0, G,
         "ASEL responds to NaCl upsteps over 0-100 mM (Suzuki et al. 2008)", "ASEL"),
    spec("sens_afd_Tstar_C", "sens_thermo", "C", 20.0, 15.0, 25.0, "measured",
         "AFD T* tracks cultivation temperature (Kimura et al. 2004; Clark et al. 2006)", "AFDL, AFDR",
         lit="J5", notes="template = cultivation at 20 C"),
    spec("sens_afd_dT_C", "sens_thermo", "C", 0.5, 0.1, 2.0, G,
         "AFD responds to warming of 0.05 C and above T* (Clark et al. 2006); width of the cyclase sigmoid",
         "AFDL, AFDR"),
    spec("sens_o2_up_K_pct", "sens_o2", "% O2", 16.0, 12.0, 19.0, INF,
         "URX/AQR/PQR respond above ~15-17% O2 (Zimmer et al. 2009; Busch et al. 2012)", "URX, AQR, PQR", lit="J9"),
    spec("sens_o2_up_n", "sens_o2", "1", 8.0, 2.0, 12.0, G, "switch-like URX response (Busch et al. 2012)",
         "URX, AQR, PQR"),
    spec("sens_o2_down_K_pct", "sens_o2", "% O2", 10.0, 5.0, 15.0, INF,
         "BAG responds below ~10% O2 (Zimmer et al. 2009)", "BAGL, BAGR", lit="J9"),
    spec("sens_o2_down_n", "sens_o2", "1", 4.0, 1.0, 10.0, G, "steepness of BAG's O2-down response", "BAGL, BAGR"),
    spec("sens_co2_K_pct", "sens_co2", "% CO2", 2.5, 0.5, 10.0, INF,
         "BAG responds to 0.5-10% CO2 (Hallem et al. 2011; Bretscher et al. 2011)", "BAGL, BAGR", lit="J10"),
    spec("sens_co2_n", "sens_co2", "1", 1.5, 1.0, 4.0, G, "steepness of BAG's CO2 response", "BAGL, BAGR"),
    spec("sens_light_K_mWmm2", "sens_light", "mW/mm2", 0.5, 0.05, 5.0, INF,
         "UV/blue light responses at 0.1-5 mW/mm2 (Ward et al. 2008; Edwards et al. 2008)", "light cells"),
    spec("sens_trpv_g_nS", "sens_repellent", "nS", 1.0, 0.1, 10.0, G, "no whole-cell OSM-9/OCR-2 conductance measured",
         "ASH, ADL, PHA, PHB, AWA front end, food cells"),
    spec("sens_trpv_E_mV", "sens_repellent", "mV", 0.0, -10.0, 20.0, INF, "TRPV and DEG/ENaC (DEL-3/7) cation channels",
         "ASH, ADL, PHA, PHB, AWA front end, food cells"),
    spec("sens_trpv_tauG_ms", "sens_repellent", "ms", 100.0, 20.0, 1000.0, G,
         "ASH Ca rises within ~1 s of stimulus (Hilliard et al. 2005); receptor/G-protein lag",
         "ASH, ADL, PHA, PHB, AWA front end, food cells"),
    spec("sens_trpv_tauD_s", "sens_repellent", "s", 5.0, 1.0, 60.0, INF,
         "ASH and AWA responses decline over seconds during a sustained stimulus (Hilliard 2005; Larsch 2015)",
         "ASH, ADL, PHA, PHB, AWA front end, food cells"),
    spec("sens_trpv_phi", "sens_repellent", "1", 0.7, 0.0, 1.0, G, "fraction of the response that adapts",
         "ASH, ADL, PHA, PHB, AWA front end, food cells"),
    spec("sens_awa_dia_K_uM", "sens_odor_attract", "uM", 1.0, 0.01, 100.0, INF,
         "AWA responds to diacetyl from ~1e-9 to 1e-5 dilutions, half-max near 1e-7 (~1 uM; Larsch et al. 2015)",
         "AWAL, AWAR"),
    spec("sens_ash_oct_K_uM", "sens_repellent", "uM", 6300.0, 63.0, 63000.0, G,
         "30% octanol on a hair drives ASH (Hilliard 2005); half-max guessed at a 1e-3 dilution",
         "ASH, ADL"),
    spec("sens_ash_gly_K_mM", "sens_repellent", "mM", 500.0, 100.0, 2000.0, INF,
         "ASH avoidance of ~1-2 M glycerol (Hilliard 2005)", "ASHL, ASHR"),
    spec("sens_ash_cu_K_mM", "sens_repellent", "mM", 1.0, 0.1, 10.0, INF,
         "ASH Ca responses to 1-10 mM CuSO4 (Hilliard 2005)", "ASH, ADL"),
    spec("sens_ash_qui_K_mM", "sens_repellent", "mM", 5.0, 0.5, 50.0, INF,
         "ASH responds to 10 mM quinine (Hilliard 2005)", "ASHL, ASHR"),
    spec("sens_ph_sds_K_mM", "sens_repellent", "mM", 0.5, 0.05, 5.0, INF,
         "PHA/PHB respond to 0.1% SDS (~3.5 mM; Hilliard et al. 2002)", "PHA, PHB"),
    spec("sens_food_K_OD", "sens_food", "OD600", 0.5, 0.01, 5.0, G, "half-max bacterial density at the mouth",
         "NSM, ADF, ASI, ASJ"),
]


def _cell_ok(brain, c):
    return c in brain.idx


class Mech:
    def __init__(self, brain, params, toggles):
        self.b, self.p = brain, params
        self.forms = {t: form(toggles, t) for t in TOGGLES}
        self.awa = toggles.get("awa_membrane", "liu2018")
        self.awa_kir = toggles.get("awa_kir", "smooth_min")
        if self.awa_kir not in AWA_KIR:
            raise ValueError(f"awa_kir: {self.awa_kir!r} not in {AWA_KIR}")
        p = params
        names = brain.cell_names
        self.n = len(names)
        self.glia = "glia" in brain.layers.on
        # cGMP cascade cells and their inputs
        cg = []

        def addc(*cs):
            for c in cs:
                if _cell_ok(brain, c) and c not in cg:
                    cg.append(c)
        f = self.forms
        if f["sens_odor_attract"] == CASCADE:
            addc("AWCL", "AWCR")
        if f["sens_repellent"] == CASCADE:
            addc("AWBL", "AWBR")
        if f["sens_salt"] == CASCADE:
            addc("ASEL", "ASER")
        if f["sens_thermo"] == CASCADE:
            addc("AFDL", "AFDR")
        if f["sens_o2"] == CASCADE:
            addc("URXL", "URXR", "AQR", "PQR", "BAGL", "BAGR")
        if f["sens_co2"] == CASCADE:
            addc("BAGL", "BAGR")
        if f["sens_light"] == CASCADE:
            addc(*CELLS_LIGHT)
        self.cg = cg
        self.cgi = {c: k for k, c in enumerate(cg)}
        self.cas = senses_cgmp.Cascade(p, len(cg)) if cg else None
        self.g_cng = Conductance(brain, cg, p["sens_cng_E_mV"])
        # TRPV template cells
        tc = []
        for t, chans in TRPV_IN.items():
            if f[t] == CASCADE:
                for _, _, cells, _ in chans:
                    tc += [c for c in cells if _cell_ok(brain, c) and c not in tc]
        self.tc = tc
        self.tci = {c: k for k, c in enumerate(tc)}
        self.g_trpv = Conductance(brain, tc, p["sens_trpv_E_mV"])
        self.amph_cg = np.array([c in AMPHID for c in cg], bool)
        self.amph_tc = np.array([c in AMPHID for c in tc], bool)
        self.lumped = [t for t in TOGGLES if f[t] == LUMPED]
        self._awa_setup()
        self.reset()

    # --- AWA membrane ----------------------------------------------------------------------------------------
    def _awa_setup(self):
        b, p = self.b, self.p
        self.awa_secs = []
        self.g_awa = {}
        if self.awa == "off" or self.awa == "baaiworm":
            return
        C = p["awa_liu_C_pF"]
        for c in ("AWAL", "AWAR"):
            if c not in b.idx:
                continue
            i = b.idx[c]
            for s in b.cells[i].all:
                s.insert("awa_liu")
                s.kir_form_awa_liu = AWA_KIR.index(self.awa_kir)
                for sfx, mod, _, _, kind in LIU:
                    if mod is None:
                        continue
                    x = p[f"awa_liu_{sfx}"]
                    if kind == "g":
                        x = x * s.cm / (1000.0 * C)          # nS of a C-pF cell -> S/cm2 at this section's cm
                    setattr(s, f"{mod}_awa_liu", x)
                if s != b.soma[i] and hasattr(s, "g_pas"):
                    s.g_pas = 0.0                            # Liu's leak replaces the passive neurite leak
                self.awa_secs.append(s)
        self.awa_idx = np.array([b.idx[c] for c in ("AWAL", "AWAR") if c in b.idx], int)

    # --- state -----------------------------------------------------------------------------------------------
    def reset(self):
        if self.cas is not None:
            self.cas.reset()
        self.G = np.zeros(len(self.tc))
        self.D = np.zeros(len(self.tc))
        self.g_cng.reset()
        self.g_trpv.reset()
        self.fresh = True

    def _inputs(self, ctx):
        """(odor, kcat) per cGMP cell and occupancy r per TRPV cell from this step's stimuli."""
        p, f, obs = self.p, self.forms, ctx.obs
        odor = np.full(len(self.cg), p["usu_odorant_rest"])
        act = np.zeros(len(self.cg))
        on = p["usu_odorant_on"]
        for t, chans in OFF_IN.items():
            if f[t] != CASCADE:
                continue
            for ch, side, cells, ref in chans:
                c = float(obs[side].get(ch, 0.0))
                for cell in cells:
                    if cell in self.cgi:
                        odor[self.cgi[cell]] += on * max(c, 0.0) / p[ref]

        def a(cell, x):
            if cell in self.cgi:
                act[self.cgi[cell]] += x
        hd = obs["head"]
        if f["sens_salt"] == CASCADE:
            a("ASEL", float(hill(hd.get("nacl_mM", 0.0), p["sens_asel_nacl_K_mM"], 1.0)))
        self.Tstar = p["sens_afd_Tstar_C"] + float(ctx.outputs.get("afd_Tstar_shift_C", 0.0))
        if f["sens_thermo"] == CASCADE:
            T = float(hd.get("temperature_C", 20.0))
            x = 1.0 / (1.0 + np.exp(-(T - self.Tstar) / p["sens_afd_dT_C"]))
            a("AFDL", x); a("AFDR", x)
        if f["sens_o2"] == CASCADE:
            o2 = float(hd.get("o2_pct", 21.0))
            up = float(hill(o2, p["sens_o2_up_K_pct"], p["sens_o2_up_n"]))
            down = 1.0 - float(hill(o2, p["sens_o2_down_K_pct"], p["sens_o2_down_n"]))
            for c in ("URXL", "URXR", "AQR", "PQR"):
                a(c, up)
            a("BAGL", down); a("BAGR", down)
        if f["sens_co2"] == CASCADE:
            x = float(hill(hd.get("co2_pct", 0.04), p["sens_co2_K_pct"], p["sens_co2_n"]))
            a("BAGL", x); a("BAGR", x)
        if f["sens_light"] == CASCADE:
            x = float(hill(hd.get("light_mW_mm2", 0.0), p["sens_light_K_mWmm2"], 1.0))
            for c in CELLS_LIGHT:
                a(c, x)
        kcat = 1.0 + p["sens_gc_gain"] * np.clip(act, 0.0, 1.0)
        for cell, sc in (ctx.outputs.get("afd_gc_scale") or {}).items():     # glia KCC-3 -> Cl- -> GCY-8
            if cell in self.cgi:
                kcat[self.cgi[cell]] *= float(sc)
        r = np.zeros(len(self.tc))
        for t, chans in TRPV_IN.items():
            if f[t] != CASCADE:
                continue
            for ch, side, cells, K in chans:
                c = max(float(obs[side].get(ch, 0.0)), 0.0)
                for cell in cells:
                    if cell in self.tci:
                        r[self.tci[cell]] += c / (c + p[K])
        return odor, kcat, np.minimum(r, 1.0)

    def step(self, ctx, dt_ms):
        p = self.p
        odor, kcat, r = self._inputs(ctx)
        if self.fresh:                                   # relax to the first step's stimuli
            if self.cas is not None:
                self.cas.advance(30.0, odor, kcat, h_s=1e-3)
            self.G[:] = r
            self.D[:] = r
            self.fresh = False
        out = {}
        I = np.zeros(self.n)
        gs = np.zeros(self.n)
        q = ctx.outputs.get("q10", {})                  # row 25 (mech/temperature.py), 1 without it
        if self.cas is not None:
            po = self.cas.advance(dt_ms * 1e-3 * q.get("enzyme", 1.0), odor, kcat)
            g = p["sens_cng_g_nS"] * po
            if self.glia:
                g = np.where(self.amph_cg, g * self.b.layers.p["glia_gain"], g)
            self.g_cng.set(g)
            I += self.g_cng.current_pA(ctx.v, self.n)
            np.add.at(gs, self.g_cng.idx, self.g_cng.g_nS)
            ca = self.cas.x[self.cas.i["Ca"]]
            out["sens_cgmp_uM"] = {c: float(self.cas.x[self.cas.i["cGMP"], k]) for c, k in self.cgi.items()}
            out["sens_cng_po"] = {c: float(po[k]) for c, k in self.cgi.items()}
            afd = [self.cgi[c] for c in ("AFDL", "AFDR") if c in self.cgi]
            if afd:
                out["afd_cascade_ca_uM"] = float(ca[afd].mean())
                out["afd_cgmp_uM"] = float(self.cas.x[self.cas.i["cGMP"], afd].mean())
                out["afd_Tstar_C"] = self.Tstar
        if len(self.tc):
            e1 = np.exp(-dt_ms * q.get("gating", 1.0) / p["sens_trpv_tauG_ms"])
            e2 = np.exp(-dt_ms * q.get("gating", 1.0) / (1000.0 * p["sens_trpv_tauD_s"]))
            self.G = r + (self.G - r) * e1
            self.D = self.G + (self.D - self.G) * e2
            po = np.clip(self.G * (1.0 - p["sens_trpv_phi"] * self.D), 0.0, 1.0)
            g = p["sens_trpv_g_nS"] * po
            if self.glia:
                g = np.where(self.amph_tc, g * self.b.layers.p["glia_gain"], g)
            self.g_trpv.set(g)
            I += self.g_trpv.current_pA(ctx.v, self.n)
            np.add.at(gs, self.g_trpv.idx, self.g_trpv.g_nS)
            out["sens_trpv_po"] = {c: float(po[k]) for c, k in self.tci.items()}
        res = {}
        if self.lumped:
            res["I_pA"] = lumped_current(self.b, self.lumped, ctx.obs, dt_ms)
        out["sens_I_pA"] = I + (res["I_pA"] if self.lumped else 0.0)
        out["sens_g_nS"] = gs
        res["out"] = out
        if self.awa_secs:
            res["g_scale"] = self._awa_gscale()
        return res

    def _awa_gscale(self):
        """AWA's BAAIWorm channels and somatic leak scaled to 0 (Liu's membrane replaces them); its synapses
        ("release", "rec_<class>") stay at 1."""
        from wormemu.mech import G_SCALE_NAMES
        if not hasattr(self, "_gsc"):
            self._gsc = {}
            for nm in G_SCALE_NAMES:
                if nm == "release" or nm.startswith("rec_"):
                    continue
                x = np.ones(self.n)
                x[self.awa_idx] = 0.0
                self._gsc[nm] = x
        return self._gsc
