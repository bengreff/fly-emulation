"""Glutamate-receptor calls per VNC hemilineage from Allen et al. 2020 (session 12).

Data: Allen, Neville et al. 2020 eLife 9:e54074, adult VNC scRNA-seq atlas, GEO
GSE141807 (4 samples: female/male x 2 replicates, Drop-seq-style digital gene
expression (DGE) matrices, genes x top-30000-barcodes, NOT pre-filtered to real
cells); eLife fig1-data1 (per-cluster marker genes, Seurat FindAllMarkers output,
120 clusters 0-119) and fig1-data2 (per-cluster cell number, neurotransmitter and
"Predicted hemilineage" annotation, 111 neuronal + 12 non-neuronal cluster rows).

GEO/eLife deposited marker-gene tables and a cluster-level hemilineage call, but
NOT the authors' per-cell cluster labels (checked: GEO GSE141807 suppl only has
the 4 raw DGE files; eLife has no additional fig-data table with a barcode; the
authors' analysis code, github aaron-allen/VNC_scRNAseq, is Seurat v2.3.4 R
scripts with no data checkpoint). Reproducing their exact CCA-integrated,
resolution-12 Seurat clustering was judged too heavy/fragile to redo here
(old Seurat version, stochastic CCA, no seed given). Instead this script
reclusters by a lighter, declared proxy:

  1. QC cells the way R_preprocessing.R does (nGene>=200 implicit in the DGE,
     1200<=nUMI<=10000, mitochondrial-read fraction <=0.15) -> the "QC-passed"
     population (reported against the paper's 26,768 "high-quality cells"; not
     expected to match exactly: no doublet removal, no CCA batch integration,
     different Seurat version).
  2. For each of the 120 published clusters, takes its top 12 positive markers
     (fig1-data1, ranked by avg_logFC). Scores every QC-passed cell against each
     cluster's marker set (mean CP10K-normalised, log1p expression over the
     markers present in our extracted gene set), z-scores each cluster's score
     across cells, and assigns each cell to its highest-z cluster
     (nearest-marker-centroid label transfer, not the authors' own labels).
  3. Validates the transfer against the published per-cluster cell counts
     (Spearman correlation, printed) -- a sanity check, not proof the transfer
     recovers the authors' exact partition.

Because of step 2-3, every number derived from cluster/hemilineage assignment in
this script is basis "inferred" (re-derived by us from the authors' marker
tables), not "measured" -- only the raw UMI counts per cell are measured.

To keep the ~750-850 MB decompressed DGE text out of pandas, a one-pass awk
script (qc_and_extract.awk) computes per-cell QC stats and extracts the ~550
wanted gene rows (receptor genes from infer_receptors.GENES, plus the top-12
marker genes of all 120 clusters) to data/raw/allen2020_vnc/cache/; this script
reads only those cached, already-small tables.

Threshold: a gene is called ON for a hemilineage if expressed (count>0) in
>=30% of its assigned QC-passed cells (also reports 20%/50% sensitivity).
Glutamate-sign rule (as scripts/infer_receptors.py / receptors_ozel2021.py):
  GluClalpha ON, GluRIA and GluRIB OFF  -> -1 (GluCl-dominated, inhibitory)
  GluClalpha OFF, GluRIA or GluRIB ON   -> +1 (iGluR-only, candidate excitatory)
  else                                   -> 0 (mixed/unclear)

Hemilineage crosswalk: Allen's "Predicted hemilineage" labels (e.g. "0A", "5B/6B")
-> male-cns trumanHl (e.g. "00A", "05B", "06B"; zero-padded, Truman nomenclature).
Single-token labels zero-pad to match trumanHl exactly (basis derived). Slash-
joined ambiguous labels ("13A/19A") first try the dot-joined trumanHl combo
name directly (e.g. "20A/22A" -> trumanHl "20A.22A", both sources agree on that
specific ambiguity -> derived); failing that, each token is matched separately
against trumanHl base names or, if absent, against trumanHl combo labels that
contain it as a "."-separated component (e.g. "24B" -> "24B.25B") -- both cases
basis inferred (the Allen or male-cns ambiguity is not actually resolved, just
carried through). trumanHl "_put*" variants of a matched base name are counted
into n_male_cns_cells_in_hl (same hemilineage, tentative call) but are not
separate crosswalk targets.

Outputs: data/derived/receptor_calls_allen2020_vnc.csv (hemilineage, gene,
frac_expressed, call, sensitivity calls) and
data/derived/glutamate_sign_by_hemilineage_allen2020.csv (allen_hl, trumanHl,
sign, n_cells, n_male_cns_cells_in_hl, basis, justification).

    uv run --with openpyxl python scripts/receptors_allen2020_vnc.py
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[1]
RAW = REPO / "data" / "raw" / "allen2020_vnc"
CACHE = RAW / "cache"
OUT = REPO / "data" / "derived"
sys.path.insert(0, str(REPO / "scripts"))
from infer_receptors import GENES  # noqa: E402

SAMPLES = ["GSM4213596_female_rep1", "GSM4213597_female_rep2",
           "GSM4213598_male_rep1", "GSM4213599_male_rep2"]
NGENE_MIN, NUMI_MIN, NUMI_MAX, MITO_MAX = 200, 1200, 10000, 0.15  # R_preprocessing.R cutoffs
TOPK = 12
THRESH = 0.30
SENS = (0.20, 0.30, 0.50)
SRC = ("Allen, Neville et al. 2020 eLife 9:e54074, adult VNC scRNA-seq atlas, GEO GSE141807 "
       "(GSM4213596-99 DGE matrices); eLife fig1-data1 (cluster markers) and fig1-data2 "
       "(cluster hemilineage annotation); marker-based cluster reassignment by this script "
       "(authors' per-cell cluster labels were not deposited)")


def marker_table() -> pd.DataFrame:
    m = pd.read_excel(RAW / "elife-54074-fig1-data1-v1.xlsx", sheet_name="All Cluster Markers")
    m = m.dropna(subset=["cluster"])
    m["cluster"] = m.cluster.astype(int)
    return m.sort_values(["cluster", "avg_logFC"], ascending=[True, False]).groupby("cluster").head(TOPK)


def hemilineage_table() -> pd.DataFrame:
    h = pd.read_excel(RAW / "elife-54074-fig1-data2-v1.xlsx", sheet_name="Neuronal Clusters")
    h = h.iloc[:, :8]
    h.columns = ["cluster", "n_cells_published", "n_markers", "n_unique_markers", "nt",
                 "allen_hl", "peptides", "hox"]
    h = h.dropna(subset=["allen_hl"]).astype({"cluster": int})
    return h[["cluster", "n_cells_published", "nt", "allen_hl"]]


def published_cluster_sizes() -> pd.Series:
    """All 120 published cluster cell counts (neuronal + non-neuronal sheets), for validation."""
    h = pd.read_excel(RAW / "elife-54074-fig1-data2-v1.xlsx", sheet_name="Neuronal Clusters").iloc[:, :2]
    h.columns = ["cluster", "n_cells_published"]
    nn = pd.read_excel(RAW / "elife-54074-fig1-data2-v1.xlsx", sheet_name="Non-Neuronal Clusters").iloc[:, :2]
    nn.columns = ["cluster", "n_cells_published"]
    return pd.concat([h, nn]).set_index("cluster").n_cells_published


def load_qc() -> pd.DataFrame:
    qc = pd.concat([pd.read_csv(CACHE / f"{s}_qc.tsv", sep="\t") for s in SAMPLES], ignore_index=True)
    qc["mito_frac"] = qc.mito_umi / qc.total_umi.clip(lower=1)
    qc["cell"] = qc["sample"] + "|" + qc.barcode
    pass_mask = (qc.n_genes >= NGENE_MIN) & qc.total_umi.between(NUMI_MIN, NUMI_MAX) & (qc.mito_frac <= MITO_MAX)
    print(f"QC: {len(qc):,} raw barcodes across {qc['sample'].nunique()} samples; "
          f"{pass_mask.sum():,} pass nGene>={NGENE_MIN}, {NUMI_MIN}<=nUMI<={NUMI_MAX}, "
          f"mito<={MITO_MAX} (paper reports 26,768 high-quality cells)")
    return qc[pass_mask].set_index("cell")


def load_marker_matrix(cells: pd.Index) -> pd.DataFrame:
    """cells x genes raw-count matrix, QC-passed cells only, union of genes across samples."""
    parts = []
    for s in SAMPLES:
        g = pd.read_csv(CACHE / f"{s}_markers.tsv", sep="\t", index_col=0)
        g.columns = s + "|" + g.columns
        keep = g.columns.intersection(cells)
        parts.append(g[keep].T)
    mat = pd.concat(parts, axis=0)
    return mat.reindex(index=cells, fill_value=np.nan)  # nan = cell absent from a sample's markers file


def assign_clusters(mat: pd.DataFrame, qc: pd.DataFrame, markers: pd.DataFrame) -> pd.Series:
    cp10k = mat.div(qc.total_umi, axis=0) * 1e4
    lognorm = np.log1p(cp10k)
    scores = {}
    for cl, g in markers.groupby("cluster"):
        genes = [x for x in g.gene if x in lognorm.columns]
        if not genes:
            continue
        scores[cl] = lognorm[genes].mean(axis=1)
    S = pd.DataFrame(scores)
    Sz = (S - S.mean()) / S.std(ddof=0).replace(0, np.nan)
    assigned = Sz.idxmax(axis=1)
    print(f"cluster assignment: {len(S.columns)} of 120 published clusters had >=1 marker "
          f"in the extracted gene set; {assigned.notna().sum():,} cells assigned")
    return assigned


def crosswalk_hl(allen_hl: str, truman_values: set[str]) -> list[tuple[str, str, str]]:
    """allen_hl -> [(trumanHl, basis, note), ...]. Declared rule, see module docstring."""
    def pad(tok: str) -> str:
        m = re.match(r"^(\d+)([A-Za-z].*)$", tok)
        return f"{int(m.group(1)):02d}{m.group(2)}" if m else tok

    tokens = allen_hl.split("/")
    padded = [pad(t) for t in tokens]
    if len(padded) > 1:
        combo = ".".join(padded)
        if combo in truman_values:
            return [(combo, "derived", f"Allen '{allen_hl}' matches trumanHl combo '{combo}' directly")]
    out = []
    for tok, allen_tok in zip(padded, tokens):
        basis = "derived" if len(tokens) == 1 else "inferred"
        if tok in truman_values:
            note = "exact trumanHl base name match" if basis == "derived" else \
                f"Allen ambiguous label '{allen_hl}' resolved by token '{allen_tok}' -> trumanHl '{tok}'"
            out.append((tok, basis, note))
            continue
        combos = [v for v in truman_values if "." in v and tok in v.split(".")]
        for c in combos:
            out.append((c, "inferred", f"token '{tok}' (from Allen '{allen_hl}') is a component of "
                        f"trumanHl combo '{c}'; that combo is not separately resolved"))
        if not combos:
            print(f"  crosswalk: no trumanHl target for Allen hemilineage '{allen_hl}' token '{tok}'")
    return out


def main() -> None:
    markers = marker_table()
    hl = hemilineage_table()
    qc = load_qc()
    mat = load_marker_matrix(qc.index)
    assigned = assign_clusters(mat, qc, markers)

    pub = published_cluster_sizes()
    j = pd.DataFrame({"assigned": assigned.value_counts(), "published": pub}).dropna()
    print(f"validation: marker-based reassignment vs published per-cluster cell counts, "
          f"{len(j)} of 120 clusters; Pearson r={j.assigned.corr(j.published):.3f}, "
          f"Spearman r={j.assigned.corr(j.published, method='spearman'):.3f} "
          "(a proxy for the authors' own clustering, not a reproduction of it)")

    cell_hl = assigned.map(hl.set_index("cluster").allen_hl)
    cell_hl = cell_hl.dropna()
    print(f"{cell_hl.nunique()} distinct Allen hemilineage labels; {len(cell_hl):,} cells assigned to "
          f"one of the {hl.cluster.nunique()} hemilineage-annotated clusters (of 120 published clusters)")

    genes = [g for g in GENES if g in mat.columns]
    missing = sorted(set(GENES) - set(genes))
    cp10k = mat.loc[cell_hl.index, genes].div(qc.loc[cell_hl.index].total_umi, axis=0) * 1e4
    expr = (mat.loc[cell_hl.index, genes] > 0)

    rows = []
    for hlname, idx in cell_hl.groupby(cell_hl).groups.items():
        n = len(idx)
        for g in genes:
            valid = mat.loc[idx, g].notna()
            n_valid = int(valid.sum())
            if n_valid == 0:
                continue
            frac = float(expr.loc[idx, g][valid].mean())
            mean_cp10k = float(cp10k.loc[idx, g][valid].mean())
            row = dict(allen_hl=hlname, gene=g, n_cells=n, n_cells_with_gene_data=n_valid,
                       frac_expressed=round(frac, 4), mean_cp10k=round(mean_cp10k, 3),
                       role=GENES[g])
            for s in SENS:
                row[f"call_{int(s*100)}"] = int(frac >= s)
            rows.append(row)
    calls = pd.DataFrame(rows)
    calls["call"] = calls[f"call_{int(THRESH*100)}"]
    calls.to_csv(OUT / "receptor_calls_allen2020_vnc.csv", index=False)
    print(f"receptor calls: {calls.allen_hl.nunique()} Allen hemilineages x {len(genes)} genes "
          f"(missing from extracted set: {missing})")
    for s in SENS:
        c = calls[f"call_{int(s*100)}"]
        print(f"  threshold {s:.0%}: ON calls {c.sum()} / {len(c)}")

    # --- glutamate sign per hemilineage ------------------------------------------------
    w = calls.pivot_table(index="allen_hl", columns="gene", values="call")
    sign_rows = []
    for a in w.index:
        gc, ia, ib = w.at[a, "GluClalpha"], w.get("GluRIA", pd.Series()).get(a), w.get("GluRIB", pd.Series()).get(a)
        if gc == 1 and ia == 0 and ib == 0:
            sign, status = -1, "GluCl-dominated, glutamatergic input inhibitory"
        elif gc == 0 and (ia == 1 or ib == 1):
            sign, status = 1, "iGluR-only (candidate), glutamatergic input excitatory"
        else:
            sign, status = 0, "mixed/unclear"
        sign_rows.append((a, sign, status))
    sign_df = pd.DataFrame(sign_rows, columns=["allen_hl", "sign", "status"])
    print("glutamate sign at 30%:", sign_df.status.value_counts().to_dict())

    hcache = pd.read_parquet(REPO / "data/cache/male_cns_hemilineage.parquet", columns=["bodyId", "trumanHl"])
    truman_counts = hcache.trumanHl.value_counts()
    truman_values = set(truman_counts.index.dropna())

    out_rows = []
    for a, sign, status in sign_rows:
        n_cells = int(cell_hl.value_counts().get(a, 0))
        targets = crosswalk_hl(a, truman_values)
        if not targets:
            out_rows.append(dict(allen_hl=a, trumanHl=None, sign=sign, n_cells=n_cells,
                                  n_male_cns_cells_in_hl=0, basis="inferred",
                                  justification=f"{status}; no trumanHl crosswalk target found"))
            continue
        for t, basis, note in targets:
            n_male = int(truman_counts.get(t, 0)) + int(
                truman_counts[[k for k in truman_counts.index if k.startswith(t + "_put")]].sum())
            out_rows.append(dict(allen_hl=a, trumanHl=t, sign=sign, n_cells=n_cells,
                                  n_male_cns_cells_in_hl=n_male, basis="inferred",
                                  justification=f"{status} (frac_expressed >= {THRESH:.0%} rule); {note}; "
                                  f"{SRC}; mRNA, not synaptic localisation"))
    out_df = pd.DataFrame(out_rows)
    out_df.to_csv(OUT / "glutamate_sign_by_hemilineage_allen2020.csv", index=False)
    print(f"glutamate sign rows: {len(out_df)} (allen_hl x trumanHl target); "
          f"{out_df.trumanHl.notna().sum()} with a trumanHl crosswalk target; "
          f"sign counts {out_df.sign.value_counts().to_dict()}")


if __name__ == "__main__":
    main()
