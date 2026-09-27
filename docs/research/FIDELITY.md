# How much fidelity does a fly need? Mechanism budget (session 8→9)

**Question (Ben):** assuming perfect data, what level of physical and neural fidelity must the simulation have to produce the target behaviours, and so how many mechanisms must be built? This is a synthesis of two research notes:
- `fidelity_neural_s9.md` (neural and sensory transduction);
- `fidelity_body_s9.md` (body, muscle, contact, flight, periphery).

The detail and citations are there. Evidence labels are those notes' own: [verified] means the full text was read; most other claims are abstract-level or unverified and must be checked before being used as constraints. The counts below are **judgements from the literature, not measurements**.

## The answer in one paragraph

A fly that walks, stands, flies, responds to its senses, grooms, feeds and learns needs neither Hodgkin–Huxley neurons, detailed dendrites, fluid dynamics, cuticle finite elements, nor wing-hinge sclerite mechanics. It does need:

- on the brain side:
  - **point neurons with the right mode per cell class** (spiking or graded);
  - per-class intrinsic parameters with background drive;
  - receptor-resolved synapses with fast and slow kinetics;
  - a few specific dynamic mechanisms (short-term depression, adaptation, presynaptic and shunting inhibition, gap junctions at named sites);
  - for state and learning, neuromodulator and peptide layers with explicit plasticity rules;
- on the body side:
  - **a measured rigid skeleton with passive joint mechanics (stiffness, damping, rest angle)**;
  - **antagonist muscle pairs with activation dynamics and force–length–velocity**;
  - adhesion with mechanical detachment;
  - filtered sensory periphery;
  - for flight, a wingbeat oscillator, a steering-muscle→wing-kinematics map, quasi-steady aerodynamics and a haltere rate signal.

That is **about 49 distinct mechanisms**:

| | Tier A: posture, walking, senses | Tier B: flight, takeoff, landing | Tier C: grooming, feeding, state, learning | Total |
|---|---|---|---|---|
| Neural | 10 | 5 | 9 | 24 |
| Body and periphery | 13 | 7 | 5 | 25 |

Of the 49, **roughly 12 are in place as mechanisms, about 20 are partial or guessed, and about 17 are absent.** The published sufficiency results all show the same thing: the mechanisms can be simple, but their **parameters must be per cell class and fitted**. That includes Lappalainen 2024 (optic lobe, 734 fitted parameters), Shiu 2024 (whole-brain LIF) and Pugliese 2025 (VNC walking rhythm with no intrinsic bursting). This is exactly the construction-by-search programme.

## Required level per subsystem (assuming perfect data)

| Subsystem | Required level | Not required (revisit only if validation points at it) | Ours now |
|---|---|---|---|
| Neuron | point neuron; spiking or graded by class; per-class V_rest, τ, threshold, gain, background drive; adaptation per class | Hodgkin–Huxley; morphology beyond T4/T5, APL, LPTC | point LIF; borrowed shared V_rest/threshold; graded for a few types; **no background drive** |
| Synapse | per-class strength; receptor sign; fast and slow kinetic classes; shunting inhibition where division is computed (T4/T5, possibly AL); depression at sensory first synapses; presynaptic inhibition at afferents | stochastic single vesicles (a lumped noise term suffices) | **one global efficacy**; sign from transmitter plus 54 transcript rows; one τs; options off |
| Electrical | gap junctions at a curated list (GF, JO→GF, eLN–PN, LPTC, flight afferent→steering MN) | brain-wide unknown coupling | GF only |
| Neuromodulation and peptides (Tier C) | pools with per-type receptor maps and second-to-minute kinetics; peptide/metabolic state layer | cAMP/PKA biochemistry | pools inert (MS rows unstable under T) |
| Plasticity (Tier C) | order-sensitive two-factor KC→MBON rule per compartment; decay and consolidation; ring-neuron→EPG mapping | molecular memory cascades | one-directional KC→MBON depression, off |
| Sensory transduction | adapting photoreceptor; two-stage ORN; FeCO claw/club/hook with adaptation; campaniform load; JO; GRN | full phototransduction cascade | mostly static proxies |
| Skeleton | rigid segments, measured mass and inertia, leg DOFs plus a compliant tarsal chain | cuticle compliance (except thorax as the flight spring) | flybody: in place |
| Passive joints | per-joint stiffness, damping and **rest angle**, measured. Passive forces dominate at fly scale, so they set posture and reflex gain | none | flybody default, 1 µN·mm/rad everywhere; guessed rest angles |
| Muscle | **antagonist Hill-type pairs per leg DOF** (activation dynamics, F–L–V, rigid tendon acceptable); per-unit twitch with saturation and facilitation | fibre-level models | **one net torque per DOF**, capped at ±30 µN·mm; slow-unit twitch decay 100 ms (guessed; measured slow twitches do not peak within 500 ms) |
| Non-leg motor | neck actuated (3 DOF); abdomen 1–2 steering DOFs for flight trim; wing: see flight | none | guessed forces and signs; they pin joints (wings at a limit 82% of the time) |
| Contact | soft contact with friction; adhesion on in stance, released by shear or peeling (needed > ~30° slopes and on ceilings) | none | friction in place; adhesion switched neurally |
| Flight (Tier B) | ~200 Hz wingbeat oscillator for asynchronous muscle and thorax resonance; steering-muscle→wing-kinematics map (Melis, Siwanowicz & Dickinson 2024); quasi-steady aerodynamics; haltere Coriolis signal; ≤ 0.05 ms step | CFD; sclerite mechanics | **only quasi-steady aerodynamics**; wings driven by spike→torque (wrong in kind) |
| Takeoff (Tier B) | fast, high-force TTM extensor via GF | none | torque cap likely too low by an order of magnitude |
| Feeding and grooming (Tier C) | proboscis MN→muscle map; cibarial pump and crop fill; bristle-field contact map | CFD of ingestion | proboscis partial; no pump; no bristle map |
| Numerics | 0.1 ms walking (have); ≤ 0.05 ms flight | none | 0.1 ms |

## What this means for constructing the brain by search

1. **Build the mechanisms first; the search fills parameters, never missing physics.** If a mechanism is absent, the optimiser distorts other parameters to compensate. For example, neural weights fitted to a net-torque body learn to fake antagonist stiffness. Tier A body mechanisms (passive joints with rest angles, antagonist Hill muscles, twitch kinetics, adhesion detachment, passive non-leg joints) and Tier A neural mechanisms (graded modes, per-class intrinsics and background drive, per-class strength) must exist before the Tier A search.
2. **Assign every unknown to exactly one mechanism and one grain.** Order-of-magnitude size of the Tier A search space at the class grain:

   | Group | Estimate | Unknowns |
   |---|---|---|
   | Neural | ~150 classes × ~8 parameters (V_rest, τ, threshold gap, background, adaptation, STD, output strength, input gain) | ~1,200 |
   | Receptor kinetics | ~150 classes × 2 | ~300 |
   | Joints | ~45 actuated DOFs × 3 | ~135 |
   | Muscles | ~36 antagonist pairs × 2 × ~5 | ~360 |
   | Adhesion and contact | | ~30 |
   | **Total** | | **~2,000** |

   Fitting that many unknowns needs the batched GPU simulator and a target library of comparable size. Measured values (e.g. leg motor-unit forces, the 54 transcript-based signs, FlyMimic muscle parameters where they exist) are fixed or tightly bounded, which shrinks the effective space.
3. **The ledger becomes the build plan.** Each `data/ontology/fly_information.yaml` entry gets a tier (A/B/C), a required level and a grain. Mechanisms the ontology lacks are added: wingbeat oscillator, hinge map, haltere Coriolis signal, bristle field, cibarial pump, background drive per class. The ledger then reports, per tier, the mechanisms built and the parameters constrained by data.

## Where perfect data would still not settle it

(Detail in both notes.)
- **Non-spiking VNC interneurons:** which classes, in the fly specifically, are non-spiking is unmeasured.
- **Walking rhythm:** whether it emerges from the connectome alone. Pugliese says yes in a rate model; untested with spiking and a body.
- **Passive stiffness:** no direct *Drosophila* measurement was found.
- **Torque vs muscle:** no study yet shows a torque-actuated fly failing where a muscle model succeeds. The argument for muscles is mechanistic (stiffness modulation, co-contraction, slow-unit kinetics), not a demonstrated failure.
- **Flight timestep:** needs a convergence test (0.1 vs 0.05 ms).
