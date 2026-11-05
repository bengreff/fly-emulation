# Genes to physiology: priors for the expression-to-density map

Research note, not canon. Scope: PLAN.md row 3 ("ion channels per neuron class: presence") and row 5
("channel densities... per class"), which are today a CeNGEN presence threshold (DECISION 5) plus an
independent bounded fit per class (section c.1). This note asks what biology itself says about the
*structure* of a map from gene expression to channel density, so that map can be one shared function with
priors, not 118 unrelated per-class fits. It does not re-survey whether the field has already built this map;
that is `OPENWORM_AND_NOVELTY.md` section 2.1 (expression-to-physiology) and 2.2 (homeostatic tuning), which
this note cites rather than repeats. Compiled 2026-11-05.

Labels follow PLAN.md: **measured** (read directly off a cited source), **derived** (arithmetic on measured
numbers, shown), **inferred** (taken from a source by reasoning, e.g. homology), **guessed** (an estimate with
no direct basis). Where a source could not be read past a paywall or a search-engine summary, that is noted;
treat such claims as **reported**, one step weaker than measured.

## 1. Terminal selectors: shared batteries are a real biological structure

The Hobert lab's terminal selector model: a small set of transcription factors, switched on after a neuron's
last division and kept on for life, directly binds the regulatory regions of the genes that make a neuron what
it is (neurotransmitter machinery, ion channels, receptors, neuropeptides), called the effector gene battery
([Hobert, *Terminal Selectors of Neuronal Identity*](https://www.researchgate.net/publication/298054537_Terminal_Selectors_of_Neuronal_Identity);
[Hobert 2016, *WIREs Dev Biol*](https://wires.onlinelibrary.wiley.com/doi/10.1002/wdev.233)). The same selector
is often reused across many neuron classes and still produces a distinct fate in each, because it acts
combinatorially with other factors (**measured/reported**, consistent across the sources above). The clearest
worked example is cholinergic identity: the COE-family factor UNC-3 is necessary in every cholinergic motor
neuron for the whole cholinergic battery (transmitter synthesis, receptors, and, in some subtypes, channels),
and different motor-neuron subclasses add a second, co-factor to the same UNC-3 battery to specialise it
([*Coordinated regulation of cholinergic motor neuron traits through a conserved terminal selector gene*](https://www.nature.com/articles/nn.2989);
[Kerk et al., *An intersectional gene regulatory strategy defines subclass diversity of C. elegans motor neurons*, eLife 2017](https://elifesciences.org/articles/25751)).
Selector function is not always switched on once and left alone either: it can be run in temporally modular
phases that re-specify the same battery at different life stages ([*Establishment and maintenance of motor
neuron identity via temporal modularity in terminal selector function*, eLife 2020](https://elifesciences.org/articles/59464)), which matters for section 4.

Two 2020-2021 papers turn this from a per-circuit story into a genome-wide, quantitative one:

- **[Reilly, Cros, Varol, Yemini & Hobert, "Unique homeobox codes delineate all the neuron classes of C.
  elegans," *Nature* 584:595-601, 2020](https://pmc.ncbi.nlm.nih.gov/articles/PMC7587405/)** (PMC full text
  read). The *C. elegans* genome has **102 homeobox genes** (measured); **80 of the 101 examined** are
  expressed in the mature nervous system (measured). Excluding the panneuronal ones, the combinatorial code
  per class averages **about 4 homeodomain proteins** (measured), and every one of the 118 neuron classes
  carries its own unique combination, with **155 distinct combinatorial codes** found once sub-identities
  within a class are counted (measured). A regression from this sparse homeobox code alone explained **74% of
  a separate reporter-gene expression atlas, at single-neuron resolution** (measured). That last number is the
  load-bearing one for this project: a handful of transcription factors already predicts most of a neuron's
  expressed-gene identity, which is the same shape of claim this project wants to make for channel density.
- **[Glenwinkel, Taylor, Langebeck-Jensen, Pereira, Reilly, Basavaraju, Rafi, Yemini, Pocock, Sestan, Hammarlund,
  Miller & Hobert, "In silico analysis of the transcriptional regulatory logic of neuronal identity
  specification throughout the C. elegans nervous system," *eLife* 10:e64906, 2021](https://elifesciences.org/articles/64906)**
  (fetched). Built directly on CeNGEN ([Taylor et al. 2021](https://doi.org/10.1016/j.cell.2021.06.023)):
  screened **136 neuronally-expressed transcription factors'** binding motifs against the CeNGEN
  differentially-expressed gene sets of all 118 classes, by phylogenetic footprinting across eight nematode
  genomes. Result: **117 of 118 classes** have a putative terminal-selector TF or TF combination (measured);
  **124 TFs** are implicated in total (measured); **98% of candidate terminal-selector pairs** that co-occur in
  a class share downstream targets, the signature of combinatorial battery control (measured); and **83%
  agreement** between the scRNA-based prediction and an independent reporter-gene dataset on which TF is the
  top selector for a class (measured). The predicted target genes explicitly include ion channels and
  receptors alongside neurotransmitter and neuropeptide genes (measured). This is, in effect, a genome-wide,
  computational confirmation of the battery model, built on the same CeNGEN data this project already has
  locally (`cengen/`, PLAN.md row 3), with an explicit TF-to-class assignment this project does not yet use.

Two further resources bear on how to use this structurally rather than just descriptively. **NeuroPAL**
([Yemini et al., *Cell* 184:272-288, 2021](https://www.cell.com/cell/fulltext/S0092-8674(20)31682-2)) gives an
invariant multicolour fluorescent code that nails down neuron-class identity directly in the living animal,
the same identity axis CeNGEN classes and the homeobox code are both indexed by; it is the tool that lets a
CeNGEN pseudobulk class, a terminal-selector TF combination, and a connectome node all be confirmed as the
same 118-way partition rather than silently drifting apart. **Packer, Zhu et al., "A lineage-resolved molecular
atlas of C. elegans embryogenesis at single-cell resolution," *Science* 365:eaax1971, 2019**
([html](https://www.science.org/doi/10.1126/science.aax1971)) profiled **86,024 single embryonic cells** and
resolved **502 terminal and pre-terminal cell types** against the Sulston lineage tree (measured); lineage
distance predicts transcriptome distance early, and that relationship breaks down as sister cells diverge into
distinct terminal fates (measured). This is the developmental precursor of the Reilly/Glenwinkel adult code:
it shows the code is laid down progressively along the lineage, which is the hook into section 4.

**Structuring the map.** The practical consequence for PLAN.md row 5: the unit of sharing does not have to
stop at "class" (118 independent fits) or jump all the way to "gene family" (one value for all 118 classes).
There is a real, measured, intermediate unit: the terminal-selector **battery** (Glenwinkel's 117-124
TF-defined groups, or Reilly's 155 combinatorial codes if finer sub-identity resolution is wanted). A channel
gene's density-determining parameters can be shared across every class whose battery includes that gene's
regulator, which is a biological claim ("the same selector drives the same channel the same way wherever it
acts"), not a numerical convenience, and it is falsifiable class by class (section 5).

## 2. mRNA, protein, and functional density: how far transcript counts can be trusted

CeNGEN gives transcript counts, not channel density. Three kinds of evidence bound how much that gap matters.

**Worm proteomics, where it exists.** Cell-type-selective proteomics in *C. elegans* is new and small, but two
independent studies already report the mRNA-protein relationship directly, and both find it weak:

- **[Aburaya, Yamauchi, Hashimoto, Minakuchi, Aoki & Ueda, "Neuronal subclass-selective proteomic analysis in
  Caenorhabditis elegans," *Scientific Reports* 10:13840, 2020](https://pmc.ncbi.nlm.nih.gov/articles/PMC7426821/)**
  (PMC full text read). BONCAT-based labelling found **4,412 proteins across all neurons** and **1,834 proteins
  in the AFD subclass alone** (measured); the paper states plainly that transcript and protein abundance "do
  not correlate" (reported, citing prior general literature, not a fitted r from their own data).
- **[Ran, Huang, Li & Zheng, "Integrating MACSPI and SILAC for Neuron Type-specific Proteomics in
  Caenorhabditis elegans," *Molecular & Cellular Proteomics*, 2026](https://pmc.ncbi.nlm.nih.gov/articles/PMC13020083/)**
  (fetched). Profiled dopaminergic neurons and touch-receptor neurons and report **Pearson r is approximately
  0.3 across all mRNA-to-protein comparisons** (measured), explicitly concluding mRNA level is not a good
  predictor of protein abundance in these neurons. Neither paper isolates ion channels specifically from this
  correlation; no worm study reporting an ion-channel-specific mRNA-to-current-density correlation was found
  this pass, which is itself a gap worth recording rather than papering over.

**Mammalian Patch-seq, the nearest real precedent.** Patch-seq (simultaneous single-cell transcriptome plus
patch-clamp) gives a better-populated version of the same question in mouse/human cortex:

- A large cross-cell-type analysis finds ion-channel-gene expression predicts single-cell variation in spike
  width with **Pearson r = 0.78 (n = 1,396 cells)** ([*Transcriptomically-measured gene expression predicts
  physiological variation across single neurons in humans and mice*, bioRxiv 2024.08.26.609746](https://www.biorxiv.org/content/10.1101/2024.08.26.609746v1.full))
  (measured, one feature, large n), far better than the worm proteomic r above, but this is a phenomenological
  feature regression (transcript to spike shape), not a mechanistic channel-density prediction.
- The closest structural precedent to what this project wants is **[Bernaerts, Deistler, Goncalves, Macke,
  Berens et al., "Combined statistical-biophysical modeling links ion channel genes to physiology of cortical
  neuron types," *Patterns* 6(10), 2025](https://pmc.ncbi.nlm.nih.gov/articles/PMC12546750/)** (preprint:
  [bioRxiv 2023.03.02.530774](https://www.biorxiv.org/content/10.1101/2023.03.02.530774v2.full)). They fit a
  13-parameter Hodgkin-Huxley model per cell by simulation-based inference against 23 electrophysiological
  features from **955 mouse motor-cortex Patch-seq neurons**, then learned expression-to-HH-parameter maps
  (linear sparse reduced-rank regression, and a nonlinear sparse bottleneck network) from **427 ion-channel and
  marker genes** (measured, already logged in `OPENWORM_AND_NOVELTY.md` s2.1). Their own finding on resolution:
  delayed-rectifier K+ conductance and membrane capacitance were predicted well; leak potential and muscarinic
  K+ conductance poorly; and generalisation was "accurate at the family level, weaker at the cell-type level"
  (measured/reported). That ceiling, mechanistic model first, statistical map second, accurate at the family
  level, is the most directly transferable result in this whole note.

**Synthesis for this project.** Every measured correlation found, worm proteomic (r ~ 0.3) or mammalian
Patch-seq feature-level (r up to 0.78) or Bernaerts' explicit family-vs-cell-type split, points the same way:
raw transcript level is a real but noisy, family-resolution signal, not a density value. That is already
consistent with how PLAN.md rows 3 and 5 use CeNGEN today (presence/threshold, then an independently bounded
fit), and it sets the honest expectation for the "one shared function of gene expression" the plan wants to
add: it should be fit (its own parameters are unknowns to be estimated, as in Bernaerts), not hand-set as
transcript-equals-density, and its held-out test should be judged at the family/battery level first (section
5), because no system studied so far, worm or mouse, gets reliable predictions at the single-class level from
expression alone. One general qRT-PCR-plus-patch-clamp study elsewhere (not worm) reports a reasonable
correlation between Kv2.1 transcript level and delayed-rectifier current density in matched cells
([ScienceDirect S016502701200221X](https://www.sciencedirect.com/science/article/abs/pii/S016502701200221X),
reported, full text not re-extracted this pass), a reminder that the relationship is gene- and
channel-specific, not a single universal slope, which again argues for a *function*, with family-level shared
parameters, rather than one constant.

## 3. Channel kinetics priors for genes nobody has recorded in a worm neuron

**The gene families.** *C. elegans* has about 72 potassium-channel genes split into three structural classes:
2TM (inward-rectifier/Kir-like), 4TM (two-pore domain, the TWK family), and 6TM (Shaker/Shab/Shaw/Shal, KCNQ,
EAG/ERG, Slo/BK) (measured, [WormBook, "Potassium channels in C. elegans"](https://www.ncbi.nlm.nih.gov/books/NBK19762/),
via search synthesis; this matches the task brief's own ~70 figure). TWK is the largest single family, about
46 genes, mostly with no clear vertebrate ortholog (measured, same source). Voltage-gated calcium channels are
one gene per class: egl-19 (Cav1/L-type), unc-2 (Cav2/N-P-Q-type), cca-1 (Cav3/T-type) (measured, already used
in this project's channel library). There is **no voltage-gated sodium channel gene** in the genome; NCA-1/
NCA-2 (the NALCN ortholog) instead give a voltage-independent background Na+ leak, and that gene is already in
this project's library under the name "NCA" (measured, `SPIKE.md`).

**What already has a recording, inside this project's own library.** The Nicoletti 2019/2024 channel set this
project has ported and checked against NEURON (PLAN.md row 4, `SPIKE.md`, `W1_RIM_AFD.md`) covers, between
heterologous expression and native recordings: EGL-19, UNC-2, CCA-1, NCA (the three VGCC genes plus NALCN);
SHL-1 (Shal/Kv4), SHK-1 (Shaker/Kv1), EGL-36 (Shaw/Kv3), EGL-2 (EAG/Kv10), UNC-103 (ERG/Kv11), KQT-1 and KQT-3
(KCNQ/Kv7), KVS-1 (Kv2-related modulatory subunit) (6TM voltage-gated K+); IRK-1/-2/-3 (Kir, 2TM); SLO-1 and
SLO-2 (BK- and Slack-like Ca2+/Cl--activated K+); and KCNL (SK/KCa2): 22 channels in total (measured, this
project, each matched to NEURON at <= 0.01 mV RMS). That is at least one recorded representative of every 6TM
subfamily plus the VGCC genes and NALCN.

**What is not covered, concretely.** The entire 46-gene TWK (4TM) family has zero kinetics in this project's
library today: UNC-58 and EGL-23, both TWK-family genes that CeNGEN calls present in RIM and AFD, had to be
"absorbed by the leak" this week for lack of a kinetics model (measured, `W1_RIM_AFD.md`, 5 Nov 2026), and the
other ~44 TWK genes are in the same position. EXP-2 (ERG-related but structurally distinct, pharyngeal and
AFD) was absorbed into the leak for the same reason (measured, same source). This is a live instance of
exactly the problem this section is about, not a hypothetical one.

**How to get a bounded prior without a worm recording.** Two layers, both already consistent with how this
project shares kinetics "by gene, not by cell" (PLAN.md row 4):

1. **Cross-species family homology.** The Shaker/Shab/Shaw/Shal nomenclature itself comes from Drosophila
   cloning (field-standard background, not independently re-verified this pass), and the same four 6TM
   subfamilies trace back through the whole bilaterian/parahoxozoan lineage: Shaker-type channels predate the
   ctenophore/parahoxozoan split, while Shab, Shal and Shaw arose as parahoxozoan-specific duplications
   ([Li, Liu, Jegla et al., "Major diversification of voltage-gated K+ channels occurred in ancestral
   parahoxozoans," *PNAS* 112(9), 2015](https://www.pnas.org/doi/10.1073/pnas.1422941112), measured). That
   means a fly Shaker, a mammalian Kv1, and the worm's own SHK-1 are the same paralogy group, not independently
   convergent proteins, which licenses borrowing a bounded range of gating time constants and voltage
   dependence shape from a recorded paralog in another species as the starting prior for a worm gene in the
   same family with no recording of its own (inferred, by homology). The worm's own 6TM genes already recorded
   (above) should anchor these family priors; it is the ~46 TWK genes, and any other 2TM/6TM gene CeNGEN calls
   present but this project has not yet ported, that would draw on a fly or mammalian two-pore-domain (K2P)
   channel's kinetics as the inferred starting range instead.
2. **AlphaFold structure as a secondary, qualitative prior.** Recent work shows AlphaFold2/3 structures of
   voltage-gated channels capture enough of the voltage-sensor (S4) and pore (S6) architecture to be used for
   conformational-state modelling ([*AlphaFold2 captures conformational transitions in the voltage-gated
   channel superfamily*, 2025](https://pmc.ncbi.nlm.nih.gov/articles/PMC12709252); [*A brief guideline for the
   studies of structure-function relationship of ion channels using AlphaFold3*](https://pmc.ncbi.nlm.nih.gov/articles/PMC13424397/);
   [hERG conformational-state preprint, bioRxiv 2024.01.27.577468](https://www.biorxiv.org/content/10.1101/2024.01.27.577468v3.full))
   (measured/reported, none of this is C. elegans-specific; no example of it being applied to a worm channel
   was found this pass). The usable signal is qualitative: S4 charge count and S6 gate geometry (one search
   result specifically flags a pore-lining pi-helix kink as changing single-channel conductance) can rank an
   unrecorded gene as fast/transient versus slow/sustained, or flag an unusual pore, before any kinetics
   number is fit. This is a plausibility check on which family-prior bound to start from, not a replacement
   for the homology prior above, and it is a method transplant from the structural-biology literature, not
   existing worm-channel work.

**Recommendation for this section.** Carry kinetics at the level of gene **family** (the ~12-15 structural
groups: VGCC x3, Shaker, Shab/EAG-ERG-KCNQ-grouped-by-nearest-recorded-paralog, Shaw, Shal, Slo, Kir, SK, TWK,
NALCN, leak), each seeded from whichever family member (worm, fly, or mammalian) has a real recording, shared
and bounded exactly as PLAN.md c.1 already shares kinetics within species. A worm paralog with no recording of
its own inherits the family's kinetics prior and gets only its density fit from CeNGEN and ephys, with family
assignment by sequence homology and an AlphaFold-structure sanity check, not a hard AlphaFold-derived number.

## 4. The invariant lineage and development: growing parameters instead of fitting them

**What is measured.** Sulston and Horvitz's cell lineage gives the exact, invariant birth time and birth order
of every somatic cell, including every neuron ([Sulston Nobel lecture, 2002, summarising Sulston 1977/1983](https://www.nobelprize.org/uploads/2018/06/sulston-lecture.pdf),
classical, measured). Packer 2019 (section 1) shows the embryonic transcriptome tracks that lineage closely
early on, then diverges as terminal fates are adopted (measured). Postembryonically, the heterochronic gene
cascade, the microRNAs lin-4 and let-7 acting on lin-14, lin-28, hbl-1 and lin-41, sequences which cell fates
are available at each of the four larval stages (measured, classical; recent work, e.g. [*A temporal sequence
of heterochronic gene activities promotes stage-specific developmental events in C. elegans*, PMC11304605](https://pmc.ncbi.nlm.nih.gov/articles/PMC11304605/),
continues to refine the timing). Terminal-selector activation itself is not always locked to the cell's birth:
transient activators can switch a selector on in a time window after birth, decoupled from division timing
(reported, consistent with the temporal-modularity paper in section 1). And the connectome itself is measured
growing: **[Witvliet, Pontes, Li, Mulcahy, Mark, Yeo, Alcantara, Han, Yemini, Lu, Cook, Tang, Rafi, Emmons, Hall,
Lu & Zhen, "Connectomes across development reveal principles of brain maturation," *Nature* 596:257-261,
2021](https://openworm.org/ConnectomeToolbox/Witvliet_2021/)** reconstructed **eight isogenic animals from L1
to adult** (3 L1, 2 L2, 1 L3, 2 adult), tracking **3,113 connections** across stages, classed as stable,
variable, or developmentally dynamic; connectivity asymmetry fell from birth to adulthood, most of that drop
in L1, while network modularity and feed-forward structure both increased with age (all measured). This is
already local to this project (`witvliet2021/`, PLAN.md row 2) as a morphology/connectivity source; it has not
been used as a developmental-physiology source.

**Is there prior work that grows channel or biophysical parameters along this axis, rather than fitting them
once at the adult endpoint?** Searched directly this pass (lineage birth order, developmental trajectory,
model, C. elegans): none found. The nearest existing mechanism is activity- and size-coupled homeostatic
tuning: a calcium-sensing feedback rule that scales channel conductances to compensate as a model neuron grows
([O'Leary, Williams, Caplan & Marder, *PNAS* 2013](https://neurostatslab.org/assets/papers/OLeary_etal_2013.pdf);
[Gorur-Shandilya, Marder & O'Leary, "Homeostatic plasticity rules that compensate for cell size are susceptible
to channel deletion," bioRxiv 2019](https://www.biorxiv.org/content/10.1101/753608), authors confirmed via
CrossRef). This already uses a growth signal (cell size, via calcium activity) to set density, but it is run
on hand-built stomatogastric-ganglion model neurons, not fit to any real population, and the growth signal is
physiological (size, activity), not the lineage clock (birth order, heterochronic stage) itself. This is
already flagged for the field generally in `OPENWORM_AND_NOVELTY.md` s2.2; nothing there or found here ties it
to birth order specifically. DevoWorm models embryogenesis and lineage, not adult channel physiology
(`OPENWORM_AND_NOVELTY.md` s1.6). No project combines a lineage/heterochronic time axis with channel-density
growth.

**What this means, as a proposal rather than a finding.** Birth order and the heterochronic clock are a
second, largely independent time axis from activity, along which density could in principle be scheduled
instead of fit. A concrete, testable version: take each class's adult channel densities from the row-5 fit,
and regress them against lineage birth time (Sulston) or the developmental stage at which each channel gene's
expression first turns on in the Packer 2019 atlas, exactly as Reilly 2020 regressed adult expression against
the homeobox code. If birth time or onset stage predicts density variance beyond what the terminal-selector
battery (section 1) already predicts, Witvliet's eight-animal series becomes a second, independent held-out
axis: predict an earlier developmental stage's physiology, not just another adult, and the model gains a
mechanism for growing day-1 parameters in a developmental run rather than only fitting an adult snapshot. This
is new, not an adoption of existing method; it should enter neutral, like every other mechanism in PLAN.md
section a, and only stay if it improves a held-out prediction current activity-only homeostatic tuning cannot
reach.

## 5. Recommendation: the map's structure, its parameter count, and the held-out test

**Structure, three levels, hierarchical by gene family then selector battery then class.**

| Level | Unit | What is shared | Source | Fit or fixed |
|---|---|---|---|---|
| 0 | Gene **family** (~12-15: VGCC x3, Shaker, Shab, Shaw, Shal, KCNQ, EAG/ERG, Slo, Kir, SK, TWK, NALCN, leak) | Kinetics (activation/inactivation shape, voltage dependence), one set per family | This project's 22 already-ported channels anchor most families; unrecorded worm paralogs (the ~46 TWK genes, EXP-2, any others) inherit the family prior by cross-species homology (section 3), with an AlphaFold structure check as a plausibility flag | Fixed, as PLAN.md row 4 already treats kinetics ("shared by gene, not per cell"); this generalises one step to "shared by family where the worm gene itself has no recording" |
| 1 | Selector **battery** (Glenwinkel's ~117-124 TF-defined groups, or Reilly's 155 combinatorial codes for finer resolution) | One density-scaling parameter per (battery, channel family) edge that CeNGEN says is actually wired | Reilly 2020 + Glenwinkel 2021 give the battery-to-class assignment; CeNGEN gives which edges exist | Fitted, bounded, shared across every class in the battery |
| 2 | **Class** (118) | A residual scale per (class, channel), regularised toward its battery's Level-1 value rather than independently bounded | Row 5's existing per-class fit machinery, unchanged mechanically | Fitted, bounded; expected (not assumed) to collapse toward zero for most classes, per the family-level ceiling found in every mRNA-to-physiology study surveyed (section 2) |

**Parameter count.** Today (PLAN.md c.1, guessed): about 1,400 class x channel density parameters (118
classes x about 8-12 channels, plus Cm/leak/Ra), each independently bounded, none sharing information across
classes beyond the bound itself. Under this structure: Level 0 kinetics are unchanged in count (already
shared by gene; now also shared by family for unrecorded genes, so if anything there are *fewer* independent
kinetics sets, not more). Level 1 adds, derived from Glenwinkel's numbers, on the order of a few hundred
battery-channel edges (117-124 batteries, each touching a handful, not all, of the 12-15 families; a rough
upper bound of 124 x 15 = 1,860 if every battery touched every family, but CeNGEN presence and the
battery-target overlap Glenwinkel reports (98% of co-occurring selector pairs share targets, implying dense
reuse of the same few families) make the real count much smaller, likely a few hundred, guessed, to be counted
exactly once the battery-to-class table exists). Level 2 keeps the same ~1,400 numbers the model needs to
match ephys, but reframes each as a deviation from a shared, independently-estimated Level-1 value rather than
a free number: the number of parameters that need their *own* data support shrinks to roughly the Level-1
count (order several hundred), with the ~1,400 class-level values becoming predictions to be checked, not
unknowns to be independently fit. That is the same "fit like a fly" shared-parameter philosophy this project
already applies to kinetics and to ephys-derived bounds; the hierarchy makes it an explicit, three-level,
falsifiable structure instead of leaving "constrained by circuit data" (row 5) informal.

**The held-out test.** Hold out whole neuron **classes**, not just a protocol or a cell within a class (which
PLAN.md c.4 already does for ephys). Concretely: seal about 20% of the 118 classes, stratified so both
ephys-recorded and never-recorded classes are represented, chosen by seed before any Level-1 fit. Fit Level 0
and Level 1 on the remaining classes. For each sealed class, predict its channel densities from CeNGEN
expression and terminal-selector battery membership **alone**, with no Level-2 term for that class (the
no-cheating condition: a sealed class gets only what its battery predicts). Score against whatever evidence
exists for it, direct ephys where available (L1 loss in c.2's table), otherwise an indirect signal such as a
Randi 2023 functional-atlas response or a coarse spiking/non-spiking class call. Pre-register a control that
must fail, as DECISION 2 already requires generally: a shuffled battery-to-class assignment fit the same way,
which should predict sealed classes no better than chance. The expected result, stated before running it, is
not "this works at the class level": every mRNA-to-physiology study surveyed here, worm proteomics and
Bernaerts/Deistler's mouse-cortex map alike, found good prediction at the family/battery level and a real
ceiling at the individual-cell-type level. So the test should be judged, and reported, at both resolutions
separately, and a model that predicts the battery-level average well but misses individual sealed classes is
an honest, informative result, not a failed one, exactly the ceiling this project should expect going in
rather than discover by surprise.
