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
