> **CORRECTION (Director, 2026-11-05):** this file misreads Ben's speed cap as "100x faster than real time". The cap is
> that the full model, body included, must be **no more than 100x SLOWER than real time** (and the fitting configuration
> no more than 10x slower). Read correctly: MetaWorm's projective-dynamics 3D body at about 1x real time (30 fps, as
> reported; not checked here) is well INSIDE the cap and is the lead 3D candidate; Sibernetic at ~7,000x slower (2014
> hardware) is outside it unless rebuilt. The rod-for-fitting recommendation stands; the "no 3D method clears the cap"
> conclusion does not.

# C. elegans body mechanics, environment mechanics and 3D/rod models: research note

Research note, not canon. Written to feed `docs/worm/PLAN.md` rows 21 ("Body") and 22 ("Environment") and
DECISION NEEDED 4 (the 3D body), without reopening those decisions: the plan has already adopted
*(decided 2026-11-05 00:59)* "try a Windows-native Sibernetic build first; if it fails, write the 3D body in
JAX, validated against Sibernetic's published results." This note supplies the numbers that decision needs:
what Sibernetic actually validated (so there is a concrete target), what it costs (so the 100x/10x bars can be
checked against evidence, not guesses), and what else exists. Labels as elsewhere in this project's worm docs:
**measured** (reported directly in a cited source), **derived** (arithmetic on measured numbers, shown),
**inferred** (taken from a source by reasoning), **guessed** (no direct basis). Compiled 2026-11-05.

## 1. Measured body mechanics

**Geometry.** Embryo about 40 um long, 25 um diameter. L1/L2 larvae 250-350 um long. Young adult hermaphrodite
about 1 mm long, about 60-80 um diameter at mid-body (measured, [WormAtlas introduction](https://www.wormatlas.org/hermaphrodite/introduction/mainframe.htm);
[community.alliancegenome.org body-size thread](https://community.alliancegenome.org/t/whole-worm-volume-c-elegans-body-size-egg-size/2847)).
Volume grows from about 2x10^4 um^3 (embryo) to about 3x10^6 um^3 (adult) (measured/derived, same sources). A
2021 high-resolution growth study measured length, width and volume at every hour from L1 to adult and found
volume stays continuous through larval moults while length and width trade off at each stage transition
(measured, [Highly scaled measurements of C. elegans development, bioRxiv 2021](https://www.biorxiv.org/content/10.1101/2021.04.01.438121v2.full)).
Radius is not constant along the body: it tapers at head and tail: the existing Virtual Worm geometry
(PLAN.md row 2, inferred/reconstructed) is the only local source with a full radius-vs-arclength profile; no
stage-resolved radius profile beyond mid-body diameter was found in this pass.

**Cuticle and tissue stiffness: techniques disagree by 2+ orders of magnitude, and the disagreement is explained
by which layer and loading geometry each technique probes, not by inconsistent biology.**
- **AFM point indentation** (local, cuticle-only): 8-2000 kPa (measured range across studies,
  [Essmann et al., AFM health biomarkers, Nature Communications 2020](https://www.nature.com/articles/s41467-020-14785-0)).
  If all elasticity is attributed to the thin cuticle shell alone (rather than a cuticle-plus-pressurized-core
  model), the implied cuticle modulus rises to 200-400 MPa (derived from the same indentation data under that
  assumption, same source).
- **Whole-body bending** (the worm as a uniform viscoelastic rod): bending experiments across a range of
  bending speeds give an effective "worm material" modulus of 110 +/- 30 kPa, with a damping coefficient that
  falls as a power law over two decades of bending speed -- shear-thinning, non-Newtonian, better fit by a
  Maxwell model than Kelvin-Voigt or elastic beam theory (measured,
  [Backholm, Ryu & Dalnoki-Veress, viscoelastic properties of C. elegans, PNAS 2013](https://www.pnas.org/doi/10.1073/pnas.1219965110)).
  A separate bending-moment analysis of the swimming gait gives a lower whole-body estimate, about 3.77 kPa
  (measured, cited in the AFM review above) -- these whole-body numbers sit far below AFM's cuticle-only range
  because bending a hydrostatic-skeleton body is dominated by the pressurized core, not the cuticle.
- **Layer-resolved finite-element inversion**: fitting a multi-compartment FE model (cuticle shell, muscle
  layer, pseudocoelom core) to combined indentation/pressure data converges on cuticle 75-140 kPa, muscle
  600-850 kPa (individual-worm variation 910-2,100 kPa), pseudocoelom 48-185 kPa (variation 42-275 kPa)
  (measured/fitted,
  [Frontiers in Bioengineering and Biotechnology 2024](https://www.frontiersin.org/journals/bioengineering-and-biotechnology/articles/10.3389/fbioe.2024.1335788/xml/nlm)).
  A related 2023 in-silico study varies internal pressure and neuromuscular agents over the same kind of
  multi-compartment model (measured/derived,
  [bioRxiv 2023.11.09.566289](https://www.biorxiv.org/content/10.1101/2023.11.09.566289v1.full)).
  *Correction (7 Nov 2026, 19:13, wranges):* a 6 Nov night note (wbody) said the model counts muscle stiffness
  twice, once in this muscle modulus and again in MetaWorm's muscle fibre constraints. wmodel's 7 Nov audit of the
  code found it does not: the fibre constraints add active force, not passive stiffness. The model's body is 7.8x
  stiffer in bending than Backholm 2013's whole-worm 110 +/- 30 kPa because of these published layer moduli
  themselves: their area-weighted section modulus is 856 kPa (derived; 856/110 = 7.8), the core (840 kPa, set by
  pressure) carries about 65% of it, and the FEM's own effective bending modulus is 676 kPa (derived), 6.1x the
  middle of the measured 50-170 kPa.
- **Direct bulk pressurization**: applying isotropic pressure directly shows the bulk mechanical response is
  largely **independent of the cuticle** -- i.e. the worm behaves as a pressurized hydrostatic skeleton, and
  cuticle stiffness is a minor contributor to whole-body stiffness (measured,
  [Worms under Pressure, Biophysical Journal 2015](https://www.cell.com/article/S0006-3495(15)00281-7/fulltext)).
  This is the mechanistic reason the other three techniques disagree: AFM indentation at micron scale loads the
  cuticle in a geometry where it dominates the local response; whole-body bending and pressurization load the
  pressurized core, where the cuticle barely matters. **A 3D model needs both a cuticle shell term and a
  pressure-dominated core term; a single bulk modulus cannot reproduce all four kinds of measurement at once.**

**Internal hydrostatic pressure.** A piezoresistive microcantilever study modelled the worm as a hollow
cylindrical shell under internal pressure to back out modulus and pressure together (measured/derived,
[Park et al., PNAS 2007](https://www.pnas.org/doi/10.1073/pnas.0702138104)). Reported ranges across sources
found in this pass span roughly 50-100 kPa (older estimates) to 150-200 kPa (newer FE-based estimates, Frontiers
2024 / bioRxiv 2023 above); internal organ tissue pressure (e.g. the gonad) is much lower, 2-30 kPa. The spread
here has the same character as the stiffness spread: not independently re-measured in this pass to resolve which
number is current best estimate; flagged **measured but unreconciled across sources**, a gap for the body
layer's own fitting step (PLAN.md row 21), not something to resolve by literature reading alone.

**Muscle force and arrangement.** 95 body-wall muscle (BWM) cells in **4 longitudinal quadrants** flanking the
dorsal and ventral nerve cords: dorsal-left (DL) and dorsal-right (DR) flank the dorsal cord, ventral-left (VL)
and ventral-right (VR) flank the ventral cord; DL, DR and VR each have 24 cells, VL has 23 (measured,
[WormAtlas, Somatic Muscle](https://www.wormatlas.org/hermaphrodite/musclesomatic/MusSomaticframeset.html);
[WormBook, body wall muscle](https://www.wormbook.org/chapters/www_bodywallmuscle/bodywallmuscle.html)). Within
each quadrant, cells form two interlocking longitudinal rows (proximal to the cord, distal from it), each cell
obliquely striated and rhomboid-shaped. Dorsoventral bending requires dorsal cells to contract while their
ventral counterparts relax (and vice versa), driven antagonistically through the D-type (inhibitory) motor
neurons -- the mechanism, not a force number. Several downstream models (Sibernetic, MetaWorm) report **96**
muscles rather than 95 -- a small, unresolved discrepancy against the WormAtlas anatomical count, flagged
**inferred (rounding or a counting-convention difference), not reconciled in this pass**. Force itself is
characterised through fitted Hill-type length-force / velocity-force relations (Boyle & Cohen; Du/Crodelle 2024
whole-cell muscle model, cited in PLAN.md row 12 and STATE_OF_THE_ART.md s1), not a single reported absolute
force-per-muscle number; no consolidated newton-scale figure was located in this pass, and it should be treated
as **fitted within bounds**, consistent with the plan's own row 12 treatment, not looked up.

**Damping and mass density.** Damping is non-Newtonian: a power-law, shear-thinning function of bending speed
over two measured decades (measured, Backholm 2013 above) -- a fixed linear (Kelvin-Voigt) damping coefficient
is a known-wrong simplification, useful only as the "deliberately wrong" control the plan's falsifier rule
(DECISIONS item 2) already asks for. Body mass density is measured at 1.07-1.08 g/cm^3 by density-gradient
centrifugation (measured,
[Shifts in the Distribution of Mass Densities, PLOS ONE 2013](https://journals.plos.org/plosone/article?id=10.1371%2Fjournal.pone.0069651)),
modestly above the water density (1.00 g/cm^3) many simpler models assume for buoyancy/inertia terms.

## 2. Environment mechanics

**Swimming in buffer.** Reynolds number is well below 1: using measured swim speeds of 0.17-0.45 mm/s, body
length about 1 mm, and buffer viscosity near that of water, Re is about 0.1-0.4 (measured/derived,
[Sznitman et al., material properties at low Re, arXiv 0911.1731](https://arxiv.org/html/0911.1731);
[Flow analysis of the low-Reynolds-number swimmer C. elegans, arXiv 1602.05381](https://arxiv.org/pdf/1602.05381)) --
inertia is negligible; drag dominates, consistent with resistive-force-theory and Stokes-flow treatments being
appropriate for the fluid phase.

**Crawling on agar.** The worm crawls inside a thin fluid film at the agar surface, not in dry contact with the
gel; direct force measurement finds very large, anisotropic surface drag: normal and tangential drag
coefficients of about 220 and 22 (arbitrary units of that study), a normal-to-tangential ratio of about 10
(measured,
["Direct Measurements of Drag Forces in C. elegans Crawling Locomotion"](https://www.researchgate.net/publication/267159452_Direct_Measurements_of_Drag_Forces_in_C_elegans_Crawling_Locomotion)).
**Reported anisotropy ratios disagree by about an order of magnitude across studies, 1.5-40 for gelatin/agar
estimates by resistive-force fits, versus a Gray-Hancock theoretical value of 2 for a thin filament in a purely
Newtonian fluid, with some agar-specific estimates as high as about 110** (measured range, same source and
["Undulatory locomotion of C. elegans on wet surfaces", arXiv 1112.1118](https://arxiv.org/pdf/1112.1118)). As
with stiffness, the spread tracks the technique: pure-fluid RFT (ratio about 2) under-predicts agar's resistance
because the gel's elastic/frictional (not purely viscous) contact adds anisotropic resistance RFT does not
model; direct force measurement and gait-inversion fits, which include that contact, give the larger, more
variable ratios actually needed to reproduce crawling wavelength.

**Viscoelastic gels and the swim-crawl transition.** Across a gelatin-concentration series spanning the
swim-to-crawl range, locomotion is a smooth, single-gait continuum, not two discrete gaits: frequency falls and
curvature amplitude rises continuously with viscosity, and it is lateral drag delaying *bending propagation*
(not a change in neural actuation pattern) that sets the crawling wavelength -- i.e. body mechanics, not neural
re-programming, explains the gait transition (measured,
[Berri et al. 2009, summarised via PMC3296079](https://pmc.ncbi.nlm.nih.gov/articles/PMC3296079/);
[Fang-Yen et al. 2010, PNAS](https://www.pnas.org/doi/full/10.1073/pnas.1003016107)). This is the mechanistic
reason Boyle & Cohen's purely-mechanical rod model (section 3) reproduced the transition without a detailed
neural model of it.

**Gait kinematics vs. viscosity (Fang-Yen 2010, Table 1, measured):**

| Quantity | Swimming (buffer) | Crawling (agar) |
|---|---|---|
| Wavelength (lambda/L) | 1.54 +/- 0.04 | 0.65 +/- 0.03 |
| Frequency (Hz) | 1.76 +/- 0.07 | 0.30 +/- 0.02 |

Frequency falls monotonically and curvature amplitude rises monotonically with viscosity between these two
endpoints (measured, same source); frequency approaches an asymptote near 1.7 Hz at the low-viscosity
(swimming) end. Later work (Sibernetic's own validation, section 3) reports a wider experimental swim/crawl
range (wavelength 0.48-0.65 crawling, 1.54-2.15 swimming; frequency 0.3-0.49 crawling, 1.76-1.99 swimming) --
consistent with Fang-Yen's numbers but drawn from a different, slightly wider, animal-to-animal sample.

**3D burrowing and reorientation.** In 3D media (gel pores, bead/pillar arrays) the worm adds roll maneuvers to
its planar dorsoventral bend, generating out-of-plane turns not seen on a 2D agar surface (measured,
[Roll maneuvers are essential for active reorientation in 3D media, PNAS 2017](https://www.pnas.org/doi/10.1073/pnas.1706754115);
[Navigation of C. elegans in three-dimensional media, arXiv 1609.03452](https://arxiv.org/pdf/1609.03452)). This
is a real mode the rod model (section 3/4) needs if 3D burrowing behaviours are in the scored corpus: a planar
(2D) Cosserat rod cannot represent roll; a 3D rod (full orientation along arclength, as in Denham/Ranner/Cohen,
section 3) can.

## 3. Models

**Sibernetic (SPH; PLAN.md's "Sibernetic row").** Smoothed-particle hydrodynamics (PCISPH), body-wall muscle
modelled as contractile matter, body plus surrounding fluid/gel represented as particles (measured/described,
[Palyanov et al., three-dimensional simulation of body and muscle cells, Phil. Trans. R. Soc. B 2018](https://pmc.ncbi.nlm.nih.gov/articles/PMC6158221/)).
**Particle count:** 500,000 particles (full-resolution swimming model), 81,000 particles (half-resolution
swimming model) in the 2018 paper (measured); an earlier 2014 development-era build used about 150,000-232,000
particles (measured, [GitHub openworm/OpenWorm#74](https://github.com/openworm/OpenWorm/issues/74)). 96 muscles
in 4 quadrants, 24 cells each (measured, same 2018 paper -- the "96 vs 95" discrepancy noted in section 1).
**Validation (measured, same 2018 paper):**

| Quantity | Experimental | Simulated |
|---|---|---|
| Crawling speed | 0.1-0.3 mm/s | 0.13-0.15 mm/s |
| Swimming speed | 0.29-0.38 mm/s | 0.26-0.41 mm/s |
| Crawling wavelength (lambda/L) | 0.48-0.65 | 0.57-0.85 |
| Swimming wavelength (lambda/L) | 1.54-2.15 | 1.49-1.66 |
| Crawling frequency (Hz) | 0.3-0.49 | 0.27-0.41 |
| Swimming frequency (Hz) | 1.76-1.99 | 1.75-1.79 |

This table is the concrete target the plan's DECISION 4 needs for "validated against Sibernetic's published
results" -- whatever body (rod or a JAX port) replaces or cross-checks Sibernetic should be scored against these
six rows, not just "looks like a worm." **Speed:** no modern (RTX-class) benchmark was found. The only
wall-clock numbers located are from 2014 development discussion on then-current hardware (a laptop GPU, GT
650M, and a Pitcairn-class AMD GPU): per-step costs from about 53 ms up to tens of seconds, and one estimate of
**about 2 hours of wall time per 1 simulated second** on the hardware of that era (measured/estimated at the
time, [GitHub openworm/OpenWorm#74](https://github.com/openworm/OpenWorm/issues/74)) -- roughly 7,000x *slower*
than real time, let alone the project's 100x-*faster*-than-real-time cap. This is old hardware and an
unoptimised build, so it is not a clean estimate for an RTX 4070 Ti SUPER, but it is the only measured Sibernetic
speed found, and it is consistent with PLAN.md's own "not measured" and "did not link in WSL" status (row 106).

**Boyle, Berri & Cohen (2008-2012), low-DOF viscoelastic rod + simple muscle.** Body-wall muscle as a low-pass-
filtered actuator driven directly by the known motor-neuron innervation pattern (not channel-level biophysics);
body as a viscoelastic rod in fluid. Quantitatively reproduced gait kinematics and the measured swim-crawl
transition (described in STATE_OF_THE_ART.md s1,
[Boyle, Berri & Cohen 2012, Frontiers in Comp. Neuroscience](https://www.researchgate.net/publication/221694495_Gait_Modulation_in_C_elegans_An_Integrated_Neuromechanical_Model)).
No wall-clock speed was published; given its low state count (a handful of bend-angle-like variables per body
segment, no fluid particles), it is **inferred** to be cheap -- the same order as the plan's own K1 guess for
the rod (section a, row 21), not independently measured here.

**Denham, Ranner & Cohen (2018) and descendants: full 3D geometrically-exact Cosserat rod.** Models a filament's
position and orientation along arclength, so it carries bending, twisting, stretching, shear, self-contact,
friction and hydrodynamic coupling, used to find "signatures of proprioceptive control" in locomotion
(described,
[Denham, Ranner & Cohen, Signatures of proprioceptive control, eprints.whiterose.ac.uk](https://eprints.whiterose.ac.uk/id/eprint/137534/1/DenhamRannerCohen18.pdf)).
A 2017 companion gives "A new computational method for a model of C. elegans biomechanics" with elasticity and
locomotion-performance results
([arXiv 1702.04988](https://arxiv.org/pdf/1702.04988)), and a later "monolithic optimal control" extension fits
the rod's displacement to reconstruct observed locomotion
([Computational Mechanics 2023](https://eprints.whiterose.ac.uk/id/eprint/193415/12/s00466-022-02247-x.pdf)).
**This is the closest published match to the plan's "fast Cosserat rod in JAX" plan item**: it is the right
representation (3D, so it can carry the roll/3D-burrowing mode section 2 flags as needed, not just a planar
bend) and the right physics (hydrodynamic coupling and self-contact already built in as terms, so a JAX port
mainly needs to re-derive these as differentiable functions, not invent new physics). No GPU/JAX port or
wall-clock speed was found; general Cosserat-rod software (PyElastica) reports that its cost scales *linearly*
with the number of nodes along the rod (unlike FEM's cubic scaling), and that it is the fastest of several
compared soft-body libraries in a rollout benchmark
([PyElastica](https://www.cosseratrods.org/software/pyelastica/); [SoRoMoX, arXiv 2608.06650](https://arxiv.org/html/2608.06650v1)) --
supporting the plan's K1 cost-class guess for a rod, though not a worm-specific number.

**Resistive-force theory (RFT) and slender-body theory (SBT).** RFT: local drag per unit length is linear in
local velocity, split into tangential and normal coefficients C_t, C_n (classically C_n/C_t = 2 for a thin
filament in Newtonian fluid), C_n = 4*pi*mu / [ln(lambda/r) + 1/2] (measured/theoretical,
[Gray & Hancock, reviewed via ScienceDirect Slender Body Theory overview](https://www.sciencedirect.com/topics/engineering/slender-body-theory);
[Theoretical models in low-Re locomotion, arXiv 1410.4321](https://arxiv.org/pdf/1410.4321)). This is accurate
for the swimming (buffer) phase (section 2's Re << 1 regime) but, as section 2 showed, under-predicts agar's
anisotropy by up to an order of magnitude unless its coefficients are replaced with measured, substrate-specific
ones (Fang-Yen 2010; the "Direct Measurements of Drag Forces" paper). RFT/SBT are the natural drag law for the
rod path (K1, cheap, no fluid mesh), with coefficients swapped by medium (buffer vs. agar vs. gel) rather than
derived from a single universal formula.

**FEM approaches.** Two local modes found. (a) *Static/quasi-static inverse FE models* (section 1's Frontiers
2024 and bioRxiv 2023 papers) fit layered moduli to indentation/pressure data; these are not dynamic locomotion
simulators and no speed figure applies. (b) *Dynamic, muscle-driven FE body*: the MetaWorm/eworm body uses a
tetrahedral mesh (3,341 tetrahedra) driven by 96 muscle actuators, solved with "projective dynamics" rather than
standard (stiff, small-timestep) FEM, reported to run at **real-time, 30 frames per second**, and to have cut
per-step solve cost from about 4.17 ms to about 0.02 ms per step by moving to this solver (measured,
[MetaWorm / An integrative data-driven model, Nature Computational Science 2024](https://www.nature.com/articles/s43588-024-00738-w)).
No GPU model was specified in the sources found in this pass (**inferred**: likely a single consumer-class GPU,
not stated). This is the fastest demonstrated full 3D deformable worm body in the literature surveyed, and it
reached only about 1x real time, not 100x -- see section 4.

**GPU / differentiable soft-body solvers.** None found with a published worm-specific benchmark; all are
general frameworks that would need a worm body built on top. NVIDIA Warp: Python-JIT GPU kernels with FEM/XPBD/
MPM solvers shipped as examples, designed for RTX-class hardware; no worm case found. Taichi/DiffTaichi:
differentiable soft-body/MPM simulation, reports up to about 1,500x GPU-vs-naive-CPU speedups in its own
benchmarks (general claim, not worm-specific,
[DiffTaichi, arXiv 1910.00935](https://arxiv.org/pdf/1910.00935)). JAX-MD: differentiable molecular-dynamics
framework reported to scale to "hundreds of thousands of particles on one GPU"
([JAX, M.D., arXiv 1912.04232](https://arxiv.org/html/1912.04232v2)) -- a general MD claim; it ships no SPH or
tissue-mechanics kernel, so a worm body in JAX-MD would mean writing an SPH or FEM kernel inside it, at which
point it is really "write the 3D body in JAX" (the plan's own fallback) using JAX-MD's neighbour-list machinery
as a starting point rather than a ready-made worm solver.

## 4. Recommendation

**No published method has been shown to run a full 3D deformable worm body at 100x real time, on any hardware.**
The fastest demonstrated full 3D dynamic body (MetaWorm's projective-dynamics tetrahedral FE mesh, 3,341
elements, 96 muscles) reaches about 1x real time (30 fps) (measured, section 3); Sibernetic's only measured
speed, on 2014-era hardware, was about 7,000x *slower* than real time (measured, section 3). A first-principles
check points the same way: explicit SPH at a particle count fine enough to resolve the 4-quadrant muscle
geometry (tens of thousands of particles, per Sibernetic's own 81K-500K) needs a stability-limited timestep far
below 1 ms; even assuming optimistic (10% of peak) utilisation of an RTX 4070 Ti SUPER's 44.1 TFLOPS FP32, 672
GB/s bandwidth (measured vendor spec,
[TechPowerUp RTX 4070 Ti SUPER](https://www.techpowerup.com/gpu-specs/geforce-rtx-4070-ti-super.c4187)), a
40-neighbour SPH step at tens of thousands of particles and realistic step counts per biological second lands
3-4 orders of magnitude short of the 0.01 wall-s-per-bio-s that 100x demands (derived, not independently coded
and timed in this pass -- a bound, not a benchmark).

**Recommendation: decouple the 100x cap from the 3D body, exactly as PLAN.md's own cost-class table already
implies (K3, "dominant and separate").** Concretely:
1. **The rod carries the 100x (run) and 10x (fit) bars.** A 3D, geometrically-exact Cosserat rod in the style of
   Denham/Ranner/Cohen (2018), ported to JAX so it shares Jaxley's autodiff and batching path, is the right
   choice: it is the fastest body representation found (linear, not cubic, scaling in nodes; PyElastica's own
   benchmark already names it the fastest of several compared libraries), it is 3D (so it can carry the roll/
   burrowing mode section 2 needs, not just a planar bend), and its physics (hydrodynamic drag via RFT/SBT with
   medium-swapped coefficients, section 2 and 3) is exactly what the plan's row 22 ("resistive-force or
   slender-body drag for the rod path") already calls for. Cost is **inferred** to sit near the plan's own K1
   guess (under about 10% of the neuron-membrane cost), consistent with its low state count; this should be
   measured directly once coded, the same way the neuron membrane was (PLAN.md section c.5), not assumed.
2. **The 3D body (whichever of Sibernetic-native, or a JAX/Warp port) is not held to 100x.** It is a periodic
   cross-check (PLAN.md's W8 stage), not the per-step engine: it needs to run a batch of held-out episodes fast
   enough to be practical overnight or over a weekend, not in the hot loop. Given MetaWorm's ~1x-real-time
   result on a tetrahedral mesh of a few thousand elements is the best demonstrated number, and given Jaxley's
   own batching result (32 independent copies cost barely more than 1 copy per step, PLAN.md section c.5) is
   the template for getting throughput from parallel episodes rather than a faster single copy, a coarse
   (roughly 1,000-5,000-element) tetrahedral or SPH-lite body solved with a large-timestep implicit scheme
   (projective dynamics / XPBD, as in Warp's shipped solvers) and run as a batch of parallel episodes on the
   RTX 4070 Ti SUPER is the most plausible path to a *useful* (not 100x, but tractable) 3D cross-check cost --
   **guessed** at perhaps 1-10x real time per copy with tens of copies batched, pending an actual measurement
   exactly like the one the neuron layer already did.
3. **If the Windows-native Sibernetic build (DECISION 4's first step) succeeds**, section 3's validation table
   (crawl/swim speed, wavelength, frequency, six rows, all measured against real worms already) is the
   off-the-shelf target for "validated against Sibernetic's published results" the decision calls for -- no
   further literature work is needed to define that bar.
4. **Validation tests tying the rod and the 3D body together (for W8):** (a) reproduce section 2's Fang-Yen
   Table 1 (wavelength, frequency vs. medium) and Berri's gait-transition continuum independently in both the
   rod and the 3D body, and require both to land within the same measured animal-to-animal spread (PLAN.md's
   own falsifier-with-a-wrong-control rule, DECISIONS item 2); (b) drive both models with the same prescribed,
   non-fitted muscle-activation waveform (bypassing the neural layer entirely) and compare resulting curvature-
   vs-phase and bend-propagation velocity, so any disagreement is attributable to the body model alone, not to
   upstream neural differences; (c) where the two disagree, treat the 3D body as the reference (as PLAN.md's W8
   row already states), and treat the disagreement itself as the measured size of the rod's approximation error
   for that behaviour -- not as an undifferentiated prior.
