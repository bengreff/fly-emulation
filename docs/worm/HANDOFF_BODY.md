# Worm body + viewer: handoff (body worker, worktree `wormbody`)

**Rewritten each session; do not append.** State as of 2026-11-05 17:38 CST, after the agar plate and agar film
gates and the first closed loop on the plate. The shared `docs/HANDOFF.md` belongs to main; this file is the body
side until the Director merges it.

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
- **Agar world (new today, toggles, neutral = the published world):** driver flags, passed as a dict `world=`.
  - `metaworm.AGAR_FILM = {scale: worm_1mm, fluid: agar_rft, substrate: agar_film}` is the one that passes its gates. Use it for the demo.
  - `body.scale = worm_1mm`: 1 mm body; mass 2.13 ug from density 1074 kg/m^3 (inside the measured 1070-1080, Reina 2013) x mesh volume; the mass unit keeps stress and drag per length numerically SI.
  - `env.fluid = agar_rft`: resistive-force drag in the implicit solve, c_t 3.2 and c_n 128 Pa s (Boyle, Berri and Cohen 2012, K 40, read per length: inferred). Stable at the published step. `viscous_rft_water` is built but not scored.
  - `env.substrate`: `agar_plate` = gravity onto the right side (guessed) plus a one-sided plate. `agar_film` adds the water film's surface as a second wall at the rest body's thickness (0.0601 L): the meniscus treated as a hard wall (form guessed; surface tension makes that force about 3000x the weight, derived).
  - Gates (pre-registered 17:20 and 17:30, BODY_TESTS.md; script `scripts/worm/agar_tests.py`):
    - A1 dead body settles: PASS;
    - **A2 P3 on the plate: FAIL**. The body pitches up out of the plate plane and its head lifts 1.3 L in 5 s. The published body's swim path is not planar (P2 pitches 55 deg too), and gravity is about 1000x weaker than the elastic forces;
    - A1f: PASS, frames bit-identical to A1;
    - A2f P3 on the film: PASS (bounded, midline 0.88-1.00 L, never above the film).
  - Crawl drive on the film (report-only, nothing fitted; the drive sets frequency and wavelength):
    - a0 0.157: 0.10 mm/s head first (literature 0.08-0.30); wavelength 0.64 L (0.46-0.84); head curvature 7.4 /mm (8-9);
    - a0 1.0: 0.06 mm/s; 25 /mm; the body shortens to 0.61 L.
  - Cost: RTF 0.28-0.40 against 0.81 in the published world; one drag refactorisation takes 4.6 ms; `--drag_every 8` gives RTF 0.58 and changes speed by 3.6%.
  - P0 and P2 frames are bit-identical with the defaults (rechecked 17:31).
- **Closed loop:** `src/wormemu/body/loop.py`.
  - `Body(out, scene, frame_every, solver_exit, world)` wraps the driver's `--mode pipe`. Each exchange sends 96 activations and returns the vertex positions.
  - `run(brain, body, seconds, brain_config=...)` steps brain and body in parallel processes and writes `out.neural.f32` beside the frames.
  - Exchange: every physics step (1/240 s). The brain's `dt_ms` runs 4.0, 4.5, 4.0, repeating; a command takes effect one exchange later (INTERFACE.md).
  - Stand-ins (`WaveStandIn`, `ReflexStandIn`) are guessed test controllers, not worm models.
  - Use `Brain(sample_worm(None), toggles=dict(receptor_sign="on"))` (the brain worker's advice). Seed 0 draws a near-silent muscle (activation 4.4e-6), and drawn worms have no guardrail yet.
  - Template loop, published world (`cl_brain_tmpl`, 5 s, 19.5 s of wall): activation 0.79, 39-42 of 95 muscle cells tonic, the body curls, no rhythm.
  - **Template loop on the agar film (`cl_film_tmpl`, new):** 5 s, 21.1 s of wall, chemical cone field on. The same tonic co-contraction (0.79); the body curls into a C within about 1.2 s and holds it on the plate; the midline shortens to 0.67 L; drift 0.05 L; no rhythm. The missing rhythm is on the brain side (BRAIN_PORT section 6).
- **Solver dead zone (measured).** MetaWorm's solver returns the iterate from before its converged solve, so a body at rest ignores drive below about 0.05.
  - Toggle `body.solver_exit`, neutral `published`; `latest` removes the dead zone.
  - P2 gait stays within 5% under `latest`; on the agar plate `latest` changes speed by 7%.
  - Not adopted; it needs its gate (next item 2).
- **World extension (ours, inert unless called):** `SetUnitMass`, `SetDragMatrix`, `SetReturnLatestIterate` in `sim/fem/World.*`.
- **Chemotaxis scene (MB11):** `src/wormemu/body/scene.py`.
  - Toggles: `env.chemical_field` none (neutral) | cone_published | exp_spot; `env.chemical_target` published_3d | plate_projected.
  - The field is in mm assuming a 1 mm body, which is exactly `worm_1mm`'s scale. It is sampled at the nose (vertex 102) and the tail (vertex 173).
  - Sources: `docs/worm/research/CHEMOTAXIS_PLATE.md`.
- **Real-time factor (measured, BODY_TESTS.md):**
  - published world, one thread: Mac 0.60x, backhouse 0.69x; OpenMP at 8 threads reaches 1.0x on backhouse;
  - agar film: 0.28-0.40x;
  - the brain costs about 3.6-4 s of wall per biological second, so the brain still sets the loop's speed.
- **Tests:** `scripts/worm/metaworm_tests.py` (P0-P3) and `scripts/worm/agar_tests.py` (A1, A2, A1f, A2f, crawl). Pre-registrations and results are in `docs/worm/BODY_TESTS.md`.
  - P0 dead: pass. P1 release: fail (0.1008 vs 0.10). P2 key: moves (pass), but the head-frequency readout fails. P3: fails speed and frequency, passes wavelength.
  - Main finding: the published world is metre scale and inertial (Re about 7,300, against a worm's 0.1-0.5); the agar world above is the literature replacement.
- **Ledger:** `scripts/worm/build_metaworm_ledger.py` writes `data/worm/ledger/` and `viewer/worm/data/`.
  - 48 body numbers (28 used by the running body in the published world) and 12 mechanisms.
  - New rows: worm length, density and mass (MB4); side down, plate contact, film surface and surface tension (MB6).
  - MB4-MB6 switches now list `worm_1mm`, both RFT fluids and both substrates as available; MB6 is partial.
  - The catalog has 414 rows (body plus the brain worker's).
  - `precision_needed` is empty because the sensitivity pass has not run.
- **Viewer:** `viewer/worm/`. Start: `.venv/bin/python viewer/worm/serve.py`, open http://127.0.0.1:8781/. It serves `viewer/worm/` only.
  - 3D body coloured by muscle activation, with a kymograph; for closed-loop runs, a raster of the 302 neuron voltages and the wiring diagram coloured by voltage.
  - Also: mechanisms with toggles, the catalog, and a Run tab.
  - Runs loaded: `cl_film_tmpl`, `agar_crawlf_a0.157`, `agar_a2_p3` (the failure), `cl_brain_tmpl`, `cl_brain_s0`, `cl_reflex` and others.
  - Run entries now carry the world (`entry.world`, label). The viewer does not draw the plate or the gradient yet.
- **MP4s (gitignored, `runs/worm/media/`, contact sheets viewed):**
  - `cl_film_tmpl.mp4`: the template brain with the body on the agar film, 5 s, on guesses. This is now the week's "MP4 on guesses", in the demo world.
  - `agar_crawlf_a0.157.mp4`: the prescribed crawl wave on the film, crawling head first.
  - `cl_brain_tmpl.mp4` (published world), `cl_brain_s0.mp4`, `p3_final.mp4` and `p2.mp4`. Recorder: `scripts/worm/record_viewer_mp4.py <run>`.
- **Interface:** `docs/worm/INTERFACE.md` body side is current. Nothing is open between the workers. The film world adds no new channel. The `head`/`tail` chemical channels already use mm.

## Next (in order)

1. **Demo polish:**
   - the viewer draws the plate disc, the spot and the gradient for runs with `entry.world`;
   - then a longer closed loop on the film with the cone field (10 s is about 45 s of wall).
2. **Gate for `body.solver_exit = latest`.** Pre-register first: P0-P3 stay inside their bars, and a 0.01 wave moves the body. Adopt if both hold and the figure is viewed. Without it, the brain's drive must exceed about 0.05 to move anything.
3. Water RFT (`viscous_rft_water`) swim gates, pre-registered like A1/A2 (the P3 swim bars apply).
4. Speed:
   - `run_body_omp` with a thread count;
   - a closed-form 3x3 polar decomposition instead of the general SVD, matched on P2 first;
   - `--drag_every` larger than 1 once its effect is gated.
5. Sibernetic toggles (`body.pressure`, `muscle.force_model`), each with its own pre-registration.
6. Sensitivity pass to fill `precision_needed`.

## Sealed / held-out evidence

None spent by the body. The agar crawl readouts against literature are report-only this week (Director 17:25),
not scored, and nothing was tuned to them. The gait means used so far are calibration targets named in the
pre-registrations, not held-out data.

## Running processes

- `viewer/worm/serve.py` on 127.0.0.1:8781, PID in `/tmp/wb_serve.pid` (left up so Ben can look; idle). Stop it with `kill $(cat /tmp/wb_serve.pid)`.
- Nothing else is running on the Mac. Nothing is running on backhouse; `/home/greff/worm-body/` (27 MB) holds the copied sources, builds and timing jsons (keep them for re-timing).
- Scratch scripts in `/tmp/wb_q/` (`cl_tmpl.py`, `cl_film.py`, `bitcheck.py`, `pitch.py`, `tilt.py`, `add_*.py`) reproduce today's checks. They are not needed; everything they measured is in BODY_TESTS.md.
