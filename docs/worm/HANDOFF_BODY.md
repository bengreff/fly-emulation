# Worm body + viewer: handoff (body worker, worktree `wormbody`)

**Rewritten each session; do not append.** State as of 2026-11-05 16:31 CST. The shared `docs/HANDOFF.md`
belongs to main; this file is the body side until the Director merges it.

Ben's direction (Director, 15:30): the 3D body only, the rod dropped entirely; the body is MetaWorm/BAAIWorm's
tetrahedral body; port OpenWorm Sibernetic's muscle and body mechanisms heavily where they add detail; first
measurement the real-time factor on the Mac and backhouse; a GPU port later.

## What exists

- **Body:** the MetaWorm body ported unchanged from BAAIWorm b99ca5ab (Apache 2.0), in `third_party/metaworm`.
  Build: `third_party/metaworm/driver/build.sh [eigen_dir]` (Mac: Homebrew Eigen 5.0.1; backhouse: the same
  headers copied to `/home/greff/worm-body/eigen/eigen3`). Run from the metaworm root (it reads `args/`). Python
  driver: `src/wormemu/body/metaworm.py` (`run(out_dir, mode=wave|key|dead, ...)`, `load`, `Frame` midline
  readout). Credits: `docs/worm/ADOPTED.md`.
- **Rod: gone from src.** `rod.py`, `muscles.py`, `drive.py`, `gait.py` and the rod ledger are in
  `archive/worm/rod_own/` (README there says how to rerun). `src/wormemu/body/` now holds only `ledger.py` and
  `metaworm.py`.
- **Real-time factor (measured, BODY_TESTS.md last section):** one thread, published key (swimming): Mac M2 Pro
  0.60x real time, backhouse i7-14700K (WSL2) 0.69x; the gentle P3 wave 0.81 / 0.94; a dead body 3.1. Results are
  identical across the two machines to 9 digits. Profile (Mac): 73% of the time is the per-tet local step, 68% of
  all time in Eigen's general 3x3 SVD; the sparse global solve 24%; drag 1%. Compiler flags: -O3 no faster;
  -O3 -march=native crashes under C++14 (Eigen alignment). Thread scaling with upstream's own commented-out
  OpenMP loop: running on backhouse (see Running processes).
- **Tests:** `scripts/worm/metaworm_tests.py` -> `data/worm/body_runs/metaworm_tests.json`; pre-registration and
  results in `docs/worm/BODY_TESTS.md`. P0 dead pass; P1 release fail (0.1008 vs 0.10); P2 published key moves
  1.95 L (pass) but the head-frequency readout fails; P3 prescribed wave fails speed (0.018 vs 0.29-0.45 L/s),
  passes wavelength (1.59 L), fails frequency. Main finding: the published world is metre scale and inertial
  (Re about 7,300 against a worm's 0.1-0.5).
- **Sibernetic survey:** `docs/worm/research/SIBERNETIC_PORT.md`. It adds four things MetaWorm lacks: internal
  pressure, a force-type muscle with a physical maximum force, gravity and agar, and validation numbers. Muscle
  layout is the same (4 x 24); it has no cuticle-versus-tissue split (its two stiffness tiers are worm against
  agar). Port plan there, each a toggle with the published body as neutral. Paper numbers still to check
  against the paper itself.
- **Ledger:** `data/worm/ledger/metaworm_parameters.csv` (built by `scripts/worm/build_metaworm_ledger.py`).
  42 numbers: 22 published, 8 derived, 3 measured, 2 inferred, 5 guessed, 2 absent; 13 to fill. `BodyLedger`
  loads it and `sample(seed)` draws the guessed rows inside their ranges. Mechanisms and toggles:
  `metaworm_mechanisms.json` (12; every toggle neutral = the published body). `precision_needed` is empty: the
  sensitivity pass has not run.
- **Viewer:** `viewer/worm/` (three.js r170). Start: `.venv/bin/python viewer/worm/serve.py`, open
  http://127.0.0.1:8781/viewer/worm/. 3D body with muscle activation colour, activation kymograph, wiring
  diagram (302 neurons, 95 muscles, 5 edge layers), mechanisms with toggles, the catalog, and a Run tab for new
  prescribed drives. Run data: `scripts/worm/build_viewer_data.py` -> `viewer/worm/runs/` (gitignored).
- **MP4s (gitignored):** `runs/worm/media/p3_final.mp4`, `runs/worm/media/p2.mp4` (10 s, 30 fps, contact
  sheets viewed). Recorder: `scripts/worm/record_viewer_mp4.py <run>`. No neural activity yet: no brain in loop.
- **Interface:** body side in `docs/worm/INTERFACE.md` (K 49, muscle positions from the mesh, 95 -> 96 map,
  proposed 4.0 ms exchange). One question open to the brain: is 4.0 ms acceptable.

## Next (in order)

1. Speed, CPU first (standing rule: a CPU reference before any GPU port): switch on upstream's OpenMP loop
   behind a build flag if the thread test shows a gain, and try a closed-form 3x3 polar decomposition in place of
   the general SVD (same maths, checked to match the published build on P2 before use). Target: at least 1x real
   time on backhouse with the brain's cost added.
2. Closed-loop driver mode: `run_body.cpp` reads 96 activations per physics step from a pipe and writes the
   49-sample midline back; `metaworm.py` wraps it as `Body.step(BrainToBody) -> BodyToBrain`. Test with a stand-in
   brain (the prescribed wave through the interface must reproduce P3).
3. dt 1/250 check (P2 at 1/250 against 1/240; adopt only if gait readouts move less than run-to-run spread).
4. Literature and Sibernetic toggles, each with a fresh pre-registration at 24 slices: `body.scale = worm_1mm`
   with `env.fluid = viscous_rft_water` (implicit in the solve), `muscle.force_model = sibernetic_force`,
   `body.pressure = volume_constraint`, then `env.substrate = agar_plate` with gravity, then the chemotaxis
   gradient (MB11). Re-time each: the RTF above is for the published configuration only.
5. Sensitivity pass to fill `precision_needed`.

## Sealed / held-out evidence

None spent by the body. Gait means used so far (swim speed, frequency, wavelength, head amplitude) are
calibration targets named in the pre-registration, not held-out data. Sibernetic's validation numbers are the
same kind of calibration targets.

## Running processes

- `viewer/worm/serve.py` on 127.0.0.1:8781, PID in `/tmp/wb_serve.pid` (left up so Ben can look; idle).
  Stop: `kill $(cat /tmp/wb_serve.pid)`.
- backhouse (WSL, user greff), all under `/home/greff/worm-body/`: `flags_both.sh` (PID in `flags_both.pid`)
  then `rtf_omp_job.sh` (PID in `rtf_omp_job.pid`), each writes a `done` file in its `rtf_*` folder. Short
  (minutes). Outputs to read: `rtf_o3n17/`, `rtf_omp/`.
