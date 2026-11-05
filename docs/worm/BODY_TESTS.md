# Worm body tests: pre-registration and results

Body = `src/wormemu/body` (planar rod, resistive-force drag, 95 muscles). All numbers from
`data/worm/ledger/body_parameters.csv` (built by `scripts/worm/build_body_ledger.py`). Sources:
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
