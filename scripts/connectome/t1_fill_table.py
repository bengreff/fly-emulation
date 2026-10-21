"""T1F: inferred T1 synapse fill from MANC and BANC (fly2, 20 Oct; rule pre-registered in DECISIONS 20 Oct 22:02).

Fills the male-CNS prothoracic (T1) input deficit (F-XCONN-1) by matched cell type and connection, never inventing
a partner. Unit: x_X(A, B, s) = synapses from all type-A cells onto the type-B cells with soma in T1 on side s,
divided by the number of those B cells, in animal X (raw counts, before the model's synapse cut). Target = median
over the animals with a value (male CNS included); factor = target / x_mcns where x_mcns > 0, x_manc > 0 and
target > x_mcns, else 1. `connectome.t1_fill` applies the factor to kept male-CNS edges; it adds no edge.

Sources (Pugliese_cpg_2025 at 10e7661, its data/ folder = --pug):
  MANC  manc full vnc data/W_20260522_allSynapses.npz (dense, rows pre) + wTable_20260522_allSynapses.feather,
        aggregated by MANC's own type / somaNeuromere / somaSide labels (not by body matching).
  BANC  banc t1 premotor/W_20260217.npz + wTable_20260217_fullData_consistentColumns.csv (cell_type, side). No
        neuromere label and premotor-network cells only: a pair uses BANC only if the extract holds exactly as
        many B cells on side s as the male CNS has in T1 on side s, and A is in the extract.
  male CNS  data/cache/male_cns_{neurons,edges}.parquet, included cells as connectome.build (Traced or typed).

  manc   (backhouse, ~5 GB RAM): MANC per-(A, B, s) sums for T1 post cells -> runs/s20/t1fill/manc_t1_typepair.parquet
  table  (Mac): combine the three animals -> data/params/t1_fill.csv.gz (+ t1_fill.json provenance with sha256 of sources)

    python scripts/connectome/t1_fill_table.py manc --pug ~/pugliese_cpg/data
    uv run python scripts/connectome/t1_fill_table.py table --pug /tmp/pugliese_cpg/data
"""
from __future__ import annotations

import argparse
import gzip
import hashlib
import json
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[2]
CACHE = REPO / "data" / "cache"
OUT = REPO / "runs" / "s20" / "t1fill"
TABLE = REPO / "data" / "params" / "t1_fill.csv.gz"
PROV = REPO / "data" / "params" / "t1_fill.json"
MANC_W = "manc full vnc data/W_20260522_allSynapses.npz"
MANC_T = "manc full vnc data/wTable_20260522_allSynapses.feather"
BANC_W = "banc t1 premotor/W_20260217.npz"
BANC_T = "banc t1 premotor/wTable_20260217_fullData_consistentColumns.csv"
KEY = ["pre_type", "post_type", "post_side"]


def side(s) -> str:
    s = str(s).strip().upper()
    return "L" if s.startswith("L") else "R" if s.startswith("R") else "?"


def sha256(p: Path) -> str:
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


def _typepair(W: np.ndarray, pre_type: pd.Series, post_ix: np.ndarray, post_type: pd.Series,
              post_side: pd.Series) -> pd.DataFrame:
    """Synapse sums from each presynaptic type onto each (post type, side) group of the given post columns."""
    keep = pre_type.notna().to_numpy()
    M = pd.DataFrame(np.abs(W[np.ix_(np.flatnonzero(keep), post_ix)]))
    grp = post_type.astype(str).to_numpy() + "\t" + post_side.to_numpy()
    cols = {}
    for name, X in (("syn", M), ("n_conn", (M > 0).astype(np.int64))):
        by = X.groupby(pre_type[keep].to_numpy()).sum().T.groupby(grp).sum().T     # pre types x (B, s)
        cols[name] = by.stack()
    out = pd.DataFrame(cols)
    out = out[out.syn > 0].reset_index()
    out.columns = ["pre_type", "grp", "syn", "n_conn"]
    out[["post_type", "post_side"]] = out.grp.str.split("\t", expand=True)
    return out[KEY + ["syn", "n_conn"]]


def manc(a) -> None:
    pug = Path(a.pug).expanduser()
    t = pd.read_feather(pug / MANC_T)
    W = np.load(pug / MANC_W)["arr_0"]
    assert W.shape == (len(t), len(t)), (W.shape, len(t))
    nm = t.somaNeuromere.astype(str)
    q = np.flatnonzero((nm.eq("T1") & t.type.notna()).to_numpy())
    ps = t.somaSide.map(side)
    tp = _typepair(W, t.type, q, t.type.iloc[q].reset_index(drop=True), ps.iloc[q].reset_index(drop=True))
    n = (pd.DataFrame(dict(post_type=t.type.iloc[q].to_numpy(), post_side=ps.iloc[q].to_numpy()))
         .value_counts().rename("n_post").reset_index())
    tp = tp.merge(n, on=["post_type", "post_side"])
    OUT.mkdir(parents=True, exist_ok=True)
    tp.to_parquet(OUT / "manc_t1_typepair.parquet")
    prov = dict(W=MANC_W, W_sha256=sha256(pug / MANC_W), table=MANC_T, table_sha256=sha256(pug / MANC_T),
                n_cells=int(len(t)), n_t1_typed_post=int(len(q)), n_pairs=int(len(tp)),
                neuromere_values=nm.value_counts().head(20).to_dict(),
                side_values=t.somaSide.astype(str).value_counts().to_dict())
    (OUT / "manc_t1_typepair.json").write_text(json.dumps(prov, indent=1))
    print(json.dumps({k: v for k, v in prov.items() if "values" not in k}, indent=1))


def mcns_typepair() -> tuple[pd.DataFrame, pd.DataFrame]:
    """Male-CNS x per (A, B, s) for T1 post cells, included cells as connectome.build, raw counts."""
    nr = pd.read_parquet(CACHE / "male_cns_neurons.parquet")
    nr = nr[(nr.status == "Traced") | nr.type.notna()]
    ed = pd.read_parquet(CACHE / "male_cns_edges.parquet")
    ty = nr.set_index("bodyId").type
    post = nr[nr.somaNeuromere.astype(str).eq("T1") & nr.type.notna()].copy()
    post["post_side"] = post.somaSide.map(side)
    e = ed[ed.post.isin(post.bodyId) & ed.pre.isin(nr.bodyId)].copy()
    e["pre_type"] = e.pre.map(ty)
    e = e[e.pre_type.notna()]
    ps = post.set_index("bodyId")
    e["post_type"], e["post_side"] = e.post.map(ps.type), e.post.map(ps.post_side)
    tp = e.groupby(KEY).weight.agg(syn="sum", n_conn="size").reset_index()
    n = post.rename(columns={"type": "post_type"})[["post_type", "post_side"]].value_counts().rename(
        "n_post").reset_index()
    return tp.merge(n, on=["post_type", "post_side"]), n


def banc_typepair(pug: Path, n_mcns: pd.DataFrame) -> pd.DataFrame:
    """BANC x per (A, B, s) where the extract's B count on side s equals the male-CNS T1 count (rule above)."""
    t = pd.read_csv(pug / BANC_T)
    W = np.load(pug / BANC_W)["arr_0"]
    assert W.shape == (len(t), len(t))
    sd = t.side.map(side)
    nb = pd.DataFrame(dict(post_type=t.cell_type, post_side=sd)).dropna().value_counts().rename("n_banc")
    ok = n_mcns.set_index(["post_type", "post_side"]).n_post.reindex(nb.index)
    good = set(nb.index[(nb.to_numpy() == ok.to_numpy())])
    q = np.flatnonzero([(ct, s) in good for ct, s in zip(t.cell_type, sd)])
    tp = _typepair(W, t.cell_type, q, t.cell_type.iloc[q].reset_index(drop=True), sd.iloc[q].reset_index(drop=True))
    tp = tp.merge(nb.rename("n_post").reset_index(), on=["post_type", "post_side"])
    return tp, dict(n_post_groups_extract=int(len(nb)), n_post_groups_count_match=len(good))


def table(a) -> None:
    pug = Path(a.pug).expanduser()
    mc, n_mcns = mcns_typepair()
    ma = pd.read_parquet(OUT / "manc_t1_typepair.parquet")
    bc, binfo = banc_typepair(pug, n_mcns)
    for d in (mc, ma, bc):
        d["x"] = d.syn / d.n_conn
    j = (mc.rename(columns=dict(syn="syn_mcns", n_post="n_post_mcns", x="x_mcns"))
         .merge(ma.rename(columns=dict(syn="syn_manc", n_post="n_post_manc", x="x_manc")), on=KEY, how="left")
         .merge(bc.rename(columns=dict(syn="syn_banc", n_post="n_post_banc", x="x_banc")), on=KEY, how="left"))
    j["target"] = j[["x_mcns", "x_manc", "x_banc"]].median(axis=1, skipna=True)
    fill = j.x_manc.gt(0) & j.target.gt(j.x_mcns)
    j["factor"] = np.where(fill, j.target / j.x_mcns, 1.0)
    j["n_animals"] = j[["x_mcns", "x_manc", "x_banc"]].notna().sum(axis=1)
    out = j[fill][KEY + ["n_post_mcns", "x_mcns", "n_post_manc", "x_manc", "n_post_banc", "x_banc", "n_animals",
                         "target", "factor"]].sort_values(KEY)
    for c in ("x_mcns", "x_manc", "x_banc", "target"):
        out[c] = out[c].round(3)
    out["factor"] = out.factor.round(5)
    TABLE.parent.mkdir(parents=True, exist_ok=True)
    with gzip.open(TABLE, "wt") as f:
        f.write("# T1F inferred T1 fill (fly2, DECISIONS 20 Oct 22:02). basis: inferred (cross-animal). Rows: "
                "(pre type, T1 post type, post side) with factor > 1 only; x = synapses per post cell from the "
                "type; target = median over male CNS, MANC (W_20260522) and BANC (W_20260217, count-matched post "
                "types only). Built by scripts/connectome/t1_fill_table.py; provenance in t1_fill.json\n")
        out.to_csv(f, index=False)
    t1_types = n_mcns.merge(ma[["post_type", "post_side", "n_post"]].drop_duplicates(),
                            on=["post_type", "post_side"], how="left", suffixes=("", "_manc"))
    prov = dict(rule="DECISIONS 20 Oct 22:02 (T1F)", basis="inferred (cross-animal)",
                manc=json.loads((OUT / "manc_t1_typepair.json").read_text()),
                banc=dict(W=BANC_W, W_sha256=sha256(pug / BANC_W), table=BANC_T, table_sha256=sha256(pug / BANC_T),
                          **binfo),
                mcns=dict(neurons_sha256=sha256(CACHE / "male_cns_neurons.parquet"),
                          edges_sha256=sha256(CACHE / "male_cns_edges.parquet")),
                pairs_mcns=int(len(j)), pairs_with_manc=int(j.x_manc.notna().sum()),
                pairs_with_banc=int(j.x_banc.notna().sum()), pairs_filled=int(fill.sum()),
                pairs_filled_with_banc=int((fill & j.x_banc.notna()).sum()),
                t1_post_groups=int(len(n_mcns)), t1_post_groups_in_manc=int(t1_types.n_post_manc.notna().sum()),
                t1_post_groups_same_count_in_manc=int(t1_types.n_post.eq(t1_types.n_post_manc).sum()),
                t1_post_cells=int(n_mcns.n_post.sum()),
                t1_post_cells_type_in_manc=int(t1_types.n_post[t1_types.n_post_manc.notna()].sum()),
                syn_mcns_t1_typed=int(j.syn_mcns.sum()),
                factor_quantiles={str(q): round(float(out.factor.quantile(q)), 3) for q in (0.1, 0.5, 0.9, 0.99)},
                factor_max=round(float(out.factor.max()), 2), table_sha256=None)
    prov["table_sha256"] = sha256(TABLE)
    PROV.write_text(json.dumps(prov, indent=1))
    print(json.dumps({k: v for k, v in prov.items() if k != "manc"}, indent=1))


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("cmd", choices=("manc", "table"))
    ap.add_argument("--pug", default="~/pugliese_cpg/data")
    a = ap.parse_args()
    manc(a) if a.cmd == "manc" else table(a)
