# Session 12 prompt: fill in the fly's information; fidelity ladder; many copies in parallel (unattended, 5 hours maximum)

Paste everything below the line into a fresh Claude Code session in `/Users/ben/fly-emulation`.

---

You are continuing the fly-emulation project **unattended**. Ben will not answer questions. You have Ben's standing authority to act as a creative scientific researcher and make judgement calls within the guardrails. Record every deviation and its reason.

## The goal

Fill in **100% of the fly's information at the highest fidelity that could plausibly matter**: finish the entire brain-body build, get many copies running in parallel, and run experiments that fill in data. **Do not tweak parameters toward a bit of behaviour.** Stability and behaviour checks are guardrails, not objectives. Progress is measured by the ledger: slots moved from absent / default / guessed to measured, derived or biology-inferred values, per mechanism and grain. Report those numbers at the start and end of the session.

Per-cell and per-synapse properties are in scope. They cannot be measured one by one; infer them from biology: morphology (size), position (segment, side), development (hemilineage, birth order, homeostatic development rules) and transcriptomes matched to cell types (receptors, channels, innexins, modulator and peptide receptors). Rule parameters are the searched unknowns; per-cell values follow from them.

## Order (see `docs/PLAN_NEXT.md` and `docs/FIDELITY_LADDER.md`)

0. Session 11 built **rung 2** (synapse receptor mix and kinetics), but it is not adopted (F-R2-1, DECISIONS 2026-10-01 02:44). m9 remains the working model.
   - What exists, all neutral by default, with candidate profile `m10p`:
     - conductance synapses on CPU and GPU (equal);
     - slow-receptor shares from mRNA;
     - `tau_s_inh`;
     - a charge-basis slow share.
   - The blocker: conductance synapses cut sugar -> MN9_L to about 1 Hz. The block sits at GNG108, two synapses in, and the inferred cause is inhibitory shunting.
   - Next, in order:
     - Done at 03:01: the recorded e_inh (-56) and threshold-referenced weights (m10q) give silence and sugar 2.4 Hz (DECISIONS 2026-10-01 03:01).
     - (a) Done in part: the class-gain re-search on m10q was pre-registered at 03:23. 12 of 24 candidates are scored and c008 leads (J 3.68). c012-c023 are running detached on backhouse.
       - First, collect them (HANDOFF gives the commands) and run their closed loops.
       - Then run the held-out test once on the overall best (seeds 23-25 plus the held-out assays).
       - Seeds 29-31 are now used, so new fits start at 32.
     - (b) Extend the resting-potential fill as type matches are confirmed (DN AX -59, Schnell 2017, needs a type match). The Azevedo and Agrawal rests are held out.
   - The other rung-2 gaps remain:
     - per-receptor rise times;
     - facilitation;
     - ORN/leg depression.

1. Ledger by source level and grain (small, first), reconciled with `data/model/mechanisms.yaml`.
2. Per-cell and per-synapse filling from biology and transcriptomes, each rule with a neutral-equivalence test, a test against a measured within-type gradient where one exists, and labelled evidence. Download the atlases you need to backhouse (≤ ~200 GB approved).
3. Many copies in parallel: batch the Python body code across flies; GPU-physics feasibility; equivalence first; the pre-declared port decision rule in PLAN_NEXT.
4. Body items at plausible fidelity (PLAN_NEXT §3).
5. Experiments: ensemble sensitivity/ablation to find which unknowns matter; then fitting remaining unknowns to recorded physiology (pre-registered, baseline-checked targets, held-out judgement).

Use subagents (at most two at a time, types that cannot spawn agents or general-purpose told not to; partition files) for bounded parallel parts: e.g. one on transcriptome-to-type receptor/channel tables, one on batching the body code.

Read first, in this order: `CLAUDE.md`; `docs/HANDOFF.md`; `docs/PLAN_NEXT.md`; the session 11 sections of `docs/FINDINGS.md` and `docs/DECISIONS.md`; `docs/FIDELITY_LADDER.md`; `docs/LESSONS.md`; `docs/WORKFLOW.md`; `docs/RUNNING.md`; `docs/GPU.md`.

## Principles that override convenience

- Biological bounds on every row of `data/model/parameters.csv`; never widen one to rescue a fit; a bound hit is a finding.
- Labels never upgrade. A value from a rule is inferred; a fitted value is inferred; a literature number is measured only after reading its source.
- Every new mechanism or rule enters at a neutral setting with a bit-identical neutral-equivalence test, then is switched on as a pre-registered change to the working model (m9), checked against the guardrails.
- Pre-register before scoring; check every criterion on the base model first; at most two post-hoc repairs per target.
- Probes step `Organism.motor_step()` and check MuJoCo warnings; the GPU must reproduce CPU results exactly before its numbers are used.
- Units: mm, g, s (torque µN·mm).

## Setup

1. `date`; create `docs/SESSION12_LOG.md`.
2. `uv run pytest tests -q` (~8 min) must pass.
3. backhouse: it stopped answering ssh and ping at the end of session 10. Check `ssh -o ConnectTimeout=8 backhouse 'wsl -d Ubuntu -- echo ok'`; if down, work Mac-only (≤ 3 heavy processes) and say so. If up: one `sleep infinity` keep-alive (kill it at the end); `scripts/sync_backhouse.sh` (check it prints `synced` before launching jobs); ≤ 8 model processes (a GPU loop with W body workers counts as W); leave PID 523 and the other GPU user alone.

## Guardrails (not objectives)

- `FLYEMU_PROFILE=m4`: sugar->MN9_L 8.9 ± 5.9 Hz (10 trials); closed loop seeds 0-2 silent.
- m7: closed loop seeds 0-2 silent; sugar->MN9_L 6.9 ± 2.3 Hz; template dead fly passes.
- m9 (default): closed loop seeds 12-19 silent; sugar->MN9_L 5.7 ± 1.4 Hz at 100 Hz, 15.7 at 200 Hz; sugar+bitter 0 Hz; bitter 0 Hz. Fresh seeds for new fits start at 32 (20-22, 26-28 and 29-31 used by rung 2 fits; 23-25 reserved, unseen, for the rung-2 held-out test).
- Stop starting new work at 4 h 40 m, then wrap up (WORKFLOW §2), including the ledger before/after and a plain-language summary for Ben.
