"""Catalog slots: the parameters each PLAN row's published model needs (docs/worm/research/PORT_SOURCES_NEURAL.md,
PORT_SOURCES_ORGANS.md, PLAN.md) before any code reads them. ledger_catalog.slots() lists them in the catalog with
used_by_code = "slot only" (or "yes" for the few structure counts the build uses), and drops each one as soon as a
row the code reads has its id or one of the ids in `match`. Builders: reuse a slot's id in your Spec and it replaces
the slot.

Every value here is copied from the research file named in the quote (the paper's own URL where the file gives one;
a PMC id named there is linked as https://pmc.ncbi.nlm.nih.gov/articles/<PMC id>/). A quote is "FILE SECTION: text"
with text copied verbatim from FILE, so the audit can check it (ledger_catalog.audit). Slots with no published value
carry a bounded guess (label guessed, bound_basis guessed) and name the paper that would pin it; a value that is
published in a free paper but not yet read is label absent (no number yet).
"""
from __future__ import annotations

import math

NEURAL, ORGANS, PLAN = "PORT_SOURCES_NEURAL.md", "PORT_SOURCES_ORGANS.md", "PLAN.md"
PMC = "https://pmc.ncbi.nlm.nih.gov/articles/{}/".format
CYS_REVIEW = PMC("PMC10480131")

MECH_NAMES = {
    "cells": "Cell inventory (counts by cell type)",
    "expression_map": "CeNGEN expression gates channel presence",
    "receptor_classes": "Postsynaptic receptor classes with kinetics (N1: EC50, Hill, unitary conductance, decay, "
                        "reversal per class)",
    "graded_release": "Graded transmitter release per synapse (N1)",
    "gap_per_innexin": "Gap junction conductance per innexin (PLAN row 8)",
    "peptide_cascade": "Peptide diffusion and the receptor-family G-protein cascade (N4)",
    "monoamine_uptake": "Monoamine reuptake by MOD-5 (SERT) and DAT-1 (N4)",
    "glia_clearance": "Glial ion clearance and glia-neuron coupling (O5)",
    "muscle_du2025": "Du/Crodelle 2025 body-wall muscle membrane with SLO-2 (O1)",
    "pharynx_fhn": "FitzHugh-Nagumo pharyngeal network with MC/M3 synapses (O2)",
    "intestine_ip3": "Intestinal IP3 receptor calcium oscillator and its outputs (O3)",
    "egg_circuit": "Egg-laying circuit: HSN and VC activity, vulval muscle channels, tyramine feedback (O4)",
    "other_cells": "Hypodermis, excretory canal, coelomocytes (O6)",
    "sens_awa_spike": "AWA calcium spikes (N5, Liu et al. 2018)",
    "sens_touch_sanzeni": "Gentle touch MEC-4 three-state channel (N5, Sanzeni et al. 2019)",
    "sens_awc_usuyama": "AWC olfactory transduction ODE (N5, Usuyama et al. 2012)",
    "sens_o2_tuning": "URX O2 tuning curve (N5)",
    "proprio_wen2012": "Proprioceptive coupling between body segments (N5, Wen et al. 2012)",
    "slow_signalling": "Slow intracellular signalling that carries state (N6)",
    "homeostasis": "Activity-dependent channel density homeostasis (N7)",
    "deb": "Standard DEB energy budget, AmP C. elegans entry (O7)",
    "env_fields": "Plate fields: O2 (Demir et al. 2020), salt, temperature, touch and tap (O9)",
    "gcamp_variants": "GCaMP variant kinetics and NeuroPAL identification (O10)",
    "stp": "Short-term synaptic depression (N2, Tsodyks-Markram form)",
    "learning": "Shared slow associative state for the learning paradigms (N3)",
    "q10": "Temperature dependence per process class (N8)",
    "noise": "Release and channel noise (N9)",
    "ion_pumps": "Na/K-ATPase and ion concentration homeostasis (PLAN row 27)",
    "sleep_ris_ala": "RIS and ALA sleep neurons (N10)",
}

SLOTS: list[dict] = []


def S(pid, row, mech, unit, tmpl=None, lo=None, hi=None, label="guessed", *, grain="global", applies="whole worm",
      n=1, basis=None, src="", url="", quote="", proj=None, notes="", match="", used="slot only"):
    if tmpl is None and label != "absent" and lo is not None and hi is not None:
        tmpl = math.sqrt(lo * hi) if lo > 0 and hi / lo >= 10 else (lo + hi) / 2
        notes = (notes + "; " if notes else "") + "template is the range's " + (
            "log-midpoint" if lo > 0 and hi / lo >= 10 else "midpoint") + " (no published value)"
    if basis is None:
        basis = "guessed" if label in ("guessed", "absent") else "measured_related"
    SLOTS.append(dict(
        param_id=pid, plan_row=row, mechanism_id=mech, mechanism_name=MECH_NAMES[mech], grain=grain,
        applies_to=applies, n_values=n, unit=unit, value_template="" if tmpl is None else tmpl,
        bio_min="" if lo is None else lo, bio_max="" if hi is None else hi, label=label,
        bound_basis="" if lo is None else basis, source=src, source_url=url, source_quote=quote,
        source_project=proj or ("none" if label == "absent" else "ours" if label == "guessed" else "literature"),
        notes=notes, match=match, used=used))


# --- row 1: cell inventory (structure counts) -------------------------------------------------------------------------
COOK = "https://www.nature.com/articles/s41586-019-1352-7"
S("cells_neurons", 1, "cells", "count", 302, 302, 302, "measured", grain="global", basis="measured_this_class",
  src="Cook et al. 2019 Nature 571:63 node list (cook2019/)", url=COOK, used="yes",
  quote=f"{PLAN} row 1: 460 nodes in the hermaphrodite graph (302 neurons, 132 muscles, 26 end organs; Cook 2019, "
        "quoted in SotA s2)", notes="the brain builds these 302 cells")
S("cells_bwm", 1, "cells", "count", 95, 95, 95, "measured", basis="measured_this_class",
  src="WormAtlas somatic muscle; BODY.md s1",
  url="https://www.wormatlas.org/hermaphrodite/musclesomatic/MusSomaticframeset.html", used="yes",
  quote=f"{ORGANS} O1: all 95 body-wall muscle cells (4 quadrants: DL, DR, VR 24 each, VL 23",
  notes="the brain builds these 95 muscles (BWM_NAMES)")
S("cells_glia", 1, "cells", "count", 56, 56, 56, "measured", basis="measured_this_class",
  src="STATE_OF_THE_ART count, via PORT_SOURCES_ORGANS.md O5",
  quote=f"{ORGANS} O5: other 44 of the 56 total glia (per STATE_OF_THE_ART's count)")
S("cells_pharyngeal_neurons", 1, "cells", "count", 20, 20, 20, "measured", basis="measured_this_class",
  src="WormAtlas pharynx, via PORT_SOURCES_ORGANS.md O2", quote=f"{ORGANS} O2: the 20 pharyngeal neurons")
S("cells_intestine", 1, "cells", "count", 20, 20, 20, "measured", basis="measured_this_class",
  src="Cook 2019 node list cross-check, via PORT_SOURCES_ORGANS.md O3", url=COOK,
  quote=f"{ORGANS} O3: Intestinal cell count in the oscillator | 20")
S("cells_coelomocytes", 1, "cells", "count", 6, 6, 6, "measured", basis="measured_this_class",
  src="multiple sources, via PORT_SOURCES_ORGANS.md O6", quote=f"{ORGANS} O6: Coelomocyte count | 6")
S("cells_seam", 1, "cells", "count", 16, 16, 16, "measured", basis="measured_this_class",
  src="WormAtlas, via PORT_SOURCES_ORGANS.md O6", quote=f"{ORGANS} O6: 16 seam cells, 1 excretory canal cell")

# --- row 3: channel presence ------------------------------------------------------------------------------------------
S("cengen_threshold", 3, "expression_map", "CeNGEN threshold level (1-4)", 2, 1, 4, "inferred",
  basis="physical_limit", src="Taylor et al. 2021 Cell (CeNGEN) thresholds 1-4; the choice of 2 is ours",
  url="https://doi.org/10.1016/j.cell.2021.06.023", used="yes",
  quote=f"{PLAN} row 3: which threshold maps to a functional channel is **inferred** (tonight: threshold 2; "
        "DECISION NEEDED 5)", notes="applied when the ledger is built (channel presence, innexin and receptor "
        "tables); a worm draw does not re-threshold. Range = CeNGEN's four levels")

# --- row 7: receptor classes (N1 table) -------------------------------------------------------------------------------
N1 = f"{NEURAL} N1"
CL_REV = (-80, -30)          # guessed chloride reversal (RANGE_ENDS_LIT item 4: no native E_Cl measured)
CAT_REV = (-10, 20)
RC = [  # key, name, ligand-gated ion, row prefix in the N1 table (for quotes)
    ("lachr", "levamisole-type nAChR (UNC-29/UNC-38/UNC-63/LEV-8)", "cation",
     "| Levamisole-type nAChR (L-AChR) | UNC-29/UNC-38/UNC-63/LEV-8(+LEV-1 in some combos) | ACh |"),
    ("acr16", "ACR-16 homomeric nAChR (N-AChR)", "cation", "| ACR-16 homomeric nAChR (N-AChR) |"),
    ("acc", "ACC-type ACh-gated chloride channel (ACC-1 to ACC-4, LGC-46)", "anion", "| ACC-type ACh-gated Cl |"),
    ("glr1", "GLR-1/GLR-2 AMPA-like glutamate receptor", "cation", "| GLR-1/GLR-2 AMPA-like |"),
    ("nmr1", "NMR-1/NMR-2 NMDA-like glutamate receptor", "cation", "| NMR-1/NMR-2 NMDA-like |"),
    ("glucl", "glutamate-gated chloride channels (AVR-14, AVR-15, GLC-1/2/3)", "anion",
     "| GluCl (glutamate-gated Cl): AVR-14, AVR-15, GLC-1/2/3 |"),
    ("unc49b", "UNC-49B homomeric GABA-A receptor", "anion", "| UNC-49 GABA-A |"),
    ("unc49bc", "UNC-49B/C heteromeric GABA-A receptor", "anion", "| UNC-49 GABA-A |"),
    ("lgc35", "LGC-35", "anion", "| LGC-35 |"),
    ("mod1", "MOD-1 serotonin-gated chloride channel", "anion", "| MOD-1 serotonin-gated Cl |"),
    ("exp1", "EXP-1 GABA-gated cation channel", "cation", "| EXP-1 GABA-gated cation (excitatory) |"),
]
# measured or inferred entries: (key, param) -> (template, lo, hi, label, quote text after the class prefix, notes)
RCV = {
    ("lachr", "ec50"): (26, 26, 26, "measured", "26 uM", "Boulin 2008 (oocyte), via the Cys-loop review"),
    ("lachr", "pS"): (32.5, 30, 35, "measured", "30-35 pS", "Rayes 2007 / Hernando 2012 via the review; template "
                      "is the midpoint of the two"),
    ("lachr", "erev"): (11, 11, 11, "measured", "+11 mV (native muscle, Richmond & Jorgensen 1999)", ""),
    ("acr16", "ec50"): (55, 55, 55, "measured", "55 uM", "oocyte, needs RIC-3"),
    ("acr16", "erev"): (11, 11, 11, "inferred", "+11 mV (shared ACh reversal, non-selective cation channel; not "
                        "separately measured for ACR-16 alone)", "by channel class"),
    ("glr1", "erev"): (-7.0, -10.2, -3.8, "measured", "-7.0+-3.2 mV (native, AVA, Lindsay 2011)", "range = mean "
                       "+- the reported error; Lindsay, Thiele & Lockery 2011"),
    ("nmr1", "erev"): (0, -10, 10, "inferred", "by homology to glutamate reversal, near 0 mV", "range guessed"),
    ("unc49b", "ec50"): (8.6, 8.6, 43, "measured", "8.6 uM (B homomer, Bamber 2005) or 43 uM (Table 1, different "
                         "prep)", "two sources disagree; template Bamber 2005, range spans both"),
    ("unc49bc", "ec50"): (19.6, 19.6, 107, "measured", "19.6 uM (B/C, Bamber 2005) or 107 uM (Table 1)",
                          "two sources disagree; template Bamber 2005, range spans both"),
    ("unc49b", "hill"): (2.0, 2.0, 2.0, "measured", "2.0 (B homomer, Bamber 2005); 1.3 (B/C)", ""),
    ("unc49bc", "hill"): (1.3, 1.3, 1.3, "measured", "2.0 (B homomer, Bamber 2005); 1.3 (B/C)", ""),
    ("unc49b", "pS"): (37, 37, 37, "measured", "37 pS (B homomer); ~30 pS (B/C, 20% less than B)", ""),
    ("unc49bc", "pS"): (30, 30, 30, "measured", "37 pS (B homomer); ~30 pS (B/C, 20% less than B)", ""),
    ("unc49b", "decay"): (206, 180, 232, "measured", "slow component 206+-26 ms (B homomer)", "range = mean +- "
                          "the reported error; HEK cells (Bamber 2005)"),
    ("unc49bc", "decay"): (149, 139, 159, "measured", "149+-10 ms (B/C, p<0.05)", "range = mean +- the reported error; HEK cells"),
    ("mod1", "ec50"): (1, 1, 1, "measured", "| serotonin | 1 uM; tryptamine 47 uM |", "oocyte (Rodriguez Araujo "
                       "et al. 2022 via the review)"),
}
RC_SRC = {("lachr", "erev"): "Richmond & Jorgensen 1999 (native muscle), via PORT_SOURCES_NEURAL.md N1",
          ("glr1", "erev"): "Lindsay, Thiele & Lockery 2011 (native AVA), via PORT_SOURCES_NEURAL.md N1",
          ("nmr1", "erev"): "by homology to glutamate reversal (PORT_SOURCES_NEURAL.md N1)"}
RC_GUESS = {  # param -> (unit, lo, hi, note)
    "ec50": ("uM", 1, 10000, "the N1 table's measured EC50s span 1 uM (MOD-1) to 10000 uM (AVR-14B)"),
    "hill": ("1", 1, 3, "measured Hill coefficients in N1: 1.3 and 2.0 (UNC-49)"),
    "pS": ("pS", 5, 50, "measured unitary conductances in N1: 26-37 pS"),
    "decay": ("ms", 1, 1000, "current decay or desensitization time constant"),
}
for key, name, ion, prefix in RC:
    for par, unit in (("ec50", "uM"), ("hill", "1"), ("pS", "pS"), ("decay", "ms"), ("erev", "mV")):
        if key == "glucl" and par == "ec50":
            continue                                   # per subtype, below
        pid = f"rc_{par}__{key}"
        if (key, par) in RCV:
            t, lo, hi, lab, qt, nt = RCV[(key, par)]
            q = f"{N1}: {prefix} ... {qt}"
            S(pid, 7, "receptor_classes", unit, t, lo, hi, lab, grain="family", applies=name,
              basis="measured_this_class" if lab == "measured" else "guessed", src=RC_SRC.get((key, par),
              "PMC10480131 (Cys-loop review) Table 1 and the papers it cites, via PORT_SOURCES_NEURAL.md N1"), url=PMC("PMC3935721") if key == "glr1" else CYS_REVIEW,
              quote=q, notes=nt, match="receptor_classes")
        else:
            if par == "erev":
                lo, hi = CL_REV if ion == "anion" else CAT_REV
                nt = ("chloride-selective; no native E_Cl measured in the worm (RANGE_ENDS_LIT.md item 4)"
                      if ion == "anion" else "cation-selective by class; no point value")
            else:
                _, lo, hi, nt = RC_GUESS[par]
            S(pid, 7, "receptor_classes", unit, None, lo, hi, "guessed", grain="family", applies=name,
              src="guessed; the N1 table has no value for this class", url=CYS_REVIEW,
              quote=f"{N1}: {prefix}", notes=nt + "; would be pinned by heterologous recordings of this class "
              "(e.g. Putrenko 2005 for ACC, Beg & Jorgensen 2003 for EXP-1, Brockie 2001 for NMR-1)",
              match="receptor_classes")
GLUCL = [("avr14b", "AVR-14B", 10000), ("avr15a", "AVR-15A", 2000), ("avr15b", "AVR-15B", 208),
         ("avr15b_glc2", "AVR-15B/GLC-2", 62), ("glc2", "GLC-2", 380), ("glc1_glc2", "GLC-1/GLC-2", 1360),
         ("glc3", "GLC-3", 1900)]
for k, nm, v in GLUCL:
    S(f"rc_ec50__{k}", 7, "receptor_classes", "uM", v, v, v, "measured", grain="family",
      applies=f"glutamate-gated chloride channel {nm} (glutamate)", basis="measured_this_class",
      src="PMC10480131 Table 1 (oocyte), via PORT_SOURCES_NEURAL.md N1", url=CYS_REVIEW,
      quote=f"{N1}: {nm} {v} uM (glu)" if k != "glc2" else f"{N1}: GLC-2 380 uM (glu)",
      notes="heterologous (oocyte) EC50 for glutamate", match="receptor_classes")
S("rel_gain_afd_aiy", 7, "graded_release", "mV/mV", 0.056, 0.056, 0.056, "measured", grain="connection",
  applies="AFD -> AIY", basis="measured_this_class", src="Narayan et al. 2011 PNAS, Fig. 4B", url=PMC("PMC3111291"),
  quote=f"{N1}: 0.056 mV postsynaptic per mV presynaptic (linear, R^2=0.69)", match="graded_release")
S("nmj_quantal_g_nS", 7, "graded_release", "nS", 0.19, 0.183, 0.203, "derived", grain="connection",
  applies="cholinergic motor neuron -> body-wall muscle", basis="measured_this_class",
  src="Liu, Hollopeter & Jorgensen 2009 Fig. 3E (17.6+-0.9 pA) / 91 mV driving force (Richmond & Jorgensen 1999)",
  url=PMC("PMC2705609"), quote=f"{N1}: ~0.19 nS (derived: 17.6+-0.9 pA mEPSC / 91 mV driving force)",
  notes="range from the mEPSC error only", match="graded_release")

# --- row 8: per innexin -----------------------------------------------------------------------------------------------
S("gap_unitary_per_innexin_pS", 8, "gap_per_innexin", "pS", None, 50, 300, "guessed", grain="gene",
  applies="each innexin gene expressed in neurons", n=25, src="range C1 (param_ranges.csv); no per-innexin value",
  quote=f"{PLAN} row 8: Gap junctions per innexin", notes="today one shared value (gap_innexin_unitary); n = 25 "
  "innexin genes (unc-7, unc-9, eat-5, inx-*; count from the CeNGEN gene list, check); would be pinned by "
  "per-innexin single-channel recordings (none found)", match="gap_per_innexin")

# --- row 9 and 10: peptide cascade, monoamine uptake (N4) -------------------------------------------------------------
N4 = f"{NEURAL} N4"
for fam, gn in (("gq", "EGL-30/Gq"), ("gio", "GOA-1/Go-i"), ("gs", "GSA-1/Gs")):
    S(f"pep_cascade_tau_s__{fam}", 9, "peptide_cascade", "s", None, 0.1, 10, "guessed", grain="family",
      applies=f"every receptor coupled to {gn} (peptide and monoamine GPCRs)", src="NEUROPEPTIDES.md homology "
      "bounds, via PORT_SOURCES_NEURAL.md N4", quote=f"{N4}: 100 ms to several seconds for Gq/Gi/Gs cascades "
      "generically", notes="one tau per receptor family, not per pair; upper end 'several seconds' taken as 10 s; "
      "shared by rows 9, 10 and 28", match="peptide_cascade")
S("pep_diffusion_um2_s", 9, "peptide_cascade", "um2/s", None, 10, 400, "guessed", src="none: no measured value",
  quote=f"{N4}: no measured in-vivo diffusion coefficient or degradation half-life for any named C. elegans "
        "peptide", notes="bounds guessed (small peptide in free solution to tortuous tissue)", match="peptide_cascade")
for k, gn in (("mod5", "MOD-5 (SERT), serotonin"), ("dat1", "DAT-1, dopamine")):
    S(f"ma_uptake_km_uM__{k}", 10, "monoamine_uptake", "uM", None, 0.05, 5, "guessed", grain="gene", applies=gn,
      src="none: no worm Km", quote=f"{N4}: Monoamine reuptake (MOD-5 SERT, DAT-1 DAT): gene identity and "
      "phenotype are measured (NEUROPEPTIDES.md section 1), but no Km/Vmax point value was retrieved",
      notes="bounds guessed around mammalian transporter Km values (not checked against a source)",
      match="monoamine_uptake")
    S(f"ma_uptake_vmax_uM_s__{k}", 10, "monoamine_uptake", "uM/s", None, 0.01, 10, "guessed", grain="gene",
      applies=gn, src="none: no worm Vmax", quote=f"{N4}: no Km/Vmax point value was retrieved in either this pass "
      "or the prior one", notes="bounds guessed; today's lumped ma_clear_tau_s stands in", match="monoamine_uptake")

# --- row 11: glia (O5) ------------------------------------------------------------------------------------------------
O5 = f"{ORGANS} O5"
S("glia_k_clear_tau_s", 11, "glia_clearance", "s", 2.1, 0.3, 6.3, "inferred", grain="class",
  applies="AMsh, CEPsh, GLR", basis="measured_related", src="mammalian Kir4.1 astrocyte literature (PLoS Comp Biol 2015 and others), via O5",
  quote=f"{O5}: | Astrocyte K+ clearance tau (cross-species fallback) | 0.7-6.3 | 0.3-6.3 | s |",
  notes="cross-species; template = log-midpoint of 0.7-6.3", match="glia_clearance")
S("glia_kcc3_cl_tau_s", 11, "glia_clearance", "s", None, 1, 100, "guessed", grain="class", applies="AMsh around AFD",
  src="none: Singhvi 2016 gives the mechanism only", quote=f"{O5}: | KCC-3 Cl- clearance time constant (worm) | "
  "not found |", match="glia_clearance")
S("glia_glr_rme_gap_nS", 11, "glia_clearance", "nS", None, 0.01, 1, "guessed", grain="connection",
  applies="GLR -> RME gap junctions", src="none: eLife PMC5083064 gives the mechanism only", url=PMC("PMC5083064"),
  quote=f"{O5}: | GLR-RME gap junction conductance | not found |", notes="bounds guessed near the neuron gap range",
  match="glia_clearance")

# --- row 12: body-wall muscle (O1) ------------------------------------------------------------------------------------
O1 = f"{ORGANS} O1"
S("bwm_slo2_alpha", 12, "muscle_du2025", "1/(ms mM^2)", 58, 29, 116, "published_fit", grain="class",
  applies="body-wall muscle", basis="guessed", src="Du/Crodelle 2025 seven-state muscle model", url=PMC("PMC11781704"),
  quote=f"{O1}: | SLO-2 Ca-binding alpha | 58 | - | ms^-1 mM^-2 | Du/Crodelle 2025 (PMC11781704) | published fit |",
  notes="range guessed (x/2 to x2)", match="muscle_du2025")
S("bwm_slo2_beta", 12, "muscle_du2025", "1/ms", 0.09, 0.045, 0.18, "published_fit", grain="class",
  applies="body-wall muscle", basis="guessed", src="Du/Crodelle 2025", url=PMC("PMC11781704"),
  quote=f"{O1}: | SLO-2 Ca-binding beta | 0.09 | - | ms^-1 |", notes="range guessed (x/2 to x2)",
  match="muscle_du2025")

# --- row 13: pharynx (O2) ---------------------------------------------------------------------------------------------
O2 = f"{ORGANS} O2"
for pid, unit, lo, hi, nt in (
        ("phar_fhn_eps", "1", 0.01, 0.5, "FitzHugh-Nagumo time-scale ratio"),
        ("phar_fhn_a", "1", 0.5, 1.0, "FitzHugh-Nagumo recovery offset"),
        ("phar_fhn_b", "1", 0.5, 1.0, "FitzHugh-Nagumo recovery slope"),
        ("phar_eat2_gain", "1", 0.1, 10, "MC -> pharyngeal muscle (EAT-2 nAChR) drive, relative"),
        ("phar_avr15_gain", "1", 0.1, 10, "M3 -> pharyngeal muscle (AVR-15 GluCl) termination, relative")):
    S(pid, 13, "pharynx_fhn", unit, None, lo, hi, "guessed", grain="class", applies="pharyngeal muscle and neurons",
      src="none read: the PNAS 2024 FHN pharynx model (search snippet only) would pin it",
      quote=f"{O2}: | FitzHugh-Nagumo pharyngeal cell count | 29 | - | cells | PNAS 2024 (search-snippet only) |",
      notes=nt, match="pharynx_fhn")

# --- row 14: intestine (O3) -------------------------------------------------------------------------------------------
O3 = f"{ORGANS} O3"
for pid, unit, lo, hi, nt in (
        ("int_ip3r_d1_uM", "uM", 0.01, 1, "IP3 dissociation constant"),
        ("int_ip3r_d5_uM", "uM", 0.01, 1, "Ca activation dissociation constant"),
        ("int_ip3r_a2", "1/(uM s)", 0.02, 2, "Ca inactivation binding rate"),
        ("int_ip3r_v1_per_s", "1/s", 0.5, 50, "maximal IP3R flux rate"),
        ("int_serca_v3_uM_s", "uM/s", 0.1, 10, "maximal SERCA uptake"),
        ("int_serca_k3_uM", "uM", 0.01, 1, "SERCA half-activation")):
    S(pid, 14, "intestine_ip3", unit, None, lo, hi, "guessed", grain="class", applies="intestinal cells (20)",
      src="none: Teramoto & Iwasaki 2006 would pin the worm's ITR-1; a generic Li-Rinzel set is the placeholder",
      quote=f"{O3}: use generic de Young-Keizer/Li-Rinzel values as a bounded placeholder, labelled guessed",
      notes=nt, match="intestine_ip3")
S("int_inx16_gap_nS", 14, "intestine_ip3", "nS", None, 0.1, 10, "guessed", grain="connection",
  applies="intestine-intestine (INX-16)", src="none: Peters et al. 2007 (PDF unreadable)",
  quote=f"{O3}: | INX-16 gap conductance | UNVERIFIED | - | nS | Peters et al. 2007 (PDF unreadable) |",
  match="intestine_ip3")
S("int_pbo_proton_dph", 14, "intestine_ip3", "pH units", None, 0.1, 1.5, "guessed", grain="class",
  applies="intestine -> posterior body-wall muscle (PBO-4/PBO-5)", src="none: Beg et al. 2008 not opened in full",
  quote=f"{O3}: | PBO-4/PBO-5 proton signal amplitude/pH | UNVERIFIED |", match="intestine_ip3")
S("int_nlp40_ca_threshold_uM", 14, "intestine_ip3", "uM", None, 0.1, 2, "guessed", grain="class",
  applies="intestine -> AVL/DVB (NLP-40)", src="none: qualitative only",
  quote=f"{O3}: | NLP-40 release threshold | UNVERIFIED |", match="intestine_ip3")

# --- row 15: egg-laying (O4) ------------------------------------------------------------------------------------------
O4 = f"{ORGANS} O4"
COLLINS = "https://doi.org/10.7554/eLife.21126"
S("egg_hsn_isi_active_s", 15, "egg_circuit", "s", 17, 15, 19, "measured", grain="class", applies="HSN",
  basis="measured_this_class", src="Collins et al. 2016 eLife 5:e21126", url=COLLINS,
  quote=f"{O4}: | HSN inter-transient interval, active state | 17 | +/- 2 (SEM) | s | Collins et al. 2016 |",
  notes="range = mean +- SEM", match="egg_circuit")
S("egg_hsn_isi_inactive_s", 15, "egg_circuit", "s", 41, 36, 46, "measured", grain="class", applies="HSN",
  basis="measured_this_class", src="Collins et al. 2016", url=COLLINS,
  quote=f"{O4}: | HSN inter-transient interval, inactive state | 41 | +/- 5 (SEM) | s |",
  notes="range = mean +- SEM", match="egg_circuit")
S("egg_vc_isi_s", 15, "egg_circuit", "s", 10, 10, 10, "measured", grain="class", applies="VC1-VC6",
  basis="measured_this_class", src="Collins et al. 2016", url=COLLINS,
  quote=f"{O4}: | VC inter-transient interval | ~10 | - | s |", match="egg_circuit")
for pid, nt in (("egg_vm_unc103_g_S_cm2", "UNC-103 (ERG K) density in vulval muscle"),
                ("egg_vm_egl19_g_S_cm2", "EGL-19 (CaV1) density in vulval muscle")):
    S(pid, 15, "egg_circuit", "S/cm2", None, 1e-5, 1e-2, "guessed", grain="class", applies="vm1, vm2",
      src="none: Collins & Koelle 2013 not opened in full",
      quote=f"{O4}: | UNC-103/EGL-19 channel conductances | UNVERIFIED |", notes=nt, match="egg_circuit")
S("egg_tyr_feedback_gain", 15, "egg_circuit", "1", None, 0, 1, "guessed", grain="connection",
  applies="uv1 tyramine -> HSN (LGC-55)", basis="guessed", src="none: qualitative only",
  quote=f"{O4}: | Tyramine/LGC-55 feedback strength | UNVERIFIED |", notes="fraction of HSN drive removed",
  match="egg_circuit")

# --- row 16: other non-neural cells (O6) ------------------------------------------------------------------------------
O6 = f"{ORGANS} O6"
S("hyp_gap_nS", 16, "other_cells", "nS", None, 0.05, 1, "guessed", grain="connection",
  applies="hypodermis/seam to muscle or neuron", src="none found; bound by row 8's neuron-neuron range",
  quote=f"{O6}: | Hyp/seam-to-muscle/neuron gap conductance | not found | bound by row 8's neuron-neuron UNC-9 range |",
  notes="bounds = gap_strength_per_pair's range", match="hyp_gap")
S("exc_aqp8_permeability_um_s", 16, "other_cells", "um/s", None, 1, 100, "guessed", grain="cell",
  applies="excretory canal cell", src="none: mechanism only",
  quote=f"{O6}: | Excretory canal AQP-8 water permeability | not found |", match="excretory")
S("exc_volume_tau_s", 16, "other_cells", "s", None, 10, 1000, "guessed", grain="cell", applies="excretory canal cell",
  src="none found", quote=f"{O6}: | Excretory canal volume/pressure time constant | not found |", match="excretory")
S("coel_uptake_tau_min", 16, "other_cells", "min", None, 1, 30, "guessed", grain="class", applies="6 coelomocytes",
  src="none: Fares & Greenwald 2001 assay is qualitative",
  quote=f"{O6}: a bounded guess of minutes-to-tens-of-minutes turnover is reasonable", match="coelomocyte")

# --- row 17: senses (N5) ----------------------------------------------------------------------------------------------
N5 = f"{NEURAL} N5"
for pid, nt in (("awa_egl19_g_S_cm2", "EGL-19 density in AWA"), ("awa_shk1_g_S_cm2", "SHK-1 density in AWA")):
    S(pid, 17, "sens_awa_spike", "S/cm2", None, 1e-5, 1e-2, "guessed", grain="class", applies="AWA",
      src="fit target: Liu et al. 2018 bioRxiv 359935 Fig 2 (spike threshold, amplitude, width) is the check",
      url="https://www.biorxiv.org/content/10.1101/359935v1",
      quote=f"{N5}: **no new channel-kinetics porting is needed, only the AWA-specific density/threshold fit**",
      notes=nt + "; fit to spike threshold -34.0+-0.6 mV, amplitude 25.8+-0.8 mV, half width 18.0+-0.8 ms "
      "(measured, same paper)", match="sens_awa_spike")
S("mec4_i0_pA", 17, "sens_touch_sanzeni", "pA", -1.6, -1.8, -1.4, "measured", grain="class",
  applies="ALM, AVM, PLM, PVM (MEC-4)", basis="measured_this_class",
  src="O'Hagan et al. 2005 and Brown et al. 2008, cited by Sanzeni et al. 2019 eLife 8:e43226",
  url="https://doi.org/10.7554/eLife.43226", quote=f"{N5}: single-channel current `i0 = -1.6 +- 0.2 pA`",
  notes="range = mean +- the reported error", match="sens_touch_sanzeni")
for pid, unit in (("mec4_g0", "1"), ("mec4_g1", "1/uN"), ("mec4_tau_ms", "ms")):
    S(pid, 17, "sens_touch_sanzeni", unit, label="absent", grain="class", applies="ALM, AVM, PLM, PVM",
      src="Sanzeni et al. 2019 eLife (free) fitted constants: not extracted", url="https://doi.org/10.7554/eLife.43226",
      quote=f"{N5}: `g0`, `g1`, `a`, `tau` not extracted to numeric values in this pass",
      notes="published; read the paper to fill", match="sens_touch_sanzeni")
S("mec4_a", 17, "sens_touch_sanzeni", "1", None, 0, 1, "guessed", grain="class", applies="ALM, AVM, PLM, PVM",
  basis="physical_limit", src="Sanzeni et al. 2019 (0<=a<=1 by definition); fitted value not extracted",
  url="https://doi.org/10.7554/eLife.43226", quote=f"{N5}: `dG_sc = (1-a)*dG_oc`, 0<=a<=1",
  match="sens_touch_sanzeni")
S("awc_usuyama_params", 17, "sens_awc_usuyama", "mixed", label="absent", grain="class", applies="AWC",
  src="Usuyama et al. 2012 PLOS ONE ODE model (free): not read", quote=f"{N5}: Usuyama 2012",
  notes="placeholder for the ODE's parameter set; count unknown until read", match="sens_awc_usuyama")
S("urx_o2_half_pct", 17, "sens_o2_tuning", "% O2", 16.5, 15, 19, "derived", grain="class", applies="URX, AQR, PQR",
  basis="measured_this_class", src="Ca imaging tuning curve described in N5 (the paper is not named there; Zimmer et al. 2009 Neuron would be the one to check)",
  quote=f"{N5}: a sharp increase between 15-19% O2, approaching saturation near 21% O2",
  notes="half-max read from the described curve (~16-17%); Hill coefficient not retrieved", match="sens_o2_tuning")
S("proprio_gain_wen", 17, "proprio_wen2012", "1", 0.62, 0.59, 0.65, "measured", grain="global",
  applies="B-type motor neurons (curvature to curvature)", basis="measured_this_class",
  src="Wen et al. 2012 Neuron, via RHYTHM_LIT.md s1", quote=f"{N5}: curvature-to-curvature gain 0.62+-0.03",
  notes="range = mean +- the reported error", match="proprio_wen2012")
S("proprio_delay_ms", 17, "proprio_wen2012", "ms", 300, 300, 1000, "measured", grain="global",
  applies="B-type motor neurons", basis="measured_this_class", src="Wen et al. 2012 Neuron",
  quote=f"{N5}: propagation delay ~300 ms at low viscosity rising to ~1 s at 300 mPa.s",
  notes="range spans the viscosity series", match="proprio_wen2012")

# --- row 18: slow signalling (N6) -------------------------------------------------------------------------------------
N6 = f"{NEURAL} N6"
S("slow_cmk1_fast_tau_min", 18, "slow_signalling", "min", 2.5, 2, 3, "measured", grain="class", applies="AFD",
  basis="measured_this_class", src="Yu et al. 2014 Neuron (doi 10.1016/j.neuron.2014.10.046), via N6",
  url="https://doi.org/10.1016/j.neuron.2014.10.046",
  quote=f"{N6}: Two explicit timescales in the same cell: **2-3 min** (fast, short-term threshold reset)",
  notes="the slow 3-5 h component is slow_thermo_tau_h", match="slow_cmk1_fast")
for pid, nm in (("slow_insulin_tau_h", "insulin/DAF-16"), ("slow_daf7_tau_h", "DAF-7 TGF-beta"),
                ("slow_crh1_tau_h", "CRH-1/CREB"), ("slow_glr1_traffic_tau_h", "GLR-1 trafficking (CMK-1)")):
    S(pid, 18, "slow_signalling", "h", None, 0.01, 24, "guessed", grain="class", applies=nm,
      src="none: not retrieved; K1 class bound", quote=f"{N6}: otherwise bounded generically in the K1 cost class "
      "PLAN.md row 18 already assigns (~1 s to hours", notes="bounds guessed (36 s to a day)", match=pid)

# --- row 19: homeostasis (N7) -----------------------------------------------------------------------------------------
N7 = f"{NEURAL} N7"
S("homeo_unc2_per_synapse", 19, "homeostasis", "channels", 100, 100, 100, "measured", grain="synapse",
  applies="UNC-2-expressing presynaptic terminals", basis="measured_this_class",
  src="PNAS 2024 121(35):e2404969121", url=PMC("PMC11363341"),
  quote=f"{N7}: | Baseline UNC-2 channels per synapse | ~100 (considerable synapse-to-synapse variation) |",
  match="homeo_unc2")
S("homeo_unc2_tau_h", 19, "homeostasis", "h", 1.5, 1, 2, "derived", grain="global",
  applies="UNC-2-expressing presynaptic terminals", basis="measured_this_class", src="derived in N7 from PMC11363341 "
  "(1 h no change, >2 h decrease)", url=PMC("PMC11363341"),
  quote=f"{N7}: bounds tau between roughly 1-2 h, derived from the reported threshold", match="homeo_unc2")
for pid, unit, lo, hi, nt in (("homeo_ca_sensor_fast_tau_s", "s", 0.01, 1, "fast Ca sensor filter"),
                              ("homeo_ca_sensor_slow_tau_s", "s", 10, 1000, "slow Ca sensor filter"),
                              ("homeo_density_rate_per_s", "1/s", 1e-6, 1e-2, "density regulation gain k_i")):
    S(pid, 19, "homeostasis", unit, None, lo, hi, "guessed", grain="global", applies="every regulated channel",
      src="O'Leary et al. 2013 PNAS (stomatogastric, not worm; values not extracted)",
      url="https://neurostatslab.org/assets/papers/OLeary_etal_2013.pdf",
      quote=f"{N7}: | O'Leary 2013 calcium-sensor filter time constants, regulation gains `k_i` | not extracted",
      notes=nt, match="homeo_oleary")

# --- row 20: metabolism (O7, AmP DEB) ---------------------------------------------------------------------------------
O7 = f"{ORGANS} O7"
AMP = "http://www.bio.vu.nl/thb/deb/deblab/add_my_pet/entries_web/Caenorhabditis_elegans/"
for pid, unit, v, nm, q in (
        ("deb_v_cm_d", "cm/d", 0.03208, "energy conductance", "| v (energy conductance) | 0.03208 | cm/d |"),
        ("deb_pM_J_d_cm3", "J/(d cm3)", 3724, "volume-specific somatic maintenance", "| p_M (volume-specific somatic "
         "maintenance) | 3724 | J/(d*cm^3) |"),
        ("deb_kJ_per_d", "1/d", 0.002, "maturity maintenance rate", "| k_J (maturity maintenance rate coefficient) | "
         "0.002 | 1/d |"),
        ("deb_kappa", "1", 0.5056, "allocation fraction to soma", "| kappa (allocation fraction to soma) | 0.5056 |"),
        ("deb_kappa_G", "1", 0.8086, "growth efficiency", "| kappa_G (growth efficiency) | 0.8086 |"),
        ("deb_kappa_R", "1", 0.95, "reproduction efficiency", "| kappa_R (reproduction efficiency) | 0.95 |")):
    lo, hi = (v / 2, v * 2) if unit != "1" else (max(v - 0.2, 0.0), min(v + 0.2, 1.0))
    S(pid, 20, "deb", unit, v, lo, hi, "published_fit", grain="global", applies="whole animal (at 20 C)",
      basis="guessed", src="Add-my-Pet C. elegans entry (DEB abj model fit)", url=AMP, quote=f"{O7}: {q}",
      notes=nm + "; range guessed (fits carry no range here)", match="deb")

# --- row 22: environment (O9) -----------------------------------------------------------------------------------------
O9 = f"{ORGANS} O9"
DEMIR = "https://doi.org/10.7554/eLife.52781"
for pid, unit, v, lab, src, url, q in (
        ("env_o2_diffusion_cm2_s", "cm2/s", 2e-5, "measured", "Demir et al. 2020 eLife", DEMIR,
         "| O2 diffusion coefficient (agar/plate) | 2e-5 | - | cm^2/s | Demir et al. 2020 eLife |"),
        ("env_o2_penetration_per_s", "1/s", 0.65, "published_fit", "Demir et al. 2020 eLife", DEMIR,
         "| O2 penetration rate (air to agar) | 0.65 | - | 1/s | Demir et al. 2020 | fitted |"),
        ("env_o2_consumption", "1/s per unit density", 7.3e-10, "published_fit", "Demir et al. 2020 eLife", DEMIR,
         "| O2 consumption rate coefficient (per worm/bacteria density) | 7.3e-10 |"),
        ("env_nacl_diffusion_cm2_s", "cm2/s", 1.5e-5, "measured", "standard chemotaxis-assay value (attribution "
         "unverified)", "", "| NaCl diffusion coefficient | 1.5e-5 | - | cm^2/s |"),
        ("env_thermo_gradient_C_cm", "C/cm", 0.5, "measured", "thermotaxis assay literature (assay setting)", "",
         "| Linear thermotaxis gradient | 0.5 | - | C/cm |"),
        ("env_touch_saturation_uN", "uN", 2, "measured", "Krieg/Pruitt PLOS ONE 2017",
         "https://doi.org/10.1371/journal.pone.0178080", "| Gentle-touch behavioural saturation force | 2 | - | uN |"),
        ("env_tap_force_N", "N", 1.5, "measured", "tap-withdrawal methods literature", "", "| Tap force | 1-2 | - | N |")):
    lo, hi = (1, 2) if pid == "env_tap_force_N" else (v / 2, v * 2) if lab == "published_fit" else (v, v)
    S(pid, 22, "env_fields", unit, v, lo, hi, lab, grain="global", applies="plate",
      basis="guessed" if lab == "published_fit" else "measured_related", src=src, url=url, quote=f"{O9}: {q}",
      notes="range guessed (x/2 to x2)" if lab == "published_fit" else "", match="env_fields " + pid)

# --- row 23: observation (O10) ----------------------------------------------------------------------------------------
O10 = f"{ORGANS} O10"
CHEN, DANA = "https://doi.org/10.1038/nature12354", "https://doi.org/10.1038/s41592-019-0435-6"
for pid, unit, v, lo, hi, src, url, q, nt in (
        ("gcamp6f_kd_nM", "nM", 364, 364, 364, "Chen et al. 2013", CHEN, "| GCaMP6f Kd | 364 | - | nM |", ""),
        ("gcamp6f_rise_ms", "ms", 2, 2, 2, "Chen et al. 2013", CHEN, "| GCaMP6f response/rise time | 2 | - | ms |", ""),
        ("gcamp7f_half_rise_ms", "ms", 26, 24, 28, "Dana et al. 2019", DANA,
         "| GCaMP7f half-rise time (1 AP) | 26 | +/-2 | ms |", "half-rise time, not a tau"),
        ("gcamp7f_half_decay_ms", "ms", 270, 255, 285, "Dana et al. 2019", DANA,
         "| GCaMP7f half-decay time (1 AP, in vivo) | 270 | +/-15 | ms |", "half-decay time in vivo, not a tau"),
        ("neuropal_id_acc_head_pct", "%", 86, 86, 86, "NeuroPAL pipeline (attribution unverified)", "",
         "| NeuroPAL head ID accuracy | 86 | - | % |", ""),
        ("neuropal_id_acc_tail_pct", "%", 94, 94, 94, "NeuroPAL pipeline (attribution unverified)", "",
         "| NeuroPAL tail ID accuracy | 94 | - | % |", "")):
    S(pid, 23, "gcamp_variants", unit, v, lo, hi, "measured", grain="global", applies="imaging datasets",
      basis="measured_this_class", src=src, url=url, quote=f"{O10}: {q}", notes=nt, match=pid)

# --- row 24: plasticity and learning (N2, N3) -------------------------------------------------------------------------
N2, N3 = f"{NEURAL} N2", f"{NEURAL} N3"
S("stp_U", 24, "stp", "1", 0.3, 0.1, 0.5, "guessed", grain="global", applies="every chemical synapse",
  src="generic invertebrate central-synapse range; no C. elegans value",
  quote=f"{N2}: | Release fraction per event, U (Tsodyks-Markram) | not measured for any C. elegans synapse | "
        "0.1-0.5 (generic invertebrate central synapse range)", match="stp")
S("stp_tau_rec_s", 24, "stp", "s", 0.58, 0.09, 4.71, "inferred", grain="global", applies="every chemical synapse",
  basis="measured_related", src="Liu et al. 2009 NMJ depression time constants", url=PMC("PMC2705609"),
  quote=f"{N2}: | Release depression tau, mid frequency (1 Hz train) | 0.58 | +-0.11 | s |",
  notes="NMJ values transplanted to every synapse; range spans the 5 Hz and 0.2 Hz trains", match="stp")
S("learn_rate_per_s", 24, "learning", "1/s", None, 1e-4, 1e-1, "guessed", grain="global",
  applies="every learning paradigm (one shared state)", src="none: no paradigm has measured kinetics",
  quote=f"{N3}: every paradigm in this list reduces to the same minimal ... \"slow associative state\" mechanism (one "
        "state variable, one learning-rate parameter, one decay",
  notes="fit target (bounded), against held-out behaviour", match="learning")
S("learn_fast_tau_min", 24, "learning", "min", None, 1, 60, "guessed", grain="global", applies="short-term trace",
  src="Kano et al. (Curr Biol): NMDA-independent short-term memory, minutes",
  quote=f"{N3}: fast trace (minutes, NMDA-independent) + slow trace (hours, NMDA-depend", match="learning")
S("learn_slow_tau_h", 24, "learning", "h", None, 1, 24, "guessed", grain="global", applies="long-term trace (NMR-1)",
  src="Kano et al. (Curr Biol): NMDA-dependent long-term memory, hours",
  quote=f"{N3}: fast trace (minutes, NMDA-independent) + slow trace (hours, NMDA-depend", match="learning")

# --- row 25: temperature (N8) -----------------------------------------------------------------------------------------
N8 = f"{NEURAL} N8"
for pid, lo, hi, nm in (("q10_channel_kinetics", 1.5, 3, "ion channel gating rates"),
                        ("q10_synaptic_release", 2, 3, "synaptic release"), ("q10_metabolic", 2, 3, "metabolic rates"),
                        ("q10_pumping", 1.5, 3, "pharyngeal pumping"), ("q10_muscle", 1.5, 3, "muscle kinetics")):
    S(pid, 25, "q10", "1", None, lo, hi, "guessed", grain="family", applies=nm,
      src="generic ectotherm range, no C. elegans Q10 retrieved",
      quote=f"{N8}: bound each process class in the 1.5-3 range as guessed/inferred from the generic ectotherm "
            "literature", match="q10")
S("q10_defecation_clock", 25, "q10", "1", 1.0, 0.9, 1.1, "measured", grain="family", applies="defecation clock",
  basis="guessed", src="Thomas 1990 Genetics (period flat 19-30 C), via STATE_OF_THE_ART item 49",
  quote=f"{N8}: with the defecation clock's Q10~1 held as the one measured, explicit exception",
  notes="range guessed around 'flat'", match="q10")

# --- row 26: noise (N9) -----------------------------------------------------------------------------------------------
N9 = f"{NEURAL} N9"
S("noise_mini_rate_per_s", 26, "noise", "1/s", 26.3, 10.2, 35.3, "measured", grain="family",
  applies="cholinergic presynaptic terminals", basis="measured_this_class",
  src="Liu, Hollopeter & Jorgensen 2009", url=PMC("PMC2705609"),
  quote=f"{N9}: | Baseline spontaneous mEPSC (\"mini\") rate, NMJ ACh | 26.3+-5.4 events/s |",
  notes="range = hyperpolarized (10.2) to rebound (35.3) rates, same paper", match="noise")
S("noise_quantal_pA", 26, "noise", "pA", 17.6, 16.7, 18.5, "measured", grain="family",
  applies="cholinergic NMJ", basis="measured_this_class", src="Liu et al. 2009 Fig 3E", url=PMC("PMC2705609"),
  quote=f"{N9}: | Single mEPSC (quantal) amplitude | 17.6+-0.9 pA |", notes="range = mean +- the reported error", match="noise")
S("noise_quantal_cv", 26, "noise", "1", None, 0.1, 0.5, "guessed", grain="family", applies="every release site",
  src="none: per-event variance not reported",
  quote=f"{N9}: treat the per-event amplitude variance itself as a gap", match="noise")

# --- row 27: pumps (no PORT_SOURCES section) --------------------------------------------------------------------------
P27 = f"{PLAN} row 27"
for pid, unit, lo, hi, nm in (
        ("pump_nak_imax_pA_pF", "pA/pF", 0.1, 2, "Na/K-ATPase maximal current density"),
        ("pump_nak_km_nai_mM", "mM", 5, 30, "Na/K-ATPase half-activation by internal Na"),
        ("pump_nak_km_ko_mM", "mM", 0.5, 3, "Na/K-ATPase half-activation by external K"),
        ("ion_cl_in_mM", "mM", 5, 60, "internal chloride (sets E_Cl, which no worm recording has measured)"),
        ("ion_na_in_mM", "mM", 5, 30, "internal sodium"),
        ("ion_k_in_mM", "mM", 100, 160, "internal potassium")):
    S(pid, 27, "ion_pumps", unit, None, lo, hi, "guessed", grain="class", applies="every neuron and muscle class",
      src="none: no C. elegans pump or concentration measurement found; bounds generic",
      quote="", notes=nm + "; bounds guessed from generic animal cells (not checked against a source); EAT-6 is the "
      "worm's Na/K-ATPase alpha subunit", match="ion_pumps")

# --- row 28: sleep (N10) ----------------------------------------------------------------------------------------------
N10 = f"{NEURAL} N10"
S("sleep_flp11_release", 28, "sleep_ris_ala", "nM/s", None, 0.01, 10, "guessed", grain="cell", applies="RIS",
  src="none: no kinetic model found", url=PMC("PMC7617803"),
  quote=f"{N10}: No published whole-circuit quantitative model of RIS or ALA quiescence", match="sleep_ris_ala")
S("sleep_ris_autoinhib_gain", 28, "sleep_ris_ala", "1", None, 0, 1, "guessed", grain="cell", applies="RIS (DMSR-1)",
  basis="guessed", src="Turek/Chew, FLP-11 self-inhibits through DMSR-1 (qualitative)", url=PMC("PMC7617803"),
  quote=f"{N10}: the self-inhibiting RIS autoreceptor giving the one qualitative dynamical feature worth preserving",
  notes="fraction of RIS drive removed at full occupancy", match="sleep_ris_ala")
S("sleep_ala_release", 28, "sleep_ris_ala", "nM/s", None, 0.01, 10, "guessed", grain="gene", n=3,
  applies="ALA: FLP-13, FLP-24, NLP-8", src="none: release kinetics not searched",
  quote=f"{N10}: ALA's three peptides (FLP-13, FLP-24, NLP-8) have measured genetic requirement for quiescence",
  match="sleep_ris_ala")
