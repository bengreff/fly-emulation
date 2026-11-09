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

So the EKI vector has **347** continuous numbers (derived: 368 - 15 - 6). Every member lives inside the hard bounds by
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
  1 % means the box and the constraints disagree, and the fit stops and reports.
- After each update: a member that breaks a hard constraint is redrawn from N(mean, cov) of the updated admissible
  members (up to 100 draws), else it keeps its last admissible z (`eki.EKI.update(admissible=...)`). Reject and redraw,
  not projection: the admissible set is not convex, so a nearest point is not defined cheaply.
- The prior-strength constraint (`passive_rin_neurons`, input resistance 0.2-5 GOhm) is reported per member and does not
  reject.

A member that breaks a hard constraint is never run, so it never enters an update.

## 3. Physicality and the vital signs (refinement 3)

Every member runs the battery (`VITAL_SIGNS.md`: one `wormemu.simulate` per condition, the whole worm, closed loop).

- **Rejection** (`vitals.physical`, per run): every voltage, Ca and module concentration finite; every soma voltage
  inside [E_lo - 1, E_hi + 1] mV; every concentration >= 0. Plus activity, added before the fit and reported only
  until then:
  - saturated: the run's mean fraction of neurons above -20 mV over 0.5 (guessed; the 7 Nov triage saw 197 of 302 in
    the saturated state);
  - silent: fewer than 10 % of neurons with a voltage range (P95 - P5 after the settle) above 2 mV (guessed).
- A rejected member is left out of that iteration's covariances and redrawn after the update (as section 2). If more
  than half the members are rejected 3 iterations in a row, the fit stops: it is pushing out of the possible worm.
- **The signs as observations: Ben to confirm** (Director default: yes, read only from the entire worm). Each scored
  sign enters with sigma from its published spread: SD for mean +- 2 SD bands, (P95 - P5) / 3.29 for the Atanas
  percentile bands, half the half-width for the inferred bands (egg timing, off-food pumping; guessed). Unscored signs (AIY and
  AFD rest, no spread) stay out. The simulation's own noise variance is added (section 7).

## 4. Maturation before scoring (refinement 4): off

The plan runs maturation before scoring each member once it reproduces the recorded cells. It does not: the single-cell
test (pre-registered 21:12, `scripts/worm/fit/maturation_ephys.py`, measured 21:27) helped in 0 of 3 classes (AIY
10.60 -> 23.92 mV, AFD 49.89 -> 49.83, AWA unchanged because its Liu 2018 membrane is out of the rule's reach). So each
member is scored as built. Maturation enters only through a new pre-registered single-cell test that passes and a gate
re-sign. If it does, its rule numbers join the vector as rule parameters, and its per-class targets need a shared rule
(today they exist only for the recorded classes).

## 5. Ensembles, inflation and localisation (refinement 5)

- **Size**: J = 128 members per ensemble (inside the plan's 100-200; guessed). **Seeds**: 3 independent ensembles per
  alternative, prior draws from `numpy.random.default_rng(20261109 + k)`, k = 0, 1, 2.
- **Update** (`eki.py`, as EnsembleKalmanProcesses.jl, opened): stochastic EKI with perturbed observations, step from
  the data-misfit controller (Iglesias & Yang 2021, arXiv 2006.14980). The steps sum to 1, so in the linear-Gaussian
  limit the ensemble goes from the prior to the posterior (tested against the closed form).
- **Inflation**: 1.0 (off). Chosen by the twin rule (smallest of 1.0, 1.02, 1.05, 1.1 with coverage >= 0.90 over 20
  hidden draws): on the excretory-canal twin, protocol B, 1.0 gives coverage 0.925 (measured 21:27). The rule is re-run
  on a second, larger twin (a neural mechanism, more than 4 numbers) before the fit; whatever it picks is fixed then.
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
  in z), the 3 ensemble means agree within 1 pooled SD, for at least 90 % of those coordinates (guessed). Otherwise the
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

So the NEURON path supports the twin tests and small pilots (tens of members) at the current share, not the full fit.
The full fit needs one of: most of backhouse for weeks, a shorter battery per iteration, or the JAX port after the
gate (refinement 10). Ben's call; not decided here.

## Ben to confirm (defaults in brackets)

1. The vital signs enter the loss as observations, read only from the entire worm. [yes]
2. Discrete alternatives are compared on a validation split of the open data; the locked set scores only the winner,
   once. [yes]
3. The open mutant strains (OWMD 11, Yemini's open mutant rows) stay out of the loss, per SCOREBOARD 15. [yes]
4. The 6 scene_* numbers are fixed per experiment, not fitted. [yes]
