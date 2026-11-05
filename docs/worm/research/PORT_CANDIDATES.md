# Port candidates for a C. elegans body model

Research notes for porting a PUBLISHED worm body model instead of writing our own. Done by web
search/fetch plus shallow clones into /tmp/wb_ext2/ (not kept in the repo). No heavy computation was
run; nothing was executed, only source read.

Labels used throughout: **measured** = reported lab measurement; **modelled** = a model's own chosen
parameter (not claimed to be measured); **derived** = computed from other listed numbers. Source is
always a paper figure/table or a repo file + line number. "Not found" means I looked and could not
confirm it.

---

## PART A. MetaWorm / BAAIWorm body model

Paper: Zhao et al. 2024, *Nature Computational Science* 4:978-990, "An integrative data-driven model
simulating C. elegans brain, body and environment interactions," DOI 10.1038/s43588-024-00738-w.
Earlier preprint under the name "MetaWorm": Zhao et al., bioRxiv 2024.02.22.581686 (v1 and v2).
Repo: https://github.com/Jessie940611/BAAIWorm (tag v1.0.0, main branch at commit b99ca5a as of
2026-11-05). The body-and-environment sub-model is in the repo's `Metaworm/` folder; the brain model is
in `eworm/`; `neuronXcore` is the C++/CUDA/Optix visualizer.

### A1. Body model type and mesh

- Solver: **projective dynamics** FEM (confirmed both by the paper text and by the repo: the muscle and
  elasticity constraints in `Metaworm/sim/fem/Constraint/*` are classic projective-dynamics local/global
  constraints — `CorotateFEMConstraint`, `LinearMuscleConstraint`, `TriangleMuscleConstraint`,
  `TriangleStrainConstraint`, `TriangleBendingConstraint`, `AttachmentConstraint`).
- Mesh (**measured/modelled mix**, source: paper text via automated extraction, cross-checked against
  repo comments): 984 vertices, 3,341 tetrahedra, 1,466 surface triangles.
- Muscles: **96** muscle cells in four longitudinal strings — ventral right (VR), ventral left (VL),
  dorsal right (DR), dorsal left (DL), i.e. 24 cells per string (paper text; matches the README's "`m`:
  worm muscles (96 muscles)" keyboard-shortcut help text, confirmed in
  `/tmp/wb_ext2/BAAIWorm/README.md`).
- Muscle activation -> mesh: each muscle is a `LinearMuscleConstraint`/`TriangleMuscleConstraint` with a
  fiber direction; activation scales the constraint's target length/stiffness (see
  `Metaworm/sim/fem/Constraint/LinearMuscleConstraint.cpp` lines 17-57). Per-muscle activation values
  come from `Metaworm/sim/Muscle.cpp` (`Initialize`, muscle_stiffness argument) and are read from JSON
  muscle-pattern files under `Metaworm/data/muscle/*.json`.
- Code provenance note (not in the paper, found by reading the repo): the FEM/muscle/constraint code
  under `Metaworm/sim` is structurally the same architecture as the "SoftCon" soft-body RL codebase
  (projective dynamics + muscle constraints + `cArgParser` args files named like
  `run_humanoid3d_walk_args.txt`, and the macro `SOFTCON_DIR` used for the data path in
  `Metaworm/sim/Environment.cpp` line 37). This is a code-reading inference, not confirmed by the paper
  or README — label it **inferred**, not measured.

### A2. Solver / timestep parameters (source: repo code, `Metaworm/sim/Environment.cpp` lines 27-38)

- `mSimulationHz = 240` -> physics timestep **dt = 1/240 s ≈ 4.17 ms** (modelled, repo line 27).
- `mControlHz = 30` -> control/sensorimotor update every **33.3 ms** (modelled, repo line 28).
- `mMaxIters = 2400` -> a run is 2400/240 = **10 s** of simulated time by default (derived).
- `mSoftWorld = new FEM::World(1.0/mSimulationHz, 50, 0.9999, false)` (repo line 38): the projective
  dynamics `World` constructor takes `(time_step, max_iteration, damping_coeff,
  is_precessing_collision)`. So the PD solver does **50 local/global iterations per step**, with a
  **damping coefficient of 0.9999** (modelled, repo line 38), and collision handling disabled in this
  constructor call.
- Separately, an automated extraction of the paper text (WebFetch summary, not independently verified
  against the PDF) reported "neural network time step ~1.67 ms" and "physical environment time step
  100 ms" with sync "every 100 ms." These numbers do **not match** the repo's 1/240 s and 1/30 s values
  above. I could not resolve the discrepancy — it may be that the paper text I got described a different
  coupling loop (e.g. the brain model's own integration step vs. the body's physics step) than the one
  in `Environment.cpp`. Flag as **unresolved**; trust the repo numbers over the auto-summarized paper
  text until someone reads the PDF directly.
- Real-time factor: paper text (via auto-extraction) says the GUI runs at "30 frames per second" / "real
  time simulation," matching `mControlHz = 30`. Not independently verified against the PDF.

### A3. Material / drag parameters (source: repo code)

- `mCreature = new Worm(5E5, 2E5, 0.4)` in `Metaworm/sim/Environment.cpp` line 38, matching the
  constructor `Worm::Worm(muscle_stiffness, youngs_modulus, poisson_ratio)` in
  `Metaworm/sim/Worm.cpp` lines 13-14:
  - **muscle_stiffness = 5e5** (modelled; units not stated anywhere in the code, presumed Pa given FEM
    convention, not confirmed).
  - **Young's modulus = 2e5** (modelled; units not stated, presumed Pa, not confirmed).
  - **Poisson ratio = 0.4** (modelled).
- Fluid density used in the drag force calculation: **1000** (hard-coded literal in
  `Metaworm/sim/Worm.cpp` line 981, `force_drag_per_face = 0.5 * 1000.0 * ...`; presumed kg/m^3 = water,
  not confirmed by a comment).
- Drag model: angle-of-attack-dependent coefficient `Cd(aoa, a, c)` (`Metaworm/sim/Worm.cpp` line 817) —
  a resistive-force-theory style per-face formula, not a single scalar C_parallel/C_perpendicular pair
  like Boyle-Berri-Cohen's. I did not fully reverse-engineer the formula; flag the exact functional form
  as **not characterized** in these notes.
- The paper itself (per the automated extraction) **explicitly states its body parameters "did not
  correspond precisely to those of actual C. elegans, because they were difficult to measure
  accurately."** This is an important finding for our per-value bar: MetaWorm's body material constants
  are acknowledged by the authors as placeholders, not fitted/measured biological values.

### A4. Quantitative validation reported in the paper

I could not get a clean read of the Nature paper or its Supplementary Information PDF directly (paywall
on nature.com; bioRxiv full text returned HTTP 429 "too many requests" on repeated tries and I did not
keep retrying since the task says light fetch only). What I have is from an automated extraction of the
bioRxiv v2 full-text HTML, which should be treated as lower-confidence than a direct PDF read:

- **No numeric swim/crawl speed, wavelength, or frequency values were found** for the body validation.
  The validation described is qualitative: Figure 8B (paper numbering, per the extraction) compares the
  simulated trajectory's "zigzag" shape to a cited experimental trajectory, described as "closely
  resembled" — no numbers.
- A prescribed/periodic (non-sensory-feedback) muscle activation test is mentioned ("periodic standard
  signal, i.e. without sensory feedback"), reported to produce a "Z-shape" trajectory similar to
  experiment (Supplementary Figure S1 per the extraction), but **no activation frequency, amplitude or
  phase-lag numbers were recoverable**.
- **Not found**: any Young's modulus/Poisson ratio/density from the paper's own text (only from the repo
  code, see A3). **Not found**: muscle force scale in physical units. **Not found**: a quantitative
  speed/wavelength/frequency table equivalent to what Sibernetic or BBC 2012 report (see Part B).
- Recommendation if this number matters: read the Nature SI PDF directly (not accessible to me here) —
  it may contain a validation table the HTML preprint text does not.

### A5. License and dependencies

- Top-level repo license: **Apache License 2.0** (`/tmp/wb_ext2/BAAIWorm/LICENSE`). Also present at
  `Metaworm/LICENSE` (Apache 2.0) and `owl/LICENSE` (Apache 2.0, this is the vendored OWL ray-tracing
  library by Ingo Wald, used only for the `neuronXcore` visualizer, not the body physics). This is a
  permissive license, unlike the CC-BY-NC of the BBC 2012 paper discussed below — worth noting since it
  removes the non-commercial restriction as a blocker.
- Dependencies (source: `README.md` "System Requirements" and "Installation Guide" sections):
  - Tested on Ubuntu 20.04, Nvidia 3090, **CUDA 11.4**, **Python 3.8.x**, **Nvidia Optix 7.0.0**.
  - C++ build: CMake, Eigen3, Boost 1.79 (built from source, with Python bindings), OpenGL/GLUT/GLEW/X11
    dev libraries.
  - Python: `NEURON==8.0.0` (compiled NMODL mechanisms via `nrnivmodl`), `torch==1.12.1`, `numpy`,
    `scipy`, plus a long tail of Ubuntu-specific system packages baked into `requirements.txt` (that file
    looks like a dump of an entire Ubuntu desktop's pip environment, not a clean dependency list — a
    red flag for easy reproducibility).
  - CUDA + Optix are needed for the `neuronXcore` 3D **visualizer**, not for the FEM body physics itself
    (`Metaworm/sim/fem` and `Metaworm/sim/Worm.cpp` are plain C++/Eigen, no CUDA calls found in a grep of
    that subtree). This suggests the body-only solver could in principle be built and run without CUDA
    or Optix, but the demo path in the README goes through the combined `neuronXcore` binary which does
    need them — not independently verified by actually building it.

---

## PART B. Published fast rod/body code for porting

### B1. Boyle, Berri & Cohen 2012 ("BBC 2012"), *Front. Comput. Neurosci.* 6:10, doi
10.3389/fncom.2012.00010, "Gait modulation in C. elegans: an integrated neuromechanical model"

- Repo (task gave `openworm/CelegansNeuromechanicalGaitModulation`; the canonical one is actually
  **`OpenSourceBrain/CelegansNeuromechanicalGaitModulation`**, confirmed BBC 2012 code — its README says
  "A model of C. elegans locomotion described in Boyle, Berri and Cohen... Front. Comput. Neurosci.,
  2012," and its `WormSim/README.md` says it is "based on the original readme.txt in the Supplemental
  data" of that paper). `openworm/CelegansNeuromechanicalGaitModulation` also exists on GitHub (checked
  via `git ls-remote`) and appears to be the same repo mirrored/forked under the openworm org (587 files
  in both, same top-level structure, only git pack-file names differ) — not confirmed to be byte-for-byte
  identical beyond directory listing and spot checks.
- Language: **C++** (`WormSim/Model/worm.cc`), plus a MATLAB viewer (`WormSim/MatlabSupport/WormView.m`)
  and newer Python viewers (`WormSim/Model/WormView.py`, `WormViewCSV.py`). Build uses `make` against a
  vendored **SUNDIALS 2.3.0 IDA** solver (`WormSim/sundials-2.3.0/`), per `WormSim/README.md`'s build
  instructions.
- License: **no top-level LICENSE file in the repo.** The only LICENSE files present are deep inside the
  vendored `sundials-2.3.0/` dependency (BSD-style, for SUNDIALS itself, not for the worm code). The
  paper itself (confirmed by reading the PDF, last page) is published under "the terms of the Creative
  Commons Attribution Non Commercial License, which permits non-commercial use, distribution, and
  reproduction in other forums, provided the original authors and source are credited" — i.e. **CC
  BY-NC**. Whether that license is meant to cover the "Supplemental data" code (S14, mentioned in the
  paper's Supplementary Material section) is not stated explicitly anywhere I found. **This is a real
  gap: the repo code itself has no explicit license grant.** Safer path: reimplement from the paper's
  published equations and parameter tables (which are covered by the CC BY-NC text) rather than copy
  repo code verbatim, and keep any port's use non-commercial/research, consistent with our project.
- Body model (read directly from the paper PDF, Section 2.2 "The physical model," Table 1, Table 3,
  pages 2-7 of the PDF):
  - 2D outline, body as 49 "rods" (**measured/modelled**, M = 48 segments, P = 2(M+1) = 98 points,
    Table 1), damped springs (lateral, diagonal) plus active muscle elements, **length L = 1 mm, minor
    radius R = 40 um** (Table 1).
  - Spring/damping constants (all **modelled**, Table 1): kappa_L = (M/24)*0.01 kg/s, kappa_D =
    kappa_L*350, kappa_0M = kappa_L*20, beta_L = kappa_L*0.025 s, beta_D = kappa_D*0.01 s, beta_0M =
    beta_L*100, Delta_M = 0.65, F_max,1 = 0.7*(2/3), F_max for m=2..M = 0.70 - 0.42*(m-1)/M (anterior-
    posterior gradient).
  - Drag coefficients (Section 2.1, p.2 of the PDF): water coefficients derived from Lighthill (1976)
    slender-body theory (**derived**, eq. 1 in the paper): C_par,water = L*2*pi*mu/ln(2q/a), C_perp,water
    = L*4*pi*mu/(ln(2q/a)+0.5), with mu ~= 1 mPa.s (water viscosity), q = 0.09*lambda (lambda ~= 1.5 mm
    typical wavelength in water), L = 1 mm, a = 40 um. Agar coefficients: **C_par,agar = 3.2e-3 kg/s**
    (measured, from Wallace 1969's direct force measurement on glass fibers, as used by Niebur & Erdos
    1991) and **C_perp,agar = 128e-3 kg/s** (derived from an estimated ratio K_agar ~= 40, citing the
    authors' own prior motion-simulator work, Berri et al. 2009). The drag ratio K = C_perp/C_par is
    swept **1.5 <= K <= 40** across their simulations (Figure 4C), with K ~= 1.5 for water and K ~= 40
    for agar.
  - No explicit Young's modulus is defined — the body is a spring-damper network, not a continuum FEM
    mesh, so "Young's modulus" doesn't directly apply; the spring constants above are the closest
    analogue.
  - Numerics (Section 2.4, p.8): implemented in C++ with the SUNDIALS IDA 2.3.0 implicit DAE solver;
    neuromuscular system integrated with **explicit Euler, 1 ms step**; physics solver uses adaptive
    time steps with base relative error tolerance 1e-12 and absolute spatial tolerances 1e-9
    (coordinates) / 1e-5 (rod angles) for "more resistive" (agar-like) media; for less resistive media
    (C_par <= 27.3e-6 kg/s or C_perp <= 51.2e-6 kg/s, i.e. close to water) all tolerances are tightened
    by 10x for stability.
- Quantitative validation reported (read directly from the PDF):
  - **Figure 4A vs 4B**: experimental frequency-wavelength relation (wavelength/body-length lambda/L vs
    frequency f in Hz), measured by Berri et al. 2009 in gelatin (varying % concentration) and agar
    (triangles), compared against the model's own lambda/L vs f relation swept across drag-coefficient
    combinations (Figure 4C). The paper states the model shows "good quantitative agreement" with this
    curve (Section 3.2, p.9) but I did not find a single reduced summary number (e.g. an R^2 or percent
    error) — it is a visual/qualitative-fit-to-a-curve comparison, not a table of speed values.
  - **Figure 3**: posteriorly-decreasing curvature gradient, kappa-bar (1/mm) vs body position S in
    [0,1], compared between agar and water, for both experiment (averaged over n=3 agar worms, n=5 water
    worms, over ~10 s each) and the model; described as "qualitatively similar."
  - **Section 3.4 / contact force**: model predicts mean peak contact force against a microfluidic pillar
    of **F = 0.84 +/- 0.22 uN** vs the experimentally reported **2.5 +/- 2.5 uN** (Doll et al. 2009),
    called "totally consistent" given the large experimental uncertainty (both measured and modelled
    numbers, clearly labelled in the text).
  - **Oscillation frequency range**: the model (via bistable B-class motoneurons) sustains frequencies
    "~0.5-2 Hz" (modelled/derived range, Section 3.5), matching the paper's stated biological range of
    0.5 Hz (crawling) to 2 Hz (swimming) quoted in the Abstract/Introduction (measured, citing prior
    work, not re-derived here).
  - **I did not find an explicit absolute speed number in mm/s** anywhere in the 15-page PDF I read (the
    paper reports frequency and wavelength/body-length, not raw forward speed) — mark this **not
    found** in the primary source; it may be in the cited Berri et al. 2009 paper instead.
- Prescribed/sine-wave activation test: **not found** — the BBC 2012 model is driven by its own
  closed-loop proprioceptive neural circuit (Section 2.3/3.1), not by an externally imposed sinusoidal
  muscle pattern; I did not find a standalone open-loop sine-drive test in this paper.

### B2. Izquierdo & Beer / Olivares, Izquierdo & Beer — "CE_locomotion"

- Repos checked (both exist and are near-identical, 20 files each, same filenames):
  `https://github.com/openworm/CE_locomotion` and `https://github.com/edizquierdo/CE_locomotion`
  (edizquierdo's is presumably upstream of the openworm mirror, not independently confirmed which way
  the fork direction runs).
- Language: **C++** (`main.cpp`, `Worm.cpp/h`, `WormBody.cpp/h`, `NervousSystem.cpp/h`, `Muscles.cpp/h`,
  `StretchReceptor.cpp/h`, `TSearch.cpp/h` for the evolutionary parameter search), no external heavy
  solver dependency — just a `Makefile`. Companion Python (`viz.py`, `load_data.py`) and Mathematica
  (`viz.nb`) scripts for visualization only.
- Body model: **this is a from-scratch, independent reimplementation of the BBC 2012 body**, explicitly
  stated in the file header of `WormBody.h`/`WormBody.cpp`: "An implementation of the C. elegans body
  model described in... J.H. Boyle, S. Berri and N. Cohen (2012)... Although this implementation is
  completely original, the body model itself should be identical to that of BBC with the exceptions
  commented as 'NOTE n'... Created by Randall Beer on 7/8/14." It documents at least two concrete
  deviations found by Beer while re-deriving BBC's code (a macro expansion bug in the original BBC code,
  and a formula discrepancy Beer could not resolve even after asking Boyle directly — "Boyle, personal
  communication, June 30, 2014"), with a `BBC_STRICT` compile flag to reproduce the original behaviour
  exactly. All of BBC's Table 1/3 parameter values are reproduced as named constants in `WormBody.h`
  (confirmed matching the PDF's Table 1: `L_worm = 1.0e-3` m, `N_segments = 50` [note: 50, not BBC's 48
  — a deliberate deviation, commented `//YYY` in the header, not explained further], `R_min = 40.0e-6` m,
  `C_agar_par_total = 3.2e-3` kg/s, `C_agar_perp_total = 128e-3` kg/s, `kappa_L`, `kappa_D`, `kappa_M0`,
  `beta_L`, `beta_D`, `beta_M0`, `delta_M = 0.65` — all matching BBC's Table 1 formulas).
  - Water drag coefficients are given directly as totals in this code: **C_water_par_total = 3.3e-6
    kg/s, C_water_perp_total = 5.2e-6 kg/s** (modelled, `WormBody.h` lines 41-42) — these are closer to
    literal numeric water-drag values than BBC's paper, which instead gives a formula (Lighthill
    slender-body theory) rather than a fixed number; not independently reconciled against BBC's formula
    here. Treat as **not verified identical** to BBC 2012, though clearly in the same regime.
  - Integration: `Worm::Step` (`Worm.cpp` line 121) drives the body with
    `WormBody::SemiImplicitBackwardEulerDAEStep` (semi-implicit backward Euler / 1st-order BDF with one
    Newton iteration per step, per the comment in `WormBody.cpp` lines 85-89), the nervous system with
    plain `EulerStep`, and the muscles with `EulerStep`. Default step size in `main.cpp` line 23:
    **StepSize = 0.005 s (5 ms)**, with an 8 s transient and 24 s duration per evaluation (`main.cpp`
    lines 21-23) — this is much coarser than BBC's own 1 ms neuromuscular step, and avoids SUNDIALS
    entirely, which is presumably why it is fast: the README says a full evolutionary run (many
    simulation trials) "takes approx. 2 minutes."
  - Fitness/target speed used during evolutionary search (`main.cpp` line 26): `AvgSpeed = 0.0001` m/s =
    **0.1 mm/s**, with a commented-out alternative `//0.00022` m/s = 0.22 mm/s right next to it. This is
    a **modelled** target (the code's own fitness function), not a citation of a measured value in this
    file — I did not trace where 0.0001 vs 0.00022 m/s came from; it is plausibly derived from BBC 2012
    or related crawling-speed literature but that link is **not confirmed** here.
- License: **no LICENSE file found in either repo.** `WormBody.h`'s header says "Created by Randall Beer
  on 7/8/14. Copyright (c) 2014 Randall Beer. All rights reserved." — i.e. explicit all-rights-reserved
  copyright notice, no open-source grant. **This blocks a direct code port without contacting the
  author(s)** for permission; a clean-room reimplementation from BBC 2012's published equations (CC
  BY-NC) would sidestep this.
- Associated papers with further parameters/validation (not fully read in this session, found by
  search only): Izquierdo & Beer 2018 (muscle model), Olivares, Izquierdo & Beer 2018 (neural unit),
  and Olivares, Izquierdo & Beer 2021, *Front. Comput. Neurosci.* 15:572339, "A neuromechanical model of
  multiple network rhythmic pattern generators for forward locomotion in C. elegans," doi
  10.3389/fncom.2021.572339 — this combines "the neural unit from Olivares et al. (2018), the muscular
  model in Izquierdo and Beer (2018), and the physical model of the body and environment in Boyle et
  al." (per search-result summary, not independently verified by reading the paper). I did not read this
  paper's own validation numbers (e.g. body-lengths/s) in this session — **not found** here, flag for a
  follow-up read if this specific paper's numbers matter.

### B3. Denham, Ranner & Cohen 2018, *Phil. Trans. R. Soc. B* 373:20180208, "Signatures of proprioceptive
control in Caenorhabditis elegans locomotion"; and Ranner 2020-era viscoelastic Cosserat-rod FE work

- I read the PDF directly (eprints.whiterose.ac.uk copy) looking for a data/code availability statement
  and validation numbers. The automated extraction of that PDF did **not** turn up a data/code
  availability statement, and did not yield clean validation numbers (the tool flagged the PDF stream as
  not fully legible for extraction) — I did not find confirmation either way of public code for this
  specific 2018 paper. **Not found.**
- A related, later paper by Thomas Ranner's group — Wang, Ranner et al., "A monolithic optimal control
  method for displacement tracking of Cosserat rod with application to reconstruction of C. elegans
  locomotion," *Computational Mechanics* 71:409-432 (2023) — reportedly has FreeFEM++ code on GitHub
  (per search results, under `github.com/yongxingwang`, not independently cloned or verified in this
  session). This is a different paper from Denham/Ranner/Cohen 2018 (it is about inverse/optimal control
  for shape reconstruction, not forward locomotion dynamics) — **not directly relevant** to a forward
  body-dynamics port, but worth knowing it exists if a Cosserat-rod FE approach is ever wanted.
- No code repo confirmed for the original 2018 Denham/Ranner/Cohen proprioceptive-control paper itself.

### B4. Sibernetic (openworm/sibernetic), Palyanov, Khayrulin et al.

- Repo: https://github.com/openworm/sibernetic (shallow clone, 119 files at this depth/filter).
- License: **MIT** (`/tmp/wb_ext2/sibernetic/LICENSE`, "Copyright (c) 2011, 2013, 2014 OpenWorm" — clean,
  permissive, confirmed directly from the file).
- Language: **C++ and OpenCL** (PCISPH — Predictive-Corrective Incompressible Smoothed Particle
  Hydrodynamics), with a Python layer (`main_sim.py`, `sibernetic_c302.py`, `SibSimulation.py`) for
  driving it from muscle-activation signals and for c302/PyOpenWorm integration; OpenGL for 3D
  visualization. Needs an OpenCL runtime (CPU or GPU) to build and run (README build instructions
  require `libOpenCL`/vendor OpenCL SDK, `freeglut3-dev`, `libglew-dev`, Python 2.x headers for the
  macOS build path specifically — the README's macOS instructions reference `python2.7`, suggesting at
  least parts of the build tooling are old/Python-2-era and may need updating for a modern port).
- Validation (paper: Palyanov & Khayrulin et al., "Three-dimensional simulation of the Caenorhabditis
  elegans body and muscle cells in liquid and gel environments for behavioural analysis," *Phil. Trans.
  R. Soc. B* 373:20170376, 2018, PMC6158221) — this is the **best-documented quantitative validation
  table found across all candidates in this research**, read via PMC (Table 1, Figure 5 per the
  extraction, not independently cross-checked against the PDF directly so treat as medium-confidence):
  - Crawling (gel, ~10-100 mPa.s): **measured** velocity 0.1-0.3 mm/s vs **modelled/simulated** 0.13-0.15
    mm/s; measured wavelength/L 0.65 +/- 0.03 vs simulated 0.57-0.85; measured frequency 0.3 +/- 0.02 Hz
    vs simulated 0.27-0.41 Hz.
  - Swimming (low-viscosity liquid, ~1 mPa.s): measured velocity 0.29-0.38 mm/s vs simulated 0.26-0.41
    mm/s; measured wavelength/L 1.54-2.15 vs simulated 1.49-1.66; measured frequency 1.76-1.99 Hz vs
    simulated 1.75-1.79 Hz.
  - Figure 5: frequency-wavelength best-fit slope, simulation 0.59 vs "literature" 0.64 (derived,
    comparison of two fitted slopes).
  - Note for our swim-speed falsifier: our own dead-worm/own-rod work (per HANDOFF/recent commits) found
    swim speed failing at 0.164 vs 0.29 mm/s target — Sibernetic's own simulated swim range (0.26-0.41
    mm/s) brackets that 0.29 mm/s target, for what it's worth as an external sanity check.
- Caveat on speed/cost: SPH with a 3D particle body is **much more expensive per simulated second**
  than any of the rod models above (thousands of particles vs ~50-100 point masses) — good for
  high-fidelity cross-checks, not well suited to an inner fitting loop that needs many fast forward
  passes.

### B5. Other candidates noticed but not deeply explored

- `OpenSourceBrain/CelegansNeuromechanicalGaitModulation` fork/mirror relationship with
  `openworm/CelegansNeuromechanicalGaitModulation`: both exist, appear to hold the same content (see
  B1) — not a separate independent model.
- No other distinct public C. elegans body-dynamics codebase was found in the time available (e.g. no
  separate Fang-Yen-lab rod-model repo was found by search).

---

## Recommendation

**Port the Boyle-Berri-Cohen 2012 body model, using the Izquierdo/Beer `WormBody.cpp` reimplementation
as the reference for correctness, but reimplement the physics from the paper's own published equations
and Table 1/3 parameters (CC BY-NC) rather than copying either repo's code verbatim.**

Why:
- It is the only candidate that is both **fast** (point-mass/rod model, ~50-100 degrees of freedom,
  millisecond-scale timesteps, a full 24 s trial running in a small fraction of a second once compiled —
  the CE_locomotion README reports full evolutionary runs, i.e. many repeated trials, in about 2 minutes
  total) and has a **fully published, closed-form parameter set** (BBC 2012 Table 1 and Table 3 give
  every spring constant, damping constant, drag coefficient and muscle-force parameter needed to
  reproduce the model exactly, with units, no code required).
- It has at least partial **quantitative validation against real measurements**, directly in the primary
  paper: the frequency-wavelength curve (Figure 4, compared to Berri et al. 2009's gelatin/agar data),
  the curvature gradient (Figure 3), and the contact-force check (0.84 vs 2.5 uN, Section 3.4) — not as
  complete as Sibernetic's table, but real and citable.
- The Izquierdo/Beer reimplementation (`WormBody.cpp`) is useful as a clean, dependency-free C++
  reference to check a from-scratch port against (no SUNDIALS, no Boost, just a Makefile), and its code
  comments flag the exact two places it is known to deviate from BBC's original — useful for debugging a
  port, even if we don't copy it directly.
- Licensing is the weak point for *both* BBC's own repo (no LICENSE file at all) and the Izquierdo/Beer
  repo (explicit "All rights reserved" notice in the header). The safe route is to treat the BBC 2012
  **paper** (CC BY-NC, confirmed by reading the PDF) as the license basis, reimplement the documented
  equations ourselves for this non-commercial research project with attribution, and use both repos only
  as a correctness cross-check (run them locally, compare trajectories/curvatures, never redistribute
  their code). This keeps us on clearly licensed ground.
- Sibernetic is the better-validated option on paper (full measured-vs-simulated table for both gaits)
  and has a clean MIT license, but SPH is too expensive per-evaluation for a fitting loop that needs many
  forward passes; keep it in reserve as a high-fidelity cross-check once a cheap rod model is fitted, not
  as the primary fast body.
- MetaWorm/BAAIWorm (Part A) is Apache-2.0 licensed (good) and structurally interesting (true 3D FEM with
  96 muscles), but its own authors say the body's material constants are placeholders, not fitted to
  real C. elegans, and I could not find a quantitative speed/wavelength validation table for it (possibly
  it exists in the Nature SI, which I could not access) — too heavy a dependency stack (CUDA/Optix/Boost/
  NEURON) for a "fast for fitting" use case, and the validation evidence is currently weaker than BBC
  2012's or Sibernetic's. Worth revisiting the SI directly later, but not the pick for porting now.

---

## Open items / follow-ups if this matters later

- Nature SI PDF for the BAAIWorm/MetaWorm paper not read directly (paywalled); may contain a
  quantitative body validation table the preprint HTML text didn't surface.
- bioRxiv full-text fetch hit HTTP 429 repeatedly; a retry later could get a cleaner read than the
  auto-summarized version used here.
- Discrepancy between the repo's dt = 1/240 s (`Environment.cpp`) and the paper-text-extraction's "100 ms
  physical environment time step" is unresolved.
- Did not independently verify that `openworm/CelegansNeuromechanicalGaitModulation` and
  `OpenSourceBrain/CelegansNeuromechanicalGaitModulation` are byte-identical, only that the directory
  listings and top files match.
- Did not read Olivares/Izquierdo/Beer 2018 or 2021 papers directly for their own validation numbers
  (only found via search-result summaries).
- Did not find any data/code availability statement for Denham, Ranner & Cohen 2018 — worth a direct
  email to the authors if their Cosserat-rod code specifically is wanted.
