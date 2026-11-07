# HELDOUT: the test set locked before any fitting

Ben's decision, 7 Nov 2026: "All data, lock now." The first fitting loss uses every dataset we
hold, and 20-30% of it is locked today, before anything is fitted, so no later fit can be tuned
against it even by accident. The lock lives in `data/worm/heldout/lock.json`.

## The rule

The held-out items in `lock.json` were chosen by reading **identifiers only**: animal and
recording IDs, neuron and strain names, gene names, file names, and counts. No measured trace,
response, kinematic value or score was read to make the choice. Where a file mixed identifiers
and values (for example an HDF5 file with both an animal ID in its filename and calcium traces
inside it), only the identifier was read - names and shapes (via `tar -t` and `h5py`'s key
listing), never the arrays.

The set itself was drawn with a fixed seed, `numpy.random.default_rng(20261107)`, not by looking
at the data and not by hand-picking anything that happened to look convenient. Two splits already
existed before today and were kept exactly as they were, not re-drawn, for consistency with work
already done on them:

- **Randi 2023**: 34 held-out stimulated neurons (of 171) plus all unc-31 animals, sealed in
  `FIT1.md` on seed 20261106.
- **Single-cell ephys**: RIM held out as a whole neuron class, sealed in `FIT2.md` by
  `numpy.random.default_rng(20261107).choice(['RIM','AFD','AWA'])`.

**Locked items are never looked at, fitted to, or plotted until one pre-registered scoring run**,
the same rule `FIT1.md` and `FIT2.md` already use: write the scoring code first, commit it, then
open the sealed file once.

## How a fitter must exclude the locked items

1. Load `data/worm/heldout/lock.json`.
2. For the dataset you're about to fit, read its `locked` list (or, for `atanas2023`, each
   condition's `ids` list).
3. Before building your training batch, filter by the matching identifier: stimulated-neuron
   name, animal/recording ID, strain name, neuron class, or corpus-item name. Drop anything that
   matches, for every genotype/condition it appears under (`randi2023`'s unc-31 lock means the
   *whole* strain is dropped, not a sample of it).
4. For `owmd_javer2018`, check both the dataset's own `locked` list and the
   `perturbation_corpus` entry's `locked` gene list - a gene can be sealed under one and not yet
   drawn under the other, and the lock file already unions the two where that matters (see its
   `forced_by_perturbation_corpus_seal` field).
5. If you are about to score a model against held-out data, stop and check this file's "never
   until one pre-registered scoring" rule first - write the eval script, commit it, then run it
   once.

## The table

| Dataset | Unit | n | Locked n | Locked % | Procedure |
|---|---|---|---|---|---|
| randi2023 (wild-type) | stimulated neuron | 171 | 34 | 20% | Existing seal, `FIT1.md`, seed 20261106 |
| randi2023 (unc-31) | animal / whole strain | 18 animals, 108 stimulated neurons | 18 | 100% | Existing seal, `FIT1.md`; whole mutant cohort reserved for the peptide-layer test |
| ephys (single-cell) | neuron class | 4 (AIY, RIM, AFD, AWA) | 1 (RIM) | 25% | Existing seal, `FIT2.md`, seed 20261107 |
| atanas2023_main | animal recording | 80 | 20 | 25% | New draw, seed 20261107; kept out of the whole-condition slot by design (primary L3 fitting corpus) |
| atanas2023 / pradhan2025 | animal recording (whole condition) | 8 | 8 | 100% | New draw, seed 20261107; drawn as the whole-condition lock among the two smaller secondary collections |
| atanas2023 / dag2023 | animal recording | 15 | 4 | 27% | New draw, seed 20261107 |
| owmd_javer2018 | strain / genotype | 17 | 6 | 35% | New draw (25% -> 5), unioned with the matching perturbation-corpus gene locks (+1, egl-2/flp-1/unc-17 already drawn there) |
| yemini2013 | strain | 304 | 76 | 25% | New draw, seed 20261107 |
| neuropal2021 | animal recording (single strain, OH16230) | 21 | 6 | 29% | New draw, seed 20261107 |
| perturbation_corpus | corpus item (mutant/ablation/stimulus) | 22 | 7 | 32% | Stratified new draw: 1/1 ablation, 2/4 stimulus, 4/17 mutant |
| wormbase_phenotype | gene (genome-wide) | ~20,000 | 0 | n/a | Not split - a categorical reference lookup, never fit against directly |

Not split, unchanged: `cook2019`, `witvliet2021`, `cengen`, `peptide_connectome`,
`morphologies`, `misc`, `brittin2021`. These are structural, connectome and gene-expression
priors the model is built from, not repeated-measurement corpora with a train/test question of
their own; `SCOREBOARD.md` already has them as FIT (not held out), and that is not reopened here.

## Notes and honest limits

- **atanas2023's family is bigger than `MANIFEST.md` says.** Alongside the 80-animal Atanas 2023
  set (`MANIFEST.md` section 6), backhouse now also has `wormwideweb_extra/pradhan2025/` (8
  animals) and `wormwideweb_extra/dag2023/` (15 animals), fetched 5 Nov but not yet written into
  `MANIFEST.md`. All three are freely-moving whole-brain NeuroPAL+GCaMP recordings and were
  treated as one family here, with atanas2023_main protected from the whole-condition lock
  because it is the dataset the first whole-brain loss (L3) is actually built on - locking it
  wholesale by an unlucky draw would have left nothing to fit.
- **atanas2023 also has a `scrambled-2022-10-03-01/` subfolder** (11 files): a derived,
  shuffled-neuron-identity copy of 11 of the main 80 animals, not independent data. It is
  excluded from both the fitting pool and the lock.
- **The "mutant/perturbation corpus" has no raw trace data on backhouse yet.** `wormbase_phenotype/`
  is a genome-wide categorical lookup (which genes have a phenotype term), not a per-animal
  measurement. The 22 locked/open corpus items are gene and ablation *names* reserved from
  `PERTURBATION_CORPUS.md`'s list and `SCOREBOARD.md`'s mutant rows, for whenever real
  perturbation data or a cited phenotype number is brought in later. The one place real
  quantitative mutant data already exists is `owmd_javer2018`'s 16-strain panel, and its lock is
  unioned with this corpus draw so the two never contradict each other.
- **No literal "stimulus" corpus item was found on disk**, only mutants and one ablation. The
  "stimulus" stratum was read as the corpus items whose published readout is a pharmacological
  dose-response assay (slo-1/ethanol, unc-49 and unc-29/unc-38/levamisole, unc-17/aldicarb) rather
  than a baseline behavioural rate. This is a declared judgment call, not a measurement, and is
  recorded here so it can be revisited if better stimulus data turns up.
- **Overall locked fraction runs 20-35% per dataset**, not a flat 25%, because the existing seals
  (unc-31's whole strain, RIM's whole class) and the stratification/union rules sometimes push a
  dataset above the 25-30% guideline. This is intentional: the stronger, more specific rule (whole
  mutant cohort, whole neuron class, whole gene across datasets) was never weakened just to hit a
  round number.
