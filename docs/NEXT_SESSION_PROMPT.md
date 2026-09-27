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

**The body is the behavioural testbed, not the thing being fitted.** Unknown actuators must not fake behaviour:
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

### 1. Passive non-leg body (≤ 40 min)

- Add `body:non_leg_actuators|mode` (`neural` | `passive`; passive = zero neural torque on wing, abdomen, head/neck, haltere and mouthpart actuators, with passive stiffness and damping to flybody's default folded pose; motor layer labelled absent).
- Add a joint-limit occupancy metric per joint family.
- Pre-register: wing and abdomen at-limit < 10%; neural regression unchanged; standing for default and T on fresh seeds 3–5.
- Adopt if it passes. Record a browser replay and describe the frames honestly.

### 2. GPU batched brain simulator (the core build, ~2 h)

- **Enable CUDA JAX on backhouse** (`uv add "jax[cuda12]"` or the matching extra for JAX 0.11.x; verify `jax.devices()` shows the GPU). Record versions in `docs/ENVIRONMENT.md`.
- **`src/flyemu/gpu/`: a batched LIF matching `lif.py`'s equations for the m4 mechanisms that matter first.** Those are exponential synapses, refractoriness, per-type thresholds/rests/tonic drive, delays per presynaptic type (bucketed), graded cells, adaptation and STD. Everything else raises `NotImplementedError` rather than being silently dropped.
  - **Class-decomposed weights:** w = Σ_k s_k · W_k, with W_k sparse (BCOO/segment ops) per parameter class. A batch of B brains then shares one sparse structure, and each brain carries its own scale vector s.
  - Delays: a spike-history ring buffer and one sparse product per delay bucket.
- **Equivalence tests against the CPU reference,** in `tests/`:
  - bit-level on a small random network (same spikes);
  - on the full brain, open-loop, a pre-registered tolerance on sugar→MN9 rate and the active-cell count;
  - a return-to-rest check.
- **Benchmark:** simulated seconds per wall second at B = 1, 16, 64 against the CPU simulator (≈ 50 s wall per simulated second). Record in `docs/ENVIRONMENT.md`. The GPU path is used only if it passes the tests.

### 3. Target library v1 and objective (~45 min, partly by the agent)

- **Agent task:** extract quantitative, per-cell-type physiology targets into `data/measurements/` with `use` = fit / held-out / sealed. This means resting and evoked rates or Vm, with conditions, n, uncertainty, source figure and table. Priority: CX (EPG, PEN, Delta7, ER), AL (ORN, PN, LN), MB (KC, MBON, DAN), optic lobe (T4/T5, Mi/Tm), descending neurons, leg premotor and MN. Assign held-out **by dataset**, keeping at least a third of datasets held out. Agent reports are leads; spot-check sources before labelling anything as measured.
- **Objective v1 (open-loop, GPU-evaluable):**
  - stability after sensory pulses (rule v2 populations);
  - sugar→MN9 in range;
  - resting-rate terms for the fit-set classes;
  - the CX bump from a strong local kick (12 nearest EPGs, inferred headings, 4 headings; B1/B2);
  - PN responses to Hallem-rate input.

  Each term has a declared scale. Pre-register the objective, parameter space and splits in DECISIONS **before** the search.

### 4. First class-level search (remaining time; may continue after wrap-up if checkpointed)

- CMA-ES (or a batched evolutionary search) over ~50–150 class-level parameters:
  - efficacy per transmitter × region;
  - per-class threshold/rest offsets;
  - per-class adaptation and STD;
  - Delta7/ER output gains;
  - leg-afferent scale;
  - neuromodulator pool gain.

  Bounds and priors come from data. Batch on GPU; checkpoint every generation to `runs/s9_search/`; log every evaluation.
- Re-score the top candidates on the CPU reference, open-loop and then closed-loop in the body (default and T, 3 seeds): stability, standing, command direction and gait on fresh seeds.
- **Report:**
  - the objective trace;
  - how far each parameter moved from its prior;
  - which targets conflict (a Pareto view);
  - the ensemble spread;
  - held-out scores only for candidates that pass the pre-registered fit criteria.

  A persistent conflict localises the missing biology, and that is a result.

## Wrap-up

Follow WORKFLOW §2 "End":
- run the full tests, regressions, ledger and census;
- stop every process on both machines, or document a checkpointed search left running and how to stop it;
- write the FINDINGS section; rewrite HANDOFF and PLAN_NEXT with the construction roadmap status; write the session-10 prompt;
- commit and push;
- end with a plain-language summary for Ben.
