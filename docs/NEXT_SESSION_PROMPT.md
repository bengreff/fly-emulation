# Session 10 prompt: continue building the complete fly (unattended, 5 hours maximum)

Paste everything below the line into a fresh Claude Code session in `/Users/ben/fly-emulation`.

---

You are continuing the fly-emulation project **unattended**. Ben will not answer questions. You have Ben's standing authority to act as a creative scientific researcher and make judgement calls within the guardrails. Record every deviation and its reason.

## Your job

Continue the **complete fly template**, the task list in `docs/CONSTRUCTION.md`. Session 9 finished tasks 1–3 and part of 4 and 5; `docs/PLAN_NEXT.md` says exactly what remains. Work in this order:
1. finish task 4: B3 rest angles, by replicating the eLife weighted protocol in the model;
2. finish task 5: MN map for the coxa and femur-roll pools, mid/hind muscles, fatigue, a Hill-mode readout for standing.py, a standing drive and the decaying-activation dead-fly variant;
3. task 6 (adhesion);
4. task 7 (dead fly with the template body and the leg battery);
5. then onward.

Do not skip ahead or leave a task half-built. Mark a task done only when its tests pass; otherwise record exactly what remains.

Read first, in this order:
1. `CLAUDE.md`;
2. `docs/HANDOFF.md`;
3. `docs/CONSTRUCTION.md`;
4. the session 9 sections of `docs/FINDINGS.md` and `docs/DECISIONS.md`;
5. `docs/LESSONS.md`;
6. `docs/WORKFLOW.md`;
7. `docs/RUNNING.md`.

## Principles that override convenience

- **Complete before search; simulate more rather than less.** Mechanisms always on at their prior (in the template); parameters released gradually.
- **Biological bounds on every row** of `data/model/parameters.csv`, with basis and source. Never set outside them, and never widen one to rescue a fit.
- **Labels never upgrade.**
  - Mark a bound `verified` only after reading its source.
  - Figure values under different conditions (e.g. loaded equilibria) are not the quantity you want.
- **Verification first:**
  - every new probe steps the motor path through `Organism.motor_step()` and checks MuJoCo warnings;
  - a run that reproduces a previous result to every digit after a change is a red flag (F-HARNESS-2);
  - every mechanism gets a neutral-equivalence test and a test of what it claims.
- **Every body change is measured against the dead-fly test** (`scripts/dead_fly.py`).
- **Units:** mm, g, s, so torque is in µN·mm. The eLife stiffness is mN·m/° (F-PASSIVE-1); FlyMimic is in g, mm, s.

## Setup

1. Run `date`; create `docs/SESSION10_LOG.md` with the start time. Use `date` for every timestamp.
2. Run `uv run pytest tests -q`; it must pass.
3. **backhouse** (`ssh -o ConnectTimeout=8 backhouse 'wsl -d Ubuntu -- echo ok'`; unreachable all of session 9):
   - if it is up, keep one `sleep infinity` keep-alive and kill it at the end;
   - run `scripts/sync_backhouse.sh`;
   - ≤ 8 model processes at once;
   - build job lists with `scripts/mkjobs.py`;
   - leave the old PID 523 alone and report it.
4. **Agents:** at most one at a time, of a type that cannot spawn agents, for bounded literature extraction. Spot-check what it returns.

## Guardrails

- **Keep the legacy model runnable.** m4 and `FLYEMU_PROFILE=m2` must reproduce their regressions. New mechanisms enter as registry switches owned by the data model (`tests/test_model_data.py` enforces coverage).
- **Regression checks** (Mac and backhouse differ in exact values):
  - sugar→MN9_L 8.9 ± 5.9 Hz (10 trials, m4);
  - closed loop seeds 0–2: 0 non-tonic spikes (CX ring types excluded).

  Also run the template body (the three switches on) on seeds 0–2 and report any move.
- Stop starting new work at 4h40m, then wrap up (WORKFLOW §2): tests, regression, ledger (construction state per tier), stop all processes, FINDINGS/DECISIONS entries, HANDOFF rewrite, session-11 prompt, commit and push.
- End with a plain-language summary for Ben (an engineer, not a neuroscientist):
  - which tasks are done;
  - what the dead fly does compared with a real one;
  - how many mechanisms are have/partial/absent;
  - how many unknowns exist, with how many bounded by data;
  - what remains.
