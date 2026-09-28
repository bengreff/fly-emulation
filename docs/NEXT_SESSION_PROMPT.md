# Session 11 prompt: from construction to search (unattended, 5 hours maximum)

Paste everything below the line into a fresh Claude Code session in `/Users/ben/fly-emulation`.

---

You are continuing the fly-emulation project **unattended**. Ben will not answer questions. You have Ben's standing authority to act as a creative scientific researcher and make judgement calls within the guardrails. Record every deviation and its reason.

## Your job

Session 10 finished construction to the point where every mechanism exists (0 absent), adopted **m5** (the template body plus two searched class values) as the working model, and ported the brain to the GPU with exact equivalence. Session 11 builds the **search engine** and runs the first broad, pre-registered class-level search. Follow `docs/PLAN_NEXT.md`:

1. Make the exact GPU closed loop (`scripts/gpu_closed_loop.py --k 1 --workers N`) the evaluator; measure its throughput; keep k = 1 (k > 1 changes the dynamics, F-STAB-5).
2. Target library v1: register each target only after checking it on m4 and m5 (session 10 lost a post-hoc attempt to an unchecked criterion, F-STAB-4). Split fit / dev / held out; the sealed register in HANDOFF applies.
3. Pre-registered CMA-ES over class-level N5 (release, input) and N3 (tonic drive) within bounds; brain-only targets via `scripts/gpu_assay.py`. Report margins and bound hits.
4. Then switch neutral mechanisms on at their priors one group at a time (N15 latency first: it already passed stability), re-testing m5.
5. Body battery and flight items as time allows.

Read first, in this order: `CLAUDE.md`; `docs/HANDOFF.md`; `docs/PLAN_NEXT.md`; the session 10 sections of `docs/FINDINGS.md` and `docs/DECISIONS.md`; `docs/LESSONS.md`; `docs/WORKFLOW.md`; `docs/RUNNING.md` (GPU section); `docs/GPU.md`.

## Principles that override convenience

- Biological bounds on every row of `data/model/parameters.csv`; never widen one to rescue a fit; a bound hit is a finding.
- Labels never upgrade. Fitted values are inferred.
- Pre-register before scoring; check every criterion on the base model first; at most two post-hoc repairs per target (the template-adoption target used one in session 10).
- Verification first: new probes step `Organism.motor_step()` and check MuJoCo warnings; the GPU evaluator must reproduce CPU results exactly before its numbers are used.
- Units: mm, g, s (torque µN·mm).

## Setup

1. `date`; create `docs/SESSION11_LOG.md`.
2. `uv run pytest tests -q` (~8 min) must pass.
3. backhouse: `ssh -o ConnectTimeout=8 backhouse 'wsl -d Ubuntu -- echo ok'`; keep one `sleep infinity` keep-alive and kill it at the end; `scripts/sync_backhouse.sh`; ≤ 8 model processes (a GPU loop with W workers counts as W); leave PID 523 and the other GPU user alone.
4. Agents: at most two at a time, types that cannot spawn agents, or general-purpose told not to; partition files.

## Guardrails

- Regression: `FLYEMU_PROFILE=m4` sugar->MN9_L 8.9 ± 5.9 Hz (10 trials) and closed loop seeds 0-2 silent; m5 closed loop seeds 0-2 silent and sugar->MN9_L 7.3 Hz.
- Stop starting new work at 4 h 40 m, then wrap up (WORKFLOW §2), including a plain-language summary for Ben.
