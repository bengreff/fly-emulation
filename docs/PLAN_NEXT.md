# Plan: next experiments

**Forward-looking only; rewritten each session.** Completed plans are in `docs/archive/`. The ranked list below is also the basis of `docs/NEXT_SESSION_PROMPT.md`.

## Goal and layers

The male-CNS connectome controls an accurately simulated fly body. Each layer is checked separately, because a good-looking behaviour can hide a wrong layer.

| Layer | "Accurate" means |
|---|---|
| Neural | predicts held-out published interventions better than a shuffled-wiring control; resting and driven rates within measured ranges |
| Neuromuscular | per-spike force and twitch within Azevedo 2020 ranges |
| Body | mass-, range- and collision-checked |
| Behaviour | kinematics match measured data under the same stimulus protocol |

## Where session 8 left things

- **Working model m4:** curated transmitters (consensusNt), efficacy recalibrated by a closed-loop rule, monoamines without fast sign. Sugar→MN9 is marginal (8.9 ± 5.9 Hz over 10 trials).
- **Config T under m3 stands on 2/3 seeds** (min z 1.03 / 0.97 mm). T's only failure is the saturated CX ring.
- **Receptor transcripts for ~95 types** (Davis 2020, Turner-Evans 2020, Epiney 2025) give glutamate sign rows for 54 types.
  - Wiring cannot predict receptor signs.
  - snRNA iGluR/GluCl ratios are biased upward relative to bulk.
- **EPG headings are inferred from connectivity.** All ring position results before that fix are unreliable, including s7's single-knob screens. Those were re-screened under m4 (DECISIONS s8).

## Ranked next steps: the construction programme

**Ben's direction (end of s8):** construct the brain by systematic search over the parameters the connectome does not fix. Constraints: data-derived priors, a growing target library, and held-out datasets as judge. The session prompt (`docs/NEXT_SESSION_PROMPT.md`) has the detail.

| Stage | Session(s) | Deliverable | Success measure |
|---|---|---|---|
| 0 | 9 | passive non-leg body; joint-limit metric | wings/abdomen < 10% at limit |
| 1 | 9 | CUDA JAX; batched GPU LIF with class-decomposed weights and delay buckets; equivalence tests vs `lif.py`; benchmark | tests pass; ≥ 10× brains per wall-second vs CPU |
| 2 | 9–10 | target library v1 (per-type physiology, split by dataset); pre-registered objective | ≥ 100 quantitative targets, ≥ 1/3 of datasets held out |
| 3 | 9–10 | class-level CMA-ES search (~50–150 params); CPU and body re-scoring of the best | fit-set terms met without stability loss; held-out score reported |
| 4 | 10–11 | closed-loop evaluation at scale (CPU pool now; MuJoCo Warp GPU body later); behavioural targets (standing, command direction, gait) | fresh-seed held-out behaviour |
| 5 | 11–12 | gradient refinement (surrogate spike gradients) of per-type parameters regularised to class; an ensemble of brains | ensemble spread and held-out prediction reported per target |
| 6 | 12+ | musculoskeletal body (flygym muscle model) replaces torque actuators; flight hinge later | behaviour without passive-actuator abstractions |
| 7 | 13+ | lifetime plasticity (KC→MBON, DAN-gated) and internal states (neuromodulator pools fitted) | held-out learning and state-dependent behaviour |

In parallel, keep filling blanks with type-matched data (transcriptomes, FANC access for leg sensors). Each fill fixes or tightly bounds a parameter, which shrinks the search.

## Later milestones (dependency order)

- Flight: needs a wing hinge driven by steering muscles, and power-muscle and thorax dynamics.
- Neuromodulation and internal state: pools exist but are inert; receptor data per type is needed. M0 shows the fast-sign placeholder must go first.
- Learning: KC→MBON depression exists, off. Needs an odour-shock assay held out from all fitting.
