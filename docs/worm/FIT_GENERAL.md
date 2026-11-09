# FIT_GENERAL: the whole-worm fit by ensemble Kalman inversion (pre-registration, draft)

weki, 8 Nov 2026, written from 21:30 CST (date). This is phase 5's pre-registration, drafted early for review. **No fit
runs from this file** until the gate (`docs/worm/GATE.md`) is signed and Ben says go. Before the first scored run the
file is frozen by a commit; any later change makes a new, separately named fit (as FIT1). Code: `src/wormemu/fit/eki.py`
(method, tested), `src/wormemu/fit/vitals.py` (battery), `src/wormemu/params.py` (the vector), `scripts/worm/ranges/
joint.py` (constraints). It follows the ten refinements in `~/director/logs/day-2026-11-08/DEBUG_PASS_PLAN.md`.

Decisions marked **Ben to confirm** carry the default the fit uses if Ben does not change them.

## 1. The vector, its transforms and its priors (refinement 1)

`params.Theta()` on f8e7699 (measured 21:20): **368 active numbers**, 325 gap and 43 rule; every one labelled guessed.
Grains: global 126, class 189, gene 20, cell 19, channel 11, pairing 3. Mechanisms: 55.

| Part | Count | Treatment |
|---|---|---|
| log-logit (lo > 0) | 303 | in the EKI vector: z = logit of the log position inside [bio_min, bio_max] |
| logit (lo <= 0) | 50 | in the EKI vector: z = logit of the linear position |
| bernoulli | 15 | outside EKI (section 6): `syn_inhibitory[cell]` for AVF, AVH, AVK, BDU, CAN, PVW, RMG (L and R) and PVT |
| of which scene_* | 6 (4 log, 2 logit) | **not the worm**: the diacetyl and NaCl plume shapes of an experiment's world. Fixed per experiment at its protocol's value, out of the vector. **Ben to confirm** (default: fixed) |
| of which obs_noise_dff | 1 (log) | **not the worm**: the microscope's per-frame imaging noise. Fixed per experiment at the dataset's own measured noise (Atanas 2023: 0.0417 F / mean F, derived, `scripts/worm/fit/atanas_noise.py`; `vitals.BATTERY_VALUES`), out of the vector. Added 8 Nov 23:25; same Ben-to-confirm item as scene_* |

So the EKI vector has **347** continuous numbers on f8e7699 (derived: 368 - 15 - 6) and **347** on main dfe027d
(derived: 369 - 15 - 6 - 1; main added wbody2's `rule_body_modulus_scale`, and obs_noise_dff leaves). On weki's
1198812 (main cea4d49) Theta has 370 (wneuro's `unc2_gs_gain` added) and the vector **348** (measured 9 Nov 00:08,
`fit/vector.py`, which builds the mask from these rules and counts it, so the number tracks main). After merging main
f7b75e7 (9 Nov 01:36) Theta has 362 and the vector **347** (measured): wbrain2 made the 7 settings above
`params.SETTINGS` (Theta leaves them out; the vector keeps a guard), and the ledger rebuild made wneuro's SER-1 EC50
(`ma_ec50_serotonin_ser-1_nM`, 1340 nM) measured, so it left the vector. After merging main 58246cf (9 Nov 02:45)
Theta has 365 and the vector **350** (measured): wneuro's near-field numbers `ecs_alpha`, `ecs_tortuosity` and
`hsn_vm2_site_receptor_um` (guessed). They act only under the `amine_synaptic` toggle, which is off, so in today's
worm no observation reads them. They stay in the vector: rho_corr (section 5) cuts their chance correlations, and a
number no observation sees keeps its prior draws (tested there). If the toggle stays off at the gate, they can leave
the vector the way maturation's numbers did; that is the gate's call, not a rule here.

**Why the imaging noise leaves the vector (8 Nov 23:25, measured unless marked).** On the f8e7699 template the
GCaMP traces are imaging noise: per-neuron SD 0.029, noise 0.029, signal 0.003 F / mean F (median over neurons;
Atanas's open animals: SD 0.293, noise 0.037-0.042). White noise of SD s alone gives a per-neuron P95 - P5 of 3.29 s
(derived), which is 0.66 at obs_noise_dff's upper bound 0.2, inside the gcamp_range bar (0.567-0.983). The signal's
response to every brain number is near zero while the noise's is 3.29 per unit, so the update would move the noise
first: it passes a brain-activity sign with no brain activity. Prior draw 1 (admissible) has obs_noise_dff 0.176 and
a noise-only range of 0.579 (derived). The rule, for every observation: **an instrument number that the statistic
reads directly is set per experiment from that dataset, never fitted** (the scene_* numbers are the world's version
of the same rule). The other obs_* numbers stay in: obs_ca_rest_nM cancels out of the Atanas readout (F / mean F,
`vitals.f_over_fmean`; Randi's dF/F0 is FIT1's statistic and should take F0 from each trace's own pre-stimulus
baseline the same way, request to wfit), and the opto and NeuroPAL numbers act only in the Randi and NeuroPAL
experiments, through the stimulated neuron's response or the identity draw, not through a statistic's noise floor. Every member lives inside the hard bounds by
construction: `Theta.from_z` maps any real z inside the box.

Priors (ledger `parameters.prior_dist`, measured): uniform 134, log-uniform 213, bernoulli 15, 6 without a ledger row
(the scene numbers). `prior_a` and `prior_b` are empty for every row, so each prior is uniform or log-uniform on
[bio_min, bio_max]. Members are drawn in natural units from that prior and mapped to z (86 uniform priors sit on a
log-logit transform, so their z prior is not the logistic; the draw handles it). No member is started at the template.

Maturation's numbers (`fit/maturation.py`, `mat_*`) are not in the vector: maturation is off (section 4).

## 2. The joint constraints (refinement 2)

`data/worm/model/constraints.yaml` (measured): **177**, of which 176 hard and 1 prior. Kinds: sum_le 123, gate_window 20,
less 15, vhalf_order 9, between 8, passive_rin 1, pool_volume 1. Checked on a member's natural values by
`joint.check(values, led)`.

- Prior draw: reject and redraw until admissible, up to 1000 draws per member. The acceptance rate is reported; under
  1 % means the box and the constraints disagree, and the fit stops and reports. Code: `vector.Vector.prior`, which
  checks each draw as the member it builds (the template worm with the vector's numbers set). Measured 9 Nov 00:08 on
  1198812: acceptance 68-72 % over the 3 seeds' 128-member ensembles (41 % for full `sample_worm` draws, whose numbers
  outside the vector are drawn too), 30 s per ensemble. Median per-coordinate z SD 1.78-1.80, about the logistic's 1.81
  (derived).
- After each update: a member that breaks a hard constraint is redrawn from N(mean, cov) of the updated admissible
  members (up to 100 draws), else it keeps its last admissible z (`eki.EKI.update(admissible=...)`). Reject and redraw,
  not projection: the admissible set is not convex, so a nearest point is not defined cheaply.
- The prior-strength constraint (`passive_rin_neurons`, input resistance 0.2-5 GOhm) is reported per member and does not
  reject.

A member that breaks a hard constraint is never run, so it never enters an update.

## 3. Physicality and the vital signs (refinement 3)

Every member runs the battery (`VITAL_SIGNS.md`: one `wormemu.simulate` per condition, the whole worm, closed loop).

- **Rejection** (`vitals.physical`, per run): every voltage, Ca and module concentration finite; every soma voltage
  inside [E_lo - 1, E_hi + 1] mV; every concentration >= 0; no soma voltage alternating at every exchange step for 25
  steps (added 9 Nov 01:04, validated: VITAL_SIGNS.md). The last one matters for the prior. Three modules (egg_laying,
  intestine, noise) hold an explicit conductance over the 4 ms step (corrected 9 Nov 01:23 from "ten"), so some
  members inside the box go numerically unstable. Prior draw seed 1 (f8e7699) did: egg_lgc55_g_nS 4.15, inside its
  0.1-5 range, sends HSN into a -137 / +20 mV alternation after the first egg (measured). On this branch's prior,
  4.5-5.8 % of draws cross HSN's threshold (1.22-1.31 nS, measured on the template) at the first egg and up to 38 %
  once tyramine saturates LGC-55 (derived, 400 draws, `scripts/worm/fit/lgc55_prior_fraction.py`). Such members are
  rejected, not scored, and the rejection rate under the prior is measured by the prior predictive before any fit. A boundary that is numerical, not biological, is a fault for the module's
  owner to fix (night file request, 9 Nov 01:04); the fit must not learn to avoid it. Plus activity, added before
  the fit and reported only until then:
  - saturated: the run's mean fraction of neurons above -20 mV over 0.5 (guessed; the 7 Nov triage saw 197 of 302 in
    the saturated state);
  - silent: fewer than 10 % of neurons with a voltage range (P95 - P5 after the settle) above 2 mV (guessed).
- A rejected member is left out of that iteration's covariances and redrawn after the update (as section 2). If more
  than half the members are rejected 3 iterations in a row, the fit stops: it is pushing out of the possible worm.
- **The signs as observations: Ben to confirm** (Director default: yes, read only from the entire worm). Each scored
  sign enters with sigma from its published spread: SD for mean +- 2 SD bands, (P95 - P5) / 3.29 for the Atanas
  percentile bands, half the half-width for the inferred bands (egg timing, off-food pumping; guessed). Unscored signs (AIY and
  AFD rest, no spread) stay out. The simulation's own noise variance is added (section 7).
  - Code: `vitals.observations` and `vitals.obs_target` (toy-tested). y is the published mean, else the band's
    midpoint (derived; the off-food pumping band has no mean).
  - **Signs the worm does not produce**: the defecation period with fewer than 2 expulsions, and the egg statistics
    in runs under 1800 bio-s. Each gives g = NaN, and the driver counts a NaN member as failed. If every member lacks
    the sign, every member fails and the run stops at once. **Default: such a sign is left out of the fit's vector**
    (it stays in the battery and the gate) until the worm produces it. A censored readout (for example, the period
    read as the run length when no interval closes) enters only by an amendment written before any run.
    **Ben to confirm.**
  - On the f8e7699 template (stored battery, measured 9 Nov 00:01), the observations' z, (g - y) / sigma, are:
    - food: pumping -18.3, PC3 -8.3, GCaMP range -4.9, AWA rest +3.6, BWM spikes +3.0, BWM rest -1.0;
    - off food: AWA rest +3.4, BWM spikes +2.9, pumping -2.1, BWM rest -1.1.

    The mean misfit Phi per observation is 23.8. So the controller's first step would be at least about 1 / (2 x 23.8) = 0.02
    (derived, if the ensemble starts near the template). Pumping carries 71 % of the summed z^2 (339 of 475, derived),
    and the silent pharynx is a mechanism fault, so the fit must not run before it is fixed (the gate).

## 4. Maturation before scoring (refinement 4): off

The plan runs maturation before scoring each member once it reproduces the recorded cells. It does not: the single-cell
test (pre-registered 21:12, `scripts/worm/fit/maturation_ephys.py`, measured 21:27) helped in 0 of 3 classes (AIY
10.60 -> 23.92 mV, AFD 49.89 -> 49.83, AWA unchanged because its Liu 2018 membrane is out of the rule's reach). So each
member is scored as built. The retry with wbrain2's bulk Ca pool as the sensor (pre-registered 23:33, measured 9 Nov
00:23 on 1198812) is falsified the same way, 0 of 3, with the same multipliers to 3 digits. At a steady resting set
point the rule stops where the sensed Ca equals the clamped-at-rest Ca, so any sensor that is a steady monotone function
of the soma Ca current gives the same answer (derived). wneuro's code trace (599ce4b, session 3; a reading of the
code, not a run) gives the premise directly: the bulk pool (`nmodl/cabulk.mod`) reads the soma's total ica and writes
neither cai nor ica, so it changes neither the soma Ca nor the Ca current, and a further retry on it cannot differ.
Closed there (Director, 9 Nov 01:45); no more retries on this sensor. Maturation enters only through a new pre-registered
single-cell test that passes and a gate re-sign. If it does, its rule numbers join the vector as rule parameters, and its per-class targets need a shared rule
(today they exist only for the recorded classes).

## 5. Ensembles, inflation and localisation (refinement 5)

- **Size**: J = 128 members per ensemble (inside the plan's 100-200; guessed). **Seeds**: 3 independent ensembles per
  alternative, prior draws from `numpy.random.default_rng(20261109 + k)`, k = 0, 1, 2.
- **Update** (`eki.py`, as EnsembleKalmanProcesses.jl, opened): stochastic EKI with perturbed observations, step from
  the data-misfit controller (Iglesias & Yang 2021, arXiv 2006.14980). The steps sum to 1, so in the linear-Gaussian
  limit the ensemble goes from the prior to the posterior (tested against the closed form).
- **Inflation**: 1.0 (off). Chosen by the twin rule (smallest of 1.0, 1.02, 1.05, 1.1 with coverage >= 0.90 over 20
  hidden draws): on the excretory-canal twin, protocol B, 1.0 gives coverage 0.925 (measured 21:27). Re-run on a
  second, larger twin (`scripts/worm/fit/twin_neuron.py`, 8 Nov 22:34-23:04, pre-registered, measured): the published
  Nicoletti AIY point neuron with its 7 densities hidden, FIT2's clamp features, J = 100, correlation localisation on.
  Coverage 0.979 at 1.0 (0.943 without localisation), so **1.0 is fixed**. That twin also shows what one cell's clamp
  can fix: leak, nca and kqt1 in at least 19 of 20 draws; shl1, egl19 and slo1iso stay wide (95 % ranges a factor
  3.4-8 of a box of 9).
- **Localisation**: rho = rho_graph x rho_corr on C_zg.
  - rho_graph (`eki.graph_rho`): structural zeros. A parameter's module (its mechanism's module in `mech.modules()`) can
    move an observation only if a directed path in `iograph.edges(iograph.record())` leads to a module the observation is
    read from, with the membrane as one hub node (writers of g_scale, I_pA or act_add; every module reads it). Because
    the membrane joins nearly everything, this is expected to cut few pairs (inferred). Measured on the real graph
    (`scripts/worm/fit/cost_graph.py`, f8e7699, 8 Nov; the 347 numbers x 13 signs): the raw 20 ms trace gives 54.8 % zero
    pairs, but those zeros are false (build-time modules such as cells_passive, receptors and structure_rules write
    nothing at run time; reads of ctx.v and ctx.ca are not traced; touch and stretch drive nothing at rest). Closed so
    that no zero is false (every module with numbers writes the membrane, the membrane drives the body, the body feeds
    every ctx.obs reader), **0.78 % of pairs are zero** (35 of 4,511: the 2 GCaMP readout numbers on the 11 signs
    that do not read GCaMP, and the NeuroPAL number on all 13). In the closed-loop worm the graph localises almost
    nothing, so rho_graph is kept only for the readout split.
  - rho_corr (`eki.corr_rho`): keep a pair only where |corr| > 3 / sqrt(J), 0.265 at J = 128 (derived), recomputed each
    iteration. With the graph this dense (measured above), it does all of the work. It is a statistical cut, not a
    structural one, so the twin test of refinement 5 must run with it on. Run on the excretory-canal twin (protocol
    B, 8 Nov 22:28, pre-registered, measured): passes, 20 / 20 recovered and coverage 0.925 at inflation 1.0, the
    cut keeping 51-59 % of pairs at the start; widths grow a little (the gain's 95 % range a factor 1.19, against
    1.15 without). With the cut on, inflation 1.1 fails (8 / 20), so the two are chosen together on the twin.
  - Tested: a parameter no observation can see keeps its prior draws exactly; without localisation it collapses.
- **Seed agreement** (part of convergence): for every data-informed coordinate (posterior SD below half the prior SD
  in z, the prior SD being the prior ensemble's own per-coordinate SD, about 1.8 for these priors, not 1; section 2's
  measurement), the 3 ensemble means agree within 1 pooled SD, for at least 90 % of those coordinates (guessed). Otherwise the
  fit reports non-identifiability, not a converged worm.

## 6. Discrete alternatives (refinement 6)

One ensemble set (3 seeds) per alternative; never averaged.

- The 15 synapse signs as 8 choices (left and right share a sign, inferred from bilateral symmetry; PVT alone).
- The class C source toggles at the gate: today `DEBUG_TRIAGE.md` lines 1 (channel forms), 2 (Ca pool volume) and 10
  (bending stiffness); `awa_kir` (smooth_min vs as_printed); any added in phase 2.
- Design: the base set at every default, then one alternative at a time (others at default), each started from its
  own prior draws. Joint combinations only for the choices that win one at a time.
- **Comparison: Ben to confirm.** The plan compares alternatives on held-out data, but held-out data are spent once.
  Default: alternatives are compared on a validation split carved from the open data (20 % of each dataset's open units,
  `default_rng(20261109)`, drawn when this file is frozen), and the locked set (`HELDOUT.md`) scores only the final
  winner, once.

## 7. Noise seeds (refinement 7)

The stochastic modules (quantal release, channel noise, `mech.noise`) run with one seed per experiment per iteration,
`hash(experiment id, iteration)`, shared by every member of the iteration (common random numbers: members differ by
their values, not their noise). The simulation-noise variance per observation is measured on the template worm at 8
seeds per experiment before the fit and added to Gamma; re-measured on the final ensemble mean and reported.

Built (9 Nov, from wbrain2's `Experiment.noise_seed`, main 1d1206b, which seeds quantal and channel noise,
brain_layers and the observation noise apart from the worm seed). `vector.noise_seed(exp_id, k)` is a stable hash
(sha256; Python's `hash()` of a string changes per process) into [1, 2^31 - 1], so it never meets the template's 0;
`battery_forward` passes `--noise-seed=noise_seed("battery_" + cond, k)` to each `vitals run`, and k None keeps the
template's noise as before. Checked on the Mac (5.5 bio-s food, the template worm; measured): seed 7 against the
default moves V in all 397 cells (max 65 mV), and seed 7 twice is bit-identical (V, Ca and GCaMP difference 0;
readouts equal). Tests: `test_noise_seed_per_experiment_and_iteration`, `test_forward_passes_the_iterations_noise_seed`,
`test_experiment_carries_the_noise_seed`. The 8-seed template measurement is not run yet: 8 seeds x 2 conditions x
200 bio-s is 16 runs, about 16 CPU-h at the night's 61 CPU-min per run, about 5.5 h on 3 processes (derived).

## 8. Data, statistics and weights (refinement 8)

Everything open except the locked set (`HELDOUT.md`, `data/worm/heldout/lock.json`). Weights are 1 / sigma^2 with
sigma from measurement noise; no other weights.

| Dataset (open part) | Statistic | sigma | Status |
|---|---|---|---|
| Randi 2023 wild type (137 of 171 stimulated neurons, 18,835 terms) | dF/F0 over 30 s after the pulse, per responder-stimulated pair, through the GCaMP model | sigma^2 = 0.068^2 / n_trials + 0.030^2 (FIT1's noise model, derived from training data) | statistic as FIT1 section 4 |
| Single-cell ephys: AIY, AFD, AWA (FIT2's training sweeps) | FIT2's 4 features x 6 sweeps | the spread between repeat sweeps where a recording has them; else the published population SD; else the class is reported, not weighted | AWA's protocol confirmation still open (FIT2 section 2) |
| Atanas 2023 main (60 of 80 animals) | top-3-PC variance fraction on 135-neuron subsets; GCaMP range; then SCOREBOARD 17's correlation structure, state transitions and encoding, each defined in an amendment before any scoring | across-animal SD (measured: 0.057 and 0.161) | first two built (`atanas_pc3.py`) |
| Dag 2023 (11 of 15 animals) | as Atanas | across-animal SD | not yet built |
| OWMD (Javer 2018): N2 | locomotion features (speed, reversal rate, curvature) | across-worm SD | the 11 open mutant strains stay out: **Ben to confirm** (SCOREBOARD 15: mutants never tune the model; HELDOUT left them open) |
| Yemini 2013: N2 rows | a pre-listed subset of locomotion features | across-worm SD | mutant rows out, as OWMD |
| Vital-signs battery | the scored signs (section 3) | published spread | **Ben to confirm** |
| Body: bending stiffness | whole-worm bending modulus | Backholm et al. 2013, 110 +- 30 kPa | needs the approved stiffness rule (DEBUG_TRIAGE line 10) |
| NeuroPAL 2021, perturbation corpus, wormbase phenotypes | none | | observation model and named tests only, never fit |
| cook2019, witvliet2021, cengen, peptide connectome, morphologies, brittin2021, misc | none | | the structure the model is built from |

Locked, never opened by the fit: Randi's 34 wild-type stimulated neurons and every unc-31 term; RIM (all ephys);
20 Atanas animals; all of Pradhan 2025; 4 Dag animals; 6 OWMD strains; 76 Yemini strains; 6 NeuroPAL sessions; 7
perturbation-corpus items; Kato 2015.

**Stochastic batches**: each iteration runs the battery (it carries physicality) plus a batch drawn by
`default_rng(seed + iteration)`: 32 of Randi's 137 stimulated neurons, all 3 ephys classes, and one 195 s window per
behavioural statistic. M in the step controller is the batch's observation count.

## 9. Stopping, the single held-out scoring, and calibrate-emulate-sample (refinement 9)

- **Stop** at the first of: (a) the controller's time reaches 1; (b) 30 iterations (guessed; a cost cap); (c) a plateau,
  where the ensemble-mean misfit per observation improved by under 1 % over the last 5 iterations (after at least 10);
  (d) the rejection stop (section 3). Then the seed-agreement check (section 5). Reaching (b) or (c) with time under 1
  means the model cannot reach the data at their noise. That is reported as the result (model error), and no
  model-error term is added to make it fit.
- **Held-out scoring, once**: a script written and committed before it runs (as FIT1's `fit1_eval.py`) scores the final
  ensemble (mean member and every member) on each locked dataset's statistic. Comparators: the prior ensemble and the
  template worm, plus the must-fail controls of `SCOREBOARD.md` section 16 (a shuffled connectome fit the same way).
  **Falsifier**: the fitted ensemble does not beat the template on the held-out statistics. Then the fit learned nothing
  that generalises, whatever its training misfit.
- **Afterwards, calibrate-emulate-sample** (Cleary, Garbuno-Inigo, Lan, Schneider & Stuart, arXiv 2001.03689):
  - calibrate: every (z, G(z)) pair from the EKI runs;
  - emulate: an emulator of G on decorrelated outputs;
  - sample: MCMC on the emulated posterior.
  The emulator is a search tool only: every point reported from the posterior region is re-run on the real model
  first. The output is the precision-needed column (each value's posterior width against its prior width).
- **Code** (`fit/ces.py`, 857784b; ported from CalibrateEmulateSample.jl @ bffeb42, its GP path with the Sinusoid
  example's settings; toy-tested only). On a nonlinear 2-value toy, EKI (40 members, 4 iterations, 200 pairs) then CES
  gave a posterior within 0.05 SD of MCMC on the true map, with SDs 0.92-0.93 of the true ones; EKI's own final
  ensemble had SDs 0.96 and 0.79 of the true ones (measured, `tests/test_worm_fit_ces.py`).
- **Worm-scale cost, before any use** (one Mac core, 347 inputs, measured 8 Nov 23:45): one marginal-likelihood
  evaluation with gradient takes 0.67 s at 1000 pairs and 2.9 s at 2000 pairs; one prediction 1.1 and 6.9 ms. At 3000
  pairs that is about 7 s per evaluation (derived, n^2 scaling) and, at 100-300 optimiser steps (guessed), 12-35 min per
  emulated output. The ported path fits one GP per output, and Randi alone has 18,835 terms. So CES on the worm needs
  an output reduction first. CES.jl has three: variance-truncated decorrelation, canonical correlation and a
  likelihood-informed subspace (`Utilities/`). None is ported, and a 347-dimension random walk mixes slowly. Which to
  port is decided after the EKI, from how many directions its ensemble shows the data inform.
- **Run loop** (`fit/driver.py`; toy-tested only, no worm forward is written). The loop keeps every step on disk,
  because backhouse reboots and the Mac sleeps:
  - the EKI state before each iteration, including the generator's state;
  - each member's result as its own file, written atomically.

  A resume re-runs only the members with no result. On the linear toy, a run killed during iteration 2 and resumed
  ends bit-identical to one that never stopped (measured, `tests/test_worm_fit_driver.py`). The loop applies stops
  (a) to (d) above. It also stops when fewer than 2 members run, since no covariance exists then, and when the data on
  disk differ from the data given. It hands every (z, G(z)) pair to the CES step.
  - The forward gets the iteration number, so it draws one noise seed per experiment per iteration (section 7). On a
    noisy toy, a 2-process pool ends identical to one process (measured).
  - The loop takes section 8's stochastic batch. The batch is fixed on disk before the iteration's first run, and the
    EKI update scores only the batch's observations. With batches, the CES pairs default to the observations that
    every batch holds.
  - `driver.seed_agreement` is section 5's 3-seed check, toy-tested.

## 10. Compute and cost (refinement 10)

backhouse only, never rented. Measured so far: the battery costs 11.7 s of wall per bio-s per condition on one core
(f8e7699's predecessor 103ece3, 200 bio-s food and nofood), so one member's core battery (2 x 200 bio-s) takes 78 min of
one core (derived).

| Design | Member-runs per iteration | Core-hours per iteration (derived) |
|---|---|---|
| one ensemble (J = 128) | 128 | 166 |
| base set (3 seeds) | 384 | 499 |
| base plus 13 one-at-a-time alternatives (8 signs, 5 toggles), 3 seeds each | 5,376 | 6,989 |

At 20 cores fully used (backhouse's i7-14700K; E-cores slower, and the share limits apply), the base set alone needs
about 25 h per iteration, and 30 iterations about a month (derived). **The full design does not fit the NEURON path at
the measured cost.** Options, to decide at the gate: a shorter battery per iteration (the batch draws from the signs
too), fewer members once localisation is measured, or the JAX port (refinement 10: only after the gate).

**Cost run (8 Nov 2026, backhouse, f8e7699, one thread per process; measured unless marked).**

- One member through the core battery: food 2,429 s + nofood 2,374 s = 4,803 s, 80 min of one process (12.1 and
  11.9 s per bio-s, run with one or two other jobs of mine beside it).
- Concurrency (`scripts/worm/fit/cost_concurrency.sh`, N copies of food 20 bio-s at once, nothing else of mine
  running, load 2.4-4.5 from other users). Wall of the simulate call per bio-s: N = 1: 10.98 s; N = 2: 11.76, 11.76 s;
  N = 3: 12.46, 12.16, 12.39 s (mean 12.34). Slowdown per process 7 % at 2, 12 % at 3. Process wall adds 0.6-0.8 s
  (startup). All six runs physical.
- 100 members (2 x 200 bio-s each), derived from those rates: 1 process 122 h; 2 processes 65 h; **3 processes (the
  share after 22:00) 46 h**. One base-set iteration (3 seeds x 128 = 384 members) at 3 processes: 175 h, about 7
  days, so 30 iterations is about 7 months.
- Beyond 3 processes nothing was measured (the egg probe holds 16 cores from 22:00). WSL sees 28 logical CPUs
  (8 P-cores with hyper-threading plus 12 E-cores). If the per-process slowdown stayed at 12 % at 20 processes (a
  guess; E-cores and shared cache make it worse), 100 members would take about 7 h and a base-set iteration about
  26 h (guessed extrapolation).
- Localisation does not cut the cost: the graph leaves 99.2 % of parameter-sign pairs connected (section 5), so
  fewer members cannot be justified by structure.

**Where the time goes (9 Nov 01:47-01:53, Mac, ad37628 plus the readouts guard, `scripts/worm/fit/cost_breakdown.py`,
food, measured unless marked).** Profiled 4 bio-s run: the exchange loop 52.7 s, of which NEURON's own integration
(the `fadvance` calls inside `Brain.step`) 42.4 s, 10.6 s per bio-s; waiting on the body's pipe 0.9 s (the FEM body
steps in its own process while the brain steps, so it is hidden); construction 15.4 s, once per run. The same run
unprofiled, 6 bio-s: 87.5 s, so the loop is about 12.0 s per bio-s and NEURON about 88 % of it, the Python modules
about 1.4 s per bio-s (derived by difference). The brain is 48,356 NEURON segments in 2,253 sections, active
channels on the 397 somas only (the rest `pas`), at dt 0.5 ms: 5.3 ms per step, 0.11 us per segment-step (derived).
The segment count is BAAIWorm's 2 um rule (`brain._segments`), which also indexes its synapse table.

**The machine under load (backhouse, f8e7699 prior predictive, 3 at once, measured unless marked).** Draws 1-3 (22:23
to 00:40, beside the egg probe's 16 workers) ran at 38.6-41.1 wall s per bio-s; draws 4-6 (00:40-02:19, load 7-12 of
28) at 27.2-29.6, and each used about 61 CPU-min for its 200 bio-s (`ps` time sampled each minute to the end), 18
CPU-s per bio-s, 1.5x the cost run's rate even in CPU time. The draw is not the cause: seed 4 costs the template's
time over its first 4 bio-s on the Mac (68.7 vs 70.9 s profiled; NEURON 41.2 vs 42.4 s). So slower or shared cores
under load cost 1.5x in CPU and 2.2-3.3x in wall (inferred), and option B's 12 % slowdown is optimistic by about that
factor. At the night's measured rate, option A is 400-580 h per base-set iteration, not 175 (derived).

Draws 7, 9, 10 (02:19-03:27, load 8-11 of 28, no other heavy job) ran at 19.2-19.9 wall s per bio-s and about 60
CPU-min each (measured): wall fell with the load, but CPU time stayed at about 18 CPU-s per bio-s, 1.5x the cost
run's. So the 1.5x in CPU is not contention. It is not the 17:00-22:00 throttle either: the WSL VM's affinity is all
28 logical processors at 03:3x (0xFFFFFFF, measured). Which cores the host gives the vCPUs (8 P-cores, 12 E-cores)
or their clock with several busy is the likely cause (guessed, not measured). For planning, a quiet night gives about
20 wall s per bio-s per process, so option A is about 280 h per base-set iteration (derived: 384 x 400 bio-s x 20 s
/ 3 processes / 3600), and the 12.34 of the cost run is a best case.

**The options, per iteration (each member 2 x 200 bio-s unless marked; derived from the rates above).**

| Option | One ensemble (J = 128) | Base set (384) | 30 base-set iterations | What it costs |
|---|---|---|---|---|
| A. NEURON, the share after 22:00 (3 processes, 12.34 s per bio-s, measured) | 58 h | 175 h | about 7 months | nothing in the design |
| B. NEURON on all of backhouse (20 processes, the 12 % slowdown at 3 assumed to hold: guessed, optimistic) | 8.8 h | 26 h | about 33 days | all of backhouse for a month, through the 17:00-22:00 cap; E-cores are slower, and each member's body process takes about 12 % of another core (derived: 1.5 / 12) |
| C. Reduced battery: food 200 s only, 3 processes | 29 h | 88 h | about 3.6 months | drops off-food pumping, 1 of the 10 signs with a bar (its band is the weakest one, limitation 6); every other sign needs the 200 s food run (the PC3 and GCaMP bands are built on 195 s windows, the defecation period needs 2 intervals at about 45 s) |
| C on 20 processes | 4.4 h | 13 h | about 16 days | as B and C |
| D. JAX brain on the GPU, modules and body on CPU (guessed range from measured anchors, below) | GPU 5-46 h, CPU side 14 h at 3 processes | GPU 16-137 h, CPU side 41 h at 3 processes or 6 h at 20 | GPU 20-171 days | the port of every brain mechanism and its CPU-path check before the gate: weeks (guessed) |

How D is estimated (no Jaxley run of this brain exists; a cheap micro-benchmark does not, because the 48,356-segment
morphology would have to be ported first). Measured anchors (PLAN.md section c.5, backhouse, 4-5 Nov): the Jaxley
stand-in, 446 cells x 4 compartments with 13 channels each, cost 0.13 us per compartment-step on one CPU core (0.39 with
the implicit gap solve), and 6.4 ns per compartment-step on the shared GPU at batch 128. Guessed factors: implicit gaps
x 2-2.6 (measured on CPU, assumed on GPU), passive compartments x 0.3-1, branched trees x 1-2. Result: 3.8-33 ns per
compartment-step, so 0.4-3.2 s per member per bio-s at 48,356 compartments and 2,000 steps per bio-s (derived). The CPU
side is the Python modules (1.4 s per bio-s, above) and the body (1.4-1.7 s per bio-s on one thread while swimming,
BODY_TESTS.md, measured 5 Nov), 2.9 core-s per member per bio-s.

**Verdict (derived; guesses as labelled).** Per core, NEURON is already about as fast as Jaxley here (0.11 against
0.13-0.39 us per compartment-step), so the GPU pays only by batching, and 48,356 compartments per member fill it after a
few members. One GPU does the brain of about 3 to 29 NEURON cores (10.6 s per bio-s / 0.4-3.2 s); at the middle of that
range (about 10) it adds about half of backhouse's CPUs. So the JAX port is worth about 1.5x on backhouse, not the 20-25x
the 4-compartment stand-in showed. The two cheap levers are design choices: the reduced battery (C, 2x) and B's machine
share (6.7x over A). A, B and C need no new code. A coarser cable would cut both paths, but that is the brain owner's
port (BAAIWorm's 2 um rule, which its synapse table is indexed by) and needs a convergence check; it is not costed
here. So the NEURON path supports the twin tests and pilots of tens of members at the current share; the full fit
needs B, B with C, or a smaller design. Ben's call; not decided here.

## Ben to confirm (defaults in brackets)

1. The vital signs enter the loss as observations, read only from the entire worm. [yes]
2. Discrete alternatives are compared on a validation split of the open data; the locked set scores only the winner,
   once. [yes]
3. The open mutant strains (OWMD 11, Yemini's open mutant rows) stay out of the loss, per SCOREBOARD 15. [yes]
4. The 6 scene_* numbers, and the imaging noise obs_noise_dff (at each dataset's measured noise), are fixed per
   experiment, not fitted. [yes]
5. A vital sign the worm does not produce yet (the defecation period with no closed interval; the egg statistics in
   runs under 1800 bio-s) is left out of the fit's vector until it is produced. It stays in the battery and the
   gate. A censored readout enters only by an amendment written before any run. [left out] (Added 9 Nov 00:01,
   section 3.)
