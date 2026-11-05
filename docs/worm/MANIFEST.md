# worm-data manifest

All data lives on backhouse under `~/worm-data/`. This file is mirrored there as `~/worm-data/MANIFEST.md`.
Fetched 2026-11-04 (date run on backhouse before writing this line: `Wed Nov 4 22:36 CST 2026`).

Budget: up to 150 GB. Actual total: 2.5 GB (see summary table). `~/worm-data/ephys/` is another assistant's
folder (`naudin2022_liu_aiy_rim_afd`, 36 MB) and was left untouched; it is listed here only so nothing is lost.
All downloads finished; no download/fetch processes are left running on backhouse.

## Summary table

| name | size | licence (as stated at source) | status |
|---|---|---|---|
| cook2019 | 12 MB | "Emmons Lab Copyright (c) 2020" (wormwiring.org footer); no further terms stated | complete |
| witvliet2021 | 91 MB | GPL-3.0 (NemaNode repo licence field; data files inherit the repo's declared licence, not independently re-licensed by the authors) | complete |
| cengen | 426 MB | not stated (checked cengen.org/downloads/ page text; no licence or terms found) | partial (thresholds + bulk tsvs + one neuron-only single-cell object; big Seurat objects and raw GEO reads skipped) |
| peptide_connectome | 1.0 GB | Neuropeptide-Connectome repo: MIT. Beets 2023 supplement: Cell Reports (open access), licence not independently confirmed (cell.com blocked fetch; PMC copy used). Bentley 2016 supplement: PLOS CC BY 4.0 (journal-wide licence) | complete |
| randi2023 | 637 MB | OSF project e2syt: no node_license set (checked OSF API `node_license` field = null) i.e. not stated. wormneuroatlas package: GPL-3.0 | complete (core processed exports; pre_review/full duplicate variants skipped) |
| atanas2023 | 714 MB | CC BY 3.0 US (Zenodo record 8185377 metadata) | complete (large model-fit files skipped, see below) |
| morphologies | 121 MB | not stated (GitHub API licence field = null for openworm/CElegansNeuroML; no LICENSE file in repo root) | complete |
| misc | 168 KB | Cell (Elsevier) copyright, not open access; supplement fetched via PMC post-embargo public access copy | complete (Bhattacharya 2019 innexin mmc1 only; monoamine connectome covered under peptide_connectome instead) |
| ephys (not mine) | 36 MB | n/a, another assistant's folder, untouched | n/a |

## 1. cook2019

**Citation:** Cook SJ, Jarrell TA, Brittin CA, Wang Y, Bloniarz AE, Yakovlev MA, Nguyen KCQ, Tang LT, Bayer EA,
Duerr JS, Bulow HE, Hobert O, Hall DH, Emmons SW (2019). "Whole-animal connectomes of both Caenorhabditis elegans
sexes." Nature 571, 63-71. DOI: 10.1038/s41586-019-1352-7.

**Source URL(s) used:** `https://wormwiring.org/si/<filename>.xlsx`, linked from `https://wormwiring.org/pages/adjacency.html`.

**Local path:** `~/worm-data/cook2019/`

**Size:** 12 MB (measured, `du -sh`). 9 files.

**Licence:** "Emmons Lab Copyright (c) 2020" stated at the bottom of the wormwiring.org page. No CC licence or other
usage terms found on the page.

**Date fetched:** 2026-11-04.

**Contents:**
- `SI 2 Synapse adjacency matrices.xlsx` - per-synapse adjacency, hermaphrodite + male adult.
- `SI 3 Synapse lists.xlsx` - synapse lists, hermaphrodite + male adult.
- `SI 4 Cell lists.xlsx` - list of all cells/neurons by class, both sexes (doubles as the WormBase/WormAtlas-style
  cell list requested under item 8; a separate dedicated fetch was skipped as redundant).
- `SI 5 Connectome adjacency matrices, corrected July 2020.xlsx` (and the original, uncorrected version) - cell-cell
  chemical and gap-junction adjacency matrices. Verified sheet names (read with openpyxl): `hermaphrodite chemical`,
  `hermaphrodite gap jn asymmetric`, `hermaphrodite gap jn symmetric`, `male chemical`, `male gap jn asymmetric`,
  `male gap jn symmetric`. Units: synapse/gap-junction contact counts between named cells.
- `SI 6 Cell class lists.xlsx`, `SI 7 Cell class ... adjacency matrices...xlsx` (corrected + original) - same data
  collapsed to cell-class level.
- `Adult and L4 nerve ring neighbors.xlsx` - physical contact adjacency, adult and L4 nerve ring/ventral ganglion.

**Not fetched:** nothing known to be missing; these are all the files linked from the adjacency page.

**sha256 (key files):**
- `SI 5 Connectome adjacency matrices, corrected July 2020.xlsx`: `1f4fdbf84746b69b49a8da0816f52787860ce349b638dce37924ba80f90c70c9`
- `SI 2 Synapse adjacency matrices.xlsx`: `ae59aa8b4bdf8f12c3bf14bfb19e71225c3db0dbe42d9155e1f0bdf796d8f2e0`

## 2. witvliet2021

**Citation:** Witvliet D, Mulcahy B, Mitchell JK, Meirovitch Y, Berger DR, Wu Y, Liu Y, Koh WX, Parvathala R,
Holmyard D, Schalek RL, Shavit N, Chisholm AD, Lichtman JW, Samuel ADT, Zhen M (2021). "Connectomes across
development reveal principles of brain maturation." Nature 596, 257-261. DOI: 10.1038/s41586-021-03778-8.

**Source URL(s) used:** `https://github.com/zhenlab-ltri/NemaNode` (the source code for the nemanode.org website;
`src/server/populate-db/raw-data/` holds the actual processed connection and trajectory data as JSON, which is
what nemanode.org serves dynamically - cloning the repo was the practical way to get the real files rather than
the JS-rendered site).

**Local path:** `~/worm-data/witvliet2021/NemaNode/`

**Size:** 91 MB (measured). Git repo, many files (connections + trajectories + annotations JSON + site code).

**Licence:** GPL-3.0 (GitHub-declared licence on the repo).

**Date fetched:** 2026-11-04.

**Contents:** `src/server/populate-db/raw-data/connections/` has one JSON per dataset: `witvliet_2020_1` through
`_8` (3x L1, 1x L2, 1x L3, 2x adult) plus `white_1986_jse/jsh/n2u/whole` (the original White 1986 reconstructions,
included for continuity). Verified structure of `witvliet_2020_7.json`: a flat list (2,781 entries for that
dataset) of edges, each `{pre, post, pre_tid, post_tid, ids, syn, typ}` - pre/post are neuron names, `syn` is
synapse count per EM section, `typ` the synapse type code. `raw-data/trajectories/` has the corresponding neurite
skeleton/position data per dataset (not raw EM images). `raw-data/annotations/` has per-cell annotation JSON.

**Not fetched:** raw EM volumes (not public via this route; nemanode.org/EM archive hosts those separately and
they are large microscopy data, out of scope per instructions).

## 3. cengen

**Citation:** Taylor SR, Santpere G, Weinreb A, Barrett A, Reilly MB, Xu C, Varol E, Oikonomou P, Glenwinkel L,
McWhirter R, Poff A, Basavaraju M, Rafi I, Yemini E, Cook SJ, Abrams A, Vidal B, Cros C, Tavazoie S, Sestan N,
Hammarlund M, Hobert O, Miller DM (2021). "Molecular topography of an entire nervous system." Cell 184,
4329-4347.e23. DOI: 10.1016/j.cell.2021.06.023. (Downloads page is still branded "CeNGEN"; some sources cite
Hammarlund/Hobert/Miller/Sestan as corresponding, journal citation as above.)

**Source URL(s) used:** `https://cengen.org/storage/<file>` as linked from `https://www.cengen.org/downloads/`.

**Local path:** `~/worm-data/cengen/`

**Size:** 426 MB (measured). 9 files.

**Licence:** not stated. Checked the downloads page text directly; no CC licence, copyright line, or "for research
use" language was present.

**Date fetched:** 2026-11-04.

**Contents:**
- Threshold csvs (`021821_{liberal,medium,conservative,stringent}_threshold{1,2,3,4}.csv`): binary expressed/not
  calls per gene per neuron class, four stringency levels (threshold 1 most permissive to 4 most stringent). Value
  is average TPM per gene per neuron type above/below threshold (0 = not expressed).
- `Average_integrated_TMM_counts_lengthNormalized_111521.tsv`: normalized integrated bulk+single-cell counts,
  143 replicates.
- `Barrett_et_al_2022_CeNGEN_bulk_RNAseq_data.tsv`: raw bulk RNA-seq gene counts, 160 samples (FACS-sorted neuron
  classes).
- `CeNGEN_aggr_bio_reps_101821.tsv`: single-cell pseudobulk counts aggregated by biological replicate.
- `Barrett_et_al_2022_CeNGEN_bulk_RNAseq_geneLevel_metadata.tsv`: gene-level metadata for the bulk set.
- `092320_L4_neuron_only_monocle_cds_for_paper.rds`: the single-cell Monocle3 CDS object, L4 neurons only
  (70,296-cell dataset), 300 MB on the server / 320 MB on disk here. Chosen over the larger (500 MB-4 GB) Seurat
  objects as the smallest format that still carries the full single-cell object, consistent with the "if under
  ~10 GB" instruction.

**Not fetched:** the full all-cells (100,955-cell) Seurat/Seurat5/Monocle objects, the 4 GB neuron-only Seurat
object, and raw reads (GEO GSE136049, GSE169137) - all either redundant with the neuron-only Monocle object taken,
or raw sequencing data out of scope. Newer 2024/2025 CeNGEN work (L1 larvae, adult hermaphrodite, adult male
scRNA-seq, described in the 2024 CeNGEN integrated-analysis manuscript, code at
`github.com/cengenproject/CeNGEN_integrated_analysis_2024`) was located but not fetched: the new raw scRNA data
sits on GEO under separate accessions not identified in this session, and the repo found is analysis code, not a
new processed matrix release comparable to the threshold csvs above.

## 4. peptide_connectome

**Citations:**
- Ripoll-Sanchez L, Watteyne J, Sun H, Fernandez R, Taylor SR, Weinreb A, Bentley BL, Hammarlund M, Miller DM,
  Hobert O, Beets I, Vertes PE, Schafer WR (2023). "The neuropeptidergic connectome of C. elegans." Neuron 111,
  3570-3589.e5. DOI: 10.1016/j.neuron.2023.09.043.
- Beets I, Zels S, Vandewyer E, Demeulemeester J, Caers J, Baytemur E, Courtney A, Golinelli L, Hasakioğulları İ,
  Schafer WR, Vertes PE, Mirabeau O, Schoofs L (2023). "System-wide mapping of peptide-GPCR interactions in
  C. elegans." Cell Reports 42, 113058. DOI: 10.1016/j.celrep.2023.113058. PMID 37656621, PMC7615250 (NIH public
  access copy, used for the download).
- Bentley B, Branicky R, Barnes CL, Chew YL, Yemini E, Bullmore ET, Vertes PE, Schafer WR (2016). "The Multilayer
  Connectome of Caenorhabditis elegans." PLOS Computational Biology 12(12): e1005283. DOI:
  10.1371/journal.pcbi.1005283. (This is the paper for item 8's "monoamine connectome"; filed here alongside the
  other peptide/GPCR data rather than in misc/, since it is small and thematically linked.)

**Source URL(s) used:**
- `https://github.com/LidiaRipollSanchez/Neuropeptide-Connectome` (git clone).
- `https://pmc.ncbi.nlm.nih.gov/articles/instance/7615250/bin/<file>` (Beets 2023 supplement).
- `https://journals.plos.org/ploscompbiol/article/file?id=10.1371/journal.pcbi.1005283.s0XX&type=supplementary`
  (Bentley 2016 S1 Dataset + S1-S14 Tables).

**Local path:** `~/worm-data/peptide_connectome/`

**Size:** 1.0 GB (measured). 3 subfolders (`Neuropeptide-Connectome/`, `beets2023_gpcr/`, `bentley2016_monoamine/`).

**Licence:** `Neuropeptide-Connectome` repo: MIT (GitHub-declared). Beets 2023: Cell Reports is an open-access
journal; exact licence line not independently confirmed (cell.com blocked automated fetch with a 403; relied on
the PMC public-access mirror, which does not display a licence banner in the fetched content). Bentley 2016: PLOS
journals apply CC BY 4.0 to all articles and supplementary files (journal-wide policy, confirmed via PLOS's
licensing page).

**Date fetched:** 2026-11-04.

**Contents:**
- `Neuropeptide-Connectome/`: full repo - `Adjacency matrices for networks/` (short-range and mid-range
  neuropeptide-GPCR connectome edge lists and per-neuron-pair network matrices, 92 x 92), `Supplementary Tables/`,
  `Scripts & data/`, figures and topology-measure outputs. Source scRNA-seq is CeNGEN (see above); receptor
  deorphanization is Beets 2023 (below).
- `beets2023_gpcr/`: `EMS189789-supplement-Data_S1.zip` (the raw deorphanization screen data), two supplementary
  PDF documents (figures S1-S12 + Table S1 listing all peptide-GPCR interactions; Document S2).
- `bentley2016_monoamine/`: `S1_Dataset.zip` (the monoamine + partial neuropeptide connectome data itself) plus
  `S1_Table.docx` through `S14_Table.docx` (gene expression / connectivity supporting tables).

**Also note:** the `wormneuroatlas` package cloned under `randi2023/` (see below) separately bundles its own
processed copies of the Bentley 2016 monoamine connectome (`esconnectome_monoamines_Bentley_2016.csv`) and
neuropeptide connectome (`esconnectome_neuropeptides_Bentley_2016.csv`) and the Beets deorphanization table
(`deorphanization_media_6.csv`) in ready-to-use csv form - useful as a machine-readable cross-check against the
docx/zip originals here.

**Not fetched:** nothing known to be missing for the three papers' primary data.

## 5. randi2023

**Citation:** Randi F, Sharma AK, Dvali S, Leifer AM (2023). "Neural signal propagation atlas of Caenorhabditis
elegans." Nature 623, 406-414. DOI: 10.1038/s41586-023-06683-4.

**Source URL(s) used:**
- OSF project `https://doi.org/10.17605/OSF.IO/E2SYT` (via the OSF API, `api.osf.io/v2/nodes/e2syt/files/osfstorage/`).
- `https://github.com/francescorandi/wormneuroatlas` (git clone) - the companion Python package, which bundles a
  pre-built functional-connectivity atlas file (`funatlas.h5`) and several other papers' processed data as a
  convenience.

**Local path:** `~/worm-data/randi2023/`

**Size:** 637 MB (measured). `exported_data.tar.gz` (523 MB) + `spont_data_fig6.zip` (2.4 MB) + `wormneuroatlas/`
package (136 MB).

**Licence:** OSF project e2syt has no licence set (`node_license` field is null via the OSF API - checked
directly, not inferred). `wormneuroatlas` package: GPL-3.0 (GitHub-declared).

**Date fetched:** 2026-11-04.

**Contents:**
- `exported_data.tar.gz`: the main processed optogenetic-stimulation + whole-brain calcium imaging dataset
  (the "signal propagation" measurements: direct activation of one neuron, simultaneous recording of others).
- `spont_data_fig6.zip`: spontaneous-activity recordings used for the paper's Figure 6 comparison.
- `wormneuroatlas/wormneuroatlas/data/funatlas.h5`: the pre-built functional connectivity atlas (signed, directed
  functional connections between neuron pairs, derived from the above). This is the "processed functional
  connectivity matrix" requested; it is bundled here as the most directly usable form of the Randi 2023 result.
  The same package also carries anatomical connectome csvs (White 1986, Witvliet 2020 datasets 7/8 - duplicates
  of items already fetched above, kept for cross-checking) and `cengen.h5` (duplicate of item 3 in packaged form).

**Not fetched:** OSF also has `exported_data_unc31*.tar.gz`, `exported_data_pre_review.tar.gz`,
`exported_data_full*.tar.gz` (up to 1.1 GB) - earlier/alternate-filter versions of the same core dataset; skipped
as redundant with `exported_data.tar.gz`. A `raw_extracted_data/` OSF subfolder (about 185 MB across ~100+ small
per-recording text files: gcamp traces, timestamps, stim-neuron labels) was found but not fetched - it duplicates
the content of the processed tar.gz in a more fragmented form and fetching it would mean 100+ individual API
calls; flagged here in case it's wanted later. DANDI archive NWB-format raw imaging (dandiset 001075) was not
fetched (large, raw format, out of scope per instructions).

## 6. atanas2023

**Citation:** Atanas AA, Kim J, Wang Z, Bueno E, Becker M, Kang D, Park J, Estrem C, Kramer TS, Baskoylu S,
Mansinghka VK, Flavell SW (2023). "Brain-wide representations of behavior spanning multiple timescales and
states in C. elegans." Cell 186, 4134-4151.e31. DOI: 10.1016/j.cell.2023.07.035.

**Source URL(s) used:** Zenodo record `https://zenodo.org/records/8185377` ("CePNEM model analysis data and
ANTSUN and microscopy neural network weights"), via the Zenodo API file-content links, as linked from
wormwideweb.org's datasets page.

**Local path:** `~/worm-data/atanas2023/`

**Size:** 714 MB (measured, `du -sh`). 2 files: `processed_h5.tar.bz2` (747,188,437 bytes) +
`dict_neuropal_label.jld2.bz2` (1,313,076 bytes).

**Licence:** CC BY 3.0 US (stated in the Zenodo record metadata).

**Date fetched:** 2026-11-04.

**Contents:** `processed_h5.tar.bz2` - the ANTSUN-pipeline processed whole-brain calcium imaging + behaviour data
in HDF5 format (NeuroPAL-identified neuron traces and simultaneous behaviour annotations; this is the processed
form, not raw microscopy). `dict_neuropal_label.jld2.bz2` - the NeuroPAL neuron identity label dictionary (Julia
format, bz2-compressed), small.

**sha256:**
- `processed_h5.tar.bz2`: `be43aea0a7913eefceddb4a764a0778cb0b5b5a8e1f8e6e5e909ed3145edbeda`
- `dict_neuropal_label.jld2.bz2`: `9ae16d2316e605f90bdbf0fab9ae9f29b1b7a90d1041a7abaecb96e14b62f023`

**Not fetched:** the same Zenodo record also has `fit_results.jld2.bz2` (12.4 GB), `relative_encoding_strength.jld2.bz2`
(14.0 GB), `umap_dict.jld2.bz2` (4.1 GB), `fit_results_lite.jld2.bz2` (1.3 GB) and `deepnet-weights.tar.bz2`
(397 MB) - these are the paper's CePNEM model fit outputs and network weights, not raw/processed trace data, and
together would be ~32 GB; skipped as out of scope (model outputs, not source data) and to stay well clear of
unnecessary disk/bandwidth use. Kato et al. 2015 and Yemini et al. 2021 NeuroPAL data were not located as separate
small (<5 GB) downloads in this session and are not included.

## 7. morphologies

**Citation:** OpenWorm project, CElegansNeuroML repository (NeuroML2-format cell models and connectome tables,
compiled from White et al. 1986, Cook et al. 2019, Witvliet et al. 2021 by the OpenWorm community; no single
paper citation - it's a code/data repository, not a publication).

**Source URL(s) used:** `https://github.com/openworm/CElegansNeuroML` (git clone).

**Local path:** `~/worm-data/morphologies/CElegansNeuroML/`

**Size:** 121 MB (measured). Git repo.

**Licence:** not stated. Checked the GitHub API `license` field (null) and the repo root file listing (no
LICENSE file present).

**Date fetched:** 2026-11-04.

**Contents:** `CElegans/` - per-cell NeuroML2 morphology/cell files; `CElegansNeuronTables.xls` and
`NeuronConnectFormatted.xlsx` - neuron and connectivity tables; `herm_full_edgelist.csv` - hermaphrodite
connectome edge list in plain csv form; `sqlConnections/` - SQL-format connectivity data.

**Not fetched:** no BAAIWorm files (per instructions, not duplicated here - flagged as "only note if another
assistant already has it"; not checked whether one does, since this session only touches `~/worm-data/`).
Witvliet/Brittin nerve-ring skeleton files beyond what's in `witvliet2021/NemaNode` (trajectories) were not
separately located as standalone public skeleton files (e.g. SWC) in this session.

## 8. misc

**Citation (innexin expression):** Bhattacharya A, Aghayeva U, Berghoff EG, Hobert O (2019). "Plasticity of the
Electrical Connectome of C. elegans." Cell 176, 1174-1189.e16. DOI: 10.1016/j.cell.2018.12.024. PMID 30686580,
PMC10064801 (NIH public access copy used for the download).

**Source URL(s) used:** `https://ars.els-cdn.com/content/image/1-s2.0-S0092867418316386-mmc1.docx` (Elsevier's
supplementary-content CDN, the pii-derived direct link; cell.com itself returned 403 to automated fetches).

**Local path:** `~/worm-data/misc/bhattacharya2019_innexin/`

**Size:** 168 KB (measured). 1 file.

**Licence:** Cell (regular Cell, not Cell Reports) is a subscription Elsevier journal, not open access; this copy
is the NIH-mandated public-access version released after the embargo period. No CC licence applies; usage terms
are Elsevier's standard copyright, consult the publisher for reuse beyond research/personal use.

**Date fetched:** 2026-11-04.

**Contents:** `mmc1.docx` - the paper's only numbered supplementary file (checked: no mmc2, mmc3, etc. exist on
the CDN at any common extension). Contains the innexin expression tables referenced in the paper (Table S1: innexin
expression per neuron class across 14 innexin genes, ~118 neuron classes; Table S2: developmental changes L2 to
adult) as a single combined document rather than separate machine-readable tables.

**Monoamine connectome (Bentley 2016):** fetched under `peptide_connectome/bentley2016_monoamine/` instead of
here, since it's the same paper family as the other peptide/GPCR data - see section 4 above. Not duplicated in
`misc/`.

**WormBase/WormAtlas cell list (all 959 somatic cells / 302 neurons with classes):** not separately fetched as a
dedicated file. `cook2019/SI 4 Cell lists.xlsx` (section 1 above) already is a cell-list-by-class table covering
both sexes from the same underlying anatomical source, and was judged to satisfy this item without a redundant
second download. If a WormBase-specific canonical list (e.g. from the WormBase REST API or WormAtlas's own
neuron-class table) is specifically needed later, it was not located/verified in this session.

## 9. Brain structure tables in the repo (`data/worm/structure/`, added 2026-11-05)

Small derived tables the brain reads directly (loader: `src/wormemu/brain_structure.py`). Raw sources stay on
backhouse as above; these are reproducible from them.

| file | rows | source | how made |
|---|---|---|---|
| `cells.csv`, `chem_edges.csv`, `gap_edges.csv` | 476 cells after the loader drops 3 SI 4 twins; 28,113 chemical synapses, 11,633 gap-junction contacts (hermaphrodite) | Cook 2019 SI 4 + SI 5 corrected July 2020 (section 1) | `scripts/worm/extract_structure.py` |
| `cengen_t2.csv` | 855 genes x 128 neuron classes, TPM at threshold 2 | CeNGEN (section 3) | same script; gene families widened 5 Nov (gnrr, nmur, sprr, trhr-1, pdfr) |
| `geometry.csv` | 302 neurons: soma x/y/z (um), soma diameter, membrane area (um2), neurite length, segment count | CElegansNeuroML `generatedNeuroML2/*.cell.nml` (section 7; Virtual Worm-derived morphologies) | `scripts/worm/extract_geometry.py` |
| `transmitters_wang2024.csv` | 282 neurons x 8 transmitters (0/1) | Wang et al. 2024 eLife 13:RP95402 neurotransmitter atlas, as tabulated by OpenWorm ConnectomeToolbox `https://openworm.org/ConnectomeToolbox/Wang2024Herm_data/` (fetched 2026-11-05) | copied from the page table |
| `peptide_gpcr_pairs.csv` | 92 ligand-receptor pairs | Ripoll-Sanchez et al. 2023 Neuron, pairs with EC50 <= 500 nM from Beets et al. 2023 (section 4) | copied from the Neuropeptide-Connectome repo |
| `monoamine_receptor_pairs.csv` | 14 transmitter-receptor pairs | Bentley et al. 2016 PLoS Comput Biol, via Ripoll-Sanchez 2023 (section 4) | same |

The 20 neurons Wang 2024 does not list take their transmitter from CeNGEN marker genes (unc-17, eat-4, unc-25,
cat-2, tph-1, tdc-1, tbh-1) where expressed (5 neurons), else none (15 neurons: no fast chemical output in the
model; recorded in the ledger).
