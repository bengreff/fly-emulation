"""s20: Davie 2018 (Cell 174:982, adult brain 10x, 57k cells) receptor rows for male-cns types that have no Davis
2020 / Ozel 2021 row (N19 receptor_map mode 2; N20 peptide receptors as data only).

p = the share of a cluster's cells with >= 1 UMI of the gene (as Allen 2020's frac_expressed), pooled over the
clusters in the crosswalk weighted by cell count. Input: runs/s20/davie/clusters_annotation.csv (from
s20_davie_receptors.py; Davie's `annotation` column). Crosswalk basis (inferred, by name):
  *_adPN types -> the five adPN clusters (anterodorsal lineage); *_lPN -> the three lPN clusters (lateral lineage);
  KCg* -> G-KC; KCab-m -> A/B-KC + A/B*-KC; MBON* -> MBON; PAM* -> PAM; PPL1*/PPL2* -> Dopaminergic (the non-PAM
  DAN cluster); s-LNv/l-LNv -> LNv; DN1* -> DN1.
Not covered: ventral and other PNs, KCa'b' (no alpha'/beta' cluster), ring neurons, AL local neurons.
Also writes a scale check: Davie p against Davis/Ozel p on the types both cover.

    .venv/bin/python scripts/probes/s20_davie_rows.py
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

import numpy as np
import pandas as pd

R = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(R / "src"))
from flyemu import connectome  # noqa: E402

CL = R / "runs/s20/davie/clusters_annotation.csv"
OUT = R / "data/derived/receptor_calls_davie2018.csv"
CHECK = R / "data/derived/receptor_calls_davie_vs_davis.csv"
WALK = [  # (type regex, clusters, basis)
    (r".*_adPN", ["adPN", "adPN/C15", "adPN/C15&kn", "adPN/kn", "adPN/kn&CG31676"], "lineage (adPN)"),
    (r".*_lPN", ["lPN", "lPN/CG31676", "lPN/unpg"], "lineage (lPN)"),
    (r"KCg.*", ["G-KC"], "KC subclass"),
    (r"KCab-.*", ["A/B-KC", "A/B*-KC"], "KC subclass"),
    (r"MBON.*", ["MBON"], "class"),
    (r"PAM.*", ["PAM"], "class"),
    (r"PPL[12].*", ["Dopaminergic"], "non-PAM DAN cluster (inferred)"),
    (r"[sl]-LNv", ["LNv"], "clock group"),
    (r"DN1.*", ["DN1"], "clock group"),
]
# overlap check only (types with Davis/Ozel rows)
CHECK_WALK = WALK + [(r"L2", ["L2"], "cell type"), (r"T1", ["T1"], "cell type")]


def pooled(c: pd.DataFrame, names: list[str]) -> tuple[pd.Series, int]:
    s = c.loc[names]
    n = s.n_cells.to_numpy(float)
    f = s[[x for x in s.columns if x.startswith("frac:")]]
    return pd.Series(n @ f.to_numpy() / n.sum(), index=[x[5:] for x in f.columns]), int(n.sum())


def main() -> None:
    c = pd.read_csv(CL).set_index("cluster")
    d = pd.read_csv(R / "data/derived/receptor_calls_davis2020.csv")
    o = pd.read_csv(R / "data/derived/receptor_calls_ozel2021.csv")
    have = pd.concat([d, o]).pivot_table(index="male_cns_type", columns="gene", values="p_expressed")
    types = sorted(set(pd.read_parquet(connectome.CACHE / "male_cns_neurons.parquet").type.dropna()))
    rows, chk = [], []
    for pat, names, basis in CHECK_WALK:
        p, ncell = pooled(c, names)
        for t in (x for x in types if re.fullmatch(pat, x)):
            if t in have.index:
                for g in p.index.intersection(have.columns):
                    if np.isfinite(have.loc[t, g]):
                        chk.append({"male_cns_type": t, "gene": g, "p_davie": round(float(p[g]), 4),
                                    "p_type_rows": float(have.loc[t, g])})
            elif (pat, names, basis) in WALK:
                rows += [{"male_cns_type": t, "davie_clusters": "+".join(names), "n_cells": ncell, "gene": g,
                          "p_expressed": round(float(v), 4), "crosswalk_basis": basis} for g, v in p.items()]
    pd.DataFrame(rows).to_csv(OUT, index=False)
    k = pd.DataFrame(chk); k.to_csv(CHECK, index=False)
    print(f"{OUT.name}: {len(rows)} rows, {len({r['male_cns_type'] for r in rows})} types")
    if len(k):
        r = np.corrcoef(k.p_davie, k.p_type_rows)[0, 1]
        print(f"overlap check: {len(k)} type-gene pairs, {k.male_cns_type.nunique()} types; r = {r:.2f}; "
              f"median p_davie {k.p_davie.median():.3f} vs p_type_rows {k.p_type_rows.median():.3f}; "
              f"calls agree (p>0.5 both sides) {((k.p_davie > .5) == (k.p_type_rows > .5)).mean():.2f}")
        print(k.groupby("gene")[["p_davie", "p_type_rows"]].mean().round(2).to_string())


if __name__ == "__main__":
    main()
