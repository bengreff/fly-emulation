# W1: RIM and AFD fits, pre-registration (runs `w1rim1`, `w1afd1`)

Status: pre-registered 2026-11-05 01:13 CST. Not run. Nothing above the line "RESULTS" (added when results
exist) changes after the first scored run; a changed rerun is a new, separately named experiment.

**What has been looked at so far, so the held-out status is honest.** Only the file headers (column names, row
counts), the cell counts (`n`) of the voltage-clamp sheet, and the CeNGEN expression tables. No RIM or AFD
voltage or current value has been printed, plotted or used. The AIY spike's loader (`fit_aiy.load_iv`) read the
whole voltage-clamp sheet into memory but used and printed only the AIY columns.

## 1. Data and split (fixed now, before any value is opened)

- **Current clamp, one cell each** (Naudin et al. 2022, Liu lab, Mendeley 10.17632/6pgdf3zrp3.1, CC BY 4.0):
  `Fig1A_RIM_CC.txt` (11 sweeps, columns `CC-IV-long_3..13`, exported pre-averaged like AIY's) and
  `Fig1B_AFD_CC-IV_11steps.txt` (11 sweeps, raw 10 kHz). Expected protocol, as for AIY: steps -15 to +35 pA by 5
  pA, from 1 s to 6 s. **Split by sweep order, not by value:** train = sweeps 0, 2, 4, 6, 8, 10; held out =
  sweeps 1, 3, 5, 7, 9, the same split as AIY.
- **Voltage clamp, population:** `Fig1_IVcurves_AFD_RIM_AIY.xlsx`, the RIM and AFD columns, peak and steady
  state, mean and SEM. n = 3 cells at most voltages for both (measured from the `n` columns; 1-2 at the two or
  three most negative voltages). All held out; never used in fitting or model choice.
- **Preprocessing:** AFD averaged in 4-sample bins (to 0.4 ms, the AIY export rate), then both interpolated to
  the model grid; loss on 0.2-8 s every 2 ms, as AIY.

## 2. Prerequisites (each must pass before the fits start; none touches the data)

- **Q1, step amplitudes and VC protocol** confirmed from the Naudin 2022 methods or figure legends (current-clamp
  amplitudes in sweep order; holding potential, step length and peak window for voltage clamp). Until then the
  AIY values above are assumptions. If the sweep order cannot be confirmed as increasing amplitude, the runs do
  not start.
- **Q2, channel port:** the eight Nicoletti 2024 channels not yet in `wormemu.nicoletti` (CCA-1, EGL-2, EGL-36,
  IRK, KQT-3, KVS-1, SHK-1, UNC-103) ported and each matched to NEURON at <= 0.01 mV RMS in one compartment,
  as the first 13 were (SPIKE.md). Their mod files have no GLOBAL coupling between mechanisms (checked).
- **Q3, multi-compartment NEURON reference:** any NEURON cross-check of a multi-compartment RIM or AFD model
  uses the per-segment patch of the Ca-channel-to-BK coupling (`scripts/worm/patch_nicoletti_mods.sh`,
  GAPCHECK.md), extended to the `kcnl` / `caintra1` Ca pool (both cells express KCNL genes).

## 3. Model (the spike's model class, extended; all fitted values labelled inferred)

- **Morphology:** Virtual Worm `RIML.cell.nml` and `AFDL.cell.nml` (DECISION 1: inferred geometry, not EM),
  2 compartments per branch, as AIY.
- **Channel set:** CeNGEN genes with kinetics in the extended library. Kinetics fixed at the published values.
  Genes present at threshold 2 get densities bounded [1e-7, UB]; genes present only at threshold 1 get
  [1e-10, UB], where 1e-10 S/cm2 counts as absent (DECISION 5: the data decide). UB as in SPIKE.md (10x the
  largest Nicoletti 2024 density for the channel or its class; for the eight new channels the same rule).
  - **RIM**, threshold 2: EGL-19, UNC-2, CCA-1, NCA (nca-2), SHL-1, KVS-1, EGL-2, EGL-36, KQT-3, UNC-103, IRK
    (irk-2, irk-3), SLO-1 and SLO-2 (each bulk and coupled to EGL-19 and to UNC-2), KCNL (kcnl-2, -4). Threshold
    1 only: SHK-1, IRK-1 (folded into IRK, so IRK keeps the threshold-2 bound). No kinetics in the library:
    UNC-58 and EGL-23 (two-pore K channels), absorbed by the leak.
  - **AFD**, threshold 2: EGL-19, CCA-1, SHL-1, SHK-1, KVS-1, EGL-2, KQT-1, IRK (irk-1, -2, -3), SLO-1 and SLO-2
    (bulk and coupled to EGL-19; no UNC-2), KCNL (kcnl-1 to -4). Threshold 1 only: KQT-3, EGL-36. No kinetics:
    EXP-2, absorbed by the leak (this abstraction is valid only if EXP-2's rectification does not shape the
    steps; a systematic misfit at depolarised steps would be the sign that it does).
- **Other fitted parameters:** Cm [0.5, 2.0] uF/cm2, leak reversal [-100, -30] mV, Ra [30, 300] ohm cm, one
  density per channel over the whole cell. No per-trace or per-compartment free parameters.
- **Fit:** Adam on all bounded parameters at once, 16 starts (one at the published Nicoletti 2024 RIM densities
  rescaled to this morphology's area, for RIM; random for the rest), 300 iterations, best start by training
  loss only. CPU, 2 cores per fit (DECISION 3), float32 with a float64 re-check of the final scores, as AIY.

## 4. Bars (all must pass for "pass"; same as AIY except the n threshold)

- **Train:** mean RMSE over the 6 training sweeps <= 4 mV.
- **Held-out current clamp:** mean RMSE over the 5 held-out sweeps <= 5 mV, and no sweep > 8 mV.
- **Held-out voltage clamp:** at >= 80% of the voltages with n >= 3 cells, the predicted current lies within
  the population mean +/- 2 SD (SD = SEM x sqrt(n)), judged separately for peak and for steady state; both
  must pass. With n = 3 the SD itself is poorly known, so this bar only counts if a control fails it (below).

## 5. Controls that must fail (DECISION 2)

- **M1, passive:** leak, Cm and Ra only, fitted to the same training sweeps the same way.
- **M2, wrong identity:** the other cell's fitted channel densities (RIM's on AFD, AFD's on RIM) on this
  cell's morphology, with only Cm, leak reversal and Ra refitted on this cell's training sweeps.
- **M3, reported only:** AIY's `fit1` CeNGEN densities, treated as M2.
- **Rule:** a held-out bar is **informative** for a cell only if M1 or M2 fails it. A cell's result is "pass"
  only if every bar passes and both held-out bars are informative; a bar that passes but is uninformative is
  reported as "uninformative", not as a pass. If M2 passes the held-out current-clamp bar, the test cannot tell
  RIM from AFD, and that is the headline.

## 6. Reported, not bars

The published Nicoletti 2024 RIM model (single compartment, published densities and kinetics) on the same RIM
sweeps and I-V curves, as a baseline; for AFD the Naudin 2022 model if its parameter table (S1 Table) is
obtained. Which fitted densities end at a bound, and which threshold-1-only channels the fit turns on. Wall
time, gradient simulations per second. Expected cost (derived from AIY's 1.5 h per fit on 2 cores): 1-3 h per
fit, about 8-12 core-hours for both fits and the controls; to run at night or outside 17:00-22:00 on backhouse.

## 7. Falsifier

If the training bar passes but a held-out bar fails, the model does not generalise for that cell, reported as
"fails the pre-registered bar". If a control passes a bar, the bar was too weak to test the model and no claim
rests on it.
