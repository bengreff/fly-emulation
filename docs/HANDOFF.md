# Handoff: current state

**Rewritten each session; do not append.** State as of the end of session 6c, 26 September 2026. History is in `docs/FINDINGS.md`, `docs/DECISIONS.md` and `docs/archive/`. The procedure is in `docs/WORKFLOW.md`, the model in `docs/MODEL.md`, the commands in `docs/RUNNING.md`.

## One paragraph

- A male-CNS connectome (167,111 neurons) drives a flybody MuJoCo fly in closed loop, with no controller.
- The body, senses and motor units are increasingly set from data:
  - morphological delays;
  - Hallem ORN rates;
  - Azevedo motor-unit forces;
  - a slow flexor MN fitted to raw recordings, and shown to transfer to a second cell;
  - leg proprioceptor identities from BANC.
- The fly **does not stand**, and its leg **resistance reflex is absent**.
- In both the leg VNC and the antennal lobe, signals of the right sign reach relay cells that sit **silent below threshold**. The cause: one brain-wide synaptic efficacy (0.165 mV), borrowed resting potentials, and no background activity. Real cells there rest partly active (graded 13Bα/10Bα; PNs at 1–5 Hz).
- **Next:** set transmission and operating points from measurements, one circuit at a time (`docs/PLAN_NEXT.md`).

## Working model

- Profile **m2**, edges ≥ 5 synapses, efficacy 0.165 mV, noise-free.
- Morphological delays on; Hallem ORN rates on; per-MN leg forces; fitted slow MNs; BANC proprioceptor subtypes.
- Runs set `motor_unit:all|force_per_spike=10` (non-leg MNs).
- Details and switches: `docs/MODEL.md`.

## Status by layer

| Layer | Status | Evidence |
|---|---|---|
| Body | mass, ranges, collisions, knee range fixed (geometry-mapped) | F-BUG-7, F-MASS-1 |
| Motor units | leg forces from Azevedo (derived); slow MN fitted, transfers to a 2nd cell | F-MOTOR-3, F-AZ-2/3 |
| Leg sensors | BANC subtypes (derived); tuning form inferred; rates guessed; silent near 90° in mV mode | F-SENSE-2 |
| Leg VNC | premotor cells silent; reflex absent on the dev cell | F-AZ-2, F-VNC-1/2 |
| AL | 70% of uPNs silent; not fixed by moving LN inhibition | F-AL-2/3 |
| Brain pathways | sugar→MN9 passes; stability holds over seeds | F-CAL-3, F-ORN-3 |
| Standing / walking | fail / no stepping | F-STAND-1, F-WALK-0 |

## Unverified foundations

Guessed or inferred items that later work depends on. Review every session (`docs/WORKFLOW.md` §4.4).

| Item | Label | What would settle it |
|---|---|---|
| Efficacy 0.165 mV for every synapse class | inferred (brain stability fit) | measured unitary PSPs per class, e.g. ORN→PN (Kazama & Wilson 2008) |
| V_rest −52 / V_th −45 mV for all non-fitted types | inferred (borrowed from Shiu 2024) | per-class recordings (Agrawal 2020 raw; others) |
| No background activity | guessed | resting-rate data for central and VNC neurons |
| Flexion vs extension tuning of claw/hook types | inferred (wiring rule + resistance prior) | functional identity in BANC/FANC papers; imaging of the types |
| Leg proprioceptor rates (2 + 8 mV × signal) | guessed | FeCO spike rates (not found for adults) |
| Slow-MN intrinsic tonic drive 36.45 mV | inferred (fitted); Azevedo says the rate is synaptically set | model tonic premotor excitation, then refit |
| Glutamate inhibitory everywhere | inferred (GluCl dominant in MNs, Lesser 2024) | per-target receptor data |
| force_per_spike = 10 for non-leg MNs | guessed | force recordings for those muscles |
| Motor-unit size scaling F ∝ V^5.1 (non-flexor leg MNs) | inferred | per-muscle force data |

## Sealed and held-out data register

| Data | Status | Rule |
|---|---|---|
| Azevedo cell 180111_F2_C1 (slow MN) | **seen** (fit and dev cell) | used for dev scoring only |
| Azevedo cell 181021_F1_C1, Piezo trials | **sealed** | open only via `scripts/score_reflex.py`, after a dev pass |
| Azevedo cell 181021_F1_C1, CurrentStep trials | seen (transfer test, passed) | none |
| Azevedo cells 180621_F1_C1, 181127_F1_C1 | downloads started by Ben on 26 Sep; **sealed spares** once unpacked | check exact size, add to MANIFEST |
| Agrawal 2020 13Bα static tuning | seen (fit target; grid fit failed) | none |
| Agrawal 2020 10Bα / 9Aα recordings | held out for VNC changes | none |
| flybench olfactory tasks 08/17/18/26/27 | held out for AL changes (m2 baseline 0.80) | none |

## Things that will bite you

- `obs["joint_angles"]` is ordered by joint DOF (102), not by actuator (98). Look joints up by name (F-BUG-6).
- Re-run `scripts/calibrate_joint_signs.py` after any body change; muscle signs depend on it.
- Recordings differ in sampling rate (10 vs 50 kHz). Read it per trial.
- Stability needs ≥ 3 seeds; one seed once hid a self-sustaining state (F-ORN-2).
- Ben's Mac overheats. Stop your processes, and never touch other projects' processes (`docs/WORKFLOW.md` §7).
- Dryad needs a login (Ben downloads). Zenodo is slow; fetch single zip members.
- Front-leg claw axons are mostly missing from male-cns (2–3 per leg). Use the T2/T3 legs for VNC comparisons.
- `runs/` and `data/cache/` are untracked and hold evidence. Do not delete them.
