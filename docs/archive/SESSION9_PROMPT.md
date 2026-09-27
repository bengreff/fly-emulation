# Session 9 prompt: build the complete fly (unattended, 5 hours maximum)

Paste everything below the line into a fresh Claude Code session in `/Users/ben/fly-emulation`.

---

You are continuing the fly-emulation project **unattended**. Ben will not answer questions. You have Ben's standing authority to act as a creative scientific researcher and make judgement calls within the guardrails. Record every deviation and its reason.

## Your job

Build the **complete fly template**, the task list in `docs/CONSTRUCTION.md`. That means:
- every mechanism that plausibly matters for behaviour, built and switched on;
- every unknown an explicit, biologically bounded parameter in one data model;
- a body that behaves as a real fly's body when the brain is dead;
- `sample_fly(seed)`, which returns a complete fly with its unknowns scrambled within their bounds.

The brain search comes after this and is not part of this session.

Work the task list in order and get as far as you can. Do not skip ahead to easier tasks or leave a task half-built. Mark a task done only when its tests pass. Otherwise record exactly what remains.

Read first, in this order:
1. `CLAUDE.md`;
2. `docs/CONSTRUCTION.md` (the plan, principles and acceptance tests);
3. `docs/LESSONS.md` (what sessions 1–8 established);
4. `docs/research/FIDELITY.md` and its two notes;
5. `docs/WORKFLOW.md`;
6. `docs/HANDOFF.md`;
7. `docs/MODEL.md` and `docs/RUNNING.md`.

## Principles that override convenience

- **Complete before search; simulate more rather than less.** If a mechanism is cheap, build it and switch it on at its prior, even where the fidelity research says it may not be needed. If it is expensive, give it an architectural slot.
- **Mechanisms always on; parameters released gradually** (`release_stage`).
- **Biological bounds:** every parameter row carries `bio_min`/`bio_max` with basis and source. Nothing is ever set outside them. Where no evidence exists, the bound is wide and labelled guessed, never absent.
- **Labels never upgrade.** Values from agent reports or abstracts are leads until a source's text or data is read. Record [verified] or [unverified].
- **Verification first.** Every mechanism gets a neutral-equivalence test and a test of what it claims. Every probe gets a correctness test before its output is read. s8 lost results to a non-local kick, a mirrored heading map and mislabelled transmitters.
- **The dead-fly test comes before body changes** (task 3), so every body change is measured against it.
- **Units:** the body is in mm, g, s, so torque is in µN·mm and a fly weighs ~10 µN. The eLife 2025 passive-stiffness table gives mN/° in the table and N·m/° in the text. Reconcile against its "70× too weak to hold the fly" statement before entering any value.

## Setup

1. Run `date`; create `docs/SESSION9_LOG.md` with the start time. Use `date` for every timestamp.
2. Run `uv run pytest tests -q`; it must pass.
3. **backhouse** (`ssh -o ConnectTimeout=8 backhouse 'wsl -d Ubuntu -- echo ok'`):
   - keep one `sleep infinity` keep-alive and kill it at the end;
   - run `scripts/sync_backhouse.sh`;
   - ≤ 8 model processes at once;
   - build job lists with `scripts/mkjobs.py` (one bash script per job; never put quoted command lines through `xargs` or `ssh "..."`);
   - leave the old `sleep infinity` PID 523 alone and report it to Ben.
4. **Agents:** at most one at a time (CLAUDE.md, unattended), of a type that cannot spawn agents. Use it for bounded literature extraction: parameter bounds, muscle and joint data, peptide receptor maps. Spot-check what it returns.
5. **Downloads:** FlyGym musculoskeletal assets, the Melis hinge code, and FlyMimic data are expected. Record each in `data/MANIFEST.yaml` with size, version and licence.

## Guardrails

- Keep the legacy model runnable: profile m4 and `FLYEMU_PROFILE=m2` must still reproduce their regressions. New mechanisms enter through the data model. Old switches become views of it and are not deleted until the replacement is tested.
- **Regression checks** (Mac and backhouse differ in exact values):
  - sugar→MN9_L 8.9 ± 5.9 Hz (10 trials, m4);
  - closed loop 0 non-tonic spikes (CX ring types excluded) on seeds 0–2.

  Report any move.
- Stop starting new work at 4h40m, then wrap up (WORKFLOW §2): tests, regression, ledger (construction state per tier), stop all processes, FINDINGS/DECISIONS entries, HANDOFF rewrite, session-10 prompt, commit and push.
- End with a plain-language summary for Ben (an engineer, not a neuroscientist):
  - which tasks are done;
  - what the dead fly does compared with a real one;
  - how many mechanisms are have/partial/absent;
  - how many unknowns exist, with how many bounded by data;
  - what remains.
