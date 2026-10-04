# Session 12 log

Start: Sun 4 Oct 2026 16:36 CDT. Directed by the Director (Ben's authority). Mode RESEARCH + DEVELOPMENT.
Ben's order: full set of blanks and an accurate body first (A blanks audit, B accurate body, C fidelity ladder to synapse-specific), nothing else until then. The finished rung-2 m10q search on backhouse stays uncollected. Heavy processes through `~/director/harness/slot.py`.

## Timeline

- 16:36 start; read worker rules, CLAUDE.md order, HANDOFF, FIDELITY_LADDER, goals (fly).
- 16:39 ledger baseline at 80836db: 91 quantities, 374.4 M slots, 4 INCONSISTENT rows, 8 rows with `mech: none` (runs/s12/ledger_before.txt).
- A. Blanks audit: walked the fly grain by grain; 52 new ledger rows (`audit: s12`); 14 stub mechanisms (N29-N34, B24-B27, S6-S8, D1), status absent, switches read at neutral by the organism and refused otherwise (`src/flyemu/stubs.py`, `tests/test_stubs.py`); 8 `mech: none` rows given owners; stale channel rows corrected to rung 1; glial-cell grain mapping bug fixed; 4 inconsistent receptor fills fixed.
- 16:47 ledger after: 143 quantities, 1,701.7 M slots, 0 INCONSISTENT, validation problems 0, 70 mechanisms (runs/s12/ledger_after.txt, runs/s12/blanks_audit.txt). Report: docs/BLANKS_AUDIT.md.
- 16:48 genotype note softened (no source in the repo for the male-cns strain).
- 16:50-17:00 full suite (slot limiter): 174 passed in 8 m 46 s (runs/s12/tests_full.txt). The MuJoCo "QACC at DOF 40" warning is also in every session 11 test log.
- 17:01 ledger regenerated after the genotype note; A committed.
- 17:02 Director approved A. B begins in the Director's order: wings at rest, coxa ranges, sensor assignment. Mid/hind leg muscles are to be a labelled derivation, not a copy. The FlyMimic author request goes on Ben's list, via the Director.
- 17:04 B, wings at rest: the passive body holds the wings folded (`scripts/probes/wing_rest.py`).
- 17:08-17:11 m9 seed 12, 1.5 s (`scripts/probes/wing_drive.py`):
  - the wings end pinned on their stops;
  - with wing torques zeroed they stay folded, but the left wing MNs fire tonically at 17-23 Hz.
- 17:21 Trace (`wing_premotor_trace.py`): the drive comes from SNpp30-33 wing-nerve campaniforms, driven as hind-leg load, through IN17A cells to b1, b2, iii1 and MNwm35. The wing map also had basalars on deviation, iii1 opening the wing, and DLM/DVM with direct hinge torque.
- 17:21-17:32 Switch `motor_map:wing|roles` (`data/params/wing_muscle_roles.csv`) and switch `sense:mechano|assign_by_nerve`:
  - with both switches, no wing MN is above 5 Hz;
  - at 10 µN·mm per spike, sporadic spikes still throw the wings to their stops;
  - at the declared default of 1, the wings stay folded and symmetric (peak 18°);
  - the legacy arm at 1 holds the left wing raised.
  - Contact sheets read. F-WING-2 and F-SENSE-NERVE-1 written.
- 17:33 Nerve counts: 198 of 2,482 leg afferents enter by non-leg nerves. There is no channel overlap.
  - Tests: `tests/test_wing_rest.py` 4 passed.
  - Full suite: the first run stopped on unquoted commas in my new structural_keys rows; fixed and re-running.
- 17:35 Pre-registration for adoption (DECISIONS s12): m9's silence gate on seeds 12-19 with both switches; running one seed at a time through the slot limiter.
- 17:43 Full suite: 178 passed in 9 m 9 s (`runs/s12/tests_full_B.txt`). The data-model tests were re-run after the B21 owner fix: 28 passed.
- 17:33-17:50 m9 silence gate with both switches, seeds 12-19: all 0 spikes/ms. m9w adopted as the working profile; m9 is kept.
- 17:52 Ledger regenerated: unchanged, validation problems 0.
