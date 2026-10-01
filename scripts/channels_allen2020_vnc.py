"""Ion-channel / innexin gene expression per VNC hemilineage from Allen et al. 2020 (session 12).

Companion to scripts/receptors_allen2020_vnc.py, reusing that script's QC, nearest-
marker-centroid cluster label transfer and Allen-cluster -> hemilineage mapping
UNCHANGED (imported, not copied: `import receptors_allen2020_vnc as base`, calling
base.load_qc(), base.marker_table(), base.hemilineage_table(), base.load_marker_matrix()
and base.assign_clusters()). receptors_allen2020_vnc.py is not modified. Everything
about cell QC, cluster assignment and the Allen-cluster -> hemilineage join is
therefore identical to, and exactly as uncertain as, that script's (see its
docstring for the full justification: marker-based recluster is a declared proxy
for the authors' undeposited per-cell cluster labels, basis "inferred").

This script only differs in which genes it reports: instead of neurotransmitter
receptors (infer_receptors.GENES), it reports voltage-/Ca-gated ion channels and
innexins (gap-junction subunits), i.e. the excitability and electrical-coupling
side of each hemilineage rather than its ligand-gated input side.

Gene cache: the receptor script's marker cache (data/raw/allen2020_vnc/cache/
*_markers.tsv) only has the ~550 genes in infer_receptors.GENES plus each
cluster's top-12 markers (wanted_genes.txt) -- the channel/innexin genes below are
mostly NOT in it. This script extracts its own small per-sample cache,
data/raw/allen2020_vnc/cache/<sample>_channels.tsv (gene rows only, same raw
DGE source, disjoint filename from the receptor script's cache so neither run can
clobber the other), via a single awk pass per sample (gzcat | awk, invoked from
Python, no separate .awk file). This pass only selects matching gene rows (no
per-cell QC accumulation -- that is reused from the receptor script's already-
cached <sample>_qc.tsv via base.load_qc(), which is gene-set-independent) so it is
much faster than the receptor script's original extraction+QC pass.

Gene symbols were checked against the raw DGE row names directly (grep on
each GSM*_dge.txt.gz). All 29 requested genes are present in at least one of
the 4 samples' DGE matrices verbatim as given (no symbol substitution needed).
Caveat: Inx5, Inx6 and zpg are present only in GSM4213597_female_rep2 and
GSM4213599_male_rep2 (absent as gene rows in GSM4213596_female_rep1 and
GSM4213598_male_rep1 -- Drop-seq DGE matrices list only genes detected at all in
that sample, so a gene can be a legitimate row in some samples and genuinely
absent as a row in others). For those 3 genes n_cells_with_gene_data is
correspondingly lower than n_cells (cells from the other two samples only);
frac_expressed/mean_cp10k are computed over the samples where the gene row
exists, same convention as the receptor script's per-gene n_cells_with_gene_data.

Thresholds and call columns (call_20/call_30/call_50/call) are identical to the
receptor script: call = call_30 (>=30% of a hemilineage's QC-passed, cluster-
assigned cells have count>0 for that gene).

Extra reference row: allen_hl="ALL_NEURONS" aggregates frac_expressed/mean_cp10k
over every QC-passed cell assigned to ANY hemilineage-annotated (neuronal)
cluster -- i.e. the same neuronal population the per-hemilineage rows are drawn
from, pooled, not a separate recompute over unassigned or non-neuronal cells.

Output: data/derived/channel_expression_allen2020_vnc.csv, same columns as
receptor_calls_allen2020_vnc.csv (allen_hl,gene,n_cells,n_cells_with_gene_data,
frac_expressed,mean_cp10k,role,call_20,call_30,call_50,call).

    python3 ~/director/harness/slot.py run --label "fly-emulation: allen channel table" \\
        -- uv run --with openpyxl python scripts/channels_allen2020_vnc.py
"""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[1]
RAW = REPO / "data" / "raw" / "allen2020_vnc"
CACHE = RAW / "cache"
OUT = REPO / "data" / "derived"
sys.path.insert(0, str(REPO / "scripts"))
import receptors_allen2020_vnc as base  # noqa: E402

SENS = base.SENS
THRESH = base.THRESH
SRC = ("Allen, Neville et al. 2020 eLife 9:e54074, adult VNC scRNA-seq atlas, GEO GSE141807 "
       "(GSM4213596-99 DGE matrices); cluster assignment and Allen-hemilineage join reused "
       "unchanged from scripts/receptors_allen2020_vnc.py (marker-based cluster reassignment, "
       "authors' per-cell cluster labels were not deposited)")

# Ion-channel and innexin genes and their declared model role (text given by the task).
GENES: dict[str, str] = {
    "para": "Nav voltage-gated Na",
    "Sh": "Kv1 fast A-type K",
    "Shal": "Kv4 A-type K",
    "Shab": "Kv2 delayed-rectifier K",
    "Shaw": "Kv3 K",
    "KCNQ": "M-type slow K",
    "slo": "BK Ca-activated K",
    "SK": "SK Ca-activated K",
    "Ih": "HCN hyperpolarisation-activated cation",
    "cac": "Cav2 high-voltage Ca",
    "Ca-alpha1D": "Cav1 L-type Ca",
    "Ca-alpha1T": "Cav3 T-type Ca",
    "eag": "Kv10 K",
    "sei": "erg Kv11 K",
    "Irk1": "inward-rectifier K",
    "Irk2": "inward-rectifier K",
    "Irk3": "inward-rectifier K",
    "Ork1": "two-pore leak K",
    "Task6": "two-pore leak K",
    "Task7": "two-pore leak K",
    "Hk": "Kv beta subunit",
    "shakB": "innexin, gap junction",
    "ogre": "innexin, gap junction",
    "Inx2": "innexin, gap junction",
    "Inx3": "innexin, gap junction",
    "Inx5": "innexin, gap junction",
    "Inx6": "innexin, gap junction",
    "Inx7": "innexin, gap junction",
    "zpg": "innexin, gap junction",
}


def extract_channel_cache() -> None:
    """Write data/raw/allen2020_vnc/cache/<sample>_channels.tsv for each sample, if missing.

    Single gzcat|awk pass per sample selecting only header + wanted-gene rows (no
    per-cell QC accumulation: QC is reused from the receptor script's cache). The
    awk program is passed as a literal argv string, not a separate .awk file.
    """
    wanted = ",".join(sorted(GENES))
    awk_prog = (
        'BEGIN{FS=OFS="\\t"; n=split(wantedlist, arr, ","); for (i=1;i<=n;i++) want[arr[i]]=1}'
        'FNR==1{print; next}'
        '($1 in want){print}'
    )
    for s in base.SAMPLES:
        out = CACHE / f"{s}_channels.tsv"
        if out.exists():
            print(f"  cache hit: {out.name}")
            continue
        dge = RAW / f"{s}_dge.txt.gz"
        print(f"  extracting {out.name} from {dge.name} ...")
        with open(out, "wb") as f:
            p1 = subprocess.Popen(["gzcat", str(dge)], stdout=subprocess.PIPE)
            p2 = subprocess.run(["awk", "-v", f"wantedlist={wanted}", awk_prog],
                                 stdin=p1.stdout, stdout=f, check=True)
            p1.stdout.close()
            p1.wait()
            if p1.returncode:
                raise RuntimeError(f"gzcat failed for {dge}")


def load_channel_matrix(cells: pd.Index) -> pd.DataFrame:
    """cells x channel-genes raw-count matrix, QC-passed cells only. Same shape/contract
    as base.load_marker_matrix, reading the channels.tsv cache instead of markers.tsv."""
    parts = []
    for s in base.SAMPLES:
        g = pd.read_csv(CACHE / f"{s}_channels.tsv", sep="\t", index_col=0)
        g.columns = s + "|" + g.columns
        keep = g.columns.intersection(cells)
        parts.append(g[keep].T)
    mat = pd.concat(parts, axis=0)
    return mat.reindex(index=cells, fill_value=np.nan)


def main() -> None:
    extract_channel_cache()

    markers = base.marker_table()
    hl = base.hemilineage_table()
    qc = base.load_qc()
    mat_markers = base.load_marker_matrix(qc.index)
    assigned = base.assign_clusters(mat_markers, qc, markers)

    cell_hl = assigned.map(hl.set_index("cluster").allen_hl).dropna()
    print(f"{cell_hl.nunique()} distinct Allen hemilineage labels; {len(cell_hl):,} cells assigned to "
          f"one of the {hl.cluster.nunique()} hemilineage-annotated clusters (of 120 published clusters)")

    cmat = load_channel_matrix(cell_hl.index)
    genes = [g for g in GENES if g in cmat.columns]
    missing = sorted(set(GENES) - set(genes))
    cp10k = cmat.loc[cell_hl.index, genes].div(qc.loc[cell_hl.index].total_umi, axis=0) * 1e4
    expr = (cmat.loc[cell_hl.index, genes] > 0)

    def gene_row(hlname: str, idx, g: str) -> dict | None:
        valid = cmat.loc[idx, g].notna()
        n_valid = int(valid.sum())
        if n_valid == 0:
            return None
        frac = float(expr.loc[idx, g][valid].mean())
        mean_cp10k = float(cp10k.loc[idx, g][valid].mean())
        row = dict(allen_hl=hlname, gene=g, n_cells=len(idx), n_cells_with_gene_data=n_valid,
                   frac_expressed=round(frac, 4), mean_cp10k=round(mean_cp10k, 3), role=GENES[g])
        for s in SENS:
            row[f"call_{int(s * 100)}"] = int(frac >= s)
        return row

    rows = []
    for hlname, idx in cell_hl.groupby(cell_hl).groups.items():
        for g in genes:
            row = gene_row(hlname, idx, g)
            if row is not None:
                rows.append(row)

    # ALL_NEURONS reference row: pool over every hemilineage-assigned (neuronal) cell.
    for g in genes:
        row = gene_row("ALL_NEURONS", cell_hl.index, g)
        if row is not None:
            rows.append(row)

    calls = pd.DataFrame(rows)
    calls["call"] = calls[f"call_{int(THRESH * 100)}"]
    calls.to_csv(OUT / "channel_expression_allen2020_vnc.csv", index=False)
    n_hl = calls.loc[calls.allen_hl != "ALL_NEURONS", "allen_hl"].nunique()
    print(f"channel/innexin calls: {n_hl} Allen hemilineages (+1 ALL_NEURONS reference row) "
          f"x {len(genes)} genes (missing from DGE matrices entirely: {missing})")
    for s in SENS:
        c = calls.loc[calls.allen_hl != "ALL_NEURONS", f"call_{int(s * 100)}"]
        print(f"  threshold {s:.0%}: ON calls {c.sum()} / {len(c)}")


if __name__ == "__main__":
    main()
