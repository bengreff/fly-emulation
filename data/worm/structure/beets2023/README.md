# Beets et al. 2023, peptide-GPCR potencies (measured)

Beets I, Zels S, Vandewyer E, et al. "System-wide mapping of peptide-GPCR interactions in C. elegans." Cell Reports
42:113058 (2023). Free preprint: bioRxiv 2022.10.30.514428 (v1, 1 Nov 2022). Fetched 6 Nov 2026 (wbrain, night of
6 Nov). Raw files are kept unchanged.

| File | Source | Content |
|---|---|---|
| biorxiv_media-6_TableS6_EC50.xlsx | https://www.biorxiv.org/content/biorxiv/early/2022/11/01/2022.10.30.514428/DC6/embed/media-6.xlsx | Table S6: every active peptide-GPCR pair, log EC50 (M) with 95% CI, from the aequorin Ca reporter in CHO cells |
| biorxiv_media-1_TableS1_GPCRs.xlsx | .../DC1/embed/media-1.xlsx | Table S1: the screened GPCRs, ID to gene name |
| biorxiv_media-9_families.xlsx | .../DC9/embed/media-9.xlsx | peptide families |
| ripoll_sanchez2023_TableS5.xlsx | https://raw.githubusercontent.com/LidiaRipollSanchez/Neuropeptide-Connectome/main/Supplementary%20Tables/Table%20S5.%20NPP-GPCR%20pairs%20information.xlsx | Ripoll-Sanchez et al. 2023 Neuron Table S5: 92 gene-level pairs with EC50 (M), GPCR class and family (cross-check) |
| peptide_gpcr_ec50.csv | derived from media-6 and media-1 | one row per peptide x GPCR isoform, 459 rows |

peptide_gpcr_ec50.csv columns: gpcr_id, gpcr_name, peptide, log_ec50_M, ci95_log_M ("a to b"), ec50_M (Table S6's
own columns, renamed), gpcr_gene (GPCR ID mapped to the gene name through Table S1), peptide_gene (the peptide name
with any "(...)" suffix, a leading "pyro" and the trailing "-N" index removed, lower case). 147 precursor-gene x
receptor-gene pairs; EC50 from 1.3e-13 to 2.2e-5 M.

Used by src/wormemu/mech/neuromod.py (rows 9, 10, 28, `beets_pairs`): each gene pair's template EC50 is its most
potent peptide's EC50 (a precursor releases all its peptides); the range runs from the lowest 95% CI bound to the
larger of the weakest peptide's EC50 and the most potent one's upper CI bound.

Version note: the preprint table has 459 pairs; the published Cell Reports paper reports 461. The published table
(paywalled) would add the two missing pairs.
