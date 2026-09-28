# Handoff: current state

**Rewritten each session; do not append.** State as of 27 September 2026, after session 10 (unattended, ~3 h of a 5 h budget used; Ben: "Complete the brain-body model and start on GPU porting if you have time"; three subagents, at most two at once). The plan is `docs/CONSTRUCTION.md`; carried-over results are `docs/LESSONS.md`; session 10 results are in `docs/FINDINGS.md` and `docs/DECISIONS.md`; the log is `docs/SESSION10_LOG.md`.

## Where the project stands

- **Direction** (unchanged): build the complete fly with every unknown bounded, validate the body with the brain dead, then construct the brain by search. Construction is now essentially complete at a first level; the next phase is the search.
- **Mechanisms** (`data/model/mechanisms.yaml`): 56; **17 have, 39 partial, 0 absent** (session start 11 / 24 / 21). Tier A 13/15/0, B 3/9/0, C 1/15/0. "Partial" mostly means a lumped or guessed version exists.
- **Unknowns** (`data/model/parameters.csv`): 655 rows; 79 bounds from data (29 sources read), 576 guessed; 593 wired to registry keys; released 14 / 502 / 139 at stages 0 / 1 / 2.
- **Working model: m5** (`profiles.M5`, the default) = m4 + every walking-template body/state switch (`model_data.TEMPLATE_SWITCHES`) + `class:DN|release_scale` 0.70 + `class:MN_other|input_scale` 1.30. Adopted by the pre-registered rule after a held-out test (DECISIONS s10, F-STAB-4). **m4 is frozen as the regression reference** (`FLYEMU_PROFILE=m4`).
  - m5 closed loop: silent after input removal on seeds 0-11 (exact coupling); brain excl. ORNs ~0.09-0.15 Hz; sugar->MN9_L 7.3 Hz (100 Hz), 96.4 Hz (200 Hz); bitter suppresses it fully; water->MN9 0 Hz (as in m4).
  - Margin is narrow: DN release 0.72 fails; a 1 ms sample-and-hold of the senses breaks silence on 5/12 seeds (F-STAB-5); realistic pure latency does not (6/6 silent).
  - Everything else built this session sits at its neutral value in m5 (see FINDINGS F-CONSTRUCT-1); principle 2 ("always on at prior") is not yet met for them.
- **Template dead fly** (`scripts/dead_fly.py --template`): passes every criterion (collapse onset 11 ms, no joint at a limit, wings/head/abdomen at rest, energy decays). Timestep convergence passes (B23).
- **Flight configuration** (not in m5): `flight:wings|generator` (needs 0.05 ms), `aero:wing|membrane_only` with Kutta lift 3.1 (inferred): tethered hover lift 0.99 of weight with exact kinematics, 0.89 with the PD-driven generator.
- **GPU** (`src/flyemu/gpu/`, backhouse `.venv-gpu`): the batched brain reproduces `lif.Network` spike for spike on the whole CNS; 0.37-0.45 s wall per simulated second per member at B = 32-64 (CPU 11-39 s). `scripts/gpu_assay.py` runs brain-only assays for many parameter sets (810 trials in 6 min, equal to the CPU search values). `scripts/gpu_closed_loop.py` runs B organisms (brain on GPU, bodies in worker processes): equal to the CPU loop with the same k-step hold; B = 12, k = 10: 10 s wall per member-second (7x CPU). k = 1 throughput: see the log (run launched at the end).

## Regressions (backhouse, session 10 end)

- m4: sugar->MN9_L 8.9 ± 5.9 Hz (10 trials); closed loop seeds 0-2 silent, brain excl. ORNs 0.349 / 0.223 / 0.297 Hz; m2 seed 0 silent.
- Tests: 145 passed (full suite, ~8 min) before the last few additions; the final full run is recorded in the log.

## Open items (carried)

- **B3/B4:** coxa DOF labels and envelopes by function, then the rest refit (F-COXA-1); mid/hind muscle parameters are copies; the 12 mid/hind promotors have no MN (male-cns has promotor MNs on the front legs only); leg damping unmeasured.
- **B5:** fused rate and facilitation guessed; fatigue built (guessed); standing drive and the decaying-activation fall test not done.
- **B7:** gate thresholds guessed; untested in stance/swing.
- **Flight:** fluid coefficients fitted to one condition; body pitch untuned; b1 locks at vector strength ~0.55, not one spike per cycle; the wing campaniform proxy reads deviation (roll), not stroke (yaw).
- **Brain:** m5 carries two searched class values only; N19 receptor maps inert; peptide receptor tables minimal; eLN->PN gap junctions absent (types unidentified); N2 V_rest/reset/refractory per class not yet.
- **State:** organ and clock parameters mostly guessed; the ingestion path through the organism was not exercised (the proboscis never touched food in the tests).
- **For Ben (optional, outward-facing):** raw data requests remain as in session 9 (eLife per-trial angles; FlyMimic mid/hind MTUs).

## Unverified foundations

| Item | Label | What would settle it |
|---|---|---|
| m5 class values (DN release 0.70, MN_other input 1.30) | inferred (search) | a broader search with margins; more held-out behaviours |
| Spring rest angles (fitted) and coxa labels | inferred / assumed (F-COXA-1) | coxa DOFs by function, refit |
| Coxa moment arms (front leg derived; mid/hind copied) | derived / guessed | FlyMimic mid/hind MTUs |
| Wing kinematics and Kutta lift 3.1 | guessed / inferred | measured hover kinematics; lift vs a blade-element model |
| Steering map coefficients (B11) | guessed | Melis et al. 2024 hinge model or data |
| Internal-state couplings (ISN, IPC, clock, dFB types) | inferred / guessed | per-population physiology |
| Haltere afferent identity SNpp25/SNpp34 (census) | inferred | haltere nerve labels (FANC/BANC) |
| Spiking vs graded mode for 2,969 unknown types | Bernoulli priors | per-class physiology |
| Everything in LESSONS labelled guessed/inferred | as recorded | see entries |

## Sealed and held-out data register

No sealed data was opened. Used this session as held out (now spent for the m5 candidate): template seeds 3-8, m4-body seeds 0-5 with the candidate, bitter->MN9, sugar+bitter suppression, sugar dose response at 200 Hz, water->MN9 (fails in m4 too).

| Data | Status | Rule |
|---|---|---|
| Azevedo cell 180111_F2_C1 (slow MN) | seen (fit and dev) | dev only |
| Azevedo cell 181021_F1_C1, Piezo trials | **sealed** (unopened) | open only via `scripts/score_reflex.py` after a dev pass |
| Azevedo cells 180621_F1_C1, 181127_F1_C1, Piezo trials | **sealed spares** | as above |
| Azevedo CurrentStep trials (181021, 180621, 181127) | seen | none |
| Agrawal 2020 13Bα static tuning | seen | none |
| Agrawal 2020 10Bα / 9Aα recordings | held out; not extracted | none |
| PN spontaneous rate; PEN 3.9 Hz; KC 0.1 Hz | spent | none |
| flybench olfactory tasks 08/17/18/26/27 | held out for AL changes (m2 baseline 0.80); not run | m5 changes no AL class, but check before use |
| Command direction (MDN back, DNg100 forward) | spent on seeds 1-4 (s7) | new seeds and a gait criterion |
| eLife 2025 passive stiffness, fall onset | seen (s9) | rest-posture data (Fig 3C) unused |
| Azevedo 2020 twitch-kinetics text/figures | seen (s9) | raw recordings keep their status |
| Session 10 search fit set: template seeds 0-2, sugar->MN9 100 Hz | seen (fit) | none |
| Session 10 held out: template seeds 3-8, m4 body seeds 0-5, bitter, sugar+bitter, sugar 200 Hz | spent (m5 candidate) | new candidates need new held-out evidence |

## Things that will bite you

- **The default profile is now m5.** Regression commands need `FLYEMU_PROFILE=m4`. `standing.py` reads legacy per-unit torque states and fails under Hill mode: run it with m4. `scripts/model_keys.py` always dumps the m4 inventory.
- **Probes must step the motor path with `Organism.motor_step()`** and check `d.warning` (F-HARNESS-1/2).
- **closed_loop_check's "tonic" exclusion** uses per-type spontaneous drive; a sampled global drive makes every cell tonic (F-SAMPLE-1). Class tonic drive is counted as network activity.
- **GPU:** `.venv-gpu` sees the main venv through a `.pth`; XLA prints out-of-memory retries at start (shared GPU) and continues; runs are not bitwise reproducible in busy regimes; plasticity mechanisms (N21-N24, N27 glia, conductance, presynaptic inhibition) are refused, not ported; k > 1 in the closed loop is an approximation.
- **Flight needs a 0.05 ms step** (FlightMotor raises otherwise); halteres and wings are PD-imposed at 3 kHz bandwidth (5 kHz diverges).
- **parameters.csv:** append rows or rewrite with pandas `dtype=str, keep_default_na=False`; `build_class_params.py` rewrites the class rows (n2c_/n3c_/n5c_) and keeps the others. Retired placeholders are in `data/params/retired_placeholder_rows_s10.csv`.
- **backhouse** dropped ssh twice around 22:50 (connection reset); a sync can fail silently inside a compound command: check `synced` before launching jobs.
- From earlier sessions, still true: eLife stiffness units mN·m/° (F-PASSIVE-1); FlyMimic in g, mm, s; Hill mode replaces leg torques only; `date` is the only clock; `runs/` and `data/cache/` hold evidence (untracked); ≤ 8 model processes on backhouse; re-run `calibrate_joint_signs.py` after an adopted body change (not re-run for m5; the signs should depend on joint geometry, not on the springs m5 changes, but that is unverified).
