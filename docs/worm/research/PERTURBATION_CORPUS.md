# Genome-wide perturbation data as a held-out corpus

Research note, not canon. Scope: can genome-wide *C. elegans* perturbation data (gene knockouts/
knockdowns and neuron ablations, scored against whatever each neuron, muscle or gland expresses)
serve as a large, mostly-free, blind-prediction corpus on top of the behaviour corpus already in
`STATE_OF_THE_ART.md` section 3 and the held-out plan in `PLAN.md` section c.4? Labels follow
`PLAN.md`: **measured** (read off a cited source), **derived** (arithmetic shown), **inferred**
(reasoned from a source), **guessed** (no direct basis, kept only where a number is needed).
Compiled 2026-11-05; web sources checked live today; none of this is downloaded yet (section 4).

## 0. Why this is worth a separate note

The mechanism ledger (`PLAN.md` section a, rows 3-10) gives every ion channel, ligand-gated
receptor, transmitter-synthesis enzyme, neuropeptide/receptor pair and innexin a CeNGEN-derived
cell list: which of the 118 neuron classes (plus muscle, pharynx, intestine, etc.) express it. Any
public experiment that disables one of those genes, scored only in the cells CeNGEN says express
it, is a natural knockout the model must predict with no refit. `PLAN.md` c.4 already names this as
the strongest test ("mutant predictions... probe internal mechanism, not just output") but scopes
it as "remove a gene from the CeNGEN table" without sizing the data. This note sizes it.

## 1. Sources and access

### 1.1 WormBase phenotype annotations (RNAi and alleles)

WormBase curates every published RNAi and allele phenotype into the Worm Phenotype Ontology (WPO),
a controlled vocabulary (**measured**: [Worm Phenotype Ontology paper](https://bmcbioinformatics.biomedcentral.com/articles/10.1186/1471-2105-12-32)).
Checked live via the ontology browser today, two branches relevant here:

- **"physiology phenotype"** (the parent branch covering locomotion, pharyngeal pumping,
  egg-laying, defecation, chemotaxis, etc.): **7,850 genes** with an RNAi-sourced annotation and
  **5,188 genes** with an allele-sourced annotation, including descendant terms (**measured**,
  live ontology-browser query, `wormbase.org/tools/ontology_browser`, 2026-11-05).
- **"locomotion variant"** alone (one descendant of the above): **1,298 genes** direct RNAi,
  **297 genes** direct allele; **1,430** and **806** respectively once descendant terms are
  included (**measured**, same tool, same date).

Genome-wide RNAi feeding libraries (Kamath/Ahringer, Fraser/Sonnichsen) reach **16,757-19,763
clones**, roughly **86-87% of the ~19,000 predicted genes** ([Kamath & Ahringer 2003](https://pubmed.ncbi.nlm.nih.gov/12828945/);
[library reliability analysis](https://bmcgenomics.biomedcentral.com/articles/10.1186/1471-2164-12-170)),
so RNAi coverage of the genome is close to complete; the counts above are the fraction of that
coverage that scored a visible phenotype. Format: WormBase REST API, TSV bulk downloads, SimpleMine
batch gene-list queries; no stated licence beyond "free for research use." Size: whole-database
TSVs are tens of MB; a SimpleMine batch query for a few hundred genes returns in seconds. **Caveat:**
the two numbers above are single live queries against two terms, not a full export; the exact count
for every row-3-10 gene needs a scripted SimpleMine/WormMine query (not run this pass, section 4).

### 1.2 Million Mutation Project (MMP)

[Thompson et al. 2013, Genome Research](https://genome.cshlp.org/content/23/10/1749): **2,007**
EMS-mutagenized, whole-genome-sequenced, N2-derived strains (**measured**), averaging **~400 SNVs**
per strain. Genome-wide, **175,257 (21.2%)** of all SNVs are nonsense and **4,660 (0.56%)** hit
canonical splice junctions, giving **12,594 putative gene knockouts** across **8,150 of ~20,000
protein-coding genes** (**measured**). This is genotype, not phenotype: strains are live and
ordered from the CGC, but no behaviour screen was run - any phenotype has to be measured after
ordering. Format: VCF + strain list, `genome.sfu.ca/mmp/`, public CGC distribution terms.

### 1.3 TaoChongBao (2026) - a much larger, newer version of the same idea

[TaoChongBao](https://pmc.ncbi.nlm.nih.gov/articles/PMC13009681/), published March 2026 in *Life
Science Alliance*: **12,069** viable EMS strains, **20,315,536** variants, **541,102** unique
missense mutations across **20,914 genes** (**measured**) - roughly the whole protein-coding
genome, 20x the missense coverage of MMP, built to let a human-disease-gene query pull back a
*C. elegans* strain carrying the matching residue change. Same caveat as MMP: a genotype and
strain-availability resource (plus AlphaMissense/ClinVar scores), not a phenotype screen.

### 1.4 Yemini et al. 2013 (Worm Tracker 2.0 / the 305-strain phenome)

[Yemini et al. 2013, Nature Methods](https://doi.org/10.1038/nmeth.2560): **305 strains**
(mostly single-gene mutants, including **76** with no previously described phenotype), **~10,000**
worms, **9,203** tracked videos, **702 quantitative features per worm** vs wild-type (**measured**).
The best-fit source here: every strain gets a full continuous feature vector, not a binary call.
Format: `wormbehavior.mrc-lmb.cam.ac.uk` and companion database. Which genes are covered was not
re-derived from the strain list this pass (follow-up: cross the public 305-strain list against the
row 3-10 gene set directly rather than estimating).

### 1.5 Open Worm Movement Database (Javer et al. 2018, Brown lab) and Tierpsy

[Javer et al. 2018](https://www.researchgate.net/publication/327347812) and the [Open Worm
Movement Database](http://movement.openworm.org/): **14,874** single-worm tracking records
(**measured**), on Zenodo as the community archive feeding Yemini 2013, later mutant deposits and
the screens below. Tierpsy Tracker extracts up to **2,763-8,289 features** per recording depending
on version (**measured**, see 1.6). Format: WCON interchange format, Zenodo, open access.

### 1.6 Recent high-throughput screens (2020-2026)

The clearest example found this pass: [Dyer et al., eLife/BMC Biology 2024-2025](https://pmc.ncbi.nlm.nih.gov/articles/PMC12465487/),
"High-throughput behavioural phenotyping of 25 *C. elegans* disease models including patient-specific
mutations." **25 CRISPR-edited strains**, **23** with a significant Tierpsy phenotype vs wild-type,
**8,289 features** per strain (**measured**). Gene list includes several already in the row 3-10
target set: **nca-2, unc-77, unc-80** (NALCN cation-channel complex), **glr-1** (glutamate receptor),
**unc-25** (GABA synthesis), **cat-4** (dopamine-synthesis cofactor), plus transporters **kcc-2,
snf-11** and cilium genes **bbs-1, bbs-2, tub-1, tmem-231** (**measured**, gene list from the paper).
Data: Zenodo (`10.5281/zenodo.12684118`, `.12684130`), full feature vectors, open access. Small (25
strains) but modern and fully quantitative - a working template for "run Tierpsy on a panel of
row-3-10 mutants" as a repeatable protocol, not a one-off.

### 1.7 CeNDR / CaeNDR natural variation

[CaeNDR](https://academic.oup.com/nar/article/52/D1/D850/7321992): **1,524 strains / 550 isotypes**
whole-genome sequenced as of the most recent release checked (**measured**, June 2023 count; a
2021-era release lists 1,378 strains / 540 isotypes). CaeNDR's own phenotype database is, in its
own words, still "developing"; the one phenotype file in a 2023 release was a gene-expression trait
table (Zhang et al. 2022), not behaviour. The useful signal today is not a systematic screen but a
handful of famous single-gene QTLs - **npr-1** (neuropeptide-Y-like receptor; aggregation and
foraging strategy, N2's gain-of-function allele vs the ancestral loss-of-function allele most wild
isolates carry) is the marquee case, already in the corpus (`STATE_OF_THE_ART.md` item 42) and
squarely in the row-9 peptide-receptor layer. Format: VCF + GWAS mapping portal, `caendr.org`.

### 1.8 Neuron ablation data

No single comprehensive ablation database was found; ablation data is scattered across papers,
most already cited in the corpus (`STATE_OF_THE_ART.md` items 11-14, 73: Chalfie 1985 touch
neurons, classic AVA/AVB/PVC/AVD ablations). One dedicated public dataset: [Scientific Data
2017](https://pmc.ncbi.nlm.nih.gov/articles/PMC5647482/), "Recordings of *C. elegans* locomotor
behaviour following targeted ablation of single motorneurons": **~300 videos**, single-cell laser
ablations of **5 identified motor neurons** plus mock-ablated controls (**measured**). These are
cell ablations, not gene knockouts - they test the connectome/circuit layer (row 7-8) directly, and
score exactly like a gene null: "silence this CeNGEN-identified cell, no refit."

### Summary table

| Source | Genes / strains | Phenotype type | Quant or binary | Format / size | Licence |
|---|---|---|---|---|---|
| WormBase WPO | ~8,000 genes (physiology branch, RNAi); ~5,200 (allele) | controlled-vocabulary calls | binary (per term) | REST/TSV/SimpleMine, tens of MB | not stated |
| Million Mutation Project | 2,007 strains, putative null in 8,150 genes | none pre-measured | n/a (genotype only) | VCF + CGC strains | public, CGC terms |
| TaoChongBao | 12,069 strains, missense in 20,914 genes | none pre-measured | n/a (genotype only) | web DB + bulk download | not confirmed |
| Yemini 2013 | 305 strains | full feature vector | **quantitative** (702 features) | web DB, moderate size | not confirmed |
| Open Worm Movement DB | 14,874 recordings | tracked features | quantitative | WCON/Zenodo | open (Zenodo CC) |
| 25-disease-model screen (2024-25) | 25 strains, 23 with phenotype | full feature vector | **quantitative** (8,289 features) | Zenodo | not stated |
| CaeNDR | 1,524 strains / 550 isotypes | mostly genomic; 1 expression trait file | n/a for behaviour (yet) | VCF + web portal | open web access |
| Scientific Data 2017 (ablation) | 5 neurons, ~300 videos | tracked locomotion | quantitative | raw video + derived data | open (Sci Data) |

## 2. Filter: how much of this hits genes the model represents

PLAN.md rows 3-10 define the model's target gene set (not all of it is coded yet - the Nicoletti
channel library in `src/wormemu/nicoletti.py` has **22 channel genes** built today; the rest of rows
7-10 are data tables, not simulator code, per `PLAN.md` section e). Counting the *target*, not just
what's built:

| Category (PLAN.md row) | Genes in the family (cited) | Coded today |
|---|---|---|
| Voltage-gated/two-pore/Ca-activated K, Ca, Na-leak channels (rows 3-6) | ~80+ K-channel genes genome-wide ([WormBook neuronal genome](https://wormbook.org/chapters/www_neuronalgenome/neuronalgenome.html), **inferred** rough figure) | 22 |
| Ligand-gated ion channel receptors, cys-loop superfamily (row 7) | **102** (61 nAChR-type + 41 GABA/Glu-gated/other; [Jones & Sattelle](https://pmc.ncbi.nlm.nih.gov/articles/PMC2257991/), **measured**) | 0 (mapping only) |
| Biogenic-amine GPCRs (row 10) | roughly two dozen (**guessed**, not independently verified this pass) | 0 (mapping only) |
| Neuropeptide precursor genes (row 9) | **160** (31 *flp* + 40 *ins* + 89 *nlp*; [Beets & Ripoll-Sanchez 2024](https://academic.oup.com/genetics/article/228/3/iyae141/7795512), **measured**, already in `NEUROPEPTIDES.md`) | 0 (mapping only) |
| Neuropeptide GPCRs (row 9) | >150 putative, 60 deorphanized (Beets 2023, **measured**) | 0 (mapping only) |
| Innexins (row 8) | **25** (**measured**, standard count) | 0 (counts only) |
| Transmitter synthesis/vesicular transport (row 7/10) | ~13 (*cat-1/2/4, tph-1, tbh-1, tdc-1, bas-1, unc-17, cha-1, eat-4, unc-25, unc-46, unc-47*) | 0 (identity only) |
| Core synaptic release machinery (row 7) | ~13 (*unc-13, unc-18, unc-10, unc-64, snb-1, rab-3, unc-31, egl-3, egl-21, sbt-1, unc-26, unc-104, cpx-1*) | 0 |
| **Total target set** | **~460-510 genes** (**derived**, sum of the above, some double-counting possible at the receptor/channel boundary) | **22** |

Against that ~480-gene target set:

- **WormBase, locomotion variant alone**: base rate is **2,022/~20,000 ≈ 10%** of the genome
  (**derived**, section 1.1). Channel/receptor/synaptic genes are disproportionately represented
  among classic "Unc" genes (they are largely *why* the Unc collection exists), so a reasoned
  mid-estimate is **150-250 of the ~480 target genes** carry at least one locomotion-variant
  annotation (**guessed**, 2-3x base-rate enrichment assumed). Across the whole "physiology
  phenotype" branch (pumping, egg-laying, defecation, chemotaxis too) the true count across all
  behaviour-adjacent WormBase terms is likely **250-350 of the ~480** (**guessed**) - all **binary**.
- **MMP**: 8,150/~20,000 ≈ 41% of genes have a putative null allele in a live strain; applied to the
  target set, **~195-200 of the ~480** have an MMP strain available (**derived**, independence
  assumed; a null in one paralog of a redundant receptor family is a weaker perturbation - section 3).
- **TaoChongBao**: missense coverage reaches 20,914 genes, essentially the whole coding genome, so
  **effectively all ~480 target genes** have a missense allele in a viable strain (**derived**),
  with zero phenotype data attached yet.
- **Yemini 2013**: not cross-referenced against the 305-strain list this pass; given the panel's
  stated focus on movement mutants, a plausible estimate is **60-100 of the 305 strains** carry a
  mutation in the target set (**guessed**), each with a full 702-feature quantitative vector - the
  single highest-value quantitative source per gene found this pass.
- **25-disease-model screen**: a direct count - **6 of 25 genes** (*nca-2, unc-77, unc-80, glr-1,
  unc-25, cat-4*) fall in the target set (**measured**), each with the full 8,289-feature profile.
- **CaeNDR**: effectively **1 gene** (*npr-1*), a well-characterised, already-quantified natural-
  variation effect (**measured**); the systematic phenotype database is not yet there to say more.

Net read: WormBase and MMP/TaoChongBao give large *counts* of genes with *some* recorded or
obtainable perturbation, but mostly as binary calls or bare genotypes. Yemini 2013 and the
25-disease-model screen give far fewer genes but *quantitative, multi-feature, reusable* phenotypes -
these are the ones worth building the first held-out test around (section 4).

## 3. Quality issues

- **RNAi in neurons is weak.** The cuticle and the neuronal RNAi pathway both resist
  double-stranded RNA uptake; most neurons need a sensitising background (*eri-1*, *rrf-3*) or a
  neuron-restricted *sid-1* rescue to show a phenotype at all. A WormBase "no phenotype by RNAi"
  call for a row-3-10 gene is **not evidence of no effect** - it is often a false negative specific
  to the assay, not the gene. Allele (mutant) annotations lack this problem and should be weighted
  far higher than RNAi annotations for any neuronal gene.
- **Genetic background effects.** MMP and TaoChongBao strains each carry ~400 other SNVs beyond the
  one of interest (section 1.2); classical alleles can carry second-site mutations from decades of
  outcrossing; even N2 has known lab-to-lab substrain drift. A measured phenotype is never purely
  the one gene's effect - this matters most for small effect sizes, less for the large, qualitative
  ones the first test should prioritise (section 4).
- **Binary vs quantitative scoring.** Most of the raw count (WormBase, MMP, TaoChongBao) is a
  presence/absence call against a controlled vocabulary, not a number. Score a binary call as a
  **directional hit test**: does the model's perturbed run cross the same qualitative threshold
  (e.g. "locomotion variant: yes/no" scored as whether bend-frequency or speed leaves the wild-type
  range used to call the phenotype in the source paper) - one bit per perturbation, cheap but weak.
  Score a quantitative dataset (Yemini 2013, the 25-disease-model screen, any Tierpsy output) the
  same way the rest of the project already does (`PLAN.md` c.4): the model's predicted value falls
  within the measured population's mean ± 2 SD, per feature, with a deliberately wrong model
  required to fail the test or it does not count as informative.

## 4. Proposed use

**Fitting vs held-out.** Per `PLAN.md` section c.2, fitting uses single-cell ephys (L1), the Randi
2023 signal-propagation atlas (L2), Atanas 2023 whole-brain statistics (L3), locomotion kinematics
(L4) and sensory-assay indices (L5) - all measured on wild-type (or baseline) animals. None of the
perturbation sources in section 1 feed any of those losses. **All of it should go to held-out**,
exactly as `PLAN.md` c.4 already states in principle: remove the gene from the relevant row-3-10
table (zero its density, receptor share, release rate or innexin conductance in the CeNGEN-identified
cells, with no refit anywhere else) and compare the resulting run against the perturbation's measured
or called phenotype. The one exception is ephys recorded *in* a mutant background purely to isolate a
current (e.g. pharmacology or a channel-null control used to subtract a current in the original
single-cell paper) - that is L1 data about the channel's own kinetics, not an emergent behaviour, and
belongs in fitting like any other ephys trace.

**One already-in-reach, high-value item:** `MANIFEST.md` section 5 records that the Randi 2023 OSF
project also hosts `exported_data_unc31*.tar.gz` - the same signal-propagation protocol run in
*unc-31* (CAPS, DCV release) mutants - which was skipped during the original fetch as "redundant."
It is not redundant for this purpose: it is a full functional-connectivity dataset in a mechanism-null
background (row 9-10, extrasynaptic signalling), already identified, not yet downloaded. Fetching it
is the cheapest possible addition to this corpus.

**The 20 most informative perturbations for a first test.** Chosen for: a clean single-gene
loss-of-function, an existing *quantitative* behavioural readout tied to that one mechanism, cells
expressing the gene already mapped by CeNGEN, and coverage across every row 3-10 category rather than
piling onto one.

1. *slo-1* (BK K channel, in the model's channel library) - locomotion rate and volatile-anaesthetic/ethanol dose-response, strongly quantitative
2. *egl-19* (L-type Ca channel, in the library) - egg-laying rate and pharyngeal EPG shape
3. *unc-103* (ERG-type K channel, in the library) - spontaneous egg-laying and locomotion rate (Egl-c)
4. *unc-2* (CaV2 N/P/Q-type Ca channel, in the library) - classic Unc locomotion-rate deficit
5. *unc-49* (GABA-A-type receptor) - aldicarb/levamisole "shrinker" assay, quantitative paralysis kinetics
6. *unc-29 / unc-38* (levamisole-receptor nAChR subunits) - dose-quantified paralysis-time assay, one of the cleanest quantitative drug-response readouts in the organism
7. *npr-1* (neuropeptide-Y-like GPCR) - aggregation index and on/off-food locomotion speed; also the marquee CaeNDR natural-variation case
8. *cat-2* (tyrosine hydroxylase, dopamine synthesis) - basal slowing response on food, a clean single-pathway quantitative assay
9. *tph-1* (tryptophan hydroxylase, serotonin synthesis) - egg-laying rate, pumping rate and roaming/dwelling bias, three quantitative readouts from one gene
10. *unc-31* (CAPS, dense-core-vesicle release) - locomotion/defecation/egg-laying rates, aldicarb resistance, **and** the Randi 2023 *unc-31* functional atlas already sitting in reach (above)
11. *unc-36* (Ca-channel alpha2delta subunit) - partners *unc-2*/*egl-19*, same assay family
12. *egl-2* (EAG-type K channel, in the library) - egg-laying defect and burrowing phenotype
13. *kqt-3* (KCNQ-type K channel, in the library) - nose-touch and chemosensory response deficits
14. *shk-1* (Shaker-type K channel, in the library) - pharyngeal pumping rate, levamisole hypersensitivity
15. *eat-4* (vesicular glutamate transporter) - pharyngeal pumping and chemotaxis-index deficits
16. *unc-17* (vesicular ACh transporter) - aldicarb-resistance dose-response, severe locomotion deficit
17. *unc-25* (GABA synthesis, GAD) - "shrinker" phenotype, quantitative body-bend assay; already in the 25-disease-model screen (1.6)
18. *glr-1* (AMPA-type glutamate receptor) - nose-touch habituation curve (reversal frequency over repeated taps), directly reusable against the existing tap-habituation corpus items
19. *flp-1* (FMRFamide-like neuropeptide precursor) - locomotor arousal/roaming bias, representative of the 160-gene peptide-precursor family
20. *unc-7 / unc-9* (innexins) - "kinking" uncoordinated locomotion with quantitative body-curvature measures, the most data-poor mechanism in the ledger (row 8) and so the one a held-out hit would most change

