"""Row 7: ionotropic receptor classes with kinetics (PLAN row 7; docs/worm/research/PORT_SOURCES_NEURAL.md N1).

Every chemical synapse site gets one wsyn point process (src/wormemu/nmodl/wsyn.mod) per receptor class the
postsynaptic cell carries for the presynaptic cell's transmitter. Graded release is BAAIWorm's (the syn_exc_Vth,
delta and k rows, the same for both of its synapse types); the cleft transmitter is tmax x release fraction; each
class has its own dose-response (EC50, Hill), rise, decay, desensitization, reversal and unit conductance (SPECS,
one value per class, not per pair). No published model gives these as one ODE scheme (PORT_SOURCES N1 (b)); the
scheme is the first-order ligand-gated form in N1 (c), with the parameter table N1 (d).

Which classes a pair gets (pair_classes): the presynaptic transmitters (Wang et al. 2024 atlas, brain_structure)
x the classes whose genes the postsynaptic CeNGEN class expresses (threshold-2 TPM, Taylor et al. 2021); an
obligate heteromer ("all") counts at its least-expressed subunit, an alternative set ("any") at its most-expressed
gene. Shares of the pair's conductance are the TPM fractions (inferred: expression as a proxy for channel number,
the expression_map assumption). Polarity: where the pair's sign is measured (Roberts et al. 2016) or predicted
+ or - by Fenyves et al. 2020 (the receptor_sign values table), only classes of that polarity are kept; complex,
no prediction or receptor_sign off keeps every expressed class. A pair left with no class gets the default class
for its transmitter and sign (DEFAULT); a pair with no fast transmitter at all keeps BAAIWorm's graded synapse
(wsyn mode 0). Body-wall muscle (no CeNGEN profile): ACh onto L-AChR and ACR-16 (rec_nmj_lacr_share), GABA onto
UNC-49B/C (Bamber et al. 2005: the NMJ receptor is the B/C heteromer).

Conductance: the ledger's per-contact strength (syn_strength_per_pair / nmj_strength_per_pair, B4) is the
conductance of one contact's channels if they were all L-AChR; a class's share scales by its unit conductance over
L-AChR's (equal channel count per contact across classes, guessed; channels per contact = 0.447 nS / 33 pS = 13.5 at
the template, derived).

Toggle receptor_kinetics: kinetic (default; wsyn mode 2) / instantaneous (mode 1: r = steady-state activation, no
desensitization; PORT_SOURCES N1 (f)) / graded (mode 0 at every site with BAAIWorm's two-type parameters: the old
synapse inside the new mod, for the neutral-equivalence test) / off (BAAIWorm's two synapse mods, as before).
"""
from __future__ import annotations

import numpy as np

from wormemu import mech
from wormemu.brain_layers import Spec

MECHANISMS = [("receptor_kinetics", "Ionotropic receptor classes with kinetics: per-class dose-response, rise, decay, "
               "desensitization, reversal and unit conductance; classes per pair from CeNGEN, transmitter and "
               "Fenyves 2020 polarity", "synapse", "kinetic")]
MODES = {"graded": 0, "instantaneous": 1, "kinetic": 2}

# class: (ligand, +1 cation / -1 anion, genes, "all" = obligate heteromer / "any" = alternatives, name)
CLASSES = {
    "lacr": ("acetylcholine", +1, ("unc-29", "unc-38", "unc-63"), "all", "levamisole-type nAChR (L-AChR)"),
    "acr16": ("acetylcholine", +1, ("acr-16",), "any", "ACR-16 homomeric nAChR (N-AChR)"),
    "nachr": ("acetylcholine", +1, ("acr-2", "acr-3", "acr-5", "acr-8", "acr-9", "acr-12", "acr-14", "acr-15",
                                    "acr-18", "acr-19", "acr-21", "lev-1", "lev-8"), "any",
              "other neuronal nAChR subunits"),
    "acc": ("acetylcholine", -1, ("acc-1", "acc-2", "acc-3", "acc-4", "lgc-46", "lgc-47", "lgc-49"), "any",
            "ACh-gated chloride (ACC, LGC-46/47/49)"),
    "glr": ("glutamate", +1, ("glr-1", "glr-2", "glr-3", "glr-4", "glr-5", "glr-6", "glr-7", "glr-8"), "any",
            "non-NMDA glutamate receptor (GLR-1/2 AMPA-like)"),
    "nmr": ("glutamate", +1, ("nmr-1", "nmr-2"), "all", "NMDA-like (NMR-1/NMR-2)"),
    "glucl": ("glutamate", -1, ("glc-1", "glc-2", "glc-3", "glc-4", "avr-14", "avr-15"), "any",
              "glutamate-gated chloride (GluCl)"),
    "gabacl": ("gaba", -1, ("unc-49", "lgc-37", "lgc-38"), "any", "GABA-A chloride (UNC-49)"),
    "gabacat": ("gaba", +1, ("exp-1", "lgc-35"), "any", "GABA-gated cation (EXP-1, LGC-35)"),
    "mod1": ("serotonin", -1, ("mod-1",), "any", "serotonin-gated chloride (MOD-1)"),
    "lgc55": ("tyramine", -1, ("lgc-55",), "any", "tyramine-gated chloride (LGC-55)"),
    "lgc53": ("dopamine", -1, ("lgc-53",), "any", "dopamine-gated chloride (LGC-53)"),
    "acr23": ("betaine", +1, ("acr-23",), "any", "betaine-gated cation (ACR-23)"),
}
assert tuple(CLASSES) == mech.RECEPTOR_CLASSES
LIGANDS = ("acetylcholine", "glutamate", "gaba", "serotonin", "tyramine", "dopamine", "betaine")
# the class a pair falls back to when the postsynaptic cell expresses none for its transmitter and sign
DEFAULT = {("acetylcholine", +1): "nachr", ("acetylcholine", -1): "acc", ("glutamate", +1): "glr",
           ("glutamate", -1): "glucl", ("gaba", -1): "gabacl", ("gaba", +1): "gabacat", ("serotonin", -1): "mod1",
           ("tyramine", -1): "lgc55", ("dopamine", -1): "lgc53", ("betaine", +1): "acr23"}
QUANTITIES = ("ec50_uM", "hill", "tau_rise_ms", "tau_off_ms", "tau_des_ms", "ss_frac", "erev_mV", "gamma_pS")

M = "receptor_kinetics"
PMC = "Cys-loop review PMC10480131 (2023) Table 1"
BAMBER = "Bamber et al. 2005 Br J Pharmacol 144:502 (PMC1576029), HEK293 whole-cell"
RJ99 = "Richmond and Jorgensen 1999 Nat Neurosci 2:791"
NJ = "Putrenko, Zakikhani and Dent 2005 JBC 280:6392 would pin it (paywalled)"
GUESS_RISE = "clamp rise times <= 1-2 ms in the cited papers (PORT_SOURCES N1 (c), UNVERIFIED point value)"
CL = "near E_Cl; the native chloride reversal is unmeasured (RANGE_ENDS_LIT 4; param_ranges B6-B8)"


def _class_specs(c, rows):
    out = []
    for q, (t, lo, hi, label, src) in zip(QUANTITIES, rows):
        unit = {"ec50_uM": "uM", "hill": "1", "tau_rise_ms": "ms", "tau_off_ms": "ms", "tau_des_ms": "ms",
                "ss_frac": "1", "erev_mV": "mV", "gamma_pS": "pS"}[q]
        out.append(Spec(f"rec_{c}_{q}", M, unit, t, lo, hi, src, label, grain="class",
                        applies_to=f"{CLASSES[c][4]} receptors at chemical synapses"))
    return out


# per class, in QUANTITIES order: (template, lo, hi, label, source)
_H1 = (1.0, 0.8, 2.5, "guessed", "Hill coefficient not reported; n = 1 (PORT_SOURCES N1 rule)")
TABLE = {
    "lacr": [(26.0, 10.0, 100.0, "measured", f"Boulin et al. 2008 PNAS (oocyte, UNC-29/38/63/LEV-1/LEV-8), via {PMC}"),
             _H1, (0.5, 0.1, 2.0, "guessed", GUESS_RISE),
             (6.5, 5.0, 8.0, "inferred", f"NMJ EPSC decay 5.6 ms (electrical) to 7.4 ms (light), {RJ99} (search "
              "summary, param_ranges B11); a compound L-AChR + ACR-16 current, so per class inferred"),
             (4000.0, 1000.0, 20000.0, "guessed", "no decay during an agonist pulse (Boulin et al. 2008, qualitative)"),
             (0.8, 0.5, 1.0, "guessed", "no decay during the pulse (Boulin et al. 2008, qualitative)"),
             (11.0, -10.0, 15.0, "measured", f"{RJ99} Fig. 4c: muscle ACh current reverses at +11 mV (n = 4)"),
             (33.0, 30.0, 35.0, "measured", f"single-channel 30-35 pS, Rayes et al. 2007 / Hernando et al. 2012, via "
              f"{PMC}")],
    "acr16": [(55.0, 20.0, 150.0, "measured", f"{PMC} (oocyte, with RIC-3)"), _H1,
              (0.5, 0.1, 2.0, "guessed", GUESS_RISE),
              (6.5, 3.0, 10.0, "inferred", f"NMJ EPSC decay (compound current), {RJ99} via param_ranges B11"),
              (100.0, 25.0, 400.0, "inferred", f"decays about 40x faster than L-AChR ({PMC}): L-AChR's guessed 4000 "
               "ms / 40"),
              (0.02, 0.0, 0.1, "guessed", f"'insignificant steady-state current' ({PMC}, qualitative)"),
              (11.0, -10.0, 15.0, "inferred", "the muscle ACh reversal (non-selective cation channel)"),
              (40.0, 20.0, 90.0, "guessed", "not reported for ACR-16; vertebrate alpha7 homomers 70-90 pS")],
    "nachr": [(40.0, 10.0, 150.0, "inferred", "between L-AChR (26 uM) and ACR-16 (55 uM)"), _H1,
              (0.5, 0.1, 2.0, "guessed", GUESS_RISE),
              (6.5, 3.0, 15.0, "inferred", "the NMJ nAChR decay (param_ranges B11)"),
              (1000.0, 100.0, 10000.0, "guessed", "between ACR-16 (fast) and L-AChR (none in a pulse)"),
              (0.3, 0.0, 1.0, "guessed", "between ACR-16 and L-AChR"),
              (11.0, -10.0, 15.0, "inferred", "the muscle ACh reversal (cation channel)"),
              (33.0, 20.0, 60.0, "inferred", "L-AChR's single-channel conductance")],
    "acc": [(20.0, 1.0, 300.0, "guessed", f"not retrieved; {NJ}"), _H1, (1.0, 0.1, 2.0, "guessed", GUESS_RISE),
            (10.0, 3.0, 50.0, "guessed", f"not retrieved; {NJ}"),
            (1000.0, 100.0, 10000.0, "guessed", f"not retrieved; {NJ}"),
            (0.5, 0.0, 1.0, "guessed", f"not retrieved; {NJ}"),
            (-58.0, -70.0, -45.0, "inferred", CL), (30.0, 10.0, 80.0, "guessed", f"not retrieved; {NJ}")],
    "glr": [(500.0, 100.0, 3000.0, "inferred", "not retrieved for GLR-1; vertebrate AMPA receptors 0.2-1 mM"),
            (1.3, 1.0, 2.0, "inferred", "vertebrate AMPA receptors 1.3-1.6"), (0.5, 0.1, 2.0, "guessed", GUESS_RISE),
            (5.0, 1.0, 20.0, "guessed", "fast (Mellem et al. 2002 Neuron 36:933, qualitative); vertebrate AMPA 2-5 "
             "ms"),
            (20.0, 3.0, 200.0, "guessed", "fast desensitization, slowed and limited by SOL-1 (Walker et al. 2006, "
             "qualitative)"),
            (0.1, 0.01, 0.5, "guessed", "SOL-1 limits the extent of desensitization (qualitative)"),
            (-7.0, -10.2, -3.8, "measured", "Lindsay, Thiele and Lockery 2011 Nat Commun 2:306: ASH-evoked current in "
             "AVA reverses at -7.0 +- 3.2 mV"),
            (15.0, 5.0, 30.0, "inferred", "vertebrate AMPA receptors 8-20 pS")],
    "nmr": [(2.3, 1.0, 10.0, "inferred", "not retrieved for NMR-1; vertebrate NMDA receptors 1-3 uM"),
            (1.4, 1.0, 2.0, "inferred", "vertebrate NMDA receptors"),
            (5.0, 2.0, 20.0, "inferred", "vertebrate NMDA rise about 5-10 ms"),
            (100.0, 30.0, 500.0, "inferred", "'slow' component in AVA (Brockie et al. 2001 Neuron 31:617, "
             "qualitative); vertebrate NMDA decay 50-300 ms"),
            (2000.0, 500.0, 10000.0, "guessed", "slowly desensitizing (Brockie et al. 2001, qualitative)"),
            (0.5, 0.1, 1.0, "guessed", "slowly desensitizing (qualitative)"),
            (0.0, -10.0, 10.0, "inferred", "cation channel; glutamate reversal near 0 mV"),
            (50.0, 20.0, 70.0, "inferred", "vertebrate NMDA receptors about 50 pS")],
    "glucl": [(208.0, 62.0, 10000.0, "measured", f"AVR-15B (oocyte), {PMC}; the subtypes span 62 uM (AVR-15B/GLC-2) "
               "to 10 mM (AVR-14B)"), _H1, (1.0, 0.1, 2.0, "guessed", GUESS_RISE),
              (10.0, 3.0, 50.0, "guessed", "not retrieved (PORT_SOURCES N1 gap)"),
              (3000.0, 300.0, 30000.0, "guessed", "not retrieved (PORT_SOURCES N1 gap)"),
              (0.6, 0.0, 1.0, "guessed", "not retrieved (PORT_SOURCES N1 gap)"),
              (-58.0, -70.0, -45.0, "inferred", CL),
              (20.0, 5.0, 60.0, "guessed", "not retrieved (PORT_SOURCES N1 gap)")],
    "gabacl": [(19.6, 8.6, 107.0, "measured", f"{BAMBER}, UNC-49B/C heteromer (the NMJ receptor). Chosen over the "
                f"review's 107 uM ({PMC}, a different preparation): the primary paper, and the composition it "
                "identifies at the NMJ; the range spans the B homomer (8.6 uM) and the review"),
               (1.3, 1.3, 2.0, "measured", f"{BAMBER}: B/C 1.3, B homomer 2.0"),
               (1.0, 0.1, 2.0, "guessed", GUESS_RISE),
               (19.16, 15.45, 22.69, "derived", "the receptor's own deactivation, solved so that the model's evoked "
                "NMJ IPSC (BAAIWorm's graded release state, 1/k = 8.6 ms after a 2 ms presynaptic step, then this "
                "receptor) decays with Liu, Hollopeter and Jorgensen 2009 PNAS 106:10823 (PMC2705609) Fig. 2B's "
                "light-evoked 24.8 +- 2.7 ms (n = 12), a composite of release and closing; bounds give the "
                "composite 22.1 and 27.5 ms, the other values at their templates "
                "(scripts/worm/debug2/derive_gaba_tau_off.py; DEBUG_TRIAGE line 3)"),
               (149.0, 139.0, 232.0, "measured", f"{BAMBER}: slow desensitization component 149 +- 10 ms (B/C), 206 "
                "+- 26 ms (B homomer); 91-95% of the weighted tau"),
               (0.1, 0.01, 0.4, "guessed", "steady-state fraction not retrieved"),
               (-58.0, -70.0, -45.0, "inferred", CL + "; +17 to +20 mV only under an imposed Cl gradient (RJ99)"),
               (30.0, 25.0, 37.0, "measured", "B/C about 20% below the B homomer's 37 pS (Bamber et al. 1999, "
                "2005)")],
    "gabacat": [(10.0, 1.0, 200.0, "guessed", "not retrieved; Beg and Jorgensen 2003 Nat Neurosci 6:1145 would pin "
                 "it"), _H1, (1.0, 0.1, 2.0, "guessed", GUESS_RISE),
                (20.0, 5.0, 100.0, "guessed", "not retrieved (Beg and Jorgensen 2003)"),
                (1000.0, 100.0, 10000.0, "guessed", "not retrieved (Beg and Jorgensen 2003)"),
                (0.5, 0.0, 1.0, "guessed", "not retrieved"),
                (0.0, -10.0, 10.0, "inferred", "cation-selective (Beg and Jorgensen 2003); param_ranges B9"),
                (20.0, 5.0, 60.0, "guessed", "not retrieved")],
    "mod1": [(4.4, 1.0, 8.0, "measured", "Ranganathan, Cannon and Horvitz 2000 Nature 408:470 (oocyte; search "
              f"summary, param_ranges D6); {PMC} gives 1 uM"), _H1, (1.0, 0.1, 2.0, "guessed", GUESS_RISE),
             (20.0, 5.0, 200.0, "guessed", "not retrieved"),
             (2000.0, 200.0, 20000.0, "guessed", "desensitizes during sustained agonist, recovers fast off agonist "
              f"({PMC}, qualitative)"),
             (0.3, 0.0, 1.0, "guessed", "not retrieved"), (-58.0, -70.0, -45.0, "inferred", CL),
             (20.0, 5.0, 60.0, "guessed", "not retrieved")],
    "lgc55": [(6.0, 3.0, 10.0, "measured", "Pirri et al. 2009 Neuron 62:526 (search summary, param_ranges D7)"), _H1,
              (1.0, 0.1, 2.0, "guessed", GUESS_RISE), (20.0, 5.0, 200.0, "guessed", "not retrieved"),
              (2000.0, 200.0, 20000.0, "guessed", "not retrieved"), (0.3, 0.0, 1.0, "guessed", "not retrieved"),
              (-58.0, -70.0, -45.0, "inferred", CL), (20.0, 5.0, 60.0, "guessed", "not retrieved")],
    "lgc53": [(5.0, 0.5, 50.0, "guessed", "not retrieved; Ringstad, Abe and Horvitz 2009 Science 325:96 would pin it"),
              _H1, (1.0, 0.1, 2.0, "guessed", GUESS_RISE), (20.0, 5.0, 200.0, "guessed", "not retrieved"),
              (2000.0, 200.0, 20000.0, "guessed", "not retrieved"), (0.3, 0.0, 1.0, "guessed", "not retrieved"),
              (-58.0, -70.0, -45.0, "inferred", CL), (20.0, 5.0, 60.0, "guessed", "not retrieved")],
    "acr23": [(1000.0, 100.0, 5000.0, "guessed", "not retrieved; Peden et al. 2013 Nat Neurosci 16:1794 would pin it"),
              _H1, (0.5, 0.1, 2.0, "guessed", GUESS_RISE), (6.5, 3.0, 20.0, "inferred", "the nAChR decay (same family)"),
              (2000.0, 200.0, 20000.0, "guessed", "not retrieved"), (0.3, 0.0, 1.0, "guessed", "not retrieved"),
              (0.0, -10.0, 15.0, "inferred", "cation channel"), (30.0, 10.0, 60.0, "guessed", "not retrieved")],
}
SPECS = [s for c in CLASSES for s in _class_specs(c, TABLE[c])] + [
    Spec(f"rec_tmax_{lg}_uM", M, "uM", t, lo, hi, src, "guessed", grain="global",
         applies_to=f"{lg} synapses (cleft concentration at full graded release)")
    for lg, t, lo, hi, src in (
        ("acetylcholine", 100.0, 10.0, 1000.0, "graded release has no measured cleft concentration; below the "
         "vertebrate quantal peak of about 1 mM (Clements et al. 1992 Science 258:1498), as a mean over sustained "
         "release"),
        ("glutamate", 100.0, 10.0, 1000.0, "as acetylcholine"),
        ("gaba", 100.0, 10.0, 1000.0, "as acetylcholine"),
        ("serotonin", 10.0, 1.0, 100.0, "monoamine release; no worm value (param_ranges D5 notes the gap)"),
        ("tyramine", 10.0, 1.0, 100.0, "as serotonin"),
        ("dopamine", 10.0, 1.0, 100.0, "as serotonin"),
        ("betaine", 100.0, 10.0, 1000.0, "as acetylcholine"))] + [
    Spec("rec_mg_mM", M, "mM", 1.0, 0.1, 5.0, "external Mg2+ at NMDA-like synapses: not measured in body fluid; NGM "
         "holds 1 mM MgSO4 (Brenner 1974)", "guessed", applies_to="NMDA-like (nmr) synapses"),
    Spec("rec_mg_k_per_mV", M, "1/mV", 0.062, 0.05, 0.08, "Jahr and Stevens 1990 J Neurosci 10:3178 (vertebrate)",
         "published_fit", applies_to="NMDA-like (nmr) synapses",
         notes="worm NMR-1 Mg block unmeasured; the conserved pore asparagine makes it inferred by homology"),
    Spec("rec_mg_c_mM", M, "mM", 3.57, 2.0, 6.0, "Jahr and Stevens 1990 J Neurosci 10:3178 (vertebrate)",
         "published_fit", applies_to="NMDA-like (nmr) synapses"),
    Spec("rec_des_recover_ratio", M, "1", 1.0, 0.5, 50.0, "recovery from desensitization is slower than its onset "
         "for GLR-1 (SOL-1 slows it; Walker et al. 2006 PNAS, qualitative, not opened) and vertebrate AMPA and "
         "nicotinic receptors (guessed); 1 = one time constant both ways", "guessed", grain="global",
         applies_to="every desensitizing class (tau_des > 0)",
         notes="tau of recovery = rec_<c>_tau_des_ms x this; one shared ratio, not one per class"),
    Spec("rec_nmj_lacr_share", M, "1", 0.5, 0.2, 0.8, "share of the NMJ ACh conductance on L-AChR (the rest ACR-16): "
         "both carry the evoked current (Touroutine et al. 2005 JBC; Francis et al. 2005), split not retrieved",
         "guessed", applies_to="neuromuscular junctions"),
]


def class_tpm(st, cls_name, c):
    """A class's expression in one CeNGEN class (threshold-2 TPM): least-expressed subunit of an obligate
    heteromer, most-expressed gene of an alternative set."""
    _, _, genes, rule, _ = CLASSES[c]
    x = [st.expr(g, cls_name) for g in genes]
    return min(x) if rule == "all" else max(x)


def pair_classes(st, pre, post_cls, polarity=None, inhibitory=False, post_muscle=False, lacr_share=0.5):
    """[(class, share)] for one chemical pair, shares summing to 1; [] = keep BAAIWorm's graded synapse.
    polarity '+' / '-' (measured or Fenyves 2020) keeps only classes of that sign; None keeps all expressed ones.
    inhibitory: the pair's sign under the sign rules, for the fallback class."""
    tr = [lg for lg in LIGANDS if lg in st.transmitter.get(pre, set())]
    if post_muscle:
        out = []
        if "acetylcholine" in tr:
            out += [("lacr", lacr_share), ("acr16", 1.0 - lacr_share)]
        if "gaba" in tr:
            out += [("gabacl", 1.0)]
        tot = sum(s for _, s in out)
        return [(c, s / tot) for c, s in out]
    want = {"+": +1, "-": -1}.get(polarity)
    w = {c: class_tpm(st, post_cls, c) for c, (lg, sg, *_) in CLASSES.items()
         if lg in tr and (want is None or sg == want) and post_cls is not None}
    w = {c: x for c, x in w.items() if x > 0}
    if not w:
        sg = want if want is not None else (-1 if inhibitory else +1)
        c = next((DEFAULT[(lg, sg)] for lg in tr if (lg, sg) in DEFAULT), None)
        return [] if c is None else [(c, 1.0)]
    tot = sum(w.values())
    return [(c, x / tot) for c, x in w.items()]


def site_params(p, c, mode):
    """wsyn parameters for one class (mod units: mM, ms, mV) from the worm's values p."""
    lg = CLASSES[c][0]
    q = {k: float(p[f"rec_{c}_{k}"]) for k in QUANTITIES}
    out = dict(mode=float(mode), tmax=float(p[f"rec_tmax_{lg}_uM"]) / 1000.0, ec50=q["ec50_uM"] / 1000.0,
               hill=q["hill"], tau_rise=q["tau_rise_ms"], tau_off=q["tau_off_ms"], tau_des=q["tau_des_ms"],
               ss=q["ss_frac"], erev=q["erev_mV"], mg=0.0, des_rec_ratio=float(p.get("rec_des_recover_ratio", 1.0)))
    if c == "nmr":
        out.update(mg=float(p["rec_mg_mM"]), mgk=float(p["rec_mg_k_per_mV"]), mgc=float(p["rec_mg_c_mM"]))
    return out


def gamma_ratio(p, c):
    """Unit conductance relative to L-AChR's (the per-contact strength's reference)."""
    return float(p[f"rec_{c}_gamma_pS"]) / float(p["rec_lacr_gamma_pS"])


class Mech:
    """The synapses are placed at wiring (brain._wire_cook); nothing runs per step. Other mechanisms scale them
    through g_scale 'release' (per presynaptic cell) and 'rec_<class>' (per postsynaptic cell)."""

    def __init__(self, brain, params, toggles):
        pass

    def reset(self):
        pass

    def step(self, ctx, dt_ms):
        return {}
