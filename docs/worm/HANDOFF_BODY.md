# Worm body + viewer: handoff (body worker, worktree `wormbody`)

**Rewritten each session; do not append.** State as of 2026-11-05 17:53 CST, after the viewer's agar plate, the
10 s demo loop on the plate, the `solver_exit` gate (failed) and the Catalog source table. The shared
`docs/HANDOFF.md` belongs to main; this file is the body side until the Director merges it. Main was merged into
this branch at 17:43 (brain: excitatory reversal template +0.5 mV, `muscle_active` wired but off).

Ben's direction (via the Director, 15:05-15:40):
- port open-source bodies, not our own physics; the 3D MetaWorm/BAAIWorm body only (the rod is dropped);
- port OpenWorm Sibernetic's mechanisms where they add detail;
- published values (BAAIWorm's tuned ones included) count as known, labelled "published";
- the demo world is an agar plate with a chemical gradient (BAAIWorm's chemotaxis scene).

The week's bar (WEEK.md, done Thu 12 Nov) is "complete, not behaving":
- a closed loop with every mechanism layer;
- every unknown guessed inside a cited range;
- toggles, the viewer and an MP4 on guesses;
- literature wins over ported numbers where they conflict;
- no fitting this week.

## What exists

- **Body:** the MetaWorm body ported unchanged from BAAIWorm b99ca5ab (Apache 2.0), in `third_party/metaworm`.
  - Build: `third_party/metaworm/driver/build.sh [eigen_dir]`. It rebuilds any object older than the newest `sim/` header; stale objects segfaulted once.
  - Python driver: `src/wormemu/body/metaworm.py` (`run(out, mode=wave|key|dead, ..., solver_exit=..., world=...)`, `load`, `gait`, `Frame`).
  - Credits are in `docs/worm/ADOPTED.md`; what we changed is in `third_party/metaworm/UPSTREAM.md`.
- **Agar world (toggles, neutral = the published world):** driver flags, passed as a dict `world=`.
  - `metaworm.AGAR_FILM = {scale: worm_1mm, fluid: agar_rft, substrate: agar_film}` passes its gates. Use it for the demo.
  - `body.scale = worm_1mm`: 1 mm body; mass 2.13 ug from density 1074 kg/m^3 (inside the measured 1070-1080, Reina 2013) x mesh volume.
  - `env.fluid = agar_rft`: resistive-force drag in the implicit solve, c_t 3.2 and c_n 128 Pa s (Boyle, Berri and Cohen 2012, K 40, read per length: inferred).
  - `env.substrate`: `agar_plate` = gravity onto the right side (guessed) plus a one-sided plate; `agar_film` adds the water film's surface as a second wall at the rest body's thickness (0.0601 L; form guessed; surface tension makes that force about 3000x the weight, derived).
  - Gates (BODY_TESTS.md; `scripts/worm/agar_tests.py`): A1 pass; **A2 FAIL** (the body lifts off the gravity-only plate); A1f pass; A2f pass.
  - Crawl drive on the film (report-only): a0 0.157 gives 0.10 mm/s head first (literature 0.08-0.30), wavelength 0.64 L (0.46-0.84), head curvature 7.4 /mm (8-9).
  - Cost: RTF 0.28-0.40 against 0.81 in the published world.
- **Closed loop:** `src/wormemu/body/loop.py`.
  - `Body(out, scene, frame_every, solver_exit, world)` wraps the driver's `--mode pipe`; `run(brain, body, seconds, brain_config=...)` writes `out.neural.f32` beside the frames.
  - Exchange every physics step (1/240 s); the brain's `dt_ms` runs 4.0, 4.5, 4.0; a command takes effect one exchange later (INTERFACE.md).
  - Use `Brain(sample_worm(None), toggles=dict(receptor_sign="on"))`. Seed 0 draws a near-silent muscle (4.4e-6) and drawn worms have no guardrail yet.
  - **Demo loop (`cl_film_tmpl10`, new, on merged main):** 10 s on the agar film with the diacetyl cone field, 43.8 s of wall. Max activation 0.795 (tonic co-contraction, unchanged by main's +0.5 mV reversal); the body curls into a C by 2.5 s and holds it; midline 0.66 L; creeps 0.13 L; stays on the plate. No rhythm, no crawling, no chemotaxis: the missing rhythm is the brain side's open item (BRAIN_PORT section 6).
  - Scratch script for it: `/tmp/wb_q/cl_film.py 10 runs/worm/metaworm/cl_film_tmpl10` (template brain + `AGAR_FILM` + cone field). Worth turning into `scripts/worm/` if it becomes the standard demo.
- **Solver dead zone and the `body.solver_exit` toggle.** MetaWorm's solver returns the iterate from before its converged solve, so drive at or below 0.03 does nothing (measured, 1.5 s swim wave). `latest` removes the threshold.
  - **Gate (pre-registered 17:48, run 17:48-17:50): FAIL, not adopted; `published` stays the default.**
  - S3 (dead zone gone) and S4 (A1f, A2f hold) pass. S1 and S2 fail, all in P3 in the published world: wavelength 1.59 to 0.565 L (pass to fail), head kappa*L -35%, speed +43%; P1 end/peak -13%.
  - In the agar film world the exit changes the A2f readouts by under 3%.
  - Figures: `data/worm/body_runs/solver_exit_gate.png` and `solver_exit_p3_kymo.png` (viewed).
  - Consequence for the loop: brain drive must exceed about 0.03-0.06 to move the body. The template worm's 0.79 is far above it.
- **World extension (ours, inert unless called):** `SetUnitMass`, `SetDragMatrix`, `SetReturnLatestIterate` in `sim/fem/World.*`.
- **Chemotaxis scene (MB11):** `src/wormemu/body/scene.py`. Toggles `env.chemical_field` none (neutral) | cone_published | exp_spot; `env.chemical_target` published_3d | plate_projected. Field in mm (1 mm body = `worm_1mm`). Sampled at the nose (vertex 102) and tail (vertex 173). Sources: `docs/worm/research/CHEMOTAXIS_PLATE.md`.
- **Real-time factor (measured):** published world, one thread: Mac 0.60x, backhouse 0.69x; agar film 0.28-0.40x; the brain costs about 3.6-4.4 s of wall per biological second, so the brain still sets the loop's speed.
- **Tests:** `scripts/worm/metaworm_tests.py` (P0-P3), `scripts/worm/agar_tests.py` (A1, A2, A1f, A2f, crawl; optional `latest` argument for A1f/A2f), `scripts/worm/solver_exit_gate.py`. Pre-registrations and results: `docs/worm/BODY_TESTS.md`.
  - P0 dead: pass. P1 release: fail (0.1008 vs 0.10). P2 key: moves (pass), head-frequency readout fails. P3: fails speed and frequency, passes wavelength.
  - Main finding: the published world is metre scale and inertial (Re about 7,300, against a worm's 0.1-0.5); the agar world is the literature replacement.
- **Ledger:** `scripts/worm/build_metaworm_ledger.py` writes `data/worm/ledger/` and `viewer/worm/data/`.
  - 48 body numbers (28 used by the running body in the published world), 12 mechanisms.
  - The catalog has 416 rows holding 90,160 numbers (brain rows can hold one number per cell, pair or synapse).
  - Each catalog row now carries `source_project` and `fill_kind` in the brain ledger's vocabulary; `catalog.json` has a `source_by_fill_kind` table (brain numbers from `docs/worm/ledger.json`, body rows).
  - `precision_needed` is empty because the sensitivity pass has not run.
- **Viewer:** `viewer/worm/`. Start: `.venv/bin/python viewer/worm/serve.py`, open http://127.0.0.1:8781/. Serves `viewer/worm/` only.
  - 3D body coloured by muscle activation, kymograph; for closed-loop runs, the 302 neuron voltages as a raster and on the wiring diagram.
  - **New:** worm-scale runs draw the agar plate (a 9 cm dish, display only; the rim is not a wall in the physics). With a chemical field, the plate colour is the concentration from scene.py's formulas, with contours every 1/20 of c_peak (1 mm apart for the cone) and a yellow ring at the odour peak; the camera frames the worm and the peak together. Plain plates keep the 0.25 L grid. Overlay text sits on a backdrop.
  - **New:** the Catalog tab shows the source project x fill kind table above the row list.
  - Runs loaded include `cl_film_tmpl10` (the demo), `cl_film_tmpl`, `agar_crawlf_a0.157`, `agar_a2_p3` (the failure), `cl_brain_tmpl`.
- **MP4s (gitignored, `runs/worm/media/`, contact sheets viewed):**
  - `cl_film_tmpl10.mp4`: **the week's "MP4 on guesses" in the demo world**: 10 s, template brain, agar plate with the gradient drawn. Opened for Ben 17:47.
  - `cl_film_tmpl.mp4` (5 s), `agar_crawlf_a0.157.mp4` (prescribed crawl, head first), `cl_brain_tmpl.mp4` (published world), `p3_final.mp4`, `p2.mp4`. Recorder: `scripts/worm/record_viewer_mp4.py <run> [port]`.
- **Interface:** `docs/worm/INTERFACE.md` body side is current. Nothing open between the workers.

## Next (in order)

1. When the brain side has a rhythm: re-run the 10 s demo loop and re-record the MP4 (one command each, above).
2. Optional narrower gate: `solver_exit = latest` inside the agar world only (A2f and the crawl drive under both exits, plus the dead-zone sweep at worm scale). Pre-register first; it is a separate decision from today's failed gate.
3. Water RFT (`viscous_rft_water`) swim gates, pre-registered like A1/A2 (the P3 swim bars apply).
4. Speed: `run_body_omp` with a thread count; a closed-form 3x3 polar decomposition matched on P2 first; `--drag_every` above 1 once gated.
5. Sibernetic toggles (`body.pressure`, `muscle.force_model`), each with its own pre-registration.
6. Sensitivity pass to fill `precision_needed`.

## Sealed / held-out evidence

None spent by the body. The agar crawl readouts against literature are report-only this week (Director 17:25),
not scored, and nothing was tuned to them. The gait means used so far are calibration targets named in the
pre-registrations, not held-out data.

## Running processes

- `viewer/worm/serve.py` on 127.0.0.1:8781, PID in `/tmp/wb_serve.pid` (left up so Ben can look; idle). Stop it with `kill $(cat /tmp/wb_serve.pid)`.
- Nothing else of mine is running on the Mac or backhouse. `/home/greff/worm-body/` on backhouse (27 MB) holds copied sources, builds and timing jsons (keep for re-timing).
- Scratch scripts in `/tmp/wb_q/` reproduce today's checks; everything they measured is in BODY_TESTS.md.
