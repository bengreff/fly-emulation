# Session 9 prompt: unattended, 5 hours maximum

Paste everything below the line into a fresh Claude Code session in `/Users/ben/fly-emulation`.

---

You are continuing the fly-emulation project **unattended**. Ben will not answer questions. You have Ben's standing authority to act as a creative scientific researcher and make judgement calls. Record every deviation and its reason; the guardrails below still hold.

## The research programme from now on: construct the brain by search

**Ben's direction (end of s8):** be ambitious. The project is to **construct a brain**. The connectome fixes who connects to whom. Everything it does not fix (synaptic strength and sign per class, receptor kinetics, thresholds and resting potentials, adaptation, short-term plasticity, neuromodulatory gains, tonic drive) is found by **systematic search over parameters**, constrained by every measurement we can collect, and judged on held-out experiments.

That replaces eight sessions of one-knob hand-tuning: 36 pre-registered tests, about 8 passes. The evidence that hand-tuning cannot converge is in the reassessment at the end of `docs/SESSION8_LOG.md`.
- A single global efficacy cannot be both stable and functional.
- Inhibitory populations (Delta7, ER) mostly inhibit each other and fall silent.
- Every local fix breaks another target.

The search is allowed by `CLAUDE.md`, which says to fit unknown parameters against physiology and behaviour. The constraints:
- fitting happens **between runs** (construction), never within an episode;
- no decoder stands in for missing circuitry;
- priors come from data (transcripts, synapse counts, physiology);
- **held-out interventions and datasets** judge the result, never the fit set.

**The programme has four pillars:**

1. **A fast, batched simulator.** Evaluate many candidate brains at once on the RTX 4070 Ti SUPER (JAX + CUDA). The CPU simulator (`src/flyemu/lif.py`) stays the reference: the GPU path must reproduce it before it is trusted (`CLAUDE.md`: select GPU implementations by measured accuracy and throughput).
2. **A structured parameter space.** The connectome's topology is fixed. Parameters sit in a hierarchy with data-derived priors:
   - global;
   - transmitter × region (brain, optic lobe, VNC);
   - cell class (≈ hundreds: superclass/class/lineage groups, ring types, PN/LN/KC/MBON, premotor, MN classes);
   - later, per type (≈ 14k) with a penalty toward the class value.

   Transcript-based signs (54 types) and measured values are fixed or tightly bounded, never free.
3. **A target library.** Every quantitative observation we can get, each tagged fit / held-out / sealed by *dataset*:
   - resting rates;
   - pathway activations (sugar→MN9 and the Shiu-style activation screens);
   - PN and ORN responses;
   - T4/T5 direction selectivity;
   - the CX bump (Ben's criteria);
   - slow-MN reflex tuning;
   - 13Bα tuning;
   - stability after sensory pulses;
   - command direction and gait in the body.

   Existing tables: `data/measurements/targets_session6.csv` and the flybench tasks.
4. **Search:**
   - stage 1: population-based (CMA-ES, batched on GPU) over ~50–150 class-level parameters;
   - stage 2: gradient refinement with surrogate spike gradients in JAX, per-type parameters regularised toward their class;
   - output: an **ensemble** of brains that satisfy the fit set. Their spread is our uncertainty. Report where the ensemble agrees and where it disagrees.

**The body must be physically a fly before the search starts** (Ben, end of s8: fidelity and clean unknowns come first; see `docs/research/FIDELITY.md`). Unknown actuators must not fake behaviour:
- **wing, abdomen, head and haltere actuators become passive** (with the motor layer labelled absent), because they currently pin joints (wings 82% of the time at a range limit);
- flygym's musculoskeletal model and MuJoCo Warp GPU are the later route to real muscles and a batched body.

## Before anything else

1. Run `date`; create `docs/SESSION9_LOG.md` with the start time. Use `date` for every timestamp.
2. Follow `docs/WORKFLOW.md`: evidence labels; pre-registration; fit / dev / held-out / sealed; ≥ 3 seeds; process hygiene; git. The post-hoc budget of 2 applies to hand repairs. A declared search over a declared parameter space against a declared fit set is not a post-hoc repair, but **the parameter space, objective and splits must be pre-registered before the search runs**.
3. Read `docs/HANDOFF.md`, `docs/PLAN_NEXT.md`, `docs/MODEL.md`, FINDINGS "# Session 8" and DECISIONS "## Session 8".
4. Run `uv run pytest tests -q`; it must pass.
5. **backhouse** (`ssh -o ConnectTimeout=8 backhouse 'wsl -d Ubuntu -- echo ok'`):
   - keep one `sleep infinity` keep-alive and kill it at the end;
   - run `scripts/sync_backhouse.sh`;
   - ≤ 8 CPU model processes at once (2.6–3.2 GB each);
   - build job lists with `scripts/mkjobs.py`; never put quoted command lines through `xargs` or `ssh "..."`;
   - old `sleep infinity` PID 523 predates s8: leave it and mention it.

## Session rules

- Stop starting new work at 4h40m, then wrap up. Long searches must checkpoint and resume, so a run left going at the end is fine if it is recorded and Ben knows how to stop it.
- **Working profile m4.** Mac and backhouse differ in exact values. Sugar→MN9 is marginal (8.9 ± 5.9 Hz / 10 trials).
- **Stability (Ben, s7):** CX ring types (EPG, PEN_a/b, PEG, Delta7, ER*, EL*) are scored by the bump test; every other cell must go quiet after silencing. A candidate that touches dynamics must be stable under **both** default and T.
- **Verification first.** Every new tool gets a test of what it claims before its results are read. s8 lost results to a non-local kick, a mirrored heading map and wrong KC transmitter labels.
- **Agents:** at most one at a time, of a type that cannot spawn agents. Use it for target extraction (below).
- Candidate rows: `FLYEMU_EXTRA_PARAMS`; candidate edge scaling: `FLYEMU_EDGE_SCALES`.

## Priorities

Read `docs/research/FIDELITY.md` first. It sets the mechanism budget: ~49 mechanisms, of which Tier A is 13 body + 10 neural. Principle: **build the mechanisms first; the search fills parameters, never missing physics.** A search run against a body with net-torque joints would teach neural weights to fake muscle stiffness. This session makes the fly physical and assigns the unknowns. The GPU engine and search follow in session 10.

### 1. Assign every unknown cleanly (≤ 45 min)

- Extend `data/ontology/fly_information.yaml`: each entry gets `tier` (A/B/C), `required_level` (from FIDELITY.md) and `grain`.
- Add the mechanisms it lacks:
  - per-class background drive;
  - antagonist muscle pairs;
  - wingbeat oscillator;
  - steering→wing-kinematics hinge map;
  - haltere Coriolis signal;
  - bristle-field contact map;
  - cibarial pump and crop.
- Extend `scripts/blank_ledger.py` to report per tier: mechanisms built / partial / absent, and parameters data-constrained / free. Commit the ledger as the build plan.

### 2. Tier A body, made physical (~2.5 h)

In this order, each with a pre-registration and a test of what it claims:

1. **Passive non-leg joints:** wing, abdomen, head/neck, haltere and mouthpart neural torque off (motor layer labelled absent), passive stiffness and damping to flybody's folded pose. Add the joint-limit occupancy metric (s8: wings at a limit 82% of the time).
2. **Passive leg joint mechanics:** per-joint stiffness, damping and rest angle. Search the literature first (one agent): Drosophila or insect passive joint torque, e.g. Hooper 2009 locust scaling, Azevedo 2020 passive tibia forces, FlyMimic. Label every value measured / inferred (scaled) / guessed.
3. **Antagonist Hill-type muscles per leg DOF,** using MuJoCo's built-in muscle actuators (activation dynamics, F–L–V). Parameters from the FlyMimic front-leg model where available (fitted), size-scaled for the other legs (inferred). Motor units map onto their muscle (flexor vs extensor), not onto a signed net torque; the calibrated joint signs become muscle identities. Keep the torque path as an option for comparison.
4. **Twitch kinetics per unit class:** slow units rise slowly (Azevedo 2020: slow twitches do not peak within 500 ms), with saturation.
5. **Adhesion detachment by load and shear** instead of a pure neural switch.

Each step is verified by: leg posture at rest vs measured resting angles (where available); the resistance reflex sign (dev cell only; sealed cells stay sealed); standing (default and T, fresh seeds 3–5); neural regression unchanged. Record a browser replay after the last step and describe the frames honestly.

### 3. Tier A neural mechanisms (~1 h, if time)

- **Graded mode per class for the VNC local interneurons and the optic-lobe front end.** Evidence for which classes are non-spiking goes in a table first, labelled.
- **A per-class background-drive term** (a mechanism with a default of 0, ready for the search).
- Do not fit these yet.

### Deferred to session 10

- CUDA JAX on backhouse; a batched GPU LIF with class-decomposed weights and delay buckets, equivalence-tested against `lif.py`; a benchmark.
- Target library v1, split by dataset.
- The pre-registered class-level CMA-ES search.

These are specified in `docs/PLAN_NEXT.md` (stages 1–3).

## Wrap-up

Follow WORKFLOW §2 "End":
- run the full tests, regressions, ledger and census;
- stop every process on both machines, or document a checkpointed search left running and how to stop it;
- write the FINDINGS section; rewrite HANDOFF and PLAN_NEXT with the construction roadmap status; write the session-10 prompt;
- commit and push;
- end with a plain-language summary for Ben.
