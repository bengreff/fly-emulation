# FIT1: class-level synapse strengths against Randi et al. 2023 (pre-registration)

Status: pre-registered 2026-11-06 (commit 44d3088, 22:39), amended at 22:46 (commit a32642d) and on 7 Nov at 00:05
(Amendment 2), 00:27 (Amendment 3) and 01:46 (Amendment 4, the freeze on worm-v1), all before any scored run (the amendments are listed at the end). Nothing above the line "RESULTS" (added when results exist) changes after the
first scored run; a changed rerun is a new, separately named fit (FIT1b, ...). Code: `scripts/worm/fit1/` (fit1_core, fit1_targets, fit1_loss, fit1_worker, fit1_run). Worker wfit,
night of 6 Nov (`docs/worm/night/2026-11-06_wfit.md`).

**Question.** Can a small set of biological, class-shared synaptic and gap-junction strengths, each inside its
cited range, make the whole 302-neuron model reproduce Randi's signal propagation atlas for stimulated neurons it
never saw? It has to do better than the template, better than predicting zero, and better than the same fit on a
wrong (degree-preserving shuffled) connectome.

**What has been looked at, so the held-out status is honest.** Before the split was drawn I read funatlas.h5's
structure and computed aggregate statistics over all pairs for the night file's Step 1: counts of measured and
significant pairs, medians, the correlation between the 30 s mean and shorter windows, and the shape of a few
average time courses. No per-neuron or per-pair value was printed or used for any choice. After the split, only
training data has been opened: the noise model (s_trial, s_floor), and the training medians given below.

## 1. Data and split (fixed; run 22:30, `fit1_targets.py`)

- **Source.** `funatlas.h5` from the wormneuroatlas package (Randi et al. 2023, Nature 623:406), on backhouse
  `/home/greff/worm-data/randi2023/wormneuroatlas/wormneuroatlas/data/funatlas.h5`.
  - Wild type: strain AML462, 113 animals, 500 ms pulses.
  - unc-31: strain AML508, 18 animals, 300 ms pulses.
- **A term.** For responder i and stimulated j:
  - y = dFF[i, j], the published mean dF/F0 over the 30 s after the pulse, averaged over trials and animals.
  - n = occ1[i, j], its trial count.
  - q = the published q value.
  - i = j is the autoresponse term, which calibrates the actuator.
  - Neuron names are matched to the model's; ventral cord numbers are zero-padded (VB1 -> VB01).
  - AWCON and AWCOFF stay unmatched, because which of AWCL/AWCR is ON differs between animals.
- **Split.** By stimulated neuron, seed 20261106, 20% held out. Of the 171 stimulated neurons that match a model
  cell, 34 are held out and 137 are for training.
  - Held out: ADAR, ADER, ADLL, AFDR, AINL, ASJR, AVBL, AVBR, AVHL, AVJR, BAGL, CEPDL, CEPVR, I2L, I2R, IL2DR,
    M3R, NSMR, OLLR, OLQDL, OLQDR, OLQVR, RIGR, RIML, RIMR, RIPL, RMED, SAAVL, SAAVR, SIBVR, URADR, URAVL,
    URXR, VA01.
  - Terms: training 18,835 (137 autoresponses, 891 significant off-diagonal at q < 0.05); held out 4,719.
- **unc-31.** Every unc-31 term (108 stimulated neurons, 9,011 terms) is sealed for the peptide-layer test
  (section 7). It is not used for anything else.
- **Files** on backhouse `~/worm-night/wfit/fit1/`. The sealed files are mode 400. Only `fit1_eval.py`, written
  and committed before it runs, reads them, once.

  | File | sha256 |
  |---|---|
  | train.npz | 176e9fac1f473f729aaa354b1e6cf95719750254e7f410804f7850d7844cbfd6 |
  | sealed/wt_heldout.npz | ae5b78a21a51c8a2cdc77b77e1594ef9096fdf700749987a6c6efcb1586d6b85 |
  | sealed/unc31.npz | e6cfb83291944737a7c4579dafd19aba18a5038f88ff139f2831d10830be8dbc |

## 2. The simulated experiment (`fit1_core.Experiment`)

- **The brain.** The 302 neurons, built once per worm. No neuron-muscle gap junction or chemical pair exists,
  so the neurons' responses are exact without the muscles.
  - Toggles at the template, except `neuropal` and `gcamp` off. The fit has its own readout, and NeuroPAL's
    expression is not modelled as a load. (Amendment 2: also `quantal_noise` and `channel_noise` off.)
  - Warm-up 5 s. Then one forked child per stimulated neuron, plus a no-light control child, all continuing from
    the same state.
- **The stimulus.** A child lights B3's GUR-3 actuator (`mech.observation`) in its target only, for 500 ms (wt)
  or 300 ms (unc-31).
- **The readout.**
  1. Soma Ca pool from each soma's own Ca current, using Nicoletti 2019's equation in total current
     (cainternm.mod's units bug: night file, Open). (Amendment 2: the brain's own pool, recorded, now that the
     units fix is on main.)
  2. GCaMP6s binding (`observation.binding_step`).
  3. F = 1 + (R - 1) B, sampled at 2 volumes/s.
- **The statistic.** Mean over the volumes in (0, 30 s] of (F_stim - F_ctrl) / F_ctrl. This is Randi's mean
  dF/F0, with F0 taken from the control twin at the same times (it removes the drift that a pre-stimulus
  baseline removes in the data).
- **Integration.** h_dt = 2.0 ms, mechanisms every 10 ms. This was chosen in section 2a from the measured match
  to brain.py's own step (0.5 ms, mechanisms every 1 ms). (Amendment 2: rechecked on the merged code, 2c.)

### 2a. Integration check (`dtcheck.py`, `dtcompare.py`; template values, actuator 1 nS; AVAL, ASHL, AWAL)

Measured on backhouse, 302 neurons, one CPU each, 30 s windows:

| Run | h_dt (ms) | mech_dt (ms) | Wall per window (s) | RMS difference from ref (per target) | r with ref |
|---|---|---|---|---|---|
| ref | 0.5 | 1 | 250 | | |
| a | 0.5 | 10 | 180 | 0 (largest 3e-5) | 1.0 |
| b | 1.0 | 10 | 93 | 1-2e-5 (largest 2.3e-4) | 0.9999 |
| c | 2.0 | 10 | 53 | 4-5e-5 (largest 6.1e-4) | 0.999-0.9996 |

Bar (set before the comparison was read): RMS difference at most 0.1 x s_floor (0.003) for every target. If c
fails it, use the coarsest run that passes. **c passes** by a factor of 60, so the fit uses h_dt 2 and mech_dt 10.
That is 4.7x faster than ref (derived from the walls). The check was at the template, where responses are small.
fit1_eval.py repeats it at main's fitted mean, with the same bar, before any held-out scoring.

Later the same night, still on the old code, at the large-response values of 2b row 3 (refbig, 23:34): h_dt 2 RMS
at most 0.0006 and h_dt 5 at most 0.0015 from the reference (measured). Both pass. Section 2c redoes the check on
the merged code.

## 3. The fitted values (23; everything else at the template)

Each value is shared by its class across the whole worm (never per pair or per synapse). Each is bounded to its
range by a sigmoid, on a log scale where the transform is log. Templates and ranges come from the ledger row
where one exists, otherwise from the module's spec (receptors.py, observation.py). Fitted results will be
labelled **fitted (FIT1)**, keep their ranges, and are never relabelled measured.

| id | Template | Range | Range basis | Transform |
|---|---|---|---|---|
| syn_strength_per_pair (one value for every pair) | 0.447 | 0.1-2 | guessed | log |
| rec_acr16_gamma_pS | 40 | 20-90 | guessed | log |
| rec_nachr_gamma_pS | 33 | 20-60 | inferred | log |
| rec_acc_gamma_pS | 30 | 10-80 | guessed | log |
| rec_glr_gamma_pS | 15 | 5-30 | inferred | log |
| rec_nmr_gamma_pS | 50 | 20-70 | inferred | log |
| rec_glucl_gamma_pS | 20 | 5-60 | guessed | log |
| rec_gabacl_gamma_pS | 30 | 25-37 | measured | log |
| rec_gabacat_gamma_pS | 20 | 5-60 | guessed | log |
| rec_mod1_gamma_pS | 20 | 5-60 | guessed | log |
| rec_lgc53_gamma_pS | 20 | 5-60 | guessed | log |
| rec_acr23_gamma_pS | 30 | 10-60 | guessed | log |
| rec_tmax_acetylcholine_uM | 100 | 10-1000 | guessed | log |
| rec_tmax_glutamate_uM | 100 | 10-1000 | guessed | log |
| rec_tmax_gaba_uM | 100 | 10-1000 | guessed | log |
| syn_exc_Vth (release threshold, mV) | -20 | -45 to -20 | published_fit | lin |
| syn_exc_delta (release slope, mV) | 5 | 2-10 | published_fit | log |
| gap_open_channels_per_em | 1.826 | 0.167-20 | guessed | log |
| obs_opto_g_nS | 0.3 | 0.05-2 | guessed | log |
| obs_opto_tau_off_ms | 500 | 50-3000 | guessed | log |
| obs_gcamp6s_thalf_ms | 550 | 300-2000 | guessed | log |
| capool_f (free Ca fraction of the soma pool) | 0.001 | 0.00033-0.003 | published_fit; range guessed (factor 3) | log |
| capool_tca (Ca removal time constant, ms) | 50 | 16.7-150 | published_fit; range guessed (factor 3) | log |

How this maps onto the brief's list:
- **Unit conductance per receptor class.** The 11 rec_*_gamma values. A synapse's conductance is g_em x
  n_em / sites x share x gamma_c / gamma_lacr, so gamma_c sets the class's strength relative to the reference
  class.
- **Release gain per transmitter.** rec_tmax, the peak transmitter concentration per release, one per fast
  transmitter. syn_exc_Vth and syn_exc_delta are the shared release curve.
- **Gap-junction unit conductance.** gap_open_channels_per_em is the only free one. The code has one value for
  every junction (g = open channels per EM contact x innexin unitary conductance); no per-innexin-class value
  exists to fit.
- **Actuator and GCaMP scale.** The three obs_ values, and the soma Ca pool's capool_f and capool_tca. These
  two set the readout's Ca transient. They set the brain's own pool too, but the units bug keeps that pool at
  rest for any value in range.

Not fitted, with reasons:
- rec_lacr_gamma_pS: it is the reference the others are relative to, so it cancels.
- lgc55: 6 sites in the whole worm, 0.55 nS in total.
- The monoamine and betaine tmax: too few sites; they are degenerate with their classes' gamma.
- Every kinetic constant.
- gap_innexin_unitary: only its product with the open-channel count enters.
- capool_vcell: only f / vcell enters the pool.
- GCaMP Kd, Hill and range: measured (Chen 2013), narrow ranges.
- The peptide, slow-signalling and plasticity values: not identifiable from 30 s single-pulse responses with this
  budget.

## 4. Objective (training data only)

- **Loss.** The reduced chi-square over the training terms whose stimulated neuron is in the generation's
  mini-batch (off-diagonal terms and autoresponses together):

  L = mean over terms of ((m_ij - y_ij) / sigma_ij)^2, with sigma_ij^2 = s_trial^2 / n_ij + s_floor^2.

- **Noise model** (training data only):
  - s_trial = 0.068, the robust within-pair SD: 1.4826 x the median absolute deviation of each trial from its
    pair's mean, over non-significant training pairs, 71,467 trial values. A pooled variance (0.112) is driven
    by a few huge trials and is not used.
  - s_floor = 0.030, the median |dFF| of non-significant training off-diagonal pairs. It stands for the model
    and data errors that more trials do not remove.
- **Baselines on training data** (derived from train.npz):
  - The zero predictor scores L = 4.72: 3.71 over off-diagonal terms, 142 over autoresponses.
  - Training medians (aggregate): autoresponse 0.43; significant off-diagonal 0.13; non-significant 0.016.

## 5. Search (`fit1_run.py`)

- **Method.** CMA-ES (pycma 4.5.0) in the unbounded coordinates.
  - x0 = the template, clipped 2% inside each range. sigma0 = 1.0, population 16, seed 20261106.
  - Each generation scores every candidate on the same mini-batch: 4 training stimulations, drawn by seed
    (20261106, generation).
  - The answer is the CMA mean when the fit stops.
- **One start per wiring.** Two fits run side by side on backhouse with the same seed, the same batches, the same
  start and the same stopping rule:
  - **main**: the real wiring.
  - **shuf**: the wrong model, below.
  - Several starts are not affordable at this cost (section 2a): the two fits fill the 16 CPUs the night allows.
- **Checkpoints, every generation**, in `~/worm-night/wfit/fit1/<fit>/`:
  - state.pkl, the pickled strategy.
  - gen_NNNN/, the candidates, jobs, evaluations and result.json.
  - history.csv: best, median, sigma and wall time per generation.
  - mean.json: the current mean as values, and which are pinned near a bound.
  - driver.pid and pids.txt.
  - DONE, with the reason, when it stops.
- **Resuming.** Rerun the same command. A generation in progress keeps its candidates and its finished
  evaluations.
- **Failed evaluations** (Amendment 3). An evaluation fails if its worker leaves no result after one retry, or if
  any of the model's values for the batch's terms is not finite. A failed evaluation is told to CMA as 10 times
  the worst loss of its generation; if every evaluation of a generation fails, the fit stops.

## 6. Stopping rule

Each fit stops at the first of:
1. a file STOP in its directory (Ben or the Director);
2. the deadline, 2026-11-07 17:00 CST (when backhouse's evening cap starts). Ben or the Director may extend it
   before it is reached, for both fits alike (resume with a later `--deadline`). Each extension is recorded here
   with its time; none may depend on held-out data;
3. 200 generations;
4. pycma's own termination criteria;
5. a plateau: after at least 40 generations, the mean of the median loss over the last 10 generations is not 1%
   below the mean over the 10 before.

The two fits are scored at their own stopping points. If shuf stops with fewer generations than main for a reason
other than its own plateau, its held-out score is reported with that caveat, and P2 below waits until shuf is
resumed to main's generation count.

## 7. Held-out scoring (once, after both fits are DONE)

`fit1_eval.py` will be written and committed before it opens the sealed files. It runs these models on all 34
held-out and all 137 training stimulations, with the same experiment and integration:

| Model | Values | Wiring |
|---|---|---|
| fit | main's mean | real |
| shuf-fit | shuf's mean | shuffled (seed 1, as fitted) |
| template | template | real |
| zero | predicts 0 everywhere | |

- **Reported for each:** L (all terms, off-diagonal, autoresponse), and the sign agreement and Pearson r over the
  significant (q < 0.05) held-out off-diagonal pairs.
- **Uncertainty:** 2,000 bootstrap resamples of the 34 held-out stimulated neurons, seed 20261106, as paired
  differences.

Pass criteria, on held-out terms:
- **P1.** L(fit) < L(template) and L(fit) < L(zero), each with the 95% bootstrap interval of the difference
  excluding 0.
- **P2 (the wrong model).** L(fit) < L(shuf-fit), with the 95% interval excluding 0.
- **P3.** Sign agreement of fit on significant pairs > 0.5, and > shuf-fit's.
- **P4 (descriptive).** r of fit on significant pairs, compared with shuf-fit's.

Verdicts:
- **PASS** = P1, P2 and P3.
- **PARTIAL** = P1 only: the fitted values improve the model, but the data does not show that the wiring carries
  the improvement.
- **FAIL** = P1 fails.
- **VOID** (Amendment 3) = any model gives a non-finite value for any term of the simulated stimulated neurons.
  The counts are reported; models are never compared on different terms.
- **Falsifier:** if P2 fails, then gain and readout values, not the wiring, explain the fit.

**unc-31 test (sealed, once, after P1-P4).**
- Run main's fitted values with the `peptides` toggle off (UNC-31/CAPS is needed for dense-core vesicle release),
  300 ms pulses, on all 108 unc-31 stimulated neurons. Run the same with peptides on.
- **U passes** if L(peptides off) < L(peptides on) on the unc-31 terms, with the 95% bootstrap interval (over
  stimulated neurons) excluding 0.
- If the two differ by less than 0.01 in L, report "the peptide layer is not tested by 30 s single-pulse data"
  rather than pass or fail.

## 8. Known limits, declared before scoring

- **The template's responses are short and small.** With the actuator at 1 nS, the autoresponse peaks at dF/F
  0.24 (ASHL) and 0.31 (AWAL), then decays within about 3 s. Its 30 s mean is 0.014-0.018, against a training
  median of 0.43 (measured, dtcheck c). The readout values (actuator, GCaMP, Ca pool) can reach the data inside
  their ranges, but only near their upper bounds (2b). Two risks follow:
  - Values pinned at bounds at the end will be reported as a model or range limit, not hidden.
  - The synaptic values may absorb a readout deficit. The wrong-model comparison (P2) is the guard against
    reading that as wiring.
- **AVAL barely responds to its own actuator** (0.048 at all upper bounds). AVAL is not held out, but the big
  interneurons' columns will fit poorly.
- **The readout's Ca pool** (updated by Amendments 2 and 4, before launch). B1's units fix landed in merge 1, so
  the readout reads the brain's own Ca, the pool its Ca-gated channels see; on worm-v1 each neuron's pool is
  sized by its own volume. The pool is one well-mixed compartment per cell (mech/ca_volume's validity range).
- **Levamisole** (Randi's immobiliser, an L-AChR agonist) is not modelled.
- **Mini-batches** of 4 make the loss noisy between generations; the plateau rule uses 10-generation means for
  that reason.
- **One start** per wiring, so a local optimum cannot be ruled out.

### 2b. Reach at the upper bounds (development check, no data scored)

h_dt 2, template values except those listed; the 30 s mean autoresponse (measured). The training median it is
compared with is 0.43.

| Values changed from the template | AVAL | ASHL | AWAL |
|---|---|---|---|
| obs_opto_g_nS 1 | 0.001 | 0.014 | 0.018 |
| obs_opto_g_nS 2, obs_opto_tau_off_ms 3000, obs_gcamp6s_thalf_ms 2000 | 0.006 | 0.076 | 0.105 |
| the same, plus capool_f 0.003 and capool_tca 150 | 0.048 | 0.64 | 1.09 |
| the same, plus syn_strength_per_pair 2 | 0.013 | 0.13 | 0.57 |

## Amendment (22:46, commit a32642d, before any scored run)

capool_f and capool_tca were added to the fitted values (21 to 23). Reason: the reach check (2b) showed that,
with the actuator and GCaMP values alone, the model cannot reach the data's autoresponse magnitude inside their
ranges. The Ca pool values can, inside theirs. The only data used was the aggregate training median (0.43).
Before this, the only runs on training data were a plumbing test of the driver (2 s windows, 2 generations,
population 4, `~/worm-night/wfit/smoke_run`). Its losses mean nothing and were not used.

## Trial before the freeze (development, training data only)

From 22:47 a trial of both fits runs on backhouse (`~/worm-night/wfit/trial/`, commit a32642d code), with exactly
the settings above. It exists to check that full-size generations finish and checkpoint, to measure throughput
under full load, and to catch failures before the real launch. It is stopped at the freeze. Its training losses
are seen. Its answer is never scored on held-out data. Any change made because of it is listed here, with the
reason, before the real launch. The real fits start from the template on the worm-v1 code, in
`~/worm-night/wfit/fit1/{main,shuf}`.

## Amendment 2 (2026-11-07 00:05, before any scored run; no held-out or unc-31 data opened)

Main changed at 23:15 (Director merge 1, d892794). It was merged into this branch at 23:26 (8aea58b). The real fits
run on worm-v1, the 02:30 freeze. Changes made because of merge 1, each with its reason:

1. **The readout reads the brain's own Ca pool.** B1's units fix landed (`mech/capool.py`, `ca_pool_units`
   total_current, on by default). With vcell set to V_cell / (10 A_soma), cainternm.mod computes, term for term,
   the equation the readout computed before. The readout now records each soma's cai. capool_f and capool_tca now
   set the pool the brain's Ca-gated channels see, not only the readout. Section 8's third limit is resolved. The old
   computed path remains for `ca_pool_units` off.
2. **Both noise forms are off in the fit (`quantal_noise` off, `channel_noise` off).** Both are on by default after
   merge 1. Reasons:
   - **Twin desync (measured on the template, 10 s windows, h_dt 2).** With quantal noise on, the light changes the
     voltage-graded vesicle rates in the stimulated child, which shifts the Poisson draws for the rest of the run.
     The stimulated child and its control twin then carry different noise. Spontaneously active cells show large
     spurious responses (IL2DL 1.31 and 0.56, SDQR 0.23, SDQL -0.12), against s_floor 0.03. With quantal noise
     off these vanish, and what remains is wired (ASHL to ASKL, ASHR, RMGL). Two control twins with no light
     are identical in every form (largest difference 0), so the fork itself is exact.
   - **Validity range.** Both noise forms state one: brain steps up to about 1 ms. The fit's mechanism step is 10 ms.
   - **The mean is kept.** Quantal off is qn = 1, the deterministic synapse, with E[qn] = 1. Channel noise is
     zero-mean. The data's statistic is a trial mean.
   - **Channel noise's measured effect at the template** (10 s windows): ASHL autoresponse 0.0121 with it on,
     0.0125 with both off.
   - fit1_eval's dtcheck adds a run of the fitted mean with channel noise on, at brain.py's own step. Its RMS
     difference from the noise-off reference is reported, not used as a criterion.
   - The toggles are recorded in each fit's config.json. Held-out scoring uses the same toggles.
3. **Integration rechecked on the merged code (2c): h_dt 5 ms, mechanisms every 10 ms, replaces h_dt 2.** It passes
   the same bar by 14x at both value sets and costs 1.6x less than h_dt 2 at the same load (measured). h_dt 10 also
   passes, but only by 1.6x, and its largest single-cell error (0.031) equals s_floor. The fitted-mean recheck in
   fit1_eval would void the fit if it failed, so the margin matters.
4. **Reach on the merged code** (h_dt 2, both noise forms off, 30 s means of the autoresponse; 2c):
   - template, actuator 1 nS: AVAL 0.0007, ASHL 0.012, AWAL 0.0023;
   - 2b row-3 values: AVAL 0.043, ASHL 0.53, AWAL 0.75.
   The data's training median is 0.43, so the readout values can still reach it inside their ranges.
5. **Trials.** Trial 1 (old code) was stopped at 23:28, by PID, during generation 1. Trial 2 runs on the merged
   code with the settings above, from 23:41 (`~/worm-night/wfit/trial2/`), under the same rules as trial 1
   (development, training data only, never scored on held-out data).

### 2c. Integration check on merge 1 (both noise forms off; AVAL, ASHL, AWAL; 30 s windows)

Measured on backhouse at 23:34-00:05, ten runs in parallel (one CPU each), so the walls are at partial load.
"Template" is the template with the actuator at 1 nS. "Large" is 2b row 3. RMS difference per target from the
reference (h_dt 0.5, mechanisms every 1 ms) with the same values:

| Run | h_dt (ms) | mech_dt (ms) | Template RMS (largest) | Large RMS (largest) | Wall per window (s) |
|---|---|---|---|---|---|
| reference | 0.5 | 1 | | | 465 |
| c2 | 2 | 10 | 0-1e-5 (2e-5) | 1.0-2.9e-4 (0.005) | 80 |
| **c5 (chosen)** | 5 | 10 | 0-1e-5 (4e-5) | 1.2-2.2e-4 (0.003) | 50 |
| c5m20 | 5 | 20 | | 1.2-2.4e-4 (0.003) | 44 |
| c10 | 10 | 10 | | 4.2e-4-1.9e-3 (0.031) | 38 |

The strong-coupling corner (measured 00:29-01:08, development, no data scored), because a large step can go
unstable when gap junctions and synapses are strong. All 16 coupling values (syn_strength_per_pair, the 11 gamma,
the 3 tmax, gap_open_channels_per_em) sit at 95% of their log range. "Strong" keeps the readout at the template;
"strong + large" also puts the readout at 2b row 3. The reference is again h_dt 0.5, mechanisms every 1 ms:

| Run | h_dt (ms) | mech_dt (ms) | Strong RMS (largest) | Strong + large RMS (largest) | Wall per window (s) |
|---|---|---|---|---|---|
| reference | 0.5 | 1 | | | 455-489 |
| s2 | 2 | 10 | | 0-3.2e-4 (0.0047) | 108 |
| **s5 (chosen)** | 5 | 10 | 0-0 (7e-5) | 0-4.1e-4 (0.0071) | 61-77 |

h_dt 5 passes the bar at the corner by 7x. Strong gap coupling shunts the stimulated cell, so the strong-only
autoresponses are small (ASHL 0.003, AWAL 0.002); with the large readout, AWAL reaches 0.36.

## Amendment 3 (2026-11-07 00:27, before any scored run; no held-out or unc-31 data opened)

Failed evaluations are now defined in section 5. Before this, the driver gave a missing result 10 times the worst
loss (unchanged), but scored a run with some non-finite values on its finite terms only. A partly blown-up run
could then score well on fewer terms. Now any non-finite value on the batch's terms fails the evaluation
(`fit1_run.score_one`, tested in `tests/test_worm_fit1.py`). No evaluation in trials 1 or 2 had a non-finite
value; re-scoring trial 2's 80 finished evaluations with the new code gives the same losses (largest difference 0).

The held-out scoring had the same gap: models were scored on their finite terms, and the zero predictor on the
first model's. Now every model must give a finite value for every term of the simulated stimulated neurons, or the
verdict is VOID (section 7) and the counts are reported; the same applies to U. The training-data plumbing test
re-scores identically (2 stimulations, 273 terms, no non-finite values).

## Amendment 4 (2026-11-07 01:46, the freeze; before any scored run; no held-out or unc-31 data opened)

1. **Code.** The Director tagged `worm-v1` = 602d21c at 00:49 (main at 00:41, before the catalog merge) as the
   frozen template for this fit. It is merged into worktree-wormfit as d174f16. The model tree there (src,
   data/worm, third_party, pyproject.toml) is identical to the tag; the fit scripts are this branch's. Both fits
   run d174f16's tree, copied with `git archive` to `~/worm-night/wfit/repo_v1/` (its COMMIT file holds the hash).
   100 worm tests pass on d174f16 (the pycma test is skipped on the Mac and passes on backhouse).
2. **What changed for the fit since merge 1.** Three modules are new and on by default:
   - `channels` (row 4): five Nicoletti 2024 channels (KQT-1, UNC-103, EXP-2, SLO-1 and SLO-2 iso) on the somas
     that have them;
   - `ca_volume` (row 6): each neuron's Ca pool sized by its own whole-cell volume in the BAAIWorm morphology
     (derived), instead of one capool_vcell for every neuron. capool_vcell therefore no longer enters; capool_f
     and capool_tca still do, and the readout still reads the brain's own Ca;
   - `cells_passive` (row 1): 46 isolated sensillar glia and 8 pharyngeal end-organ cells on Cook's gaps.
   The ranges of the 23 values are unchanged (checked, `freeze_check.py`).
3. **Template, measured.** 10 s windows: ASHL's autoresponse fell from 0.0126 to 0.0078, AWAL's from 0.0004 to
   0.0002. Across all cells the change is RMS 2.3e-4, largest 0.0048. No cell is above -20 mV after warm-up.
4. **Reach, measured** (30 s windows, readout at 2b row 3, reference integration). ASHL 0.385, AWAL 0.345,
   AVAL 0.0098; on merge 1 the same values gave 0.53, 0.75 and 0.043. The training median is 0.43, so the
   readout's upper bounds no longer reach the median autoresponse. The first risk in section 8 (values pinned at a bound)
   is now more likely. The plan does not change: the values stay inside their ranges, and pinned values are
   reported.
5. **Integration re-checked on worm-v1** (measured 01:21-01:45, against h_dt 0.5 with mechanisms every 1 ms):

   | Run | Template RMS (largest) | Large RMS (largest) | Strong + large RMS (largest) | Wall per window (s) |
   |---|---|---|---|---|
   | reference | | | | 332-334 |
   | h_dt 2, mech 10 | | 1.1-1.2e-4 (0.0018) | | 78 |
   | **h_dt 5, mech 10** | 0-0 (3e-5) | 0.6-1.5e-4 (0.0014) | 0-1.9e-4 (0.0032) | 46-47 |

   h_dt 5 passes the bar (0.003) by 16x at all three value sets and stays the fit's step.
6. **The wrong model on worm-v1** rewires exactly as on merge 1: 5,868 of 6,301 chemical sites and 1,388 of
   1,390 non-rectifying gap junctions moved, 138 rectifying junctions kept; the run is finite. The 208 gap junctions
   that modules add after the wiring are not shuffled: the wrong model shuffles Cook's neuronal wiring only.


## After the freeze (a record, not an amendment; nothing about the fit changes)

Main moved after `worm-v1`, and this branch merged it at 02:01 (ec5a8a9) for the Director's merges. The fits keep
running d174f16's tree in `repo_v1`. The merged branch differs from that tree in ways that would change FIT1's model:
- the catalog merge (7b49648) changed 10 ledger rows' template values and wrote 508 module values into the
  ledger as new rows, some with new values (counted 02:05). Examples outside the 23: GLR-1 desensitisation
  (rec_glr_tau_des_ms 20 to 4 ms) and the neuron pump volume (pumps module value 100, now a ledger row of 72 um3);
- the template's GCaMP6s half-decay is now a derived 619 ms, against a guessed 550 ms at the freeze (same range);
- rec_acr16_gamma_pS's range is now [5, 90] pS, against [20, 90] at the freeze;
- wsyn.mod no longer gives NaN at a release tau of 0 (5b7e141). That value is not reachable in worm-v1.
Held-out scoring (section 7) therefore runs from `repo_v1`. `fit1_eval.py` on this branch now refuses to run
unless its tree's COMMIT file matches the fits' config (`--any-tree` for plumbing tests only). A later fit
(FIT2) would take the new values and ranges, with its own pre-registration.
