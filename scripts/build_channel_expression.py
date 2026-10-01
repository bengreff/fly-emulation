"""Ion-channel and innexin expression per male-cns type (session 11, fidelity rung 1).

Data (measured, mRNA):
  Davis, Nern et al. 2020 eLife 9:e50901, GEO GSE116969: dataTable7a (TPM) and
  dataTable7b (on/off probability), joined through data/derived/davis2020_crosswalk.csv;
  Özel, Simon et al. 2021 Nature 589:88, GEO GSE142787: Adult_average_expression
  (log-normalised cluster means) and Adult_MM_final (on/off probability), clusters
  joined to male-cns types as in scripts/receptors_ozel2021.py.

Per (type, gene): p_expressed (mean over the type's populations), level (TPM, or
expm1 of the Özel log-normalised mean) and rel_level = level / the gene's median
level over that dataset's mapped types. Types in both datasets get the geometric
mean of the two rel_levels. rel_level is dimensionless and comparable across
datasets only through that median normalisation (inferred).

Interpretation used by src/flyemu/channels.py (inferred, not measured): channel
density of a type = class gbar x rel_level^beta, beta a registry exponent
(0 = uniform). mRNA level is a weak proxy for functional channel density.

    uv run --with openpyxl python scripts/build_channel_expression.py
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "scripts"))
from receptors_ozel2021 import SKIP, SPECIAL, annotation  # noqa: E402

DAVIS = REPO / "data/raw/davis2020"
OZEL = REPO / "data/raw/ozel2021"
OUT = REPO / "data/derived/channel_expression_by_type.csv"

GENES = {
    "para": "Nav: voltage-gated Na (spike, persistent Na)",
    "Sh": "Kv1: fast A-type K", "Shal": "Kv4: somatodendritic A-type K",
    "Shab": "Kv2: delayed-rectifier K", "Shaw": "Kv3: K",
    "KCNQ": "Kv7: M-type slow K", "eag": "Kv10: K", "sei": "Kv11 (erg): K",
    "slo": "BK: Ca- and voltage-activated K", "SK": "SK: Ca-activated K",
    "Ih": "HCN: hyperpolarisation-activated cation (Ih)",
    "cac": "Cav2: high-voltage-activated Ca", "Ca-alpha1D": "Cav1: L-type Ca",
    "Ca-alpha1T": "Cav3: T-type (low-voltage) Ca",
    "Irk1": "inward-rectifier K", "Irk2": "inward-rectifier K", "Irk3": "inward-rectifier K",
    "Ork1": "two-pore leak K", "Task6": "two-pore leak K", "Task7": "two-pore leak K",
    "Hk": "Kv beta subunit",
    "shakB": "innexin (neuronal gap junctions)", "ogre": "innexin", "Inx2": "innexin",
    "Inx3": "innexin", "Inx5": "innexin", "Inx6": "innexin", "Inx7": "innexin", "zpg": "innexin",
}


def davis() -> pd.DataFrame:
    tpm = pd.read_csv(DAVIS / "GSE116969_dataTable7a.genes_x_cells_TPM.modeled_genes.txt.gz", sep="\t", index_col=0)
    pe = pd.read_csv(DAVIS / "GSE116969_dataTable7b.genes_x_cells_p_expression.modeled_genes.txt.gz",
                     sep="\t", index_col=0)
    cw = pd.read_csv(REPO / "data/derived/davis2020_crosswalk.csv")
    cw = cw[cw.davis_cell.isin(tpm.columns) & cw.davis_cell.isin(pe.columns)]
    genes = [g for g in GENES if g in tpm.index and g in pe.index]
    rows = []
    for r in cw.itertuples(index=False):
        for g in genes:
            rows.append((r.male_cns_type, g, float(pe.at[g, r.davis_cell]), float(tpm.at[g, r.davis_cell]),
                         r.basis, r.davis_cell))
    d = pd.DataFrame(rows, columns=["male_cns_type", "gene", "p_expressed", "level", "crosswalk_basis", "populations"])
    d = d.groupby(["male_cns_type", "gene"]).agg(
        p_expressed=("p_expressed", "mean"), level=("level", "mean"), crosswalk_basis=("crosswalk_basis", "min"),
        populations=("populations", lambda s: ";".join(sorted(set(s))))).reset_index()
    d["source"] = "davis2020"
    return d, sorted(set(GENES) - set(genes))


def ozel(types: set) -> pd.DataFrame:
    a = annotation()
    cw = []
    for r in a.itertuples(index=False):
        if r.name in SKIP:
            continue
        for t in SPECIAL.get(r.name, [r.name]):
            if t in types:
                cw.append((r.cluster, t, "derived" if (r.name == t and r.confident) else "inferred"))
    cw = pd.DataFrame(cw, columns=["cluster", "male_cns_type", "crosswalk_basis"])
    lv = pd.read_excel(OZEL / "GSE142787_Log_normalized_average_expression.xlsx",
                       sheet_name="Adult_average_expression", index_col=0)
    mm = pd.read_excel(OZEL / "GSE142787_Mixture_modeling.xlsx", sheet_name="Adult_MM_final", index_col=0)
    cols = [c for c in cw.cluster.unique() if c in lv.columns and c in mm.columns]
    cw = cw[cw.cluster.isin(cols)]
    genes = [g for g in GENES if g in lv.index and g in mm.index]
    rows = []
    for r in cw.itertuples(index=False):
        for g in genes:
            rows.append((r.male_cns_type, g, float(mm.at[g, r.cluster]), float(np.expm1(lv.at[g, r.cluster])),
                         r.crosswalk_basis, str(r.cluster)))
    d = pd.DataFrame(rows, columns=["male_cns_type", "gene", "p_expressed", "level", "crosswalk_basis", "populations"])
    d = d.groupby(["male_cns_type", "gene"]).agg(
        p_expressed=("p_expressed", "mean"), level=("level", "mean"), crosswalk_basis=("crosswalk_basis", "min"),
        populations=("populations", lambda s: ";".join(sorted(set(s), key=int)))).reset_index()
    d["source"] = "ozel2021"
    return d, sorted(set(GENES) - set(genes))


def main() -> None:
    neurons = pd.read_parquet(REPO / "data/cache/male_cns_neurons.parquet")
    types = set(neurons.type.dropna())
    parts = []
    for name, (d, miss) in (("davis2020", davis()), ("ozel2021", ozel(types))):
        med = d.groupby("gene")["level"].median()
        d["rel_level"] = d["level"] / d.gene.map(med).where(lambda m: m > 0)
        parts.append(d)
        print(f"{name}: {d.male_cns_type.nunique()} types; genes absent: {miss}")
    d = pd.concat(parts, ignore_index=True)
    comb = (d.assign(lr=np.log(d.rel_level.clip(lower=1e-3)))
            .groupby(["male_cns_type", "gene"])
            .agg(rel_level=("lr", lambda s: float(np.exp(s.mean()))), p_expressed=("p_expressed", "mean"),
                 sources=("source", lambda s: ";".join(sorted(s))),
                 crosswalk_basis=("crosswalk_basis", "min")).reset_index())
    comb["role"] = comb.gene.map(GENES)
    comb["label"] = "measured mRNA (rel_level normalised per dataset: derived)"
    comb = comb.merge(d.pivot_table(index=["male_cns_type", "gene"], columns="source", values="level")
                      .add_prefix("level_").reset_index(), on=["male_cns_type", "gene"], how="left")
    comb.to_csv(OUT, index=False, float_format="%.4g")
    nt = comb.male_cns_type.nunique()
    ncell = int(neurons.type.isin(set(comb.male_cns_type)).sum())
    both = (comb.sources.str.contains(";")).groupby(comb.male_cns_type).any().sum()
    print(f"-> {OUT.relative_to(REPO)}: {nt} types ({both} in both datasets), {ncell} of {len(neurons)} "
          f"male-cns neurons ({100 * ncell / len(neurons):.1f}%)")
    j = d.pivot_table(index=["male_cns_type", "gene"], columns="source", values="rel_level").dropna()
    if len(j):
        r = np.corrcoef(np.log(j.davis2020.clip(lower=1e-3)), np.log(j.ozel2021.clip(lower=1e-3)))[0, 1]
        print(f"cross-dataset check: log rel_level r = {r:.2f} over {len(j)} shared type-gene pairs")
    s = comb.pivot_table(index="male_cns_type", columns="gene", values="rel_level")
    print("rel_level spread across types (10th / 50th / 90th percentile):")
    print(s.quantile([0.1, 0.5, 0.9]).T.round(2).to_string())


if __name__ == "__main__":
    main()
