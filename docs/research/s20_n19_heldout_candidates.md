# S20/N19 — held-out neuromodulation candidates (new, not previously spent)

Date: 2026-10-22. Excludes Dacks 2009, Strother 2018, Hige 2015, Lv 2024, Wan 2021 (already used/spent).
Magnitudes are NOT in this file — see sealed `docs/research/sealed/s20_n19_candidates_sealed.md`.

## Candidate 1 — octopamine, VS cells (visual system, LPTC)
Suver MP, Mamiya A, Dickinson MH (2012). "Octopamine Neurons Mediate Flight-Induced Modulation of Visual
Processing in Drosophila." *Curr Biol* 22(24):2294–2302. doi:10.1016/j.cub.2012.10.034.
Open access: no (Cell Press paywall; full text not reachable via WebFetch/curl — 403).
Cell type: vertical-system (VS) lobula-plate tangential cells, VS1–VS6 (named individually in
hemibrain/male-CNS; not sub-typed further here). Modulator: octopamine, bath/local application onto the
exposed brain. Prep: in vivo whole-cell patch clamp, quiescent (non-flying) tethered fly. Stimulus: wide-field
visual motion (optic flow); readout: VS-cell membrane potential / graded depolarization response to motion.
Sample size and exact figure not confirmed from accessible text (paywalled; flagged in sealed file).
Direction stated in abstract: excitatory — octopamine application "evokes responses... that mimic" the
flight-induced boost in VS-cell visual-motion sensitivity.

## Candidate 2 — serotonin, antennal-lobe GABAergic local neurons (5-HT7+)
Suzuki Y, Schenk JE, Tan H, Gaudry Q (2020). "A Population of Interneurons Signals Changes in the Basal
Concentration of Serotonin and Mediates Gain Control in the Drosophila Antennal Lobe." *Curr Biol*
30(6):1110–1118.e4. doi:10.1016/j.cub.2020.01.018.
Open access: unclear/likely paywalled (403 on publisher site; not confirmed in PMC).
Cell type: a GABAergic antennal-lobe local-neuron (LN) population defined by 5-HT7 receptor expression
(distinct from the uniglomerular PNs used in the excluded Dacks 2009 study); hemibrain/male-CNS LN subtype
mapping not given in accessible text. Modulator: serotonin (paracrine/basal, not just stimulus-evoked).
Prep: ex vivo whole-cell patch-clamp electrophysiology + pharmacology. Readout: LN depolarization and the
resulting GABAergic postsynaptic inhibition delivered onto projection-neuron output (a gain-control effect
on PNs). Sample size/figure not confirmed from accessible text. Direction stated in abstract: the 5-HT7+ LNs
are excited by serotonin and inhibit PN output (net inhibitory on the PN side) — a "subtractive" gain control.

## Candidate 3 — serotonin, lamina monopolar neuron L2 (visual system)
Sampson MM, Myers Gschweng KM, Hardcastle BJ, Bonanno SL, Sizemore TR, Arnold RC, Gao F, Dacks AM, Frye MA,
Krantz DE (2020). "Serotonergic modulation of visual neurons in Drosophila melanogaster." *PLOS Genetics*
16(8):e1009003. doi:10.1371/journal.pgen.1009003. Open access: yes.
Cell type: L2 lamina monopolar neuron (standard hemibrain/male-CNS name "L2"), a core optic-lobe cell type
present in Fly Cell Atlas/Davie-2018-style atlases. Modulator: serotonin, 100 µM, gravity-fed bath
perfusion. Prep: ex vivo, exposed optic lobe. Readout: GCaMP6f calcium signal in L2 axon terminals (medulla
layer M2). n = 4–8 flies (Fig. 4B). Direction stated in abstract/results: excitatory — serotonin increases
intracellular calcium in L2. (T1 and L1 were also tested in the same figure; T1 showed no significant
serotonin effect — a candidate null/negative-direction check rather than a magnitude check.)

## Candidate 4 — dopamine, ellipsoid-body ring neurons R2 and R5 (central complex)
Frighetto G, Zordan MA, Castiello U, Megighian A, Martin NS (2022). "Dopamine Modulation of Drosophila
Ellipsoid Body Neurons, a Nod to the Mammalian Basal Ganglia." *Front Physiol* 13:849142.
doi:10.3389/fphys.2022.849142. Open access: yes (PMC9048027).
Cell type: ellipsoid-body ring neurons R2 and R5 (classical nomenclature; exact hemibrain/male-CNS ER-type
correspondence not resolved from this source — flag for cross-check against the connectome before scoring).
Modulator: dopamine, 100 µM bath, 10 min pre-incubation. Prep: in vivo bioluminescent Ca2+ imaging
(GFP-aequorin, photon counts — not a GCaMP dF/F readout). Stimulus/readout: R2 challenged with nicotine
(Fig. 5), R5 challenged with picrotoxin (Fig. 6); photon-count response to the challenge drug, with and
without dopamine pretreatment. n = 12–13 flies (R2), 15–21 flies (R5). Direction: opposite signs in the two
cell types — excitatory/potentiating in R2 (via Dop1R1-like signaling) and inhibitory/suppressive in R5 (via
D2R-like signaling), as stated in the paper. Useful as a same-modulator, opposite-sign pair.

## Cross-check: 5-HT/OA/DA receptor expression in antennal-lobe uniglomerular PNs (qualitative only)
- Sizemore TR, Dacks AM (2016). "Serotonergic Modulation Differentially Targets Distinct Network Elements
  within the Antennal Lobe of Drosophila melanogaster." *Scientific Reports* 6:37119 (not J Neurosci, despite
  how it's sometimes cited). Used 5-HT-receptor MiMIC-GAL4 lines crossed to ChAT/GAD1-MiMIC-LexA to separate
  PN (cholinergic) vs LN (GABAergic) expression; found differential, receptor-specific targeting of PNs vs
  LNs rather than uniform 5-HT-receptor expression across the antennal lobe.
- Li H, Horns F, Wu B, Xie Q, Li J, Li T, Luginbuhl DJ, Quake SR (2017). "Classifying Drosophila Olfactory
  Projection Neuron Subtypes by Single-Cell RNA Sequencing." *Cell* 171:1206–1220 (Cell, not eLife).
  Comprehensive PN-class transcriptomes; supports that individual uniglomerular PN classes carry distinct,
  identifiable receptor-expression profiles (consistent with per-type, not per-synapse, modulator sensitivity),
  though the paper's emphasis is developmental wiring genes more than monoamine receptors specifically.
- Fly Cell Atlas / Davie et al. framework (the atlases named in the model spec) provide the quantitative
  per-type transcript-probability calls the model consumes; the two papers above are the qualitative,
  receptor-identity cross-check that those transcript calls are directionally sensible for PNs.
