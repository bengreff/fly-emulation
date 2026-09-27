# Transcriptome sources matched to connectome types (session 8 survey)

Date: 2026-09-26. Purpose: find per-type receptor expression to fill synapse-sign blanks (F-RCPT-1) beyond Davis, Nern et al. 2020 (GSE116969), which the project already uses.

Labels: **[V]** means checked directly in this survey (file listing, HTTP range/HEAD, or opened file). **[U]** means unverified (taken from a paper summary or search result). Nothing was downloaded above 5 MB. Only the two small Turner-Evans xlsx files and one 2 MB metadata table were fetched (copies are in the session scratchpad, not in the repo).

## Ranking (connectome-matched central-brain/VNC types per unit of download and effort)

| # | Dataset | Matched types useful here | Download needed | Verdict |
|---|---|---|---|---|
| 1 | Turner-Evans et al. 2020, GSE155329 | EPG, Delta7, PEG, PEN_b (PEN2), PEN_a (PEN1), ER4d (R4d) | 1.4 MB + 2.8 MB (+56 MB scRNA) | **Take now.** Direct split-GAL4 sorting, receptor genes present [V] |
| 2 | Epiney et al. 2025 eLife, GSE294658 + GitHub | ~27 CX labels (EPG, PEN, PEG, PFN, PFR, hΔA/D/E/H/I/K, vΔC/E, FR1, PFGs, 12 FB tangential types) | 1.4 KB annotation table; expression requires the 9.3 GB RDS | **Take the annotation now; the 9.3 GB RDS goes on backhouse** |
| 3 | Cachero et al. 2026 Nature (VNC developmental atlas), GSE304221 | Hemilineage × neuromere for ~95% of secondary VNC neurons (122 groups, mean ~26 MANC types per group) plus motor neurons | Metadata 16 MB (GitHub); expression 21 GB RDS or Zenodo loom (size [U]) | Good for VNC at hemilineage resolution. **Pupal (≤48 h APF) only, so receptor levels may be immature** |
| 4 | Crocker et al. 2016, GSE74989 | MB-V2 and MB-V3 MBONs, αβ and γ KCs, DAL; two other lines (R27…, G386) | 1.4–4.7 MB | Cheap. The MBON-to-hemibrain name mapping needs checking |
| 5 | Allen et al. 2020 eLife adult VNC, GSE141807 | Hemilineage-level clusters and motor-neuron clusters (adult) | 70 MB DGE | Adult counterpart of #3. The cluster-label file location is [U] |
| 6 | Özel et al. 2021 Nature, GSE142787 | ~100+ optic-lobe types, including the adult stage [U count] | 139 MB average-expression xlsx | Optic lobe only; overlaps Davis 2020 |
| 7 | Kurmangaliyev et al. 2020 PNAS, GSE156455 | ~60 named optic-lobe types (Mi1, T4/T5, Tm, Dm, LC, LPLC…) [V] | 1.0 GB matrix + 2 MB metadata | Pupal (24–96 h APF). Low priority |
| 8 | Allen et al. 2025 Cell Genomics (Goodwin lab) | 4,167 subtypes, but connectome-type labels are sparse (a few CX types, e.g. EPG, PEG, hΔK, PFNa, FB2E, ExR1) | GEO 476 MB of raw counts only [V]. Annotated objects appear to be web-app only (flycns.com) [U] | Watch. The annotation is not yet downloadable in a usable form |
| 9 | Fly Cell Atlas head (Li et al. 2022) | Coarse neuron classes (KCs, some optic-lobe types) [U] | 2.64 GB h5ad [V] | Low value for CX, DN or VNC |

## 1. Turner-Evans et al. 2020, *Neuron* 108:145, "The neuroanatomical ultrastructure and function of a biological ring attractor" — GEO GSE155329 [V]

- Files (FTP `https://ftp.ncbi.nlm.nih.gov/geo/series/GSE155nnn/GSE155329/suppl/`):
  - `GSE155329_Turner-Evans_BulkRNASeq_updated.xlsx`: 1.4 MB. Bulk RNA-seq, 2 replicates per line: Delta7 (SS02238, SS30295), EPG (SS00096, SS00131), PEG (SS02191), PEN2 (SS02232), and whole brain.
  - `GSE155329_Turner-Evans_LowCellRNASeq_updated.xlsx`: 2.8 MB. Low-cell (~35–40 cells) RNA-seq: SS02232 = PEN2 (14 replicates), SS00238 = R4d (7 replicates; line identity from the GEO design text), central-brain controls.
  - `GSE155329_Turner-Evans_scRNASeq_updated.xlsx`: 56 MB. Plate-based single cells for PEN1 and PEN2.
  - `GSE155329_Turner-Evans_DGEanalysis_updated.xlsx`: 9.0 MB.
- Type match: FACS or manual sorting of split-GAL4 lines characterised against the hemibrain in the same paper, so confidence is high. In hemibrain/male-CNS names, PEN1 = PEN_a and PEN2 = PEN_b. R4d is the older name for ER4d.
- Receptor values read from the files [V]. Units are as given in the sheets. The bulk units are unlabelled (normalised expression); the low-cell values are counts.
  - **EPG (bulk, 4 samples):** GluClα 190–333, Rdl 358–451, GABA-B-R1 9–25, GABA-B-R2 9–16, GABA-B-R3 16–29, nAChRα7 12–22, ChAT 39–51, VGlut ~0. Whole brain for comparison: GluClα ~200, Rdl ~240.
  - **Delta7 (bulk, 4 samples):** VGlut 311–402, GluClα 64–110, nAChRα7 37–53, Rdl 40–93, GluRIA ≤11.
  - **PEG (bulk, 2 samples):** GABA-B-R3 46–93 (the highest of these types), GluClα 47–79.
  - **PEN2 (bulk, 2 samples):** GluClα 120–200, nAChRα6 92–134. Replicate 1 shows Gad1 211, so contamination is possible and the replicate should be flagged.
  - **PEN2 (low-cell, 14 samples):** GluClα 135–379 (central brain 71–169), Rdl 1.4–2.8k (CB ~1.1k), nAChRα6 0.7–2.1k, ChAT ~1k, VGlut 0.
  - **R4d / ER4d (low-cell, 7 samples):** Gad1 ~600–740, Rdl ~15k, nAChRα7 0.5–1.1k, nAChRα6 3.7–6.1k, GABA-B-R1 34–122, GABA-B-R2 44–105, GluClα 0–47 (low), GluRIA/B ~0.
- Quirk: the bulk sheet header lists `SS00238_r2` under D7, which is probably a typo for SS02238. The same line code appears as R4d in the low-cell sheet. Verify before use.
- Licence: GEO public data (NCBI places no use restrictions). Cite the paper.

## 2. Epiney, Morales Chaya, Dillon, Lai & Doe 2025, *eLife* 14:RP105896 (type 2 neuroblast snRNA-seq)

- Expression: GEO GSE294658 [V]: `GSE294658_T2.atlas.neurons.rds` 9.3 GB, `GSE294658_T2.atlas.rds` 12 GB, `GSE294658_T2.atlas.glia.rds` 2.8 GB. Seurat objects; no per-cluster average table was found.
- Annotation [V]: `https://github.com/dgepiney/2023_Doe_Drosophila_Central_Brain_RNAseq/tree/HEAD/Data/sup tables`
  - `Supplemental Table 12 T2_cell_identity_by_cluster.csv` (1.4 KB): cluster → label.
    - Labelled clusters: EPG 75,95; PEG 102; PEN 46,66,130; PFN 38,123; PFR 105; hΔA 82,139; hΔD 42,189; hΔE 52; hΔH 64,126,197; hΔI 128; hΔK 100; vΔC 43; vΔE 86; FR1 72; PFGs 120; lbSps-P 40.
    - FB tangentials: FB1C 170, FB2A 149, FB2B 124, FB2I_ab 106, FB3C 80,113,117, FB4K 135, FB4L 160, FB6A/FB8G 162, FB6H 168, FB7B 127,129, FB8B 89,174.
    - Non-type labels: DOPA, SER, OCTA, MBN, dsx.
  - `Supplemental Table 11 …columnar…csv`: split line, neuropeptide, TF evidence and predicted cluster for 16 types.
  - `Supplemental Table 6 T2_neuron_markers_by_cluster.csv` (17.7 MB): FindAllMarkers output. It holds pct.1/pct.2 for enriched genes only, so it is not a full receptor table.
- Matching method: correlation to bulk RNA-seq (Turner-Evans 2020 and others) for EPG, PEG, hΔK, FB6A and FB7A; split-GAL4 enhancer genes; TF (Toy/Runt) plus Gal4/LexA validation for PFN, PEN and PFR; neuropeptide profiles (weakest evidence). PEN and PFN are not split into connectome subtypes (PEN_a/b; PFNa/d/m/p/v).
- No ER ring neurons (type I lineage) and no receptor analysis in the paper [V via paper text].
- Licence: CC BY 4.0.

## 3. Cachero, Mitletton, … Lacin, Jefferis & Donà 2026, *Nature* 657:202 (bioRxiv 2025.07.16.664682), VNC developmental atlas

- GEO GSE304221 [V]: `GSE304221_VNC_neurons.rds` 21 GB, `_all.rds` 25 GB, `_glia.rds` 3.0 GB, `_RAW.tar` 14 GB, README 13 KB.
- Zenodo looms: 17183028 (all), 17184089 (neurons), 17185432 (glia, 558 MB [V]). Sizes of the first two are [U] because Zenodo rate-limited the check.
- Metadata [V]: `https://github.com/FlyNeuroAtlas/DevSeqVNC/tree/main/metadata`. `VNC_2ary_neurons_metadata.rds` is 16 MB. Columns include `hemilineage`, `soma_neuromere`, `soma_neuromere_MCNS`, `adultHemi` (labels transferred from Allen 2020), `neurotransmitter`, and clusters cut to the number of expected connectome types per hemilineage × segment (`allDEGs_1`, …).
- Matching: hemilineage sizes vs MANC, R² 0.9 [U, from summary]. Split-GAL4 validation. fru+ clones matched to MANC groups. The atlas does **not** assign individual MANC type names to clusters [V from metadata description].
- Stage: 6–48 h after puparium formation, so receptor expression may not reflect the adult.
- Browser: `https://flyem.mrc-lmb.cam.ac.uk/VNCatlas`; SCope "HundredDrills".
- Licence: Zenodo CC BY 4.0 (glia record [V]); paper open access.

## 4. Crocker, Guan, Murphy & Murthy 2016, *Cell Rep* 17:1945 — GEO GSE74989 [V]

- Files: `GSE74989_HTseqCountscompiledData.txt.gz` 1.4 MB, `GSE74989_NormalizedCPMcorrectedData.txt.gz` 4.7 MB, `GSE74989_TargetInformationSheet.txt.gz` 1 KB.
- Samples: patch-pipette harvests of about 10 neurons per sample, from lines DAL, MB-V2 (R71D08), MB-V3, αβ KC (c739), γ KC (NP1131), R27…, and G386, in trained and control flies.
- MB-V2 corresponds roughly to MBON-α2sc/α'3 and MB-V3 to MBON-α3 (MBON14). This mapping is [U] and needs a check against Aso 2014 names.
- Adds MBON types absent from our Davis crosswalk, cheaply.

## 5. Allen, Neville, Birtles, … Goodwin 2020, *eLife* 9:e54074 — adult VNC atlas, GEO GSE141807

- `GSE141807_RAW.tar` 70.6 MB [V]: 4 DGE txt files, 8–23 MB each.
- About 100 clusters with hemilineage assignments by marker and transmitter logic, plus motor-neuron clusters. The annotation source file (eLife supplementary file or SCope loom) is [U].
- MANC types such as IN21A_xxx are hemilineage-prefixed. A hemilineage-level receptor call can therefore be joined to MANC type names directly, at coarse resolution.

## 6–9. Lower priority

- **Özel et al. 2021** (GSE142787) [V sizes]: `GSE142787_Log_normalized_average_expression.xlsx` 139 MB (per cluster, all stages including adult), `_Cluster_markers.xlsx` 34 MB, `_Adult.rds.gz` 3.5 GB. Optic lobe only.
- **Kurmangaliyev et al. 2020** (GSE156455) [V]: `metadata_main.tsv.gz` 2 MB has a `type` column (187 labels, ~60 named, e.g. Mi1, Mi4, Mi9, Tm1–Tm29, T4.T5, Dm1–12, LC4/6/10a/b, LPLC1/2, L1–L5); `matrix_main.mtx.gz` 1.0 GB. Pupal only.
- **Allen et al. 2025 Cell Genomics** "A high-resolution atlas of the brain predicts lineage and birth order underlying neuronal identity" (GSE296540).
  - The GEO record holds only 4 new samples as mtx, 476 MB total [V].
  - The code (GitHub aaron-allen/Dmel-adult-central-brain-atlas; Zenodo 17513514, 1.1 MB) integrates 17 published datasets and correlates type II clusters with Turner-Evans and Davis bulk data [V].
  - The paper says "much of the central brain remains unannotated" [U]. Annotated objects are visible on flycns.com; whether they can be downloaded is [U].
- **Fly Cell Atlas head** (Li et al. 2022, Science): `s_fca_biohub_head_10x.h5ad` = 2,644,193,366 bytes [V] via `https://cloud.flycellatlas.org/index.php/s/LAEybPc2HZnpzKs/download`. No login needed. The annotations are consensus broad classes [U]; few connectome-level types.
- **ConnectionMiner** (PMC11908227): leg motor system scRNA matched jointly with connectivity for 29 leg MN types. Data in GSE290807 (public status [U]). No receptor table.

## Needs login / access issues

- No candidate needs a login. The flycns.com web apps are browse-only (download options [U]).
- Zenodo API rate-limited this survey (HTTP 403), so retry later.

## Published per-type receptor measurements for CX neurons (glutamate receptor class, GABA-B, nAChR)

- **Turner-Evans 2020 (GSE155329)**: EPG, Delta7, PEG, PEN_a, PEN_b and ER4d, with values above [V]. Main points:
  - PEN_b expresses GluClα, so Delta7→PEN glutamate is inhibitory-compatible.
  - EPG expresses GluClα and GABA-B-R1/2/3.
  - ER4d has low GluClα and expresses GABA-B-R1/R2 and nAChRα6/α7.
- **Davis, Nern et al. 2020 (GSE116969)**: EPG and Delta7 (already in the project, F-RCPT-1).
- **Aso et al. 2019 eLife** (nitric oxide cotransmitter): all 10 DAN types profiled express GluClα and Nmdar2 highly. Nmdar1 and other iGluRs are limited and cell-type-specific [U; quoted from search summary; likely the same TAPIN data as Davis 2020].
- **Epiney 2025**: no receptor analysis [V].
- **Protein-level:** Sanfilippo et al. 2024 Neuron tagged endogenous receptor subunits (nAChR, GluClα, Rdl, GABA-B) and mapped them to connectome synapses, mainly in the optic lobe (T4/T5) [U for any CX coverage]. Kondo et al. 2020 and Deng et al. 2019 "chemoconnectomics" knock-in lines give neuropil-level (EB/FB) receptor patterns, not per-type tables [U].
- No per-type receptor data were found for ExR, PFN subtypes, hΔ or the other ER subtypes except through Epiney's clusters, which require the 9.3 GB object.

## Suggested next step

1. Ingest the two Turner-Evans xlsx files (4.2 MB) as a second receptor source. Crosswalk: EPG, Delta7, PEG, PEN_a, PEN_b, ER4d. Check them against Davis for EPG/Delta7 as a replication test.
2. On backhouse, download `GSE294658_T2.atlas.neurons.rds` (9.3 GB). Pseudobulk the receptor genes per Supplemental Table 12 cluster, keeping the confidence tier of each cluster's match method.
3. For the VNC, pseudobulk the Allen 2020 adult data (70 MB) by hemilineage. Use Cachero's `hemilineage`/MANC-matched metadata only as a cross-check, because that atlas is pupal.
