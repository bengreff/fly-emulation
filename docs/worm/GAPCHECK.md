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

## Runs before any score, and the scored run `gapcheck1` (written 2026-11-05 01:10 CST)

Two harness defects were found and fixed before the first run that implements the cases as written above. Neither
changed a case, a bar or a tolerance; both logs are kept in `data/worm/gapcheck/`.

- **Run 0 (invalid reference).** The NEURON `LinearMechanism` was given absolute conductances (uS), but its rows at
  segment nodes are current densities (mA/cm2), so it coupled area/100 of the intended conductance (65 pS instead
  of 0.1 nS for the pair). Seen because every Jaxley form disagreed with NEURON equally at weak coupling and NEURON's
  pair disagreed with the analytic solution. Fixed: each row gets g / (its segment's area), in S/cm2. After the fix
  the converged NEURON pair matches the exact matrix-exponential solution to 1e-5 mV (measured; the script now
  prints this, as the pre-registration asked).
- **Run 1 (wrong Jaxley geometry).** Jaxley's `length` is per compartment, so the chain cells were 90 um long
  instead of 30 um. Fixed to `L / ncomp`.
- **Run 2 = `gapcheck1`, scored** (log `data/worm/gapcheck/gapcheck1.log`). Measured, float64, max over all
  compartments and times:

| Case | g (nS) | dt (ms) | a | ImplicitGap vs NEURON (mV) | ExplicitGap (mV) | Gap (mV) |
|---|---|---|---|---|---|---|
| P | 0.1 | 0.1 / 0.4 | 0.02 / 0.06 | 1.7e-13 / 2.3e-13 | 0.022 / 0.088 | 0.048 / 0.187 |
| P | 1 | 0.1 / 0.4 | 0.16 / 0.64 | 1.7e-13 / 9.9e-14 | 0.029 / 0.168 | 0.430 / 1.406 |
| P | 10 | 0.1 / 0.4 | 1.59 / 6.37 | 1.2e-12 / 9.5e-13 | 4.5e16 / 1.1e16 (blew up) | 2.68 / 4.99 |
| C | 0 (B2) | 0.1 / 0.4 | 0 | **0.134 / 0.133** | - | - |
| C | 1 | 0.1 / 0.4 | 0.10 / 0.40 | 0.0075 / 0.0075 | 0.082 / 0.298 | 0.229 / 0.871 |
| C | 20 | 0.1 / 0.4 | 1.99 / 7.96 | 0.00032 / 0.00032 | inf / inf (blew up) | 2.89 / 6.75 |

  B3: gradient -1605.299 against finite difference -1605.300, relative difference under 1e-6: **pass**.
  B1: **pass** (every gap case <= 0.0075 mV). F1: ExplicitGap fails in the strongest P and C cases, as required.
  **B2: fail** (0.134 mV > 0.01 mV). By the rule above, the C results do not count as evidence, the gate is not met,
  and `gapcheck1` adopts nothing.

**Cause of the B2 failure (measured, diagnostic runs, not scored).** Passive cables match NEURON to 1e-12 mV
(1 cell, 2 and 3 compartments), and the active AIY membrane matches in one compartment, but the active membrane
differs over several compartments, more so the harder the cell is driven (2e-5 mV at 5 pA, 0.001 mV at 15 pA
with 2 compartments, 0.13 mV with 3). The published Nicoletti 2024 mod files pass EGL-19's gates to the coupled
BK channel through NEURON GLOBAL variables: `egl19.mod` declares `GLOBAL ... megl19, hegl19` and writes them in
its BREAKPOINT; `slo1egl19.mod` (and `slo2egl19.mod`) read them as `EXTERNAL megl19_egl19, hegl19_egl19`. The same
holds for UNC-2 (`unc2.mod` to `slo1unc2.mod`, `slo2unc2.mod`) and for the Ca pool that `kcnl.mod` reads
(`calcium_caintra1`, GLOBAL in `caintra1.mod`). A GLOBAL is one number for the whole model, so in a cell with
several segments every segment's BK channel sees the EGL-19 state of whichever segment wrote last. In a single
compartment, which is how the published models are used, this is exact; across compartments the NEURON
reference is wrong and the Jaxley port's per-compartment coupling is the intended model. So the B2 failure is a
defect of the reference, not of the cable or of `ImplicitGap`, but that is a diagnosis, not a pass.

## Pre-registration of `gapcheck2` (written 2026-11-05 01:10 CST, before the patched reference exists)

Same method, cases (P, C, both step sizes), error measure, bars B1-B3, F1, F2 and adoption gate as above. One
change, to the reference only: NEURON runs on a local copy of the Nicoletti mods
(`~/worm-spike/ext/nicoletti2024_local/`, the patch is in `scripts/worm/patch_nicoletti_mods.sh`) in which
`megl19, hegl19` (and `munc2, hunc2`) are RANGE variables of `egl19` (`unc2`) and the coupled BK mechanisms read
them through a per-segment POINTER, set segment by segment. Nothing else in any mod file changes.

**R0 (the patch must not change the published model):** a single-compartment AIY cell (the C membrane, 10 um,
15 pA) run in NEURON with the original mods and with the patched mods must agree to <= 1e-9 mV at dt 0.1 and
0.4 ms, and both must match Jaxley's single compartment to <= 0.01 mV. If R0 fails, `gapcheck2` is void.
The `kcnl` / `caintra1` GLOBAL is not patched here (AIY's published set has no KCNL); it is recorded for W1.

## Result of `gapcheck2` (scored 2026-11-05 01:17 CST): void by its own R0 rule

Log `data/worm/gapcheck/gapcheck2.log`. With the patched reference every gap bar passed: B1 max 1.2e-5 mV over all
P and C cases (P 1e-12 mV), B2 7.6e-6 / 1.2e-5 mV, B3 relative 6.4e-7, F1 ExplicitGap blows up in the strongest P
and C cases, F2 Gap 0.05-6.7 mV. **R0 failed:** the single-compartment cell with the original and the patched
mods differed by 2.7e-5 mV (dt 0.1) and 4.3e-5 mV (dt 0.4), against <= 1e-9. By the rule written above,
`gapcheck2` is void and adopts nothing.

**Cause of the R0 failure (measured, diagnostic, not scored).** The same GLOBAL carries state from one simulation
to the next inside one NEURON process: `egl19.mod` writes `megl19` only in its BREAKPOINT, and `slo1egl19.mod`'s
INITIAL reads it before anything has set it in the new run, so the BK gate starts from the previous run's final
EGL-19 value (0.0011 here) instead of 0. The first run in a fresh process with the original mods equals the
patched run exactly (0.0 mV, dt 0.1); the second and later runs differ by 2.7e-5 mV. With the patched mods every
run is identical (0.0 mV). So the published mods are not reproducible run to run inside one process, at the
1e-5 mV level, whenever SLO-1/EGL-19 is present.

## Pre-registration of `gapcheck3` (written 2026-11-05 01:17 CST, before it runs)

Identical to `gapcheck2` (cases, bars B1-B3, F1, F2, R0 at <= 1e-9 mV, gate) except one harness change: with the
original mods, the GLOBALs `megl19_egl19`, `hegl19_egl19`, `munc2_unc2`, `hunc2_unc2` are set to 0 before every
NEURON run, so each run starts as a fresh process does. Honest status: the R0 quantity this measures (fresh
original against patched) was already seen in the diagnostic above (0.0 mV), and the gap bars were already seen
in `gapcheck2` with the same `ImplicitGap` code, so `gapcheck3` is a confirmation run of a complete, consistent
harness, not a blind test. `ImplicitGap` has not changed since the pre-registration at the top of this file.

## Result of `gapcheck3` (scored 2026-11-05 01:22 CST): every bar passes; gate met; `ImplicitGap` adopted

Logs `data/worm/gapcheck/gapcheck3.log` (patched reference, scored), `gapcheck3_orig.log` (original mods, for
R0), `gapcheck3_r0.json`; figure `docs/worm/media/gapcheck3.png` (viewed). All numbers measured, float64, max over
every compartment and time point.

| Case | g (nS) | dt (ms) | a | ImplicitGap vs NEURON (mV) | ExplicitGap (mV) | Gap (mV) |
|---|---|---|---|---|---|---|
| R0, 1 comp, original vs patched NEURON | - | 0.1 / 0.4 | - | 0.0 / 0.0 (NEURON vs NEURON) | - | - |
| S, 1 comp, no gap (Jaxley vs NEURON) | 0 | 0.1 / 0.4 | 0 | 7.6e-6 / 1.2e-5 | - | - |
| P | 0.1 | 0.1 / 0.4 | 0.02 / 0.06 | 1.7e-13 / 2.3e-13 | 0.022 / 0.088 | 0.048 / 0.187 |
| P | 1 | 0.1 / 0.4 | 0.16 / 0.64 | 1.7e-13 / 9.9e-14 | 0.029 / 0.168 | 0.430 / 1.41 |
| P | 10 | 0.1 / 0.4 | 1.59 / 6.37 | 1.2e-12 / 9.5e-13 | 4.5e16 / 1.1e16 (blew up) | 2.68 / 4.99 |
| C (B2) | 0 | 0.1 / 0.4 | 0 | 7.6e-6 / 1.2e-5 | - | - |
| C | 1 | 0.1 / 0.4 | 0.10 / 0.40 | 7.6e-6 / 1.2e-5 | 0.075 / 0.292 | 0.229 / 0.871 |
| C | 20 | 0.1 / 0.4 | 1.99 / 7.96 | 7.6e-6 / 1.2e-5 | inf / inf (blew up) | 2.89 / 6.75 |

- **R0 pass** (0.0 <= 1e-9 mV; Jaxley single compartment 1.2e-5 <= 0.01 mV). **B1 pass** (max 1.2e-5 mV).
  **B2 pass** (1.2e-5 mV). **B3 pass** (gradient -1605.2987 against finite difference -1605.2997, relative
  6.4e-7). **F1 fails as required** (ExplicitGap blows up in the strongest P and C cases, and exceeds 0.01 mV in
  every case). **F2** Gap 0.048-6.75 mV, failing B1 everywhere, as expected.
- The ImplicitGap error in every C case equals the no-gap single-compartment residual (7.6e-6 / 1.2e-5 mV), so
  what remains comes from the membrane port (presumably a constant rounded differently), not from the coupling; in
  the passive pair it is at rounding (1e-12 mV).
- Each NEURON reference is itself 0.07-0.4 mV from the converged solution (NEURON at dt 0.001 ms) at these steps:
  the 0.01 mV bar tests that Jaxley solves the same discrete scheme, not that dt 0.1-0.4 ms is accurate enough
  for a given use.
- **Figure (viewed):** in the chain at 20 nS and dt 0.1 ms, ImplicitGap lies on the NEURON traces in cells 0, 3
  and 7; the half-implicit Gap rises visibly slower (the 1 + a slowdown of F-W0-5); ExplicitGap's error grows to
  1e17 mV by about 11 ms.
- **Gate met:** B1, B2, B3 pass, F1 fails, R0 passes, figure viewed. `ImplicitGap` is adopted as the
  gap-junction form for network fits (DECISIONS, 2026-11-05), scoped to what was tested plus the two checks below.

**Code change after the pre-registration (does not touch any scored case).** The 446-cell bench exposed that
`use_implicit_gaps` looked up each junction's cell by position in `net.nodes`, while edge indices are node labels,
which skip the branch points of branched cells. In single-branch cells (every pre-registered case) labels equal
positions, so the scored runs were not affected; on branched cells the old code raised an IndexError or could
assign a junction to the wrong cell. Fixed to a label lookup (`src/bioemu/jx_gap.py`; Jaxley itself indexes area
and capacitance by label, so the rest of the solve was already in label space).

**Branched-cell check (reported, not a bar; `scripts/worm/check_gap_branched.py`, log
`data/worm/gapcheck/gapbranch.log`).** Three Virtual Worm AIYL cells (2 branches, 2 compartments each, so 12
compartments with labels up to 13), the spike's CeNGEN membrane, three 5 nS junctions on both branches with two
sites in every cell, 20 pA into cell 0, 100 ms. ImplicitGap against ExplicitGap at the same small step: 0.062,
0.031, 0.015 mV at dt 0.004, 0.002, 0.001 ms (measured). The difference halves with dt, so both converge to the
same solution and the junctions are placed and solved correctly; a wrong lookup would leave a difference that does
not shrink. ImplicitGap's own step error at dt 0.1 ms against dt 0.001 ms in this spiking-range run: 0.61 mV.

**Cost on the 446-cell network (reported; `scripts/worm/bench_network.py`, CPU, one core, T 200 ms, dt 0.1 ms,
logs `data/worm/gapcheck/gapbench_*.log`).** The stand-in network: every Cook 2019 cell as a 4-compartment AIY,
4841 chemical synapses, 1342 gap-junction pairs, which land on 434 junction compartments (one per cell).
Measured, one core, shared machine (load about 22 of 28 threads):

| Form | conductance scale | forward (us per step) | forward + gradient (us per step) | voltage range (mV) | gradient finite |
|---|---|---|---|---|---|
| ExplicitGap | 1.0 | 283 | 1948 | -60.0 to 0.7 | yes |
| ExplicitGap | 1.5 | 228 | 2010 | -78.6 to 48.6 | **no** |
| ImplicitGap | 1.0 | 6377 | 24523 | -60.0 to 0.7 | yes |
| ImplicitGap | 1.5 | 5756 | 25385 | -60.0 to 0.5 | yes |

So the adopted form fixes the stress case: at 1.5x every cell stays in range and the gradient is finite, where the
explicit form's gradient is not. At 1.0x both forms give the same range. The price is about 23x per forward step
and 13x per gradient step at this size (derived from the table). The likely cause (inferred, not profiled): the
434 x 434 junction system is factorised densely every step, about 2/3 x 434^3 = 5e7 floating-point operations,
which is about 5 ms at a guessed 10 GFLOP/s on one core and matches the measured gap. Since every cell here has
one junction compartment, that system is a diagonal plus the sparse junction graph (2684 entries), so a sparse or
iterative solve should remove most of the cost. That change gets the same NEURON check before it replaces the
dense solve.
