# Param ranges notes (C. elegans whole-animal model, adult N2 hermaphrodite)

Companion notes for `param_ranges.csv`. Written 2026-11-05. Covers (1) one-line reasoning for every
row labelled "guessed", and (2) the two required Q&A items. Did not spawn subagents, per instruction.

Search budget used: roughly 36 of the ~40-lookup budget (WebSearch calls plus one blocked WebFetch to
a Cell.com Previews PDF, HTTP 403). Stopped at that point to write up rather than keep spending budget.

## 1. Q&A

### Q1: Wen et al. 2012 Neuron 76:750 - direction of the proprioceptive drive, and receptive field

**Answer, with the caveat below:** curvature in an ANTERIOR body region drives bending in the region
POSTERIOR to it. Each B-type motor neuron (VB/DB) senses stretch/curvature over a receptive field that
extends roughly half a body length ANTERIOR to its own neuromuscular junction, and uses that anterior
curvature signal to drive contraction at its own, more posterior, junction. This is the mechanism that
propagates the bending wave from head to tail during forward crawling and swimming: each segment copies
the curvature of the segment ahead of it with a short delay, so the wave looks like it travels posteriorly
even though no single global pacemaker is driving it from the head. This matches the paper's conclusion
that proprioceptive coupling WITHIN the motor neuron pool (not just from premotor interneurons) is what
sets wave propagation direction and velocity.

**Caveat on this answer:** this was read from a WebSearch snippet summarizing the paper's abstract/findings,
not the primary PDF. A direct WebFetch of the Cell.com "Previews" piece on this paper returned HTTP 403
(blocked) this session, so the exact receptive-field length (whether it is ~0.5 body lengths, ~10 muscle
segments, or some other specific figure) was not independently re-verified against the primary text. The
row J12 in the CSV and the direction/mechanism claim above should both be confirmed against the primary
Wen et al. 2012 PDF or a reliable secondary source (e.g. Boyle, Berri & Cohen 2012's follow-up model, which
assumes the same anterior-sensing, posterior-driving architecture) before being treated as fully measured.

### Q2: neurotransmitter atlas by neuron class (CeNGEN / Cook 2019)

A single published atlas matching exactly this description exists: **Wang, Vidal, Witvliet et al. 2024,
"A neurotransmitter atlas of C. elegans males and hermaphrodites," eLife 13:e95402**
(https://elifesciences.org/articles/95402; also on PMC as PMC11488851). It reports, across identified
neuron classes in both sexes: about one quarter of neurons glutamatergic (eat-4/VGLUT-positive), a little
more than half cholinergic (unc-17/VAChT-positive), around 10% GABAergic (unc-25/GAD-positive), and about
another 10% monoaminergic (cat-1/VMAT-positive). It also reports novel glial/non-neural expression and
candidate betaine- and exclusively-peptidergic neurons, and documents frequent co-transmission (most often
a fast transmitter, ACh or glutamate, paired with a monoamine).

Downloadability: the paper's own supplementary files are downloadable from the eLife article page in the
usual way (source data / supplementary tables attached to the article). In addition, the hermaphrodite
dataset is mirrored as a structured, directly downloadable dataset in the OpenWorm Connectome Toolbox at
https://openworm.org/ConnectomeToolbox/Wang2024Herm_data/, which is likely the more convenient route for a
per-neuron-class table. I did not fetch either the eLife supplementary files or the OpenWorm mirror
directly this session (only the search snippets describing them), so the exact table schema and the
male-specific mirror were not independently verified; this should be checked before the project relies on
a specific file.

## 2. Guessed rows, one-line reasoning each (46 of 107 rows)

- **A2** (Total plasma membrane surface area per neuron): No whole-cell surface-area survey located for C. elegans neurons. Soma ~2-5um diameter (~20-80um2); many classes add long thin (~0.1-0.5um) neurites up to ~1mm, adding large unmeasured area. Range is a physically motivated guess, not a citation.
- **A6** (Intracellular axial resistivity (Ra)): NEURON-model convention for fine invertebrate/vertebrate neurites; no direct C. elegans measurement located this session. Nicoletti 2019/2024 model files (code only) were not fetched and may contain a fitted value; flagged for follow-up.
- **B12** (NMJ synaptic release latency (stimulus to EPSC onset)): No explicit latency value surfaced in available search snippets. Range guessed from generic fast chemical synapse latency (sub-ms to a few ms) as a physical-limit-type bound.
- **C1** (UNC-9/UNC-7 innexin single-channel conductance): Search did not surface a direct patch-clamp single-channel conductance for UNC-9/UNC-7 innexin hemichannels. Range guessed from the broader innexin/connexin single-channel literature (tens to a few hundred pS). Flag for a targeted fetch of Starich et al. 2009 primary data.
- **C4** (Conductance per single EM-reconstructed gap-junction contact): No direct measurement of per-contact conductance located. Guessed by dividing a plausible macroscopic coupling conductance (C2) by a typical number of EM gap-junction contacts per coupled pair (often several, per the Cook 2019 connectome).
- **C5** (RMG hub-neuron gap-junction coupling conductance (RMG-ASH/ADL/URX)): RMG is a densely gap-junction-coupled hub in the npr-1 social-feeding circuit (Macosko et al. 2009 Nature) but no quantitative coupling conductance was retrieved this session; guessed in the same range as C2.
- **C6** (ASH-ADL gap-junction coupling conductance): Same caveat as C5; guessed by analogy to other identified-pair coupling conductances.
- **D3** (Pseudocoelomic neuropeptide diffusion coefficient): NEUROPEPTIDES.md already flags this as inferred from generic peptide biophysics in other systems, not measured for worm pseudocoelomic fluid; carried over unchanged.
- **D4** (Neuropeptide extracellular clearance/degradation time constant): No C. elegans peptidase-kinetics measurement located. Range guessed from generic neuropeptidase turnover in other invertebrates/vertebrates (seconds to minutes).
- **D5** (Monoamine (5-HT/DA/TA/OA) synaptic clearance time constant via transporters (MOD-5/DAT-1/etc)): NEUROPEPTIDES.md already notes monoamine transporter kinetics (cat-1/VMAT, dat-1/DAT) were not retrieved. Range guessed from generic monoamine transporter turnover rates in other systems.
- **D8** (SER-4 metabotropic serotonin receptor EC50): SER-4 is named among C. elegans serotonin GPCRs (SER-1/4/7) but a specific EC50 was not retrieved. Range guessed as typical GPCR-amine affinity (sub-uM to low-uM), consistent with the Beets 2023 submicromolar-median finding (D1/D2).
- **D9** (DOP-1 dopamine receptor EC50): Not retrieved this session; guessed the same way as D8.
- **D11** (FLP-11 sleep-induction time course): NEUROPEPTIDES.md notes FLP-11/DMSR-1 induces and self-limits sleep (lethargus quiescence bouts); exact release/clearance kinetics not found, guessed from quiescence bout durations reported in the lethargus literature.
- **E1** (Amphid sheath glia extracellular K+ buffering (concentration change)): No C. elegans-specific extracellular K+ buffering measurement located this session. Range guessed from generic glial K+ buffering in other invertebrate/vertebrate systems.
- **E2** (KCC-3 co-transporter contribution to AFD microvilli ion homeostasis): KCC-3 (K-Cl cotransporter) is implicated in AFD sensory-ending ion homeostasis (Procko et al. 2011) but no numeric flux/concentration value was retrieved; left qualitative rather than inventing a number.
- **E3** (Amphid sheath glial GABA release magnitude/effect on neighboring neurons): Sheath glia have been reported to release GABA/signaling molecules but no quantitative release-rate number was found; flagged qualitative only, per the rule against inventing a number.
- **F3** (Body-wall muscle action potential duration): Gao & Zhen 2011 and Liu et al. 2011 J Physiol likely report AP duration directly, but it did not appear in the retrieved search snippets. Range guessed from the slow, plateau-like Ca-AP waveform described (tens to a couple hundred ms), pending a primary-text check.
- **F4** (Body-wall muscle intrinsic AP/bursting frequency): Not directly retrieved; guessed in rough correspondence with measured crawling bend frequency (0.3-0.5Hz, project STATE_OF_THE_ART.md) since BWM activity paces the bend cycle.
- **F5** (Body-wall muscle whole-cell capacitance): Not found in available snippets. Guessed from typical small-invertebrate-muscle-cell capacitance scaled to BWM spindle-shaped cell size (roughly 50x100um).
- **F6** (Body-wall muscle whole-cell input resistance): Not found in available snippets. Guessed as lower than neuronal input resistance (A3) because muscle cells are larger and electrically coupled to neighbors via UNC-9 gap junctions.
- **F7** (Excitation-contraction coupling Hill coefficient (Ca2+ to force)): Not found for C. elegans BWM specifically this session. Range guessed from generic striated/obliquely-striated muscle Ca-force Hill coefficients (1-4) reported across invertebrates.
- **F8** (Muscle force rise time): Fang-Yen 2010 and Petzold 2011 are the named sources but their specific force-kinetics numbers were not retrieved via search snippet this session. Range guessed from the measured bend-cycle period (~2-3s crawling) assuming rise is a fraction of the cycle.
- **F9** (Muscle force decay/relaxation time): Same caveat as F8.
- **F10** (Maximum body-wall muscle force (single cell or whole-animal bend)): Fang-Yen 2010/Petzold 2011 report whole-animal bending force/torque but it was not retrieved numerically this session. Range guessed loosely from project BODY.md mechanical-stiffness numbers (muscle layer 600-850kPa) combined with rough cross-section; downgraded to guessed because the arithmetic chain was not actually carried out with cited numbers.
- **F11** (Body-wall muscle UNC-9 gap-junction coupling conductance between neighboring cells): Paper title and existence confirmed; the actual coupling-conductance number was not present in the retrieved search snippet. Range guessed in line with other gap-junction estimates (C2).
- **G6** (MC neuron to pm synaptic latency via EAT-2): EAT-2 is the pharynx-specific nAChR subunit at the MC-pm synapse (Raizen 1995 Genetics; McKay 2004). A specific latency number was not retrieved this session; range guessed from generic fast cholinergic synaptic latency.
- **G7** (M3 neuron termination of pharyngeal pump via AVR-15 glutamate-gated Cl current): Dent, Smith, Vassilatis & Avery 2000 PNAS identify AVR-15 as mediating M3's fast inhibitory termination of the pump. A specific timing number was not retrieved this session; range guessed as a fraction of the overall pump cycle (G3).
- **H2** (pBoc (posterior body-wall muscle contraction) step duration): The three-step program (pBoc/aBoc/Exp) is well described qualitatively (Thomas 1990) but individual step durations within the ~45s cycle were not retrieved numerically this session. Guessed as a few seconds given the full cycle is 45s and the contraction itself is brief.
- **H3** (aBoc (anterior body-wall muscle contraction) step duration): Same caveat as H2.
- **H4** (Intestinal IP3R-dependent Ca2+ wave propagation speed): ITR-1/IP3R-dependent intestinal Ca waves are described (Dal Santo et al. 1999 Cell; Espelt et al. 2005 J Cell Biol) but a wave-speed number was not found in available snippets. Range guessed from typical IP3-dependent Ca wave speeds in other invertebrate epithelia.
- **H6** (PBO-4/PBO-5 intestinal proton-signaling pH change): Beg, Ernstrom, Nix, Davis & Bargmann 2008 Neuron 60:758 identify PBO-4/PBO-5 as sodium/proton exchangers mediating gut-to-muscle signaling. A specific lumen or pseudocoelomic pH swing value was not retrieved; range guessed from generic epithelial pH-signaling swings.
- **I6** (HSN motor neuron firing rate during active phase): HSN is known to fire in bursts specifically during active phases (Zhang, Rotkina & Komuniecki 2008; Collins et al. 2016 Ca imaging) but a specific Hz value was not retrieved in available snippets. Range guessed from typical slow bursting interneuron firing rates in this system.
- **I7** (Vulval muscle Ca2+ transient amplitude during egg-laying contraction): Collins et al. 2016 and related Ca-imaging papers report vm Ca transients but a specific dF/F number was not retrieved this session. Range guessed from typical GCaMP dF/F transients reported elsewhere in the worm literature (section M).
- **I8** (uv1 neuroendocrine cell tyramine release magnitude/effect): uv1 cells release tyramine to inhibit egg-laying via LGC-55 on vm/HSN (Pirri et al. 2009; Collins et al. 2016) but no quantitative release-rate number was retrieved; qualitative only.
- **J6** (AFD thermosensory sensitivity (dCa/dT)): AFD is known as one of the most temperature-sensitive neurons recorded (fractions of a degree resolution) but a specific dF/F-per-degree slope was not retrieved this session; range guessed from generally reported high sensitivity.
- **J8** (PVD harsh-touch mechanoreceptor current/response): PVD harsh-touch transduction (via MEC-10/TRP-4/degenerins, Chatzigeorgiou et al. 2010 Nat Neurosci) is qualitatively established; no quantitative current/response value was retrieved this session.
- **J10** (BAG CO2-sensing response threshold): BAG neurons respond to CO2 increases (Hallem & Sternberg 2008 PNAS; Bretscher et al. 2011) but a specific threshold/EC50 was not retrieved this session; range guessed from typical reported behavioral CO2-avoidance thresholds.
- **J13** (DVA TRP-4 stretch receptor current): Li, Feng, Sternberg & Xu 2006 Nature identify TRP-4 as a stretch-activated channel in DVA; no quantitative current-strain relationship was retrieved this session.
- **J14** (SMD motor neuron head-bending function): SMD neurons drive dorsal/ventral head bending during foraging (Hendricks et al. 2012 Nature; Kaplan et al. 2020) but a specific numeric firing-to-curvature relationship was not retrieved this session.
- **K3** (GLR-1 (AMPA-type glutamate receptor) trafficking timescale in AVA): GLR-1 trafficking/insertion in AVA is studied (Rongo & Kaplan 1999 Nature; Glodowski et al. 2007) in experience-dependent plasticity contexts; a specific trafficking time constant was not retrieved this session. Range guessed from generic AMPA-receptor trafficking timescales in other systems.
- **K4** (DAF-7/TGF-beta expression change timescale with food availability): DAF-7 expression in ASI is food-dependent (Ren et al. 2000 Science; Meisel et al. 2014) but a specific induction/decay timescale was not retrieved this session; range guessed from generic transcriptional response timescales.
- **L1** (Fat store depletion timescale under starvation): Fat (lipid droplet) depletion under starvation is documented (Jones & Ashrafi 2009 Dis Model Mech review; O'Rourke et al. 2009 Genes Dev) on a scale of roughly one to two days to substantial depletion, but a specific quantitative curve was not retrieved this session; range guessed accordingly.
- **L2** (Food (bacteria) intake volume per single pharyngeal pump): Each pump grinds and ingests a small bolus of bacteria; no direct per-pump volume/count measurement was retrieved this session. Range guessed from pharynx lumen dimensions and pump rate.
- **L3** (Whole-animal metabolic rate / energy budget): C. elegans whole-animal respirometry has been reported in multiple papers (e.g. Van Voorhies & Ward 1999 PNAS) with values roughly in this range, but a number was not freshly re-verified by search this session; treated as guessed pending confirmation rather than cited as measured.
- **M6** (GCaMP7f kinetics (Kd, Hill, tau)): Search results referenced GCaMP7f only in combination with other indicators without giving its own Kd/Hill/tau numbers separately; not found this session, left unresolved rather than guessed from nothing meaningful.
- **M8** (Typical GCaMP dF/F imaging noise floor in C. elegans whole-brain recordings): Not found as an explicit number in available snippets. Range guessed from generally reported noise floors in similar in-vivo single-photon/confocal GCaMP recordings.

## 3. General caveats on the whole table

- A large share of "measured" and "inferred" rows (not just the "guessed" ones above) were populated from
  WebSearch result snippets or from the agent's general background knowledge of well-known C. elegans
  papers, not from a fresh primary-source PDF read this session. Every such row says so in its own `note`
  field and uses `source` = "search summary" where that applies; rows recalled from general familiarity
  without a fresh search this session are flagged in-note as "not freshly re-verified." These should be
  treated as a first pass, not a final audited table.
- Several named primary sources in the task brief (Nicoletti 2019/2024 model files, Liu et al. 2018 Cell
  AWA dataset, the Richmond & Jorgensen 1999 and Gao & Zhen 2011 PDFs) were identified and confirmed to
  exist but not actually fetched and read in full this session; numeric values attributed to them above
  come from search-result summaries, which is a weaker evidence tier than a direct read.
- Reversal potentials for the various ligand-gated Cl- channels (GluCl, ACh-Cl, GABA-A) are all estimated
  from a single assumed intracellular Cl- concentration rather than channel-specific measurements; if the
  project needs these to differ meaningfully, they need individual primary-literature checks.
- Many "guessed" rows for muscle force kinetics, gap-junction single-channel conductance, and glial
  signalling numbers almost certainly have measured values in the cited papers that this session's search
  snippets simply did not surface; they are gaps in this session's search coverage, not necessarily gaps
  in the literature.
- Some rows list a single point value (bio_min = bio_max = prior_centre, e.g. M7) because only one number
  was reported in the source consulted, not a biological range across individuals; this differs semantically
  from genuine measured ranges elsewhere in the table and should not be treated as a tight constraint.
