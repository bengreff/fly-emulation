# OpenWorm Sibernetic: what it adds to the MetaWorm body, and the port plan

Body worker, 2026-11-05 16:26 CST. Ben 15:30: the body is MetaWorm's 3D tetrahedral body; use OpenWorm
Sibernetic's muscle and body definitions where they add detail, and port its mechanisms heavily.

Source: `openworm/sibernetic` (GitHub, default branch, shallow clone read on 5 Nov by a survey agent and then
deleted), MIT licence (`LICENSE`, and MIT headers on the source files). Paper: Palyanov, Khayrulin & Larson 2018,
Phil Trans R Soc B 373:20170376. File and line references below are to that clone. The paper numbers were read
from PMC by the survey agent, not from the repo; **check them against the paper before any of them is used as a
target**.

## Verdict

Sibernetic is a different kind of body: a particle simulation (PCISPH) of the worm, the liquid and an agar gel
together, not a finite-element mesh. Its whole solver cannot be dropped into MetaWorm. What ports are its
mechanisms and numbers. Four add detail MetaWorm lacks:

1. **Internal pressure.** Sibernetic traps liquid inside the cuticle shell, so the body is a pressurised tube.
   MetaWorm has no pressure (ledger MB10, `body.pressure`).
2. **A force-type muscle with a physical maximum force.** Sibernetic's muscle pushes with activation x Fmax along
   each muscle spring, whatever its length. MetaWorm's muscle is a spring pulling the fibre toward (1 - a) of its
   current length, with an arbitrary stiffness 5E5.
3. **Gravity and an agar gel substrate.** Sibernetic has both; MetaWorm has neither (MB6).
4. **Validation numbers** for crawling and swimming from the same model.

Two things the survey called added detail are not: muscle count and layout are the same (4 quadrants x 24, same
MDR/MVR/MDL/MVL names, 96 slots against biology's 95), and the "two stiffness tiers" in Sibernetic are worm
tissue against agar gel, not cuticle against inner tissue. Sibernetic has one worm material. So it does not fill
the cuticle / muscle layer / pseudocoelom moduli in our ledger (MB2); those stay literature placeholders.

## What Sibernetic defines (survey, file:line in the clone)

| mechanism | Sibernetic | MetaWorm (ours, published) | adds detail? |
|---|---|---|---|
| body solid | particles, 3 types (liquid 1, elastic 2, boundary 3), `inc/owOpenCLConstant.h:41-43`; `configuration/worm`: 169,397 particles (76,446 liquid, 4,867 worm elastic, 5,276 agar, 82,808 boundary; counted) | corotated FEM, 984 vertices, 3341 tets, E 2E5, nu 0.4 | different method |
| elastic links | up to 32 springs per particle, rest length stored, `src/owHelper.cpp:316-330`; force -(r_ij - r0) x elasticityCoefficient, worm-worm full, any agar pair x0.25, `src/sphFluid.cl:668-740` | one homogeneous material | no for the body (one worm material); yes for agar |
| internal pressure | membrane triangles keep the SPH liquid inside the shell, so real SPH pressure pushes out, `src/sphFluid.cl:1113-1295` | none | **yes** |
| muscles | `MUSCLE_COUNT = 96`, `src/owConfigProperty.cpp:39`; MDR/MVR/MVL/MDL 01-24, `main_sim.py:12-50` | 4 x 24 fibre strings, same names | same |
| muscle to tissue | each spring carries one muscle id (hard assignment), `src/sphFluid.cl:732-740` | each tet weighted by distance to the fibre, exp(-d/0.005) | small (a diagnostic) |
| activation -> force | accel += -r_hat x a x max_muscle_force when a > 0; max_muscle_force 4000 program units, `inc/owPhysicsConstant.h:217`; paper: about 2.7e-9 N, against an estimate of 1.4-9.6e-9 N for real muscle (paper, unchecked; not yet clear whether per spring or per muscle) | projection target p0 = (1 - a) F d, stiffness 5E5 x weight (`sim/fem/Constraint/LinearMuscleConstraint.cpp:167`) | **yes**: a physical force scale |
| activation source | travelling sine (`main_sim.py:56-120`) or c302 / NEURON, updated every physics step | key file at 30 Hz | ours goes per physics step in closed loop anyway |
| time step | 2.0e-5 s (`inc/owPhysicsConstant.h`) | 1/240 s | n/a |
| liquid | PCISPH, rho0 1000 kg/m3, 3 pressure iterations, Ihmsen 2010 boundaries | quadratic drag and lift per surface triangle | **yes** (a real liquid), but not portable into FEM |
| gravity | on, -9.8 m/s2 (`inc/owPhysicsConstant.h:175`) | off | **yes** |
| agar | second elastic particle material, 0.25 x worm stiffness, higher particle viscosity (`src/sphFluid.cl:580-606`) | none | **yes** |

Unreconciled: the particle mass comment says "0.8 mm worm", but the scale factor gives about 2.5 mm for this
configuration file (derived by the survey agent). Sibernetic ships several rescaled variants; which one the paper
used is not checked.

## Validation numbers (Palyanov 2018, from PMC via the survey; unchecked)

| readout | Sibernetic | experiment as cited by the paper |
|---|---|---|
| crawl speed | 0.13-0.15 mm/s | 0.1-0.3 mm/s |
| swim speed | 0.26-0.41 mm/s | 0.29 +/- 0.03 to 0.38 +/- 0.02 mm/s |
| swim frequency | 1.75-1.79 Hz | 1.76 +/- 0.07 Hz |
| swim wavelength / L | 1.49-1.66 | 1.54 +/- 0.04 |

Sibernetic's frequency and wavelength largely come from its prescribed sine drive, so they are inputs, not
results. Its swim speed is a result, and it falls inside the experimental range our P3 test uses (0.29-0.45 L/s
for a 1 mm worm). Our ported body gives 0.018 L/s under the same drive. These are calibration targets already in
`BODY_TESTS.md`, not held-out data.

## Port plan (each a toggle; neutral = the published MetaWorm body)

In order of what they fix:

1. **`body.scale = worm_1mm` plus `env.fluid = viscous_rft_water`** (already planned). Sibernetic's own swim at
   Re of 0.05 or less is the reason: a worm swims in the viscous regime, and MetaWorm's metre-scale world is
   inertial (Re about 7,300). Resistive-force drag is the cheap FEM version of what Sibernetic gets from its
   particle liquid. The PCISPH liquid itself is not ported (a different solver, and costly).
2. **`muscle.force_model = sibernetic_force`.** Add a muscle term of size a x Fmax along each fibre segment,
   length independent, beside the published (1 - a) target-length constraint. In projective dynamics a constant
   force goes into the external force (right-hand side), so the prefactored solve is unchanged. Fmax per muscle
   is a ledger row: Sibernetic's value labelled published, the 1.4-9.6e-9 N estimate as the range, once both are
   checked in the paper. A Hill force-length option stays a separate choice of the same toggle (literature).
3. **`body.pressure = volume_constraint`.** Sibernetic's mechanism (trapped liquid) as the FEM equivalent: a
   volume-preservation constraint on the body's inner tets at a set pressure (projective dynamics has a standard
   volume constraint). Pressure value: the ledger's guessed 100 kPa (50-200), MB10. This is a port of the idea,
   not the code; labelled so.
4. **`env.substrate = agar_plate`** with gravity on. Sibernetic models agar as a soft elastic gel; for a 2D
   plate our planned route is resistive-force drag with agar coefficients (Ct, Cn already in the ledger, MB5)
   plus gravity and a contact plane. Sibernetic's 0.25 gel stiffness ratio is recorded as a published
   alternative for a deformable gel, not used first.
5. **Hard muscle ids per tet** (diagnostic only, no toggle): store each tet's main muscle so the viewer and the
   strain readout can name which muscle a tet belongs to, as Sibernetic does per spring.

Licence: MIT, compatible. ADOPTED.md gets a row when the first of these lands.
