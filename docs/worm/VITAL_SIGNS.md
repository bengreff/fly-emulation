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
| Instrument | GCaMP read as GCaMP7f, the indicator Atanas 2023 imaged (methods, PMC10836760, opened). The gcamp module is readout only, so this does not change the worm |
| Temperature | 20 C (`Experiment.temperature_C`; see limitation 2) |
| Recording | every exchange (4.167 ms), every cell; settle 5 s dropped from every readout |
| Lengths | core: 200 bio-s per condition; eggs tier: at least 1800 bio-s (egg signs report "too short" below that) |

`simulate()` builds its Body with no world or environment, so `vitals.plate()` subclasses `body.loop.Body` for the
call to add them, exactly as `scripts/worm/triage/vital_loop.py` does. Nothing else in simulate changes. Request to
wbrain2 (night file): put the world and environment on `Experiment`.

## Physicality, per run (pre-registered)

- finite: every recorded voltage, Ca and module concentration is finite;
- V bounds: every soma voltage stays inside [E_lo - 1 mV, E_hi + 1 mV], E_lo / E_hi the lowest and highest reversal
  potential in this worm's values (34 reversal Specs plus BAAIWorm's literal -80 / +60 mV). A membrane made only of
  conductances cannot leave that interval, so leaving it means a module injects current past it. The 1 mV allows
  integrator overshoot (guessed);
- concentrations >= 0: `ca_uM` and every `out:*_uM / _mM / _nM` recorded.

A run that fails physicality is rejected in the fit (FIT_GENERAL.md). The fraction of neurons above -20 mV is
reported with no bar (none is published; DEBUG_TRIAGE line 18).

## The signs

Band = mean +- 2 SD unless a range is given. SD derived from SEM as SEM x sqrt(n) where only SEM is reported.

| Sign | Readout | Scored in | Published | Band | Label | Source (opened 8 Nov 2026) |
|---|---|---|---|---|---|---|
| rest_AIY | median V of AIYL/R after 5 s, mean of the pair | both | -53 mV, no spread, no n | none: reported only | measured (point) | Naudin et al. 2022 PLoS ONE e0268380 (V0, cited from their ref 23) |
| rest_AFD | as AIY | both | -78 mV, no spread, no n | none: reported only | measured (point) | Naudin et al. 2022 |
| rest_AWA | as AIY | both | -75.3 mV, "SEM = 4.7 mV", Gaussian fit, n = 27 traces | -84.7 to -65.9 mV | measured; band reading inferred | Liu, Kidd, Dobosiewicz & Bargmann 2018 bioRxiv 359935v1 Fig 2E |
| pc3_frac | GCaMP7f dF/F of the 302 neurons resampled at 0.600 s, z-scored, top-3-PC variance fraction on random 135-neuron subsets (median of 50) | food | 0.440 +- 0.057 (SD), n = 60 animals | 0.353 to 0.506 (P5-P95) | measured (computed) | Atanas et al. 2023 Cell 186:4134, Zenodo 8185377, the 60 open atanas2023_main animals |
| gcamp_range | per neuron P95 - P5 of dF/F (resampled), median over neurons | food | 0.718 +- 0.161 (SD), n = 60 | 0.567 to 0.983 (P5-P95) | measured (computed) | Atanas 2023, F / mean F |
| ca_rest_uM | median over neurons of each one's median Ca | both | none opened | none: reported only | | |
| pump_hz | completed pumps (organs_pharynx's count) per s after 5 s | food | 4.76 +- 0.26 Hz (SD), n >= 24 | 4.24 to 5.28 Hz | measured | Zhou et al. 2015 J Lipid Res, PMC4617398 (285.7 +- 15.5 /min, N2 on a lawn, 20 C) |
| pump_hz_off | as pump_hz | nofood | 1.37 +- 0.18 Hz after 90 min off food (SD); 0.09 +- 0.03 Hz in M9 (spread type not stated, n = 31) | 0.03 to 1.73 Hz | inferred band (two sources, neither at 0-200 s off food) | Zhou 2015; Hiebert et al. 2020 microPubl Biol, PMC7255870 |
| dmp_period_s | mean of expulsion-to-expulsion intervals (needs >= 2) | food | 45 s, SD about 3 s (within an individual) | 39 to 51 s | measured | Liu & Thomas 1994 J Neurosci 14:1953, PMC6577142 (abstract). Kwan et al. 2008 PMC2409367: 46.4 s, CV 5.5%, L4, 20 C, inside |
| egg_inactive_min | mean gap between active phases (eggs < 300 s apart form one phase) | food, >= 1800 s | inter-cluster intervals exponential, tau2 ~ 20 min; no spread or n | 10 to 40 min | inferred band (factor 2 width guessed) | Zhang, Schafer & Breitling 2010 BMC Syst Biol, PMC2887794 |
| egg_intra_s | mean interval inside an active phase | food, >= 1800 s | tau1 ~ 20 s; no spread or n | 10 to 40 s | inferred band (guessed width) | Zhang 2010 |
| bwm_rest_mV | median over the 95 BWM somata of each one's median V | both | -25.0 +- 1.0 mV SEM, n = 27 (dissected) | -35.4 to -14.6 mV | measured (SD derived) | Gao & Zhen 2011 PNAS 108:2557, PMC3038695 |
| bwm_spike_hz | upward crossings of -10 mV per firing muscle per s | both | 0.73 +- 0.14 Hz SEM, n not attached (27 assumed) | 0 to 2.19 Hz | measured (SD derived, n inferred) | Gao & Zhen 2011 (threshold about -10 mV; about 80% of preparations fire) |

Also reported, not scored: intestinal Ca peaks and their period (> 0.3 uM, >= 10 s apart, wtriage's readout), the
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

## Limitations

1. The plate goes in through a subclass of `body.loop.Body` (above), until `Experiment` carries it.
2. `simulate()` sets the head's temperature to `Experiment.temperature_C`, overwriting the env_temp gradient's value.
   On the default plate (20 C at 0.5 C/cm) a 200 s run moves under about 1 mm, so the lost gradient is under about
   0.05 C (derived); thermotaxis is not a vital sign. Requested as a fix to wbrain2.
3. Atanas's neurons are head neurons found by segmentation; the model's 135 are drawn from all 302.
4. AIY and AFD have points with no spread: reported, not scored, until a recorded population is opened.
5. The BWM bars come from dissected muscle; ours is driven by the intact network.
6. Off-food pumping: neither source is the first 200 s off food.
