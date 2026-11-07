# FIT2: the expression-to-excitability map (pre-registration)

Worker wexcite, night of 6-7 Nov 2026. Written 7 Nov 01:46-01:51 CST, before any scored run (committed 01404ed). TO_A_REAL_WORM item 2;
the structure follows `docs/worm/research/GENES_TO_PHYSIOLOGY.md` section 5 (gene family above selector battery above
class; Bernaerts et al. 2025 found the map accurate at family level and weaker at cell-type level; leave whole
classes out; CeNGEN is an L4 prior).

**What it replaces.** Today `expression_map=on` takes BAAIWorm's per-cell fitted densities and masks them with
CeNGEN presence without refitting. In isolation, 61 of 302 cells then go above every reversal under +10 to +40 pA
(single-cell sanity, `docs/worm/night/2026-11-07_wexcite.md`). FIT2 instead fits one map from expression to density,
shared by all 302 neurons, and tests it on a whole class it never saw.

## 1. The map (form `expression_map=fit2`, neutral: not the default until adopted)

For every neuron class c and channel k (BAAIWorm's 16 somatic densities plus Nicoletti 2024's 5 added channels):

    g_k,c = 0                                                              if TPM_k,c = 0 (CeNGEN threshold 2)
    g_k,c = clip( m_k * 10^a_f(k) * ((TPM_k,c + C) / (TPMref_k + C))^b ,  lo_k, hi_k )   otherwise

- **TPM_k,c**: CeNGEN (Taylor et al. 2021, threshold 2) for the channel's gene. A channel with several genes takes
  the max, as `build_ledger.CHANNELS`: irk (irk-1/2/3), nca (nca-1/2), kcnl (kcnl-1..4). The slo-1 and slo-2 variants
  read slo-1 and slo-2.
- **TPMref_k** (derived): the median TPM over the neuron classes that detect the gene.
- **C = 10 TPM** (guessed): a pseudo-count, five times the detection threshold, so a barely detected gene does not
  get a density near zero from the log.
- **m_k** (derived): the median of the published nonzero densities of channel k. For BAAIWorm's channels these are
  the 302 per-cell fits in the ledger (`dens_<k>`). For the Nicoletti channels they are the templates in
  `mech/channels._density_specs` (median of the fitted cells, or the stated guess for exp2). So a_f = 0 means "the
  published median at typical expression".
- **[lo_k, hi_k]** (derived): the published nonzero range of channel k (BAAIWorm's per-cell min and max; for the
  Nicoletti channels, the module's own bounds). No map value leaves a published range.
- **Families, one shared a_f each (17).**
  - shk1 (Kv1); egl36 (Kv3); shl1 (Kv4); kvs1 (Kv2);
  - kqt (kqt3 and kqt1, KCNQ); egl2 (EAG); unc103 (ERG); exp2;
  - irk (Kir);
  - slo1 (slo1_egl19, slo1_unc2, slo1iso: BK);
  - slo2 (slo2_egl19, slo2_unc2, slo2iso);
  - kcnl (SK); egl19 (Cav1); unc2 (Cav2); cca1 (Cav3); nca (NALCN);
  - leak (below).
  - Bounds on a_f: log10 of the family's pooled published range relative to m_k, [log10 min(g/m), log10 max(g/m)],
    capped at [-2, +2].
- **b**: one slope shared by every family, bounds [0, 1.5]. b = 0 is the nested presence-only form.
- **Leak** (every section): gpas_part,c = M_part * 10^a_leak * ((TWK_c + C) / (TWKref + C))^b, with no presence cut.
  - TWK_c (derived): the summed TPM of the 38 two-pore K genes in the CeNGEN table (twk-*, sup-9, unc-58, egl-23).
  - M_part: the median of the ledger's `pas_soma_gpas` or `pas_neurite_gpas`.
  - Bounds on a_leak: [-1.5, +1.5].
  - e_leak: one value shared by every cell, bounds the ledger's `pas_soma_epas` [lo, hi].
- **Not fitted, the brain's values:** morphology, Ra and cm (per cell, literature-clipped), Ca pool, ion
  concentrations, temperature, every kinetic constant, and the Nicoletti channels' kinetics.
- **Class-level noise:** not fitted. Three training classes cannot estimate it. The brain's worm sampler will draw
  each class's family scales log-normally around the map, with sd 0.15 decades (guessed) and bounds +/- 0.3 decades.
  FIT2 fits the mean map (noise 0).
- **Cells without a CeNGEN class:** keep BAAIWorm's presence pattern (density > 0) at m_k * 10^a_f.
- **AWA:** the fit and the score use `awa_membrane=baaiworm` so the map sets AWA (the brain's default AWA is Liu 2018's
  own model).
- **Parameters: 19** (17 family scales, b, e_leak), all bounded, all biological quantities, shared across classes.
  None is per class, per cell or per synapse.

## 2. Recordings, protocol and split

| Class | Recording | Sweeps FIT2 may use | Status before FIT2 |
|---|---|---|---|
| AIY | Naudin 2022 `Fig1A_AIY_CC.txt` (backhouse `~/worm-data/ephys/naudin2022_liu_aiy_rim_afd`), one cell | -15, -5, +5, +15, +25, +35 pA (indices 0, 2, ..., 10) | training only (register); odd sweeps spent, consistency only |
| RIM | Naudin 2022 `Fig1A_RIM_CC.txt` | indices 0, 2, ..., 10 only | W1 training sweeps (seen); odd sweeps and all voltage clamp sealed for W1 and never loaded by FIT2 |
| AFD | Naudin 2022 `Fig1B_AFD_CC-IV_11steps.txt` (0.1 ms, binned x4 to 0.4 ms as W1) | indices 0, 2, ..., 10 only | as RIM |
| AWA | Liu et al. 2018 Cell, `Liu et al Figure 1.zip` / `Fig 1A_AWA Current-Clamp Trace.txt` (backhouse `~/worm-data/liu2018_awa_ephys/`) | indices 0, 2, ..., 10 | unseen, except as noted in section 6 |

- **Protocol** (as W1 and W0, Naudin 2022): 11 sweeps of 11 s at 0.4 ms. Steps of -15 to +35 pA by 5 pA, from 1.0 to
  6.0 s.
  - AWA's file is the same figure panel with the same format (11 sweeps, 11 s, 0.4 ms). Its amplitudes and timing are
    therefore inferred to be the same. They are not stated in the file, so a confirmation is requested from the
    Director.
  - If they differ, the AWA protocol is corrected before AWA is used, with a dated note here.
- **Not used:**
  - Liu 2018's Fig 1A AIY and RIM files: byte-identical in size to Naudin's, so the same recordings.
  - Liu 2018's Fig 1A AFD file: possibly the same cell as Naudin's AFD, so not opened.
  - Liu 2018 Fig S1A voltage clamp: probably the W1-held voltage clamp, so not opened.
  - Fig 1B AWA (2 pA steps): amplitudes unknown.
  - No Nicoletti 2019 or 2024 experimental traces are available. The 2024 repository on backhouse
    (`~/worm-spike/ext/nicoletti2024`) holds model scripts only.
- **Voltage clamp:**
  - The only voltage clamp FIT2 could use is spent (AIY population I-V) or sealed for W1 (RIM, AFD).
  - The AIY I-V (steady state and peak, Naudin 2022) is therefore reported after the fit as a consistency check and
    is not in the objective.
  - The RIM and AFD voltage clamp stays sealed for the joint W1 scoring, where the fitted map can be scored as one
    more model.
- **Held-out class (sealed).**
  - One class is drawn from {RIM, AFD, AWA} by `numpy.random.default_rng(20261107).choice(["RIM", "AFD", "AWA"])`.
  - AIY is never held out (its data are spent or training-only).
  - The other two classes and AIY are the training set. One class is held out, not two: two held out would leave two
    training classes for 19 parameters.
  - The fit code never opens the held-out class's file. Only `scripts/worm/fit2_eval.py`, committed before it runs,
    opens it, once, after every registered fit has finished.
  - Drawn 7 Nov (time and result in section 7).

## 3. Objective (training) and the held-out score

- **Simulation.**
  - Each recorded class is the brain's own cell (left member: AIYL, RIML, AFDL, AWAL), built by `wormemu.brain.Brain`
    with the wiring removed and every input and cross-cell mechanism off, as `scripts/worm/single_cell_sanity.py`.
  - Each sweep starts from a fresh reset, settles 2 s at 0 pA, then runs the recorded protocol to 7.0 s.
  - The brain's internal step is 0.5 ms.
- **Features per sweep.** The data are smoothed with a 2 ms moving mean first.
  - baseline: mean V, 0.5-1.0 s.
  - early peak: the extreme V in the step's direction, 1.0-1.5 s.
  - steady state: mean V, 5.0-6.0 s.
  - after-step: mean V, 6.05-6.55 s.
- **Loss of a class:** the mean absolute feature error in mV over its 6 sweeps and 4 features (24 terms).
  - Training loss: the mean over the training classes, equal weight.
  - A non-finite trace scores 1000 mV.
  - Also reported, not in the objective: the RMSE over 1.2-7.0 s.
- **Held-out score:** the same loss on the held-out class's 6 FIT2 sweeps, computed once by `fit2_eval.py`.

## 4. The deliberately wrong models and the falsifier

- **Shuffles.**
  - 4 shuffled-CeNGEN models, seeds 20261108, 20261109, 20261110 and 20261111.
  - Each permutes the 128 neuron-class columns of the CeNGEN table (every gene moves together, so each class gets
    another class's whole profile).
  - A permutation is redrawn until none of the four recorded classes keeps its own profile.
  - TPMref, m_k, the bounds and the fit procedure are identical (TPMref and m_k are permutation-invariant).
- **Falsifier (registered).** FIT2's map is supported only if its held-out score is below every one of the 4
  shuffles' held-out scores. If any shuffle scores at or below it, the result reads "expression did not predict the
  held-out class better than shuffled expression", and the map is not adopted on this evidence.
  - With 4 shuffles, an uninformative map passes by chance 1 time in 5 (derived). This is a weak test with one
    held-out cell, and it is stated as such.
- **Reported beside it (not falsifiers):**
  - the held-out score of the brain as it stands (`expression_map=on`) and of BAAIWorm as ported
    (`expression_map=off`);
  - the training fit's AIY odd-sweep loss (consistency only, spent data);
  - the AIY voltage-clamp I-V against Naudin's mean and SD;
  - the single-cell sanity bars of section 0 over all 302 neurons under the fitted map (correctness, not a score).
- **Optional sixth fit, if time allows after the five registered ones:** a generic cell. Every channel family is
  present in every class at m_k * 10^a_f, with expression ignored. It is reported, not a falsifier.

## 5. Fitting and the stopping rule

- **Optimiser.** CMA-ES (`cma` package) on the 19 parameters, each scaled to [0, 1] within its bounds.
  - Start: the centre of the a_f bounds, b 0.5, e_leak the ledger template.
  - sigma0 0.25; population 16; one start per model.
  - The five registered fits (true map first, then the shuffles in seed order) get the identical budget.
- **Stopping rule** (whichever comes first):
  - 150 generations;
  - the best training loss improves by less than 0.1 mV over 20 generations;
  - CMA-ES's own tolerances (tolfun 1e-3, tolx 1e-4);
  - 3 h of wall per fit.
- **Checkpoint and resume.** The full CMA-ES state is pickled every generation; a restart resumes from it. A
  done-file per fit, and one when all five are done.
- **Where it runs.** backhouse, `~/worm-night/wexcite/fit2/`, 8 worker processes, one thread each. The 17:00-22:00
  cap is the machine's own.
- **Validity range of the result.**
  - The map is fitted on three somatic current-clamp cells at room temperature (the recordings' 20-22 C), on
    BAAIWorm's somatic channel set.
  - It says nothing yet about neurites, the classes' synaptic behaviour, or development.

## 6. Exposure before the draw (for the register)

- RIM and AFD, training sweeps 0 and 10: min and max printed 7 Nov about 01:40, to set item 0's sanity bars.
- AIY, training sweep 0: min printed (-126.3 mV). Same reason.
- AWA, Liu 2018 Fig 1A: the file has no header rows. Reading its "header" at about 01:48 therefore printed the first 3
  samples (t = 5.4-6.2 ms, before the step) of all 11 sweeps: about -78 mV.
  - So AWA's baseline is not fully unseen.
  - If AWA is the held-out class, the held-out score is also reported without the baseline feature (18 terms).
- AWA, Fig 1B: header lines only (10 sweeps named "CC-IV-2pA/step", 11 s).

## 7. Split (drawn after this file was written)

Drawn 7 Nov 01:51:50 CST, right after commit 01404ed:
`numpy.random.default_rng(20261107).choice(["RIM", "AFD", "AWA"])` returned **RIM** (numpy 2.x on the Mac venv).

- **Held out (sealed for FIT2): RIM**, its FIT2 sweeps (indices 0, 2, ..., 10). The fit code does not open
  `Fig1A_RIM_CC.txt`. These sweeps are W1's training sweeps, so W1's own seal (odd sweeps, voltage clamp) is untouched.
  The held-out evidence is weaker than an unseen recording: W1 fitted these sweeps per cell, and I printed the min and
  max of sweeps 0 and 10 (section 6). Neither reaches FIT2's map.
- **Training: AIY, AFD, AWA.** AWA is now training data, so its step timing is checked against its own traces
  before the first fit, and recorded here.
