# Handoff: current state

**Rewritten each session; do not append.** State as of 27 September 2026, after session 9 (construction tasks 1–5; a ~2 h session set by Ben). The plan is `docs/CONSTRUCTION.md`; carried-over results are `docs/LESSONS.md`; session 9 results are in `docs/FINDINGS.md` and `docs/DECISIONS.md`; the log is `docs/SESSION9_LOG.md`.

## Where the project stands

- **Direction** (unchanged): build the complete fly, with every unknown biologically bounded in one data model and the body validated with the brain dead. Then construct the brain by search.
- **Construction tasks:**
  - done: 1 (data model), 2 (class taxonomy), 3 (dead-fly harness);
  - partial: 4 (passive joints; leg rest angles remain), 5 (muscles; see below);
  - not started: 6–14.
- **Data model** (`data/model/`, `src/flyemu/model_data.py`):
  - 56 mechanisms (11 have, 24 partial, 21 absent);
  - 126 numeric unknowns with bounds, basis, prior, label and release stage;
  - 11,770 class rows;
  - `scripts/blank_ledger.py` prints the construction state.
  - Every registry key the m4 organism reads is owned by exactly one mechanism (tested live). `sample(seed, stage)` draws within bounds; stage 0 equals the current model.
- **Dead fly** (`src/flyemu/deadfly.py`, `scripts/dead_fly.py`):
  - current m4 body: collapses like a real fly (onset 19 ms) but pins its wings on a stop (spring reference outside the range);
  - template body (measured leg springs, folded wings): passes everything except the pending leg rest posture.
- **Template body switches.** All are 0 in m4, 1 for the template, and none adopted into the working default:
  - `joint:leg|passive_stiffness_source` (B3, measured eLife 2025, F-PASSIVE-1);
  - `joint:wing|spring_reference` (B14);
  - `muscle:leg|model` (B4/B5: antagonist Hill pairs, class twitch kinetics, saturation, NMJ facilitation).
  - With the m4 brain, the template body is stable on seeds 0–2 (pre-registered, DECISIONS). The first reading of that test bypassed Hill mode (F-HARNESS-2) and was corrected. With the muscles really on, the brain excluding ORNs runs at 0.11–0.12 Hz, below the m4 range.
- **Working model m4:** unchanged. Regressions this session (Mac): sugar→MN9_L 8.9 ± 5.9 Hz over 10 trials (identical to reference); closed loop seeds 0–2 give 0 spikes in the silent window, brain excluding ORNs 0.38/0.22/0.30 Hz. 85 tests pass.

## What remains in tasks 4 and 5

- **B3 rest angles.**
  - The eLife Figure 3C medians are loaded equilibria (weights on the tarsi), not rest angles; see F-PASSIVE-1.
  - Next: replicate the tethered, weighted protocol in the model and fit spring references to the measured equilibria. Their angle definitions (θ, φ, ψ, γ) are in the paper's methods (Eqs. 5–11); the full text is fetched via EuropePMC `PMC12324252/fullTextXML`.
  - Damping is still the flybody default (guessed).
- **B4.**
  - 20 of 84 antagonist muscles get no motor neuron under the legacy map (F-MUSCLE-1).
  - The legacy coxa assignments disagree with axis geometry: promotors go to roll, rotators to yaw.
  - Mid/hind muscle parameters are copies of the front leg (guessed); the tibia-tarsus pair is a placeholder.
  - Next: resolve MN→muscle→DOF for the coxa and femur-roll pools from the FANC/MANC atlas.
- **B5.**
  - Twitch rise/decay per class are now inferred from Azevedo 2020 (read; F-TWITCH-1).
  - Still guessed: fused rate (100 Hz), facilitation (0; bounded by the 1.6x two-spike ratio), fatigue (absent; force per spike saturates at ~10 spikes in fast/intermediate units).
  - The decaying-activation dead-fly variant (τ ≈ 100 ms from a standing drive) needs a standing drive. The Hill model can now supply one: find activations that hold the neutral pose.
- **Body physical battery (task 7):** not started.

## Unverified foundations

| Item | Label | What would settle it |
|---|---|---|
| Spring rest angles = flybody neutral pose (legs) | guessed | model replication of the eLife weighted protocol |
| DOF mapping of the eLife axes onto flybody joints | inferred (axis geometry) | the replication above; FlyMimic joint correspondence |
| Hill mode: coxa and femur-roll muscle directions | guessed | FANC/MANC MN→muscle atlas; FlyMimic moment arms on matched axes |
| Legacy MN map: promotor → coxa roll, rotators → coxa yaw | as recorded (legacy) | same |
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
