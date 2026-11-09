"""Row 14: the intestine as a Ca oscillator and wave, and the defecation motor program's three outputs.

    oscillator  every intestinal cell (int1 x 4, int2-int9 x 2: the 20 cells) is a Li & Rinzel 1994 IP3 receptor Ca
                cell (J Theor Biol 166:461, the two-variable reduction of De Young & Keizer 1992 PNAS 89:9895; the
                rates as in Ermentrout's LiRinzel.ode, sites.pitt.edu/~phase/bard/bardware): ER release through ITR-1
                (m_inf^3 n_inf^3 h^3), SERCA uptake (Hill 2), ER leak, h the IP3R's slow Ca inactivation. These are
                generic IP3R kinetics, not C. elegans measurements (no worm rate constants are published: PORT_SOURCES
                O3), so they are labelled guessed. Two values are fitted: a2, the IP3R's recovery from inactivation,
                with the non-pacemaker cells' resting IP3, to Espelt et al. 2005's period (49 s) and wave velocity
                (33 um/s) on the coupled isolated intestine (Dal Santo et al. 1999: the period is set by ITR-1).
                IP3 per cell: a basal PLC-gamma rate (Espelt 2005: PLC-gamma makes the IP3 that drives ITR-1) plus
                a Ca-stimulated PLC term (Teramoto & Iwasaki 2006's Ca -> PLC feedback), first-order degradation.
                int9's basal rate is higher (the pacemaker: the wave starts at the posterior end, Espelt 2005,
                Teramoto & Iwasaki 2006); the other cells are excitable, not oscillating.
    wave        INX-16 gap junctions (Peters et al. 2007) pass IP3 and Ca between cells of a ring and of adjacent
                rings, as a permeability over the ring length (guessed; the velocity is fitted through the resting
                IP3, not through the permeability).
    pBoc        Beg et al. 2008: Ca drives the PBO-4 Na/H exchanger on the basolateral intestine; the protons in the
                cleft open PBO-5/PBO-6 (pH50 6.83, Hill 5, measured in oocytes) on the posterior body-wall muscles.
                Here one posterior cleft: H+ release = rate x Hill(posterior ring Ca), cleared with Beg's 2.9 s
                decay; the PBO-5/6 cation conductance (E_rev 0 mV) sits on the posterior third of the BWM, one wgc
                point process per muscle (nmodl/wgc.mod), its g set each exchange step and solved implicitly by
                NEURON (wbody2, 9 Nov, A, inbox 01:45; nested `pboc_g_solver=explicit`: the code before,
                g (E - V) from the step's start V into I_pA, which alternates at 12-14 nS on these muscles, weki).
    NLP-40      Wang et al. 2013 (Curr Biol 23:746): Ca-dependent (SNT-2) release of NLP-40 from the intestine
                activates the AEX-2 GPCR on AVL and DVB. Here each cell releases at rate x Hill(its Ca) / 20 (the
                total is rate x the mean Hill), into the pseudocoelom compartment its ring lies in
                (_ring_compartment_shares: rings 1-4 and part of 5 in the anterior body, the rest in the posterior
                body; wbody2, 8 Nov, A: all 20 cells used to release next to DVB, so the anterior rings' release,
                seconds after int9's on Espelt 2005's 20-60 um/s wave, smeared the cycle at DVB).
                out['peptide_release'] = {'nlp-40@<compartment>': molecules/s} (the nM/s rate times neuromod's
                posterior-body compartment volume, split by ring), which mech.neuromod adds to its pool and reads at
                AEX-2 (default `release_only`); the local concentration (own decay plus the coelomocytes' uptake,
                outputs['coelomocyte_uptake_per_s'], row 16) is read only by the nested `direct` form. The nested form `direct` (the first
                port) instead puts an AEX-2 current (gain x occupancy of the local pool) into AVL and DVB here.
    enteric     the 4 enteric muscles (mu_intL, mu_intR, mu_anal, mu_sph) as cells with the Du/Crodelle 2025 BWM
                membrane (nmodl/organs/du_bwm.mod; inferred: the enteric muscle membrane is not recorded), Cook 2019's
                gaps among them at Liu 2006's BWM gap (inferred), Cook's DVB synapses onto mu_intL/R as excitatory
                (the EXP-1 GABA-gated cation channel: Beg & Jorgensen 2003 Nat Neurosci 6:1145; organs_nrn.chem_synapse,
                the brain's gabacat class when receptor kinetics run). Ca -> activation is
                row 12's Boyle-Berri-Cohen integrator. One expulsion = the mean intestinal-muscle and anal-depressor
                activation rising above ent_exp_on and falling below ent_exp_off. Cook's hypodermis gaps to these
                muscles wait for row 16's hypodermis.

Nested simpler forms (toggle values):
    defecation       ip3r (default) | timer (brain_layers' 45 s clock, verbatim) | off
    pboc_protons     on (default) | off
    pboc_g_solver    implicit (default) | explicit
    nlp40_aex2       release_only (default: only out['peptide_release'], for neuromod) | direct | off
    enteric_muscle   du2025 (default) | off
The id defecation is brain_layers' id, so this module takes that toggle over. At reset the intestine is run alone
for brain_layers' random phase draw (dmp_t, 0-45 s), so a worm starts at a random point of its cycle as before.
"""
from __future__ import annotations

import numpy as np

from wormemu.brain_layers import Spec
from wormemu.interface import BWM_NAMES, ENTERIC_MUSCLES

NA_PL = 602.214                       # molecules per pL per nM (mech.neuromod's constant)

LR = ("Li & Rinzel 1994 J Theor Biol 166:461 (De Young & Keizer 1992 PNAS 89:9895 rates; values as in Ermentrout's "
      "LiRinzel.ode, opened)")
ESP = "Espelt, Estevez, Yin & Strange 2005 J Gen Physiol 126:379 (PMC2266627: period, wave velocity, rise/fall)"
TI = "Teramoto & Iwasaki 2006 Cell Calcium 40:319 (Ca -> PLC feedback; not opened)"
BEG = "Beg, Ernstrom, Nix, Davis & Jorgensen 2008 Cell 132:149 (PMC2258244: PBO-5/6 pH50, Hill, cleft pH kinetics)"
WANG = "Wang et al. 2013 Curr Biol 23:746 (NLP-40 -> AEX-2 on AVL/DVB; full text not opened)"
OLD = "brain_layers lumped defecation clock (the nested simpler form)"

MECHANISMS = [
    ("defecation", "Defecation: 20-cell intestinal IP3R (Li-Rinzel) Ca oscillator and INX-16 wave (nested: 45 s "
     "timer)", "organ", "ip3r"),
    ("pboc_protons", "Intestinal H+ (PBO-4) -> PBO-5/6 cation current in the posterior body-wall muscles", "organ",
     "on"),
    ("pboc_g_solver", "PBO-5/6 conductance as NEURON point processes, implicit (nested explicit: g (E - V) from the "
     "step's start V as a current)", "organ", "implicit"),
    ("nlp40_aex2", "Intestinal NLP-40 release into neuromod's pool (nested direct: an AEX-2 current in AVL and DVB "
     "here)", "organ", "release_only"),
    ("enteric_muscle", "Enteric muscles: Du 2025 membrane, Cook gaps, DVB EXP-1 synapses, Ca -> activation", "muscle",
     "du2025"),
]

PRE_DT_MS = 5.0          # step of the intestine's pre-run at reset (the cycle phase), ms

# the 20 cells, anterior to posterior, and their ring (1-9)
INT_CELLS = ["int1DL", "int1DR", "int1VL", "int1VR"] + [f"int{k}{s}" for k in range(2, 10) for s in ("L", "R")]
RING = np.array([int(n[3]) for n in INT_CELLS])

_D = "defecation"
_C = "intestinal cell"
_GEN = "generic IP3R kinetics (not C. elegans); range 0.5-2x, guessed"


def _s(pid, unit, v, lo, hi, source, label="guessed", notes="", mech=_D, applies=_C, grain="class"):
    return Spec(pid, mech, unit, v, lo, hi, source=source, label=label, grain=grain, applies_to=applies, notes=notes)


def _lr(pid, unit, v, notes=_GEN):
    return _s(pid, unit, v, *sorted((0.5 * v, 2.0 * v)), LR, notes=notes)


SPECS = [
    # Li-Rinzel IP3R Ca cell
    _lr("int_lr_c0_uM", "uM", 2.0, notes="total Ca over cytosolic volume; " + _GEN),
    _lr("int_lr_c1", "ratio", 0.185, notes="ER over cytosolic volume; " + _GEN),
    _lr("int_lr_v1_per_s", "1/s", 6.0, notes="ITR-1 maximal release rate; " + _GEN),
    _lr("int_lr_v2_per_s", "1/s", 0.11, notes="ER leak; " + _GEN),
    _lr("int_lr_v3_uM_per_s", "uM/s", 0.9, notes="SERCA maximal rate; " + _GEN),
    _lr("int_lr_k3_uM", "uM", 0.1, notes="SERCA half-activation (Li-Rinzel 0.1; Ermentrout's file 0.05); " + _GEN),
    _lr("int_lr_d1_uM", "uM", 0.13, notes="IP3 dissociation; " + _GEN),
    _lr("int_lr_d2_uM", "uM", 1.049, notes="Ca inactivation dissociation; " + _GEN),
    _lr("int_lr_d3_uM", "uM", 0.9434, notes="IP3 dissociation (inactivated); " + _GEN),
    _lr("int_lr_d5_uM", "uM", 0.08234, notes="Ca activation dissociation; " + _GEN),
    _s("int_lr_a2_per_uM_s", "1/(uM s)", 0.034, 0.01, 0.2, ESP + "; " + LR, label="inferred",
       notes="IP3R recovery from Ca inactivation; fitted with int_ip3_rest_uM on the coupled isolated intestine to "
             "Espelt 2005's period 49 s and wave velocity 33 um/s (dt 5 ms grid: 50.1 s, 33.3 um/s); Li-Rinzel's 0.2 "
             "gives a ~12 s period; range guessed. (Attempt 1, fitted on the lone int9 cell: 0.023.)"),
    # IP3 production and degradation
    _s("int_ip3_tau_s", "s", 7.14, 2.0, 20.0, "Ermentrout LiRinzel.ode tau_ip3 (astrocyte); worm value guessed"),
    _s("int_ca_rest_uM", "uM", 0.1, 0.05, 0.2, LR, notes="resting cytosolic Ca: the start value and the PLC "
       "baseline (Ca-stimulated PLC adds only above it); guessed, a usual resting level", applies=_C),
    _s("int_ip3_rest_uM", "uM", 0.348, 0.2, 0.355, ESP + "; " + LR, label="inferred", notes="basal PLC-gamma rate x "
       "tau: the resting IP3 of the non-pacemaker cells, kept below Li-Rinzel's oscillation onset (~0.355 uM) so they "
       "are excitable, not oscillating; fitted with a2 to Espelt 2005's period and velocity (attempt 1 guess: 0.30)"),
    _s("int_ip3_rest_pacemaker_uM", "uM", 0.42, 0.36, 0.6, ESP + "; " + LR, notes="int9's resting IP3: inside "
       "Li-Rinzel's oscillating range, so int9 is the pacemaker (the wave starts posteriorly); value guessed"),
    _s("int_plc_ca_uM_per_s", "uM/s", 0.042, 0.0, 0.2, TI, notes="Ca-stimulated PLC maximal rate (Teramoto & "
       "Iwasaki's Ca -> PLC loop); guessed so a Ca spike adds ~0.3 uM of IP3"),
    _s("int_plc_ca_k_uM", "uM", 0.3, 0.1, 1.0, TI, notes="half-activation of the Ca-stimulated PLC; guessed"),
    _s("int_plc_ca_hill", "1", 2.0, 1.0, 4.0, TI, notes="guessed"),
    # INX-16 coupling
    _s("int_gap_p_ip3_um_s", "um/s", 2.0, 0.1, 10.0, "Peters et al. 2007 Curr Biol 17:1601 (INX-16 carries the "
       "wave; no number); guessed", notes="IP3 permeability of the junctions between neighbouring cells"),
    _s("int_gap_p_ca_um_s", "um/s", 0.5, 0.0, 5.0, "Peters et al. 2007 (no number); guessed",
       notes="effective (buffered) Ca permeability of the junctions"),
    _s("int_ring_length_um", "um", 80.0, 60.0, 100.0, "WormAtlas intestine (~720 um over 9 rings); guessed",
       notes="cell length along the body, sets the junction exchange rate P / L and the wave velocity readout"),
    # pBoc: protons
    _s("int_cleft_ph_rest", "pH", 7.35, 7.0, 7.6, BEG, notes="pseudocoelomic pH at rest; not given in Beg 2008; "
       "guessed", mech="pboc_protons", applies="posterior intestine-muscle cleft"),
    _s("int_h_release_nM_per_s", "nM/s", 160.0, 20.0, 800.0, BEG, notes="PBO-4 maximal H+ release into the cleft; "
       "guessed so a full Ca spike takes the cleft to about pH 6.3", mech="pboc_protons", applies="intestinal cell"),
    _s("int_h_release_k_uM", "uM", 0.3, 0.1, 1.0, BEG, notes="Ca half-activation of PBO-4 release; guessed",
       mech="pboc_protons", applies="intestinal cell"),
    _s("int_h_release_hill", "1", 2.0, 1.0, 4.0, BEG, notes="guessed", mech="pboc_protons", applies="intestinal cell"),
    _s("int_h_tau_s", "s", 2.9, 2.6, 3.2, BEG, label="measured", notes="cleft acidification decay to baseline, "
       "2.9 +- 0.3 s (Fig. 4; rise 1.9 s)", mech="pboc_protons", applies="posterior intestine-muscle cleft"),
    _s("pbo5_ph50", "pH", 6.83, 6.82, 6.84, BEG, label="measured", notes="PBO-5/PBO-6 in Xenopus oocytes, "
       "6.83 +- 0.01 (Fig. 6C)", mech="pboc_protons", applies="posterior body-wall muscle"),
    _s("pbo5_hill", "1", 5.0, 4.0, 6.0, BEG, label="measured", notes="steep Hill coefficient of 5 (Fig. 6C); range "
       "guessed", mech="pboc_protons", applies="posterior body-wall muscle"),
    _s("pbo5_erev_mV", "mV", 0.0, -10.0, 10.0, BEG, label="inferred", notes="non-selective cation channel; reversal "
       "not given; inferred", mech="pboc_protons", applies="posterior body-wall muscle"),
    _s("pbo5_g_nS", "nS", 1.0, 0.1, 10.0, BEG, notes="PBO-5/6 conductance per posterior muscle at full opening; "
       "guessed (oocyte currents only)", mech="pboc_protons", applies="posterior body-wall muscle"),
    _s("pbo5_posterior_frac", "body length", 0.33, 0.2, 0.5, BEG, label="inferred", notes="the BWM behind this "
       "fraction of the body length carry PBO-5/6 (posterior body muscles; pBoc is posterior)",
       mech="pboc_protons", applies="posterior body-wall muscle"),
    _s("int_posterior_rings", "rings", 3.0, 2.0, 5.0, BEG, label="inferred", notes="the last n rings face the "
       "posterior muscles' cleft (int7-int9); guessed count", mech="pboc_protons", applies="intestinal cell"),
    # NLP-40 -> AEX-2
    _s("nlp40_release_nM_per_s", "nM/s", 15.0, 1.0, 100.0, WANG, notes="maximal Ca-dependent (SNT-2) release; "
       "guessed", mech="nlp40_aex2", applies="intestinal cell", grain="global"),
    _s("nlp40_release_k_uM", "uM", 0.3, 0.1, 1.0, WANG, notes="guessed", mech="nlp40_aex2", applies="intestinal cell"),
    _s("nlp40_release_hill", "1", 2.0, 1.0, 4.0, WANG, notes="guessed", mech="nlp40_aex2", applies="intestinal cell"),
    _s("nlp40_tau_s", "s", 2.0, 0.5, 10.0, WANG, notes="pseudocoelomic decay besides coelomocyte uptake (AVL/DVB "
       "fire one Ca transient per cycle); guessed", mech="nlp40_aex2", applies="pseudocoelom", grain="global"),
    _s("aex2_ec50_nM", "nM", 10.0, 1.0, 100.0, WANG, notes="guessed", mech="nlp40_aex2", applies="AVL, DVB"),
    _s("aex2_gain_pA", "pA", 10.0, 1.0, 30.0, WANG, notes="depolarising current at full occupancy (synthetic NLP-40 "
       "depolarises the GABAergic neurons); guessed", mech="nlp40_aex2", applies="AVL, DVB"),
    # enteric muscles
    _s("ent_c_pF", "pF", 22.0, 11.0, 44.0, "Du, Crodelle et al. 2025 (BWM 22 pF)", label="inferred",
       notes="enteric muscle capacitance taken from the BWM model", mech="enteric_muscle", applies="enteric muscle"),
    _s("ent_gap_nS_per_contact", "nS", 0.35, 0.05, 0.35, "Liu, Chen & Wang 2006 J Biol Chem 281:7881 (BWM)",
       label="inferred", notes="BWM junctional conductance (<= 350 pS) per Cook contact", mech="enteric_muscle",
       applies="enteric muscle"),
    _s("ent_dvb_excitatory", "flag", 1.0, 1.0, 1.0, "Beg & Jorgensen 2003 Nat Neurosci 6:1145 (EXP-1)",
       label="measured", notes="GABA onto the enteric muscles opens the EXP-1 cation channel: excitatory",
       mech="enteric_muscle", applies="enteric muscle"),
    _s("ent_act_khalf_mM", "mM", 0.014, 0.002, 0.05, "Boyle, Berri & Cohen 2012 (form); row 12's value",
       label="inferred", notes="the BWM value (bwm_act_khalf_mM) used for enteric muscle", mech="enteric_muscle",
       applies="enteric muscle"),
    _s("ent_act_hill", "1", 2.0, 1.0, 4.0, "row 12's value", label="inferred", notes="the BWM value",
       mech="enteric_muscle", applies="enteric muscle"),
    _s("ent_act_tau_ms", "ms", 100.0, 50.0, 200.0, "Boyle, Berri & Cohen 2012 (tau_M = 100 ms, BWM)",
       label="inferred", notes="the BWM value", mech="enteric_muscle", applies="enteric muscle"),
    _s("ent_exp_on", "activation", 0.5, 0.2, 0.8, "this model", notes="expulsion detector, guessed",
       mech="enteric_muscle", applies="enteric muscle"),
    _s("ent_exp_off", "activation", 0.2, 0.05, 0.4, "this model", notes="expulsion detector, guessed",
       mech="enteric_muscle", applies="enteric muscle"),
]

# brain_layers' defecation clock (the nested timer form) uses its own dmp_* specs
_OLD = {"dmp_period_s": 45.0, "dmp_pboc_dur_s": 2.0, "dmp_aboc_delay_s": 3.0, "dmp_aboc_dur_s": 1.0,
        "dmp_exp_delay_s": 4.0, "dmp_exp_dur_s": 0.3, "dmp_pboc_amp": 0.5, "dmp_pboc_frac": 0.33}


def defaults():
    q = {s.id: s.template for s in SPECS}
    q.update(_OLD)
    return q


def _hill(x, k, n):
    x = np.maximum(x, 0.0)
    return x ** n / (x ** n + k ** n)


def neighbours():
    """(i, j) pairs, i < j: cells in the same ring and in adjacent rings (INX-16 junctions)."""
    return [(i, j) for i in range(len(INT_CELLS)) for j in range(i + 1, len(INT_CELLS)) if abs(RING[i] - RING[j]) <= 1]



def _pc_params(brain):
    """mech.neuromod's pseudocoelom parameters (templates, or this worm's spec values)."""
    from wormemu import mech
    from wormemu.mech import neuromod
    p = {x.id: x.template for x in neuromod.SPECS}
    if getattr(brain, "spec", None) is not None and getattr(brain.spec, "values", None) is not None:
        p.update(mech.params_for(neuromod, brain.spec))
    return p


def _posterior_volume_um3(brain):
    """neuromod's posterior-body compartment volume (cross-section x vulva-to-tail length), um3."""
    p = _pc_params(brain)
    return float(p["pc_cross_section_um2"]) * (float(p["pc_tail_start_y_um"]) - float(p["pc_vulva_y_um"]))


def _ring_compartment_shares(brain):
    """(20 cells, neuromod.COMPARTMENTS): each intestinal cell's share of its NLP-40 release in each pseudocoelom
    compartment. Ring k spans fraction (k-1)/9 to k/9 of the intestine, which runs from neuromod's head cut (just
    behind the retrovesicular ganglion, about the pharynx's end) to its tail cut (the pre-anal ganglion, about the
    rectum); rings of equal length (WormAtlas: 9 rings over about 720 um; inferred), release uniform along a ring
    (inferred); split by length overlap. Rows sum to 1."""
    from wormemu.mech import neuromod
    p = _pc_params(brain)
    y0, yv, y1 = (float(p[k]) for k in ("pc_head_end_y_um", "pc_vulva_y_um", "pc_tail_start_y_um"))
    edges = [-np.inf, y0, yv, y1, np.inf]
    W = np.zeros((len(INT_CELLS), len(neuromod.COMPARTMENTS)))
    for i, r in enumerate(RING):
        a, b = y0 + (r - 1) / 9.0 * (y1 - y0), y0 + r / 9.0 * (y1 - y0)
        for c in range(len(neuromod.COMPARTMENTS)):
            W[i, c] = max(0.0, min(b, edges[c + 1]) - max(a, edges[c])) / (b - a)
    return W

class Intestine:
    """The 20 Li-Rinzel cells with IP3, Ca -> PLC and INX-16 exchange (numpy; the CPU reference and the run path).
    Time in s, concentrations in uM. `ip3r` scales the ITR-1 flux (0 = itr-1 null)."""

    def __init__(self, q, ip3r=1.0):
        self.q, self.ip3r = q, ip3r
        n = len(INT_CELLS)
        pace = RING == 9
        self.p_rest = np.where(pace, q["int_ip3_rest_pacemaker_uM"], q["int_ip3_rest_uM"])
        pr = np.array(neighbours())
        self.A = np.zeros((n, n))
        self.A[pr[:, 0], pr[:, 1]] = self.A[pr[:, 1], pr[:, 0]] = 1.0
        self.L = self.A - np.diag(self.A.sum(1))             # graph Laplacian: sum_j (x_j - x_i)
        self.reset()

    def reset(self):
        q = self.q
        self.c = np.full(len(INT_CELLS), q["int_ca_rest_uM"])
        self.p = self.p_rest.copy()
        self.h = q["int_lr_d2_uM"] * (self.p + q["int_lr_d1_uM"]) / (self.p + q["int_lr_d3_uM"])
        self.h = self.h / (self.h + self.c)                   # h at steady state for c

    def step(self, dt_s):
        q, c, p, h = self.q, self.c, self.p, self.h
        c0, c1 = q["int_lr_c0_uM"], q["int_lr_c1"]
        cer = (c0 - c) / c1
        m = p / (p + q["int_lr_d1_uM"])
        ni = c / (c + q["int_lr_d5_uM"])
        j_chan = self.ip3r * c1 * q["int_lr_v1_per_s"] * (m * ni * h) ** 3 * (c - cer)
        j_pump = q["int_lr_v3_uM_per_s"] * c * c / (q["int_lr_k3_uM"] ** 2 + c * c)
        j_leak = c1 * q["int_lr_v2_per_s"] * (c - cer)
        k_ip3 = q["int_gap_p_ip3_um_s"] / q["int_ring_length_um"]
        k_ca = q["int_gap_p_ca_um_s"] / q["int_ring_length_um"]
        a2 = q["int_lr_a2_per_uM_s"]
        q2 = q["int_lr_d2_uM"] * (p + q["int_lr_d1_uM"]) / (p + q["int_lr_d3_uM"])
        tau = q["int_ip3_tau_s"]
        k, n = q["int_plc_ca_k_uM"], q["int_plc_ca_hill"]
        plc = self.p_rest / tau + q["int_plc_ca_uM_per_s"] * (_hill(c, k, n) - _hill(q["int_ca_rest_uM"], k, n))
        dc = -j_chan - j_pump - j_leak + k_ca * (self.L @ c)
        dh = a2 * q2 * (1.0 - h) - a2 * c * h
        dp = plc - p / tau + k_ip3 * (self.L @ p)
        self.c = np.maximum(c + dt_s * dc, 0.0)
        self.h = np.clip(h + dt_s * dh, 0.0, 1.0)
        self.p = np.maximum(p + dt_s * dp, 0.0)
        return self.c


class Cleft:
    """The posterior intestine-muscle cleft: H+ (nM above rest) released by PBO-4, cleared with Beg's tau."""

    def __init__(self, q):
        self.q = q
        self.reset()

    def reset(self):
        self.dh = 0.0

    def step(self, c_post_uM, dt_s):
        q = self.q
        rel = q["int_h_release_nM_per_s"] * float(np.mean(_hill(c_post_uM, q["int_h_release_k_uM"],
                                                                  q["int_h_release_hill"])))
        self.dh += dt_s * (rel - self.dh / q["int_h_tau_s"])
        return self.ph

    @property
    def ph(self):
        return float(-np.log10(10.0 ** (-self.q["int_cleft_ph_rest"]) + self.dh * 1e-9))

    def p_open(self):
        q = self.q
        return 1.0 / (1.0 + 10.0 ** (q["pbo5_hill"] * (self.ph - q["pbo5_ph50"])))


def peaks(t, x, frac=0.5):
    """Times where x rises through frac of its range (one per transient)."""
    lo, hi = float(np.min(x)), float(np.max(x))
    thr = lo + frac * (hi - lo)
    k = np.flatnonzero((x[1:] >= thr) & (x[:-1] < thr)) + 1
    return t[k]


def run_isolated(q=None, t_s=600.0, dt_ms=0.5, ip3r=1.0, every=20):
    """The intestine alone. Returns (t s, Ca (steps, 20) uM, cleft pH, PBO-5/6 open fraction)."""
    q = q or defaults()
    gut, cleft = Intestine(q, ip3r), Cleft(q)
    post = RING > 9 - q["int_posterior_rings"]
    n = int(round(t_s * 1000.0 / dt_ms))
    T, C, PH, PO = [], [], [], []
    for k in range(n):
        c = gut.step(dt_ms / 1000.0)
        cleft.step(c[post], dt_ms / 1000.0)
        if k % every == 0:
            T.append(k * dt_ms / 1000.0)
            C.append(c.copy())
            PH.append(cleft.ph)
            PO.append(cleft.p_open())
    return np.array(T), np.array(C), np.array(PH), np.array(PO)


def single_cell_period(q, p_uM, t_s=600.0, dt_s=0.005):
    """Free period of one Li-Rinzel cell at fixed IP3 (for fitting a2), or None if it does not oscillate."""
    c, h = 0.1, 0.7
    cs = []
    c0, c1 = q["int_lr_c0_uM"], q["int_lr_c1"]
    a2, d1, d2, d3, d5 = (q[k] for k in ("int_lr_a2_per_uM_s", "int_lr_d1_uM", "int_lr_d2_uM", "int_lr_d3_uM",
                                         "int_lr_d5_uM"))
    for _ in range(int(t_s / dt_s)):
        cer = (c0 - c) / c1
        jc = c1 * q["int_lr_v1_per_s"] * (p_uM / (p_uM + d1) * c / (c + d5) * h) ** 3 * (c - cer)
        jp = q["int_lr_v3_uM_per_s"] * c * c / (q["int_lr_k3_uM"] ** 2 + c * c)
        c, h = c + dt_s * (-jc - jp - c1 * q["int_lr_v2_per_s"] * (c - cer)), \
            h + dt_s * (a2 * d2 * (p_uM + d1) / (p_uM + d3) * (1 - h) - a2 * c * h)
        cs.append(c)
    cs = np.array(cs[len(cs) // 3:])
    if cs.max() - cs.min() < 0.05:
        return None
    up = peaks(np.arange(len(cs)) * dt_s, cs)
    return float(np.diff(up).mean()) if len(up) > 1 else None


class Mech:
    """Steps the intestine; puts the PBO-5/6 current into the posterior BWM and the AEX-2 current into AVL and DVB;
    builds the 4 enteric muscle cells. The nested timer form runs brain_layers' clock instead and builds nothing."""

    def __init__(self, brain, params, toggles):
        self.brain = brain
        q = defaults()
        q.update(getattr(getattr(brain, "layers", None), "p", None) or {})
        q.update({k: float(v) for k, v in params.items() if np.isscalar(v)})
        self.q = q
        self.form = toggles.get("defecation", "ip3r")
        self.pboc = toggles.get("pboc_protons", "on")
        self.solver = toggles.get("pboc_g_solver", "implicit")
        self.nlp = toggles.get("nlp40_aex2", "release_only")
        if self.nlp == "on":
            self.nlp = "release_only"
        self.nlp_V_um3 = _posterior_volume_um3(brain)
        from wormemu.mech.neuromod import COMPARTMENTS
        self.nlp_W = _ring_compartment_shares(brain)
        self.nlp_keys = [(k, f"nlp-40@{cp}") for k, cp in enumerate(COMPARTMENTS) if self.nlp_W[:, k].any()]
        self.ent = toggles.get("enteric_muscle", "du2025")
        assert self.form in ("ip3r", "timer", "off") and self.pboc in ("on", "off")
        assert self.solver in ("implicit", "explicit"), self.solver
        assert self.nlp in ("direct", "release_only", "off") and self.ent in ("du2025", "off")
        self.n = len(brain.cell_names)
        self.bwm = np.asarray(brain.bwm)
        bp = np.asarray(getattr(brain.layers, "bwm_pos", np.linspace(0, 1, len(BWM_NAMES))))
        self.bwm_pos = bp
        post = (bp > 1.0 - q["pbo5_posterior_frac"]) & (self.bwm >= 0)
        self.post_cells = self.bwm[post]
        self.post_rings = RING > 9 - q["int_posterior_rings"]
        self.aex2_cells = np.array([brain.idx[c] for c in ("AVL", "DVB") if c in brain.idx], int)
        self.gut, self.cleft = Intestine(q), Cleft(q)
        self.n_syn = self.n_gap = 0
        self.gpb = None                           # the PBO-5/6 wgc conductances (implicit form, NEURON brain only)
        if self.pboc == "on" and self.solver == "implicit" and getattr(brain, "soma", None) is not None:
            h = brain.h
            self.gpb = [h.wgc(brain.soma[i](0.5)) for i in self.post_cells]
            self._pgb = h.PtrVector(max(1, len(self.gpb)))
            for k, pp in enumerate(self.gpb):
                pp.e, pp.g = q["pbo5_erev_mV"], 0.0
                self._pgb.pset(k, pp._ref_g)
        if self.ent == "du2025" and self.form == "ip3r":
            self._build_enteric()
        self.reset()

    def _build_enteric(self):
        from wormemu.mech import muscle_bwm as mb, organs_nrn
        b, q = self.brain, self.q
        h = b.h
        organs_nrn.load_organ_mods(h)
        vals = getattr(b.spec, "values", {}) or {}
        qb = {s.id: (float(vals[s.id]) if s.id in vals and np.isscalar(vals[s.id]) else s.template) for s in mb.SPECS}
        self.sec = {}
        for n in ENTERIC_MUSCLES:
            sec = h.Section(name=f"enteric_{n}")
            sec.nseg, sec.L, sec.diam = 1, 20.0, 5.0              # BAAIWorm's muscle cylinder
            sec.insert("du_bwm")
            area = organs_nrn.area_um2(sec)
            mb.configure(sec, qb, area)
            sec.cm = q["ent_c_pF"] * 100.0 / area
            self.sec[n] = sec
        st, nm, mine = b.st, b.st.names, set(ENTERIC_MUSCLES)
        g = q["ent_gap_nS_per_contact"] / 1000.0
        for i, j, n in st.gap:
            if nm[i] in mine and nm[j] in mine:
                b._gap(self.sec[nm[i]](0.5), self.sec[nm[j]](0.5), n * g, "gap_enteric")
                self.n_gap += 1
        g_nmj = float(np.median(b.spec.v("nmj_strength_per_pair").to_numpy(float)))
        self.wsyn = []
        for i, j, n in st.chem:
            a, c = nm[i], nm[j]
            if c in mine and a in b.idx:
                inh = False if q["ent_dvb_excitatory"] > 0.5 else b._inhibitory(a, c)
                self.wsyn += organs_nrn.chem_synapse(b, a, self.sec[c](0.5), g_nmj * n, inh, "syn_enteric")
                self.n_syn += 1
        k = len(ENTERIC_MUSCLES)
        self._pca, self._pv = h.PtrVector(k), h.PtrVector(k)
        for x, n in enumerate(ENTERIC_MUSCLES):
            self._pca.pset(x, self.sec[n](0.5).du_bwm._ref_cad)
            self._pv.pset(x, self.sec[n](0.5)._ref_v)
        self._buf = h.Vector(k)

    def reset(self):
        from wormemu.mech.muscle_bwm import INIT
        self.gut.reset()
        self.cleft.reset()
        self.nlp40 = 0.0
        self.ent_act = np.zeros(len(ENTERIC_MUSCLES))
        self.in_exp, self.exp_total = False, 0
        self.dmp_t = float(getattr(self.brain.layers, "dmp_t", 0.0))
        if self.form == "ip3r":                   # start at a random point of the cycle: the timer's own phase draw
            for _ in range(int(self.dmp_t / PRE_DT_MS)):
                self.gut.step(PRE_DT_MS / 1000.0)
        for sec in getattr(self, "sec", {}).values():
            seg = sec(0.5)
            seg.v = INIT["v"]
            for k, x in INIT.items():
                if k != "v":
                    setattr(seg.du_bwm, k, x)
        for pp in self.gpb or []:
            pp.g = 0.0

    def timer(self, dt):
        """brain_layers.Layers.defecation, verbatim: (posterior/anterior BWM boost, enteric activation, expulsions)."""
        p = self.q
        t0 = self.dmp_t
        self.dmp_t = (self.dmp_t + dt) % (p["dmp_period_s"] * 1000.0)
        t = self.dmp_t / 1000.0
        boost = np.zeros(len(self.bwm_pos))
        if t < p["dmp_pboc_dur_s"]:
            boost[self.bwm_pos > 1 - p["dmp_pboc_frac"]] = p["dmp_pboc_amp"]
        a0, a1 = p["dmp_aboc_delay_s"], p["dmp_aboc_delay_s"] + p["dmp_aboc_dur_s"]
        e0, e1 = p["dmp_exp_delay_s"], p["dmp_exp_delay_s"] + p["dmp_exp_dur_s"]
        if a0 <= t < a1:
            boost[self.bwm_pos < p["dmp_pboc_frac"]] = p["dmp_pboc_amp"]
        ent = np.zeros(4)
        if e0 <= t < e1:
            ent[:] = 1.0
        n_exp = int(t0 / 1000.0 < e0 <= t)
        return boost, ent, n_exp

    def step(self, ctx, dt_ms):
        if self.form == "off":
            return {"out": {"expulsions": 0, "enteric_activation": np.zeros(len(ENTERIC_MUSCLES))}}
        qd = ctx.outputs.get("q10", {}).get("dmp_clock", 1.0)     # row 25: the clock on temperature's time axis
        if self.form == "timer":
            boost, ent, n_exp = self.timer(dt_ms * qd)
            self.exp_total += n_exp
            return {"act_add": boost, "out": {"expulsions": n_exp, "enteric_activation": ent,
                                              "expulsions_total": self.exp_total}}
        q, dt_s = self.q, dt_ms / 1000.0
        c = self.gut.step(dt_s * qd)
        I = np.zeros(self.n)
        out = {"intestine_ca_uM": c.copy(), "intestine_ip3_uM": self.gut.p.copy()}
        if self.pboc == "on":
            self.cleft.step(c[self.post_rings], dt_s)
            po = self.cleft.p_open()
            if self.gpb is None:
                v = np.asarray(ctx.v)[self.post_cells]
                I[self.post_cells] += q["pbo5_g_nS"] * po * (q["pbo5_erev_mV"] - v)      # nS x mV = pA
            elif self.gpb:
                self._pgb.scatter(self.brain.h.Vector(np.full(len(self.gpb), q["pbo5_g_nS"] * po * 1e-3)))   # uS
            out.update(cleft_pH=self.cleft.ph, pbo5_open=po)
        if self.nlp != "off":
            hc = _hill(c, q["nlp40_release_k_uM"], q["nlp40_release_hill"])
            rel = q["nlp40_release_nM_per_s"] * float(np.mean(hc))
            k_out = 1.0 / q["nlp40_tau_s"] + float(ctx.outputs.get("coelomocyte_uptake_per_s", 0.0))
            self.nlp40 += dt_s * (rel - k_out * self.nlp40)
            mol = q["nlp40_release_nM_per_s"] * NA_PL * self.nlp_V_um3 / 1000.0 * (hc @ self.nlp_W) / len(hc)
            out.update(peptide_release={key: float(mol[k]) for k, key in self.nlp_keys}, nlp40_nM=self.nlp40)
            if self.nlp == "direct" and len(self.aex2_cells):
                I[self.aex2_cells] += q["aex2_gain_pA"] * self.nlp40 / (self.nlp40 + q["aex2_ec50_nM"])
        n_exp = 0
        if self.ent == "du2025":
            self._pca.gather(self._buf)
            ca = self._buf.as_numpy().copy()
            target = _hill(ca, q["ent_act_khalf_mM"], q["ent_act_hill"])
            self.ent_act = target + (self.ent_act - target) * np.exp(-dt_ms / q["ent_act_tau_ms"])
            a = float(self.ent_act[:3].mean())                    # mu_intL, mu_intR, mu_anal
            if not self.in_exp and a > q["ent_exp_on"]:
                self.in_exp = True
            elif self.in_exp and a < q["ent_exp_off"]:
                self.in_exp, n_exp = False, 1
                self.exp_total += 1
            self._pv.gather(self._buf)
            out.update(enteric_v_mV=self._buf.as_numpy().copy(), enteric_ca_mM=ca)
        out.update(expulsions=n_exp, enteric_activation=self.ent_act.copy(), expulsions_total=self.exp_total)
        return {"I_pA": I, "out": out}
