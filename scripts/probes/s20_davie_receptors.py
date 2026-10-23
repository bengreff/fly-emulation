"""s20 N19/N20: receptor and marker expression per Davie et al. 2018 (Cell 174:982) adult-brain cluster.

Input: GEO GSE107451 57k matrix (MEX inside the tar) and metadata (Seurat clusters res.*, `annotation` code).
Output per grouping (`annotation`, `res.2`): cluster x gene fraction of cells with >= 1 UMI and mean log1p
CP10k, plus n_cells and age mix. No cell-type names are assigned here: the PN / KC / monoamine clusters are
called from the marker columns afterwards (derived, written down with the calls).

    python scripts/probes/s20_davie_receptors.py data/raw/scrna/davie2018_brain runs/s20/davie
"""
import sys
import tarfile
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import io, sparse

RECEPTORS = ["Dop1R1", "Dop1R2", "Dop2R", "DopEcR", "Oamb", "Octbeta1R", "Octbeta2R", "Octbeta3R", "CG18208",
             "TyrR", "TyrRII", "5-HT1A", "5-HT1B", "5-HT2A", "5-HT2B", "5-HT7",
             "AkhR", "InR", "NPFR", "sNPF-R", "Dh44-R1", "Dh44-R2", "CrzR", "AstA-R1", "AstA-R2", "Lkr", "CCHa1-R",
             "CCHa2-R", "Dh31-R", "Pdfr", "SIFaR", "Proc-R", "TkR86C", "TkR99D", "MsR1", "MsR2", "CCAP-R", "ETHR",
             "Lgr3", "Lgr4", "FMRFaR", "PK1-R", "PK2-R1", "rk"]
MARKERS = ["elav", "repo", "acj6", "vvl", "ct", "ey", "Pka-C1", "prt", "ChAT", "VAChT", "Gad1", "VGlut", "ple",
           "Ddc", "DAT", "SerT", "Trh", "Tbh", "Vmat", "Tdc2", "sNPF", "Lim1", "tim", "per", "Clk", "Pdf"]


def main() -> None:
    src, out = Path(sys.argv[1]), Path(sys.argv[2])
    out.mkdir(parents=True, exist_ok=True)
    work = out / "mex"
    if not (work / "matrix.mtx").exists():
        work.mkdir(exist_ok=True)
        with tarfile.open(src / "GSE107451_57k_DGEM_MEX.mtx.tsv.tar.gz") as t:
            t.extractall(work)
    genes = pd.read_csv(work / "genes.tsv", sep="\t", header=None, names=["fbgn", "symbol"])
    bc = pd.read_csv(work / "barcodes.tsv", sep="\t", header=None)[0].to_numpy()
    meta = pd.read_csv(src / "GSE107451_57k_Metadata.tsv.gz", sep="\t", index_col=0)
    meta = meta.loc[:, ~meta.columns.duplicated()]
    m = io.mmread(work / "matrix.mtx").tocsr()
    if m.shape[0] == len(genes):
        m = m.T.tocsr()                                   # cells x genes
    assert m.shape == (len(bc), len(genes)), (m.shape, len(bc), len(genes))
    meta = meta.reindex(bc)
    print("cells", len(bc), "with metadata", int(meta["annotation"].notna().sum()), flush=True)
    lib = np.asarray(m.sum(axis=1)).ravel()
    want = [g for g in RECEPTORS + MARKERS if g in set(genes.symbol)]
    missing = [g for g in RECEPTORS + MARKERS if g not in set(genes.symbol)]
    col = {g: int(np.flatnonzero(genes.symbol.to_numpy() == g)[0]) for g in want}
    sub = m[:, [col[g] for g in want]].toarray().astype(np.float64)
    expr = sub > 0
    lnorm = np.log1p(sub / lib[:, None] * 1e4)
    for grouping in ("annotation", "res.2"):
        g = meta[grouping].to_numpy()
        rows = []
        for c in pd.unique(g[pd.notna(g)]):
            k = g == c
            r = {"cluster": c, "n_cells": int(k.sum()), "median_age_d": float(np.median(meta["Age"].to_numpy()[k])),
                 "frac_male": float((meta["sex"].to_numpy()[k] == "male").mean())}
            for j, gene in enumerate(want):
                r[f"frac:{gene}"] = round(float(expr[k, j].mean()), 4)
                r[f"mean:{gene}"] = round(float(lnorm[k, j].mean()), 4)
            rows.append(r)
        df = pd.DataFrame(rows).sort_values("cluster")
        df.to_csv(out / f"clusters_{grouping}.csv", index=False)
        print(grouping, len(df), "clusters", flush=True)
    (out / "README.txt").write_text(
        f"Davie 2018 GSE107451 57k; genes found {len(want)}, missing {missing}; frac = fraction of cells with "
        f">= 1 UMI; mean = mean log1p(CP10k). Groupings: annotation (metadata code), res.2 (Seurat).\n")
    print("missing", missing)


if __name__ == "__main__":
    main()
