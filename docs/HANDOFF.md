# Handoff: current state

**Rewritten each session; do not append.** State as of 27 September 2026, after session 8 and the pivot to the construction programme. The plan is `docs/CONSTRUCTION.md`; carried-over results are `docs/LESSONS.md`; the procedure is `docs/WORKFLOW.md`; the model is `docs/MODEL.md`; commands are `docs/RUNNING.md`.

## Where the project stands

- **Direction.** Build the complete fly: every mechanism that plausibly matters, always on; every unknown an explicit, biologically bounded parameter in one data model; the body validated with the brain dead. Then construct the brain by search against physiology and judge it on held-out data. Session 9 builds the template (task list in CONSTRUCTION.md). The search comes after.
- **Working model m4:** male-cns, edges ≥ 5 synapses, per-type LIF point neurons, curated transmitters (consensusNt), efficacy 0.15675 mV, monoamines without fast sign, 54 transcript-based glutamate sign rows, morphological and inferred delays, flybody with per-DOF torque actuators. Reproducible with `FLYEMU_PROFILE=m4` (m2 for sessions 5–8).
- **Regression (m4):** sugar→MN9_L 8.9 ± 5.9 / 96 Hz over 10 trials (marginal; > 5 Hz required); closed loop seeds 0–2: 0 non-tonic spikes; brain excluding ORNs 0.22–0.38 Hz. Exact values differ between the Mac and backhouse.
- **Template status** (CONSTRUCTION.md inventory): 56 mechanisms, about 10 in place, 25 partial, 21 absent.
  - **Body:** the body with a working brain is not yet a fly. The non-leg joints are pinned by guessed torque (wings at a range limit 82% of the time). Legs have one net torque per DOF, no antagonist muscles, and guessed passive mechanics (1 µN·mm/rad).
  - **Brain:** one global synaptic strength; borrowed shared V_rest/threshold; no background drive.
- **Data available and not yet used:**
  - measured passive leg torques and rest posture from MN silencing (eLife 2025);
  - FlyMimic Hill-type leg muscles (CC-BY, in FlyGym);
  - the wing-hinge model code (Melis 2024);
  - the flybody wing-pattern generator.

  URLs are in CONSTRUCTION.md.

## Unverified foundations

Every guessed or inferred item later work depends on moves into the parameter table of the new data model, with bounds and a basis (CONSTRUCTION.md, task 1). Until then, the per-item evidence is in `docs/LESSONS.md` and the unverified-foundations table in `docs/archive/HANDOFF_s8.md`.

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
- **s7's `cx_kick.py` "local" kick was not local** (the first N EPGs in table order). It has been deleted. Use `warm_start.py` (EPG heading inferred from connectivity; 12-nearest-cell kick).
- **The ledger counts per-type fills** via `fills:` entries in the ontology; CONSTRUCTION.md task 14 makes it report the construction state.
- **backhouse via ssh → cmd.exe mangles `|` and nested quotes.** Use `scripts/mkjobs.py` (one bash script per job, BLAS pinned to one thread) and launch with `xargs -P 8 -n 1 bash` in tmux.
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
