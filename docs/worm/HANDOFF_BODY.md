# Worm body + viewer: handoff (body worker, worktree `wormbody`)

**Rewritten each session; do not append.** State as of 2026-11-05 16:18 CST. The shared `docs/HANDOFF.md`
belongs to main; this file is the body side until the Director merges it.

## What exists

- **Body:** the MetaWorm body ported unchanged from BAAIWorm b99ca5ab (Apache 2.0), in `third_party/metaworm`.
  Build: `third_party/metaworm/driver/build.sh`. Python driver: `src/wormemu/body/metaworm.py`
  (`run(out_dir, mode=wave|key|dead, ...)`, `load`, `Frame` midline readout). Credits: `docs/worm/ADOPTED.md`.
- **Tests:** `scripts/worm/metaworm_tests.py` -> `data/worm/body_runs/metaworm_tests.json`; pre-registration and
  results in `docs/worm/BODY_TESTS.md`. P0 dead worm pass. P1 release fail (0.1008 vs 0.10). P2 published key:
  displacement pass (1.95 L), head-frequency readout fail. P3 prescribed wave at swim means: speed fail (0.018 vs
  0.29-0.45 L/s), wavelength pass (1.59 L), frequency fail. Main finding: the published world is metre-scale
  and inertial (Re about 7,300 against a worm's 0.1-0.5; density 19x a worm if read as SI).
- **Ledger:** `data/worm/ledger/metaworm_parameters.csv` (built by `scripts/worm/build_metaworm_ledger.py`).
  42 numbers: 22 published, 8 derived, 3 measured, 2 inferred, 5 guessed, 2 absent; 13 to fill (guessed, absent,
  or a published/derived value outside the literature). `BodyLedger.load()` reads it; `sample(seed)` draws the
  guessed rows inside their ranges. Mechanisms and toggles: `metaworm_mechanisms.json` (12 mechanisms; every
  toggle neutral = the published body). `precision_needed` is empty: the sensitivity pass has not run.
  The own-rod ledger is archived in `archive/worm/rod_own/`.
- **Viewer:** `viewer/worm/` (three.js r170). Start: `.venv/bin/python viewer/worm/serve.py` then open
  http://127.0.0.1:8781/viewer/worm/. Shows the 3D body with muscle activation colour, the activation kymograph,
  the wiring diagram (302 neurons, 95 muscles; chemical, electrical, nmj, peptide, monoamine layers), the
  mechanism list with toggles, the catalog (search, label filter, "to fill only"), and a Run tab that runs new
  prescribed drives through `/api/run`. Run data: `scripts/worm/build_viewer_data.py` writes
  `viewer/worm/runs/` (gitignored). Checked in headless Chrome (screenshots viewed); the body-culling bug is fixed.
- **MP4s (gitignored):** `runs/worm/media/p3_final.mp4` (prescribed wave) and `runs/worm/media/p2.mp4` (published
  key), 10 s each at 30 fps, with contact sheets `*_sheet.png` (viewed). Recorder:
  `scripts/worm/record_viewer_mp4.py <run>` (needs serve.py running). No neural activity yet: no brain in the loop.
- **Interface:** body side written in `docs/worm/INTERFACE.md`. K = 49, muscle positions from the MetaWorm mesh,
  95 -> 96 mapping (MVL segment 23 copies vBWML23, guessed), proposed exchange 4.0 ms (dt 1/250), strain derived
  by the brain. One question open to the brain: is 4.0 ms acceptable.

## Next (in order)

1. Closed-loop driver mode: `run_body.cpp` reads 96 activations per physics step from a pipe and writes the
   49-sample midline back; Python `metaworm.py` wraps it as `Body.step(BrainToBody) -> BodyToBrain`. Test with a
   stand-in brain (the prescribed wave fed through the interface must reproduce P3) before `sample_worm` lands.
2. dt 1/250 check: re-run P2 at dt 1/250 and compare with 1/240; adopt only if the gait readouts move less than
   their run-to-run spread.
3. Literature-replacement toggles (neutral = published), each with a fresh pre-registration at 24 slices:
   `body.scale = worm_1mm` (L 1 mm, worm density), `env.fluid = viscous_rft_water` (resistive-force drag,
   implicit in the PD solve, an upstream edit behind a flag), then `env.substrate = agar_plate` with gravity and
   contact, then the BAAIWorm chemotaxis gradient (MB11).
4. Sensitivity pass to fill `precision_needed`.

## Sealed / held-out evidence

None spent by the body. Gait means used so far (swim speed, frequency, wavelength, head amplitude) are
calibration targets named in the pre-registration, not held-out data.

## Running processes

- `viewer/worm/serve.py` on 127.0.0.1:8781, PID in `/tmp/wb_serve.pid` (left up so Ben can look; idle at 0% CPU).
  Stop: `kill $(cat /tmp/wb_serve.pid)`.
