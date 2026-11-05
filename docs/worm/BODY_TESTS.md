# Worm body tests: pre-registration and results

First body tested here = our own planar rod (resistive-force drag, 95 muscles), now archived with its ledger in
`archive/worm/rod_own/` (`body_parameters.csv`, built by `build_body_ledger.py`). The ported MetaWorm body's
numbers are in `data/worm/ledger/metaworm_parameters.csv` (built by `scripts/worm/build_metaworm_ledger.py`). Sources:
`docs/worm/research/BODY_PARAMS.md`, `docs/worm/research/BODY.md`.

## Pre-registration (written 2026-11-05 14:55 CST, before any gait or dead-worm run was scored)

Only a 1 s smoke run with zero input (straight worm, drift 3e-16 m) had been run when this was written.

### D: dead worm (brain silent)
Muscle input u = 0 for every muscle throughout. Media: agar and water. 10 s each.
- **D1 straight start:** centroid displacement < 1e-9 m and max |curvature| < 1e-9 /m over 10 s.
- **D2 bent start** (posture kappa(s) = 8 /mm sin(2 pi s / 0.65 L), muscle state 0): elastic energy never rises
  between steps (allowing 1e-12 of the initial energy for rounding); energy below 1% of initial by 10 s; centroid
  moves < 0.05 L in total.
- **D3 contracted start** (straight body, every dorsal muscle at activation 1, input 0): activation decays with
  tau_act; the body bends and then straightens; by 10 s elastic energy < 1% of its peak and curvature < 0.1 /mm.
- Falsifier control (must FAIL D2): the same run with the bending stiffness sign flipped (an unstable body) must
  raise its energy.

### G: prescribed muscle wave (no brain), crawling on agar and swimming in buffer
Drive: dorsal muscles u = a0 (1 + sin phi)/2, ventral u = a0 (1 - sin phi)/2, phi = 2 pi (f t - s_m / lambda_d),
s_m = muscle centre; ramped in over the first period; analysis window = the last 4 periods of 8 (swim) or of
6 (crawl). Frequency and wavelength of the drive are INPUTS set to the Fang-Yen 2010 means (swim f 1.76 Hz,
lambda_d 1.54 L; crawl f 0.30 Hz, lambda_d 0.65 L). So frequency and wavelength outputs only check that the
body transmits the wave; they are not predictions.

**Calibration (fitted, one number per medium, labelled fitted):** a0 is set by bisection so the head curvature
amplitude (mean over s = 0.1-0.2 L) equals the measured value: agar 8.5 /mm (Boyle-Berri-Cohen 2012 Fig. 3A,
read from figure, 8-9 /mm); water 4.5 /mm (midpoint of BBC Fig. 3A ~3 /mm and Sznitman 2010 6.07 /mm). a0 is a
stand-in for neural drive amplitude (a brain-side quantity), not a body parameter. If a0 > 1 is needed the body
is too weak: a failure, recorded as such (no change to M0 after seeing it).

**Held-out outputs and bars:**
- **G1 forward speed** (centroid, over the window): crawl in [0.08, 0.30] mm/s (Rabets 2014 80-300 um/s;
  Sibernetic 2018 experimental 0.1-0.3); swim in [0.29, 0.45] mm/s (Sibernetic 2018 experimental 0.29-0.38;
  Sznitman 2010 0.45). Must move head-first.
- **G2 body wavelength** lambda/L from the phase of the body curvature along s = 0.1-0.9 L: crawl [0.46, 0.84],
  swim [1.29, 2.15] (Fang-Yen 2010 mean +/- 2 SD with SD = SEM x sqrt(10), widened to the Sibernetic 2018
  experimental range). Transmission check.
- **G3 frequency** of body bending within 2% of the drive. Transmission check.
- **G4 (diagnostic, recorded, not a body pass condition)** tail/head curvature ratio (s 0.8-0.9 over 0.1-0.2) in
  [0.15, 0.5] (BBC Fig. 3A agar ~2/8.5 = 0.24, water ~1/3 = 0.33; Sznitman 2.21/6.07 = 0.36). With a uniform drive
  this tests body plus uniform-drive together, so a failure can be the drive's (brain side) and is not counted
  against the body.
- **Wrong control (must FAIL G1):** isotropic drag (C_n = C_t) in each medium. Resistive-force theory predicts no
  net thrust, so speed must fall below the lower speed bar.
- **Numerical check:** dt 1 ms vs 0.25 ms and N 48 vs 96 segments change speed and wavelength by < 2%.
- Also reported, no bar: the alternative agar drag toggle (`env.agar_drag = rabets_K1p4`) and the BBC force
  gradient toggle, run with the same a0 calibration rule.

The body passes G if G1, G2 and G3 pass in both media, the wrong control fails, and the numerical check passes.

## Results (2026-11-05 15:07 CST). Own rod, now ARCHIVED (Ben, 15:05: port published bodies instead)

The rod tested here is our own Kirchhoff rod with Boyle-Berri-Cohen 2012 numbers, not a faithful port of any
published code, so it is archived at `archive/worm/rod_own/` (Director, 15:05). Results kept as a record.
Raw: `data/worm/body_runs/body_tests*.json`, `gait_explore_posthoc.json`.

**Dead worm: PASS (after a numerical fix).** v0 (full-form solve) failed D1 on agar: curvature crept to 1.0e-6 /m
(bar 1e-9 /m) from rounding; displacement 2e-17 m was fine. Rewriting the step in incremental form (same
solution) gave D1 agar 0 /m, water 1.3e-10 /m. D2: no energy rise in 10 s; energy left 2.8e-5 (agar) and ~0
(water) of initial; centroid moved 0.008 L / 0.012 L; energy half-life 0.098 s agar, 0.002 s water. D3: bends
dorsal, then straightens (energy 0.4% of peak by 10 s). Flipped-stiffness control fails D2, as required.

**Gait v1 (as pre-registered, moment exponent 2):** crawl speed 0.105 mm/s PASS, wavelength 0.654 L PASS,
frequency PASS; swim speed 0.081 mm/s FAIL (bar 0.29-0.45), wavelength 1.54 L PASS, frequency PASS. Isotropic
controls fail as required (0.0002 and 0.0065 mm/s). G4 tail/head 0.88 / 1.00 (out of range, diagnostic). The
curvature profile was U-shaped: 42 /mm at the head tip, because the guessed moment ~ r^2 against EI ~ r^4
amplifies the thin ends.

**Post hoc (not passes):** the guessed exponent was revised to 4 (equal to EI, neutral) for the tip-curvature
reason; swim speed is therefore spent as held-out evidence. v2/v3: crawl 0.144 mm/s PASS, 0.645 L PASS, numerics
0.4%; swim 0.164 mm/s FAIL even at a converged step (water needs dt 0.125 ms: 1 ms was 8% off; first-order
convergence 0.175, 0.169, 0.166, 0.164, 0.163 mm/s as dt halves). Even a uniform 6.07 /mm swim curvature gave
~0.21-0.23 mm/s. Rabets K = 1.4 agar toggle: crawl 0.017 mm/s (cannot crawl at measured speeds under that drag
world). BBC force-gradient toggle: tail/head 0.65 crawl, 0.54 swim; speeds 0.149 / 0.108 mm/s.

Open (carried to the ported body): swim speed shortfall with Lighthill drag (K = 1.59) and a uniform sine drive;
the candidate causes are the drag anisotropy formula and the drive shape.

## Ported body: MetaWorm (BAAIWorm commit b99ca5ab), pre-registration (written 2026-11-05 15:21 CST)

Body = `third_party/metaworm/sim` (upstream C++, unchanged; Apache 2.0), driven headless by
`third_party/metaworm/driver/run_body.cpp` (ours; replaces only the GLUT loop and the Boost.Python bridge, same
stepping: muscle input at 30 Hz, 8 physics steps at 240 Hz). Published constants used as is: E 2e5, Poisson 0.4,
muscle stiffness 5e5, mass 10, mesh scale 0.004 (body 0.628 units long), fluid density 1000 with the upstream
quadratic drag and lift per surface triangle. Seen before writing this: one 2 s smoke run of the default key (turn2);
the centroid moved 0.059 units. No gait readout had been computed.

What MetaWorm itself published (Zhao et al. 2024 Nat Comput Sci; docs/worm/research/PORT_CANDIDATES.md A4): no
numeric speed, wavelength or frequency for the body. The body validation is qualitative: a periodic standard muscle
signal (no sensory feedback) gives a "Z-shape" / zigzag trajectory resembling experiment (SI Fig. S1, read via an
extraction; SI not read directly). So reproduction is of that qualitative result, made operational below.

Readouts (all from the vertex frames): midline = mean current position of the vertices in each of 48 material
slices along the rest body axis (head = the end where muscle segment 0 starts); signed dorsoventral curvature at each
interior node = d(tangent)/ds projected on the current material dorsoventral direction, reported as kappa x L
(dimensionless, L = rest length 0.628); speed = centroid (vertex mean) displacement over the window / window / L, in
L/s, + = head first; gait frequency, wavelength and amplitude by the same complex demodulation as the rod tests.

- **P0 dead body:** all 96 activations 0 for 10 s. Pass: max vertex displacement from rest < 1e-9 units.
- **P1 release:** key t0_fast for 3 s, then all activations 0 until 10 s. Pass: the RMS shape deviation from rest
  (after best rigid alignment, / L) at 10 s is below 10% of its peak.
- **P2 published periodic gait (reproduction):** key t0_fast (symmetric dorsal/ventral, 20-row period = 1.5 Hz),
  10 s (the published episode length, 2400 steps). Pass = the zigzag result: net centroid displacement over 2-10 s
  > 0.5 L, head first; the head tip's lateral position (perpendicular to the net path) has its dominant frequency
  within 5% of 1.5 Hz.
- **P2b default key turn2** (asymmetric, the upstream code default): diagnostic only; reported: net heading change
  over 10 s.
- **P3 literature check, prescribed sine wave (held out against Sibernetic 2018 Table 1 / Sznitman 2010):** driver
  mode `wave` at the Fang-Yen 2010 swim means f = 1.76 Hz, lambda_d = 1.54 L (inputs). Amplitude a0 calibrated (fitted,
  brain side) by bisection so the head curvature amplitude (s 0.1-0.2) is kappa x L = 4.5 (water target as for the
  rod, taking L = 1 mm). If a0 = 1 cannot reach it, record a0 = 1 and its readouts. Bars: speed in [0.29, 0.45] L/s
  (measured 0.29-0.38 mm/s Sibernetic 2018 experimental, 0.45 mm/s Sznitman 2010, over L ~ 1 mm: derived);
  wavelength [1.29, 2.15] L and frequency within 2% of the drive (transmission checks). Also reported: the Reynolds
  number U L / nu taking the units as SI and nu = 1e-6 m^2/s (derived; a real swimming worm is ~0.1-0.5).
- Not run, stated now: a time-step check (240 Hz is hard-coded in Environment; changing it means editing upstream).

Expectation stated in advance (a guess, not a bar): P3 speed may fail, because the published environment is an
inertial (quadratic, density-only) drag on a 0.63 unit, mass 10 body, not the viscous low-Reynolds world of a worm.
A P3 failure is a finding about the published environment, carried to the literature replacement step.

## Results: ported MetaWorm (2026-11-05 15:29 CST)

Readouts: `data/worm/body_runs/metaworm_tests.json` (scripts/worm/metaworm_tests.py, one run each, deterministic,
single thread, about 15 s wall per 10 s simulated on the Mac). Raw frames: runs/worm/metaworm/ (not in git).
Figures looked at: body silhouettes of p2 and p3_final at 0-10 s (each frame drawn in its own bending plane) and
docs/worm/figures/metaworm_p2.png. Verdict: **the port runs as published, its own qualitative gait reproduces (forward
undulation, curving path), and it fails the worm literature on speed by about 16-24x.** P0 pass, P1 fail by 0.1%,
P2 pass on displacement but fail on the pre-registered head-frequency readout, P3 fail on speed and frequency, pass
on wavelength.

| test | readout (measured in the sim) | bar | result |
|---|---|---|---|
| P0 dead body, 10 s | max vertex displacement 0 (exact; no gravity, no forces) | < 1e-9 | pass |
| P1 release at 3 s | RMS shape deviation at 10 s / peak = 0.1008 (peak 0.163 L at 0.93 s; 0.106 at 3 s, 0.052 at 4 s, 0.041 at 6 s, 0.032 at 8 s, 0.016 at 10 s) | < 0.10 | **fail** (decays, but slowly: damping is 0.9999 per step plus drag) |
| P2 key t0_fast | net displacement 1.95 L head first over 2-10 s | > 0.5 L | pass |
| P2 key t0_fast | head lateral frequency 0.30 Hz | 1.5 Hz +/- 5% | **fail** |
| P3 wave, a0 = 0.1573 (fitted) | speed 0.0185 L/s | 0.29-0.45 L/s | **fail** (16x to 24x too slow) |
| P3 | wavelength 1.59 L | 1.29-2.15 L | pass |
| P3 | body frequency 1.866 Hz vs drive 1.76 | within 2% | **fail** (6.0% off) |

Why P2's frequency readout fails while the body beats at the drive: the body curvature oscillates at exactly 1.5 Hz
(f_body_hz 1.500, measured), but the path curves (heading change 109 deg over 2-10 s, measured), so the head's
excursion perpendicular to the net chord is dominated by the 0.3 Hz path curvature. The readout was badly chosen;
the result stands as a fail. Post hoc and not a pass: the body does undulate at the drive frequency.

Other P2 numbers (measured): wavelength 0.57 L, head kappa x L 21.9, tail 26.8, speed rises over the run (centroid
speed per 2 s window 0.06, 0.20, 0.30, 0.35, 0.35 L/s), i.e. a 6 s inertial spin up. P2b (turn2, diagnostic):
heading change 173 deg, net displacement 0.75 L, speed 0.10 L/s.

Found while doing this (observations, no bar was set):
- **The drive-to-amplitude map is not smooth near the target.** P3 bisection head kappa x L vs a0: 0.15625 -> 4.06,
  0.1572 -> 4.18, 0.15771 -> 4.67, 0.1582 -> 5.07, 0.1602 -> 6.01. A 2.5% change in a0 moves the amplitude 48%. The
  calibrated run's amplitude also grows over time (head kappa x L per 2 s window 2.8, 5.3, 5.0, 4.6, 5.7): momentum
  builds up across beats. The bisection stopped at 14 iterations at 4.88 (8% off the target, not the 1% tolerance).
- **The body shortens under drive.** Midline length / rest length after 2 s, mean: p2 0.83, p3_final 0.89, a0 = 1
  0.63 (minimum 0.57). Co-contraction of both sides compresses the FEM body. A real worm's length is close to
  constant during locomotion (inferred from the inextensible rod models that match its gait; no measured bound
  cited yet).
- **The body tumbles in 3D.** There is no gravity or floor, so the bending plane rotates (per-frame plane normal
  moves from the y axis to (0.41, -0.59, -0.69) by 5 s in p2). Readouts use the material dorsoventral direction,
  so they are unaffected; plots must use each frame's own plane.
- **Reynolds number** U L / nu with units read as SI: 7,300 for P3 (derived). A swimming worm: ~0.1-0.5. The
  published world is metre scale, mass 10 over 0.63 units (density about 20,400 kg/m^3, derived from the mesh volume),
  with quadratic (inertial) drag. That is the regime behind the slow spin up, the slow decay (P1) and the speed fail.

What follows (Ben, 15:30: "Body: the 3D body only (no rod)"): keep this body, and make the literature replacements
labelled in the ledger: worm length and mass (1 mm, density about 1,080 kg/m^3), viscous resistive-force drag with the
measured drag anisotropy (water and agar) instead of the quadratic drag, and an E inside the measured range. Viscous
drag at worm scale is stiff at dt = 1/240 s, so it has to enter the projective-dynamics solve implicitly (an edit
to upstream World, kept as a toggle with the published environment as the other setting). Re-run P0-P3 after.

Readout check (post hoc, measured): at 48 slices the curvature readout has a static noise floor from the uneven mesh
(rest pose kappa x L RMS 7.4, max 17: the horizontal stripes in docs/worm/figures/metaworm_p3_final.png). The
amplitudes subtract the time mean, so they barely move with slice count: P2 head 21.9 / 22.3 / 23.3 and P3 head
4.9 / 5.5 / 5.0 at 48 / 24 / 16 slices; P3 wavelength 1.59 / 1.54 / 1.82 L (all inside the bar); frequencies
unchanged. No verdict changes. Use 24 slices (rest RMS 1.9) for the next pre-registration.

## Real-time factor of the ported body (2026-11-05 16:23-16:27 CST, measured)

Ben 15:30: "Real time seems fast enough, especially with a GPU port." This is a cost measurement, not a model test,
so no bar was pre-registered; the reference is 1.0 (real time). RTF = simulated seconds / wall seconds of the
control loop (`wall_s` in each run's json, a steady clock around the loop only, excluding mesh load and matrix
factorisation, about 0.2-0.3 s). 10 s simulated per run = 2,400 physics steps at 1/240 s, 50 projective-dynamics
iterations at most per step, early exit at the convergence threshold. One thread, frames written every control
step (30 Hz, as the viewer needs). Same sources (BAAIWorm b99ca5ab, unchanged) and driver on both machines, built
with `driver/build.sh` at `-O2 -std=gnu++14`.

| machine | build | run | wall per 10 s (mean, n) | RTF | ms per physics step |
|---|---|---|---|---|---|
| Mac, Apple M2 Pro, macOS 15.5 | Apple clang 17.0.0, -O2 | published key t0_fast (swimming) | 16.78 s (3; 16.58-17.05) | **0.60** | 7.0 |
| Mac | same | prescribed wave, a0 0.157 (P3) | 12.33 s (1) | 0.81 | 5.1 |
| Mac | same | dead (no drive) | 3.25 s (1) | 3.08 | 1.4 |
| backhouse, i7-14700K, WSL2 Ubuntu, vCPU 4 | g++ 13.3.0, -O2 | key t0_fast | 14.50 s (3; 13.88-14.97) | **0.69** | 6.0 |
| backhouse, vCPU 4 | same | wave a0 0.157 | 10.68 s (1) | 0.94 | 4.4 |
| backhouse, vCPU 4 | same | dead | 3.20 s (1) | 3.12 | 1.3 |
| backhouse, vCPU 20 | same | key t0_fast | 15.58 s (3; 15.01-15.91) | 0.64 | 6.5 |
| backhouse, vCPU 20 | same | wave / dead | 11.26 / 3.38 s (1 each) | 0.89 / 2.96 | 4.7 / 1.4 |

Verdict: **on one CPU thread the published body runs at 0.6-0.7x real time while swimming** (1.45-1.7x short of
real time), and 3x faster than real time when nothing moves. Load at the time: Mac 2.3-4.0 (other sessions),
backhouse 4.1-4.5 of 28 CPUs.

What the numbers say:
- **Cost follows the solver's iteration count, not the mesh.** Same mesh, same steps: dead 1.3 ms per step,
  the gentle wave 4.4-5.1, the published key 6.0-7.0. The solver stops early when converged, so a body that
  moves hard uses more of its 50 iterations. (Inferred from the code, `World::ProjectiveDynamicsMethod`; the
  iteration count was not logged.)
- **Same answer on both machines.** The max vertex displacement from rest is 1.15622578 (key) and 0.260600792
  (wave) on the Mac and on backhouse, equal to 9 digits (measured): the port is reproducible across compilers.
- **vCPU 4 against vCPU 20** is not a P-core against E-core comparison: inside WSL2 `taskset` pins to a virtual
  CPU, and Windows schedules vCPUs on any core. The 17:00-22:00 throttle pins the whole WSL VM to E-cores; that
  speed was not measured.
- Bash `time` around the runs on backhouse disagreed with the loop's steady clock (one run 7.5 s outside against
  15.0 s inside), so wall-clock jumps happen in WSL; only `wall_s` is used.

**Where the time goes** (Mac, macOS `sample` over 6 s of a key run, 5,134 samples, measured): the local step
(per-tet corotated projection plus muscles) 73%, of which Eigen's general 3x3 `JacobiSVD` alone is 68% of all
time; the sparse global solve with the J d product 24%; drag 1%; the rest under 2%.

**Speed-ups tried (backhouse, 16:28-16:36 CST, published key, 10 s each, measured).** Backhouse load rose from
4 to 14 (other users) during these runs, so compare only within a block, not with the table above.

| build | threads | wall per 10 s | RTF | max displacement |
|---|---|---|---|---|
| -O3 -std=gnu++14 | 1 | 16.52, 18.30, 17.68 s | 0.57 | 1.15622578 |
| -O3 -march=native -std=gnu++14 | 1 | crashes at start (segfault) | - | - |
| -O3 -march=native -std=gnu++17 | 1 | 18.25, 19.68, 18.61 s | 0.53 | 1.15622578 |
| -O2 -fopenmp, upstream's own loop switched on | 1 | 18.90, 18.18 s | 0.54 | 1.15622578 |
| same | 2 | 17.99, 16.47 s | 0.58 | 1.15622578 |
| same | 4 | 12.53, 13.00 s | 0.78 | 1.15622578 |
| same | 8 | 9.78, 10.32 s | **1.00** | 1.15622578 |

- **Threads work and change nothing in the result**: the OpenMP loop over the local step is upstream's own line
  (`sim/fem/World.cpp:237`, written and commented out; upstream's CMake links OpenMP), switched on in a copy of
  the sources. 8 threads give 1.85x over 1 thread in the same block and reach real time (RTF 0.97-1.02) even
  with the box loaded to 11-14. The result is identical to 9 digits at every thread count (each tet's projection
  is independent, the sum order is unchanged). Scaling is below the 2.8x the 73% share would allow at 8 threads
  (derived, Amdahl), most likely from the shared load (inferred).
- **Compiler flags are not a lever.** -O3 and -O3 -march=native are no faster than -O2 here (confounded by the
  rising load, but not faster within the noise). The C++14 native build crashes: Eigen fixed-size types need
  32-byte alignment under AVX and C++14 `new` does not give it (inferred, the standard Eigen pitfall); C++17
  fixes the crash.
- Not tried: a closed-form 3x3 polar decomposition in place of the general SVD (68% of the time; same maths,
  slightly different rounding, so it needs a P2 match check before use); the GPU port (Ben: later); fewer
  iterations or a looser threshold (a numerical change, needs its own check).

Not timed: the brain. The closed-loop budget is body plus brain per biological second.

## Closed loop and the solver dead zone (2026-11-05 16:40-17:05 CST, measured, Mac)

Director 17:00: "the bar is that it runs, stays bounded, and the viewer shows neurons lighting with the body.
Behaviour isn't required." These are plumbing and numerics checks, not model tests, so no behaviour bar was set.

**Pipe check.** The driver's `--mode pipe` (activations in, positions out, one exchange per physics step) against
the driver's own `--mode wave` with the same wave sent from Python: amplitude 0.5, 1.5 s. Largest frame difference
1.9e-9 (in units of the body's own coordinates; the body is 0.63 long), so the pipe does not change the physics
(measured). The difference is most likely numpy's `sin` against libm's (inferred). The pipe adds about 1% wall.

**Stand-in brain loop** (`cl_reflex`, 5 s, chemotaxis cone field on). A guessed test controller (head oscillator
plus a curvature reflex down the body), not a worm model. Runs, stays finite and bounded, RTF 0.74 on the Mac. The
body locks into a dorsal coil: the stand-in's reflex is positive feedback (inferred from its sign). Plumbing only.

**Real brain loop** (`cl_brain_s0`): brain.py `sample_worm(0)`, default toggles (Cook wiring), 0.5 ms internal
step, through INTERFACE.md with the body exchanging every 1/240 s and the brain stepping 4.0, 4.5, 4.0 ms.

| quantity | value |
|---|---|
| biological time | 3.0 s |
| wall (brain and body in parallel processes) | 10.65 s, 3.6 s per biological second |
| state finite throughout | yes |
| neurons above -20 mV at the end | 142 of 302 (the saturation the brain worker is diagnosing) |
| largest muscle activation sent | 4.4e-6 (scale 0 to 1) |
| largest vertex displacement from rest | 0 (exact) |

It runs and is bounded; the viewer shows the 302 neurons' voltages as a raster beside the muscle kymograph and on
the wiring diagram (checked by eye in screenshots and the MP4 contact sheet). The body does not move, for two
reasons: the drive is tiny, and the published solver has a dead zone (below).

**Solver dead zone.** MetaWorm's `World::ProjectiveDynamicsMethod` stops when one iteration changes the positions
by less than 5e-7 per coordinate on average, and then returns the iterate from before that last solve (read in
the code). For a body at rest under a weak load, the first solve already passes the test, so the step returns the
inertial prediction and the muscles are ignored. Prescribed wave, 1.5 s each, largest displacement from rest:

| wave amplitude | published exit | `latest` exit |
|---|---|---|
| 0.01 | 0 (exact) | 0.0099 |
| 0.03 | 0 (exact) | 0.0239 |
| 0.06 | 0.0299 | - |
| 0.09 | 0.0411 | - |
| 0.12 | 0.0501 | - |
| 0.15 | 0.0598 | - |

So with the published solver, drive below roughly 0.05 does nothing and drive above it moves the body (measured,
threshold bracketed between 0.03 and 0.06). Toggle `body.solver_exit`, neutral `published`; `latest` keeps the
converged solve (`World::SetReturnLatestIterate`, a wormemu extension). Its effect on the published gait P2 (key
t0_fast, 10 s, gait over 1.5-2.0 s):

| measure | published | latest |
|---|---|---|
| body frequency | 1.5 Hz | 1.5 Hz |
| wavelength | 0.568 L | 0.560 L |
| head curvature amplitude (kappa L) | 21.898 | 22.709 |
| speed | 0.260 L/s | 0.273 L/s |
| largest displacement from rest | 1.15622578 | 1.33096819 |

The gait is the same to within 5%, but the paths drift apart (largest vertex difference over 10 s 0.72 L), and
wall was 15.49 s against about 16.8 s. Not adopted: it changes a published result, so it needs a pre-registered
gate (does it keep P1-P3 inside their bars and remove the dead zone) before it can be on by default.

**Template worm loop** (`cl_brain_tmpl`, 17:14-17:16 CST, Mac, measured). The brain worker's recommended closed-loop
brain: `Brain(sample_worm(None), toggles=dict(receptor_sign="on"))` (every guessed number at its ledger default,
Fenyves et al. 2020 synapse signs first; brain at main 85080b4 with proprioception anterior of the soma), the body
with the published solver exit, the cone field on, 5 s. The seed-0 worm above cannot move because its own draw
caps muscle activation near 5e-6 (brain worker, derived); drawn worms have no guardrail yet.

| quantity | value |
|---|---|
| wall | 19.5 s for 5 s (3.9 s per biological second) |
| state finite | yes; soma voltages -67.6 to +5.1 mV |
| neurons above -20 mV | 9 at the first frame, then 104-109 of 302 |
| muscle cells above -20 mV | 39-42 of 95 after the first second |
| largest muscle activation | 0.794; 64 of 96 muscles average above 0.1 over 1-5 s; dorsal mean 0.40, ventral 0.38 |
| activation rhythm | none: over 1-5 s the power is in the lowest bin (0.25 Hz for a 4 s window), a slow drift |
| largest vertex displacement from rest | 0.436 (0.69 body lengths) |
| centroid travel | 0.036 net (0.06 body lengths) |
| largest midline curvature | 26 /mm in the first second, 13-19 /mm after |

Seen in the viewer and the MP4 contact sheet: the body curls within about 1 s and its shape drifts slowly after
(coil, then a V, then a coil); no rhythm and no crawling. The loop works end to end with real drive. That the
posture is held rather than a gait is the brain's saturation (still open on the brain side), not a body fault,
inferred from the tonic muscle cells. MP4: `runs/worm/media/cl_brain_tmpl.mp4`.

## Agar plate: pre-registration (written 2026-11-05 17:20 CST, before the code exists or any agar run)

Director 17:25 (for Ben): Boyle, Berri and Cohen's agar coefficients with their anisotropy as published; gates are a
dead body settling onto the plate and P3 not blowing up; crawl speed, frequency and wavelength against literature
agar values are report-only this week; the published world stays the other setting of the same toggles.

Configuration (new driver flags, each neutral = the published world):
- `body.scale = worm_1mm`. Keep the mesh; 1 length unit = 1.5934 mm, so the 0.6276-unit body is 1.0 mm (BBC's
  model length, published). Mass unit chosen so stress, stiffness and drag per length are numerically SI, so the
  published E and muscle stiffness carry over unchanged as Pa. Mass = density 1074 kg/m^3 (Reina et al. 2013,
  measured) x mesh volume, about 2.13 ug (derived), spread evenly over the vertices.
- `env.fluid = agar_rft`. Resistive-force drag, linear, in the implicit solve (`World::SetDragMatrix`):
  per vertex w [c_t t t^T + c_n (I - t t^T)], t = local midline tangent from 24 slice centroids, w = slice length
  per vertex. c_t = 3.2, c_n = 128 Pa s: BBC 2012's 3.2e-3 and 128e-3 kg/s for a 1 mm worm read per unit length
  (inferred), K = 40 as published. The out-of-plane direction uses c_n. The drag matrix is rebuilt from the current
  tangents every physics step (`--drag_every 1`) for the gates.
- `env.substrate = agar_plate`. Gravity 9.81 m/s^2 toward the plate; right side down (guessed: worms crawl on
  either side); the plate plane touches the rest body's lowest point; after each physics step, vertices below the
  plate are put back on it and their velocity into the plate is zeroed (no bounce). No friction beyond the drag.
- `env.fluid = viscous_rft_water` (c_t 0.00357, c_n 0.005675 Pa s, ledger rows mw_water_Ct/Cn) is built at the
  same time but not scored here.

Gates (L = rest length; frames at 30 Hz):
- **A1 dead body on the plate**, all activations 0, 3 s. Pass if all positions stay finite; the body's lowest
  point stays within 1e-3 L of the plate; the centroid moves less than 0.01 L in the plate plane; and no vertex
  moves more than 0.02 L from rest. (Expectation, derived: gravity is about 1000x weaker than the elastic forces,
  so the sag should be near 1e-3 L.)
- **A2 P3 drive on agar**: wave mode at the P3 inputs (f 1.76 Hz, lambda 1.54 L, a0 0.157), 5 s. Pass if all
  positions stay finite; at every frame no vertex is further than 0.6 L from the centroid; the midline length
  stays within 0.8-1.2 L; and the centroid stays within one body diameter (0.08 L) of the plate.

Numerics, reported with the gates: A2 with `--drag_every 8` against 1 (centroid speed change); A2 with
`body.solver_exit = latest` against published; the cost of one drag refactorisation and the RTF.

Report-only this week (no bar, no fitting): a crawl drive at the Fang-Yen 2010 crawl means (f 0.30 Hz,
lambda 0.65 L, inputs) at a0 = 0.157 (the P3 value) and a0 = 1.0 (the maximum), 10 s, last 2 periods. Readouts
against literature agar values: speed 0.08-0.30 mm/s (Rabets 2014; Sibernetic 2018 experimental 0.1-0.3), head
first; body wavelength 0.46-0.84 L (Fang-Yen 2010); body frequency against the drive (transmission); head
curvature against 8-9 /mm (BBC 2012 Fig. 3A, read from the figure). A2's readouts are reported the same way.
Expectation (a guess, not a bar): with K = 40 the slip is small, so the crawl speed should be near the wave speed
f x lambda = 0.195 L/s if the body carries the wave, head first.

## Results: agar plate (2026-11-05 17:21-17:29 CST, measured, Mac)

Smoke (measured): worm-scale numbers come out as derived (mesh volume 4.908e-4 units, mass 2.13 ug, g 6157
units/s^2). One drag refactorisation (rebuild C, refactor the implicit system) costs 4.6 ms. RTF at
`--drag_every 1`: 0.40 dead, 0.377 driven (published world, same wave on the Mac: 0.81, table above).

| gate | result | numbers (measured) |
|---|---|---|
| A1 dead body, 3 s | **PASS** | finite; lowest point within 8.0e-10 L of the plate; centroid drift 7.7e-5 L in plane; max vertex displacement 4.8e-4 L |
| A2 P3 drive, 5 s | **FAIL** (centroid height) | finite; spread max 0.520 L (bar 0.6); midline length 0.881-1.000 L (bar 0.8-1.2); **centroid height max 1.031 L** (bar 0.08 L); max vertex displacement 1.93 L; wall 13.27 s |

Numerics (A2 inputs, measured): `--drag_every 8` gives RTF 0.58, centroid height max 0.907 L, speed 0.394 L/s
(-3.6% against every step); `solver_exit = latest` gives RTF 0.38, height max 0.861 L, speed 0.380 L/s (-7%).
Neither changes the verdict. The implicit solve stays stable at the published step with K = 40 (no blow-up in
any run).

A2 readouts (report-only, and not meaningful: the body is mostly off the plate): body frequency 1.76 Hz,
wavelength 1.14 L, head amplitude kappa*L 5.2, tail/head 0.69, speed 0.41 L/s, wave head to tail.

What happened (measured): the body leaves the plate plane by pitching. The head-to-tail axis tilts up out of
the plate plane: 0 deg at 0.8 s, 10 deg at 1.7 s, 27 deg at 2.5 s, 48 deg at 3.3 s, 58 deg at 4.2 s; the head
rises 0.83 units (1.3 L) by 5 s; the centroid climbs about 0.15 units/s while moving along the body axis. The
dorsoventral axis rolls up to a median 33 deg out of the plate plane by 3 s. The published world does the same
without a plate: in P2 (10 s, no gravity) the axis pitches to -55 deg and the centroid drifts -0.76 units across
the plate axis. So the ported body's swimming path is not confined to its dorsoventral plane, and on the plate
nothing holds it down: gravity is about 1000x weaker than the elastic forces (derived), so the head lifts off.
The node-to-node alternating mean curvature profile in these runs (about +-25 kappa*L near the head) is not
out-of-plane bending: it is already there in the rest mesh, frame 0, in both worlds, a slicing artifact of the
midline estimate. The gait readouts subtract the mean, so they are unaffected.

Why a real worm stays down (published, qualitative): it lies in a thin water film whose surface tension holds it
against the agar (Gray and Lissmann 1964; Shen et al. 2012, Biophys J, "constrained to the surface of the plate by
a thin water layer"). Order of size (derived, not cited as a measurement): water surface tension 0.072 N/m x 1 mm
body is about 7e-5 N, against a weight of about 2.1e-8 N. The pre-registered plate has only gravity, so A2 fails
as written. The A2 failure stands; the fix below is a new setting with its own pre-registration.

## Agar film: pre-registration (written 2026-11-05 17:30 CST, before the code exists or any film run)

New setting of the same toggle: `env.substrate = agar_film` (needs `env.fluid = agar_rft`; `agar_plate` stays as
it is and keeps its A2 failure). Everything in `agar_plate`, plus the film surface: a second plane parallel to the
plate at the rest body's thickness across the plate axis (0.0601 L, measured from the mesh; 60 um at 1 mm). After
each physics step, vertices beyond it are put back on it and their velocity out of the film is zeroed, the same
rule as the plate. This is the water film's meniscus treated as a hard wall (form guessed; the force it stands
for is about 3000x the weight, derived above). Validity range: crawling on the surface only. No head lifting,
nictation or burrowing; a real meniscus lets the head rise a little and the hard wall does not.

Gates (bars as A1 and A2, unchanged):
- **A1f dead body on the film**, 3 s: the A1 bars. Expectation: frames bit-identical to A1, since the film
  surface is never reached at rest (report whether they are).
- **A2f P3 drive on the film**, 5 s: the A2 bars. The centroid-height bar is met by construction under the film
  (every vertex is within 0.0601 L of the plate), so the real tests are finite, spread and midline length. Added
  implementation check: the highest vertex never exceeds the film surface by more than 1e-6 L.

Report-only: share of vertices on the film surface and on the plate (mean over frames); the A2f readouts; the
crawl drive (f 0.30, lambda 0.65 L, a0 0.157 and 1.0, 10 s) with the readouts and literature values listed in the
agar plate pre-registration. Published world: P0 and P2 frames must stay bit-identical after the change.

## Results: agar film (2026-11-05 17:31-17:35 CST, measured, Mac)

| gate | result | numbers (measured) |
|---|---|---|
| A1f dead body, 3 s | **PASS** | as A1, and the frames are bit-identical to A1 (the film surface is never reached at rest) |
| A2f P3 drive, 5 s | **PASS** | finite; spread max 0.520 L; midline length 0.879-1.000 L; centroid height max 0.034 L (met by construction); highest vertex 0.0601422 L = the film surface (check passes); wall 17.94 s (RTF 0.28) |

P0 and P2 (published world) frames are bit-identical after the film change (checked 17:31). A2f report-only:
4.4% of vertex-frames sit on the film surface and 3.3% on the plate; body frequency 1.76 Hz, wavelength 1.20 L,
head amplitude kappa*L 3.8, tail/head 0.80, speed 0.31 L/s, wave head to tail. The RTF drops from 0.38 (plate) to
0.28; the likely reason is more solver iterations after each projection (inferred, not measured).

Crawl drive on the film (f 0.30 Hz, lambda 0.65 L, 10 s, readouts over the last 2 periods; report-only, no bar,
nothing fitted; 1 mm body, so L/s = mm/s and kappa*L = curvature in /mm):

| a0 | body f (Hz) | wavelength (L) | head curvature amplitude (/mm) | tail/head | speed (mm/s) | midline length (L) |
|---|---|---|---|---|---|---|
| 0.157 | 0.298 | 0.64 | 7.4 | 1.03 | 0.10, head first | 0.88-1.00 |
| 1.0 | 0.298 | 0.63 | 25.2 | 1.07 | 0.06, head first | 0.61-1.00 |
| literature (agar) | 0.30 (drive, Fang-Yen 2010 mean) | 0.46-0.84 (Fang-Yen 2010) | 8-9 (BBC 2012 Fig. 3A) | | 0.08-0.30 (Rabets 2014; Sibernetic 2018) | |

Reading (report-only): at a0 0.157 every readout is inside or near the literature range: speed 0.10 mm/s inside
0.08-0.30, wavelength 0.64 L inside 0.46-0.84, head curvature 7.4 /mm just under 8-9. The wavelength and
frequency are imposed by the drive, so they show transmission, not an emergent gait. Speed is 0.53 of the wave
speed f x lambda (0.195 L/s), not near 1 as I guessed beforehand. At a0 1.0 the body over-bends (25 /mm, about 3x)
and shortens to 0.61 L, and goes slower (0.06 mm/s). Viewed: `runs/worm/media/agar_crawlf_a0.157_sheet.png` and
the MP4 beside it: a flat sinuous body on the plate, about 1.5 waves along it, head first, no lift-off.

## Closed loop on the agar film (2026-11-05 17:37 CST, measured, Mac; no bar, a demonstration run)

`Brain(sample_worm(None), toggles=dict(receptor_sign="on"))` with `loop.Body(..., world=AGAR_FILM)` and the cone
chemical field, 5 s (`cl_film_tmpl`, scratch script `/tmp/wb_q/cl_film.py`). Wall 21.1 s (4.2 s per biological
second). Finite; highest vertex exactly at the film surface (0.0601 L); max activation 0.794, the same tonic
co-contraction as in the published world. The loop's curvature readout reaches 14.6 /mm by 1 s and 16.5 /mm by
5 s; the midline shortens to 0.67 L; the centroid drifts 0.05 L net in the plate plane (path 0.18 L). Viewed
(`runs/worm/media/cl_film_tmpl_sheet.png` and the MP4): the body curls into a C within about 1.2 s and holds it on
the plate, raster lit. No rhythm, no crawling: the brain side's open item (BRAIN_PORT section 6), not the body's.

## Closed loop on the agar film, 10 s demo (2026-11-05 17:44 CST, measured, Mac; no bar, a demonstration run)

Same setup as above, after merging main (brain: excitatory reversal template +0.5 mV, `muscle_active` wired but
off), 10 s (`cl_film_tmpl10`). Wall 43.8 s. Finite; highest vertex at the film surface; max activation 0.795; the
loop's curvature readout 14.6 /mm at 1 s, 16.3 /mm at 10 s; midline shortens to 0.66 L; centroid creeps 0.13 L net
in the plate plane (path 0.32 L). Viewed (`runs/worm/media/cl_film_tmpl10_sheet.png`, MP4 beside it, opened for
Ben): the body curls into a C by 2.5 s and holds it, with the plate, the 1 mm contours of the diacetyl cone and the
odour peak in view. No rhythm, no crawling, no chemotaxis.

## Gate for `body.solver_exit = latest`: pre-registration (2026-11-05 17:48 CST, written before any run below)

What changes: MetaWorm's solver returns the iterate from before its last converged solve; `latest` returns the
converged one (`World::SetReturnLatestIterate`). Neutral is `published`. Question: does `latest` remove the dead
zone without changing the published body's tested behaviour?

Already seen before this pre-registration (disclosed; these parts are confirmations, not tests): P2 under
`latest` (gait within 5%, table above), the 0.01 and 0.03 waves under both exits (1.5 s), and A2 on the gravity
plate under `latest` (speed -7%, 17:2x). Not yet seen: P0, P1, P3 under `latest`; anything at amplitude 0.001; A1f
and A2f under `latest`.

Same drives as the published tests, nothing recalibrated (P3 keeps a0 0.1573). Bars:
- **S1 no regression.** Under `latest`, P0 stays below 1e-9 displacement; every sub-bar of P1, P2 and P3
  (`pass`, `pass_disp`, `pass_freq`, `pass_speed`, `pass_wavelength`) keeps its published outcome or goes from fail
  to pass. Falsifier: any pass turns to fail.
- **S2 readouts close.** P2 and P3 gait readouts (body frequency, wavelength, head kappa*L, speed) and P1
  end/peak are each within 10% (relative) of the published values. Falsifier: any one off by more than 10%.
- **S3 dead zone gone.** Prescribed swim wave (f 1.76 Hz, lambda 1.54 L), 1.5 s, amplitudes 0.001 and 0.01, under
  both exits. Pass if under `latest` both move the body (largest displacement from rest above zero) and the
  0.01/0.001 displacement ratio is between 5 and 20 (close to linear, so no threshold remains); the published
  exit must still give exactly 0 at both (control). A response curve over 0.001-0.157 is report-only.
- **S4 demo world holds.** A1f and A2f under `latest` meet their 17:30 bars.

Adoption: if S1-S4 all pass and the figure is viewed, `latest` is adoptable as the default; I report it to the
Director before flipping the default, because the brain worker's closed loops use it. If any fails, it stays a
toggle and the failure is recorded here.
