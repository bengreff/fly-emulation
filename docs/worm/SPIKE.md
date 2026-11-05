# The spike: one C. elegans neuron (AIY), multicompartment, CeNGEN channel set, gradient fit on the GPU

Status: pre-registered 2026-11-04 23:03 CST, before any fit was run or scored. Results are appended below the
line "RESULTS" once they exist; nothing above that line changes after the run.

## 1. Pre-registration (written before running)

**Neuron and data.** AIY, the non-spiking amphid interneuron. Current-clamp data: Naudin et al. 2022 (Liu lab),
Mendeley 10.17632/6pgdf3zrp3.1, CC BY 4.0, file `Fig1A_AIY_CC.txt`: one cell, 11 current steps -15 to +35 pA
by 5 pA, step from 1 s to 6 s, trace 0-11 s, exported at 0.4 ms (the lab averaged every 20 points), 22-23 degC.
Voltage-clamp data: same deposit, `Fig1_IVcurves_AFD_RIM_AIY.xlsx`: population I-V curves for AIY (n = 5-7
cells), peak and steady-state current at -120 to +50 mV by 10 mV, mean and SEM. Whether the current-clamp cell
is one of these cells is not stated, so the voltage-clamp test is across protocol and mostly across cells, not
guaranteed fully independent of the training cell.

**Model.** AIYL morphology from OpenWorm CElegansNeuroML (`AIYL.cell.nml`, Virtual Worm geometry, not a true
EM reconstruction; this is a known gap), converted to SWC (`bioemu.morph.nml_to_swc`). Membrane: one fused
mechanism (`bioemu.jx_membrane`) carrying the Nicoletti et al. 2024 channel kinetics (`wormemu.nicoletti`,
transcribed from their .mod files and checked against NEURON: 0.000 mV RMS at the published AIY densities,
<= 0.009 mV RMS with all 13 channels on). Kinetics are fixed at the published values. Channel set = the CeNGEN
threshold-2 genes for AIY that have kinetics in the library: leak, NCA, EGL-19, UNC-2, KQT-1, SLO-1 (coupled to
EGL-19 and to UNC-2, plus bulk), SLO-2 (same three), KCNL (SK, with the Ca pool). SHL-1 is not in AIY at
threshold 2, so the CeNGEN model has no SHL-1 although the published AIY model does. A second model, "pub", uses
the published 7-channel AIY set for comparison. Densities are uniform over the cell (one value per channel).
E_Ca fixed at 60 mV (the published stated value; the published code actually ran at 127.6 mV, see FINDINGS).

**Fitted parameters and bounds (all inferred, not measured).** Density of each channel in the set, in S/cm2,
bounded [1e-7, 10x the largest density any of the six Nicoletti 2024 neurons uses for that channel or its class]
(K and SLO channels 1.5e-2, Ca channels 3.2e-3, NCA 9.1e-4, leak 2.1e-3). Specific capacitance [0.5, 2.0] uF/cm2.
Leak reversal [-100, -30] mV. Axial resistivity [30, 300] ohm cm. Densities and Ra fitted in log space.
No per-trace or per-compartment free parameters.

**Training data.** The 6 current-clamp steps at -15, -5, +5, +15, +25, +35 pA (indices 0, 2, 4, 6, 8, 10).
Loss: mean squared error of the somatic voltage from 0.2 s to 8 s, sampled every 2 ms, averaged over the 6
traces. Optimiser: Adam on all bounded parameters at once (sigmoid-bounded), gradients by backpropagation through
the simulator on the GPU, 16 starts (one at the published densities rescaled to this morphology's area, 15
random), 300 iterations, best start chosen on training loss only.

**Held-out data (not used in fitting or model choice).**
1. The other 5 current-clamp steps of the same cell: -10, 0, +10, +20, +30 pA (indices 1, 3, 5, 7, 9).
2. The population voltage-clamp I-V curves (a different protocol), predicted blind: soma voltage clamp, hold
   -60 mV for 1100 ms, step 500 ms, return 100 ms (the Nicoletti 2024 AIY protocol); steady state = mean current
   over the last 50 ms of the step; peak = extreme current 0-100 ms after step onset (minimum for steps <= -60 mV,
   maximum above).

**Success bars (all must pass for "pass").**
- Train fit: mean RMSE over the 6 training traces <= 4 mV.
- Held-out current clamp: mean RMSE over the 5 held-out traces <= 5 mV, and no single held-out trace > 8 mV.
- Held-out voltage clamp ("within real variability"): at >= 80% of the voltages that have n >= 5 cells, the
  predicted current lies within the population mean +/- 2 SD (SD = SEM x sqrt(n)); judged separately for steady
  state and for peak, and both must pass.
- Reported but not a bar: the same numbers for the published Nicoletti 2024 AIY model (single compartment) as a
  baseline, and which fitted parameters ended at a bound (a value at a bound was set by the bound, not the data).

**Falsifier.** If the training bar passes but either held-out bar fails, the fit does not generalise and the
spike result is "fails the pre-registered bar", reported as such. No bar, split or window is changed after the
first scored run; a changed rerun is a new, separately labelled experiment.

**Also measured (for the compute extrapolation).** Wall time of the whole fit; simulations per second on the GPU
for forward and for forward+gradient at the batch used; a timed forward and gradient run of a 302-cell network
of this neuron model, from which the whole-worm cost is derived (labelled derived).

## RESULTS
