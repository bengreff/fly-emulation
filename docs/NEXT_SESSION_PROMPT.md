# Session 8 prompt: unattended, 5 hours maximum

Paste everything below the line into a fresh Claude Code session in `/Users/ben/fly-emulation`.

---

You are continuing the fly-emulation project **unattended**. Ben will not answer questions. You have Ben's standing authority to act as a creative scientific researcher and make judgement calls: reorder or substitute experiments when the evidence says so. Record every deviation and its reason; the guardrails below still hold.

## Before anything else

1. Run `date`; create `docs/SESSION8_LOG.md` with the start time. Use `date` for every timestamp; never guess the time.
2. Follow `docs/WORKFLOW.md`:
   - lifecycle; evidence labels; pre-registration;
   - fit / dev / held-out / sealed splits; the post-hoc budget of 2;
   - the unverified-foundations rule; ≥ 3 seeds; process hygiene; git.
3. Read `docs/HANDOFF.md`, `docs/PLAN_NEXT.md`, `docs/MODEL.md` (session-7 switches), `docs/RUNNING.md`, FINDINGS "# Session 7", and DECISIONS "## Session 7".
4. Run `uv run pytest tests -q`; it must pass.
5. Check backhouse: `ssh -o ConnectTimeout=8 backhouse 'wsl -d Ubuntu -- echo ok'`. If up:
   - keep a `sleep infinity` keep-alive attached;
   - run `scripts/sync_backhouse.sh`;
   - run ≤ 14 model processes at once (31 GB RAM).

   Run `score_reflex.py` on the Mac, which holds the raw cells.

## Session-specific rules

- Stop new work at 4h40m, then wrap up (WORKFLOW §2).
- **Agents:** at most one Explore subagent at a time.
- **Candidate rows:** use `FLYEMU_EXTRA_PARAMS` / `FLYEMU_PROPRIO_ASSIGNMENT`. Do not edit the live tables until a change is adopted.
- **Reflex scoring:** always pass `--kp 100 --kd 0.133`.
- **On the Mac (zsh),** expand override lists with `${=VAR}`.

## Priorities (in order)

### 1. Central-complex ring operating point (F-STAB-1)

The default ring is bistable: silent (0 Hz) at rest, and saturated (EPG ~75, PEN ~187 Hz) after a strong kick or under config T. It never holds a bump. Config T is otherwise stable (ring-silenced diagnostic), so this is the gate for the embodied work.

a. Look up measured ring physiology with one Explore agent: Turner-Evans et al. 2017 eLife, 2020 Neuron; Seelig & Jayaraman 2015. Record in `data/measurements/targets_session6.csv` with a `use` status.
b. Pre-register the criteria:
   - a local 6-EPG kick leaves a bump (≤ 1/4 EPGs active) for ≥ 200 ms;
   - a full-ring kick (`--targets EPG,PEN_ --kick-ms 200 --mv 15`) gives PEN < 50 Hz;
   - the resting PEN rate is held out: 3.9 ± 2.6 Hz.
c. Screen mechanisms (`candidates_s7_cx_*.csv` are guessed starting points). Pre-register one, fit at most one parameter on the bump criterion, and hold out the PEN rate.
d. Adopt as the default only if the regression checks pass (sugar→MN9, 3-seed stability with CX rates reported).

### 2. Re-test config T with the working ring

T = `afferent:leg_proprioceptors|rate_mode_max_hz=200`, `connection_class:leg_proprioceptor_output|efficacy_scale=10.9`, `afferent:leg_proprioceptors|transferred_depression=1`.
- Stability on 3 fresh seeds; standing on 3 seeds (≥ 0.90 mm).
- Command direction (DNg100 forward, MDN backward) on **new seeds 5–8**, **plus a gait criterion** pre-registered first (alternating tarsal stepping).
- Reflex: dev first. A sealed spare (180621 or 181127) only after a dev H1 + H2 pass, scored once; update the register.

### 3. Extension pathway

Settle claw/hook direction from data, via the Lesser et al. 2024 FANC FeCO classes and FANC↔male-cns matches (BANC `fanc_cell_type` is empty for these types; try MANC/FANC tables). Relabel the directions if evidence is found. The reflex target is over its post-hoc budget: no further fitting on 180111.

### 4. As time allows

- Per-class resting potentials from the targets table, one class at a time.
- An M0 recalibration plan.

## Wrap-up

Follow WORKFLOW §2 "End":
- rewrite HANDOFF (unverified foundations; sealed register) and PLAN_NEXT;
- write the next prompt;
- record post-hoc use per target in the log;
- end with a plain-language summary for Ben (an engineer without a neuroscience background).
