# From the worm we have to a real worm (7 Nov 2026, 01:16 CST, main at c0c13b8)

Written by wfinal from `docs/worm/MECHANISMS_AUDIT.md` (rows 1-28), `docs/worm/CATALOG.md` (the ledger at
7b49648), the Open lists of the 6-7 Nov night files, FIT1.md (wfit worktree) and STRATEGY.md.

## Verdict

**Not a real worm yet, and the gap is mostly numbers, not mechanisms.**

- Every PLAN row runs in the v1 loop: 13 rows full and 15 lumped (audit).
- The numbers that set brain dynamics are mostly guesses. 9,246 of the 20,252 physiology numbers are guessed (46%, derived from CATALOG). 7,753 of those sit in four connection blocks: per-pair synapse, gap and NMJ strengths, and receptor assignment. That leaves 1,493 guessed numbers spread over everything else.
- 11 rows fail a unit check today.
- In the 20 s v1 loop the worm does not crawl. It holds a shallow one-sided bend and drifts 0.61 body lengths (measured, night file step 3).

The first two items below need no lab: they are fits to data we already hold on backhouse (Randi 2023, Atanas 2023, CeNGEN, Cook 2019, recordings). The bar stays STRATEGY's: predict held-out perturbations (mutants, ablations, new stimuli) with no refit, within real animal-to-animal spread.

**Cost classes** (mine, for this list):
- **A**: hours. Data in hand; a script, or a choice between published values.
- **B**: one to three nights. Port or fit one published model or free dataset, with one pre-registration.
- **C**: a week or more of backhouse nights. A whole-worm pre-registered fit with held-out tests.
- **L**: needs a lab measurement. We can only write the experiment down (Ben's call).

## Ranked by expected effect on brain function (brain first)

**1. Synapse and gap-junction strengths (rows 7, 8).** Cost C (FIT1 under way), then L for spot checks.
- **Now:**
  - Every chemical pair's conductance is one shared per-contact value times Cook's measured contact count: `syn_strength_per_pair` 3,709 guessed, `nmj_strength_per_pair` 956, `gap_strength_per_pair` 1,091.
  - For 1,997 of the 3,709 pairs, which receptor class carries the synapse is guessed (`syn_sign_receptor`).
  - Network state swings with any global change. 197 of 302 neurons were above -20 mV with every default on (6 Nov), 94 once neuromodulation's Gi was on, and 16% in v1 (measured).
- **Would pin it:**
  - FIT1 (pre-registered, no result yet): 23 class-shared values fitted to Randi 2023's propagation atlas (held). 137 stimulated neurons train, 34 are held out, and unc-31 is sealed for the peptide test. A degree-preserving shuffled connectome must do worse.
  - Next, Atanas 2023 freely-moving whole-brain activity (held) for the network state.
  - Gap junctions per innexin from Bhattacharya 2019 expression (held) times unitary conductances. Those are 25 slot numbers, guessed.
  - Per-pair values will not be pinned by any dataset we know of. Class-level is the realistic grain (CATALOG says the same).

**2. Neuron excitability and calcium (rows 3-6, 19).** Cost C for the map, L for unrecorded classes.
- **Now:**
  - BAAIWorm's per-cell values are used as published. 709 guessed numbers are clips to a literature range, plus `pas_soma_cm` and `pas_neurite_cm` (302 guessed each).
  - Nicoletti densities per (gene, class): 216 inferred and 189 guessed. These 478 `mech.channels` Specs are not in the ledger yet.
  - Channels sit at the soma only. Leak K2P (35 twk genes), shw, kvs, DEG/ENaC, TRP and CNG have no model (CHANNEL_SLOTS).
  - **Failing checks:**
    - row 4 W, 3.8 mV against 2;
    - row 6 volumes, up to 3.05x Nicoletti's cells;
    - neuron Ca peaks near 0.11 uM, so GCaMP barely moves;
    - AIYL reaches +168 mV under 20 pA in a 4-cell brain.
  - FIT1's own declared limit: the template's autoresponse 30 s mean is 0.014-0.018 against a training median of 0.43, and AVAL reaches only 0.048 at every upper bound. The readout can absorb an excitability deficit, so item 1's fit must be read with this.
- **Would pin it:**
  - STRATEGY move 2: one expression-to-physiology map (gene family > selector battery > class) fitted on recorded neurons and tested on held-out recorded classes. Inputs: CeNGEN (held), Nicoletti 2019/2024 and the AIY/RIM/AFD recordings (on backhouse).
  - Most classes have no recording. Whole-cell current clamp of a held-out set of classes is the lab ask.

**3. Release and short-term plasticity (rows 7, 24).** Cost B.
- **Now:**
  - One BAAIWorm release curve serves every presynaptic class, and release is graded only (Liu's 10.2 /s voltage-independent floor is not split out).
  - Tonic release depletes the pool at rest (x 0.30 at -60 mV).
  - **Failing checks at the ledger values:** the composite NMJ GABA IPSC decays in 29.2 ms against 24.8 +/- 2.7, and the GABA STP plateaus are 0.76 and 0.57 against > 0.8.
  - Row 24's held-out bars were seen three times, so they are no longer clean evidence.
- **Would pin it:** release per presynaptic class from Randi's time courses (held). Also the published NMJ recordings at 1, 5 and 20 Hz (Liu 2009 and later). A fresh held-out set is needed for row 24.

**4. Neuromodulation: peptides, monoamines, RIS (rows 9, 10, 28).** Cost C for the fit, L for coupling.
- **Now:**
  - 125 guessed numbers in row 9 and 40 in row 10, including per-gene current gains and per-family release rates (`pep_gain_pA` 51, `pep_release_nM_per_s` 49, `ma_gain_pA` 14).
  - 21 of 69 GPCRs have unknown G-protein coupling, split a third each. Gi dominates: mean Gi 0.80 in v1 and RIS Gi 0.998.
  - The peptide maximum is still rising at 20 s (18 nM).
  - **Failing check:** RIS Gi without its autoreceptor is 0.034 against a bar of 0.
- **Would pin it:** the sealed unc-31 atlas (Randi 2023, held), scored once, as FIT1's peptide-layer test. The EC50s from Beets 2023 are already in. Coupling assays for the 21 unknown GPCRs are the lab ask.

**5. Sensory transduction (row 17).** Cost B.
- **Now:**
  - 61 guessed numbers.
  - **Failing check:** AWA (Liu 2018 port) is not all-or-none and blocks near -12 mV. The printed Kir sign is suspect.
  - The cyclase-route cells (ASE, AFD, URX, BAG) move Po by at most about 10%. Their gain is guessed, and URX has no tonic O2 response.
  - Gentle touch gave 0.042 nS on 6 Nov, against measured tens of pA. The catalog has since raised the channel count from 50 to 113; not re-run.
  - DVA's strain field is guessed.
- **Would pin it:** published calcium and current responses for these cells against the same stimuli (free papers), with the gain fitted per cell type and held-out stimuli kept back.

**6. Slow signalling, learning, homeostasis, glia (rows 11, 18, 19, 24b).** Cost B.
- **Now:**
  - EGL-4, CMK-1 and the associative term act on release, standing in for their measured targets (AWC transduction, AFD's T*). DAF-7 and CREB have outputs nothing reads, and learning is 9 guessed numbers.
  - Glia: the AMsh cell and the amphid K+ compartment are not linked. The Kir null is only 1.07x slower on today's main (1.17x on 6 Nov), with a guessed leak and ending volume, and the check now fails 3 of 4.
- **Would pin it:** published adaptation and learning time courses (L'Etoile 2002, Yu 2014; partly in) as held-out tests. Move the effects onto their real targets first (code, A to B).

## Then the body (it closes the loop, but brain function comes first)

**7. Body-wall muscle (row 12).** Cost B.
- **Now:** Du 2025's muscle has no stable rest and fires on its own; mean activation is 0.037 in v1. `mpas_epas` (95) and `bwm_gap` (96) are guessed. The old gap range contradicts Liu 2006's measured 350 pS or less.
- **Would pin it:** published body-wall muscle recordings, refit at class level.

**8. Body mechanics (row 21).** Cost A to B.
- **Now:**
  - **Failing check:** the stiffness and damping unit check fails. The Frontiers 2024 moduli give a section 7.8x stiffer in bending than Backholm 2013's whole-worm value.
  - The damping prefactor is guessed.
  - The tail's curvature with damping on is unexplained.
- **Would pin it:** choose between two published measurements by a bending test (Backholm 2013, measured).

**9. Organs (rows 13-16).** Cost B each.
- **Now:**
  - **Pharynx:** 0 pumps in v1 (muscles at -70 mV at 18.75 s; on 6 Nov they sat depolarised at -35 to -24 mV), so metabolism only falls.
  - **Defecation:** the Ca fall takes 9.8 s against Espelt's 23 +/- 3 s.
  - **Egg-laying:** the vulval muscles never reach threshold.
  - **Hypodermis:** follows a guessed rest, and seam cells are absent.
  - The pharynx and egg-laying problems follow the network state (items 1-4).
- **Would pin it:** the papers each row already cites (Raizen and Avery 1994 EPGs, Espelt 2005, Collins 2016), as held-out tests after items 1-4.

**10. The small rows (20, 22, 23, 25, 26, 27).** Cost A to B.
- **Now:**
  - **Failing check:** the opto sign check (row 23).
  - PMCA, SERCA and NCX are missing (row 27).
  - The Q10 does not reach BAAIWorm's own channel gating (row 25).
  - Noise passes its checks.
- **Would pin it:** mostly published single numbers; little effect on brain function until items 1-4 are done.

## Not a numbers problem

- Two checks never done: a compartment convergence check (row 2) and neurite channels.
- ER calcium is missing.
- Most gene families have no published C. elegans kinetics. STRATEGY's answer is homologue priors and keeping the alternative worms that differ there, with the experiment written down.
- Speed is not the blocker. v1 runs at 11.85 s wall per bio s on the Mac (measured), inside the 100x cap. The brain-only fitting configuration is FIT1's, on backhouse.
