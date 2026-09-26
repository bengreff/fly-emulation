# Session 9 prompt: unattended, 5 hours maximum

Paste everything below the line into a fresh Claude Code session in `/Users/ben/fly-emulation`.

---

You are continuing the fly-emulation project **unattended**. Ben will not answer questions. You have Ben's standing authority to act as a creative scientific researcher and make judgement calls: reorder or substitute experiments when the evidence says so. Record every deviation and its reason; the guardrails below still hold.

## Before anything else

1. Run `date`; create `docs/SESSION9_LOG.md` with the start time. Use `date` for every timestamp; never guess the time.
2. Follow `docs/WORKFLOW.md`:
   - lifecycle; evidence labels; pre-registration;
   - fit / dev / held-out / sealed splits; the post-hoc budget of 2;
   - the unverified-foundations rule; ≥ 3 seeds; process hygiene; git.
3. Read `docs/HANDOFF.md`, `docs/PLAN_NEXT.md`, `docs/MODEL.md` (session-7 switches), `docs/RUNNING.md`, FINDINGS "# Session 8", and DECISIONS "## Session 8".
4. Run `uv run pytest tests -q`; it must pass.
5. Check backhouse: `ssh -o ConnectTimeout=8 backhouse 'wsl -d Ubuntu -- echo ok'`. If up:
   - keep a `sleep infinity` keep-alive attached;
   - run `scripts/sync_backhouse.sh`;
   - run ≤ 14 model processes at once (31 GB RAM).

   Run `score_reflex.py` on the Mac, which holds the raw cells.

## Session-specific rules

- Stop new work at 4h40m, then wrap up (WORKFLOW §2). Ben prefers stopping at a natural end over starting multi-hour items that cannot finish.
- **Stability criterion (Ben's decision, DECISIONS s7):** CX ring types (declare the list in the pre-registration) are scored by the bump test, not by "0 spikes after silencing". Every other cell must still go quiet.
- **Agents:** at most one Explore subagent at a time.
- **Candidate rows:** use `FLYEMU_EXTRA_PARAMS` / `FLYEMU_PROPRIO_ASSIGNMENT`. Do not edit the live tables until a change is adopted.
- **Reflex scoring:** always pass `--kp 100 --kd 0.133`.
- **On the Mac (zsh),** expand override lists with `${=VAR}`.

## Priorities (in order)

Work the ranked list in `docs/PLAN_NEXT.md` ("Ranked next steps"). In short:

1. **CX ring: movable bump.** Read the s8 bump-move result in DECISIONS first. Pre-register any adoption on fresh seeds; the ring's criteria are Ben's bump test, plus "the bump follows the kick".
2. **m3 consequences:** redo M0 under m3; re-test T under m3 (standing, stability, command direction on fresh seeds with a gait criterion); run more trials of the marginal sugar pathway.
3. **Filling blanks** (Ben's main task): transcriptomes matched to connectome types, used for receptor signs and kinetics. Wiring alone cannot infer them (F-RCPT-1). Make the ledger count per-type rows.
4. As time allows: extension pathway; per-class operating points; abdomen/wing calibration.

The working profile is **m3** (`FLYEMU_PROFILE=m2` for the old model). Sugar→MN9 is marginal (6.3 Hz); report any change that takes it below 5 Hz.

## Wrap-up

Follow WORKFLOW §2 "End":
- rewrite HANDOFF (unverified foundations; sealed register) and PLAN_NEXT;
- write the next prompt;
- record post-hoc use per target in the log;
- end with a plain-language summary for Ben (an engineer without a neuroscience background).
