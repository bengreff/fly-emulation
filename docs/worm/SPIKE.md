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

### Addendum A, written 2026-11-04 23:26 CST, before any held-out score was computed

The pre-registration left four details of the voltage-clamp prediction open. They are fixed here, before the
evaluation (`scripts/worm/eval_aiy.py`) has been run on either fit, and follow the published protocol file
(`AIY_simulation_vclamp.py`, Nicoletti 2024) wherever it says something:
1. The predicted current is the total **ionic** current (all channels plus leak), summed over every compartment
   with the soma clamped. There is no capacitive term, as in the published script (it sums ik + ica + ileak +
   inca). Neurites are not clamped, so space-clamp error is part of the prediction.
2. Windows as in the published script: steady state is the mean over 450-500 ms after step onset; peak is the
   minimum (steps at or below -60 mV) or maximum (above) over 0-100 ms after onset. This matches the
   pre-registered wording.
3. Voltage clamp is integrated at dt 0.1 ms in float64. dt 0.025 ms is reported as a convergence check. The
   published script uses 0.01 ms.
4. E_Ca = 60 mV, as in the fit. The published-model baseline is reported at both 60 mV and 127.59 mV.

Also reported, not bars:
- the current-clamp RMSEs recomputed in float64 at dt 0.4 and 0.1 ms, and their RMS difference from the
  float32 dt 0.4 traces the fit produced;
- any CPU contention during the fits. My benchmarks shared core 11 with the "pub" fit for about 10 minutes
  (23:10-23:22), so its timing is slightly pessimistic; the "cengen" fit's cores were not shared by my jobs.

### Results of run `fit1`, scored 2026-11-05 00:41 CST

Rerun: `scripts/worm/run_spike.sh` (RUN=fit1). Numbers: `data/worm/spike/fit1/` (`fit_cengen.json`,
`fit_pub.json`, `eval.json`, logs). Figure (viewed): `docs/worm/media/spike_fit1.png`. Every number below is
**measured** unless labelled otherwise.

**Verdict: fails the pre-registered bar.** Both models miss the training bar (mean RMSE 4.79 and 4.80 mV against
<= 4 mV). Both pass both held-out bars. Under the rules above, a failed bar is the result; nothing is refitted
under this name.

| Bar | Pre-registered | cengen (CeNGEN set, 12 channels, no SHL-1) | pub (published 7-channel set) |
|---|---|---|---|
| Train, mean RMSE over 6 steps | <= 4 mV | 4.79 mV, **fail** | 4.80 mV, **fail** |
| Held-out current clamp, mean of 5 steps | <= 5 mV | 3.78 mV, pass | 3.77 mV, pass |
| Held-out current clamp, worst step | <= 8 mV | 5.68 mV (-10 pA), pass | 5.81 mV (-10 pA), pass |
| Held-out voltage clamp, steady state | >= 80% of 18 voltages inside mean +/- 2 SD | 100%, pass | 100%, pass |
| Held-out voltage clamp, peak | same | 100%, pass | 100%, pass |
| *Baseline, not a bar: published model, E_Ca 60 / 127.59* | | train 5.31 / 5.81, held-out mean 3.88 / 4.54, max 4.94 / 7.14; voltage clamp 100% / 100% | |

What the numbers say:
1. **The fits beat the published model on training (4.79 against 5.31 mV) but not by much, and the two channel
   sets fit equally well.** The pub fit drove SHL-1 to 1.8e-6 S/cm2 (in log terms 24% of the way up from its 1e-7
   floor to its 1.5e-2 ceiling; derived) and EGL-19 and bulk SLO-1 almost to zero. So this cell's current-clamp data do not ask
   for SHL-1, consistent with CeNGEN calling it absent in AIY (F-W0-3; a statement about this cell's current
   clamp, not proof of absence).
2. **The misfit is systematic, not noise.** The data's own fast fluctuation is 0.7-1.7 mV RMS (derived,
   F-W0-7). Both fits miss the steady-state voltage of several steps by 5-8 mV in the same direction: at -5 pA
   the model sits near -76 mV against -84 mV recorded, and at +5 pA it depolarises too little. The model's steady-state
   I-V is too straight for this cell. Candidate causes (inferred, untested): the fixed published kinetics, uniform
   densities over the cell, and the Virtual Worm morphology.
3. **Capacitance went to its upper bound in cengen (1.99 of 2.0 uF/cm2) and nearly so in pub (1.98).** That value
   is set by the bound, not the data. With this morphology's 88 um2 that gives about 1.75 pF in total, against
   1.05 pF in the published single compartment (65.9 um2 x 1.6; derived). Possible reading (inferred): the
   Virtual Worm geometry underestimates AIY's membrane area.
4. **Parameters are not identifiable from this data.** Leak reversal came out at -49 mV (cengen) and -74 mV (pub)
   with the same error. 11 of 16 cengen starts and 8 of 16 pub starts converged to a pooled training RMSE of 4.86-4.95 mV;
   one start per model went non-finite and the rest (4 and 7) ended at 89-910 mV (stuck, the flat grey lines in
   the figure).
5. **The held-out current-clamp bar is softer than it looks.** The 0 pA step (no stimulus) scores 0.7 mV and pulls
   the held-out mean down; without it the mean is 4.56 mV (cengen; derived), still under 5. The steps are from the
   same cell, so this tests other amplitudes, not other cells (F-W0-2).
6. **The voltage-clamp bar did not discriminate** (F-W0-6). The fits predict less outward current than the
   population mean above 0 mV (at +50 mV: 40 pA predicted, 82 pA mean, 47 pA SD) and still pass, because 2 SD is
   wide. The published model is closer there (54-65 pA).

Numerical checks (reported, not bars): re-integrating the fitted models in float64 changes the soma traces by at
most 0.15 mV RMS (cengen) and 0.42 mV (pub) at dt 0.4 ms, and at dt 0.1 ms by at most 0.15 and 0.42 mV; the
training and held-out mean RMSEs move by at most 0.04 mV and the worst held-out step by at most 0.15 mV (pub,
5.81 to 5.95); every bar result is unchanged. Voltage clamp at dt 0.025 ms gives the same fractions inside as at 0.1.

**Cost (measured; CPU, 2 cores per fit, backhouse load about 30 from other users' jobs throughout, so
pessimistic):**
- Whole fit (16 starts x 300 Adam iterations, 6 traces of 8 s at dt 0.4 ms, float32): 5,243 s (cengen) and
  5,367 s (pub), about 1.5 h.
- Per iteration: 17.7 and 18.0 s for 96 gradient simulations, i.e. 5.43 and 5.34 gradient simulations per
  second, or about 43 biological seconds of gradient per wall second on 2 cores (derived, x 8 s).
- Forward only: 31.1 and 32.9 simulations per second (about 250 bio-s per wall-s; derived).
- **Deviation from the pre-registration: the fits ran on CPU, not the GPU.** Before any fit was scored, the shared
  GPU measured 0.33 gradient simulations per second for this cell at batch 12, against about 6 on CPU (F-W0-4);
  another user held the GPU at 65-99%. No single-cell GPU forward rate was recorded. The GPU's measured rates are
  for the 446-cell network (PLAN c.5): forward 10.4 bio-s per wall-s at batch 32, gradient 1.07.
- **Whole-worm extrapolation (derived):** PLAN.md section c.5. In short, running the worm at 4 compartments per
  cell costs about 2.4 h per biological hour on one CPU core, and one joint whole-worm fit (guessed size: 1e5
  biological seconds of gradient) about a day on backhouse.

**Next experiment (new name, to be pre-registered before it runs):** free the gating midpoints of each gene within
measured bounds (shared by gene, as Ben's rules allow), allow soma and neurite densities to differ, and add a
control model that must fail the voltage-clamp test (passive membrane only). Then RIM and AFD from the same
deposit (W1).
