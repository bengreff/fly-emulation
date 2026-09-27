# Handoff: current state

**Rewritten each session; do not append.** State as of the end of session 8 (attended), 26 September 2026. History is in `docs/FINDINGS.md`, `docs/DECISIONS.md` and `docs/archive/`. The procedure is in `docs/WORKFLOW.md`, the model in `docs/MODEL.md`, the commands in `docs/RUNNING.md`.

## One paragraph

- A male-CNS connectome (167,111 neurons) drives a flybody MuJoCo fly in closed loop, with no controller.
- **The working model changed this session: profile m4** (m3 = curated transmitters + recalibrated efficacy; m4 = m3 + monoamines without fast sign).
  - Transmitter identity now comes from the curated `consensusNt`. The EM classifier had labelled every Kenyon cell dopaminergic and wired ~3.3k GABA/glutamate cells as excitatory.
  - Efficacy was recalibrated to 0.15675 mV by a closed-loop rule (v3).
  - `FLYEMU_PROFILE=m2` reproduces sessions 5–8.
- **Blanks filled from data:**
  - transcript-based receptor calls for 69 types (Davis 2020), including EPG and Delta7;
  - glutamate sign for 51 types (receptor balance; Davis 2020 + Turner-Evans 2020);
  - inferred delays for 10,809 untyped cells.
- **Inference algorithm result:** wiring cannot predict sign-critical receptors (leave-one-type-out at chance).
- **CX ring:**
  - starting the fly from a living state instead of "brain death" does not fix it (F-WARM-1);
  - the NMDA lead was withdrawn;
  - my first EPG heading map was wrong (L/R glomeruli run opposite ways round the ring). Headings are now inferred from connectivity, and all earlier s8 bump-position results are unreliable;
  - Delta7's glutamate input is GluCl-dominated in two datasets, so the model's inhibitory Delta7→Delta7 is supported.
- **m3/m4 consequences:** M0 (monoamines without fast sign) now passes and is adopted (m4). Config T stands on 2/3 seeds and is blocked only by the ring.

## Working model (m4)

- Profile **m4** = m2 + `connectome:all|nt_source_consensus=1` + efficacy 0.15675 mV + `transmitter:{dopamine,serotonin,octopamine}|sign=0`. Edges ≥ 5 synapses, noise-free.
- Morphological delays (typed: skeleton; untyped: inferred); Hallem ORN rates; per-MN leg forces; fitted slow MNs; BANC proprioceptor subtypes; transcript-based glutamate sign rows (51 types).
- Runs set `motor_unit:all|force_per_spike=10` (non-leg MNs).
- Regression (end of s8, m4): sugar→MN9_L **8.9 ± 5.9 / 96.0 Hz** over 10 trials (marginal; > 5 required); closed loop seeds 0–2: 0 non-tonic spikes, brain excluding ORNs 0.22–0.38 Hz. Exact values differ between the Mac and backhouse (float order; each reproducible).

## Options (off unless stated)

| Key | Meaning | Status |
|---|---|---|
| `connectome:all\|nt_source_consensus` | consensusNt transmitters | **on in m3** |
| `cell_type:untyped\|inferred_conduction_delay` | inferred untyped-cell delays | **on** |
| `cell_type:all\|background_noise` + `scripts/probes/warm_start.py` | warm start (noise, ramped senses) | tested, does not rescue the ring (F-WARM-1) |
| `candidates_s8_d7_glu_pos.csv` | Delta7 glutamate input excitatory | not supported by receptor levels; its bump results were read with the wrong heading map |
| `candidates_s8_ring_norm*.csv` | per-cell total ring input normalisation | no effect |
| `cell_type:cx_ring\|class_input_normalisation` | per-class ring input normalisation (inferred homeostasis) | screened in s8 (see DECISIONS) |
| s7 options (ORN→PN ×10.9, depression, leg afferent ×10.9 = config T) | see MODEL.md | unchanged |
| `FLYEMU_EXTRA_PARAMS`, `FLYEMU_PROPRIO_ASSIGNMENT`, `FLYEMU_PROFILE` | candidate rows / assignment / profile | mechanisms |

- **T** = `rate_mode_max_hz=200` + `leg_proprioceptor_output|efficacy_scale=10.9` + `transferred_depression=1`.

## Status by layer

| Layer | Status | Evidence |
|---|---|---|
| Body | mass, ranges, collisions checked; one net torque actuator per DOF | F-BUG-7, F-MASS-1 |
| Motor units | leg forces from Azevedo (derived); slow MN fitted | F-MOTOR-3, F-AZ-2/3/4 |
| Leg sensors | BANC subtypes (derived); claw directions inferred | F-SENSE-2 |
| Leg VNC | default silent; under T right-signed flexion reflex; extension cancelled by glutamatergic IN21A006 | F-XFER-1 |
| AL | measured ORN→PN strength over-drives PNs; budget spent | F-AL-4 |
| Transmitters / receptors | consensusNt (m3); receptor calls for 69 types; glutamate sign for 20 | F-NT-1, F-RCPT-1 |
| Central complex | default silent; T saturates. s8 bump-position results before the heading correction are unreliable; Delta7 +1 is unsupported by receptor levels | F-CX-1, F-WARM-1, DECISIONS s8 |
| Brain pathways | sugar→MN9 passes, marginally, under m3 | DECISIONS s8 rule v3 |
| Standing / walking | m3: default fails (0.59–0.68 mm); **T stands on 2/3 seeds (1.03, 0.97 mm)** but is unstable only through the ring | DECISIONS s8 |

## Unverified foundations

Guessed or inferred items that later work depends on. Review every session (`docs/WORKFLOW.md` §4.4).

| Item | Label | What would settle it |
|---|---|---|
| Efficacy 0.15675 mV for every synapse class (m3) | inferred (closed-loop stability fit, rule v3; 3 seeds, non-monotonic in scale). **Contradicted for ORN→PN** (measured ≈ 11×) | per-class unitary PSPs; more seeds; the CX ring model |
| V_rest −52 / V_th −45 mV for all non-fitted types | inferred (borrowed). Literature now says rests of −55 to −68 mV and a KC gap of 21.5 mV (targets table) | per-class values in the targets table; apply class by class |
| Monoamines without fast sign (m4) | inferred (GPCR-only receptors); passed M0 under m3. Their action now rests entirely on the neuromodulator pools, which are inert (sensitivities 0) | per-type receptor data (transcripts, F-RCPT-1) to set pool sensitivities | the neuromodulator pools must take over the monoamines' function |
| CX ring parameters (uniform counts); ring headings | inferred. Delta7, EPG, PEN_b, PEG are GluCl-dominated (Davis + Turner-Evans), so Delta7→Delta7 inhibition is supported. EPG headings are inferred from connectivity (`infer_epg_heading.py`; L/R glomeruli run opposite ways). NMDA lead withdrawn | ring synaptic physiology; ER ring-neuron activity |
| No background activity; exact-rest start | guessed. s8: a warm start (noise + ramped senses) does not rescue the ring and lowers its ignition threshold (F-WARM-1) | resting-rate data; VNC tonic drive failed (it recruits inhibition) |
| Claw/hook flexion vs extension | inferred (wiring rule); supported on dev by the swap test. No publication maps it to SNpp types | FANC T1L labels (Lee et al. 2025; `data/raw/lee2025/`) joined to male-cns. CAVE token at `~/.config/flyemu/cave_token` authenticates, but FANC production returns 403 (**Ben: request FANC production access**); otherwise NBLAST bridging. VFB types MANC SNpp39 as club and SNpp41 as claw (conflict) |
| Glutamate sign per target (all but 20 types) | guessed −1 (GluCl). Transcripts: 18 types GluCl-only, Dm9/T1 iGluR-only (rows live), 36 types mixed; wiring cannot predict it (F-RCPT-1) | transcriptomes matched to connectome types (FCA, T2 snRNA-seq) |
| Transmitter identity | derived: consensusNt (m3). predictedNt was wrong for all KCs and ~3.3k GABA/Glu cells (F-NT-1) | 62/68 types agree with transcripts; Lai and T1 disagree |
| Untyped-cell delays | inferred (F-DELAY-2; CV error 0.14 ms) | skeletons for untyped cells |
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

- **The working profile is m4 now.** Numbers from sessions 5–8 were m2; compare like with like (`FLYEMU_PROFILE=m2`). Exact regression numbers differ between the Mac and backhouse.
- **Sugar→MN9 is marginal under m4** (8.9 ± 5.9 Hz at 100 Hz; single trials below 5). Report any change that takes it below 5 Hz.
- **s7's `cx_kick.py` "local" kick was not local** (the first N EPGs in table order). Use `warm_start.py` (heading from the PB glomerulus; `--heading`).
- **The blank ledger does not see per-type rows** (it reads static labels from `data/ontology/fly_information.yaml`), so s8 fills don't move its totals. It needs to count `cell_types.csv` rows.
- **backhouse via ssh → cmd.exe mangles `|` and nested quotes.** Put jobs in a file and run `xargs -L 1 env < jobs` in tmux, or use a runner script.
- **Probe stiffness.** Once the legs make torque, the default reflex probe (kp 3) is pushed off target. Use `--kp 100 --kd 0.133`; `score_reflex.py` refuses invalid runs.
- **zsh does not word-split `$VAR`.** Use `${=VAR}` for override lists on the Mac. bash on backhouse is fine.
- **backhouse RAM.** WSL has 31 GB and each model process peaks at ~2.6–3.2 GB RSS (measured s8; the old ~1.4 GB figure was stale, not caused by any one change), so run at most ~8 at once (12 thrashed in s8). `scripts/sync_backhouse.sh` now also ships `data/params`, `data/derived` and `data/measurements`; raw data stays on the Mac, so run `score_reflex.py` on the Mac.
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
