# Handoff: current state

**Rewritten each session; do not append.** State as of the end of session 7, 26 September 2026. History is in `docs/FINDINGS.md`, `docs/DECISIONS.md` and `docs/archive/`. The procedure is in `docs/WORKFLOW.md`, the model in `docs/MODEL.md`, the commands in `docs/RUNNING.md`.

## One paragraph

- A male-CNS connectome (167,111 neurons) drives a flybody MuJoCo fly in closed loop, with no controller. **The working model is unchanged this session**; all new mechanisms are options, off by default.
- Session 7 replaced guesses with **measured synaptic physiology**:
  - the measured ORN→PN unitary EPSP is **11× the model's** brain-wide efficacy;
  - its measured depression (Nagel 2015) has the same form as the model's rule.
- Wiring these measured values into the model shows why the fly does not stand. Transferring the measured first-order synapse to leg afferents (config **T/T′**):
  - gives the first right-signed flexion reflex on dev (H1 0.80);
  - gives the best standing yet (min z up to 0.87–0.92 mm, against 0.90 needed);
  - makes the forward command DNg100 move the fly forward on 4/4 fresh seeds.
- It cannot be adopted: it trips a **bistable central-complex ring**. The default model's ring is either silent (0 Hz) or saturated (EPG 77, PEN 189 Hz), never the measured bump state (PEN ~3.9 Hz).
- With the ring's output removed, T is fully stable. **The CX ring is now the gate to the embodied milestones.**

## Working model (unchanged)

- Profile **m2**, edges ≥ 5 synapses, efficacy 0.165 mV, noise-free.
- Morphological delays on; Hallem ORN rates on; per-MN leg forces; fitted slow MNs; BANC proprioceptor subtypes.
- Runs set `motor_unit:all|force_per_spike=10` (non-leg MNs).
- Regression (start = end, bit-identical): sugar→MN9_L 26.3 / 87.3 Hz; closed loop 0 non-tonic spikes, brain 0.27–0.39 Hz.

## New options (all off; see MODEL.md "session 7 switches")

| Key | Meaning | Status |
|---|---|---|
| `connection_class:ORN_to_uPN\|efficacy_scale` | ×10.9 = measured uEPSP 6.19 mV at the median 22-synapse connection | tested, fails the PN rate criteria (F-AL-4) |
| `connection_class:ORN_to_uPN\|homeostatic_matching` | equal median uEPSP per PN (KW2008 Fig 4B) | tested, fails |
| `afferent:ORN\|measured_depression` | U 0.22, τ_rec 893 ms (Nagel 2015, hand-verified) | tested with the above |
| `connection_class:leg_proprioceptor_output\|efficacy_scale` | the ORN→PN strength transferred to leg afferents | config T / T′ (F-XFER-1) |
| `afferent:leg_proprioceptors\|transferred_depression` | Nagel depression on leg afferents | on in T, off in T′ |
| `FLYEMU_EXTRA_PARAMS=<csv>` | candidate cell-type rows, appended to `cell_types.csv` | the mechanism for testing rows without touching live tables |
| `FLYEMU_PROPRIO_ASSIGNMENT=<csv>` | candidate proprioceptor assignment table | used for the claw-swap test |

- **T** = `rate_mode_max_hz=200` + `leg_proprioceptor_output|efficacy_scale=10.9` + `transferred_depression=1`.
- **T′** = the same without depression. T′ fails stability.
- Candidate row files are `data/params/candidates_s7_*.csv`. None is live.

## Status by layer

| Layer | Status | Evidence |
|---|---|---|
| Body | mass, ranges, collisions checked; one net torque actuator per DOF (no co-contraction stiffness) | F-BUG-7, F-MASS-1 |
| Motor units | leg forces from Azevedo (derived); slow MN fitted, transfers to a 2nd cell | F-MOTOR-3, F-AZ-2/3 |
| Leg sensors | BANC subtypes (derived); claw directions inferred, favoured over their mirror on dev (H1 0.80 vs 0.10) | F-SENSE-2, s7 claw swap |
| Leg VNC | default silent; under T, the reflex is right-signed for flexion; extension excitation is 20× short because glutamatergic IN21A006 cancels it | F-XFER-1 |
| AL | measured ORN→PN strength over-drives PNs into a bimodal population; post-hoc budget spent | F-AL-4 |
| Central complex | **bistable: silent or saturated; no bump** | F-STAB-1 |
| Brain pathways | sugar→MN9 passes; stability holds over seeds (default) | F-CAL-3 |
| Standing / walking | default fails; T reaches 0.75–0.92 mm and DNg100 moves forward, but T is unstable | F-XFER-1 |

## Unverified foundations

Guessed or inferred items that later work depends on. Review every session (`docs/WORKFLOW.md` §4.4).

| Item | Label | What would settle it |
|---|---|---|
| Efficacy 0.165 mV for every synapse class | inferred (brain stability fit). **Contradicted for ORN→PN** (measured ≈ 11×) | per-class unitary PSPs; the CX ring model (F-STAB-1) |
| V_rest −52 / V_th −45 mV for all non-fitted types | inferred (borrowed). Literature now says rests of −55 to −68 mV and a KC gap of 21.5 mV (targets table) | per-class values in the targets table; apply class by class |
| Monoamines as fast excitation | **guessed and biologically wrong** (all receptors are GPCRs), but load-bearing. M0 at 0.165 is stable on 4/6 seeds; at 0.9× stable, but sugar→MN9 falls to 0.3 Hz | the neuromodulator pools must take over the monoamines' function |
| CX ring parameters (uniform) | inferred (defaults). Delta7→Delta7 626 syn/cell; PEN→PEN 420; ER ring neurons silent | measured targets: bump FWHM ~100°, persistence in darkness, PENs spike at rest; EPGs express NMDA receptors (slow excitation is a candidate) |
| No background activity; exact-rest start | guessed. s8: a warm start (noise + ramped senses) does not rescue the ring and lowers its ignition threshold (F-WARM-1) | resting-rate data; VNC tonic drive failed (it recruits inhibition) |
| Claw/hook flexion vs extension | inferred (wiring rule); supported on dev by the swap test. No publication maps it to SNpp types | FANC T1L labels (Lee et al. 2025; `data/raw/lee2025/`) joined to male-cns. CAVE token at `~/.config/flyemu/cave_token` authenticates, but FANC production returns 403 (**Ben: request FANC production access**); otherwise NBLAST bridging. VFB types MANC SNpp39 as club and SNpp41 as claw (conflict) |
| Glutamate inhibitory at leg MNs | inferred (GluCl transcripts, Lesser 2024); excitatory would help the reflex (+0.6 → +3.4 Hz) but is insufficient | electrophysiology of IN21A→MN |
| Leg proprioceptor rates (mV mode / r_max 200) | guessed | FeCO spike rates (none for adults). Depression makes static tuning pass only at low rates |
| Leg afferent strength ×10.9 (T) | inferred (cross-class transfer) | a unitary PSP at any leg afferent synapse (not found) |
| Slow-MN intrinsic drive 36.45 mV, θ 32.6 | inferred (one-cell fit). Transfers to 1 of 3 further cells. Rest rates 20–47 Hz across 4 cells; τm 15.5–16.6 ms everywhere. Azevedo (hand-verified): the rest rate is nicotinic-synaptic | per-cell distribution refit; cholinergic premotor tone |
| force_per_spike = 10 for non-leg MNs; abdomen pitch/yaw alternation | guessed. **Confounds standing**: in the video the abdomen curls up; zeroing it raises the default fly (min z +0.1–0.24 mm) but tips T over | abdominal MN force and sign data; calibrate the abdomen like the legs |
| Motor-unit size scaling F ∝ V^5.1 | inferred | per-muscle force data |

## Sealed and held-out data register

| Data | Status | Rule |
|---|---|---|
| Azevedo cell 180111_F2_C1 (slow MN) | **seen** (fit and dev) | dev only; the dev target is over the post-hoc budget |
| Azevedo cell 181021_F1_C1, Piezo trials | **sealed** (still unopened) | open only via `scripts/score_reflex.py` after a dev pass (H1 + H2); the scorer now also refuses if the clamp misses by > 1.5° |
| Azevedo cell 181021_F1_C1, CurrentStep trials | seen (transfer test passed) | none |
| Azevedo cells 180621_F1_C1, 181127_F1_C1, Piezo trials | **sealed spares** (unpacked, sizes verified, in MANIFEST; both R35C09) | as above |
| Azevedo cells 180621 / 181127, CurrentStep trials | seen (s7 transfer test: τm transfers; the point fit fails) | none |
| Agrawal 2020 13Bα static tuning | seen (fit target; also the held-out layer check in s7) | none |
| Agrawal 2020 10Bα / 9Aα recordings | held out; not extracted | none |
| PN spontaneous rate (KW2009 "1–5 Hz"; Turner 2008 4.6 ± 4.2 Hz) | **spent** in s7 (AL P/M/PR/MR/PRG/MRG) | none |
| PEN spontaneous 3.9 Hz; KC 0.1 Hz (targets table) | **spent** in s8 warm-start test (PEN fail, KC within 1 SD) | none |
| flybench olfactory tasks 08/17/18/26/27 | held out for AL changes (m2 baseline 0.80); not run | none |
| Command direction (MDN back, DNg100 forward) | spent on seeds 1–4 in s7 | use new seeds and a gait criterion next time |

## Things that will bite you

- **Probe stiffness.** Once the legs make torque, the default reflex probe (kp 3) is pushed off target. Use `--kp 100 --kd 0.133`; `score_reflex.py` refuses invalid runs.
- **zsh does not word-split `$VAR`.** Use `${=VAR}` for override lists on the Mac. bash on backhouse is fine.
- **backhouse RAM.** WSL has 31 GB and each model process ~1.4 GB, so run at most ~14 at once. `scripts/sync_backhouse.sh` now also ships `data/params`, `data/derived` and `data/measurements`; raw data stays on the Mac, so run `score_reflex.py` on the Mac.
- **`render_organism.py` was stale** (1-synapse edges, no profile, no adhesion) and is fixed. Videos: `runs/s7_video/{default,T}_seed2.mp4`; a frame comparison is in `runs/s7_video/compare.png`.
- **External input is a steady depolarisation, not a kick.** A value below 7 mV never fires a cell (cx_kick first run).
- `obs["joint_angles"]` is ordered by joint DOF (102), not by actuator (98). Look joints up by name (F-BUG-6).
- Re-run `scripts/calibrate_joint_signs.py` after any body change.
- Recordings differ in sampling rate (10 vs 50 kHz). Read it per trial.
- Stability needs ≥ 3 seeds. Single-seed behavioural anecdotes are noise: the MDN "backward walk" on seed 0 did not replicate.
- `date` is the only clock. This session's first timestamps were guessed and had to be corrected.
- Ben's Mac overheats. Stop your processes, and never touch other projects' processes.
- Front-leg claw axons are mostly missing from male-cns. Use T2/T3.
- `runs/` and `data/cache/` are untracked and hold evidence. Do not delete them.
