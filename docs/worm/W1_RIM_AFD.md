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

## Prerequisite status (added after pre-registration; no RIM or AFD value opened)

**Q1, 2026-11-05 01:46 CST: current clamp confirmed; voltage clamp confirmed except the holding potential.**

- Current clamp (measured protocol, from the paper): Naudin et al. 2022 PLoS ONE 17:e0268380, Fig 1 legend:
  "a series of current injections, in spans of 5 seconds, starting from -15pA and increasing to 35pA by 5pA
  increments". Sweep order (inferred from the authors' code, strong): their fitting scripts
  (github.com/lois76/codeGenerationNonSpikingCBM, tag v1, Zenodo 10.5281/zenodo.5407653) pair data column i with
  `stim=[-15:5:25]` element i, in increasing order, for both RIM and AFD. Our files' headers number the sweeps in
  acquisition order (`CC-IV-long_3..13`). So sweep k is -15 + 5k pA, as assumed in section 1.
- Voltage clamp, from the papers: steps -100 to +50 mV by 10 mV (Naudin 2022 Methods; Nicoletti 2024 Fig 5
  legend, "16 voltage steps from -100 mV to 50 mV with a duration of 500 ms"). Peak = the largest absolute
  current in the first 100 ms of the step; steady state = the mean current over the last 50 ms (Naudin 2022 Fig 1
  legend; these windows are used, since the held-out numbers are Naudin's). Recorded at 22-23 C.
- Holding potential, **inferred, not confirmed**: -60 mV, held 1100 ms before the step and 100 ms after it, as in
  Nicoletti 2024's published simulation (`RIM_simulation_vclamp.py`). It is not stated in Naudin 2022 or in
  Nicoletti 2024's text, and the recording paper (Liu et al. 2018 Cell 175:57) was not reachable (403). The peak
  current depends on the holding potential through inactivation, so the peak half of the VC bar uses -60 mV
  labelled inferred until the Liu 2018 methods are checked; the steady-state half barely depends on it.
- **Holding potential update, 2026-11-05 (brain worker): -60 mV is now published, not inferred.** The Liu et al.
  2018 bioRxiv preprint (10.1101/359935 v1, saved at `docs/worm/research/liu2018_biorxiv_359935v1.html`), Fig 1B
  legend, for the voltage-clamped RIM, AIY, AFD and AWA recordings: "voltage step protocol, starting from -100 mV
  and increasing to 50 mV in 10 mV increments. The holding potential was set at -60 mV before and after applying
  each voltage step." These are the same three cell types (RIM, AIY, AFD) whose recordings Naudin 2022 used. Label:
  holding potential -60 mV **measured protocol (published, preprint)**; the Cell 175:57 version itself is still
  unchecked (403). The hold durations (1100 ms before, 100 ms after) are **still inferred** from Nicoletti 2024's
  simulation script; the preprint does not state them.
- Noted, not used: Naudin's own fits train on -15 to +25 pA and keep 30 and 35 pA out; our split (section 1) is
  different and stays as registered.

**Q2, pre-registered 2026-11-05 01:53 CST (run `port2`), before any check ran.**

Code: the eight channels are in `wormemu.nicoletti` (`NEW_CHANNELS`), transcribed from the same commit's .mod
files. They are opt-in: `make_membrane(lib, channels=[...])` builds only the listed channels and their gates;
the default (`lib.CHANNELS`, the AIY spike's 13) is unchanged. CCA-1's current joins EGL-19's and UNC-2's in
the Ca pool, as `caintra1.mod` reads the total `ica`.

Check (`scripts/worm/check_port2.sh`): single compartment, NEURON 9.0.2 on the published .mod files
(`ext/nicoletti2024`; one compartment, so the GLOBAL defect of F-W0-10 does not apply) against Jaxley, both in
float64, the `neuron_ref.py` protocol (11 steps, -15 to +35 pA, 1-6 s, 11 s, v_init -65 mV, eca 60, ek -80), at
dt 0.4 ms and 0.1 ms. Configurations (densities in nS per cell; test settings, not biological claims):

- `rim_pub`: the published Nicoletti 2024 RIM model (SHL-1, EGL-2, IRK, CCA-1, UNC-2, EGL-19, leak at the
  `RIM_simulation.py` densities; RIML surface 103.34e-8 cm2, volume 10.94e-12 cm3, cm 1.5, eL -50 mV).
- `iso_<channel>`, one for each of the eight: leak 0.5 nS (eL -50) plus that channel at 1.0 nS, RIML geometry
  (guessed test density: four of the eight, EGL-36, KQT-3, KVS-1 and UNC-103, have no published density in any
  Nicoletti 2024 neuron); `leak_only` is the same cell without the channel.
- `all21`: the earlier `all_test` (all 13 original channels, AIY geometry) plus the eight at 0.3 nS each, with
  KCNL and the Ca pool on, so CCA-1 feeds the pool.

Bars, all must pass:

- **B1, match:** in every configuration, at both dt, every sweep's RMS difference (Jaxley minus NEURON, whole
  11 s trace) <= 0.01 mV.
- **B2, the check can see the channel (must-differ control):** for each `iso_<channel>`, the NEURON trace
  differs from `leak_only` by >= 1 mV RMS (mean over the 11 sweeps, dt 0.4 ms), i.e. at least 100 times the B1
  bar. A channel that fails B2 has an uninformative B1, and its port is not adopted from this run.
- **R0, the default path is unchanged:** the refactored membrane, with the default channel set, reproduces the
  stored Jaxley outputs of the earlier check (`ref/aiy_pub_jx.npy`, `ref/all_test_jx.npy`, dt 0.4 ms) to
  <= 1e-9 mV max absolute difference.

Reported, not bars: the largest absolute difference per configuration; the resting potential of each.
Adoption: if all bars pass and the figure has been viewed, the eight channels become available for W1; nothing
changes for existing models (R0).

**Q2 result, port2 (scored 2026-11-05 01:57 CST): all bars pass; the eight channels are adopted for W1.**
Measured, float64, single compartment (`data/worm/port2/score.json`; figure `docs/worm/media/port2.png`, viewed):

| Bar | Result |
|---|---|
| B1, every sweep <= 0.01 mV RMS | pass. Each channel alone: 1e-13 to 3e-13 mV, except EGL-2 1.6e-8 and SHK-1 1.1e-7 mV (the same at both dt, so a rounding-level constant difference, not the time step). Published RIM model 2.8e-6 mV (max 1.9e-5 mV). All 21 on: 2.2e-3 mV at dt 0.4, 5.5e-4 at dt 0.1 (max 0.049 mV; the same Ca-pool residual as the earlier 13-channel test, which gives 0.009 mV) |
| B2, each channel moves the trace >= 1 mV RMS | pass: 4.0 (EGL-36) to 9.6 mV (KQT-3) |
| R0, default path unchanged <= 1e-9 mV | pass: 0.0 mV for both stored checks |

The first scorer run crashed (it globbed its own `score.json` as a configuration); the scorer was fixed and rerun
on the same saved traces, and no simulation was rerun.

**Amendment, 2026-11-05 01:58 CST, before any RIM or AFD value was opened: EXP-2 joins the AFD model.** Section 3
said EXP-2 has no kinetics in the library. That was wrong: Nicoletti 2024 ships `exp2.mod` (K current, m h^2).
The registered rule ("CeNGEN genes with kinetics in the extended library") therefore puts EXP-2 in AFD (CeNGEN
threshold 2: 129.8; RIM: 0, so RIM is unchanged), bounded [1e-7, UB] like the other threshold-2 genes. The
sentence about the leak absorbing EXP-2 no longer applies. It is ported (`exp2` in `wormemu.nicoletti`) and checked
by run `port2b`, pre-registered here with port2's bars: `iso_exp2` (leak 0.5 nS plus EXP-2 1.0 nS) and `all22`
(all21 plus EXP-2 at 0.3 nS) must pass B1 at both dt; `iso_exp2` must pass B2 (>= 1 mV against `leak_only`);
R0 must pass again.

**port2b result (scored 2026-11-05 01:59 CST): B1 and R0 pass, B2 fails, so EXP-2 is not adopted from this run.**
EXP-2 alone matches NEURON to 4.5e-13 mV (all22: 2.2e-3 mV at dt 0.4; R0 0.0 mV), but at 1.0 nS it changes the
trace by only 0.52 mV RMS, under the 1 mV must-differ bar. That makes its match uninformative under the
registered rule. The likely reason (inferred): EXP-2 inactivates almost fully above -50 mV (h^2, h half-point
-50 mV, h time constant about 1-2 ms), so at 1 nS its window current is small.

**port2c, pre-registered 2026-11-05 02:00 CST:** port2b's configurations and bars unchanged, except that
`iso_exp2` carries EXP-2 at 10 nS (`ISO_NS=10`; a guessed test density).

**port2c result (scored 2026-11-05 02:00 CST): all bars pass; EXP-2 is adopted for AFD.** Measured
(`data/worm/port2/port2c/score.json`; figure `docs/worm/media/port2c.png`, viewed): B2, EXP-2 at 10 nS moves the
trace 2.2 mV RMS (bar 1 mV). B1, EXP-2 alone matches NEURON to 3.5e-13 mV at dt 0.4 and 1.4e-13 at dt 0.1; all 22
channels on, 2.2e-3 mV at dt 0.4 and 5.5e-4 at dt 0.1 (max 0.049 mV); published RIM 2.8e-6 mV. R0, 0.0 mV. The 10 nS
is a test density only; AFD's EXP-2 density is fitted inside the registered bounds. With port2 this completes Q2:
nine channels (CCA-1, EGL-2, EGL-36, IRK, KQT-3, KVS-1, SHK-1, UNC-103, EXP-2) are available to W1 through
`make_membrane(lib, channels=[...])`; the default 13-channel membrane is unchanged (R0).

**Q3, pre-registered 2026-11-05 02:09 CST (run `kcnl1`), before any check ran.** Patch: in the local copy of the
mods (`scripts/worm/patch_nicoletti_mods.sh`), `caintra1`'s `calcium` becomes a RANGE variable and `kcnl` reads it
through a POINTER set per segment (`h.setpointer(seg._ref_calcium_caintra1, "calcium_caintra1", seg.kcnl)`), as
was done for the BK coupling. Check (`scripts/worm/check_kcnl.py`), NEURON 9.0.2 against Jaxley, float64, steps
-15 to +35 pA from 1 to 6 s, 8 s runs, v_init -65 mV, eca pinned at 60, ek -80, dt 0.4 and 0.1 ms. Membrane: the
published RIM densities (`rim_pub`, S/cm2) plus KCNL, SLO-1 coupled to EGL-19 and SLO-2 coupled to UNC-2, each at
1e-3 S/cm2 (guessed test densities), with the `caintra1` pool given each segment's own surface and volume.
Cells: `S`, one compartment with the RIM geometry; `M`, a 300 um x 0.3 um cable in 3 compartments, current
injected in the first (thin, so the compartments' voltages and Ca differ); `M0`, `M` without KCNL. Bars, all must
pass:

- **K0, published model unchanged:** `S` on the patched mods equals `S` on the published mods, max absolute
  difference <= 1e-9 mV, both dt.
- **K1, match:** patched NEURON vs Jaxley, `S`, `M` and `M0`, every compartment and every sweep, RMS <= 0.01 mV,
  both dt.
- **K2, the check can see KCNL:** patched NEURON `M` vs `M0` at the injected compartment, mean RMS over sweeps
  (dt 0.4) >= 1 mV.

Reported, not a bar: the published (unpatched) mods on `M` against the patched ones, i.e. the size of the GLOBAL
defect in this cell. If it is under 0.01 mV, this check shows the patch is harmless here but not that it was
needed. Adoption: if all bars pass and the figure is viewed, Q3 passes and the patched mods are the NEURON
reference for any multi-compartment RIM or AFD cross-check.

**Q3 result, kcnl1 (scored 2026-11-05 02:11 CST): K0 and K1 fail, K2 passes, so Q3 does not pass and the patch is
not adopted from this run.** Measured, float64 (`data/worm/kcnl1/score.json`; figure `docs/worm/media/kcnl1.png`,
viewed):

| Bar | Result |
|---|---|
| K0, patched = published on `S`, <= 1e-9 mV | fail: 3.8e-6 mV (dt 0.4), 2.6e-6 mV (dt 0.1); sweep 0 identical, later sweeps differ |
| K1, Jaxley = patched NEURON, <= 0.01 mV RMS | fail: `S` 0.016 (dt 0.4) and 0.004 (dt 0.1); `M` 1.95 (max 5.2) and 0.64; `M0` 2.4e-4 and 1.8e-4 |
| K2, KCNL moves `M` >= 1 mV | pass: 31.9 mV |

Reported: the published (GLOBAL) mods differ from the patched ones on `M` by up to 6.55 mV RMS (max 15.1 mV) at the
depolarising steps, so the patch is needed for any multi-compartment NEURON reference; this run does not show the
patched NEURON and Jaxley agree. `M0` (no KCNL) matches, so the K1 failure sits in the Ca pool to KCNL link.

Development after scoring (not a pre-registered run; `data/worm/kcnl1/dev_after_kcnl1.json`):

- Jaxley's Ca pool took i_ca at the current step's voltage and KCNL read the pool before its update; NEURON's
  `caintra1` reads the ica stored at the previous voltage, and `kcnl` (registered after `caintra1`) reads the
  updated pool. An opt-in `make_membrane(..., ca_lag=True)` reproduces that order. It cuts the mismatch 4-6x (`S`
  0.0027 mV, `M` 0.42 mV at dt 0.4, 0.11 at dt 0.1) but `M` stays 40x over the bar. The residual grows during the
  step and peaks in the far compartment (1.77 mV at 5.95 s), so another difference remains, not yet found. Default
  path unchanged (0.0 mV against kcnl1's Jaxley traces).
- K0 is not calcium carryover (resetting `calcium` changes nothing). Inferred: `unc2` registers after
  `slo1unc2`/`slo2unc2`, so their INITIAL reads the previous run's UNC-2 gates through the new pointer, while the
  published-mods harness resets the GLOBAL copies to 0. A harness reset of the UNC-2 gates is the candidate fix.
- Against NEURON at dt 0.01 ms, NEURON at dt 0.4 is 1.67 mV RMS off on `M` and Jaxley 2.16 mV (dt 0.1: 0.46 and
  1.07). In this thin cable with KCNL at the guessed 1e-3 S/cm2, the 0.4 ms time step is itself a 2 mV-scale
  error. The fits run at dt 0.4; whether that matters at fitted densities is open.

**Launch, 2026-11-05 02:21 CST.** Q3 did not pass by the 02:50 cutoff, so only fits that cannot depend on it were
launched: **M1 (passive) for RIM and AFD** (run `w1m1`), which has no Ca channel, Ca pool or KCNL. The full fits
`w1rim1`/`w1afd1`, M2 and M3 all contain KCNL and are held until a new pre-registered check (`kcnl2`) passes.
M1 alone is not scored: per section 5 it only serves to make the held-out bars informative, so it is scored once,
together with the full fits.

**Correction, 2026-11-05 02:25 CST:** the Q2 text above says EGL-36, KQT-3, KVS-1 and UNC-103 have no published
density in any Nicoletti 2024 neuron. That is wrong for UNC-103: `AVAR_simulation.py` gives 0.0481669 nS (on
1121.79e-8 cm2, about 4.3e-6 S/cm2). The other three stand. It changes nothing scored (the 1.0 nS was a test
density) or the bounds (`fit_w1.py` gives every K channel the K-class UB, 1.52e-2 S/cm2, unchanged by this).
