# C. elegans single-neuron current-clamp sources (survey for tonight's fit)

Checked 2026-11-04 (date run before writing, per CLAUDE.md). Web search + direct API/file fetch only; no
secrets read. Backhouse path root: `~/worm-data/ephys/`. Mac path root: `data/worm/ephys/` (only copied if the
source's total size is under 20 MB; noted per row).

## Table

| Source | Neuron(s) | Raw data? | Protocol | Cells | Format | Size | Licence | URL | Code/model URL |
|---|---|---|---|---|---|---|---|---|---|
| **Naudin et al. 2022** PLoS ONE (`10.1371/journal.pone.0268380`), ephys credited to Q. Liu lab | AIY, RIM, AFD (non-spiking) | **Yes, raw CC traces** | Current-clamp, steps -15 pA to +35 pA by 5 pA (11 steps, matches filename "CC-IV 11 steps"); AFD raw sample interval 0.1 ms (10 kHz, measured from file); AIY/RIM exported pre-averaged ("reduce every 20 points"); room temp 22-23 degC (stated in paper) | RIM n=3, AIY n=7, AFD n=3 (stated in paper). Correction (spike, 4 Nov): the deposited AIY current-clamp file `Fig1A_AIY_CC.txt` is **one cell**; n=5-7 is the voltage-clamp population in `Fig1_IVcurves_AFD_RIM_AIY.xlsx` (n per voltage in the sheet) | Plain tab-delimited `.txt`, one time column + one voltage column per step, plus one summary `.xlsx` of I-V curves | 36 MB total (downloaded) | **CC BY 4.0** (confirmed via Mendeley API `data_licence`) | Mendeley `doi.org/10.17632/6pgdf3zrp3.1` (dataset id `6pgdf3zrp3`) | Model code: `github.com/lois76/codeGenerationNonSpikingCBM` (tag v1; archived at Zenodo `10.5281/zenodo.5407653`). Licence on that repo listed by Zenodo only as "Other (Open)", not a named OSS licence - re-check the repo's own LICENSE file before reuse. |
| **Liu, Kidd, Dobosiewicz, Bargmann 2018** Cell (`10.1016/j.cell.2018.08.018`) | AWA (spiking, Ca-mediated) | **Yes, raw CC/VC traces + Ca imaging** | Current/voltage clamp per figure; exact step list not pulled from methods text yet (would need full-text fetch of Methods, blocked by 403 on direct PDF fetch this pass) | Not confirmed count (paper reports multiple cells per genotype/condition) | Per-figure `.zip` (Figure 1-7, S1-S7), format inside not inspected (likely Igor/Clampfit exports or txt) | **809 MB total** across 15 zips (one file, calcium imaging raw data, is 219 MB; two figure zips S6/S7 are 390 MB and 100 MB) | **CC BY 4.0** (confirmed via Mendeley API) | Mendeley `doi.org/10.17632/tngf9w3pgd.1` (or short id `6pgdf3zrp3`→ no, AWA set is `tngf9w3pgd`) | Model/analysis code: Data Availability statement in the Naudin paper points to a Zenodo-archived GitHub repo (same `zenodo.5407653` lineage note - Liu is a shared senior author across both datasets) |
| **Nicoletti et al. 2019** PLoS ONE (`10.1371/journal.pone.0218738`), ModelDB 267187 | AWCon, RMD | **No raw traces in the repo/ModelDB** - model code only | Paper figures show CC and VC traces (not re-extracted as data this pass; would need figure PDF digitizing) | n/a (model, not raw deposit) | ModelDB files are XPPAUT `.ode` (`AWC.ode`, `RMD.ode`) | 2 small text files | Not stated on ModelDB page or repo | `modeldb.science/267187`; code mirror `github.com/ModelDBRepository/267187` | Channels modeled: K, Ca, big-conductance KCa (BK/Slo), small-conductance KCa (SK) currents (gene-level mapping and exact g values not yet pulled from the paper body - need a full-text pass) |
| **Nicoletti et al. 2024** PLoS ONE (`10.1371/journal.pone.0298105`) | AIY, RIM, AVAL/AVAR, VA5, VB6, VD5 | **No raw traces in the GitHub repo** - NEURON `.mod` + Python simulation code only, per-neuron (iclamp/vclamp variants) | Paper reproduces CC/VC experiments from literature (stated goal); for AIY/RIM this likely reuses the same Liu-lab data as above, not independently confirmed this pass | n/a | Python `.py` driving NEURON `.mod` mechanisms | small (code only) | **No LICENSE file found in repo** | `github.com/martinanicoletti92/CelegansInterMotorNeuronsModels` | Same repo is the model code |
| **BAAIWorm / MetaWorm** (Zhao et al. 2024, Nat Comput Sci, `10.1038/s43588-024-00738-w`) | Whole connectome (eworm submodel), compartmental, mechanism files configurable | Repo ships model/mechanism code and a connectome, not a traceable "raw patch-clamp dataset" for a single identified neuron - not useful for tonight's single-neuron fit | n/a | n/a | NMODL mechanisms + Python/C++ | not sized this pass | **Apache 2.0** (LICENSE file present, confirmed) | `github.com/Jessie940611/BAAIWorm` (submodules `eworm`, `MetaWorm`, `neuroXcore`) | Same repo |
| Broader Dryad/Zenodo/Figshare/OSF/ModelDB sweep (Goodman lab, Lockery lab) | - | **Not completed this pass** - time-boxed to the two Mendeley hits above, which already answered the "raw data" requirement | - | - | - | - | - | - | Flagged as a follow-up, not a blocker: the two datasets found already satisfy "raw trace data for an identified neuron with a published matching model." |

## What was downloaded

- Backhouse `~/worm-data/ephys/naudin2022_liu_aiy_rim_afd/`: `Fig1A_AIY_CC.txt` (6.2 MB), `Fig1A_RIM_CC.txt`
  (6.2 MB), `Fig1B_AFD_CC-IV_11steps.txt` (25 MB), `Fig1_IVcurves_AFD_RIM_AIY.xlsx` (13 KB). Total 36 MB, confirmed
  on disk.
- Mac `data/worm/ephys/naudin2022_liu_aiy_rim_afd/Fig1_IVcurves_AFD_RIM_AIY.xlsx` only (13 KB) - the full set is
  36 MB, over the 20 MB Mac-copy bar from the brief, so the two large trace `.txt` files stay on backhouse only.
- Liu et al. 2018 AWA set (809 MB) was **not downloaded** this pass - it is far over the size/time budget for
  "tonight," and AWA is a spiking neuron (more complex fit, EGL-19/SHK-1 Ca-spike mechanism) versus the
  non-spiking AIY/RIM/AFD set, which is smaller, already plain text, and pairs with a published model. Flagged
  for a later session if AWA is wanted.
- Nicoletti 2019/2024 GitHub repos were inspected (file listing) but not cloned; they are code only, no data to
  fetch, and small enough to clone in seconds when the model code is actually needed.

## Recommendation

**Fit AIY tonight** from `Fig1A_AIY_CC.txt` (or RIM as a close second). Reasoning:
1. It is genuine raw current-clamp data (not a figure to digitize), already plain tab-delimited text - no
   digitizing or proprietary-format parsing needed before fitting starts.
2. It has the largest cell count of the three in this set (n=7 vs RIM n=3, AFD n=3) - more basis for "consistent
   with some fly [worm] of this species" per the project bar, though n is still small; label any fitted
   parameter range **fitted**, not measured, and note n in provenance.
3. It pairs with a named published biophysical model (Naudin et al. 2022: `ICa,t + IKir + IK,p + IL`) with
   channel composition stated in the paper (S1 Table has the numeric parameters - not yet extracted; needed
   before fitting, separate step). AFD's channel set (`ICa,p + IKir + IK,t + IL`) is also stated and AFD has the
   most current steps (11, finer resolution) but only 3 cells and a much larger, less-reduced file (10 kHz, not
   pre-averaged) - more preprocessing before a fit.
4. Avoids AWA (spiking, Ca-action-potential mechanism - EGL-19/SHK-1) as a first target: it is a harder
   multicompartment/channel-kinetics problem and the dataset is 809 MB, mostly calcium-imaging video, not yet
   on backhouse.

**Caveats:**
- The AIY/RIM files are pre-decimated ("reduce every 20 points with Average") by the source lab before export -
  this is already-smoothed data, not the rawest form; the AFD file is raw at 10 kHz. If a higher-bandwidth AIY
  trace is wanted later, it does not exist in this deposit; would need to contact the Liu lab or use the figure
  reproduction in Nicoletti 2024 (same cells, different paper) as a cross-check only, not independent evidence.
- Model parameter values (conductances, Cm, Erev, temperature-matched) are referenced to a S1 Table in Naudin
  2022 that was not pulled into numbers this pass - needed before the fit can run; next step is a direct PDF/S1
  fetch of that paper.
- The Naudin-paper code repo's licence is listed by Zenodo only as "Other (Open)" - check the repo's own
  LICENSE file before any redistribution, even though the data itself is clearly CC BY 4.0.
- Cell counts (n=3, n=7, n=3) are small; per the project's "consistent with some worm of this species" bar this
  is usable, but any fitted value should carry that n and show it was checked against the whole small sample,
  not cherry-picked to one trace.
