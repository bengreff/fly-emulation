# Neuropeptide and monoamine signalling: what's measured, what has to be inferred

Research note, not canon. Scope: row 9 ("Neuropeptides and receptors") and row 10 ("Monoamines") of the
mechanism ledger in `docs/worm/PLAN.md` section a, which STATE_OF_THE_ART.md section 5 names as the hardest
of the five open problems: Randi et al. 2023 shows the synaptic connectome alone predicts function poorly,
so this layer is structurally necessary, but it is mapped today as binary links (peptide X can activate
receptor Y), not as the release, diffusion, degradation and receptor-to-channel kinetics a dynamical model
needs. Compiled 2026-11-05.

Labels follow PLAN.md: **measured** (read directly off a cited source), **derived** (arithmetic on measured
numbers, shown), **inferred** (taken from a source by reasoning, e.g. homology or generic biophysics),
**guessed** (an estimate with no direct basis, kept only where a number is needed).

## 1. What is measured

### The neuropeptide connectome (Ripoll-Sanchez et al. 2023)

[Ripoll-Sanchez et al. 2023, Neuron](https://www.cell.com/neuron/fulltext/S0896-6273(23)00756-0) combine
CeNGEN expression data with the Beets 2023 ligand-receptor map (below) and neuron anatomy to build a
predicted "neuropeptidergic connectome." The published network uses **51 GPCRs and 49 neuropeptide precursor
(NPP) genes** (measured, the gene set the network is built from). Two findings bear directly on model
structure: the neuropeptidergic and synaptic connectomes overlap for only **5%** of all peptidergic
connections (measured), and the peptidergic "rich club" (densely interconnected hub neurons) comprises
**52% of all neurons**, against **11 neurons** for the synaptic rich club (measured). So this is not a sparse
correction to the synaptic wiring; it is a different, much denser network layered on top of it. Separately,
EM anatomy puts roughly **10% of neurons in the nerve-ring neuropil** as primarily harbouring dense-core
vesicles (DCVs) at the ultrastructural level (measured by EM morphology, a distinct measure from the
expression-based prediction above; the two should not be conflated when deciding which cells get a release
state).

### GPCR deorphanisation with EC50s (Beets et al. 2023)

[Beets et al. 2023, Cell Reports](https://www.cell.com/cell-reports/fulltext/S2211-1247(23)01069-0) ran a
systematic cell-based deorphanisation screen: GPCRs expressed individually in a heterologous cell line,
challenged with synthetic peptides, read out via a reporter assay. They tested **more than 55,000 possible
peptide-GPCR pairs** and found **461 active pairs** (both measured). Potency across those 461 active pairs:
EC50s range from **0.1 pM to 22 micromolar**, and **73% are sub-micromolar** (measured). The companion review
([Beets & Ripoll-Sanchez 2024, Genetics](https://academic.oup.com/genetics/article/228/3/iyae141/7795512))
gives the genome-wide totals this screen sits inside: **160 peptide-encoding genes** (31 *flp*, 40 *ins*, 89
*nlp*) giving rise to **more than 300 distinct peptides**, and **more than 150 putative peptide-activated
GPCRs**, of which **60 now have at least one identified ligand** (all measured, as of that review). The
screen also supports conservation of **at least 14 bilaterian peptidergic systems** (measured, phylogenetic
comparison), which matters below for how parameters can be grouped.

### Peptide and receptor gene expression per neuron (CeNGEN)

[CeNGEN](https://www.cengen.org) ([Hammarlund et al. 2018, Neuron](https://doi.org/10.1016/j.neuron.2018.07.042);
[Taylor et al. 2021, Cell](https://doi.org/10.1016/j.cell.2021.06.023)) gives bulk and single-cell RNA-seq
across all 302 neurons in 118 classes, with threshold-calibrated expression calls per gene per class. This is
the source both Ripoll-Sanchez 2023 and this project's own CeNGEN tables (`cengen/`, PLAN.md row 3) use for
*which* peptide and receptor genes are on in *which* cell: the raw material for turning the binary Beets/
Ripoll-Sanchez map into candidate functional edges (co-expressed peptide-and-release-machinery in one cell,
receptor in a reachable cell), not itself a kinetic parameter.

### Dense-core vesicle release

[Speese et al. 2007, J Neurosci](https://www.jneurosci.org/content/27/23/6150) establish, genetically, that
UNC-31 (the *C. elegans* CAPS homolog) is specifically required for DCV exocytosis and not for synaptic
vesicle exocytosis (measured): this is the molecular basis for why Randi 2023 (below) uses *unc-31* mutants as
an extrasynaptic-null control. Beyond presence/absence of release, acute release kinetics in *C. elegans* are
not measured directly: a 2018 study that tried to localise peptide release sites states plainly that "no
methods have been described to measure acute neuropeptide release in *C. elegans*"
([Chen & Alkema lab, PLoS ONE](https://journals.plos.org/plosone/article?id=10.1371%2Fjournal.pone.0196954)),
and instead used static GFP-fluorescence depletion after 1 hour of monoamine exposure (4-10 mM, far above
physiological concentration) to infer release direction, not rate. What is measured, in other secretory cell
types (vertebrate endocrine cells), is that DCV release is biphasic (fast initial component, then slow
sustained release) and that fusion-pore width sets the release rate (measured in those systems, not in the
worm).

### Peptide diffusion and degradation in the pseudocoelom

The route itself, extrasynaptic volume transmission through the pseudocoelomic fluid, is established
anatomically and by genetic dependence on *unc-31* ([Ripoll-Sanchez/Beets/Schafer preprint, "Extrasynaptic
volume transmission: a novel route for neuropeptide signalling in
nematodes"](https://www.biorxiv.org/content/10.1101/2020.08.07.240440.full.pdf), not independently re-read in
full in this pass: the server rate-limited the fetch). That preprint and the later Ripoll-Sanchez 2023
network paper classify candidate connections into short-, mid- and long-range categories from EM anatomy, but
these are reachability categories, not a calibrated diffusion coefficient or degradation half-life for any
named *C. elegans* peptide. No measured in-vivo diffusion coefficient or degradation rate for a *C. elegans*
neuropeptide was found in this pass; flag this explicitly as a gap, not an oversight, before building on it
(section 2).

### Randi 2023's evidence of peptidergic/monoaminergic effects (*unc-31* mutants)

[Randi et al. 2023, Nature](https://www.nature.com/articles/s41586-023-06683-4) measure sign, strength,
kinetics and direction of signal propagation across **23,433 probed neuron pairs** in the head, by optogenetic
stimulation of one neuron at a time combined with NeuroPAL-identified whole-brain calcium imaging (measured;
already in `randi2023/` per PLAN.md row 7). Critically for this layer, they also ran the same protocol in
*unc-31* mutants, which lack DCV-mediated release of both peptides and monoamines, so synaptic transmission
survives but this entire layer does not. Their headline result: the measured (wild-type) functional atlas
predicts spontaneous whole-brain dynamics better than any model built from the anatomical (synaptic)
connectome alone (measured), i.e. extrasynaptic signalling is not a minor correction but does real
computational work. What this note could not pin down in this pass is the exact published effect size: how
many, and which, of the 23,433 pairs change sign, strength or kinetics between wild-type and *unc-31*. That
number is the single most valuable thing to pull from the paper's own supplement before any peptide fitting
starts (see section 4's recommended first test).

### Monoamines: release, receptors, clearance

*C. elegans* uses the same biosynthesis and handling genes as mammals: synthesis (*tph-1*/TPH for serotonin,
*cat-2*/TH for dopamine, *tdc-1*/TDC for tyramine from tyrosine, *tbh-1*/TBH for octopamine from tyramine),
vesicular loading (*cat-1*/VMAT, shared by all four monoamines), and selective reuptake (*mod-5*/SERT for
serotonin, *dat-1*/DAT for dopamine) (all measured, gene identity and phenotype). No dedicated reuptake
transporter for octopamine or tyramine was found in this pass; their clearance may rely more on diffusion and
enzymatic breakdown than on a *dat-1*/*mod-5*-style transporter, which is itself a gap worth flagging rather
than assuming symmetry with 5-HT/DA.

- *cat-1*/VMAT has been characterised biochemically in vitro: saturable, time-dependent uptake of
  [3H]dopamine and [3H]serotonin, competitively inhibited by dopamine, norepinephrine, serotonin, histamine,
  tyramine and octopamine ([Duerr et al. 1999, J Neurosci](https://www.jneurosci.org/content/19/1/72))
  (measured in vitro; specific Km/Vmax numbers not retrieved in this pass).
- *dat-1* mutants show impaired dopamine clearance and a "vigorous motor activity"/swimming-induced-paralysis
  phenotype ([McDonald et al. 2007, J Neurosci](https://www.jneurosci.org/content/27/51/14216)) (measured
  phenotype, no rate constant retrieved).

Behavioural roles with receptor pharmacology, where published:

| Ligand | Receptor(s) | G-protein coupling | Circuit / cells | Behaviour | Evidence |
|---|---|---|---|---|---|
| PDF-1 | PDFR-1a/b | Gs, raises cAMP | widespread PDFR-1-expressing cells | promotes roaming | [Flavell et al. 2013, Cell](https://www.cell.com/cell/fulltext/S0092-8674(13)00956-2); receptor pharmacology from heterologous expression assays |
| PDF-1 | PDFR-1c (isoform) | Gi/o, lowers cAMP | as above | opposes PDFR-1a/b effect | same source |
| Serotonin (5-HT) | MOD-1 (ionotropic, ligand-gated Cl- channel, not a GPCR) | n/a | AIY, RIF, ASI | promotes dwelling, extends dwelling/truncates roaming | Flavell et al. 2013 |
| FLP-11 | DMSR-1 | Gi/o, lowers cAMP | RIS -> cholinergic wake-circuit neurons; autoreceptor on RIS itself | induces sleep; self-limits sleep duration | [Turek/Chew, "FLP-11 induces and self-inhibits sleep through DMSR-1"](https://pmc.ncbi.nlm.nih.gov/articles/PMC7617803/) |
| NLP-12 | CKR-1, CKR-2 (CCK homologs) | not fully resolved per isoform in this pass | DVA (stretch-sensitive interneuron) -> cholinergic motor neurons/NMJ | potentiates NMJ transmission, sustains locomotion, promotes local search/reorientation | [Hu et al. 2011, Neuron](https://www.cell.com/neuron/fulltext/S0896-6273(11)00377-1); [Bhattacharya et al. 2014, eLife](https://elifesciences.org/articles/71747) |
| FLP-18 | NPR-1, NPR-4 | Gi/o, inhibit cAMP | multiple | context-dependent inhibition | Beets & Ripoll-Sanchez 2024 review |
| FLP-18 | NPR-5 | couples both Gs and Gq, raises cAMP and Ca2+ | multiple | context-dependent excitation | same review |
| Octopamine / tyramine | multiple GPCRs | mixed | antagonistic circuits | food-dependent locomotion, opposing serotonin/octopamine balance | [PMC5559759](https://pmc.ncbi.nlm.nih.gov/articles/PMC5559759/) |

## 2. What must be inferred

**Release rate and triggers.** *C. elegans* DCV exocytosis needs UNC-31/CAPS and UNC-13-family priming
(measured presence of homologs), but the Ca2+-cooperativity and rate constant of fusion in a given worm
neuron is not measured. Must infer from DCV kinetics measured in other secretory cells (biphasic: fast
initial component then slow sustained release; narrower fusion pores release more slowly), bounded to
plausible invertebrate secretory-cell ranges rather than fit to a worm-specific point value, since no
worm-specific point value exists (inferred, bounded guess). The trigger threshold (sustained depolarisation
or burst firing, higher than for fast synaptic vesicle release in better-characterised systems) is inferred by
homology, not measured in the worm.

**Diffusion range.** No measured in-situ diffusion coefficient exists for any named *C. elegans* neuropeptide
(section 1). Must infer bounds from three things: generic small-peptide diffusion coefficients in aqueous/
interstitial media (order 10-150 um^2/s depending on tissue tortuosity, for peptides in the few-kDa range;
inferred from general biophysics, not worm-specific and not independently re-verified against a primary
citation in this pass, flag before use), the worm's own geometry (body cross-section roughly 50-80 um, length
roughly 1 mm, so a peptide needs tens of seconds to reach the far end of the body by pure diffusion at those
coefficients, derived from the stated ranges), and the short/mid/long-range reachability categories from the
extrasynaptic volume transmission work (section 1), which give a plausible topology but not an absolute rate.

**Receptor coupling to channels.** This is generic GPCR biology, applicable by homology since the worm's
core heterotrimeric G-alpha genes are few (EGL-30/Gq, GOA-1/Go, GSA-1/Gs are the ones overwhelmingly used by
aminergic and peptidergic GPCRs; measured as a gene-count fact, itself useful for identifiability, section 4):

- **Gq** (EGL-30) typically signals through PLC-beta to IP3/DAG: IP3 opens the ITR-1 IP3 receptor on the ER,
  releasing Ca2+; DAG can activate TRP-family channels; net effect usually excitatory and often potentiates
  further exocytosis (inferred by homology to characterised Gq cascades, not measured per receptor).
- **Go/Gi** (GOA-1) typically inhibits adenylyl cyclase, lowering cAMP, and can directly modulate inwardly
  rectifying K+ channels (via RGS proteins such as EGL-10); net effect usually inhibitory/hyperpolarising
  (inferred by homology).
- **Gs** (GSA-1) stimulates adenylyl cyclase, raising cAMP, which activates PKA (KIN-2); PKA phosphorylation
  targets include channels and vesicle-priming machinery; net effect usually potentiating (inferred by
  homology; PDFR-1a/b above is the one worm GPCR pair with this specifically measured in vitro).

Which of these three generic cascades a given one of the 461 deorphanized pairs actually uses, in a given
expressing cell, is not measured for the overwhelming majority of pairs; it must be inferred per cell from
which downstream channels CeNGEN says that cell expresses, constrained by the receptor's known G-alpha
preference where published (as in the PDFR-1 and NPR-1/4/5 cases above).

**Time constants.** GPCR cascades are slow relative to ionotropic synapses: in well-characterised systems,
activation-to-effect for Gs/Gq/Gi cascades runs roughly 100 ms to several seconds, against under 5 ms for
ligand-gated ion channels (inferred from general GPCR signalling literature, not measured in the worm). This
sets a plausible bound, not a fitted point value, for every peptidergic and most monoaminergic edges (MOD-1,
being ionotropic, is the measured exception that should keep the fast timescale).

## 3. How other models handled it

No surveyed effort has a kinetic, receptor-to-channel neuropeptide or monoamine layer at whole-animal scale.

- **OpenWorm (c302/Sibernetic)**: none (STATE_OF_THE_ART section 1).
- **BAAIWorm/MetaWorm (2024)**: the `eworm` 136-cell model has gene-named ion channels (confirmed from its
  `.mod` file list, `docs/worm/research/adoption_tests.md` section on BAAIWorm) but no peptide or monoamine
  layer (measured, by inspection of the installed package).
- **modWorm (Kim et al., bioRxiv, posted 2025-06-12)**: its own discussion explicitly names monoamine
  signalling and neuropeptide activity modulation as data that is "rapidly becoming available" but not yet
  incorporated into its 7-module pipeline (measured, from the paper's own text).
- **Izquierdo & Beer, Kunert et al., Boyle & Cohen**: none; these largely predate the bulk of the
  deorphanisation data (measured, STATE_OF_THE_ART section 1).
- The closest working precedent inside this project's own codebase is `src/flyemu/neuromod.py`: a per-cell
  monoamine-pool mechanism with receptor maps, already slated to carry over as the generic mechanism for the
  worm's monoamine layer, with worm-specific values (PLAN.md row 10, section d).

**Parameter count.** PLAN.md section c.1 guesses about 300 parameters for peptides and monoamines combined
(release, clearance, receptor coupling), inside a roughly 2,000-parameter whole-animal total. This note
sharpens that guess and finds it likely too low if applied per deorphanized pair: 461 pairs (measured, Beets
2023) is the hard floor on distinct candidate signalling edges. If each (peptide, receptor) pair gets its own
{release rate, diffusion reach, degradation rate, coupling sign and gain} as four shared-by-pair parameters
(the same rule PLAN.md section c.1 already applies to synapses, no per-instance free knobs), that is 461 x 4
= **1,844 parameters** (derived) just for the deorphanized peptide pairs, well above the plan's 300-parameter
guess. Monoamines are the cheap part by comparison: 4 ligands against a handful of receptor classes each
(order 10-20 total ligand/receptor-class pairs from CeNGEN) x 4 parameters is roughly **40-80 parameters**
(derived), and this part is also the best behaviourally anchored (section 1's table). The gap between 1,844
and the plan's 300 is exactly the identifiability problem taken up next: the data cannot support 1,844
independent values, so the model structure has to group pairs, not fit them individually.

## 4. Identifiability

**Datasets that could constrain these parameters, and what each one actually pins down:**

- **Wild-type vs *unc-31* Randi maps.** The single most direct lever: differences between the *unc-31*
  (extrasynaptic-null) and wild-type functional atlases isolate exactly the signal this layer has to
  reproduce, pair by pair, in the head (measured design, section 1; already local in `randi2023/`). This
  note could not confirm from the paper's abstract/summary alone how many of the 23,433 pairs the *unc-31*
  comparison actually covers, or the published effect size; that needs a direct read of the paper's
  supplementary tables before fitting (named as the first task in section 5).
- **Whole-brain imaging across states** (Atanas 2023, Kato 2015, Nichols 2017, already local per PLAN.md row
  7 and 18). Constrains the slow, multi-neuron correlation timescales that fast synaptic transmission alone
  cannot produce, useful for pinning release/diffusion/degradation time constants in aggregate (does the
  model's predicted correlation timescale match the data's), but not useful for assigning which specific
  receptor mediates which edge.
- **Mutant behaviour** for the genes with published phenotypes (*pdf-1*, *pdfr-1*, *flp-11*, *dmsr-1*,
  *nlp-12*, *ckr-1*, *ckr-2*, *mod-5*, *dat-1*, *cat-1*, *tbh-1*, *tdc-1*, and the handful of others in
  section 1's table). Each is already a held-out ablation prediction under PLAN.md section c.4's design
  ("mutant predictions are the strongest test of 'the same brain'"). These pin sign and rough magnitude for
  perhaps 10-15 of the 461 pairs; the remaining ~450, and the large majority of the 150+ receptor genes, have
  no behavioural tie-down at all.
- **In-vitro EC50s** (Beets 2023). Constrain relative affinity within a peptide's own set of receptors
  (ranking which receptor it hits hardest), not absolute in-vivo release concentration, diffusion reach, or
  degradation rate; those three remain unconstrained by this dataset alone, by any dataset found in this
  pass, in fact.

**Proposed minimal-but-complete model structure.** Given the gap between 1,844 candidate parameters and what
the data above can actually pin down:

- One concentration state per peptide per reachable body region (not per cell: the diffusion-reach categories
  from section 1 already lump cells into regions at the pseudocoelom scale), plus one receptor-occupancy or
  downstream-second-messenger state per receptor per expressing cell. That is **2 state variables per
  (peptide, receptor) pair that is actually built**, consistent with PLAN.md row 9's K1 cost label (a few
  state variables per cell or connection, well under the membrane's per-compartment cost).
- Parameters shared by structural/phylogenetic family (the at-least-14 conserved bilaterian peptidergic
  systems Beets 2023 identifies), not by individual gene, for any family lacking its own direct behavioural or
  strong EC50 anchor. This is the only way to keep the free-parameter count near the plan's original few-
  hundred budget while still building a mechanistic, not binary, layer: grouping by family turns the
  1,844-parameter floor (461 pairs x 4) into roughly (14 families, or more conservatively the 60 receptors
  with any known ligand) x 4, i.e. **56-240 parameters** (derived, depending on grouping granularity) for the
  peptide side, plus the 40-80 for monoamines above, landing close to PLAN.md's original 300-parameter guess
  once grouped, not when fit pair-by-pair.
- Anchored families (the 10-15 with published mutant phenotypes) get their own fitted values, one per family,
  not shared; unanchored families share one set of bounded values per structural group, flagged clearly as
  the weakest-constrained part of the whole-animal fit.

## 5. Recommendation and first pre-registered test

**Build order** (pulls milestones in rather than pacing to anything, per standing project practice):

1. **Monoamines first.** Four ligands, few receptor classes, the best-anchored behaviourally (PDF-1/
   serotonin roaming-dwelling and FLP-11 sleep already have clean genetic phenotypes to fit and hold out
   against). Reuses the `neuromod.py` pool mechanism already slated to carry over from the fly (PLAN.md row
   10, section d), so this is mostly a worm-data-filling exercise, not new mechanism design.
2. **Then the 10-15 peptide pairs with direct behavioural phenotypes and published receptor pharmacology**
   (PDF-1/PDFR-1, FLP-11/DMSR-1, NLP-12/CKR-1/CKR-2, FLP-18/NPR-1/4/5, and similar). Each is independently
   falsifiable against its own published mutant phenotype before touching the unanchored remainder.
3. **Only then the remaining ~450 deorphanized pairs**, grouped by structural family per section 4, fit
   jointly against whatever the wild-type-vs-*unc-31* Randi atlas difference turns out to show and against
   whole-brain imaging timescales. Never fit per-individual-pair without an anchor; nothing in the data pins
   an individual pair otherwise (section 4).
4. **Never build the full binary Ripoll-Sanchez network as 461 independently point-valued pairs in one
   pass.** That adds on the order of 1,800 parameters (section 3) against data that can only identify
   family-level groups (section 4), which is exactly what PLAN.md section c.1's rule against per-instance free
   knobs is meant to prevent.

**First pre-registered test.** Before fitting anything in this layer, pre-register a comparison that costs
nothing new to collect, because the data are already local or already being pulled in for other reasons
(`randi2023/`, `peptide_connectome/`, PLAN.md rows 7 and 9): take the W3 head-circuit fit (PLAN.md roadmap
stage W3, synaptic-only, with a connectome-only baseline already required as that stage's falsifier) and ask
whether its held-out prediction error on the Randi 2023 stimulated pairs is *concentrated* on exactly the
neuron pairs for which Ripoll-Sanchez 2023 and Beets 2023 predict a co-expressed peptide/GPCR edge, versus
pairs with no predicted peptidergic edge. Randi 2023's own headline result is that the wild-type functional
atlas beats an anatomy-only model; this project's matching, not-yet-run test is whether the synaptic-only
model's errors specifically sit where the peptide map says they should. If the errors are **not** concentrated
there, the extrasynaptic layer, however real in Randi's own *unc-31* data, may not be the thing this project's
synaptic-only model is missing most, and the build order above should be deprioritised relative to other
error sources already known to be incomplete (channel kinetics, gap-junction rectification). That is the
built-in way to fail, required by this project's own decision log (PLAN.md DECISIONS item 2: every
pre-registration needs a named wrong-model control). It requires no new data collection, only a re-analysis of
data already slated to be local.
