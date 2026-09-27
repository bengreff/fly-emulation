# Session 9 prompt: unattended, 5 hours maximum

Paste everything below the line into a fresh Claude Code session in `/Users/ben/fly-emulation`.

---

You are continuing the fly-emulation project **unattended**. Ben will not answer questions. You have Ben's standing authority to act as a creative scientific researcher and make judgement calls. Record every deviation and its reason; the guardrails below still hold.

## Why this session is different

Eight sessions have tuned one mechanism at a time: 36 pre-registered tests, about 8 passes, and mostly stability checks. The session-8 reassessment (end of `docs/SESSION8_LOG.md`, DECISIONS s8) found three structural reasons.

1. **The body lies.** In the best recording (m4, config T, seed 0), wing joints sit at a range limit 82% of the time, abdomen joints 62% (every pitch joint 100%), head and neck 47%, legs 18%.
   - Only the leg motor units have measured forces and signs. Wing, abdomen and head actuators use a guessed force per spike and guessed signs, with one net torque per joint and no antagonist stiffness, so any tonic motor-neuron firing pins them.
   - A real fly's wings fold through hinge and passive mechanics, not through motor-neuron torque. Every embodied result so far is confounded by this layer.
2. **One global synapse strength cannot be both stable and functional.** Stability forces it low (0.157 mV), and function then fails everywhere it was tested: AL, leg reflex, CX ring. Inhibitory populations (Delta7, ER) mostly inhibit each other and fall silent. Biology gets stability from class-specific properties that the model lacks. Hand-tuning one knob at a time does not converge in a recurrent system: each fix breaks another target, and the post-hoc budget then stops the work.
3. **Unverified tools cost whole sessions.** KC transmitter labels, a non-local ring kick and a mirrored EPG heading map each invalidated conclusions.

The strategy, in order:
1. an **honest body** (unknown actuators passive, not guessed);
2. an **honest scoped configuration for locomotion** (the CX ring clamped and labelled, so walking work is not blocked by the compass);
3. a **calibration engine**: derivative-free optimisation of a small, interpretable, class-level parameter vector against a battery of fit-set physiology targets, judged only on held-out data.

This replaces hand-tuning as the main way forward.

## Before anything else

1. Run `date`; create `docs/SESSION9_LOG.md` with the start time. Use `date` for every timestamp.
2. Follow `docs/WORKFLOW.md`: evidence labels; pre-registration; fit / dev / held-out / sealed; the post-hoc budget of 2; ≥ 3 seeds; process hygiene; git.
3. Read `docs/HANDOFF.md`, `docs/PLAN_NEXT.md`, `docs/MODEL.md`, FINDINGS "# Session 8" and DECISIONS "## Session 8".
4. Run `uv run pytest tests -q`; it must pass.
5. **backhouse** (`ssh -o ConnectTimeout=8 backhouse 'wsl -d Ubuntu -- echo ok'`):
   - keep one `sleep infinity` keep-alive attached, and kill it at the end (s8 left three orphans);
   - run `scripts/sync_backhouse.sh`;
   - **≤ 8 model processes at once** (each peaks at 2.6–3.2 GB; 12 thrashed);
   - build job lists with `scripts/mkjobs.py` (one bash script per job, BLAS pinned to one thread); never put quoted command lines through `xargs` or `ssh "..."`;
   - JAX with the RTX 4070 Ti SUPER (16 GB) is installed there, not on the Mac.
6. An old `sleep infinity` (PID 523) in backhouse WSL predates session 8. Leave it and mention it to Ben.

## Session rules

- Stop starting new work at 4h40m, then wrap up. Prefer a natural end over starting something that cannot finish.
- **Working profile m4.** Exact regression values differ between the Mac and backhouse, so compare like with like. Sugar→MN9 is marginal (8.9 ± 5.9 Hz over 10 trials); report any change that takes it below 5 Hz.
- **Stability criterion (Ben, s7):** CX ring types (EPG, PEN_a/b, PEG, Delta7, ER*, EL*) are scored by the bump test. Every other cell must go quiet after silencing (Q in `scripts/probes/score_warm.py`).
- **Every candidate that touches dynamics** gets stability under **both** default and T. The s8 MS rows passed default and then sustained a 9 Hz brain under T.
- Candidate rows: `FLYEMU_EXTRA_PARAMS`; candidate edge scaling: `FLYEMU_EDGE_SCALES`. Do not edit live tables until adopted.
- Reflex scoring always uses `--kp 100 --kd 0.133`. zsh on the Mac: `${=VAR}`.
- **Agents:** at most one subagent at a time, of a type that cannot spawn agents.
- **Verification first:** any new probe gets a unit test of what it claims (e.g. "the kick is local": kicked cells are contiguous in inferred heading) before its results are interpreted.

## Priorities

### 1. Honest body at rest (target ≤ 75 min)

- Add a body option `body:non_leg_actuators|mode`: `neural` (today) or `passive`.
  - `passive` gives zero neural torque to every wing, abdomen, head/neck, haltere and mouthpart actuator, with passive stiffness and damping toward flybody's default (folded) pose. Use flybody's own passive groups where they exist; otherwise declare a guessed stiffness.
  - Label it as an abstraction: these motor layers are **absent**, not simulated. That is more honest than guessed-and-wrong.
- Add a probe metric: the fraction of time each joint family sits within 3% of a range limit (see the s8 analysis in SESSION8_LOG).
- Pre-register the adoption criteria:
  - wing and abdomen at-limit fraction < 10%;
  - neural regression unchanged (the brain is untouched; motor spikes of non-leg MNs are still recorded);
  - standing (min z 0.5–1.5 s and 0.5–3.0 s) reported for default and T on **fresh seeds 3, 4, 5**.
- Record a 3 s browser replay of the best configuration (`scripts/record_organism.py`) and look at frames. Describe what is visible, honestly.

### 2. Scoped locomotion configuration L (target ≤ 60 min)

- **L = T + passive non-leg actuators + CX ring output clamped.** Implement it as a candidate edge scale of 0 on ring → non-ring edges, or silencing of the ring types. It is **visibly labelled** in every output as "CX clamped; not a biological-emulation result for navigation". s7 showed T is stable with ring output removed; re-verify under m4.
- Pre-register, on fresh seeds:
  - stability (Q) 3/3;
  - standing ≥ 0.90 mm over 0.5–3.0 s;
  - DNg100 stimulation → forward displacement vs no-stim control;
  - a **gait criterion**: alternating tarsal stance/swing in at least one leg pair, from tarsus contact or height traces;
  - MDN → backward, as a second command.
- The command-direction data from s7 (seeds 1–4) are spent; use seeds 5–8.

### 3. The calibration engine (the main work, ≥ 2.5 h)

**Goal.** A reusable, resumable harness that fits a small vector of interpretable, class-level parameters against a fit-set battery. Deliver a first run and an honest report. Adoption is optional this session; the engine is the deliverable.

- **Optimiser.** CMA-ES (`uv add cma`, or a minimal numpy implementation) on backhouse, 8 parallel evaluations, with a checkpoint every generation so it can resume. Derivative-free, because the objective is a closed-loop spiking simulation: gradients through it are not available, and a rate-model surrogate would add a second, unvalidated model.
- **Parameters.** ≤ 20, each with bounds, a prior and a biological interpretation. For example:
  - efficacy scales per transmitter class and region (ACh / GABA / Glu × brain / VNC);
  - leg-afferent output scale (T's ×10.9 becomes a fitted value with that prior);
  - CX ring adaptation increment and Delta7 output gain (the s8 bump candidates);
  - ER tonic drive;
  - VNC premotor input gain;
  - slow-MN drive.

  Parameters without any data constraint must not be added.
- **Objective (fit set only; say in the pre-registration which data each term uses):**
  - stability Q under default and T (a hard penalty);
  - sugar→MN9 in range;
  - PN spontaneous rate (spent/seen) in 1–5 Hz;
  - 13Bα static tuning slope (Agrawal, seen);
  - slow-MN reflex on the dev cell 180111 (seen; over budget as a gate, usable as a fit term);
  - Ben's CX bump criteria (B1/B2 with the strong kick at 4 headings, 12 nearest EPGs);
  - PEN resting rate (spent) in range;
  - under L: standing height.

  Keep each term's scale explicit, so the weights are declared, not tuned post hoc.
- **Held out, never in the objective:**
  - the sealed Azevedo spare cells (180621, 181127; open only via `score_reflex.py` after a dev pass);
  - flybench olfactory tasks 08/17/18/26/27;
  - command direction and gait on fresh seeds;
  - KC rest rate (spent, but not fitted).
- **Budget per evaluation.** Keep one evaluation ≤ 3–4 min of wall time on 8 cores (short windows; 1 seed during search, 3 seeds for re-scoring the best). Plan roughly 150–300 evaluations this session. Write the trace to `runs/s9_cmaes/` and a registry of each evaluation.
- **Report:** the best vector with its terms, how far every parameter moved from its prior, which terms conflict (a Pareto view), and a held-out score only if the pre-registered dev criteria pass.
- A conflict the optimiser cannot resolve is a result. For example: stability and a functional AL cannot coexist with any class-level setting. Such a conflict localises the missing biology.

### 4. If time remains

- Re-test adaptation + Delta7 ×4 under T **without** MS (its s8 B1 passes had MS on), fresh seeds.
- Check whether VNC premotor interneuron classes in the model should be graded (non-spiking): list the evidence found, do not change anything.

## Wrap-up

Follow WORKFLOW §2 "End":
- run the full tests, regressions, ledger and census;
- stop every process on both machines;
- write the FINDINGS section; rewrite HANDOFF (unverified foundations, sealed register) and PLAN_NEXT; write the session-10 prompt;
- log the post-hoc budget use per target;
- commit and push;
- end with a plain-language summary for Ben (an engineer, not a neuroscientist): what changed, what it means, what is next.
