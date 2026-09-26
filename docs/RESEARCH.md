# Research map and audit notes

Compiled 14 September 2026. Primary publications, official dataset releases and source repositories are preferred. Availability and versions can change. “Reviewed” below means paper/release/documentation inspected during preparation, not all raw files downloaded or all claims independently reproduced. Source labels are descriptive where exact bibliographic details have not been rechecked.

## Anatomy and identity infrastructure

| Resource | What it contributes | Use and limitation |
|---|---|---|
| [MaleCNS official downloads](https://male-cns.janelia.org/download/) | Continuous male CNS, annotation, connectivity, synapse positions, transmitter predictions and skeletons | Candidate primary specimen. Retention policy determines counts; graph rows are not interchangeable with anatomical contacts. Published files include graph 1.1 GB, positions 12.7 GB and partners 6.8 GB. |
| [BANC project](https://github.com/htem/BANC-project), [Distributed control circuits across a brain-and-cord connectome](https://www.nature.com/articles/s41586-026-10735-w) | Female brain-and-cord reconstruction, versioned resources and cross-dataset metadata | Candidate primary specimen; recorded donor turning bias is a possible later validation target, not proof its individuality is encoded in the graph. Derived influence matrices are not measured physiological weights. |
| [FlyWire annotations](https://github.com/flyconnectome/flywire_annotations) | Established brain graph identities and annotations | Useful for reproducing brain-only models and cross-dataset matching. Does not itself supply the VNC. |
| [MANC circuit organization](https://elifesciences.org/articles/96084) | Descending-to-motor architecture and motor identities | Correct title: Organization of circuits linking descending input to motor output in the Drosophila Male Adult Nerve Cord connectome. Inspect relevant muscle assignments and their confidence. |
| [FANC motor-control reconstruction](https://pmc.ncbi.nlm.nih.gov/articles/PMC11348827/) | Female nerve-cord motor circuitry and anatomical mappings | Useful comparison and peripheral identification evidence; verify full methods and target assignments before import. |
| [Virtual Fly Brain](https://www.virtualflybrain.org/), [coconatfly](https://github.com/natverse/coconatfly) | Ontologies, anatomical identities and comparative analysis | Integration tools; inferred matches retain confidence, sex and specimen provenance. |
| [Curated transmitter evidence](https://github.com/flyconnectome/drosophila_neurotransmitters) | Experimental transmitter assignments across datasets | Distinguish experimental evidence from EM prediction. Transmitter alone does not uniquely specify postsynaptic sign or kinetics. |
| [Fly Cell Atlas](https://pmc.ncbi.nlm.nih.gov/articles/PMC8944923/) | Adult expression evidence across tissues and cell populations | Inform channel/receptor/peptide priors; neither exact conductances nor one-to-one transcriptomes of scanned neurons. |

Choose one primary graph. Other animals supply comparison evidence and priors; combining them into a species-level reconstruction is allowed if declared. Neither repeated cross-animal similarity nor disagreement automatically proves tracing correctness/error.

## Executable neural precedents

**Shiu et al.** [Paper](https://www.nature.com/articles/s41586-024-07763-9); [Brian2 code](https://github.com/philshiu/Drosophila_brain_model). A whole-brain LIF model uses connectivity and transmitter assumptions to predict sensory–motor responses. The global synaptic scale includes calibration to a specified sensory-to-motor response. Reproduce selected published outputs as a baseline. This is neither parameter-free physiology nor demonstrated autonomous whole-animal competence.

**Pugliese et al.** [Connectome simulations identify a central pattern generator circuit for fly walking](https://pmc.ncbi.nlm.nih.gov/articles/PMC13142387/); [JAX code](https://github.com/smpuglie/Pugliese_cpg_2025). Strong precedent for anatomically constrained locomotor dynamics and perturbation predictions. Reproduce the versioned stimulus protocol and motor activity before attempting embodiment. Rhythmic output under stimulation is not standing or walking. Descending-neuron names differ across drafts/annotations; resolve identity from the actual version rather than hard-coding names from this conversation.

**Flyvis / Lappalainen et al.** [Paper](https://www.nature.com/articles/s41586-024-07939-3); [source](https://github.com/TuragaLab/flyvis). Connectome-constrained, task-optimized visual models predict physiological responses. Valuable visual architecture, data and fitting precedent. Trained parameters remain fitted, not directly measured. Audit transfer of visual responses into a different whole-brain model.

**Jaxley / Deistler et al.** [Nature Methods](https://doi.org/10.1038/s41592-025-02895-w); [source](https://github.com/jaxleyverse/jaxley/). Differentiable biophysical simulation permits fitting conductances and related quantities against observations or tasks. Demonstrations include neural memory tasks and large synaptic systems. Benchmark examples use hardware/models different from the user's machine; this does not prove a complete fly can be differentiated efficiently on the project's RTX 4070 Ti SUPER. Long trajectories, nonconvexity and memory remain concerns.

**Inference tools.** [sbi documentation](https://sbi.readthedocs.io/en/latest/) for simulation-based posterior inference; [multimodal neuron fitting study](https://www.frontiersin.org/journals/neuroinformatics/articles/10.3389/fninf.2021.663797/full) for population/evolutionary fitting context. Apply to tractable parameter groups; do not infer whole-brain identifiability from a small successful fit.

## Leg, sensory and body evidence

| Resource | Relevant measurements/assets | First action |
|---|---|---|
| [Azevedo motor-unit data](https://datadryad.org/dataset/doi:10.5061/dryad.76hdr7stb) | Voltage/EMG, force-probe observations, limb motion and optogenetic perturbations for identified tibia-flexor motor units | Download README and one suitable recording. Full release is about 48.76 GB; no need to fetch it all first. |
| [Leg proprioception study](https://pmc.ncbi.nlm.nih.gov/articles/PMC6481666/) | Femoral chordotonal sensory classes and response properties | Extract condition-specific position, motion and vibration coding; do not generalize one sensor to all leg feedback. |
| [Central proprioceptive processing](https://elifesciences.org/articles/60299), [Dryad data](https://datadryad.org/dataset/doi:10.5061/dryad.k3j9kd55t) | Neural recordings and stimulus/kinematic evidence | Audit variable units and time alignment; construct causal afferent response tests. |
| [DoOR](https://neuro.uni-konstanz.de/DoOR/content/DoOR.php) | Aggregated odor–receptor responses | Useful receptor priors; normalized responses are not a universal absolute concentration-to-spike law. |
| [NeuroMechFly v2](https://www.nature.com/articles/s41592-024-02497-y), [FlyGym](https://github.com/NeLy-EPFL/flygym) | Body physics, sensory infrastructure and controller interfaces | Inspect current API and model assets. Published behavior can rely on supplied controllers. |
| [Musculoskeletal simulation of limb movement biomechanics](https://arxiv.org/abs/2509.06426), [muscle tutorial](https://neuromechfly.org/tutorials/6_muscle_imitation/) | Anatomical muscle modeling and fitted biomechanics | Tutorial inspected in prior research exposes 15 left-front-leg actuators in a tethered preparation. This is not a complete six-leg MN-to-muscle solution; recheck current version. |
| [flybody paper](https://www.nature.com/articles/s41586-025-09029-4), [code](https://github.com/TuragaLab/flybody), [data](https://doi.org/10.25378/janelia.25309105) | Combined walking/flight body and supporting motion assets | Distinct from FlyGym. Demonstrated control uses learning and a wingbeat generator; aerodynamic calibration and cross-species flight data need provenance auditing. |

A rigid-body observable is not necessarily what a receptor measures. Load/strain sensing, contact feedback, adhesion and muscle recruitment require specific models. Check species, sex and preparation before transferring physiology or mechanics.

## Flight evidence and an important code finding

**Melis, Siwanowicz and Dickinson:** [wing-hinge paper](https://www.nature.com/articles/s41586-024-07293-4), [Caltech data](https://data.caltech.edu/records/aypcy-ck464), [umbrella code](https://github.com/FlyRanch/mscode-melis-siwanowicz-dickinson). Paired steering-muscle calcium and wing kinematics, plus RoboFly aerodynamic measurements, are a promising basis for empirical local body models. The paper's maneuver controller is not a reconstructed neural controller. Caltech lists 2.6 GB muscle/wing HDF5, 1.3 GB RoboFly and 1.6 GB FlyNet archives; README was read but full arrays were not validated.

At wing-hinge-CNN commit `cd5081aac460754b8ff3d6426835920e43542f95`, [dataset construction](https://github.com/FlyRanch/wing-hinge-cnn/blob/cd5081aac460754b8ff3d6426835920e43542f95/wing_hinge_cnn/wing_hinge_cnn.py) pairs `x_i[j:j+N_window]` with `y_i[j]`, using a nine-sample window with muscle channels and wingbeat frequency. It therefore uses later recorded samples relative to the predicted wingbeat. Future fluorescence can legitimately inform retrospective inference of earlier activation; the released predictor is not automatically a causal live actuator model. Refit/check time alignment and observation dynamics. Do not import it blindly into the closed loop.

**Flight pathways:** [Dhawan et al. atlas](https://dickersonlab.princeton.edu/publications/neural-connectivity-atlas-fly-flight-control) provides identified flight-control connectivity; [Lesser et al. wing sensory dataset](https://datadryad.org/dataset/doi:10.5061/dryad.mgqnk99b5) provides peripheral/central registration evidence. Neither supplies a complete local strain-to-spike atlas.

**Flight causal validation:** [Whitehead et al.](https://authors.library.caltech.edu/records/rvsgq-z1314), [data DOI](https://doi.org/10.7298/6jdx-1j29), link steering motor pathways to pitch correction through perturbations. Reserve some interventions as tests. Do not install a hand-built feedback law in place of the corresponding circuitry.

**Additional mechanisms:** [myogenic wingbeat study](https://arxiv.org/abs/1301.5148); [octopamine and flight-dependent vision](https://pubmed.ncbi.nlm.nih.gov/23142045/); [mixed electrical/chemical escape transmission](https://pmc.ncbi.nlm.nih.gov/articles/PMC1974813/); [histaminergic visual transmission](https://www.frontiersin.org/journals/neural-circuits/articles/10.3389/fncir.2016.00019/full). These motivate specific mechanism audits; they do not supply all parameters for the whole fly.

## Behavioral fitting and individuality resources

| Dataset/source | Scientific use | Access/interpretation limit |
|---|---|---|
| [BABAM / Fly Bowl](https://kristinbranson.github.io/BABAM/) | Neural activation screen, behavior and expression mapping | Genetic lines can label multiple cells; do not equate a line with one connectome neuron. Guide and download references reviewed. |
| [DN activity collection](https://dataverse.harvard.edu/dataverse/DNs) | Neural activity paired with odor-evoked/spontaneous behavior | Author-linked collection; automated access encountered a verification page. File-level schema still needs checking. |
| [Gattuso locomotor statistics](https://zenodo.org/records/15047774) | Processed/raw walking behavior and anatomical data | Release page reviewed. Inspect intervention protocol and recording units before fitting. |
| [Behavioral decathlon](https://lab.debivort.org/structure-of-behavioral-variability/) | Multiple traits measured in the same individuals | Useful covariance and persistence tests; population distributions do not specify the scanned animal. |
| [Learning is a fundamental source of individuality](https://elifesciences.org/reviewed-preprints/111235), [linked repository](https://github.com/jaksiclab/GeneticsOfLearningIndividuality) | Learning-associated behavioral divergence in individual flies | Reviewed preprint; source-linked data/code not fully inspected. Reverify files and experimental conditions. |
| BANC donor phenotype | A possible donor-specific turning-bias test | Previously disclosed in this conversation, so not pristine blind evidence for the present researcher. Use prospective independent evaluation/controls and disclose prior knowledge. |

No dataset supplies the complete natural repertoire under all states. Add feeding, grooming, thermosensation, reproductive behavior and longer-timescale state evidence as those mechanisms enter scope. Do not use larval learning data as adult ground truth without a justified transfer model.

## Closest projects and what they establish

**BAAIWorm:** [Nature Computational Science](https://doi.org/10.1038/s43588-024-00738-w). An important precedent omitted in early discussion: a morphologically and biophysically detailed 136-neuron sensory/locomotor network, fitted using physiological and network observations, is embodied with sensory feedback and attractant-directed movement. Shared cell templates and inferred connection properties remain assumptions. It demonstrates a limited biological reconstruction, not a complete worm mind.

**modWorm:** [preprint](https://arxiv.org/abs/2504.18073). Integrates connectome-based neural dynamics, muscle calcium, force, mechanics and proprioception; reports locomotor and perturbation responses. Study its modular interfaces and validation rather than assuming its repertoire is complete.

**OpenWorm:** [c302](https://royalsocietypublishing.org/rstb/article/373/1758/20170379/42135/c302-a-multiscale-framework-for-modelling-the), [science resources](https://openworm.org/science.html). Foundational infrastructure, not proof that a full autonomous digital worm has been achieved.

**Eon:** [technical account](https://eon.systems/updates/embodied-brain-emulation). A connectome brain is coupled to a body through sparse descending-neuron mappings and existing learned locomotor controllers. This is useful engineering precedent; it does not establish full biological VNC-to-muscle control.

**FlyGM:** [preprint and methods](https://arxiv.org/html/2602.17997). Connectome-structured learned locomotor control. Shows useful architecture, not individually measured biological dynamics throughout the nervous system and interfaces.

**Digital Sphinx:** [reviewed preprint](https://elifesciences.org/reviewed-preprints/111516), [full-text source](https://pmc.ncbi.nlm.nih.gov/articles/PMC13041780/). A worm graph can participate in fly-body control when a decoder is trained. Behavioral appearance does not establish circuit identity.

**DOOMFLY:** [current README](https://github.com/nftechie/doomfly), [technical audit](https://github.com/nftechie/doomfly/blob/main/docs/doom-neuroscience-review.md). Retains substantial MaleCNS wiring but uses approximate dynamics and engineered visual, button and reinforcement interfaces. Its documented candidate failed learning validation. Useful implementation reference, not demonstrated fly cognition or successful learned survival. Audit status is version-specific.

## Corrections to older notes

- The BANC paper is **Distributed control circuits across a brain-and-cord connectome**, not the incorrect title used in the earliest pack.
- eLife 96084 is the MANC circuit-organization paper listed above; earlier author/title attribution was wrong.
- Nature DOI `s41586-024-07968-y` is **Network statistics of the whole-brain connectome of Drosophila**, not the neurotransmitter-classifier paper. Do not repeat that citation mismatch.
- The 2025 whole-body walking/flight simulator is **flybody**, separate from NeuroMechFly/FlyGym.
- Dataset completeness, physiological coverage, computational feasibility and behavioral fidelity are different quantities.
- There is no known measured probability that this project will succeed, no established Tier 3 file size, and no validated percentage of “missing brain bits.”

Use these notes to find evidence, then verify the exact statements needed for a model decision. Do not promote a project self-report, title, abstract or release page into evidence of a result that has not been checked.
