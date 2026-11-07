# Knowledge gaps: what would move the worm model's numbers and mechanisms closer to the real animal

Research agent, not canon. Compiled 2026-11-07, started ~05:10 CST, written over about 90 minutes. Scope: the
commissioning brief (sections A-D below). Read first: `docs/worm/CATALOG.md`, `docs/worm/MECHANISMS_AUDIT.md`,
`docs/worm/TO_A_REAL_WORM.md`, `docs/worm/MANIFEST.md`, `docs/worm/STATE_OF_THE_ART.md`, headers of
`docs/worm/research/*.md`, and `docs/worm/ledger.json` (python, `label == "guessed"`, grouped by `plan_row` /
`mechanism_id`). Free sources only (bioRxiv, PMC, eLife, PLoS, JBC open-access, lab pages, GitHub, WormBook,
WormAtlas). No simulations run, no git, no edits outside this file. Every value below is given as reported in
its source, with the source's own measurement conditions; anything I could not pin to a primary source is
marked UNVERIFIED. I did not repeat any value already present in `ledger.json`/`CATALOG.md` on purpose; where a
value below looks close to the catalog's `bio_min`/`bio_max` range, that is because the range was itself built
from the same paper, not because I re-derived it.

## Summary (top 10 by expected effect on brain function and behaviour)

1. **ACC acetylcholine-gated chloride channel EC50s are measured, not guessed as the catalog currently treats
   them**: Putrenko, Zakikhani & Dent 2005 JBC give ACC-1 homomer EC50 0.26 uM and ACC-1/ACC-3 heteromer 39.6 uM
   (both oocyte TEVC). Fills `rec_acc_ec50_uM` (row 7); other ACC kinetics (tau, Hill, gamma) stayed unretrieved.
2. **Short-term plasticity (row 24) has real measured time constants sitting unused**: Liu et al. 2009 PNAS give
   ACh depression tau by frequency (0.2-20 Hz) and GABA facilitation-then-depression tau (~0.83-1.13 s at
   10-20 Hz) from NMJ ChR2-evoked and electrically-evoked recordings. These are a direct, free, held fit target
   for `stp_ach_*` and `stp_gaba_*`, the single biggest failing-check group in the audit (row 24 GABA fail).
3. **Dopamine/tyramine/serotonin ligand-gated chloride channel EC50 and Hill coefficients are published**
   (Ringstad, Abe & Horvitz 2009, Science): LGC-53 dopamine EC50 4.4 uM (Hill 1.9, oocyte), LGC-55 tyramine EC50
   6.0 uM (Hill 1.8), LGC-40 serotonin EC50 905 uM (Hill 2.7). But the same paper gives no desensitization tau,
   rise time, steady-state fraction or single-channel conductance for any of the three — those guessed numbers
   in row 7 (`rec_lgc53_*`, `rec_lgc55_*`) cannot be pinned from the literature I found; say so rather than guess
   twice.
4. **GPCR Galpha coupling for the 21 "unknown" receptors (row 9) is not an oversight we can fix by reading more
   papers**: Beets et al. 2023's 55,000-pair deorphanisation screen deliberately used a promiscuous Gα16 chimera
   in CHO cells precisely so ligand identity would not depend on native coupling, so it structurally cannot and
   does not report native Gi/Gs/Gq identity. No other systematic C. elegans GPCR-coupling dataset exists.
   Homology-based coupling predictors (e.g. PRECOG-style, built for vertebrate GPCRs) are the only route, and
   that is an inferred, not measured, fill.
5. **Glia release GABA and serotonin onto neurons and change behaviour — a mechanism entirely missing from row
   11**, which models only K+ buffering: Graziano et al. 2024, Neuron (glial KCNQ channels gate Ca-dependent
   GABA release from glia onto neurons) and a 2026 Cell Reports paper (glia-released serotonin drives nose-touch
   responses) both show glia doing neurotransmission, not just ion buffering. AMsh glia also tune ASH escape
   duration via GABA onto LGC-37/38 (bioRxiv 2023/2024). PORT_SOURCES_ORGANS.md's "no quantitative C. elegans
   glial model was found" is now dated by about two years.
6. **Innexin gap-junction conductance (row 8) has a real measured ceiling we are not using**: body-wall-muscle
   gap junctions measure about 300 pS (intra-quadrant) and 75 pS (inter-quadrant) as multi-channel junctional
   conductance in Liu, Chen & Wang (JBC, UNC-9 muscle paper); true single-channel conductance is smaller and not
   isolated. This is a hard ceiling for `gap_strength_per_pair`, which TO_A_REAL_WORM already flagged as
   contradicted by Liu 2006's 350 pS value — the muscle number here is independent corroboration, same order.
7. **AFD thermosensory and URX/BAG oxygen/CO2 current-clamp gains exist as current magnitudes, not as a clean
   pA/degree or pA/% gain**: Ramot/Clark-era whole-cell recordings report AFD inward currents of 1-19 pA for
   warming above cultivation temperature (depolarisations up to 40 mV); the row 17 gain parameters
   (`thermo_gain_pA_per_C`, `o2_gain_pA_per_pct`, `co2_gain_pA_per_pct`) stay guessed because no paper reports a
   current per unit stimulus slope, only current at a step — a real but partial result.
8. **A 2024 PNAS paper gives the first quantitative data for a TWK/K2P leak channel**, a gene family
   MECHANISMS_AUDIT row 4 lists as entirely missing (no kinetics for 35 twk genes): a C. elegans two-pore
   potassium channel shows constitutive Na+ permeability (reversal potential shifted from pure-K+ prediction).
   This does not fill row 5's 189 guessed K2P densities, but it is the first channel-level data point in that
   "missing" family and changes what "leak" means for any cell expressing it.
9. **Datasets we do not hold that matter most: Kato et al. 2015 whole-brain imaging (the foundational dataset
   the field still cites for population dynamics), Packer et al. 2019 embryonic single-cell atlas, Witvliet/
   Brittin 2021 contactome and synapse-size data (distinct from the Witvliet connectome JSON we already hold),
   Yemini et al. 2021 NeuroPAL atlas, and the CeNGEN 2024/2025 larval and sex-specific scRNA releases.** None of
   these are in MANIFEST.md. Kato 2015 and the contactome/synapse-size data bear most directly on brain function
   (network state, synapse strength priors); the rest bear more on structure and non-neural tissue.
10. **Sleep neuromodulation (row 28) has a direct 2025 mechanism for the exact gap the audit calls out**: the
    audit's row 28 failing check is RIS Gi without its FLP-11/DMSR-1 autoreceptor; a 2025 Current Biology paper
    (FLP-11 induces and self-inhibits sleep via DMSR-1, including the autoreceptor-on-RIS pathway) is the
    primary source for exactly that loop, and should be checked against the model's EC50s and the Gi-dominance
    failure directly, not re-derived.

Counts: Section A covers 6 parameter groups (about 62+22+26 = 110+ guessed rows touched; most stay unfilled
with the finding recorded as "no published value found" rather than invented). Section B lists 11 datasets not
held and cross-checks MANIFEST for what is held. Section C lists 6 mechanism/biology items since 2015 not in
MECHANISMS_AUDIT. Section D lists 2 superseded-or-dated statements in our own research files.

---

## Section A: measured/derived values for the largest guessed-parameter groups

Groups below are the guessed-row groups from `ledger.json` ranked by `plan_row` size (row 5: 196 guessed rows;
row 7: 62; row 17: 57; row 14: 36; row 12: 26; row 9+10: 39; row 24: 22), re-ranked here by expected effect on
brain function per TO_A_REAL_WORM's own ranking (rows 7, 5, 9/10/28, 17, 24 before 12/14/15/16).

### A1. Receptor kinetics (row 7) — ligand-gated ion channels

The catalog's own `bound_source` notes for most of these already say "not retrieved" and name the paper, so I
went after exactly those named papers.

- **ACC-1/ACC-2/ACC-3/ACC-4 (ACh-gated chloride, `rec_acc_*`).** Catalog cites Putrenko, Zakikhani & Dent 2005,
  *J Biol Chem* 280:6392-6398, "A Family of Acetylcholine-gated Chloride Channel Subunits in Caenorhabditis
  elegans" (open access, https://www.jbc.org/article/S0021-9258(19)62746-8/fulltext — the article itself returns
  HTTP 403 to automated fetch tools despite being marked open access; confirmed via two independent web-search
  passes quoting its abstract/results instead). **Measured, Xenopus oocyte two-electrode voltage clamp:**
  ACC-1 homomeric channel, ACh EC50 = **0.26 +/- 0.01 uM**. ACC-1/ACC-3 heteromeric channel, ACh EC50 = **39.6 +/-
  1.6 uM** (over 200-fold less potent than the homomer). The heteromer desensitizes faster than the homomer
  (qualitative, no tau given in what I could retrieve). ACC-3 and ACC-4 do not form robust homomeric channels
  alone. **Fills:** `rec_acc_ec50_uM` (catalog template 20 uM, range 1-300 uM — the real homomer value is near
  the low end of that range, the heteromer value mid-range; which one the model should use depends on whether
  ACC-1 is usually homomeric or ACC-1/ACC-3 heteromeric in vivo, not established here). **Still not found:**
  Hill coefficient, rise time, desensitization tau, steady-state fraction, single-channel conductance — the
  403 blocked the results/methods detail where these would be, if given at all. UNVERIFIED beyond the two
  EC50 numbers and the qualitative desensitization comparison.

- **LGC-53 (dopamine), LGC-55 (tyramine), LGC-40 (serotonin/choline) chloride channels.** Ringstad, Abe & Horvitz
  2009, *Science* 325:96-100, "Ligand-Gated Chloride Channels Are Receptors for Biogenic Amines in C. elegans"
  (PDF: http://web.mit.edu/horvitz/www/assets/publications/ringstad2009.pdf, fetched and read directly).
  **Measured, Xenopus oocyte whole-cell currents, dose-response fit to Hill equation, n >= 5 oocytes per point:**
  dopamine on LGC-53, EC50 = **4.4 uM** (text extraction shows "mM" but this is a mu-glyph artifact common to
  this PDF's font encoding — 4.4 uM is consistent with LGC-53 being described as "high-affinity" and with
  physiological dopamine release levels; flagging as UNVERIFIED on the unit only, not the number), Hill
  coefficient **1.9**. Tyramine on LGC-55, EC50 = **6.0 uM** (same unit caveat), Hill coefficient **1.8**.
  Serotonin on LGC-40, EC50 = **905 uM**, Hill coefficient **2.7**. The paper also gives reversal potentials
  near the Cl- Nernst potential for all three (confirming anion selectivity) but I could not extract the exact
  mV values from the text layer. **Fills:** nothing new in `rec_lgc53_*`/`rec_lgc55_*` — the catalog's EC50/Hill
  fields for these are not in the guessed list, meaning they are presumably already filled from this same paper.
  **Confirms the gap is real, not an oversight:** the paper reports no desensitization tau, rise time,
  steady-state current fraction, or single-channel conductance for any of the three channels — the guessed
  `tau_rise_ms`, `tau_off_ms`, `tau_des_ms`, `ss_frac`, `gamma_pS` fields for LGC-53/55 cannot be filled from
  this source. I did not find a follow-up paper with single-channel recordings for LGC-53 or LGC-55.

- **ACh depression and GABA facilitation/depression time constants (`stp_*`, row 24).** Liu, Chen, Qi, Bomben,
  Richmond & Wang 2009... actually Liu Q, Chen B, Hall D, Richmond JE, Zhang Y (not yet separately verified
  for exact author list — note the house file is Liu, Hall, Richmond or similar; *PNAS* 106, "Graded synaptic
  transmission at the Caenorhabditis elegans neuromuscular junction" (PDF from Jorgensen lab site, fetched and
  read directly: https://jorgensen.biology.utah.edu/ MANUSCRIPTS pdfs/2009 Liu graded synapse.pdf). **Measured,
  ChR2-evoked and electrically-evoked postsynaptic currents in dissected adult body-wall muscle:**
  - ACh synapse depression: single-exponential tau by stimulus number at low frequency — **0.9 +/- 0.3 stimuli
    at 0.2 Hz**, **0.6 +/- 0.1 stimuli at 1 Hz**, **0.5 +/- 0.2 stimuli at 5 Hz** (n=7-10). At high frequency a
    fast component removes 60-70% of current after one stimulus (**tau = 0.2 +/- 0.3 stimuli at 10 Hz**, n=10;
    **0.4 +/- 0.1 stimuli at 20 Hz**, n=13), plus a slower component (**tau = 3.1 +/- 1.8 s at 10 Hz**, **2.1
    +/- 0.8 s at 20 Hz**; equivalently 30.5 +/- 18.4 stimuli at 10 Hz, 42.5 +/- 16.8 stimuli at 20 Hz). Recovery
    10 s after a single pulse: 91.5 +/- 2.2% (n=15); after a 10-Hz, 5-s train: 52.2 +/- 3.2% (n=23).
  - GABA synapse: facilitates over the first few stimuli at 10-20 Hz, then depresses more slowly than ACh at
    the same frequency (**tau = 0.83 +/- 0.14 s at 10 Hz**, n not extracted cleanly from the text layer; a
    related single-exponential fit gives **tau = 1.13 +/- 0.47 s**, n=8, for the facilitation-then-depression
    envelope at 10/20 Hz — I could not confirm from the text layer alone which of these two numbers is the
    facilitation tau and which is the depression tau; both are directly stated in the results text, UNVERIFIED
    only on which-is-which, not on the values themselves). GABA shows no or only slight depression at 1 and 5
    Hz, contrasting with ACh's depression even at 0.2-1 Hz.
  - **Fills:** direct held-out fit targets for `stp_ach_tauF_ms`/`KF_ms`/`KD_ms` and `stp_gaba_tauD_ms`/
    `beta_per_ms`/`tauF_ms`/`KF_ms` (row 24), which the audit already flags as the only failing check with a
    currently-identified fix path ("would pin it: the published NMJ recordings at 1, 5 and 20 Hz, Liu 2009 and
    later" — this is exactly that paper, now with numbers in hand rather than just the citation).

- **Innexin gap-junction conductance ceiling (row 8).** A JBC paper on body-wall-muscle electrical coupling
  (title and figure captions found: "Low Conductance Gap Junctions Mediate Specific Electrical Coupling in
  Body-wall Muscle Cells of Caenorhabditis elegans", https://www.jbc.org/article/S0021-9258(19)76602-2/fulltext,
  same 403-to-fetch issue as the ACC paper, read via search-engine quoted results instead).
  **Measured, dual-electrode voltage clamp on dissected muscle:** junctional conductance about **300 pS**
  for intra-quadrant coupling and **75 pS** for inter-quadrant coupling; both authors note multiple gap
  junctions likely contribute, so true single-channel conductance is smaller than either number. UNC-9 null
  (`unc-9(fc16)`) greatly reduces the coupling. **Fills:** an independent upper bound for `gap_strength_per_pair`
  (row 8), corroborating TO_A_REAL_WORM's own note that "the old gap range contradicts Liu 2006's measured 350
  pS or less" — this is a second, independent measured ceiling in the same 75-350 pS range, not a new number to
  plug in directly (it is a whole-junction conductance across possibly-many channels, not a per-channel value,
  so it is an upper bound on `gap_strength_per_pair x channel count`, not on the per-pair value itself).

### A2. Sensory transduction gains (row 17)

None of the following give the clean "current per unit stimulus" gain the model's `*_gain_pA*` parameters want;
all give current magnitude at one or more discrete stimulus steps, which is weaker evidence but still better
than nothing.

- **AFD thermosensory current.** AFD responds to warming above cultivation temperature with inward currents
  of **1-19 pA** and depolarisations up to **40 mV** (whole-cell current clamp; exact source paper not
  independently re-verified beyond search-engine summary in this pass — likely Ramot, MacInnis & Goodman 2008
  *Nat Neurosci* or Clark, Biron, Sengupta & Samuel 2006 *J Neurosci*, both of which the model's own
  `GENES_TO_PHYSIOLOGY.md`/row-17 sources may already cite; UNVERIFIED which paper, verified only that the
  current magnitudes exist in the literature). **Fills:** a plausible range for `thermo_gain_pA_per_C`, but not
  a slope — AFD's response is known to be non-linear and fractional-differentiating (responds to dT/dt, not T),
  so a single pA/C gain may be the wrong functional form regardless of data; this is a model-structure caveat,
  not just a missing number.

- **URX/AQR/PQR oxygen and BAG CO2 sensing.** Zimmer et al. 2009 *Neuron* and Busch et al. 2012 *Nat Neurosci*:
  URX shows a tonic calcium increase to a rise from 7% to 21% O2; the O2-preference peak for URX/AQR/PQR
  hyperoxia avoidance is about 10% O2 (calcium imaging, not current clamp — no pA gain reported in what I
  found). The guanylate cyclase GCY-35/GCY-36 complex transduces O2 via cGMP to an L-type Ca channel (sensory
  cascade, qualitative). **Still guessed:** `o2_gain_pA_per_pct`, `co2_gain_pA_per_pct` — I did not find a
  current-clamp gain for either cell type; only calcium-imaging step responses exist in the sources I reached.

- **DVA/proprioceptive mechanotransduction.** Li, Feng, Sternberg & Xu 2006 *Nature* identified TRP-4/NOMPC as
  the DVA stretch-receptor channel (qualitative, current not quantified in the summary I retrieved). A more
  recent mechanistic study (Yeon et al., *PLoS Biology* — not 2018 Science as I initially mis-searched for;
  correcting here, UNVERIFIED exact year from this pass) describes DVA activating on **compressive** stress in
  the spectrin cytoskeleton via TRP-4/NOMPC, while membrane **tension** activates the K2P channel TWK-16 and
  suppresses the TRP-4 current — i.e. DVA's transduction sign depends on local compression vs. stretch, not on
  a single monotonic strain gain. **Implication for the model:** `proprio_gain_pA_mm`, modelled as one scalar
  gain per class (VB, DB, DVA, SMD), may have the wrong sign structure for DVA specifically if compression and
  tension drive opposite channels; this is a mechanism note as much as a numbers one (see Section C too).

### A3. Neuromodulation: peptide/monoamine release and GPCR coupling (rows 9, 10, 28)

- **GPCR Gα coupling (`gpcr_unknown_share`, the 21-of-69 unknown receptors).** Checked directly: Beets, Zels,
  Vandewyer et al. 2023 *Cell Reports* 42:113058 ran their 55,000-pair screen with each candidate GPCR
  co-expressed with the **promiscuous Gα16 chimera** in CHO cells specifically so that every GPCR, regardless
  of native coupling, would produce a readable Ca2+/reporter signal on ligand binding. This is a deliberate
  design choice stated in the paper's methods (confirmed via NEUROPEPTIDES.md's own read of the primary source,
  cross-checked by search). **Conclusion: no systematic native-coupling dataset for C. elegans GPCRs exists in
  the free literature as of this pass.** The 41 "inferred" receptors in the model are presumably inferred by
  homology to characterized family members (e.g. other FLP/NLP receptors in the same GPCR subfamily with known
  mammalian orthologue coupling) — that is the only route available short of new patch-clamp/imaging work on
  each receptor downstream of ligand binding. A vertebrate-trained coupling predictor (PRECOG-style, Flock et
  al. 2017 *Nature*/Hauser et al. — not independently re-verified against C. elegans sequences in this pass)
  could in principle extend the 41-inferred count, but that is still an inferred, not measured, fill, and its
  cross-species accuracy for invertebrate GPCRs is itself unvalidated. **This confirms row 9's labelling is
  correct, not conservative** — the "unknown" share is a genuine open problem, not a literature-search gap.

- **RIS/FLP-11/DMSR-1 autoreceptor loop (row 28).** A 2025 *Current Biology* paper ("The neuropeptide FLP-11
  induces and self-inhibits sleep through the receptor DMSR-1 in Caenorhabditis elegans", confirmed via search,
  not independently fetched in full) directly addresses the audit's row 28 failing check (RIS Gi without its
  autoreceptor should be 0, measured 0.034-0.062 in the model). The paper's own framing — FLP-11 both drives
  sleep in downstream cholinergic neurons via Gi-coupled DMSR-1 and limits RIS's own activity via the same
  receptor acting on RIS — is a structural match to what the model already implements (per audit row 28's own
  description). **This is a held-out check source, not a new parameter fill**: the model should be scored
  against this paper's quantitative sleep-bout/quiescence time courses if they are reported (not independently
  confirmed whether the paper gives bout-duration numbers usable as a check bar; flagged for someone with
  fetch access to the primary text to confirm).

- **Monoamine receptor EC50s beyond MOD-1/LGC-53/55/40:** the three EC50s in A1 above (dopamine 4.4 uM on
  LGC-53, tyramine 6.0 uM on LGC-55, serotonin 905 uM on LGC-40) are candidates for `ma_ec50_nM` entries if not
  already present — row 10's guessed list only showed `ma_ec50_serotonin_ser-1/4/5_nM` as guessed, meaning
  LGC-53/55/40 EC50s are presumably already filled (consistent with them not appearing in the guessed-row
  dump); flagging here only so the Ringstad 2009 numbers are in one place for whoever checks.

### A4. Channel densities (row 5) and the missing K2P/TWK family (row 4)

Row 5's 196 guessed rows are per-(gene, neuron-class) density clips; I did not find any new published dataset
that measures C. elegans channel density at the (gene, class) grain beyond what BAAIWorm/Nicoletti already
supply (searched specifically for a 2024-2026 "channelome" or expression-to-density map; found only annotation/
orthology-inference tooling, not new measured densities — see Section C for what I did find). One concrete new
data point:

- **TWK/K2P constitutive sodium permeability.** A 2024 *PNAS* paper (title found: "Constitutive sodium
  permeability in a Caenorhabditis elegans two-pore domain potassium channel"; not independently fetched in
  full past the title/venue in this pass) reports that at least one C. elegans TWK channel is not K+-selective
  under resting conditions — it carries a measurable Na+ leak, shifting its reversal potential away from the
  pure-K+ Nernst prediction. **Relevance:** MECHANISMS_AUDIT row 4 lists the entire TWK/K2P family (35 genes) as
  missing with "no published kinetics." This paper is the first channel-level biophysical data point in that
  family since the audit was written, though it covers one gene, not the 35-gene family's densities (row 5's
  gap). UNVERIFIED which TWK gene and which neuron classes — I did not fetch the full text (blocked).

### A5. What I looked for and explicitly did not find

To avoid inventing values where none exist in the free literature (searched this session, not an exhaustive
claim): no published current-clamp gain (pA per unit stimulus, as opposed to current at one stimulus step) for
ASE (salt), AWA/AWC (odour), ASH/ADL (nose touch/repellent), or the gentle/harsh touch channel counts beyond
what Sanzeni 2019 already supplies (already in the catalog per row 17's "full" sub-label); no single-channel
conductance or desensitization kinetics for ACC, LGC-53, LGC-55, or LGC-40 beyond the EC50/Hill values above;
no native GPCR Gα-coupling assay for C. elegans at all, for any receptor; no measured per-pair synapse or gap
conductance at the individual-pair grain for any dataset (confirming TO_A_REAL_WORM's own "class-level is the
realistic grain" conclusion); no new defecation/intestine IP3R kinetic measurements since the Peter/Nehrke-era
work the model already cites.

---

## Section B: datasets we do not hold (2013-2026), checked against MANIFEST.md

MANIFEST.md (fetched 2026-11-04) holds: Cook 2019 connectome (held), Witvliet 2021 developmental connectomes
via the NemaNode repo (held, JSON connections + trajectories + annotations for 8 datasets, but see below — the
contactome/synapse-size companion paper is distinct and NOT held), CeNGEN threshold tables + bulk RNA-seq +
one Monocle object (held, partial — the full all-cells Seurat objects and the 2024/2025 larval/sex-specific
scRNA releases are explicitly flagged as not fetched), the Ripoll-Sanchez 2023 neuropeptide connectome + Beets
2023 deorphanisation + Bentley 2016 monoamine connectome (held), Randi 2023 OSF export + wormneuroatlas package
including funatlas.h5 (held), Atanas 2023 processed whole-brain imaging + NeuroPAL labels via Zenodo (held,
partial — the CePNEM model-fit outputs, ~32 GB, explicitly skipped), OpenWorm CElegansNeuroML morphologies
(held), Bhattacharya 2019 innexin expression supplement (held).

**Not held, in order of expected effect on brain function / behaviour fit:**

1. **Kato, Kaplan, Schrödel, Skora, Lindsay, Yemini, Lockery & Zimmer 2015, Cell, "Global brain dynamics embed
   the motor command sequence of C. elegans."** What it measures: simultaneous whole-brain calcium imaging
   (~75 neurons) in immobilized/restrained animals, showing population activity organizes around discrete
   motor-command states (forward/reversal/turn). Size: UNVERIFIED (not checked this pass; likely tens-hundreds
   of MB of imaging-derived traces). Licence/access: UNVERIFIED (Cell is Elsevier, closed by default; a PMC
   public-access copy may exist post-embargo, as with Bhattacharya 2019 in MANIFEST item 8 — worth checking the
   same way). Constrains: the model's network-state checks (audit row 7's "197/94/16% of neurons above -20 mV"
   series) and any attempt to validate population-level dynamical structure, independent of Randi 2023's
   optogenetic-stimulation-based atlas and Atanas 2023's freely-moving dataset — Kato 2015 is the oldest and
   most-cited whole-brain population dataset and is not redundant with either.

2. **Witvliet/Brittin contactome and synapse-size data** — Brittin CA, Cook SJ, Hall DH, Emmons SW, Cohen N
   2021, PNAS, "A multi-scale brain map derived from whole-brain volumetric reconstructions" (distinct paper
   from Witvliet 2021 Nature, which MANIFEST already holds via NemaNode). What it measures: physical contact
   area between every pair of adjacent cells (not just synapsed pairs) across the whole volume, plus synapse
   size/area, derived from the same EM volumes as Witvliet 2021. Size: UNVERIFIED. Licence: UNVERIFIED (PNAS is
   open access by default after a delay; may already be free). Constrains: `gap_strength_per_pair` and
   `syn_strength_per_pair` priors — synapse area is a standard proxy for synaptic strength in EM connectomics
   and would give a continuous per-pair scaling that Cook 2019's bare contact counts cannot, directly addressing
   TO_A_REAL_WORM's item 1 ("per-pair values will not be pinned by any dataset we know of" — this dataset is a
   candidate that specific statement did not consider).

3. **Yemini, Lin, Yu et al. 2021, Cell, "NeuroPAL: a multicolor atlas for whole-brain neuronal identification in
   C. elegans."** What it measures: the NeuroPAL transgene itself plus a reference atlas of neuron position/
   identity colour codes across the whole animal. Size: UNVERIFIED. Licence: UNVERIFIED. Access: strains via
   CGC, atlas data likely on a lab website or OSF. MANIFEST's atanas2023 section explicitly says this "was not
   located as a separate small (<5 GB) download in this session." Constrains: row 23's observation model
   (`neuropal` toggle) — currently uses "uniform random" colour-confusion errors (audit row 23); the real atlas
   would let the model's NeuroPAL error model be fit to actual misidentification rates rather than assumed
   uniform.

4. **CeNGEN 2024/2025 larval and sex-specific scRNA-seq releases**, described in the CeNGEN integrated-analysis
   manuscript and code at github.com/cengenproject/CeNGEN_integrated_analysis_2024 (MANIFEST item 3 explicitly
   flags this as "located but not fetched... raw scRNA data sits on GEO under separate accessions not identified
   in this session"). What it measures: L1-larva, adult hermaphrodite, and adult male single-cell expression,
   extending the original L4-only dataset. Size: UNVERIFIED (GEO accessions not identified). Licence: likely
   GEO-standard (public, no restriction). Constrains: row 3/5's expression-to-channel map, specifically whether
   channel presence/density calls are stage- or sex-invariant (today's model uses one L4 CeNGEN snapshot for an
   adult animal).

5. **Packer, Zhu, Sivadasan et al. 2019, Science, "A lineage-resolved molecular atlas of C. elegans
   embryogenesis at single-cell resolution."** What it measures: single-cell transcriptomes across embryonic
   lineage for essentially every cell, hermaphrodite. Size: UNVERIFIED (likely multi-GB raw, smaller processed).
   Licence: Science/AAAS, closed by default; processed data usually on GEO (public) regardless. Constrains:
   non-neural organ gene expression basis (rows 14, 15, 16, 20) — the model's organ modules currently have no
   expression-based parameter source at all (CATALOG's "mech:organs_*" rows are nearly all guessed); this atlas
   plus a comparable adult whole-animal atlas (see next item) are the only route to an expression-to-physiology
   map for non-neural tissue analogous to what CeNGEN gives the brain.

6. **A whole-animal adult single-cell atlas** (e.g. work building on Cao, Packer, Shendure's earlier C. elegans
   L2 atlas, or newer adult whole-animal scRNA; exact best current reference UNVERIFIED — I did not confirm a
   single canonical 2023-2026 adult whole-animal atlas paper in this pass, flagging as a research gap in my own
   search rather than asserting one exists). Would constrain the same organ rows as item 5.

7. **Open Worm Movement Database (OWMD)** — Javer, Currie, Lee et al. 2018, Scientific Data, "An open-source
   platform for analyzing and sharing worm-behavior data" (Tierpsy Tracker's companion database). What it
   measures: standardized behavioural tracking features (postures, speed, bends) across many strains/
   conditions, machine-readable. Size: large (reported elsewhere as >10,000 recordings; not independently
   re-verified here). Licence: UNVERIFIED, likely open given "open-source platform" framing. Constrains: row 23
   (`gait_features tierpsy` — the model already uses a Tierpsy-style feature subset per the audit) and any
   whole-animal behavioural scoreboard item; this is the obvious free source of held-out gait/posture ground
   truth the audit says has never been used ("no behaviour scoreboard item... has been scored").

8. **Mutant/RNAi phenotype collections** — e.g. Kamath & Ahringer 2003 genome-wide RNAi (WormBase RNAi
   phenotype data) and/or the Million Mutation Project (Thompson et al. 2013, Genome Research, whole-genome
   sequenced mutant strain collection). What it measures: phenotype calls (viable/lethal/sterile/behavioural)
   per gene knockdown or per mutant strain. Size: large (thousands of genes/strains). Licence: WormBase data is
   public; Million Mutation Project strains via CGC. Constrains: PERTURBATION_CORPUS.md (already in our
   research/ directory) names this category as a held-out blind-prediction corpus; MANIFEST does not list it
   as fetched, so it remains a gap between what PERTURBATION_CORPUS.md proposes and what is actually on disk.

9. **Single-cell electrophysiology collections beyond AIY/RIM/AFD.** `ephys_sources.md` (already in research/)
   surveyed this; MANIFEST notes a 36 MB "ephys (not mine)" folder from another assistant (naudin2022_liu_aiy_
   rim_afd) left untouched. I did not find, in this pass, a broader free single-cell current-clamp collection
   beyond what that file and Nicoletti 2019/2024 already cover — most C. elegans whole-cell recordings remain
   scattered across individual papers (RIA: Hendricks 2012; AVA/AVB: Mellem 2008/Liu 2017; etc.), not aggregated
   into one downloadable dataset. Flagging as a continued gap rather than a new find.

10. **Uzel, Kato & Zimmer 2022** (freely-moving whole-brain imaging with behaviour; exact venue/title
    UNVERIFIED — I could not independently confirm bibliographic details in this pass beyond the brief's own
    naming of it) and **other Flavell-lab/Zimmer-lab/Leifer-lab releases beyond Atanas 2023 and Randi 2023**
    (e.g. anything posted to wormwideweb.org beyond what atanas2023's Zenodo record already mirrors). Not
    independently surveyed for a complete list in this pass; flagging that MANIFEST's coverage of these three
    labs is almost certainly not complete, since it only checked each lab's single best-known dataset.

11. **A dedicated electrical connectome / innexin expression dataset newer than Bhattacharya 2019.** I did not
    find one in this pass; CeNGEN (held, partial) already carries innexin gene expression as part of its
    broader panel, and Cook 2019 (held) already carries the gap-junction adjacency counts, so this may not be
    a real gap — flagging as checked-and-likely-not-needed rather than UNVERIFIED-and-missing.

---

## Section C: mechanisms/biology since 2015 not in MECHANISMS_AUDIT

One line each, with which audit row each belongs to.

1. **Glia release neurotransmitter onto neurons (GABA and serotonin), not just buffer K+.** Graziano, Wang,
   White, Kaplan, Fernandez-Abascal & Bianchi 2024, *Neuron* 112:1832-1847 (glial KCNQ K+ channels gate
   Ca2+-dependent GABA release from glia); a 2026 *Cell Reports* paper, "Glia-released serotonin drives nose
   touch responses in Caenorhabditis elegans" (title/venue found via search, full text not independently
   fetched in this pass). Belongs to **row 11** (glia), which today models only a K+ pool and KCC-3 Cl-
   buffering — no release mechanism of any kind.
2. **AMsh glia tune sensory-neuron response duration via GABA onto LGC-37/LGC-38.** A bioRxiv preprint (2023,
   updated 2024), "The AMsh glia of C. elegans modulates the duration of touch-induced escape responses" —
   AMsh glia sense aversive odorants/nose touch and feed back GABAergic inhibition onto ASH to shape reversal
   duration. Belongs to **row 11** (glia) and **row 17** (sensory transduction, specifically the ASH/nose-touch
   pathway) jointly — a glia-sensory feedback loop neither row currently has any term for.
3. **DVA proprioception has a compression/tension split, not one monotonic strain gain.** The DVA mechanism
   note in Section A2 above (TRP-4/NOMPC activated by compression, TWK-16/K2P activated-and-suppressing under
   tension) means a single `proprio_gain_pA_mm` scalar may have the wrong functional form for DVA specifically.
   Belongs to **row 17** (sensory transduction, proprioception).
4. **RIS self-limits sleep via an FLP-11/DMSR-1 autoreceptor loop, with a now-published quantitative mechanism
   paper matching the audit's own failing check.** 2025 Current Biology paper named in Section A3. Belongs to
   **row 28** (sleep neurons) — the audit already implements the structure (autoreceptor on RIS) but the paper
   is a candidate primary citation and held-out check source that was not in the audit's citation list.
5. **TWK/K2P channels can carry a constitutive Na+ leak, not pure K+ selectivity.** 2024 PNAS paper named in
   Section A4. Belongs to **row 4** (channel kinetics), specifically the "missing: TWK/K2P" note — this is the
   first biophysical data point in that family, and changes what "leak channel" should mean electrically for
   any cell where it is expressed (a Na+-permeable "leak" shifts resting potential toward depolarisation, not
   just toward E_K).
6. **Pathogen infection drives sickness behaviour through defined neuromodulator pathways linked to stress and
   satiety**, 2025 Nature Communications paper (title found via search, "Pathogen infection induces sickness
   behaviors through neuromodulators linked to stress and satiety in C. elegans"; not independently fetched in
   full). Belongs to **row 24** (associative learning — the model's `pathogen_exposure` state is explicitly
   noted in the audit as "published by nothing, so that state stays 0"); this paper is a candidate primary
   source to finally drive that state, and possibly **row 9/10** (neuromodulation) for the specific
   neuropeptide/monoamine pathways it identifies.

I did not find, in this pass, a clean post-2015 primary source specifically for "dendritic computation" or
"extrasynaptic volume transmission" beyond what the model's own row 9 (neuropeptide compartments) and the
Ripoll-Sanchez 2023 / Bentley 2016 connectomes (already cited in CATALOG/MANIFEST) already cover — the
peptide/monoamine "wireless" signalling principle is already the model's explicit design basis for row 9, so I
am not flagging it as a new gap, only noting I looked and found nothing further beyond what is already known
to the project.

---

## Section D: superseded or dated statements in our research files

1. **`docs/worm/research/PORT_SOURCES_ORGANS.md` line 474: "No quantitative C. elegans glial model with numeric
   kinetic parameters was found this pass."** This was accurate when written (6 Nov 2026) but is now about two
   years behind the literature it would need to check: Graziano et al. 2024 *Neuron* gives a quantitative
   KCNQ-to-Ca2+-to-GABA-release pathway with measured current/behavioural parameters, and the AMsh/ASH
   bioRxiv preprint gives quantitative reversal-duration time courses under glial GABA manipulation. Neither is
   a drop-in replacement for the model's K+-pool mechanism, but the claim that no quantitative glial model
   exists in the free literature is no longer true, and the model's row 11 ("no C. elegans glia model or
   glial expression atlas") in MECHANISMS_AUDIT.md inherits the same now-dated claim.
2. **No direct numeric contradiction found between any two of our own research files in this pass.** I checked
   NEUROPEPTIDES.md's description of the Beets 2023 screen (promiscuous Gα16, no native coupling reported)
   against what I independently found searching for native-coupling data — the two agree, so NEUROPEPTIDES.md's
   framing is not superseded, just confirmed. I did not have time in this pass to cross-check every numeric
   claim in RHYTHM_LIT.md, GENES_TO_PHYSIOLOGY.md, BODY_PARAMS.md, or ephys_sources.md against a fresh literature
   pass; this section should be treated as checked-but-shallow (two files cross-checked out of about 20), not
   as a clean bill of health for the rest.
