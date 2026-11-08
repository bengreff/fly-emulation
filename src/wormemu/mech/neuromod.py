"""Rows 9, 10 and 28: neuropeptides, monoamines and the sleep neurons' peptides (PLAN rows 9, 10, 28;
docs/worm/research/PORT_SOURCES_NEURAL.md N4 and N10; research/NEUROPEPTIDES.md).

No published worm model of the cascade exists (PORT_SOURCES N4 (a)); the port target is release -> volume
transmission -> receptor occupancy -> G protein -> channel and release modulation, each step one relaxation, with
the time constants shared by G-protein family. Structure below; every number is in SPECS.

Pseudocoelom. Four named compartments along the body (COMPARTMENTS), cut at landmarks of the soma coordinates
(pc_*_y_um, derived) and closed by the most anterior and most posterior neuron somas. Volume = length x
pc_cross_section_um2 (guessed). Neighbours exchange by diffusion through the shared cross-section A:
dN_k/dt = A D (c_j - c_k) / d_kj, d_kj the distance between compartment centres, so total molecules are conserved;
D is the molecular diffusion coefficient plus pc_stirring_um2_per_s (body movement stirring the fluid; template 0).
The linear exchange is integrated exactly (matrix exponential). Each cell releases into and reads the compartment of
its soma (validity: a cell's processes elsewhere, e.g. along the ventral cord, count at its soma). Concentration
(nM) = molecules / (602.214 x volume in pL).

Peptides (row 9). Dense-core vesicle release through UNC-31/CAPS (Speese et al. 2007 J Neurosci 27:6150; UNC-31 taken
as pan-neuronal, so no expression gate): a slow drive q' = (sigmoid((V - dcv_vhalf)/dcv_k) - q)/dcv_tau, times
dcv_rate_per_s vesicles at full drive, times dcv_peptides_per_vesicle, split among the Table S6 precursors the cell
expresses (CeNGEN threshold 2) by TPM share (inferred: expression as a proxy for cargo), times the cell's
G-protein release factor. Loss: degradation (pep_degrade_tau_s, param_ranges D4) and coelomocyte uptake
(pc_coelomocyte_uptake_per_s, a placeholder until B2's row 16 writes outputs['coelomocyte_uptake_per_s'], a first-order
rate per s, uniform). Other modules' release, outputs['peptide_release'] = {gene or "gene@compartment": molecules/s},
is added (a bare gene is spread by volume). Receptors: every Beets et al. 2023 Table S6 EC50 (bioRxiv
2022.10.30.514428 v1 media-6: 459 peptide-GPCR pairs, reduced to 147 precursor-receptor gene pairs in
data/worm/structure/beets2023/), one Spec per gene pair at the precursor's most potent peptide, bounds from the 95% CIs
and the least potent peptide; occupancy c^h / (c^h + EC50^h).

Monoamines (row 10). Release cells from the transmitter atlas (5-HT, DA, OA, TA). Each releasing cell's vesicular
store S (fraction of ma_store_molecules) refills with ma_synth_tau_s and empties by release J = ma_release_per_s x q x
S x R (q the cell's drive with the ma_ voltage specs, R its release factor). Reuptake is Michaelis-Menten by MOD-5
(SERT) and DAT-1 (DAT) cells and refills the uptaking cell's store if it releases that amine; residual loss
ma_degrade_tau_s. OA and TA have no known plasma-membrane transporter, so only the residual loss clears them.
Receptors: the 14 Bentley et al. 2016 amine-GPCR pairs (one EC50 Spec each) and the three amine-gated chloride
channels outside synapses, MOD-1, LGC-55 and LGC-53 (row 7's class values for EC50, Hill, reversal and unit
conductance; ma_extrasyn_channels per expressing cell), each a wgc conductance at the soma (nmodl/wgc.mod).

G proteins. Per cell and family f in (q, i/o, s): target_f = 1 - prod over its receptors of (1 - w_f x occ), w the
receptor's coupling (GPCR_COUPLING: 1 on its family; gpcr_unknown_share on all three when unknown), 0 where the cell
lacks that G alpha (EGL-30, GOA-1, GSA-1 in CeNGEN). G_f' = (target_f - G_f)/g<f>_tau_ms. Effectors, as g_scale (1 at
G = 0):
  release    (1 + aq Gq)(1 + as Gs)/(1 + ai Gi): Gq-DAG-UNC-13 and Gs-PKA raise release, Go-DGK-1 lowers it (Miller
             et al. 1999 Neuron 24:323; Lackner et al. 1999 Neuron 24:335; Nurrish et al. 1999 Neuron 24:231; Charlie
             et al. 2006 Genetics 173:111); multiplies the cell's synapses (wsyn relgain), its DCV and amine release
  dens_nca   1 + bq Gq (Gq-TRIO-RHO-1 raises the NCA leak; Topalidou et al. 2017 Genetics 206:1231)
  dens_irk   1 + bi Gi (G beta-gamma opening an inward rectifier, by homology to GIRK)
  dens_egl19 1 + bs Gs (PKA raising L-type Ca current, by homology)
The gains are guessed; which family moves which effector, and which way, is from the genetics cited.

Sleep (row 28) runs through the same machinery: RIS releases FLP-11 (CeNGEN), read by DMSR-1 (Gi/o) on its targets and
on RIS itself. CeNGEN gives dmsr-1 0 in RIS, so the autoreceptor is added (EXPR_ADD; Rossi et al. 2025 Curr Biol
35:2183, RIS-specific dmsr-1 knockdown lengthens sleep). ALA releases FLP-13 and FLP-24 onto their Table S6 receptors.
NLP-8 has no receptor in Table S6: not modelled (no receptor to act on) until one is found.

Toggles peptides and monoamines: compartments (default; "on" means the same) / well_mixed (one compartment of the
whole volume, everything else unchanged; the limit of compartments as diffusion grows, tested) / lumped (brain_layers'
old current-injection layer, run here unchanged; the neutral-equivalence test) / off.
"""
from __future__ import annotations

import csv
from pathlib import Path

import numpy as np
from scipy.linalg import expm

from wormemu import mech
from wormemu.brain_layers import Spec, _sig
from wormemu.brain_structure import cengen_class
from wormemu.mech import receptors

ROOT = Path(__file__).resolve().parents[3]
BEETS = ROOT / "data" / "worm" / "structure" / "beets2023" / "peptide_gpcr_ec50.csv"
BEETS_SRC = "Beets et al. 2023 Science (bioRxiv 2022.10.30.514428 v1 media-6, Table S6; 95% CI)"

MECHANISMS = [
    ("peptides", "Neuropeptides: UNC-31 dense-core release into four pseudocoelom compartments, every Beets 2023 "
     "EC50 pair, GPCR -> Gq/Gi/Gs -> release, NCA, IRK, EGL-19", "neuromodulation", "compartments"),
    ("monoamines", "Monoamines (5-HT, DA, OA, TA): stores, release, MOD-5/DAT-1 reuptake, GPCRs -> G proteins, "
     "MOD-1/LGC-55/LGC-53 outside synapses; the same compartments", "neuromodulation", "compartments"),
]
FORMS = ("compartments", "well_mixed", "lumped", "off")
COMPARTMENTS = ("head", "anterior_body", "posterior_body", "tail")
AMINES = ("serotonin", "dopamine", "octopamine", "tyramine")
TRANSPORTERS = {"serotonin": "mod-5", "dopamine": "dat-1"}
EXTRASYN = {"serotonin": "mod1", "dopamine": "lgc53", "tyramine": "lgc55"}       # row 7 classes
N_EXTRA = {AMINES.index(lg): rc for lg, rc in EXTRASYN.items()}
G_ALPHA = ("egl-30", "goa-1", "gsa-1")                                           # Gq, Gi/o, Gs
NA_PL = 602.214                                                                  # molecules per nM per pL
# expression CeNGEN lacks: (CeNGEN class, gene): source
EXPR_ADD = {("RIS", "dmsr-1"): "Rossi et al. 2025 Curr Biol 35:2183: RIS-specific dmsr-1 knockdown lengthens sleep "
                               "(the self-inhibiting FLP-11 autoreceptor); CeNGEN gives 0 in RIS"}

HOM = "inferred by homology: the family's vertebrate or insect members couple this way"
# receptor gene: (family "q" / "i" / "s" / "u" unknown, receptor family, label, source). Families: Beets et al. 2023
# media-9 (peptide GPCRs) and Bentley et al. 2016 (amines)
GPCR_COUPLING = {
    "ntr-1": ("q", "vasopressin/oxytocin", "inferred", HOM),
    "tkr-1": ("q", "tachykinin", "inferred", HOM),
    "tkr-2": ("q", "tachykinin", "inferred", HOM),
    "gnrr-1": ("q", "GnRH/AKH", "inferred", HOM),
    "gnrr-3": ("q", "nematode GnRH-like RPamide", "inferred", HOM),
    "gnrr-6": ("q", "nematode GnRH-like RPamide", "inferred", HOM),
    "ckr-1": ("q", "CCK/sulfakinin", "inferred", HOM),
    "ckr-2": ("q", "CCK/sulfakinin", "measured", "genetic: NLP-12/CKR-2 raises ACh release through EGL-30 (Gq) and "
              "EGL-8, Hu et al. 2011 Neuron 71:92 (not re-opened tonight)"),
    "nmur-1": ("q", "NMU/pyrokinin", "inferred", HOM),
    "nmur-2": ("q", "NMU/pyrokinin", "inferred", HOM),
    "trhr-1": ("q", "TRH/fulicin", "inferred", HOM),
    "npr-11": ("i", "NPY/NPF", "inferred", HOM),
    "npr-12": ("i", "NPY/NPF", "inferred", HOM),
    "npr-35": ("i", "NPFF/SIFamide", "inferred", HOM),
    **{g: ("i", "short neuropeptide F", "inferred", HOM) for g in ("npr-1", "npr-2", "npr-3", "npr-4", "npr-5",
                                                                     "npr-6", "npr-10", "npr-13")},
    "sprr-1": ("i", "AstB/MIP", "inferred", HOM),
    "sprr-2": ("i", "AstB/MIP", "inferred", HOM),
    **{g: ("i", "myosuppressin-like", "inferred", HOM) for g in ("dmsr-2", "dmsr-3", "dmsr-5", "dmsr-6", "dmsr-7",
                                                                   "dmsr-8")},
    "dmsr-1": ("i", "myosuppressin-like", "measured", "Gi/o: pertussis-toxin sensitive, Rossi et al. 2025 Curr Biol "
               "35:2183"),
    "egl-6": ("i", "myosuppressin-like", "measured", "genetic: EGL-6 inhibits HSN through GOA-1 (Go), Ringstad and "
              "Horvitz 2008 Nat Neurosci 11:1168"),
    "npr-24": ("i", "nematode SST/opioid/AstC-like", "inferred", HOM),
    "npr-32": ("i", "nematode SST/opioid/AstC-like", "inferred", HOM),
    "pdfr-1": ("s", "PDF/cerebellin", "measured", "genetic: PDFR-1 acts through GSA-1 (Gs) and PKA, Flavell et al. 2013 "
               "Cell 154:1023; cAMP rise in cells, Janssen et al. 2008"),
    "seb-3": ("s", "PDFR-like (secretin family)", "inferred", HOM),
    "aex-2": ("s", "no clear family", "inferred", "genetic: activated GSA-1 in GABA neurons bypasses aex-2, Mahoney et "
              "al. 2008 PNAS 105:16350 (not re-opened)"),
    **{g: ("u", "protostomian RFamide", "guessed", "coupling unknown") for g in (
        "frpr-3", "frpr-4", "frpr-6", "frpr-7", "frpr-8", "frpr-9", "frpr-15", "frpr-16", "frpr-18", "frpr-19",
        "npr-37", "npr-39", "npr-43")},
    "npr-22": ("u", "RWamide/RYamide/luqin", "guessed", "coupling unknown"),
    "npr-40": ("u", "nematode EF/YL/IRFamide", "guessed", "coupling unknown"),
    **{g: ("u", "no clear family", "guessed", "coupling unknown") for g in ("npr-8", "npr-41", "npr-42")},
    # amine GPCRs
    "ser-1": ("q", "5-HT2-like", "inferred", HOM),
    "ser-4": ("i", "5-HT1-like", "inferred", HOM),
    "ser-5": ("s", "5-HT6-like", "inferred", HOM),
    "ser-7": ("s", "5-HT7-like", "measured", "SER-7 raises cAMP in cells, Hobson et al. 2003 J Neurochem 87:22"),
    "dop-1": ("q", "D1-like", "measured", "genetic: DOP-1 acts through EGL-30 (Gq), Chase, Pepper and Koelle 2004 "
              "Nat Neurosci 7:1096"),
    "dop-2": ("i", "D2-like", "inferred", HOM),
    "dop-3": ("i", "D2-like", "measured", "genetic: DOP-3 acts through GOA-1 (Go), Chase et al. 2004"),
    "dop-4": ("s", "D1-like", "inferred", HOM),
    "octr-1": ("i", "alpha2-adrenergic-like", "inferred", HOM),
    "ser-3": ("q", "alpha1-adrenergic-like (octopamine)", "inferred", HOM),
    "ser-6": ("u", "octopamine receptor", "guessed", "coupling unknown"),
    "ser-2": ("i", "tyramine receptor", "inferred", HOM),
    "tyra-2": ("u", "tyramine receptor", "guessed", "coupling unknown"),
    "tyra-3": ("u", "tyramine receptor", "guessed", "coupling unknown"),
}
FAMILY = {"q": (1.0, 0.0, 0.0), "i": (0.0, 1.0, 0.0), "s": (0.0, 0.0, 1.0)}


def form(value) -> str:
    v = {True: "compartments", False: "off", None: "off", "on": "compartments"}.get(value, value)
    assert v in FORMS, f"neuromodulation form {value!r} not one of {FORMS}"
    return v


def _g4(x):
    return float(f"{x:.4g}")


def beets_pairs():
    """{(precursor gene, receptor gene): (EC50 template nM, lo nM, hi nM, n peptides)} from Table S6."""
    rows = {}
    with open(BEETS) as f:
        for r in csv.DictReader(f):
            a, b = sorted(10 ** float(x) for x in r["ci95_log_M"].split(" to "))
            rows.setdefault((r["peptide_gene"], r["gpcr_gene"]), []).append((float(r["ec50_M"]), a, b))
    out = {}
    for k, xs in sorted(rows.items()):
        best = min(xs)
        lo, hi = min(x[1] for x in xs), max(max(x[0] for x in xs), best[2])
        out[k] = (_g4(best[0] * 1e9), _g4(min(lo, best[0]) * 1e9), _g4(hi * 1e9), len(xs))
    return out


PAIRS = beets_pairs()
PRECURSORS = tuple(sorted({a for a, _ in PAIRS}))


def S(sid, mid, unit, t, lo, hi, src="guessed", label="guessed", **kw):
    return Spec(sid, mid, unit, t, lo, hi, src, label, **kw)


P, A = "peptides", "monoamines"
BOTH = "peptides and monoamines (shared)"
SPECS = [
    S("pc_head_end_y_um", P, "um (soma y)", -200, -240, -160, "the soma atlas: just behind the retrovesicular ganglion "
      "(somas y -227 to -240), the nerve ring and head ganglia anterior", "derived", applies_to=BOTH),
    S("pc_vulva_y_um", P, "um (soma y)", 61, 40, 80, "the soma atlas: HSN somas (y 61) mark the vulva", "derived",
      applies_to=BOTH),
    S("pc_tail_start_y_um", P, "um (soma y)", 330, 316, 359, "the soma atlas: between AS11 (y 316) and the pre-anal "
      "ganglion (y 359-385)", "derived", applies_to=BOTH),
    S("pc_cross_section_um2", P, "um2", 400, 100, 1500, notes="pseudocoelom cross-section; the body's is about "
      "1600-2000 um2 at 45-50 um diameter, most of it intestine, gonad and muscle", applies_to=BOTH),
    S("pc_stirring_um2_per_s", P, "um2/s", 0.0, 0.0, 1000.0, notes="effective dispersion added by body movement "
      "stirring the pseudocoelomic fluid; unmeasured; 0 = diffusion only", applies_to=BOTH),
    S("pc_coelomocyte_uptake_per_s", P, "1/s", 0.001, 0.0001, 0.01, notes="placeholder until row 16 (B2) writes "
      "outputs['coelomocyte_uptake_per_s']; first-order, uniform over compartments; secreted GFP is taken up by "
      "coelomocytes over minutes to hours (Fares and Greenwald 2001, qualitative)", applies_to="peptides"),
    S("pep_diffusion_um2_per_s", P, "um2/s", 50, 10, 150, lit="D3"),
    S("pep_degrade_tau_s", P, "s", 100, 10, 600, lit="D4", notes="peptidase loss (NEP-1 etc.) other than coelomocytes"),
    S("dcv_vhalf_mV", P, "mV", -30, -50, 0, notes="the old lumped layer's pep_release_vth_mV"),
    S("dcv_k_mV", P, "mV", 5, 2, 15, notes="the old lumped layer's fixed 5 mV"),
    S("dcv_tau_ms", P, "ms", 1000, 100, 10000, notes="DCV release needs sustained activity (seconds); the drive's "
      "relaxation time"),
    S("dcv_rate_per_s", P, "vesicles/s per neuron", 5, 0.1, 50, notes="DCV fusions per neuron per s at full drive"),
    S("dcv_peptides_per_vesicle", P, "molecules", 3000, 300, 30000),
    S("gpcr_hill", P, "1", 1.0, 0.5, 2.0, BEETS_SRC + ": EC50s from dose-response fits", "inferred",
      notes="Hill coefficient of every GPCR's occupancy", applies_to=BOTH),
    S("gpcr_unknown_share", P, "1", 0.333, 0.0, 1.0, notes="coupling weight on each of Gq, Gi/o, Gs for a receptor of "
      "unknown coupling", applies_to=BOTH),
]
for f, nm in (("gq", "Gq (EGL-30)"), ("gi", "Gi/o (GOA-1)"), ("gs", "Gs (GSA-1)")):
    SPECS.append(S(f"{f}_tau_ms", P, "ms", 1000, 100, 5000, "PORT_SOURCES N4 (a): 100 ms to several s for G-protein "
                   "cascades (homology)", "inferred", grain="class", applies_to=f"{nm}, every cell, {BOTH}"))
for sid, t, hi, what in (("release_gq_gain", 1.0, 3.0, "Gq raises release (DAG, UNC-13)"),
                         ("release_gs_gain", 1.0, 3.0, "Gs raises release (cAMP, PKA)"),
                         ("release_gi_gain", 1.0, 3.0, "Go/i lowers release (DGK-1)"),
                         ("nca_gq_gain", 1.0, 4.0, "Gq raises the NCA leak density"),
                         ("irk_gi_gain", 1.0, 4.0, "Gi/o raises the IRK density"),
                         ("egl19_gs_gain", 0.5, 2.0, "Gs raises the EGL-19 density")):
    SPECS.append(S(sid, P, "1 per unit G", t, 0.0, hi, notes=what + "; the direction is from the genetics in the "
                   "module docstring, the size is guessed", grain="class", applies_to=BOTH))
for (pg, rg), (t, lo, hi, k) in PAIRS.items():
    SPECS.append(S(f"pep_ec50_{pg}_{rg}_nM", P, "nM", t, lo, hi, BEETS_SRC, "measured", grain="pairing",
                   applies_to=f"{pg} peptides on {rg}",
                   notes=f"most potent of {k} {pg} peptide(s); bounds: lowest 95% CI and least potent peptide"))
SPECS += [
    S("ma_diffusion_um2_per_s", A, "um2/s", 600, 200, 1000, "free aqueous dopamine about 6e-6 cm2/s (Gerhardt and "
      "Adams 1982 Anal Chem 54:2618), slowed by tortuosity", "inferred"),
    S("ma_degrade_tau_s", A, "s", 5, 0.5, 50, notes="loss other than reuptake (AMX amine oxidases etc.)"),
    S("ma_vhalf_mV", A, "mV", -30, -50, 0, notes="the old lumped layer's ma_release_vth_mV"),
    S("ma_k_mV", A, "mV", 5, 2, 15),
    S("ma_tau_ms", A, "ms", 100, 10, 1000, notes="small clear and dense-core vesicles: faster than peptide DCVs"),
    S("ma_release_per_s", A, "molecules/s per neuron", 1e5, 1e3, 1e7, notes="at full drive and a full store",
      grain="class", applies_to="5-HT, DA, OA, TA release cells"),
    S("ma_store_molecules", A, "molecules per neuron", 1e6, 1e4, 1e8, grain="class", applies_to="each release cell"),
    S("ma_synth_tau_s", A, "s", 60, 5, 600, notes="refill time of an empty store (TPH-1, CAT-2, TDC-1/TBH-1 synthesis "
      "and CAT-1 loading)", grain="class"),
    S("ma_uptake_vmax_per_s", A, "molecules/s per cell", 2e5, 1e4, 1e7, grain="class",
      applies_to="MOD-5 and DAT-1 cells"),
    S("mod5_km_nM", A, "nM", 500, 100, 2000, "human SERT Km 0.3-1 uM (homology); Ranganathan et al. 2001 J Neurosci "
      "21:5871 would pin MOD-5's", "inferred", applies_to="MOD-5 (SERT) cells"),
    S("dat1_km_nM", A, "nM", 1200, 500, 3000, "Jayanthi et al. 1998 Mol Pharmacol 54:601 (DAT-1 in transfected cells)",
      "measured", applies_to="DAT-1 cells"),
    S("ma_extrasyn_channels", A, "channels per cell", 200, 10, 2000, notes="MOD-1, LGC-55 or LGC-53 channels outside "
      "synapses on each expressing cell", grain="class"),
]
AMINE_PAIRS = (("serotonin", "ser-1"), ("serotonin", "ser-4"), ("serotonin", "ser-5"), ("serotonin", "ser-7"),
               ("dopamine", "dop-1"), ("dopamine", "dop-2"), ("dopamine", "dop-3"), ("dopamine", "dop-4"),
               ("octopamine", "octr-1"), ("octopamine", "ser-3"), ("octopamine", "ser-6"), ("tyramine", "ser-2"),
               ("tyramine", "tyra-2"), ("tyramine", "tyra-3"))                  # Bentley et al. 2016
for lg, rg in AMINE_PAIRS:
    t, lo, hi, src = 1000.0, 10.0, 1e5, "no EC50 retrieved"
    if rg == "ser-4":
        t, lo, hi, src = 1000.0, 100.0, 10000.0, "param_ranges D8 (guessed, typical GPCR)"
    elif rg == "dop-1":
        t, lo, hi, src = 500.0, 10.0, 5000.0, "param_ranges D9 (guessed)"
    SPECS.append(S(f"ma_ec50_{lg}_{rg}_nM", A, "nM", t, lo, hi, src, grain="pairing", applies_to=f"{lg} on {rg}"))
assert len({s.id for s in SPECS}) == len(SPECS)
assert set(GPCR_COUPLING) >= {r for _, r in PAIRS} | {r for _, r in AMINE_PAIRS}


class _Pool:
    """Molecules of each ligand in each compartment, exchanging between neighbours (exactly, by expm)."""

    def __init__(self, n_lig, V_um3, d_um, A_um2, D):
        self.V, m = np.asarray(V_um3, float), len(V_um3)
        self.N = np.zeros((n_lig, m))
        K = np.zeros((m, m))
        for k in range(m - 1):
            g = A_um2 * D / d_um[k]
            K[k, k] -= g / self.V[k]
            K[k + 1, k] += g / self.V[k]
            K[k + 1, k + 1] -= g / self.V[k + 1]
            K[k, k + 1] += g / self.V[k + 1]
        self.K, self._E = K, {}

    def mix(self, dt_s):
        E = self._E.get(dt_s)
        if E is None:
            E = self._E[dt_s] = expm(self.K * dt_s)
        self.N = self.N @ E.T

    def nM(self):
        return self.N / (NA_PL * self.V / 1000.0)


def _hill(c, ec50, h):
    ch = np.power(np.maximum(c, 0.0), h)
    return ch / (ch + np.power(ec50, h))


class Mech:
    def __init__(self, brain, params, toggles, expr_add=None):
        self.p = p = params
        self.brain = brain
        self.form = {k: form(toggles.get(k, "off")) for k in (P, A)}
        st = brain.st
        names, musc = list(brain.cell_names), np.asarray(brain.is_muscle, bool)
        n = self.n = len(names)
        self.names = names
        classes = set(st.cengen_classes)
        cls = [None if m else cengen_class(c, classes) for c, m in zip(names, musc)]
        add = EXPR_ADD if expr_add is None else expr_add

        def expr(g, c):
            return 1.0 if (cls[c], g) in add else st.expr(g, cls[c])

        self.neuron = ~musc
        neurons = [x for x, k in zip(st.names, st.kind) if k == "neuron"]
        yall = np.array([st.soma_y_um[st.index[x]] for x in neurons])
        self.edges = np.array([yall.min(), p["pc_head_end_y_um"], p["pc_vulva_y_um"], p["pc_tail_start_y_um"],
                               yall.max()], float)
        self.y = np.array([st.soma_y_um[st.index[c]] if not m else np.nan for c, m in zip(names, musc)])
        self.gate = np.array([[expr(g, c) > 0 for g in G_ALPHA] for c in range(n)], float)
        self.lumped = {k: v == "lumped" for k, v in self.form.items()}
        self.on = {k: v in ("compartments", "well_mixed") for k, v in self.form.items()}
        self.entries = []                                  # (cell, ligand row, ec50 nM, weights (3,), pool key)
        if self.on[P]:
            self.pep_comp, self.pep = self._pool(self.form[P] == "well_mixed", len(PRECURSORS),
                                                 p["pep_diffusion_um2_per_s"])
            tpm = np.array([[expr(g, c) if self.neuron[c] else 0.0 for g in PRECURSORS] for c in range(n)])
            tot = tpm.sum(1, keepdims=True)
            self.pep_share = np.divide(tpm, tot, out=np.zeros_like(tpm), where=tot > 0)
            self.pep_onehot = np.eye(self.pep.N.shape[1])[self.pep_comp]
            li = {g: k for k, g in enumerate(PRECURSORS)}
            for (pg, rg) in PAIRS:
                for c in range(n):
                    if self.neuron[c] and expr(rg, c) > 0:
                        self.entries.append((c, li[pg], float(p[f"pep_ec50_{pg}_{rg}_nM"]), self._w(rg), P))
        if self.on[A]:
            self.ma_comp, self.ma = self._pool(self.form[A] == "well_mixed", len(AMINES), p["ma_diffusion_um2_per_s"])
            self.ma_rel = np.array([[float(self.neuron[c] and lg in (st.transmitter.get(names[c]) or set()))
                                     for lg in AMINES] for c in range(n)])
            self.ma_onehot = np.eye(self.ma.N.shape[1])[self.ma_comp]
            self.uptake = {}                               # amine row: (cells, Km nM)
            for lg, gene in TRANSPORTERS.items():
                cells = np.array([c for c in range(n) if self.neuron[c] and expr(gene, c) > 0], int)
                self.uptake[AMINES.index(lg)] = (cells, float(p[f"{gene.replace('-', '')}_km_nM"]))
            for lg, rg in AMINE_PAIRS:
                for c in range(n):
                    if self.neuron[c] and expr(rg, c) > 0:
                        self.entries.append((c, AMINES.index(lg), float(p[f"ma_ec50_{lg}_{rg}_nM"]), self._w(rg), A))
            rp = mech.params_for(receptors, brain.spec)
            self.extrasyn = []                             # (amine row, cells, ec50 nM, hill, erev mV, gamma pS)
            for lg, rc in EXTRASYN.items():
                cells = np.array([c for c in range(n) if self.neuron[c] and
                                  receptors.class_tpm(st, cls[c], rc) > 0], int)
                self.extrasyn.append((AMINES.index(lg), cells, float(rp[f"rec_{rc}_ec50_uM"]) * 1000.0,
                                      float(rp[f"rec_{rc}_hill"]), float(rp[f"rec_{rc}_erev_mV"]),
                                      float(rp[f"rec_{rc}_gamma_pS"])))
            # in the brain: one wgc conductance per (channel, cell) at the soma, solved implicitly by NEURON; the
            # stand-in brain of the unit checks (no NEURON) injects the same conductance as an explicit current
            self.wgc = None
            if getattr(brain, "soma", None) is not None:
                h, self.wgc = brain.h, []
                for row, cells, ec50, hh, erev, gam in self.extrasyn:
                    pps = [h.wgc(brain.soma[c](0.5)) for c in cells]
                    pv = h.PtrVector(max(1, len(pps)))
                    for k, pp in enumerate(pps):
                        pp.e = erev
                        pv.pset(k, pp._ref_g)
                    self.wgc.append((pps, pv))
        e = self.entries
        self.e_cell = np.array([x[0] for x in e], int)
        self.e_lig = np.array([x[1] for x in e], int)
        self.e_ec50 = np.array([x[2] for x in e], float)
        self.e_w = np.array([x[3] for x in e], float).reshape(-1, 3)
        self.e_pep = np.array([x[4] == P for x in e], bool)
        self.reset()

    def _w(self, rg):
        f = GPCR_COUPLING[rg][0]
        return FAMILY.get(f, (self.p["gpcr_unknown_share"],) * 3)

    def _pool(self, one, n_lig, D):
        e = self.edges[[0, -1]] if one else self.edges
        L = np.diff(e)
        assert (L > 0).all(), e
        mid = (e[:-1] + e[1:]) / 2.0
        comp = np.clip(np.searchsorted(e, np.nan_to_num(self.y, nan=e[0]), side="right") - 1, 0, len(L) - 1)
        A_ = float(self.p["pc_cross_section_um2"])
        return comp, _Pool(n_lig, L * A_, np.diff(mid), A_, float(D) + float(self.p["pc_stirring_um2_per_s"]))

    def reset(self):
        n = self.n
        self.G = np.zeros((n, 3))
        self.q_pep, self.q_ma = np.zeros(n), np.zeros(n)
        if self.on[P]:
            self.pep.N[:] = 0.0
        if self.on[A]:
            self.ma.N[:] = 0.0
            self.store = self.ma_rel.copy()                # full stores at t = 0
            for pps, _ in getattr(self, "wgc", None) or ():
                for pp in pps:
                    pp.g = 0.0
        self.lc = {}
        L = getattr(self.brain, "layers", None)
        for k, key in ((P, "peptide"), (A, "monoamine")):
            if self.lumped[k]:
                self.lc[k] = np.zeros(getattr(L, key)[0].shape[1])

    def release_factor(self):
        p, G = self.p, self.G
        return (1 + p["release_gq_gain"] * G[:, 0]) * (1 + p["release_gs_gain"] * G[:, 2]) / \
            (1 + p["release_gi_gain"] * G[:, 1])

    def _lumped(self, k, v, dt):
        """brain_layers.Layers.modulator_current for one ligand class, unchanged."""
        L = self.brain.layers
        release, receptor, (ec50, lig) = L.peptide if k == P else L.monoamine
        vth, tau = ("pep_release_vth_mV", "pep_clear_tau_s") if k == P else ("ma_release_vth_mV", "ma_clear_tau_s")
        c = self.lc[k]
        r = _sig((v - L.p[vth]) / 5.0) @ release * dt / 1000.0
        c = c + r - c * dt / (1000.0 * L.p[tau])
        self.lc[k] = c
        occ = c[lig] / (c[lig] + ec50)
        return receptor @ occ

    def step(self, ctx, dt_ms):
        p, dt = self.p, dt_ms / 1000.0
        v = np.asarray(ctx.v, float)
        I = np.zeros(self.n)
        for k in (P, A):
            if self.lumped[k]:
                I = I + self._lumped(k, v, dt_ms)
        if not (self.on[P] or self.on[A]):
            return {"I_pA": I}
        R = self.release_factor()
        h = p["gpcr_hill"]
        occ = np.zeros(len(self.e_cell))
        out = {}
        if self.on[P]:
            pool = self.pep
            u = _sig((v - p["dcv_vhalf_mV"]) / p["dcv_k_mV"]) * self.neuron
            self.q_pep += (u - self.q_pep) * (1.0 - np.exp(-dt_ms / p["dcv_tau_ms"]))
            rate = p["dcv_rate_per_s"] * p["dcv_peptides_per_vesicle"] * self.q_pep * R
            src = (self.pep_share * rate[:, None]).T @ self.pep_onehot
            ext = 0.0
            for key, x in (ctx.outputs.get("peptide_release") or {}).items():
                g, _, cp = key.partition("@")
                if g in PRECURSORS:
                    row = PRECURSORS.index(g)
                    if cp and pool.N.shape[1] > 1:
                        src[row, COMPARTMENTS.index(cp)] += x
                    else:
                        src[row] += x * pool.V / pool.V.sum()
                    ext += x
            kcc = ctx.outputs.get("coelomocyte_uptake_per_s", p["pc_coelomocyte_uptake_per_s"])
            kcc = float(np.mean(kcc))
            pool.N = (pool.N + src * dt) * np.exp(-dt / p["pep_degrade_tau_s"] - dt * kcc)
            pool.mix(dt)
            c = pool.nM()
            m = self.e_pep
            occ[m] = _hill(c[self.e_lig[m], self.pep_comp[self.e_cell[m]]], self.e_ec50[m], h)
            out.update(pep_release_molecules_per_s=float(rate.sum()), pep_external_molecules_per_s=float(ext),
                       pep_total_molecules=float(pool.N.sum()), pep_max_nM=float(c.max()),
                       pep_n_receptor_sites=int(m.sum()))
            for g in ("flp-11", "flp-13", "flp-24", "pdf-1", "nlp-12"):
                if g in PRECURSORS:
                    out[f"{g.replace('-', '')}_head_nM"] = float(c[PRECURSORS.index(g), 0])
        if self.on[A]:
            pool = self.ma
            u = _sig((v - p["ma_vhalf_mV"]) / p["ma_k_mV"]) * self.neuron
            self.q_ma += (u - self.q_ma) * (1.0 - np.exp(-dt_ms / p["ma_tau_ms"]))
            R_ma = R
            for key in ("ma_release_scale", "ma_release_scale_slow"):   # per cell: row 24 pathogen learning; row 18
                ms = ctx.outputs.get(key)                                 # DAF-7 on RIM/RIC (slow_signalling)
                if ms is not None:
                    R_ma = R_ma * np.asarray(ms, float)
            J = self.ma_rel * (p["ma_release_per_s"] * self.q_ma * R_ma)[:, None] * self.store   # molecules/s
            cap = p["ma_store_molecules"]
            c = pool.nM()
            sink = np.zeros_like(pool.N)
            back = np.zeros_like(self.store)
            for row, (cells, km) in self.uptake.items():
                if not len(cells):
                    continue
                comp = self.ma_comp[cells]
                U = p["ma_uptake_vmax_per_s"] * c[row, comp] / (km + c[row, comp])
                tot = np.bincount(comp, U, minlength=pool.N.shape[1])
                scale = np.minimum(1.0, np.divide(pool.N[row], tot * dt, out=np.ones_like(tot), where=tot > 0))
                U = U * scale[comp]
                sink[row] = np.bincount(comp, U, minlength=pool.N.shape[1])
                back[cells, row] = U
            self.store = np.clip(self.store + dt * ((1.0 - self.store) / p["ma_synth_tau_s"] - J / cap
                                                    + back * self.ma_rel / cap), 0.0, 1.0) * self.ma_rel
            pool.N = np.maximum(pool.N + (J.T @ self.ma_onehot - sink) * dt, 0.0) * np.exp(-dt / p["ma_degrade_tau_s"])
            pool.mix(dt)
            c = pool.nM()
            bath = ctx.outputs.get("bath_amine_nM")        # mech/drugs: exogenous amine, uniform along the body
            if bath:
                c = c + np.array([bath.get(lg, 0.0) for lg in AMINES])[:, None]
            glia5 = ctx.outputs.get("glia_amine_nM")       # mech/glia_release: AMsh 5-HT, in the head compartment
            if glia5:
                c = c.copy()
                for lg, x in glia5.items():
                    c[AMINES.index(lg), 0] += x
            m = ~self.e_pep
            occ[m] = _hill(c[self.e_lig[m], self.ma_comp[self.e_cell[m]]], self.e_ec50[m], h)
            for k, (row, cells, ec50, hh, erev, gam) in enumerate(self.extrasyn):
                if len(cells):
                    g_nS = p["ma_extrasyn_channels"] * gam * 1e-3 * _hill(c[row, self.ma_comp[cells]], ec50, hh)
                    if self.wgc is None:
                        I[cells] += g_nS * (erev - v[cells])                      # nS x mV = pA
                    else:
                        self.wgc[k][1].scatter(self.brain.h.Vector(g_nS * 1e-3))   # uS
                    out[f"extrasyn_{N_EXTRA[row]}_max_nS"] = float(g_nS.max())
            for k, lg in enumerate(AMINES):
                out[f"ma_{lg}_max_nM"] = float(c[k].max())
                rel = self.ma_rel[:, k] > 0
                out[f"ma_{lg}_store_min"] = float(self.store[rel, k].min()) if rel.any() else 1.0
        # G proteins
        lg = np.log(np.maximum(1.0 - self.e_w * occ[:, None], 1e-12))
        target = 1.0 - np.exp(np.stack([np.bincount(self.e_cell, lg[:, f], minlength=self.n) for f in range(3)], 1))
        target *= self.gate
        tau = np.array([p["gq_tau_ms"], p["gi_tau_ms"], p["gs_tau_ms"]])
        self.G += (target - self.G) * (1.0 - np.exp(-dt_ms / tau))
        G = self.G
        nr = self.neuron
        out.update(gq_mean=float(G[nr, 0].mean()), gi_mean=float(G[nr, 1].mean()), gs_mean=float(G[nr, 2].mean()),
                   release_factor_min=float(R[nr].min()), release_factor_max=float(R[nr].max()))
        if "RIS" in self.names:
            out["ris_gi"] = float(G[self.names.index("RIS"), 1])
        return {"I_pA": I, "out": {"neuromod": out},
                "g_scale": {"release": self.release_factor(), "dens_nca": 1 + p["nca_gq_gain"] * G[:, 0],
                            "dens_irk": 1 + p["irk_gi_gain"] * G[:, 1], "dens_egl19": 1 + p["egl19_gs_gain"] * G[:, 2]}}
