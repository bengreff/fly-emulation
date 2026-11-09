# Vital signs: the entire worm's physiology battery

weki, 8 Nov 2026 (phase 2 of the debugging pass). Code: `src/wormemu/fit/vitals.py`; tests:
`tests/test_worm_fit_vitals.py`; the Atanas bar: `scripts/worm/fit/atanas_pc3.py`.

The battery is the gate's instrument and the candidate EKI observation set (`FIT_GENERAL.md`). Ben, 8 Nov: "Vital
signs is a good direction as a check, as long as all the signs emerge from the mechanics of the entire worm." So
every sign is read from one closed-loop run per condition of the whole model. No generator, timer or clamp writes a
sign. A sign the worm does not produce is reported as a miss and left alone.

## The experiment

One `wormemu.simulate(theta, Experiment)` call per condition:

| Part | Setting |
|---|---|
| Brain | every registered module at its default form (`mech.REGISTRY`, 28 modules incl. organs, senses, glia, pumps, metabolism, noise) |
| Body | `body="on"`: the MetaWorm FEM body in closed loop, exchange 1/240 s (4.167 ms), the brain on its 0.5 ms grid |
| World | the agar film (`metaworm.AGAR_FILM`), the plate fields of `body/environment.py` at their defaults (lawn, O2, CO2, salt plug, 20 C at 0.5 C/cm), no events; wtriage's `ChemotaxisScene("cone_published")` |
| Conditions | `food` = env_food lawn (the worm starts 2 mm inside the edge); `nofood` = env_food off |
| Instrument | GCaMP read as GCaMP7f, the indicator Atanas 2023 imaged (methods, PMC10836760, opened), with Atanas's own per-frame imaging noise, obs_noise_dff = 0.0417 F / mean F (derived from the 60 open animals, `scripts/worm/fit/atanas_noise.py`; from 8 Nov 23:25, before that the worm's own guessed 0.03). The gcamp module is readout only, so neither changes the worm |
| Temperature | 20 C (`Experiment.temperature_C`: the worm, and the plate at the start; the head reads the plate's gradient from main 27f7276, limitation 2) |
| Recording | every exchange (4.167 ms), every cell; settle 5 s dropped from every readout |
| Lengths | core: 200 bio-s per condition; eggs tier: at least 1800 bio-s (egg signs report "too short" below that) |

The plate goes in on `Experiment` (world, env, scene; wbrain2 added them, main 27f7276, merged 9 Nov 01:36), exactly
as `scripts/worm/triage/vital_loop.py` sets it up. Before that `vitals.plate()` subclassed `body.loop.Body` for the
call; batteries up to 910f6f8 ran that way.

## Physicality, per run (pre-registered)

- finite: every recorded voltage, Ca and module concentration is finite;
- V bounds: every soma voltage stays inside [E_lo - 1 mV, E_hi + 1 mV], E_lo / E_hi the lowest and highest reversal
  potential in this worm's values (34 reversal Specs plus BAAIWorm's literal -80 / +60 mV). A membrane made only of
  conductances cannot leave that interval, so leaving it means a module injects current past it. The 1 mV allows
  integrator overshoot (guessed);
- concentrations >= 0: `ca_uM` and every `out:*_uM / _mM / _nM` recorded;
- no step alternation (added 9 Nov 00:55, pre-registered before its two validation runs): no soma voltage reverses
  direction at every body exchange step for 25 steps in a row (100 ms at 4 ms) with every step larger than 2 mV.
  brain.step holds each module's `I_pA` fixed over the step, from V at the step's start. In the NEURON brain three
  modules put a conductance g (E - V) through that path (read from the code, 9 Nov 01:23): egg_laying (LGC-55 on
  HSN, and the vulval-muscle cation term on its own clamps), intestine (PBO-5 on the posterior body-wall muscles)
  and noise (the zero-mean conductance fluctuation). drugs, k2p_leak and neuromod do it only on the stand-in brain
  of the unit tests and use NEURON point processes otherwise; senses_chem, senses_proprio and senses_touch use
  SensG point processes (implicit); glia, pumps and slow_signalling feed V back through slow states (K+, Na+, a
  homeostatic integral), not a per-step conductance. (The 01:04 entry here listed ten modules; that came from a
  search for modules that read V, and was wrong for seven of them.) Such an explicit conductance makes V alternate
  every step once it is large against the capacitance it charges in one step (derived: explicit Euler). The
  threshold, measured on the template's intrinsic membrane by `scripts/worm/fit/explicit_gcrit.py` (E -41 mV, from
  rest, 4.0 / 4.5 ms steps): HSNL 1.31 / 1.22 nS, AWAL 1.87 / 1.79, ASHL 1.39 / 1.27, AFDL 1.46 / 1.34, AVAL
  1.94 / 1.84, RIS 0.87 / 0.79, ALA 20.2 / 19.8. The soma clamp sits on a soma of 0.15-0.72 pF against 2-24 pF
  for the whole cell, so no single capacitance predicts these (g dt / C on the whole cell runs 0.46-3.7). A
  posterior body-wall muscle (one 22 pF compartment, E 0 mV for PBO-5) goes at 13.8 / 12.2 nS, above
  pbo5_g_nS's top of 10, so PBO-5 stays stable inside its range at rest; the vulval muscles were not measured. A 125 Hz sustained oscillation is not a C. elegans
  behaviour, so it is read as numerical (thresholds guessed). Validation, written before either run: on the template
  (food, 16 bio-s, Mac) the check flags no cell; on prior draw seed 1 (food, 16 bio-s), which leaves the bounds after
  its first egg at 12.6 s, it flags HSNL and HSNR. If the template flags any cell, the thresholds are wrong or the
  template alternates; either way it is not adopted until explained.
  Result (9 Nov 01:04, Mac, `scripts/worm/fit/physicality_recheck.py`, measured): the template on this branch
  flags no cell (alt_cells 0, physical); seed 1 on f8e7699 flags HSNL and HSNR (811 steps in a row, from 12.62 bio-s
  to the end), the two cells the bounds already caught. Adopted. Its use is the case the bounds miss: an alternation
  that stays inside them.

A run that fails physicality is rejected in the fit (FIT_GENERAL.md). The fraction of neurons above -20 mV is
reported with no bar (none is published; DEBUG_TRIAGE line 18).

## The signs

Band = mean +- 2 SD unless a range is given. SD derived from SEM as SEM x sqrt(n) where only SEM is reported.

| Sign | Readout | Scored in | Published | Band | Label | Source (opened 8 Nov 2026) |
|---|---|---|---|---|---|---|
| rest_AIY | median V of AIYL/R after 5 s, mean of the pair | both | -53 mV, no spread, no n | none: reported only | measured (point) | Naudin et al. 2022 PLoS ONE e0268380 (V0, cited from their ref 23) |
| rest_AFD | as AIY | both | -78 mV, no spread, no n | none: reported only | measured (point) | Naudin et al. 2022 |
| rest_AWA | as AIY | both | -75.3 mV, "SEM = 4.7 mV", Gaussian fit, n = 27 traces | -84.7 to -65.9 mV | measured; band reading inferred | Liu, Kidd, Dobosiewicz & Bargmann 2018 bioRxiv 359935v1 Fig 2E |
| pc3_frac | GCaMP7f F / mean F of the 302 neurons resampled at 0.600 s, z-scored, top-3-PC variance fraction on random 135-neuron subsets (median of 50) | food | 0.440 +- 0.057 (SD), n = 60 animals | 0.353 to 0.506 (P5-P95) | measured (computed) | Atanas et al. 2023 Cell 186:4134, Zenodo 8185377, the 60 open atanas2023_main animals |
| gcamp_range | per neuron P95 - P5 of F / mean F (resampled; from 8 Nov 23:25, was dF/F0), median over neurons | food | 0.718 +- 0.161 (SD), n = 60 | 0.567 to 0.983 (P5-P95) | measured (computed) | Atanas 2023, F / mean F |
| ca_rest_uM | median over neurons of each one's median Ca | both | none opened | none: reported only | | |
| pump_hz | completed pumps (organs_pharynx's count) per s after 5 s | food | 4.76 +- 0.26 Hz (SD), n >= 24 | 4.24 to 5.28 Hz | measured | Zhou et al. 2015 J Lipid Res, PMC4617398 (285.7 +- 15.5 /min, N2 on a lawn, 20 C) |
| pump_hz_off | as pump_hz | nofood | 1.37 +- 0.18 Hz after 90 min off food (SD); 0.09 +- 0.03 Hz in M9 (spread type not stated, n = 31) | 0.03 to 1.73 Hz | inferred band (two sources, neither at 0-200 s off food) | Zhou 2015; Hiebert et al. 2020 microPubl Biol, PMC7255870 |
| dmp_period_s | mean of expulsion-to-expulsion intervals (needs >= 2) | food | 45 s, SD about 3 s (within an individual) | 39 to 51 s | measured | Liu & Thomas 1994 J Neurosci 14:1953, PMC6577142 (abstract). Kwan et al. 2008 PMC2409367: 46.4 s, CV 5.5%, L4, 20 C, inside |
| egg_inactive_min | mean gap between active phases (eggs < 300 s apart form one phase) | food, >= 1800 s | inter-cluster intervals exponential, tau2 ~ 20 min; no spread or n | 10 to 40 min | inferred band (factor 2 width guessed) | Zhang, Schafer & Breitling 2010 BMC Syst Biol, PMC2887794 |
| egg_intra_s | mean interval inside an active phase | food, >= 1800 s | tau1 ~ 20 s; no spread or n | 10 to 40 s | inferred band (guessed width) | Zhang 2010 |
| bwm_rest_mV | median over the 95 BWM somata of each one's median V | both | -25.0 +- 1.0 mV SEM, n = 27 (dissected) | -35.4 to -14.6 mV | measured (SD derived) | Gao & Zhen 2011 PNAS 108:2557, PMC3038695 |
| bwm_spike_hz | upward crossings of -10 mV per firing muscle per s | both | 0.73 +- 0.14 Hz SEM, n not attached (27 assumed) | 0 to 2.19 Hz | measured (SD derived, n inferred) | Gao & Zhen 2011 (threshold about -10 mV; about 80% of preparations fire) |

Also reported, not scored: the GCaMP per-neuron SD and its split into white imaging noise and signal
(`vitals.noise_sd`: noise^2 = 2 D1 - D2 from frame differences, the estimate atanas_noise.py made on the data; it reads
high by S^2 (1 - a)^2 for an exponential signal, test_noise_sd_on_slow_signal), intestinal Ca peaks and their period (> 0.3 uM, >= 10 s apart, on the mean of int9L and
int9R, the pacemaker ring, as wbody2's `dmp_trace.py`; until 8 Nov 23:06 the max over all 20 cells, which peaks
whenever any ring peaks), the
BWM fraction firing, the neuron fraction above -20 mV, the median neuron voltage, mean |curvature|.

Not reachable through free sources (agent search, 8 Nov): Raizen, Lee & Avery 1995 pumping, Thomas 1990 defecation
numbers, Waggoner 1998 egg-laying statistics, Ramot 2008 AFD rest (a snippet's "-41 +- 2 mV" was never opened and is
not used), Liu, Golowasch, Marder & Abbott 1998 (J Neurosci blocked every route; it matters for maturation).

### How the Atanas bars were set (pre-registered in the script's docstring before any model run was scored)

The held-out lock (`heldout.exclude("atanas2023", ...)`) drops the 20 locked animals before any file is opened; only
the 60 open animals were copied off backhouse and read. For each animal, `traces_array_F_Fmean` (F / mean F per
neuron, finite columns) cut into non-overlapping 195 s windows (the model's 200 s less the 5 s settle), the
statistic per window, the median over the animal's windows. Measured over the 60: frame interval 0.600 s (median),
ROI count 135 (median; P5-P95 105-151), PC3 fraction P5 0.353, median 0.444, P95 0.506 (whole recordings: 0.343 to
0.519). The model is scored on 135-neuron random subsets because the fraction depends on how many neurons enter.

## Running it

    python -m wormemu.fit.vitals run food 200 OUTDIR        # backhouse; writes OUTDIR/food.json and food.npz
    python -m wormemu.fit.vitals table OUTDIR               # the markdown table

Cost (the EKI forward cost, measured): see the results section.

## Results

(filled by each battery run; the night file carries the table for each Director merge)

### 8 Nov 2026, f8e7699 (main 41ea9aa merged), default worm, seed default, 200 bio-s per condition, backhouse, one core

All measured. `python -m wormemu.fit.vitals table` on the two result directories:

| Sign | Unit | Published band (mean +- 2 SD, or range) | food (200 s) | nofood (200 s) |
|---|---|---|---|---|
| AIY soma, median voltage | mV | no opened measurement | -52.5 (no bar) | -53.8 (no bar) |
| AFD soma, median voltage | mV | no opened measurement | -56.5 (no bar) | -57.7 (no bar) |
| AWA soma, median voltage | mV | -84.7 to -65.9 | -58.5 (miss) | -59.3 (miss) |
| whole-brain GCaMP: variance fraction in the top 3 PCs (z-scored, 195 s windows, 135 neurons) | 1 | 0.353 to 0.506 | 0.0559 (miss) |  |
| GCaMP per-neuron range (P95 - P5 of dF/F), median over neurons, 195 s windows | dF/F | 0.567 to 0.983 | 0.0976 (miss) |  |
| neuron soma Ca, median over neurons of each one's median | uM | no opened measurement | 0.0504 (no bar) | 0.0503 (no bar) |
| pharyngeal pumping rate on food | Hz | 4.24 to 5.28 | 0 (miss) |  |
| pharyngeal pumping rate off food | Hz | 0.03 to 1.73 |  | 0 (miss) |
| defecation period (expulsion to expulsion) on food | s | 39 to 51 | none (not produced) |  |
| egg-laying: inactive phase duration, mean | min | 10 to 40 | none (too short) |  |
| egg-laying: interval between eggs inside an active phase, mean | s | 10 to 40 | none (too short) |  |
| body-wall muscle, median voltage | mV | -35.4 to -14.6 | -30.4 (in) | -30.8 (in) |
| body-wall muscle action potentials per firing muscle | Hz | 0 to 2.19 | 2.89 (miss) | 2.83 (miss) |
| physical (finite, V in reversal bounds, conc >= 0) | | | yes | yes |
| wall per bio-s | s | | 12.1 | 11.9 |

1 of 10 signs with a bar in (BWM rest), 6 miss, 3 not produced or too short; physical in both. Activity (from the stored
traces, after the 5 s settle): per-neuron V range (P95 - P5) median 2.5 / 2.4 mV, 45 / 42 of 302 neurons above 5 mV,
none above 20 mV; no neuron's GCaMP range above 0.2 dF/F. The brain sits within a few mV of rest, so the PC3 and
GCaMP misses are a quiet brain, not a readout fault (inferred). Against the first pass (103ece3): AWA rest moved from
-53.1 to -58.5 mV (the AWA Kir merge), toward the bar but still 7.4 mV short of it.

Intestinal Ca, re-read from the stored f8e7699 traces after the int9 fix (8 Nov 23:06, measured, no new run): the
old max-over-cells readout's 16.8 s was the artefact the Director flagged (10 peaks from different rings). The
int9L/R mean peaks 4 times, intervals 52.1, 49.8, 49.0 s (mean 50.3 s), in both conditions, inside the published
39-51 s. The scored sign is unchanged (expulsion to expulsion, as registered): still 0 expulsions. So the intestinal
clock runs near the right period and the step from int9 Ca to the expulsion never fires (inferred; the DMP motor chain
is wbody2's, reported to them).


### 8 Nov 2026 23:25: the GCaMP signs read imaging noise (template f8e7699, stored traces, no new run)

Measured unless marked. From `/tmp/weki/battery_f8e7699/{food,nofood}.npz` (50 ms samples, after the 5 s settle):

- Every neuron's GCaMP range is about 0.10, including RMFR, whose Ca does not move at all (range 0.000 nM). The
  per-neuron GCaMP SD is 0.0301 against the module's added noise of 0.03; with the noise subtracted the signal SD
  is 0.0018 dF/F (median; P95 0.0068; largest IL2DL 0.039). Lag-1 autocorrelation at 50 ms 0.005: white. So both
  GCaMP signs of the template are the noise floor: P95 - P5 of white noise is 3.29 SD = 0.099 (derived; measured
  0.098), and the top-3-PC fraction of 135 white columns over 325 frames is about 0.058 (Marchenko-Pastur edge,
  derived; measured 0.056).
- Ca barely follows voltage: the neurons that swing 14-15 mV (AS07-AS09) raise Ca by 4 nM over the 50 nM floor
  (max 59 nM); the largest neuron Ca anywhere is 112.6 nM (IL2DL, the one neuron reaching +5 mV). So the quiet GCaMP
  is three stacked shortfalls: small voltage swings (median range 2.5 mV), a Ca chain that converts 15 mV into 4 nM,
  and an indicator whose dF/F from 4 nM at 50 nM is under the imaging noise. The second is the Ca-chain problem
  wbrain2's bulk Ca pool addresses (inferred).
- Atanas's open animals for comparison (atanas_noise.py): per-neuron SD 0.293 F / mean F (P5-P95 0.215-0.411),
  imaging noise 0.0417 (2 D1 - D2; 0.0257-0.0682) or 0.0371 (AR(1)-exact; 0.0222-0.0656). Their signal SD is
  about 0.29 (derived from the medians), about 100 times the template's 0.003 (F / mean F, rescored below).
- Rescored with the new readout (F / mean F, the run's own 0.03 noise): gcamp_range 0.0947 / 0.0952, pc3_frac
  0.0561 / 0.0560 (food / nofood), signal SD 0.0032 / 0.0031. Both still miss; the verdicts do not change.
- Hazard closed: obs_noise_dff is one of the fit numbers (bounds 0 to 0.2) and noise alone reaches the gcamp_range bar
  at 0.172 (derived, 0.567 / 3.29). It is now set per experiment at the dataset's measured noise (FIT_GENERAL section
  1). Prior draws carry it too: seed 1's 0.176 gives 0.579 from noise alone, so the prior-predictive table reports
  each draw's noise and signal SD (amendment of 23:24, before any result was read).

### 9 Nov 2026: prior predictive (f8e7699, 9 draws)

Measured unless marked. Nine draws of the prior (`sample_worm(s)`, s = 1-7, 9, 10; seed 8 was not drawn), food, 200
bio-s each, f8e7699's code, backhouse, one core each; the registered script `scripts/worm/fit/prior_predictive_table.py`
against the template battery above. The registered question: does any draw reach PC3 (0.353-0.506) and the GCaMP
range (0.567-0.983) from the brain? A pass that the drawn imaging noise reaches alone does not count. Admissible
draws (joint.check passes): 1, 4, 7, 9, 10.

**Answer: no.** pc3_frac is in its bar in 0 of 9 (0 of 5 admissible); every value is 0.0561-0.0570, the white-noise
floor (template 0.0559). gcamp_range from the brain: 0 of 9 (0 of 5). Seed 1's 0.571 is inside the bar, but its drawn
noise alone gives 0.579 (and seed 1 is not physical).

| Sign | Bar | template | 1 | 2 (x) | 3 (x) | 4 | 5 (x) | 6 (x) | 7 | 9 | 10 | in: all | admissible |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| rest_AWA (mV) | -84.7 to -65.9 | -58.5 | -51.2 | -66.8 | -35.2 | -61.4 | -41.4 | -38.8 | -35.5 | -54.9 | -59.5 | 1 of 9 | 0 of 5 |
| pc3_frac | 0.353 to 0.506 | 0.0559 | 0.0564 | 0.0561 | 0.0562 | 0.0564 | 0.0567 | 0.0565 | 0.057 | 0.0563 | 0.0567 | 0 of 9 | 0 of 5 |
| gcamp_range | 0.567 to 0.983 | 0.0976 | 0.571 | 0.241 | 0.209 | 0.449 | 0.114 | 0.421 | 0.348 | 0.214 | 0.516 | 0 of 9 from the brain | 0 of 5 |
| pump_hz | 4.24 to 5.28 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 of 9 | 0 of 5 |
| dmp_period_s, egg signs | | none | none in all 9 | | | | | | | | | 0 of 9 | 0 of 5 |
| bwm_rest_mV | -35.4 to -14.6 | -30.4 | -30 | -31.5 | -25.9 | -36.9 | -28.8 | -33.2 | -35.5 | -25.4 | -25.3 | 6 of 9 | 2 of 5 |
| bwm_spike_hz | 0 to 2.19 | 2.89 | 1.47 | 2.11 | 2.31 | 0.236 | 3.9 | 0.262 | 1.69 | 5.74 | 13.8 | 4 of 9 | 2 of 5 |
| physical | | yes | no | yes | yes | yes | yes | yes | yes | yes | yes | 8 of 9 | |
| obs_noise_dff (drawn) | | 0.03 | 0.176 | 0.0736 | 0.0641 | 0.138 | 0.0348 | 0.13 | 0.106 | 0.0661 | 0.158 | | |
| noise-only range, 3.29 x noise (derived) | | 0.0987 | 0.579 | 0.242 | 0.211 | 0.453 | 0.114 | 0.426 | 0.349 | 0.217 | 0.52 | | |
| GCaMP signal SD (F / mean F) | | 0.0032 | 0 | 0.0063 | 0.0057 | 0 | 0.0079 | 0.0155 | 0 | 0.0125 | 0.0484 | | |
| range under Atanas's noise, 3.29 sqrt(sig^2 + 0.0417^2) (derived) | | 0.138 | 0.137 | 0.139 | 0.138 | 0.137 | 0.14 | 0.146 | 0.137 | 0.143 | 0.21 | | |
| neurons with V range > 5 mV (of 302) | | 45 | 57 | 35 | 103 | 136 | 156 | 15 | 88 | 5 | 65 | | |
| wall per bio-s (s) | | 12.1 | 38.6 | 41.1 | 40.9 | 29.6 | 27.2 | 29.4 | 19.2 | 19.6 | 19.9 | | |

(x): not admissible. No draw laid an egg, so the LGC-55 explicit-step condition (night file 01:40) never arose.

- **Why (stored records, 50 ms samples after the settle).** Soma Ca sits at its 50 nM floor in every draw (median
  50.1-51.0 nM). Its P95 - P5 range is 0.50-2.11 nM (median over the neurons whose V range exceeds 5 mV), and at most
  2-15 nM over all 302, even in seed 5, where 82 neurons reach a V P95 above -30 mV. Across neurons the GCaMP range
  tracks the Ca range only in seed 7 (r 0.58; 0.00-0.19 in seeds 1-6, 0.04 in seed 9, -0.01 in seed 10). So the
  link that fails across the prior is V to soma Ca, under the default Ca chain (Nicoletti's microdomain pool,
  cainternm): the box of the prior does not escape it. wbrain2 has the cause (the `ca_bulk` toggle, default off).
- Seed 10's signal SD (0.048, the largest) does not follow its Ca (r -0.01; max Ca range 2.2 nM) and is not the
  volume rate (1.7 Hz in every draw). Its source is not identified. It is far below the bar either way: under
  Atanas's noise it gives a range of 0.21 (derived).
- What does move across the prior: the BWM signs (bwm_rest_mV 6 of 9 in, bwm_spike_hz 4 of 9; the template misses
  spikes at 2.89 Hz) and AWA's rest (-66.8 to -35.2 mV; in only in seed 2). Pumping, defecation and eggs are absent
  in every draw, as on the template.
- Cost: wall 19.2-41.1 s per bio-s against the template's 12.1. Wave 1 (seeds 1-3) ran at 38.6-41.1, wave 2 (4-6) at
  27.2-29.6, wave 3 (7, 9, 10) at 19.2-19.9, with backhouse's load falling from wave to wave. About 61 CPU-min per run
  (ps); seed 4 profiled on the Mac costs the template's time (FIT_GENERAL section 10), so the spread is the machine's
  load, not the draws.

### 9 Nov 2026: battery on 5e3c87a (main 58246cf's default worm), 200 bio-s per condition, backhouse, one core

Measured unless marked. Same battery as the f8e7699 run above, on main 58246cf's default worm. Since f8e7699: the
head reads the plate's temperature gradient (ad37628), neuromodulator sites use 8 um bins (wneuro, 58246cf), and the
GCaMP signs read F / mean F under Atanas's measured imaging noise, 0.0417 (23:25). Table: `vitals table`.

| Sign | Bar | 5e3c87a food | 5e3c87a nofood | f8e7699 food | f8e7699 nofood |
|---|---|---|---|---|---|
| AIY rest (mV) | none | -52.5 | -53.7 | -52.5 | -53.8 |
| AFD rest (mV) | none | -56.5 | -57.6 | -56.5 | -57.7 |
| AWA rest (mV) | -84.7 to -65.9 | -58.5 miss | -59.3 miss | -58.5 miss | -59.3 miss |
| pc3_frac | 0.353 to 0.506 | 0.0559 miss | | 0.0559 miss | |
| gcamp_range | 0.567 to 0.983 | 0.133 miss | | 0.0976 miss | |
| soma Ca (uM) | none | 0.0504 | 0.0503 | 0.0504 | 0.0503 |
| pumping on / off food (Hz) | 4.24-5.28 / 0.03-1.73 | 0 miss | 0 miss | 0 miss | 0 miss |
| defecation period | 39 to 51 s | not produced | | not produced | |
| egg signs | | too short | | too short | |
| BWM rest (mV) | -35.4 to -14.6 | -30.5 in | -30.4 in | -30.4 in | -30.8 in |
| BWM spikes (Hz) | 0 to 2.19 | 2.97 miss | 2.92 miss | 2.89 miss | 2.83 miss |
| physical | | yes | yes | yes | yes |
| wall per bio-s (s) | | 16.8 | 17.1 | 12.1 | 11.9 |

- **No verdict changes.** 1 of the 10 barred signs is in (BWM rest, both conditions), 6 miss, 3 are not produced or
  too short, as on f8e7699. Rest voltages move by 0.1 mV or less.
- gcamp_range 0.133 is the noise floor under Atanas's noise (3.29 x 0.0417 = 0.137, derived), not the brain: the
  change from 0.0976 is the readout's noise (0.03 before), not the worm.
- Noise alone, one pair (food, noise seed 1 against this run's default; the pre-registered spread, night file 03:03,
  has 1 of 14 runs in): BWM spikes 2.75 against 2.97 Hz, a 0.22 Hz difference; rest voltages within 0.02 mV;
  pc3_frac 0.0564 against 0.0559. So the 0.08 Hz rise in BWM spikes since f8e7699 is inside the noise (inferred from
  one pair; the full spread will say). Wall 16.8-17.1 s per bio-s with one noise run beside the two (load 8-10 of
  28).

## Limitations

1. (Closed 9 Nov 01:36.) The plate went in through a subclass of `body.loop.Body` until `Experiment` carried it.
2. (Closed by main 27f7276.) Up to 910f6f8, `simulate()` set the head's temperature to `Experiment.temperature_C`,
   overwriting the env_temp gradient's value. On the default plate (20 C at 0.5 C/cm) a 200 s run moves under about
   1 mm, so the lost gradient was under about 0.05 C (derived). Since the merge the head reads the plate (simulate
   notes it), so batteries before and after differ by that much in the head's temperature.
3. Atanas's neurons are head neurons found by segmentation; the model's 135 are drawn from all 302.
4. AIY and AFD have points with no spread: reported, not scored, until a recorded population is opened.
5. The BWM bars come from dissected muscle; ours is driven by the intact network.
6. Off-food pumping: neither source is the first 200 s off food.
