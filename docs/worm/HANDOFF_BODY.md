# Worm body + viewer: handoff (body worker, worktree `wormbody`)

**Rewritten each session; do not append.** State as of 2026-11-05 17:15 CST, at commit 4f7ef4a and the handoff
commit after it. The shared `docs/HANDOFF.md` belongs to main; this file is the body side until the Director
merges it.

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
  - Python driver: `src/wormemu/body/metaworm.py` (`run(out, mode=wave|key|dead, ..., solver_exit=...)`, `load`, `gait`, `Frame`).
  - Credits are in `docs/worm/ADOPTED.md`; what we changed is in `third_party/metaworm/UPSTREAM.md`.
- **Closed loop (new today, works):** `src/wormemu/body/loop.py`.
  - `Body(out, scene, frame_every, solver_exit)` wraps the driver's `--mode pipe`. Each exchange sends 96 activations and returns the vertex positions.
  - `run(brain, body, seconds)` steps brain and body in parallel processes and writes `out.neural.f32` beside the frames.
  - Exchange: every published physics step (1/240 s). The brain's `dt_ms` runs 4.0, 4.5, 4.0, repeating, and a command takes effect one exchange later. INTERFACE.md body side has the details.
  - Stand-ins (`WaveStandIn`, `ReflexStandIn`) are guessed test controllers, not worm models.
  - Measured (BODY_TESTS.md, last section):
    - pipe against the driver's own wave mode: the same to 1.9e-9;
    - stand-in loop: bounded, RTF 0.74;
    - real brain.py (seed 0, defaults, 3 s): runs and stays finite in 10.65 s of wall, with 142 of 302 neurons above -20 mV;
    - the largest muscle activation sent was 4.4e-6, so the body does not move.
- **Solver dead zone (found today, measured).** MetaWorm's solver returns the iterate from before its converged solve. A body at rest therefore ignores drive below about 0.05: a wave of amplitude 0.03 moves nothing, 0.06 does.
  - Toggle `body.solver_exit`, neutral `published`. `latest` (`World::SetReturnLatestIterate`) removes the dead zone.
  - On P2 the gait stays within 5% (1.5 Hz in both; wavelength 0.568 vs 0.560 L; speed 0.260 vs 0.273 L/s), but the paths drift apart.
  - Not adopted; it needs a gate (next item 2).
- **World extension (ours, inert unless called):** `SetUnitMass`, `SetDragMatrix` (implicit linear drag in the global solve) and `SetReturnLatestIterate`. With none called, P0 and P2 frames are bit-identical to the runs before the extension (rechecked 17:12).
- **Chemotaxis scene (MB11):** `src/wormemu/body/scene.py`.
  - Toggle `env.chemical_field`: none (neutral) | cone_published | exp_spot. Toggle `env.chemical_target`: published_3d | plate_projected.
  - The field is sampled at the nose (vertex 102) and the tail (vertex 173) into the `head`/`tail` channels.
  - Numbers and sources are in `docs/worm/research/CHEMOTAXIS_PLATE.md`. Upstream has no plate; its offline default has no gradient at all.
- **Real-time factor (measured, BODY_TESTS.md):**
  - one thread, swimming: Mac 0.60x, backhouse 0.69x;
  - upstream's own OpenMP loop at 8 threads reaches 1.0x on backhouse, with the same result to 9 digits (build `OMP=1 driver/build.sh`);
  - 68% of the time is Eigen's general 3x3 SVD;
  - the brain costs about 3.6 s of wall per biological second, so the brain now sets the loop's speed.
- **Tests:** `scripts/worm/metaworm_tests.py`; pre-registration and results are in `docs/worm/BODY_TESTS.md`.
  - P0 dead: pass. P1 release: fail (0.1008 vs 0.10). P2 published key: moves 1.95 L (pass), but the head-frequency readout fails. P3 prescribed wave: fails speed (0.018 vs 0.29-0.45 L/s) and frequency, passes wavelength.
  - Main finding: the published world is metre scale and inertial (Re about 7,300, against a worm's 0.1-0.5).
- **Ledger:** `scripts/worm/build_metaworm_ledger.py` writes `data/worm/ledger/` and `viewer/worm/data/`.
  - 42 body numbers (28 used by the running body) and 12 mechanisms. Every toggle is neutral = the published body.
  - Updated today: MB7 `brain_closed_loop` available; MB8 streamed; MB9 `body.solver_exit`; MB11 partial, with its two switches.
  - The viewer catalog now also carries the brain worker's 366 rows from `docs/worm/ledger.json`: 408 in all.
  - `precision_needed` is empty because the sensitivity pass has not run.
- **Viewer:** `viewer/worm/`. Start: `.venv/bin/python viewer/worm/serve.py`, open http://127.0.0.1:8781/. It now serves `viewer/worm/` only, not the repo root.
  - 3D body coloured by muscle activation, with an activation kymograph.
  - For closed-loop runs: a raster of all 302 neuron voltages under the kymograph, grouped by class, with a colour scale from -70 mV (dark blue) to +20 mV (pale yellow). The wiring diagram nodes are coloured by voltage.
  - Also: mechanisms with their toggles, the catalog, and a Run tab.
  - Run data: `scripts/worm/build_viewer_data.py` writes `viewer/worm/runs/` (gitignored); `cl_brain_s0` and `cl_reflex` are loaded.
- **MP4s (gitignored):** `runs/worm/media/cl_brain_s0.mp4` (the real brain with the body, 3 s; contact sheet viewed: raster lit, body still), plus `p3_final.mp4` and `p2.mp4`. Recorder: `scripts/worm/record_viewer_mp4.py <run>`.
- **Interface:** `docs/worm/INTERFACE.md` body side is current (exchange, lag, the first loop, the dead zone, head/tail from scene.py). The question sent to the brain worker at 17:12: are 4.0-4.5 ms steps fine for its lumped muscle and GCaMP layers, or does it need 1 ms? Not yet answered.

## Next (in order)

1. **Agar plate physics (MB4 to MB6), the demo world.** The plan, all derived and not yet built:
   - `--scale worm_1mm`:
     - keep the mesh; 1 length unit = u = 1.5934 mm (so the 0.6276-unit body is 1.0 mm);
     - the mass unit is u * (1 s)^2, which makes E, muscle stiffness and drag per length numerically SI;
     - mass = 1074 kg/m^3 (Reina 2013, measured) x mesh volume 4.90778e-4 x u^2 = 1.338e-6 sim units (2.13 ug), spread with `SetUnitMass`;
     - gravity 9.81 / u = 6156.6 u/s^2.
     - The published quadratic drag hard-codes water's density, so worm_1mm with it is an error.
   - `--fluid agar_rft | viscous_rft_water`:
     - resistive-force drag as the implicit matrix C (`SetDragMatrix`);
     - per-vertex 3x3 blocks w_k [c_t t t^T + c_n (I - t t^T)];
     - w_k = slice length / vertices per slice over 24 rest-z slices, with t from the slice centroids;
     - re-factorise when C changes.
     - Agar values: Boyle, Berri and Cohen 2012, Ct 3.2e-3 and Cn 128e-3 kg/s (K = 40), read per body length. Other K estimates run 3-40.
   - `--substrate agar_plate --side_down right|left`:
     - gravity along -y;
     - the plate plane at the rest minimum;
     - a post-step projection of positions and normal velocities.
   - Scale check (derived): c_n/h about 19.6 per coordinate against an elastic term of about 6000 and a mass term of 7.8e-5. So the body is overdamped, and gravity is about 1000x weaker than elasticity.
   - Tests: pre-register first. A dead body must settle on the plate; P3 on agar must not blow up. Re-time, including the factorisation cost.
   - Then the viewer shows the plate disc, the spot and the gradient, and an MP4 of the worm on the plate with the brain.
2. **Gate for `body.solver_exit = latest`.** Pre-register: P0-P3 stay inside their bars, and a 0.01 wave moves the body. Adopt if both hold and the figure is viewed. Without it, the brain's drive must exceed about 0.05 to move anything.
3. Speed:
   - let `metaworm.py` and `loop.py` use `run_body_omp` with a thread count;
   - replace the general SVD with a closed-form 3x3 polar decomposition, matched on P2 first;
   - the brain side is now the larger cost.
4. Sibernetic toggles (`body.pressure`, `muscle.force_model`), each with its own pre-registration at 24 slices.
5. Sensitivity pass to fill `precision_needed`.

## Sealed / held-out evidence

None spent by the body. The gait means used so far (swim speed, frequency, wavelength, head amplitude) are calibration targets named in the pre-registration, not held-out data. Sibernetic's validation numbers are the same kind of target.

## Running processes

- `viewer/worm/serve.py` on 127.0.0.1:8781, PID in `/tmp/wb_serve.pid` (left up so Ben can look; idle). Stop it with `kill $(cat /tmp/wb_serve.pid)`.
- Nothing else is running on the Mac. Nothing is running on backhouse; `/home/greff/worm-body/` (27 MB) holds the copied sources, builds and timing jsons (keep them for re-timing).
- Scratch scripts in `/tmp/wb_q/` (`brain_loop.py`, `deadzone.py`, `exit_check.py`, `bitcheck.py`, `shot.py`) reproduce today's checks. They are not needed; everything they measured is in BODY_TESTS.md.
