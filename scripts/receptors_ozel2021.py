"""Receptor calls per optic-lobe cell type from Özel et al. 2021 (session 11).

Data: Özel, Simon et al. 2021 Nature 589:88, GEO GSE142787
GSE142787_Mixture_modeling.xlsx sheet Adult_MM_final (per-cluster probability that
a gene is ON from a bimodal mixture model, the same kind of call as Davis 2020
dataTable7b); cluster names from Supplementary Table 1
(41586_2020_2879_MOESM4_ESM.xlsx, "Annotation"; '*' = less confident annotation).
A gene is "expressed" at p >= 0.5; types with several clusters take the mean p.

Steps
  1. crosswalk Özel adult cluster names -> male-cns types (exact names; declared
     splits/pools below); unnamed clusters are skipped;
  2. calls for the receptor genes of scripts/infer_receptors.py
     -> data/derived/receptor_calls_ozel2021.csv (same columns as the Davis file);
  3. agreement with Davis 2020 on types both profile (a check of both datasets);
  4. glutamate sign per postsynaptic type, rule adapted to on/off calls:
     GluClalpha ON and GluRIA and GluRIB OFF -> -1 (GluCl-dominated);
     GluClalpha OFF and GluRIA or GluRIB ON -> +1 (candidate only, as for Davis)
     -> data/derived/glutamate_sign_ozel2021_rows.csv (types not already in the
     Davis-derived live rows).

    uv run --with openpyxl python scripts/receptors_ozel2021.py
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[1]
RAW = REPO / "data" / "raw" / "ozel2021"
OUT = REPO / "data" / "derived"
sys.path.insert(0, str(REPO / "scripts"))
from infer_receptors import GENES  # noqa: E402

SRC = "Özel, Simon et al. 2021 Nature 589:88, GEO GSE142787 Mixture_modeling (Adult_MM_final); Supp Table 1"
# Özel name -> male-cns types, when not an exact match
SPECIAL = {
    "Tm5ab": ["Tm5a", "Tm5b"], "Dm8": ["Dm8a", "Dm8b"], "Dm3": ["Dm3a", "Dm3b", "Dm3c"],
    "T4-5a/b": ["T4a", "T4b", "T5a", "T5b"], "T4-5c/d": ["T4c", "T4d", "T5c", "T5d"],
}
SKIP = {"T4/T5", "PR", "LQ", "TEv/d", "TEv", "TEd", "TEe", "Tm9v", "Tm9d", "Apop", "NB", "LPC"}


def annotation() -> pd.DataFrame:
    a = pd.read_excel(RAW / "41586_2020_2879_MOESM4_ESM.xlsx").iloc[:, :2]
    a.columns = ["cluster", "name"]
    a = a.dropna(subset=["cluster"])
    a = a[a.name.apply(lambda v: isinstance(v, str))]
    a["cluster"] = a.cluster.astype(int)
    a["confident"] = ~a.name.str.endswith("*")
    a["name"] = a.name.str.rstrip("*")
    return a


def main() -> None:
    types = set(pd.read_parquet(REPO / "data" / "cache" / "male_cns_neurons.parquet").type.dropna())
    a = annotation()
    rows = []
    for r in a.itertuples(index=False):
        if r.name in SKIP:
            continue
        tgt = SPECIAL.get(r.name, [r.name])
        tgt = [t for t in tgt if t in types]
        for t in tgt:
            basis = "derived" if (r.name == t and r.confident) else "inferred"
            rows.append(dict(cluster=r.cluster, ozel_name=r.name, male_cns_type=t, crosswalk_basis=basis))
    cw = pd.DataFrame(rows)
    mm = pd.read_excel(RAW / "GSE142787_Mixture_modeling.xlsx", sheet_name="Adult_MM_final", index_col=0)
    mm = mm[[c for c in mm.columns if isinstance(c, (int, np.integer))]]
    cw = cw[cw.cluster.isin(mm.columns)]
    genes = [g for g in GENES if g in mm.index]
    missing = sorted(set(GENES) - set(genes))
    p = mm.loc[genes, cw.cluster].T.set_axis(cw.index)          # rows: crosswalk entries
    p = pd.concat([cw[["male_cns_type", "crosswalk_basis"]], p], axis=1)
    per = p.groupby("male_cns_type").agg({**{g: "mean" for g in genes}, "crosswalk_basis": "min"})
    calls = per[genes].stack().rename("p_expressed").reset_index().rename(columns={"level_1": "gene"})
    calls["call"] = (calls.p_expressed >= 0.5).astype(int)
    calls["ozel_clusters"] = calls.male_cns_type.map(cw.groupby("male_cns_type").cluster.apply(
        lambda s: ";".join(map(str, sorted(s)))))
    calls["crosswalk_basis"] = calls.male_cns_type.map(per.crosswalk_basis)
    calls["role"] = calls.gene.map(GENES)
    calls.to_csv(OUT / "receptor_calls_ozel2021.csv", index=False)
    print(f"{calls.male_cns_type.nunique()} male-cns types from {cw.cluster.nunique()} adult clusters; "
          f"{len(genes)} genes (absent from the table: {missing})")

    dv = pd.read_csv(OUT / "receptor_calls_davis2020.csv")
    j = calls.merge(dv[["male_cns_type", "gene", "call"]], on=["male_cns_type", "gene"],
                    suffixes=("_ozel", "_davis"))
    if len(j):
        agree = (j.call_ozel == j.call_davis)
        print(f"agreement with Davis 2020: {agree.mean():.3f} over {len(j)} type-gene calls "
              f"({j.male_cns_type.nunique()} shared types); "
              f"Davis-on/Özel-off {((j.call_davis == 1) & (j.call_ozel == 0)).sum()}, "
              f"Davis-off/Özel-on {((j.call_davis == 0) & (j.call_ozel == 1)).sum()}")
        by = j.assign(a=agree).groupby("gene").a.mean().sort_values()
        print("  lowest-agreement genes:", by.head(6).round(2).to_dict())
        j.to_csv(OUT / "receptor_calls_ozel_vs_davis.csv", index=False)

    w = calls.pivot_table(index="male_cns_type", columns="gene", values="call")
    live = set(pd.read_csv(OUT / "glutamate_sign_transcript_live_rows.csv").type)
    out = []
    for t, r in w.iterrows():
        if t in live:
            continue
        if r.get("GluClalpha") == 1 and r.get("GluRIA") == 0 and r.get("GluRIB") == 0:
            out.append((t, -1.0, "live", "GluClalpha ON, GluRIA and GluRIB OFF (Özel adult mixture "
                        "model): GluCl-dominated, glutamatergic input inhibitory; mRNA, not synaptic localisation"))
        elif r.get("GluClalpha") == 0 and (r.get("GluRIA") == 1 or r.get("GluRIB") == 1):
            out.append((t, 1.0, "candidate", "iGluR ON, GluClalpha OFF (Özel adult mixture model): "
                        "glutamatergic input excitatory (candidate, not live; as for Davis)"))
    rows = pd.DataFrame([{"type": t, "param": "glutamate_receptor_sign", "value": v, "units": "sign",
                          "basis": "inferred", "source": SRC, "justification": why, "status": s}
                         for t, v, s, why in out])
    rows.to_csv(OUT / "glutamate_sign_ozel2021_rows.csv", index=False)
    print(f"glutamate sign rows (types not in the Davis live rows): "
          f"{rows.status.value_counts().to_dict() if len(rows) else {}}")


if __name__ == "__main__":
    main()
