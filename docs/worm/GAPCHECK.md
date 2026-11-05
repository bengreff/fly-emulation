# Gap-junction coupling solved with the cable: pre-registration and results

Why: Jaxley 0.14 integrates an ohmic gap junction written as a synapse fully explicitly, which blows up on
strongly coupled cells; a half-implicit patch is stable but slows coupled cells' common relaxation by about
1 + a (FINDINGS F-W0-5). Every network fit needs a coupling that is both stable and accurate.

## Pre-registration (written 2026-11-05 00:56 CST, before any code for it ran)

**Method under test: `ImplicitGap`** (`src/bioemu/jx_gap.py`). The gap conductances go into the same
backward-Euler system as the cable and the membrane, so the step solves (M + dt G) v = rhs, where M is
Jaxley's own matrix (cable, membrane and synapse slopes) and G is the gap-junction Laplacian. It uses Jaxley's
tree solver plus an exact low-rank correction (Woodbury identity) over the compartments that carry junctions:
one extra tree solve per junction site per cell, one dense solve the size of the set of junction compartments,
and one more tree solve. In exact arithmetic this is the same scheme as NEURON's fully implicit coupling with a
`LinearMechanism`, so the two should agree to rounding at the same step.

**Reference.** NEURON 9.0.2 on backhouse, the same cells, gap junctions as a `LinearMechanism` (fully implicit),
backward Euler (`secondorder = 0`), same dt, float64 in both. Error = max over every compartment and every time
point of |v_Jaxley - v_NEURON|, index-aligned as in `check_port.py`.

**Cases.**
- **P, coupled pair:** two passive single-compartment cells (radius 1 um, length 10 um, 1 uF/cm2, leak 1e-4
  S/cm2 at -70 mV, so 0.628 pF each), coupled both ways at g = 0.1, 1 and 10 nS; 1 pA into cell 0 from 10 to
  60 ms; 100 ms. a = dt g / C reaches 6.4 at 10 nS and dt 0.4 ms.
- **C, strongly coupled chain:** 8 active cells in a line. Each is one branch of 3 compartments (radius 1 um,
  length 30 um, Ra 100 ohm cm, 1.6 uF/cm2) with the published Nicoletti 2024 AIY membrane at its published
  densities (uniform per area; E_Ca pinned at 60 mV as in the port check). Junctions join compartment 2 of cell k
  to compartment 0 of cell k + 1, at g = 1 and 20 nS (a = 2.0 at dt 0.1 ms and 8.0 at 0.4 ms for 20 nS; each
  compartment about 1.0 pF). 15 pA into cell 0, compartment 0, from 10 to 60 ms; 100 ms; v_init -65 mV.
- Both step sizes: dt 0.1 ms (the network bench) and 0.4 ms (the spike).

**Bars.**
- **B1 (accuracy against NEURON):** `ImplicitGap` error <= 0.01 mV in every P and C case at both step sizes.
- **B2 (cable control):** the chain with g = 0 matches NEURON to <= 0.01 mV at both step sizes. If B2 fails,
  the C results are reported but do not count as evidence about the gap junctions.
- **B3 (gradient):** the gradient of a scalar loss (mean squared soma voltage of the last cell in C at 20 nS,
  dt 0.1 ms) with respect to the gap conductance is finite and matches a central finite difference to 1e-4
  relative (float64).
- **F1 (control that must fail):** the explicit form (`ExplicitGap`, Jaxley's default behaviour) must fail B1,
  by more than 0.01 mV or by blowing up, in at least the strongest P case and the strongest C case. If it
  passes there, the test is uninformative and no adoption follows.
- **F2 (second control, reported):** the half-implicit `Gap`, expected to fail B1 at a > 1.

**Reported, not bars:** the error of `ImplicitGap` against a converged reference (NEURON at dt 0.001 ms), the
NEURON-only steady state against the analytic value for P, the cost per step against the explicit form on the
446-cell bench, and whether the 1.5x bench network stays in range with a finite gradient.

**Adoption gate.** B1, B2 and B3 pass, F1 fails, and the comparison figure is viewed: then `ImplicitGap` becomes
the gap-junction form for network fits, recorded in DECISIONS. Otherwise nothing is adopted and the failure is
the result.
