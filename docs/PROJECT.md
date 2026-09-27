# Project specification

## Authoritative scope

The user wants an ultra-realistic simulation of the fly brain–body connection, with behavior constrained by the existing body of fly biology. The overall aspiration is that the simulated organism can live a fly-like life. Realism and agreement with actual data are the central objectives. A spectacular animation is not a sufficient result.

This is a gradient of demonstrated capabilities rather than a binary checklist. Full Tier 1 and Tier 2 are priorities; individual fidelity and uploading experiments will be reassessed afterward. Work continues alongside a propulsion project, so preserve useful intermediate results and avoid unnecessary infrastructure.

| Working tier | Intended capabilities | Interpretation |
|---|---|---|
| Tier 1: embodied repertoire | Posture, walking, turning, flight, transitions, responses to vision/odor/touch/proprioception, and eventually grooming/feeding and other natural actions | Increasingly complete immediate sensorimotor function |
| Tier 2: internal continuity | State-dependent behavior, adaptation, learning, memory, retention/forgetting, motivation and coherent behavioral selection | An organism with history and changing internal state |
| Tier 3: individuality | Persistent traits and learned preferences; potentially similarities to the scanned animal | A coherent constructed individual is distinct from demonstrated recovery of the donor's identity |

These are project definitions, not standard neuroscientific tiers. Define concrete assays, operating conditions and tolerances as each capability is undertaken. Do not call a handful of demonstrations “full Tier 1+2.” Also do not require every conceivable fly behavior before recognizing progress.

## The construction programme (from 27 September 2026)

The route to Tier 1–2 is to **construct** the fly, as set out in `docs/CONSTRUCTION.md`:
- build every mechanism that plausibly matters for behaviour, always on;
- represent every quantity the connectome does not fix as an explicit unknown, with hard bounds set by what fly biology allows;
- validate the body on its own, first with the brain dead;
- search within the bounds for flies that reproduce measured physiology;
- judge them on held-out data, and measure by ablation which mechanisms behaviour actually needs.

We simulate more rather than less, because no one has run this experiment and sufficiency cannot be assumed.

## Optimization and evidence

Behavioral optimization is authorized. It must seek a realistic biological reconstruction consistent with anatomy, physiology, muscle mechanics and other research—not simply a task-solving network constrained by an adjacency matrix.

Trusted measurements constrain allowable models. Uncertain, indirect or preparation-specific observations require explicit uncertainty rather than universal hard constraints. Resolve apparent contradictions by inspecting species, sex, genotype, age, temperature, preparation, measurement method and physiological state. Do not use “within reason” to excuse systematic contradictions.

Examples:

- Fit an unknown synaptic conductance to neural and behavioral observations while preserving supported receptor and anatomical constraints.
- Fit muscle mechanics to measured force/motion evidence; do not place a muscle on an anatomically impossible attachment to make the fly walk.
- Infer a missing connection if anatomical/physiological evidence supports it, recording alternative hypotheses. Do not add arbitrary shortcuts from input to output.
- Simplify a mechanism when the approximation reproduces the relevant independent measurements, then test whether it survives integration.

Exact microscopic reconstruction is not assumed. “Ultra-realistic” means progressively stronger mechanistic and empirical fidelity, not automatically the maximum number of differential equations.

## Plasticity and lifetime

The earlier fixed-connectivity constraint is revoked. Synaptic efficacy changes, adaptation, neuromodulation, memory mechanisms, homeostasis and structural plasticity are permitted when biologically justified. Structural change is not mandatory in early milestones; omission should be explicit and appropriate to the time horizon.

Separate:

1. Outer fitting: an optimizer modifies candidate biological parameters between trials.
2. Within-lifetime plasticity: the simulated organism changes through its modeled biology.
3. Checkpoint state: all variables required to continue that specific simulated individual.

After the outer fit is frozen, demonstrate new learning through the organism's own mechanisms. Persistent preferences hard-coded by the optimizer do not establish learning.

## What a result can claim

| Result | Supported claim |
|---|---|
| Reproduces fitting data | A model can fit those observations |
| Predicts withheld behavior and neural responses | The model generalizes over tested conditions |
| Predicts specific biological interventions | Stronger evidence for correct causal organization |
| Several admissible completions agree | Evidence that remaining uncertainty is unimportant for those tests, conditional on shared assumptions |
| Recovers a synthetic individual's hidden memories/traits | Reconstruction fidelity within the tested reference/model families |
| Resembles the scanned animal on independent individual-specific evidence | Preliminary individual recovery for those properties |

A new constructed individual can be scientifically useful without matching the donor. That does not imply that its behavior, memories or consciousness have been copied from the donor.

## Later extension: information sufficiency

Once a validated reference organism exists, checkpoint it, hide selected information and reconstruct it repeatedly. Vary measurement type, resolution, noise and precision. Evaluate capabilities and individual responses that were not supplied during reconstruction.

Distinguish information from the synthetic scan, population priors, behavioral fitting targets, known life history and simulator assumptions. Use different reconstruction methods and reference model families to test for shared-assumption bias. This estimates recoverability within specified model classes; it does not directly prove human-upload requirements.

## Explicitly superseded claims

- No-behavioral-tuning is an optional comparison condition, not a project restriction.
- Fixed anatomical connectivity is no longer a permanent restriction.
- Full Tier 3 and donor identity are not the immediate acceptance requirement.
- Earlier success probabilities were subjective and changed with scope. Do not treat them as evidence or engineering gates.
- The illustrative 17% measured-slot estimate counted fields in an invented representation. It was not biological completeness.
- A few-GB model storage estimate was representation-dependent, not a demonstrated Tier 3 requirement or a GPU-throughput benchmark.
- “All major pieces exist” does not imply every causal interface is calibrated or available in one compatible specimen.
