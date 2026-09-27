# The construction programme

**Status: the project's direction from 27 September 2026** (Ben, after session 8). This document supersedes earlier plans. `CLAUDE.md` still states the goals and scientific requirements, and `docs/WORKFLOW.md` the procedure. Findings carried over from sessions 1–8 are in `docs/LESSONS.md`; the fidelity research is in `docs/research/`.

## Mission

Build a **complete fly**: every mechanism that plausibly matters for behaviour, from receptors through the CNS to motor units, muscles and body mechanics, and back through the sense organs. Represent every quantity the connectome does not fix as an explicit unknown, bounded by what biology allows. Then **construct the brain by search**: find the flies within those bounds that reproduce measured physiology, and test whether fly behaviour emerges, judged on held-out data.

Nobody has run this experiment. We do not know which mechanisms make behaviour emerge, so **we simulate more rather than less**. Which mechanisms matter is itself a result, measured by ablation in fitted flies.

## Principles

1. **Complete before search.** The search fills parameters; it never compensates for missing physics. A missing mechanism makes an optimiser distort other parameters to imitate it: neural weights fitted to a torque-driven body learn to fake muscle stiffness. When a fitted fly fails, the reason must be "wrong parameters", which search can fix, never "absent mechanism", which it cannot.
2. **Mechanisms always on; parameters released gradually.** Every mechanism in the inventory is simulated in every run, at its prior. The search frees parameters in stages: class level first, then type level. Parameters with no data constraint stay at their priors until data or ablation shows they matter. Expensive mechanisms not yet affordable (Hodgkin–Huxley channels, multi-compartment dendrites, CFD, cuticle FEM) get an architectural **slot**, not an omission.
3. **Biology bounds the search.** Every parameter has hard bounds `[bio_min, bio_max]` from the literature, and the search can never leave them. A search that presses against a bound is a finding: evidence of a missing mechanism or a wrong assumption, reported as such, never relaxed silently. Inside the bounds sits a prior (distribution, centre, spread) with its own evidence label. This is what separates construction from curve-fitting.

   The counter-example is FlyGM (arXiv 2602.17997, 2026). It drives flybody from the FlyWire connectome with ~32 learned, physiologically unconstrained latents per neuron. It walks and flies, but it is not a fly brain.
4. **Every unknown belongs to exactly one mechanism, at one grain.** The grains are global, region, class, type, cell, joint and muscle. No parameter is shared implicitly between mechanisms. No mechanism has hidden constants.
5. **The body is validated as a body first, with the brain dead.** A fly with a silent brain must fall and lie like a real fly with silenced motor neurons. Each muscle, joint, wing and sense organ has its own physical test against data. Only then may the brain be judged through the body.
6. **Verification first.** Every mechanism has a test of what it claims, including a **neutral-equivalence test**: at neutral settings it reproduces the model without it. Every probe has a test of its own correctness before its results are read.
7. **Ensembles, held-out judgement.** The output of construction is a set of flies within bounds that fit the fit set. Their disagreement is our uncertainty. Held-out datasets and interventions judge them. Labels never upgrade (WORKFLOW §3).

## What "complete fly" means: the template

The template is the fly with every mechanism built and every unknown **scrambled**, i.e. drawn from its prior within bounds. `sample_fly(seed)` returns one such fly. After construction starts, only numbers change; the mechanism structure is final unless a validation failure points to a new mechanism.

Required fidelity per mechanism follows `docs/research/FIDELITY.md`. Where that note says "not required", we still include the mechanism if it is cheap, per principle 2. Status as of end of session 8: **have** / **partial** / **absent**.

### Body and periphery

| ID | Mechanism (required level) | Implementation route and data | Status |
|---|---|---|---|
| B1 | Rigid skeleton, measured mass/inertia (mm, g, s; torque µN·mm) | flybody | have |
| B2 | Leg DOFs; compliant passive tarsal chain | flybody; check tarsal compliance | partial |
| B3 | Passive mechanics at every joint: stiffness, damping, **rest angle** | legs: *Passive muscle forces in Drosophila are large but insufficient to support a fly's weight* (eLife 2025, [PMC12324252](https://pmc.ncbi.nlm.nih.gov/articles/PMC12324252/)): linear springs per joint per leg, ~2-fold range across flies, rest posture after MN silencing. Other joints: bounded guesses | partial (s9: measured leg stiffness as switch `joint:leg\|passive_stiffness_source`; rest angles and damping still guessed) |
| B4 | Leg muscles: antagonist Hill-type muscle–tendon units (activation dynamics, F–L–V, rigid tendon acceptable) | FlyMimic ([arXiv 2509.06426](https://arxiv.org/abs/2509.06426), CC-BY): 15 fitted MTUs per front leg; 7/8 anatomical MTUs mid/hind (unfitted); in FlyGym (`flygym.compose.fly.musculoskeletal`). MuJoCo muscle actuators | partial (s9: antagonist Hill pairs per leg DOF, switch `muscle:leg\|model`; front leg from FlyMimic, mid/hind guessed) |
| B5 | Motor units → muscles: MN→muscle identity, per-unit force, twitch rise/decay by unit class, summation/saturation, NMJ facilitation | MN→muscle map (F-DATA-1; Azevedo 2024 FANC atlas); forces Azevedo 2020; slow twitches do not peak within 500 ms | partial (s9: class twitch rise/decay, saturation, NMJ facilitation in Hill mode; 20 of 84 muscles lack MNs) |
| B6 | Contact and friction | MuJoCo soft contact | have (untuned) |
| B7 | Adhesion (claws, pulvilli): on in stance, released by load/shear | flybody adhesion actuators + detachment rule | partial (neural switch) |
| B8 | Neck: 3 DOF with neck muscles/MNs | flybody joints; MN map | partial (guessed drive) |
| B9 | Abdomen: 1–2 steering DOFs plus passive | flybody | partial (pins at limit) |
| B10 | Flight motor: ~200 Hz wingbeat oscillator standing in for stretch-activated power muscles and thoracic resonance; amplitude set by power-muscle drive | flybody wing-pattern generator (WPG; Vaxenburg 2025 Nature) | absent |
| B11 | Wing hinge: steering-muscle activity → per-stroke wing kinematics (b1–b3, i1–i2, iii1–iii4, hg1–4, tp) | Melis, Siwanowicz & Dickinson 2024 Nature; code [FlyRanch/mscode-melis-siwanowicz-dickinson](https://github.com/FlyRanch/mscode-melis-siwanowicz-dickinson) (`wing-hinge-cnn`) | absent |
| B12 | Aerodynamics: quasi-steady | flybody fluid model | have |
| B13 | Halteres: antiphase beating; Coriolis-driven strain → campaniform (dF2) signal, phase-locked; electrical synapse to b1 MN | analytic proxy; ~110 sensilla to b1 in published models | absent |
| B14 | Wings folded at rest (passive) | passive wing joints | have (s9: spring reference folded, switch `joint:wing\|spring_reference`) |
| B15 | Jump: TTM fast high-force extensor; GF-timed | jump myofibril tension 19.8 ± 10.5 mN/mm²; takeoff kinematics (JEB 2004) | absent (torque cap ±30 µN·mm) |
| B16 | Proboscis: rostrum/haustellum/labella + labellar spread; MN map | flybody joints; MN9/MN2/MN6/MN8 identities | partial |
| B17 | Ingestion: cibarial pump, crop/gut fill | lumped hydraulic | absent |
| B18 | Self-collision; bristle-field contact map for grooming | flybody collision; bristle map | partial |
| B19 | Compound-eye optics: per-ommatidium Gaussian acceptance, geometry; render rate ≥ several hundred Hz for flight | flybody eyes; retinotopy (F-VISION-2) | partial |
| B20 | Antenna/arista: passive rotational oscillator (wind, gravity, sound) → JO | new | absent |
| B21 | Proprioceptor periphery: FeCO (claw/hook/club), campaniform strain proxies, hair plates, bristles | proxies exist | partial |
| B22 | World: odour plume with intermittency and wind; visual scene; tastants; temperature | world.py | partial |
| B23 | Numerics: 0.1 ms walking; ≤ 0.05 ms flight (convergence test) | MuJoCo | partial |

### Internal state and organs (lumped)

| ID | Mechanism | Status |
|---|---|---|
| S1 | Hemolymph sugar/trehalose | absent |
| S2 | Fat body energy store (AKH/DILP coupling) | absent |
| S3 | Crop and gut fill (links B17) | absent |
| S4 | Water balance (thirst) | absent |
| S5 | Body temperature (Q10 on neurons; have) | partial |

### Nervous system

| ID | Mechanism (required level) | Status |
|---|---|---|
| N1 | Point neuron per cell; **mode by class** (spiking LIF or graded leaky integrator with threshold-linear release); a slot for richer models | partial (graded for a few types) |
| N2 | Per-class intrinsics: V_rest, τm, threshold gap, reset, refractory, gain | partial (borrowed shared defaults, a few fits) |
| N3 | Per-class background drive: tonic plus noise | absent |
| N4 | Per-class spike-frequency adaptation | have (off) |
| N5 | Per-class synaptic strength (presynaptic release, postsynaptic gain) | partial (one global efficacy) |
| N6 | Receptor-resolved sign per postsynaptic type | partial (consensusNt + 54 transcript rows) |
| N7 | Two kinetic classes per synapse: fast ionotropic, slow metabotropic (GABA-B, mGluR, mAChR) | partial (GABA-B option) |
| N8 | NMDA-type voltage-dependent slow excitation where expressed | absent |
| N9 | Conductance-based (shunting) inhibition: flagged classes, option for all | have (option) |
| N10 | Short-term depression/facilitation per presynaptic class | have (option) |
| N11 | Presynaptic inhibition at afferent terminals | have (option) |
| N12 | Gap junctions at curated sites (GF, JO→GF, eLN–PN, LPTC, haltere/wing afferent→steering MN), rectifying where known | partial (GF) |
| N13 | Conduction delays per type | have |
| N14 | Synaptic/membrane noise | have (option) |
| N15 | Dynamic sensory transducers: adapting photoreceptor; two-stage ORN; FeCO/CS/JO filters with adaptation; GRN with state gain; thermal | partial (mostly static) |
| N16 | Wingbeat-phase sensing (haltere, wing campaniforms) | absent |
| N17 | Steering-MN phase locking (one spike per cycle) | absent |
| N18 | GF escape system: electrical + chemical; timing-dependent mode | partial |
| N19 | Neuromodulator pools (DA, OA, 5-HT, TA): per-type receptor maps, GPCR kinetics | partial (pools; sensitivities not live) |
| N20 | Neuropeptides/hormones: release cells, receptor maps (AKH, DILPs, sNPF, Hugin, DH44, PDF, tachykinin, …) | absent |
| N21 | KC→MBON plasticity: DAN-gated, bidirectional, timing-dependent, per compartment | partial (one-way LTD, off) |
| N22 | Memory decay, forgetting, consolidation | absent |
| N23 | APL local (compartmental) inhibition | absent |
| N24 | CX plasticity: ring neuron→EPG Hebbian mapping | absent |
| N25 | Sleep homeostat (dFB switch, glial Ca integrator) | absent |
| N26 | Circadian oscillator in clock neurons | absent |
| N27 | Glia, lumped | absent |
| N28 | Temperature dependence (Q10) | have |

**Totals:** 56 mechanisms. At the end of session 8, about 10 are in place, about 25 partial, about 21 absent. The authoritative status is now `data/model/mechanisms.yaml` (end of session 9: 11 have, 24 partial, 21 absent; `scripts/blank_ledger.py`).

## The data model

**One authoritative table of unknowns.** New files under `data/model/`:

- **`mechanisms.yaml`:** one entry per mechanism ID above. Fields: tier (A/B/C), status, switch key, neutral setting, test name and evidence notes.
- **`classes.csv`:** every neuron type → its class at each grain:
  - superclass;
  - circuit class (ring types, PN/LN/KC/MBON/DAN, LMC/Mi/Tm/T4/T5, DN, premotor by hemilineage, MN by muscle);
  - transmitter;
  - mode (spiking/graded).

  Every assignment is labelled, and hemilineage must be fetched (our cache column is empty).
- **`parameters.csv`:** one row per unknown. Columns:
  - `param_id`, `mechanism_id`, `grain`, `applies_to` (class/type/joint/muscle selector), `unit`;
  - `bio_min`, `bio_max`, `bound_basis` (measured range for this class / measured in related fly class / insect-wide / physical limit), `bound_source`;
  - `prior` (distribution + parameters), `prior_basis`, `prior_source`;
  - `value_fixed` (if measured and fixed), `release_stage` (0 fixed at prior; 1 class search; 2 type refinement), `label` (measured/derived/inferred/guessed).

**`sample_fly(seed, stage)`** draws every free parameter from its prior within bounds and returns a complete fly specification. The existing registry, `cell_types.csv` rows and profiles become *views* of this table. `profile m4` stays reproducible as a named specification.

**The ledger reports the construction state:**
- mechanisms have / partial / absent, per tier;
- unknowns in total, with bounds from data vs guessed;
- how many are fixed by measurement;
- how many are released at each stage.

### Setting biological bounds

For each parameter, take the widest defensible range from the strongest available evidence, in this order:
1. a measured range for this class in adult *Drosophila*;
2. a measured range in related fly classes, or larval fly;
3. insect-wide measurements;
4. physical or biophysical limits.

Examples of anchors (to be verified and cited in the table):
- **Central resting potentials:** adult −50 to −60 mV and larval −45 to −65 mV (Gouwens & Wilson 2009 J Neurosci; larval central-neuron survey, J Neurophysiol 2002); literature table −48 to −68 mV.
- **Input resistance:** PNs ~600 MΩ; slow MNs 532–1,041 MΩ.
- **τm:** 15–17 ms measured in MNs.
- **Unitary EPSPs:** 1–10 mV in larval central neurons; ORN→PN ~6 mV at a 22-synapse connection.
- **Firing rates:** ≤ ~500 Hz (physical); PN spontaneous 1–5 Hz.
- **Passive joint stiffness:** measured per joint within a ~2-fold IQR, 7-fold across joints.
- **Muscle specific tension:** 9–37 mN/mm² (flight to jump muscle); FlyMimic used 28.

A bound is never widened to rescue a fit without a recorded reason. A search pressing on a bound is reported.

## Acceptance tests for the template

**Dead fly (brain silent).** No neuron fires and no motor unit is active; the body is exactly as built. Spawned in a standing posture, the fly must:
- collapse to the ground: real flies with silenced MNs fall on 92/92 trials, starting within ~40 ms; passive torques are ~70× below what supports the weight;
- let its legs settle toward the measured passive rest posture (prothoracic protracted, metathoracic retracted relative to mesothoracic);
- keep its wings folded and its abdomen and head at rest;
- have no joint within 3% of a range limit for more than 5% of the time;
- show mechanical energy decaying with no jitter.

A variant sets muscle activation decaying with τ ≈ 100 ms from a standing drive, to compare fall kinematics with the measured fall. Passive torques per joint must match the measured spring constants **after unit reconciliation**. The paper's stiffness table is given in mN/° while its text says N·m/°. Resolve this from the methods and the "70× too weak" statement before using the numbers; our body is in µN·mm.

**Body physical battery:**
- isometric force per motor-unit class vs Azevedo 2020;
- twitch time course by unit class;
- muscle moment-arm signs (flexor vs extensor);
- leg resistance to imposed movement;
- jump impulse vs measured takeoff;
- wingbeat frequency 200–230 Hz;
- lift ≈ weight at a nominal hover stroke;
- haltere signal linear in body rotation rate;
- eye acceptance angle and sampling;
- proboscis range of motion;
- pump volume per cycle.

**Brain template:**
- neutral-equivalence test per mechanism;
- `sample_fly(seed)` for 10 seeds runs 3 s of closed loop without runaway (> 20k spikes/step), NaNs or joint explosions;
- every free parameter lies within its bounds;
- no parameter without a row.

**Ledger:** 0 absent mechanisms in tiers A and B; tier C absent only where it is recorded with a reason.

## Task list

The tasks are not divided into sessions. Work them in order, as far as possible; later ones depend on earlier ones. Mark each done only when its tests pass.

1. [done s9] **Data model skeleton:** `data/model/{mechanisms.yaml, classes.csv, parameters.csv}`, loaders, validation tests (every param has bounds, prior, label and mechanism; no orphan mechanisms), and ledger integration.
2. [done s9] **Class taxonomy:** fetch hemilineage and any missing annotations (neuPrint token in `~/.config/flyemu/`); build `classes.csv` with labelled mode assignments; the evidence table for spiking vs graded.
3. [done s9] **Dead-fly test harness,** before any body change: brain silenced, spawn standing, metrics above. Record the current body's failures as the baseline.
4. [partial s9: leg rest angles remain] **B3 passive joints:** reconcile units; enter measured leg stiffness and rest angles with bounds; other joints get bounded guesses. The wings, abdomen and head become passive at rest (B14, B9, B8 at rest).
5. [partial s9: see HANDOFF] **B4/B5 muscles:** import FlyMimic MTUs (front leg), anatomical mid/hind MTUs with scaled parameters (labelled), and antagonist pairs for every leg DOF not covered. Remap motor units to muscles (not signed torques). Twitch kinetics by unit class; saturation; NMJ facilitation. Keep the torque path as a comparison option.
6. **B7 adhesion** with load/shear detachment.
7. **Dead fly passes;** the body physical battery (legs) passes or failures are recorded.
8. **Flight apparatus:**
   - B10 WPG oscillator driven by power-muscle MNs (DLM/DVM);
   - B11 hinge map from steering MN activity (Melis code or a fitted phenomenological map, labelled);
   - B13 halteres with the Coriolis signal;
   - N16/N17 phase-locked sensing and steering-MN locking;
   - ≤ 0.05 ms flight step with a convergence test;
   - wingbeat and lift tests.
9. **B15 jump muscle** with a raised force cap; GF→TTMn timing test.
10. **B16/B17/S3 proboscis, pump, crop;** B18 bristle map; B20 antenna oscillator; B21/N15 transducer dynamics.
11. **Neural mechanisms N1–N3, N5–N8, N12, N14:** per-class modes, intrinsics, background drive, strengths, receptor classes and NMDA, gap-junction site list. Each gets parameter rows with bounds and priors, is neutral-equivalence tested, and is **switched on at its prior**.
12. **State and learning N19–N27, S1–S4:** neuromodulator receptor maps (transcripts where available, else priors); peptide release/receptor tables (extend `scripts/infer_receptors.py` to peptide receptors and channel genes); plasticity rules; decay; APL; CX plasticity; sleep homeostat; circadian oscillator; glia; metabolic organs.
13. **`sample_fly(seed, stage)` and the template acceptance tests,** 10 seeds.
14. **Ledger report:** the construction state per tier.

**Afterwards (search), in order:**
- a batched GPU simulator (JAX + CUDA on backhouse; class-decomposed weights, delay buckets), equivalence-tested against `lif.py`;
- target library v1, split by dataset;
- a pre-registered class-level CMA-ES search within bounds;
- CPU and body re-scoring of the best;
- gradient refinement per type;
- ensembles and held-out judgement;
- ablation of each mechanism in fitted flies.

## Sources used for this plan (verify before relying on specific numbers)

- Passive muscle forces in *Drosophila* are large but insufficient to support a fly's weight, eLife 2025: [PMC12324252](https://pmc.ncbi.nlm.nih.gov/articles/PMC12324252/)
- Musculoskeletal simulation of limb movement biomechanics in *Drosophila melanogaster* (FlyMimic), [arXiv 2509.06426](https://arxiv.org/abs/2509.06426); FlyGym [musculoskeletal API](https://neuromechfly.org/api_reference/flygym/compose/fly/musculoskeletal/)
- Melis, Siwanowicz & Dickinson 2024, *Machine learning reveals the control mechanics of an insect wing hinge*, [Nature](https://www.nature.com/articles/s41586-024-07293-4); [code](https://github.com/FlyRanch/mscode-melis-siwanowicz-dickinson)
- Vaxenburg et al. 2025, *Whole-body physics simulation of fruit fly locomotion*, [Nature](https://www.nature.com/articles/s41586-025-09029-4); [flybody](https://github.com/TuragaLab/flybody)
- Azevedo et al. 2024, *Connectomic reconstruction of a female Drosophila ventral nerve cord*, [Nature](https://www.nature.com/articles/s41586-024-07389-x)
- Haltere campaniforms and b1 steering: [JEB 2026](https://journals.biologists.com/jeb/article/229/6/jeb250431/371120/), [numerical model (PMC6127168)](https://pmc.ncbi.nlm.nih.gov/articles/PMC6127168)
- Jump force: [Zumstein et al. 2004 JEB](https://journals.biologists.com/jeb/article/207/20/3515/14914/); jump myofibril tension: [PubMed 42235795](https://pubmed.ncbi.nlm.nih.gov/42235795/)
- Central neuron properties: [Gouwens & Wilson 2009](https://www.jneurosci.org/content/29/19/6239); [larval central neurons 2002](https://journals.physiology.org/doi/full/10.1152/jn.2002.88.2.847)
- Counter-example (unconstrained latents): FlyGM, [arXiv 2602.17997](https://arxiv.org/abs/2602.17997)
