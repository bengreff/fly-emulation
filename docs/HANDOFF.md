# Handoff: current state

**Rewritten each session; do not append.** State as of 27 September 2026, after session 9 (a ~2 h session set by Ben, plus a 1 h extension with two literature subagents). The plan is `docs/CONSTRUCTION.md`; carried-over results are `docs/LESSONS.md`; session 9 results are in `docs/FINDINGS.md` and `docs/DECISIONS.md`; the log is `docs/SESSION9_LOG.md`.

## Where the project stands

- **Direction** (unchanged): build the complete fly, with every unknown biologically bounded in one data model and the body validated with the brain dead. Then construct the brain by search.
- **Construction tasks:**
  - done: 1 (data model), 2 (class taxonomy), 3 (dead-fly harness);
  - built as switches with open items: 4 (passive joints), 5 (muscles);
  - started: 6 (adhesion gate);
  - not started: 7–14.
- **Next session's order** (DECISIONS, end-of-session judgement calls): task 11's per-class background drive and synaptic strength first, then the body open items. See `docs/PLAN_NEXT.md`.
- **Data model** (`data/model/`, `src/flyemu/model_data.py`):
  - 56 mechanisms (11 have, 24 partial, 21 absent);
  - 128 numeric unknowns: 70 with a data basis (29 sources read), 58 guessed;
  - 11,770 class rows.
  - Every registry key the m4 organism reads is owned by exactly one mechanism (tested live). `sample(seed, stage)` draws within bounds; stage 0 equals m4. `scripts/blank_ledger.py` prints the construction state.
  - The ledger's "legacy m4 outside bounds" line for front/hind protraction comes from the name-mapped stiffness rows. F-PASSIVE-2 shows that mapping is wrong for coxa joints, so treat that line as stale.
- **Template body** = `model_data.TEMPLATE_SWITCHES` (all 0 in m4); use `closed_loop_check.py --template`:
  - `joint:leg|passive_stiffness_source=2`: coupled projected leg springs, J^T K J (F-PASSIVE-2);
  - `joint:leg|spring_reference=1`: rest angles fitted to the eLife weighted protocol (F-REST-2);
  - `joint:wing|spring_reference=1`: folded wings (B14);
  - `muscle:leg|model=1`: antagonist Hill pairs, class twitch kinetics, saturation; rotators mapped by action (`muscle:leg|rotator_map`, default 1 in Hill mode);
  - `adhesion:leg|detachment=1`: load/shear gate (untested in behaviour).
- **Dead fly:**
  - m4 body: falls like a real fly (onset 19 ms), but the wings are pinned on a stop.
  - Template body: passes every criterion (onset 11 ms; the posture criterion is weak, since m4 passes it too).
- **Session 9 end baseline, `closed_loop_check.py --template` (Mac):** silent-window spikes/ms seed 0/1/2 = 0.0 / 45.37 / 3.12; brain excluding ORNs 0.103 / 0.197 / 0.135 Hz; final thorax 0.57 / 0.52 / 0.60 mm. Without the adhesion gate the failing seeds were 0 and 2, so the loop is marginal and seed-dependent.
- **Brain with the template body:** unstable. Seeds 0 and 2 ignite the Mi18/DNge019/DNg12 loop (F-STAB-2). Uniform adaptation at 1 mV silences it but drops sugar→MN9 to 0.7 Hz (F-STAB-3). Adoption rule (DECISIONS): the template body becomes the default when it is silent on 3/3 seeds and sugar→MN9 > 5 Hz.
- **Working model m4:** unchanged. Regressions (Mac): sugar→MN9_L 8.9 ± 5.9 Hz over 10 trials; closed loop seeds 0–2 silent, brain excluding ORNs 0.38/0.22/0.30 Hz. 94 tests pass.

## Open items in tasks 4–6

- **B3:**
  - The middle-leg rest fit presses the assumed coxa envelopes; relabel joints.py coxa DOFs and ranges by function (F-COXA-1).
  - The front coxa yaw/roll split is not unique.
  - The gamma convention is unverified.
  - Damping is the flybody default (FlyMimic c/k 0.05 s; no measurement found).
- **B4:**
  - 30 of 84 antagonist muscles have no MN (F-MUSCLE-2): front/middle coxa yaw and ThC coxa pitch. Next: coxa muscles with moment arms on all three axes.
  - Middle/hind parameters are copies of the front leg (FlyMimic middle/hind MTUs are not public); the tibia-tarsus pair is a placeholder.
- **B5:**
  - Twitch kinetics are from Azevedo 2020 (read; F-TWITCH-1).
  - Still guessed: fused rate 100 Hz, facilitation 0 (bounded by the 1.6x two-spike ratio).
  - Fatigue is absent.
  - The standing drive and the decaying-activation dead-fly variant are not done.
- **B7:** gate thresholds guessed; stance shear/normal (~0.8) is near the peel ratio.
- **For Ben (optional, outward-facing):** raw data would replace figure-digitised or missing values: the eLife per-trial equilibrium angles (Bhandawat lab) and FlyMimic's middle/hind MTUs (Özdil / Ramdya lab).

## Unverified foundations

| Item | Label | What would settle it |
|---|---|---|
| Spring rest angles = flybody neutral pose (legs) | guessed (fit exists, not wired) | coupled stiffness first; verify left/right mirroring; the rotation axis of their body roll |
| DOF mapping of the eLife axes onto flybody joints | questioned (F-PASSIVE-2): valid for FTi only | use the J^T K J projection |
| joints.py coxa labels and range envelopes | assumed; labels contradict geometry (F-COXA-1) | measured coxa excursions mapped by function, not name |
| Hill mode: coxa and femur-roll muscle directions | guessed | FANC/MANC MN→muscle atlas; FlyMimic moment arms on matched axes |
| Legacy MN map: sternal rotators on the least-foot-motion coxa joint with an assumed sign | assumed | Cheong 2024 roles (anterior = forward swing, posterior = backward): verify the quotes, re-map by action |
| Twitch kinetics by unit class (Hill mode) | inferred from Azevedo 2020 (read) | per-class twitch recordings for non-tibia muscles |
| Spiking vs graded mode for 86,541 cells | unknown (Bernoulli priors) | per-class physiology; search + ablation |
| 62 of 126 bounds with a data basis; only 22 sources read | leads | read each source (bound_verified column) |
| Everything in `docs/LESSONS.md` labelled guessed/inferred | as recorded | see the entries |

## Sealed and held-out data register

No sealed data was opened. Two published results were used to set values (last two rows).

| Data | Status | Rule |
|---|---|---|
| Azevedo cell 180111_F2_C1 (slow MN) | **seen** (fit and dev) | dev only; the dev target is over the post-hoc budget |
| Azevedo cell 181021_F1_C1, Piezo trials | **sealed** (still unopened) | open only via `scripts/score_reflex.py` after a dev pass (H1 + H2); the scorer also refuses if the clamp misses by > 1.5° |
| Azevedo cell 181021_F1_C1, CurrentStep trials | seen (transfer test passed) | none |
| Azevedo cells 180621_F1_C1, 181127_F1_C1, Piezo trials | **sealed spares** (unpacked, sizes verified, in MANIFEST; both R35C09) | as above |
| Azevedo cells 180621 / 181127, CurrentStep trials | seen (s7 transfer test) | none |
| Agrawal 2020 13Bα static tuning | seen | none |
| Agrawal 2020 10Bα / 9Aα recordings | held out; not extracted | none |
| PN spontaneous rate | **spent** in s7 | none |
| PEN spontaneous 3.9 Hz; KC 0.1 Hz | **spent** in s8 | none |
| flybench olfactory tasks 08/17/18/26/27 | held out for AL changes (m2 baseline 0.80); not run | none |
| Command direction (MDN back, DNg100 forward) | spent on seeds 1–4 in s7 | use new seeds and a gait criterion |
| eLife 2025 passive stiffness (Table 1) and fall onset (~40 ms; OpenSim ~20 ms) | **seen** (s9: used to set B3 and as dead-fly criteria) | its rest-posture data (Fig 3C) is still unused |
| Azevedo 2020 paper text/figures on twitch kinetics (Fig 4D/E/H; slow-unit rate steps) | **seen** (s9: used to set B5 constants) | the raw recordings above keep their own status |

## Things that will bite you

- **Probes must step the motor path with `Organism.motor_step()`.** A private loop calling `Neuromuscular.step` bypasses Hill mode; it now raises under Hill mode (F-HARNESS-2). Clamp probes pass their clamp torque as `motor_step(sp, extra={actuator: torque})` (premotor_inputs, vnc_angle_tuning and azevedo_reflex are ported). `standing.py` reads legacy per-unit torque states and is legacy-only.
- **MuJoCo silently resets a diverging state.** A probe that ignores `d.warning` reads the spawn pose as a result (F-HARNESS-1). `deadfly.score()` checks it; do the same in new probes.
- **eLife stiffness units.** The values are mN·m/°; ×1e6 × 57.3 gives µN·mm/rad. Table 1's "mN/°" and the discussion's "Nm/°" are typos (F-PASSIVE-1).
- **FlyMimic** is in g, mm, s, so F0 is in µN. Its MJCF needs its meshes removed to compile (`scripts/build_leg_muscles.py`).
- **Hill mode replaces leg torques only.** Non-leg actuators keep the legacy torque path. Hill mode keeps its own motor-unit state (`HillLegDrive.units`), separate from `Neuromuscular.unit`.
- **Keys read only under a switch** (e.g. `motor_unit:leg|fused_rate`) are not in the m4 inventory. Their `parameters.csv` rows are unwired, with a note.
- **Markdown tables:** escape `|` in registry keys as `\|`.
- backhouse was unreachable all of session 9 (ssh timeout to 100.81.254.12). PID 523 (old `sleep infinity`) was not touched.
- From session 8, still true:
  - m4 vs m2 (`FLYEMU_PROFILE=m2`);
  - sugar→MN9 is marginal;
  - `warm_start.py`, not the deleted `cx_kick.py`;
  - mkjobs for backhouse;
  - probe stiffness `--kp 100 --kd 0.133`;
  - zsh `${=VAR}`;
  - ≤ 8 model processes on backhouse;
  - re-run `calibrate_joint_signs.py` after any body change that is adopted;
  - `date` is the only clock;
  - `runs/` and `data/cache/` hold evidence (untracked).
