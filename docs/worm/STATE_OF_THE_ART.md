# C. elegans emulation: state of the art

Research note, not canon. Scope: background for scoping a worm-emulation intermediate step
before fly work resumes. Labels: **measured** (reported directly in the cited source),
**derived** (computed from measured quantities by a stated method), **inferred** (plausible,
not directly shown). Plain factual descriptions of what a paper did carry no label. Nothing
here has been fit or used in any model; it is a map of the terrain. Compiled 2026-11-04.

## Contents

1. [Prior emulation efforts](#1-prior-emulation-efforts)
2. [Data available, by layer](#2-data-available-by-layer)
3. [Behaviour corpus (validation scoreboard)](#3-behaviour-corpus-validation-scoreboard)
4. [Gaps](#4-gaps)
5. [Assessment](#5-assessment)

---

## 1. Prior emulation efforts

**OpenWorm (c302 / Sibernetic / Geppetto).** [c302](https://royalsocietypublishing.org/rstb/article/373/1758/20170379/42135/c302-a-multiscale-framework-for-modelling-the)
is a NeuroML2-based generator for neuron/network models at several abstraction levels (A: abstract
integrate-and-fire up to C/D: multicompartment, channel-level), built on the Varshney 2011 /
Cook 2019 connectome tables. Sibernetic is a smoothed-particle-hydrodynamics body/fluid simulator
using the Boyle & Cohen muscle model; Geppetto is the visualisation/web layer. **Achieved:**
foundational open infrastructure and NeuroML standardisation; a muscle/body simulator that
reproduces qualitative crawling shapes; one demonstrated pipeline (with a Vienna group) that
drives Sibernetic directly from c302 output. **Fidelity:** neuron and muscle models exist at
several abstraction levels but are not integrated end-to-end for the full 302-neuron animal in
closed loop. **Validated against:** qualitative body-shape/locomotion patterns; no published
quantitative fit to a named behaviour dataset across stimuli. **Lacked:** closed-loop full
nervous system, neuromodulation/extrasynaptic signalling, broad sensory repertoire, and (as of
late 2024, per the project's own retrospectives) 13+ years without a published whole-animal
behavioural reproduction. [OpenWorm science resources](https://openworm.org/science.html);
[Wikipedia overview](https://en.wikipedia.org/wiki/OpenWorm).

**BAAIWorm / MetaWorm (2024).** Companion papers in *Nature Computational Science* 4(12), Dec 2024:
[MetaWorm preprint](https://www.biorxiv.org/content/10.1101/2024.02.22.581686v2.full) and
[companion full-connectome paper](https://www.nature.com/articles/s43588-024-00740-2). The
"eworm" core brain model has **136 neurons** (15 sensory, 41 inter, 80 motor) with realistic
multicompartment morphology and **1,901** inter-neuron synaptic connections; the companion paper
describes a biophysically detailed network for the **full 302-neuron** animal plus muscle
dynamics (exact overlap between the two neuron counts is not fully resolved from abstracts alone
— inferred, not independently verified against full text in this pass). The body model has 96
muscle actuators. **Achieved:** true closed-loop brain-body-environment interaction (sensory
input from a simulated environment drives muscles which deform the body which changes sensory
input), reproducing zigzag chemotaxis-like approach to an attractant, and showing that synaptic
perturbations propagate to altered locomotion. **Validated against:** qualitative chemotaxis-like
trajectories, not a quantified chemotaxis-index benchmark. **Lacked:** neuropeptide/monoamine
signalling, non-neural tissue, multiple behaviours beyond locomotion/orientation, and (as the
fly-emulation project's own research note already flags) shared cell templates and inferred
connection properties remain assumptions, not direct reconstructions of a single animal.

**modWorm (Kim, Florman, Santos, Alkema & Shlizerman; bioRxiv, posted 2025-06-12).**
[Preprint](https://www.biorxiv.org/content/10.1101/724328v3) /
[PMC](https://pmc.ncbi.nlm.nih.gov/articles/PMC12045391/). A 7-module pipeline: intracellular
dynamics → electrical extracellular dynamics → chemical extracellular dynamics → neural activity
to muscle calcium → calcium to force → force to posture → proprioceptive feedback. Couples the
**full mapped somatic connectome (279 neurons)** to a viscoelastic body. **Achieved:** a working,
open, modular framework used to identify which sensorimotor pathways drive specific behaviours by
perturbing modules. **Validated against:** locomotory behaviour and some perturbation responses;
scope of quantitative behavioural match not established from the abstract. **Lacked:**
neuropeptide/hormonal signalling, non-neural tissue, and (as with all of the above) no claim of
coverage across the literature's behaviour corpus.

**Si elegans (EU FP7, 2013–2017).** [Project page](https://iopscience.iop.org/article/10.1088/1741-2560/13/6/065001),
[university page](https://www.ntu.ac.uk/research/groups-and-centres/projects/si-elegans). Proposed
a massively parallel FPGA hardware architecture to emulate the ~302-neuron nervous system in
biological real time, embodied in a virtual environment, served through an open web portal.
**Achieved/fidelity:** design and architecture papers (2016); no major published whole-animal
behavioural validation found in this pass — appears to have stalled at the framework/proposal
stage after FP7 funding ended. Listed for completeness; treat as largely superseded by the
software efforts above.

**Izquierdo & Beer, and Olivares, Izquierdo & Beer (neuromechanical VNC models, 2015–2021).**
[Izquierdo & Beer, bioRxiv](https://www.biorxiv.org/content/10.1101/710566v3.full);
[Olivares et al. 2021, Frontiers in Computational Neuroscience](https://par.nsf.gov/servlets/purl/10286537).
A dynamical-systems model of the ventral nerve cord (anatomically constrained, graded —
non-spiking — neuron dynamics with gap junctions) drives a Boyle-Cohen-style muscle/body model.
Parameters are evolved/optimised (not fit to channel-level data) to find configurations that
produce forward locomotion without pacemaker neurons or stretch-receptor feedback; later work
extends to backward locomotion and gait modulation. **Achieved:** existence proof that *multiple*
chained VNC oscillators (rather than a single central pattern generator) can drive forward
locomotion, with gap junctions between motor-neuron classes coordinating them. **Validated
against:** kinematic features of forward-crawling (bend frequency/wavelength ranges) and some
comparison to neuron-ablation locomotor deficits. **Lacked:** sensory integration beyond simple
proprioception, no other behaviours, parameters are searched/evolved rather than derived from
measured channel densities, and it models a VNC sub-circuit, not the whole animal.

**Kunert, Varshney & Wicks (connectome dynamics, 2011–2017).**
[Kunert et al. 2017, PLoS Comp Biol](https://journals.plos.org/ploscompbiol/article?id=10.1371%2Fjournal.pcbi.1005261);
earlier foundational model in
[Kunert, Shlizerman & Kutz, "Low-dimensional functionality..."](https://www.researchgate.net/publication/258083880_Low-dimensional_functionality_of_complex_network_dynamics_Neuro-sensory_integration_in_the_Caenorhabditis_elegans_connectome).
Extends the Wicks et al. 1996 single-compartment conductance model to the **full somatic
connectome (279 neurons)** using Varshney 2011 synapse/gap-junction counts, with no body and no
stimulus-specific sensory transduction (pure open-loop neural dynamics). **Achieved:** showed the
undriven network settles to a static state, and that arbitrary external input only ever excites
one of six attractor-like dynamical patterns, whose shape is set by the connectome; used the model
to predict behavioural deficits from simulated neuron injury. **Validated against:** qualitative
correspondence of excited patterns to known behavioural circuits, and some comparison to published
ablation phenotypes (e.g. touch-circuit ablations). **Lacked:** body, muscle, channel diversity
(single-compartment per neuron), and any sensory-driven closed loop.

**Nicoletti et al. (single-neuron and muscle biophysics, 2019 & 2024).**
[Nicoletti et al. 2019, PLoS ONE](https://journals.plos.org/plosone/article?id=10.1371%2Fjournal.pone.0218738)
built Hodgkin-Huxley-type whole-cell models of **two** individual neurons, AWCon (sensory) and RMD
(motor), with channel conductances (e.g. SLO-1, SLO-2 both set to 15 nS) fit directly to that
neuron's own voltage/current-clamp traces where available, filled in from homologous channels in
other organisms where not. [Du, Crodelle et al. 2024, PLoS Comp Biol](https://journals.plos.org/ploscompbiol/article?id=10.1371%2Fjournal.pcbi.1012318)
/ [bioRxiv](https://www.biorxiv.org/content/10.1101/2024.07.15.603498v1.full) extended the same
approach to **body-wall muscle cells**, the first experimentally validated whole-cell
electrophysiological muscle model, finding a preferred oscillation frequency in the same band as
locomotor bend frequency. **Validated against:** the specific recorded cell's own current/voltage
traces, not network behaviour. **Lacked:** coverage — only a handful of the ~118 neuron classes
have this level of direct biophysical characterisation; no network integration into locomotion in
these papers. A related 2025 effort,
["A data-driven biophysical network model reproduces C. elegans premotor neural dynamics"](https://arxiv.org/pdf/2501.00278),
extends this single-cell-biophysics approach toward a small premotor network (scope not
independently verified beyond the title/abstract in this pass).

**Boyle & Cohen (body-wall muscle and body mechanics, 2008–2012).**
[Boyle & Cohen 2008, Biosystems](https://www.sciencedirect.com/science/article/abs/pii/S0303264708001408);
[Boyle PhD thesis 2009](https://etheses.whiterose.ac.uk/id/eprint/1377/1/jboyle.pdf);
[Boyle, Berri & Cohen 2012, Frontiers in Comp. Neuroscience](https://www.researchgate.net/publication/221694495_Gait_Modulation_in_C_elegans_An_Integrated_Neuromechanical_Model).
Treats body-wall muscle as a simple (low-pass-filtered) actuator driven directly by the known
motor-neuron innervation pattern, combined with a mechanical body (viscoelastic rod in fluid).
**Achieved:** quantitatively reproduced gait kinematics (bend frequency/wavelength) and the
measured gait transition with medium viscosity, without needing detailed muscle ion-channel
biophysics — i.e. body mechanics alone explained a large share of the gait. This model (or its
descendants) underlies most of the body/muscle component in OpenWorm, Izquierdo-Beer, and
Olivares et al. **Lacked:** no closed sensory loop in the earliest version, no non-body-wall
muscle (pharynx, vulva, anus, male tail), and neural drive is a prescribed input, not an emergent
output of a modelled nervous system.

**2024–2026 miscellany.** [NeuroSimWorm](https://www.sciencedirect.com/science/article/abs/pii/S0925231225007271)
(2025) proposes a multisensory simulation framework (scope not independently verified in this
pass). [Digital Sphinx](https://elifesciences.org/reviewed-preprints/111516) (2024/2025 reviewed
preprint) trains a decoder so that a *C. elegans* connectome-derived graph can drive a *fly* body
model — a useful cautionary result for this project: behavioural appearance under a trained
decoder does not establish circuit identity, i.e. it is exactly the kind of result the fly-
emulation project's own "no decoders" rule is designed to rule out. The
[State of Brain Emulation Report 2025](https://arxiv.org/pdf/2510.15745) (an independent ~175-page
cross-organism survey) places *C. elegans* as the best-recorded of five surveyed organisms, with
roughly 50% of its neurons recorded at single-cell resolution in some functional dataset, but
names non-synaptic signalling, the absence of a fully proofread/consensus connectome, and
generally immature model integration as the open blockers; it gives no organism-specific timeline
for the worm, only a human-whole-brain-emulation estimate of decades out, which is not directly
informative for this project's narrower target.

## 2. Data available, by layer

**Connectomes (structural).**
[White et al. 1986](https://royalsocietypublishing.org/doi/10.1098/rstb.1986.0056) — original
hermaphrodite wiring diagram from serial-section EM (Brenner lab). Access: digitised in WormAtlas/
WormWiring, not the raw EM.
[Varshney et al. 2011, PLoS Comp Biol](https://doi.org/10.1371/journal.pcbi.1001066) — re-curated
directed, weighted synapse + gap-junction graph for ~300 neurons; the substrate for most dynamics
papers above. Access: paper's supplementary tables, WormAtlas.
[Cook et al. 2019, Nature](https://www.nature.com/articles/s41586-019-1352-7) — whole-animal
connectomes of **both sexes**: hermaphrodite graph **460 nodes** (302 neurons, 132 muscles, 26
non-muscle end organs); male graph **579 nodes** (385 neurons, 155 muscles, 39 non-muscle end
organs). Access: [wormwiring.org](https://wormwiring.org), [OpenWorm Connectome Toolbox](https://openworm.org/ConnectomeToolbox/Cook_2019/).
[Witvliet et al. 2021, Nature](https://www.nature.com/articles/s41586-021-03778-8) — **8** full
brain connectomes across development (3× L1, 2× L2, 1× L3, 2× adult), showing the overall
geometric scaffold is fixed early but synaptic weights change substantially, and that individuals
differ measurably from each other. Access: [OpenWorm toolbox](https://openworm.org/ConnectomeToolbox/Witvliet_2021/).
[Brittin et al. 2021, Nature](https://doi.org/10.1038/s41586-021-03284-x) — a "contactome": every
physical membrane contact (not just chemical synapses) in the nerve ring at two ages (L4 and
adult), from EM volumes; the first nanometre-resolution map of all neuropil adjacency. Access:
[Zenodo](https://zenodo.org/records/4763083), wormwiring.org.

**Gene expression.** [CeNGEN](https://www.cengen.org); primary paper
[Hammarlund et al. 2018, Neuron](https://doi.org/10.1016/j.neuron.2018.07.042). Bulk + single-cell
RNA-seq covering **all 302** hermaphrodite neurons across **118** anatomically distinct neuron
classes, with threshold-calibrated per-gene expression calls; a 2025 refinement
([bioRxiv](https://www.biorxiv.org/content/10.1101/2025.01.26.634951v1.full)) improves isoform
resolution. This is the main route from "which channel/receptor genes are expressed where" to a
per-neuron-class parameter.

**Neuropeptide connectome.** [Beets et al. 2023](https://openworm.org/ConnectomeToolbox/Beets_2023/)
report a genome-wide peptide–GPCR interaction map (**150+** putative peptide-activated GPCRs
deorphanised). [Ripoll-Sánchez et al. 2023, Neuron](https://doi.org/10.1016/j.neuron.2023.09.043)
combine that ligand–receptor map with CeNGEN expression to build a predicted "neuropeptidergic
connectome" — a wireless signalling network far denser than the synaptic one. This is binary
(peptide X can activate receptor Y in neuron Z), not kinetic.

**Functional atlas.** [Randi et al. 2023, Nature](https://www.nature.com/articles/s41586-023-06683-4) —
direct optogenetic stimulation of each of many neurons combined with simultaneous NeuroPAL-
identified whole-brain calcium imaging, measuring sign, strength, kinetics and causal direction of
signal propagation across **23,433** neuron pairs in the head. Key result: this functional atlas
predicts spontaneous dynamics better than any model built from the anatomical connectome alone —
extrasynaptic signalling matters structurally. Access: [DANDI 001075](https://dandiarchive.org/dandiset/001075).

**Whole-brain imaging.** [Kato et al. 2015, Cell](https://doi.org/10.1016/j.cell.2015.09.034) —
simultaneous calcium imaging of many head neurons in immobilised/restrained animals, revealing a
low-dimensional manifold embedding the motor-command sequence. [Nichols et al. 2017, Science](https://doi.org/10.1126/science.aam6851) —
brain-wide imaging showing a single global brain state underlies sleep-like behaviour.
[Atanas et al. 2023, Cell](https://doi.org/10.1016/j.cell.2023.07.035) — freely moving, most-of-
brain calcium imaging with NeuroPAL identity, across many behavioural/internal states, at
multiple timescales. [Yemini et al. 2021, Cell, NeuroPAL](https://doi.org/10.1016/j.cell.2021.03.045) —
the multicolour transgenic landmark strain that makes unambiguous whole-brain neuron ID routine,
and that underlies Randi/Atanas/Flavell-lab datasets. The Flavell lab maintains ongoing freely-
moving whole-brain datasets tied to internal states (e.g. serotonergic system mapping, aversive
responses), released piecemeal via Zenodo/Dryad — no single public dataset yet covers >90% of
neurons in freely behaving animals across many conditions (inferred from search of current
releases, not exhaustively verified).

**Electrophysiology per neuron.** [Goodman, Hall, Avery & Lockery 1998, Neuron](https://www.sciencedirect.com/science/article/pii/S0896627300810144)
established tight-seal whole-cell patch clamp in *C. elegans* (ASER across 4 developmental stages,
plus 42 unidentified neurons at one stage). Direct current/voltage-clamp recordings exist for only
a small minority of the 118 neuron classes — single digits to low tens, by neuron-class count
(**inferred, approximate**; no single consolidated count was verified in this pass). The rest rely
on inference (Section 4).

**Muscle physiology.** Body-wall muscle: dissected-preparation patch clamp (used by Boyle & Cohen)
plus the 2024 Du/Crodelle whole-cell model above. Pharyngeal muscle: well characterised
electrically via the electropharyngeogram (E and P spikes), reviewed in
[WormBook, Feeding](https://www.ncbi.nlm.nih.gov/books/NBK20143/). Vulval, anal-sphincter and
male-specific sex muscles: anatomically described, not biophysically modelled at the same level.

**Body mechanics.** Young's modulus estimates vary by **2+ orders of magnitude** depending on
method: AFM indentation 8–2000 kPa; a 2024 finite-element study gives cuticle 75–140 kPa, muscle
600–850 kPa, pseudocoelom 48–185 kPa (natural variation pseudocoelom 42–275 kPa, muscle
910–2,100 kPa) — [Frontiers in Bioengineering 2024](https://www.frontiersin.org/journals/bioengineering-and-biotechnology/articles/10.3389/fbioe.2024.1335788/xml/nlm).
[Park et al., PNAS](https://www.pnas.org/doi/10.1073/pnas.0702138104) used a piezoresistive
microcantilever, modelling the worm as a hollow cylindrical shell, to extract modulus and
hydrostatic pressure. [Biophysical Journal 2015, "Worms under pressure"](https://www.cell.com/article/S0006-3495(15)00281-7/fulltext)
directly measures bulk mechanical response under isotropic pressure and finds bulk mechanics are
largely **independent of the cuticle** (i.e. hydrostatic-pressure-dominated, hydroskeleton-like).

**Behaviour databases.** [Open Worm Movement Database](http://movement.openworm.org/) —
**14,874** single-worm tracking records (videos, skeletons, features), via Zenodo community.
[Yemini et al. 2013, Nature Methods](https://doi.org/10.1038/nmeth.2560) — Worm Tracker 2.0:
**300+** strains, ~**10,000** worms, **700+** phenotypic features per worm. [Tierpsy Tracker](https://www.biorxiv.org/content/10.1101/377960v1.full.pdf) —
open-source multi-worm tracker with an improved feature set (peak strain-classification accuracy
56.2% at 1,024 features vs 47.8% at 256 Yemini-style features, in the paper's own benchmark).

**Learning/memory.** Classic salt-chemotaxis associative learning (pairing salt with starvation),
NMDA-receptor-dependent memory (see behaviour corpus), thermotaxis associative learning (pairing
feeding state with temperature), and tap-withdrawal habituation/sensitisation (Rankin, Beck & Chiba
1990, below) are all well-studied paradigms with quantified acquisition/retention curves; no single
dataset spans all of them for the same animals.

**Internal states.** Roaming/dwelling (serotonin/PDF circuit, Flavell et al. 2013), lethargus/
developmental sleep (Raizen et al. 2008), satiety quiescence (You et al. 2008) — see behaviour
corpus for citations. Brain-wide imaging during these states exists (Nichols 2017, Atanas 2023)
but mechanistic (channel/receptor-level) models of the state-switching circuitry itself are
partial.

**Feeding, egg-laying, defecation, male mating** — see behaviour corpus (Section 3); each has a
WormBook chapter and a quantified core metric ([Feeding](https://www.ncbi.nlm.nih.gov/books/NBK20143/),
[Defecation](https://www.ncbi.nlm.nih.gov/books/NBK20047/),
[Male mating behavior](https://www.wormbook.org/chapters/www_malematingbehavior/malematingbehavior.html)).

**Metabolism.** [Yilmaz & Walhout 2016, Cell Systems](https://doi.org/10.1016/j.cels.2016.04.012) —
genome-scale metabolic model iCEL1273 (1,273 genes, 623 enzymes, 1,985 reactions). [MERGE,
Mol Syst Biol 2020](https://link.springer.com/article/10.15252/msb.20209649) — extends this to
tissue-resolved (muscle/intestine/hypodermis) predictions from single-cell RNA-seq. [A systems-
level, semi-quantitative landscape of metabolic flux in C. elegans, Nature 2025](https://www.nature.com/articles/s41586-025-08635-6) —
Perturb-seq of ~900 metabolic genes integrated with the network model and validated by stable-
isotope tracing, giving the most direct empirical flux dataset to date. None of this is resolved
to individual-neuron metabolic budgets.

**Innexin-specific gap junctions.** [Altun et al. 2009, Dev. Dynamics / high-resolution map](https://pmc.ncbi.nlm.nih.gov/articles/PMC2732576/) —
promoter-GFP expression map for all **25** innexin genes; UNC-7 and UNC-9 are the most broadly
expressed. Biophysical properties (conductance, rectification) are only characterised in
heterologous systems for a handful of specific innexin pairs (e.g. UNC-7/UNC-9); most combinations
are uncharacterised (Section 4).

## 3. Behaviour corpus (validation scoreboard)

| # | Behaviour | Measured quantity | Dataset / paper | Depends on (layers) |
|---|---|---|---|---|
| 1 | Crawling speed | ~0.21–0.26 mm/s (measured) | Fang-Yen 2010 PNAS gait-adaptation work, cited via [arXiv 2006.10122](https://arxiv.org/pdf/2006.10122) | locomotion CPG; body-wall muscle; body mechanics; agar substrate |
| 2 | Swimming speed | ~0.35–0.36 mm/s (measured) | same gait-adaptation literature | as above; fluid mechanics |
| 3 | Crawling bend frequency | ~0.3–0.5 Hz | gait-adaptation literature above | CPG; muscle; substrate viscosity |
| 4 | Swimming bend frequency | ~1.5–2 Hz | gait-adaptation literature above | CPG; muscle; fluid viscosity |
| 5 | Crawling wavelength | ~0.79 mm (≈2 bends/body length) | as above | body mechanics; CPG |
| 6 | Swimming wavelength | ~2.12 mm (≈1 bend/body length) | as above | body mechanics; CPG |
| 7 | Gait transition with medium viscosity | continuous frequency/wavelength shift vs viscosity | Fang-Yen 2010 PNAS; Boyle, Berri & Cohen 2012 | proprioceptive feedback; muscle force-velocity; fluid mechanics |
| 8 | Forward/backward VNC oscillator chaining | multiple local oscillators sufficient, no single pacemaker needed | Izquierdo & Beer [bioRxiv](https://www.biorxiv.org/content/10.1101/710566v3.full); Olivares et al. [2021](https://par.nsf.gov/servlets/purl/10286537) | VNC connectome; gap junctions; graded neuron dynamics |
| 9 | Spontaneous reversal rate | strain/condition-dependent, quantified in Tierpsy/OpenWorm feature sets | [Open Worm Movement Database](http://movement.openworm.org/); [Yemini 2013](https://doi.org/10.1038/nmeth.2560) | AVA/AVB/PVC/AVD premotor circuit |
| 10 | Omega-turn rate and geometry | quantified postural feature | Tierpsy Tracker; Yemini 2013 phenome | premotor circuit; body mechanics |
| 11 | Anterior gentle-touch response (ALM/AVM circuit) | reversal probability on anterior touch | [Chalfie et al. 1985](https://doi.org/10.1523/JNEUROSCI.05-04-00956.1985) laser ablation | touch-receptor neurons; AVD/AVA interneurons; locomotion |
| 12 | Posterior gentle-touch response (PLM circuit) | forward acceleration on posterior touch | Chalfie et al. 1985 | touch-receptor neurons; AVB/PVC interneurons |
| 13 | Harsh-touch response (PVD-mediated) | distinct withdrawal from gentle-touch pathway | WormBook [Mechanosensation](https://www.wormbook.org/chapters/www_mechanosensation/mechanosensation.html) | PVD nociceptors; separate interneuron pathway |
| 14 | Nose-touch avoidance | reversal probability on anterior collision | [ASH IP3R paper, PLoS Genetics 2009](https://journals.plos.org/plosgenetics/article?id=10.1371%2Fjournal.pgen.1000636) | ASH polymodal neuron; itr-1/IP3 signalling |
| 15 | Tap-withdrawal habituation (short-term) | response decrement over repeated taps | [Rankin, Beck & Chiba 1990](https://doi.org/10.1016/0166-4328(90)90074-O) | tap-withdrawal circuit; synaptic depression |
| 16 | Tap-withdrawal long-term habituation | retention over hours after spaced training | Rankin et al. and successors, reviewed [Learn. Mem. 2001](https://learnmem.cshlp.org/content/8/2/63.full) | as above; protein-synthesis-dependent plasticity |
| 17 | Tap-withdrawal response probability vs inter-stimulus interval | parametric response curve | temporal-processing literature, [arXiv 1803.04085](https://arxiv.org/pdf/1803.04085) | mechanosensory circuit dynamics |
| 18 | NaCl chemotaxis | quantified chemotaxis index toward attractant gradient | classic Ward/Bargmann chemotaxis assays, reviewed in WormBook Chemotaxis | ASE sensory neurons; AIY/AIB interneurons; biased random walk + klinotaxis |
| 19 | Diacetyl attraction | chemotaxis index | AWA-mediated attraction, standard chemotaxis assay | AWA; downstream interneurons |
| 20 | Benzaldehyde/isoamyl alcohol attraction | chemotaxis index | AWC-mediated attraction, standard chemotaxis assay | AWC; downstream interneurons |
| 21 | Biased-random-walk / klinotaxis strategy | pirouette rate modulation + weathervaning | Pierce-Shimomura klinotaxis analyses | chemosensory neurons; locomotor state switching |
| 22 | CO2 avoidance | avoidance index, cGMP-pathway dependent | [PNAS 2008](https://www.pnas.org/doi/10.1073/pnas.0707469105) | BAG neurons; TAX-2/TAX-4 |
| 23 | Oxygen preference / aerotaxis | peak preference ~8–10% O2 depending on circuit | [PLoS Biology 2006](https://journals.plos.org/plosbiology/article?id=10.1371%2Fjournal.pbio.0040274) | URX/AQR/PQR; soluble guanylate cyclases |
| 24 | O2–CO2–temperature cross-modulation | URX tonic signalling sets CO2 response gain | PLoS Genetics 2014 cross-modulation paper | URX; RIA; BAG |
| 25 | Hyperosmotic (glycerol) avoidance | fraction escaping a glycerol ring within set time | ASH osmotic-avoidance assays | ASH; downstream circuit |
| 26 | Osmotic avoidance adaptation | reduced avoidance after pre-exposure | osmotic-avoidance adaptation literature | ASH; receptor/channel adaptation |
| 27 | Copper avoidance | avoidance index, food-state dependent | dopamine-modulated avoidance, [PMC3061029](https://pmc.ncbi.nlm.nih.gov/articles/PMC3061029/) | ASH; dopaminergic modulation |
| 28 | Thermotaxis set-point (isothermal tracking) | tracks near cultivation temperature | [Mori & Ohshima 1995, Nature](https://doi.org/10.1038/376344a0) | AFD; AIY/AIZ; RIA |
| 29 | Bidirectional thermotaxis strategy | distinct sensorimotor strategies above/below set point | [PNAS 2014](https://www.pnas.org/doi/abs/10.1073/pnas.1315205111) | AFD; downstream motor strategy switch |
| 30 | Noxious-heat avoidance | rapid withdrawal, distinct from thermotaxis circuit | FLP/AFD nociceptive literature | FLP thermal nociceptors; AVD/AVA |
| 31 | Dauer formation vs pheromone + temperature | dauer-entry fraction as function of ascaroside dose and temperature | classic dauer-pheromone dose-response literature | chemosensory neurons; AFD-via-ttx-1; insulin/DAF-16 pathway |
| 32 | Pharyngeal pumping rate (fed) | ~4–5 Hz, ~250 pumps/min | Avery & Horvitz 1989, reviewed [WormBook Feeding](https://www.ncbi.nlm.nih.gov/books/NBK20143/) | MC/M4 pharyngeal neurons; pharyngeal muscle |
| 33 | Pharyngeal pumping, single-pump duration | ~170 ms | same source | pharyngeal muscle electrical properties |
| 34 | Pharyngeal pumping, food-dependent on/off switching | pumping ceases within seconds off food | WormBook Feeding | pharyngeal neurons; chemosensory food detection |
| 35 | Pharyngeal pumping, serotonin regulation | rate modulated by exogenous serotonin | [Scientific Reports 2016](https://www.nature.com/articles/srep22940) | serotonergic neuromodulation of MC/pharynx |
| 36 | Foraging head-swing rate (on vs off food) | quantified head-swing frequency change | automated feeding-tracking literature, [eLife 2022](https://elifesciences.org/articles/77252) | chemosensory food detection; head motor circuit |
| 37 | Roaming/dwelling bout durations and switching | long-lasting (minutes-scale) locomotor states | [Flavell et al. 2013, Cell](https://doi.org/10.1016/j.cell.2013.08.001) | serotonin (MOD-1); PDF neuropeptide; locomotor circuit |
| 38 | Lethargus duration per larval stage | ~2 hours per molt, quiescent | [Raizen et al. 2008, Nature](https://doi.org/10.1038/nature06535) | egl-4/PKG; sensory-neuron gating |
| 39 | Developmental-sleep homeostatic rebound | increased quiescence after deprivation | Raizen et al. 2008; [two-mechanism follow-up, eLife 2015](https://elifesciences.org/articles/04380) | same circuitry; homeostatic drive |
| 40 | Satiety quiescence onset after refeeding | gradual inhibition of feeding/movement | [You, Kim, Raizen & Avery 2008, Cell Metabolism](https://doi.org/10.1016/j.cmet.2008.01.005) | insulin; cGMP (egl-4); TGF-β signalling |
| 41 | Global quiescent brain state during lethargus | brain-wide downregulation of activity | [Nichols et al. 2017, Science](https://doi.org/10.1126/science.aam6851) | ALA/RIS sleep neurons; global neuromodulation |
| 42 | Social feeding / aggregation (npr-1-dependent) | solitary vs social feeding phenotype | classic npr-1 aggregation literature | NPR-1 neuropeptide receptor; O2-sensing circuit |
| 43 | Egg-laying rate, basal | ~1–3 eggs/hr depending on temperature | [Comm Biology 2022](https://www.nature.com/articles/s42003-022-03819-6); [life-cycle data](https://wormatlas.org/papers/Byerly%20et%20al%201976.pdf) | HSN/VC egg-laying circuit; vulval muscle |
| 44 | Egg-laying rate, serotonin/nicotine-stimulated | ~7.4 eggs/hr | Comm Biology 2022 | serotonergic modulation of HSN; vulval muscle |
| 45 | Egg-laying rate, peak during adulthood | up to ~9 eggs/hr at ~92 h post-hatch | life-cycle/egg-laying literature | reproductive-stage-dependent circuit state |
| 46 | Inter-egg-interval distribution (active/inactive states) | bimodal timing | classic egg-laying-state literature (WormBook) | HSN bistability; stretch feedback |
| 47 | Brood size | ~300 offspring per hermaphrodite | classic life-cycle literature, [Byerly et al. 1976](https://wormatlas.org/papers/Byerly%20et%20al%201976.pdf) | germline + egg-laying circuit, whole-organism |
| 48 | Generation time | ~3.5 days at 20 °C | Byerly et al. 1976 | whole-organism developmental timing |
| 49 | Defecation motor program (pBoc) cycle period | 45 s (±<3 s at 20 °C), temperature-insensitive 19–30 °C | [WormBook Defecation](https://www.ncbi.nlm.nih.gov/books/NBK20047/); Thomas 1990 | intestinal IP3R clock; AVL/DVB motoneurons |
| 50 | Defecation IP3R-dependent rhythm | ~45–50 s rhythm set by posterior-intestine Ca2+ oscillation | [Dal Santo et al. 1999, Cell](https://doi.org/10.1016/s0092-8674(00)81510-x) | itr-1 IP3 receptor; intestinal Ca2+ signalling |
| 51 | Defecation reset by touch | next DMP occurs 45 s after a touch perturbation | WormBook Defecation | mechanosensory input to the intestinal clock |
| 52 | Defecation step sequence (pBoc, aBoc, eBoc) | discrete motor steps with fixed order and timing | WormBook Defecation | AVL/DVB GABAergic motoneurons; enteric muscle |
| 53 | HSN/defecation circuit coupling | egg-laying command neurons modulate defecation timing | [PMC7252377](https://www.ncbi.nlm.nih.gov/pmc/articles/PMC7252377/) | HSN; VC; AVL/DVB |
| 54 | Male mating, full sequence completion | 6-step sequence: response, backing, turning, vulva location, spicule insertion, sperm transfer | [WormBook Male Mating Behavior](https://www.wormbook.org/chapters/www_malematingbehavior/malematingbehavior.html) | male-specific sensory rays, hook, spicule neurons; male CNS |
| 55 | Male response to hermaphrodite contact | initiation probability/latency | WormBook Male Mating Behavior | ray sensory neurons |
| 56 | Male ventral turning | sharp ventral tail coil, can be bypassed if vulva found early | WormBook Male Mating Behavior | ray neurons; turning motor program |
| 57 | Male vulva-location search | search pattern using ≥8 overlapping sensory neurons | WormBook Male Mating Behavior | hook (HOA/HOB); postcloacal sensilla |
| 58 | Male spicule insertion trigger | initiates on cloaca–vulva contact | WormBook Male Mating Behavior | spicule neurons (SPV/SPD); sex muscles |
| 59 | Male sperm transfer / ejaculation timing | coordinated with spicule insertion | WormBook Male Mating Behavior | male-specific motor circuit |
| 60 | Male mating incorporates sex-shared defecation components | males suppress defecation during mating, reuse DVB/AVL-adjacent circuitry | [G3 2017](https://academic.oup.com/g3journal/article/7/2/647/6027520) | shared defecation/mating circuit overlap |
| 61 | Salt (NaCl) chemotaxis associative learning | shift from attraction to avoidance after salt+starvation pairing | classic salt-learning paradigm, reviewed in [Learn. Mem. 2010](https://learnmem.cshlp.org/content/17/4/191.full.pdf) | ASE; AIY; insulin signalling |
| 62 | NMDA-dependent long-term memory for salt learning | memory persists hours vs short-term (minutes) | [Kano et al., Current Biology](https://www.cell.com/current-biology/fulltext/S0960-9822(08)00743-4) | glutamatergic/NMDA receptor signalling |
| 63 | Thermotaxis associative learning | learned association of feeding state with cultivation temperature | thermotaxis-plasticity literature (Mori 1997 review and successors) | AFD; AIY; insulin/DAF pathway |
| 64 | Chemosensory adaptation (ASH to repellents) | reduced Ca2+ response after repeated exposure | [EMBO J ASH imaging paper](https://link.springer.com/article/10.1038/sj.emboj.7600493) | ASH receptor/channel adaptation |
| 65 | Pathogen (aversive) learning | single-exposure shift in bacterial lawn preference | pathogen-avoidance learning literature | AWZ/ASI-type sensory circuit; serotonin |
| 66 | Lifespan / survival curve | median lifespan ~2–3 weeks at 20 °C | standard C. elegans lifespan literature | whole-organism aging, metabolism |
| 67 | Locomotor decline with age | measurable slowing of crawling speed across adult lifespan | lifespan/locomotion-aging literature (Tierpsy-based) | neuromuscular aging; muscle physiology |
| 68 | Pharyngeal pumping decline with age | reduced pumping rate in aged animals | feeding/aging literature | pharyngeal neuromuscular aging |
| 69 | Dauer exit kinetics (recovery on food) | time course of dauer-to-L4 recovery | classic dauer-recovery literature | insulin/DAF-16; whole-organism developmental switch |
| 70 | Photophobic (UV/blue-light) avoidance | avoidance response mediated by LITE-1 | LITE-1 photoreception literature | ASH/ASJ-type circuit; LITE-1 photoreceptor |
| 71 | Electrotaxis | directed movement along an applied electric field | electrotaxis assay literature | mechanosensory/unknown field-sensing circuit; whole-body conductivity |
| 72 | Mechanosensory proprioceptive gait feedback | curvature-dependent modulation of local bend | proprioceptive-feedback locomotion literature, [arXiv 1705.02301](https://arxiv.org/pdf/1705.02301) | stretch receptors in motor neurons/muscle; CPG coupling |
| 73 | Neuron-ablation locomotor deficits (AVA/AVB/PVC/AVD) | specific loss-of-forward/backward phenotypes | classic ablation literature, used as validation in Kunert et al. models | premotor interneuron circuit |
| 74 | Functional signal-propagation sign/strength (23,433 pairs) | measured excitatory/inhibitory sign, strength, kinetics, direction | [Randi et al. 2023, Nature](https://www.nature.com/articles/s41586-023-06683-4) | whole head circuit; extrasynaptic signalling |
| 75 | Brain-wide state representations across timescales | multiplexed encoding of behaviour/state in whole-brain activity | [Atanas et al. 2023, Cell](https://doi.org/10.1016/j.cell.2023.07.035) | whole-brain network; internal-state neuromodulation |
| 76 | Connectome change across development (8 animals) | synaptic weight changes while overall geometry is fixed | [Witvliet et al. 2021, Nature](https://www.nature.com/articles/s41586-021-03778-8) | developmental wiring program |
| 77 | Individual-to-individual connectome variability | substantial inter-animal wiring differences at fixed stage | Witvliet et al. 2021 | developmental noise / stochastic wiring |
| 78 | Nerve-ring contactome organisation | precisely wired core circuit embedded in variable background | [Brittin et al. 2021, Nature](https://doi.org/10.1038/s41586-021-03284-x) | neuropil-scale physical organisation |
| 79 | Body-wall muscle whole-cell dynamics | preferred oscillation frequency matching locomotor band | [Du, Crodelle et al. 2024](https://journals.plos.org/ploscompbiol/article?id=10.1371%2Fjournal.pcbi.1012318) | muscle channel biophysics |
| 80 | AWCon/RMD single-neuron current traces | voltage/current-clamp traces reproduced by HH model | [Nicoletti et al. 2019](https://journals.plos.org/plosone/article?id=10.1371%2Fjournal.pone.0218738) | single-neuron channel biophysics |
| 81 | Bulk body mechanical response under hydrostatic pressure | bulk modulus independent of cuticle | [Biophysical Journal 2015](https://www.cell.com/article/S0006-3495(15)00281-7/fulltext) | hydrostatic skeleton; pseudocoelom pressure |
| 82 | Body Young's modulus (cuticle/muscle/pseudocoelom) | cuticle 75–140 kPa; muscle 600–2,100 kPa; pseudocoelom 42–275 kPa | [Frontiers Bioeng. 2024](https://www.frontiersin.org/journals/bioengineering-and-biotechnology/articles/10.3389/fbioe.2024.1335788/xml/nlm) | whole-body soft tissue mechanics |
| 83 | Metabolic flux landscape (whole organism) | semi-quantitative flux map validated by isotope tracing | [Nature 2025](https://www.nature.com/articles/s41586-025-08635-6) | genome-scale metabolic network |
| 84 | Tissue-resolved metabolic predictions | muscle/intestine/hypodermis-specific flux differences | [MERGE, Mol Syst Biol 2020](https://link.springer.com/article/10.15252/msb.20209649) | tissue-specific gene expression + metabolic network |
| 85 | Gene-essentiality prediction from metabolic model | iCEL1273 predicts lethal/viable gene knockouts | [Yilmaz & Walhout 2016](https://doi.org/10.1016/j.cels.2016.04.012) | genome-scale metabolic network |
| 86 | Phenotypic feature battery across strains | 700+ quantified behavioural features per worm, 300+ strains | [Yemini et al. 2013](https://doi.org/10.1038/nmeth.2560) | whole-animal behaviour, many circuits |
| 87 | Strain classification from postural features | classification accuracy as a function of feature-set size | Tierpsy Tracker benchmark | postural/behavioural phenotyping pipeline |
| 88 | Chemotaxis-like approach to attractant in closed-loop simulation | zigzag approach trajectory reproduced in silico | BAAIWorm/MetaWorm 2024 | simulated sensorimotor loop (not yet behaviourally quantified against the real animal) |
| 89 | Sensorimotor pathway identification via module perturbation | identifies which modules are necessary for specific behaviours | modWorm 2025 | full modular neuromechanical pipeline |
| 90 | Innexin expression breadth (UNC-7/UNC-9 dominance) | broadest-expressed gap-junction genes identified | [Altun et al. 2009](https://pmc.ncbi.nlm.nih.gov/articles/PMC2732576/) | gap-junction gene expression map |

## 4. Gaps

**Per-neuron channel densities/kinetics.** Directly measured for a small minority of neuron
classes (Section 2). Inference path: CeNGEN presence/level of channel-gene transcripts per class
→ map to conductance/kinetics via homology to channels characterised in heterologous expression
systems or in the directly-recorded *C. elegans* neurons (AWCon, RMD, body-wall muscle) → bound
peak conductance by any available whole-cell input resistance / resting potential for that class
or a close relative → treat as a bounded, shared, fitted parameter in the fly-emulation project's
existing sense, not a declared constant.

**Synaptic sign and strength per connection.** EM gives contact count/area, not sign or strength;
only Randi 2023's 23,433 optogenetically probed pairs give direct functional sign/strength/
kinetics, and that is specific to the head, to adult hermaphrodites, and to the stimulation
condition used. Inference for the remainder: neurotransmitter identity (from CeNGEN: ACh/Glu/GABA/
monoamine) plus postsynaptic receptor type (ionotropic vs GPCR, also from CeNGEN) predicts likely
sign; strength can be bounded by measured unitary postsynaptic potentials where available (e.g.
neuromuscular-junction recordings) and calibrated against the Randi atlas for any overlapping
pairs, then validated on held-out functional pairs not used in fitting.

**Neuropeptide release kinetics and diffusion.** Beets 2023 / Ripoll-Sánchez 2023 give binary
peptide–GPCR interactions, not release rate, diffusion constant in the pseudocoelom, or receptor
affinity/desensitisation kinetics for most of the ~100 peptides × 150+ GPCRs. Inference: use the
subset with biochemically measured Kd/kinetics as anchors; propagate to homologous peptide-GPCR
families by sequence/structural similarity; estimate diffusion from pseudocoelom geometry (from
EM volumes) and generic peptide diffusion coefficients measured in other systems.

**Innexin-specific gap-junction conductance/rectification.** Expression maps exist (Altun 2009);
biophysical properties (unitary conductance, voltage dependence, rectification) are characterised
in heterologous systems for only a few pairs (notably UNC-7/UNC-9). Inference: phylogenetic
grouping of the 25 innexins plus any available heterologous electrophysiology, applied class-by-
class, bounded to the measured range for the closest characterised relative.

**Non-body-wall muscle biophysics.** Pharyngeal muscle has a well-characterised electrical
signature (E/P spikes) but not a full channel-level model; vulval, anal-sphincter, and male sex
muscles are essentially unmodelled biophysically. Inference: adapt the validated body-wall-muscle
channel repertoire, adjusted by whatever tissue-level expression data exists for these muscle
types (not CeNGEN, which is neuron-only; other RNA-seq atlases partially cover non-neuronal
tissue), and constrain whole-cell behaviour to the qualitative E/P electrical signature where
available.

**Glia and other non-neural support cells.** 56 glial cells in the hermaphrodite with
increasingly appreciated modulatory roles (e.g. amphid sheath glia shaping ASH/ASER responses),
but no comprehensive channel/transporter-level model. Inference: use available glial marker/
transporter expression data where it exists; where it does not, borrow mechanism (not parameter
values) from characterised invertebrate glial transporters (the same move the fly-emulation
project already makes for its own glia at class level), bounded and labelled inferred.

**Wiring-rule / developmental determinants.** The Witvliet 2021 series shows *what* changes
synapse-by-synapse across development, not the molecular cell-adhesion code that *determines*
which pair of neurons forms a synapse. Not required for a single-snapshot adult emulation; would
be required for a development model (explicitly listed as priority (2) after the base worm in the
given brief).

**Per-neuron-type metabolic budgets.** The genome-scale and MERGE models resolve to tissue level,
not per-neuron-class. Inference: EM-derived mitochondrial density per neurite type (visible in the
same EM volumes used for the connectomes) combined with a generic per-mitochondrion ATP output
figure, bounded and labelled derived/inferred rather than measured.

**Body mechanics measurement disagreement, not just absence.** Young's modulus estimates differ by
2+ orders of magnitude across measurement technique (AFM vs bulk compression vs piezoresistive
cantilever) — this is a genuine unresolved conflict in the literature, not a simple blank. The
practical response is a bounded range per technique, reconciled (if possible) by whether a given
technique probes local cuticle stiffness or whole-body hydrostatic response, rather than a single
point value.

**Agar/fluid mechanical interaction at the worm's scale.** Low-Reynolds-number swimming drag is
reasonably well characterised; crawling on agar (a porous viscoelastic gel) is mostly captured
empirically (viscosity-dependent gait, Fang-Yen 2010) rather than derived from first-principles
pore-scale mechanics of the substrate — adequate for matching observed gaits, not for predicting
behaviour on novel substrates outside the measured range.

## 5. Assessment

No existing effort combines full-animal coverage, mechanism-level biophysics (channels, peptides,
gap junctions, glia, muscle, soft body) and validation against more than a handful of behaviours
at once. The closest integrated efforts — BAAIWorm/MetaWorm (2024) and modWorm (2025) — each
achieve genuine closed-loop brain-body-environment simulation, but validate against locomotion/
orientation only, and both still treat most neurons with simplified (non-channel-specific or
partially homology-derived) dynamics. The single most important recent result for anyone planning
a mechanism-complete model is Randi et al. 2023: the anatomical connectome, on its own, does not
predict function — extrasynaptic and neuromodulatory signalling materially changes the picture in
measured pairs — so any model built from Cook/Varshney connectivity alone, however many neurons it
spikes correctly, is missing a load-bearing layer. The richest functional and expression datasets
(Randi 2023, Atanas 2023, CeNGEN refinements, the 2025 metabolic-flux paper) are all from the last
three years, so the field has had very little time to integrate them into any single model; no
integration attempt yet uses more than two or three of the structural/functional/expression/
metabolic layers simultaneously, and none claims validation across the breadth implied by "every
observed scenario in the literature."

**The 5 hardest problems:**

1. **Extrasynaptic signalling is structurally necessary and mostly unparameterised.** Randi 2023
   shows the synaptic connectome alone is insufficient; the neuropeptide connectome (Beets/
   Ripoll-Sánchez 2023) gives binary interactions for ~100 peptides × 150+ GPCRs, not the release,
   diffusion and receptor kinetics a dynamical model needs.
2. **No single dataset is structure + function + expression + sex + development, same animals.**
   Cook 2019 (structure, both sexes) ≠ Witvliet 2021 (structure, development) ≠ Randi 2023
   (function, adult hermaphrodite head, one condition) ≠ CeNGEN (expression, population average)
   ≠ Atanas 2023 (function, different animals again). Witvliet 2021 also shows real individual
   worms differ from each other structurally — "the" connectome may not even be the right target.
3. **Per-neuron biophysical parameters are an underdetermined inverse problem.** Direct recordings
   exist for a handful of the 118 classes; most parameters must come from expression + homology +
   population-level fitting, and many *C. elegans* neurons are graded/non-spiking, so there is no
   simple "spike rate matches" fitting target the way there is for a conventional spiking model.
4. **Multi-tissue soft-body mechanics has unresolved empirical disagreement**, not just gaps:
   Young's modulus estimates span 2+ orders of magnitude by measurement technique, and simulating
   a hydrostatic-pressure-dominated, cuticle-anisotropic body in agar/fluid at micron scale remains
   numerically hard (Sibernetic's SPH approach is the most complete attempt and is still coarse).
5. **Validation breadth has never been attempted.** Every effort above validates against a
   handful of behaviours (mostly locomotion and simple chemotaxis); the behaviour corpus in
   Section 3 lists ~90 independently measured, quantified phenomena spanning a dozen circuits and
   life-history stages, each with its own assay conditions (temperature, food state, strain
   background). No project has checked a single model against more than a small fraction of this
   list at once, so "functionally equivalent in every observed scenario" is a bar nothing has
   been tested against even partially.
