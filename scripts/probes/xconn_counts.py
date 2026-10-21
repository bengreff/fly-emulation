"""X1 cross-connectome control (s13, 14 Oct; DECISIONS 14 Oct 00:39): MANC counts on male-CNS cells, and the count audit.

DIAGNOSTIC; no fitting. Sources (Pugliese_cpg_2025 at 10e7661, their extracts, `--pug` = its data/ folder):
  MANC   manc full vnc data/W_20260522_allSynapses.npz (dense, rows pre, columns post; orientation and counts checked
         here against their T1L minicircuit, E2->I1 = 71) + wTable_20260522_allSynapses.feather
  BANC   banc t1 premotor/W_20260217.npz + wTable_20260217_fullData_consistentColumns.csv (MANC type labels)
  FANC   not usable: that extract labels interneurons by hemilineage only, so E2 and I1 can't be identified
Male CNS is our own cache (data/cache/male_cns_{neurons,edges}.parquet); matching is the dataset's `mancBodyid`.

  build  (backhouse, needs ~5 GB RAM for the dense MANC matrix): every MANC edge between two VNC-set male-CNS cells
         with a one-to-one mancBodyid, as male-CNS bodyIds -> runs/s13/xconn/manc_on_mcns_edges.parquet; plus
         MANC per-cell input totals for the core cells (manc_core.json).
  audit  (Mac): core edges per neuromere and side in male CNS, MANC and BANC, matched-edge ratio distribution, I1 input
         completeness -> runs/s13/xconn/audit.json.

    uv run python scripts/probes/xconn_counts.py build --pug ~/pugliese_cpg/data
    uv run python scripts/probes/xconn_counts.py audit --pug /tmp/pugliese_cpg/data
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(Path(__file__).resolve().parent))
from bypass_s2_descending import VNC_SUPER  # noqa: E402

OUT = REPO / "runs" / "s13" / "xconn"
CACHE = REPO / "data" / "cache"
# male-CNS type -> role; MANC/BANC/FANC use MANC type names (E2 = IN15A001, I1 = IN16B007; F-BYPASS-3)
CORE_MCNS = {"DNg100": "DNg100", "IN17A001": "E1", "INXXX466": "E2", "IN16B036": "I1", "IN19A007": "A007",
             "IN19A004": "A004", "IN19A002": "A002"}
# MANC v1.2 full table and BANC use the male-CNS names; the 2024 minicircuit the old ones
CORE_MANC = {**CORE_MCNS, "BDN2": "DNg100", "IN15A001": "E2", "IN16B007": "I1"}
EDGES = (("DNg100", "E1"), ("DNg100", "E2"), ("E1", "E2"), ("E2", "E1"), ("E2", "I1"), ("E1", "I1"), ("I1", "E1"),
         ("I1", "E2"), ("E1", "A007"), ("E2", "A007"), ("A007", "E1"), ("A002", "I1"), ("A004", "I1"))


def vnc_matched(neurons: pd.DataFrame) -> pd.DataFrame:
    """Included (Traced or typed, as connectome.build) VNC-set cells with a one-to-one mancBodyid."""
    n = neurons[(neurons.status == "Traced") | neurons.type.notna()]
    sc = n.superclass.fillna("").astype(str)
    n = n[(sc.str.startswith("vnc_") | sc.isin(VNC_SUPER)) & n.mancBodyid.notna()].copy()
    n["mancBodyid"] = n.mancBodyid.astype(np.int64)
    return n[~n.mancBodyid.duplicated(keep=False)]


def build(a) -> None:
    pug = Path(a.pug).expanduser()
    D = pug / "manc full vnc data"
    t = pd.read_feather(D / "wTable_20260522_allSynapses.feather")
    W = np.load(D / "W_20260522_allSynapses.npz")["arr_0"]
    # orientation and count check against their T1L minicircuit (the F-BYPASS-3 reference)
    mt = pd.read_csv(pug / "manc t1l minicircuit" / "wTable_20241118_T1Lminicircuit.csv")
    mW = np.load(pug / "manc t1l minicircuit" / "W_20241118_T1Lminicircuit.npy")
    e2 = int(mt.bodyId[mt.type.eq("IN15A001")].iloc[0]); i1 = int(mt.bodyId[mt.type.eq("IN16B007")].iloc[0])
    ix = pd.Series(np.arange(len(t)), index=t.bodyId.astype(np.int64))
    mix = pd.Series(np.arange(len(mt)), index=mt.bodyId.astype(np.int64))
    chk = dict(mini_e2_i1=float(mW[mix[e2], mix[i1]]), mini_i1_e2=float(mW[mix[i1], mix[e2]]),
               full_e2_i1=float(W[ix[e2], ix[i1]]), full_i1_e2=float(W[ix[i1], ix[e2]]), e2=e2, i1=i1)
    print("check", chk)
    assert abs(chk["full_e2_i1"]) == abs(chk["mini_e2_i1"]) and abs(chk["mini_e2_i1"]) == 71, chk
    W = np.abs(W)  # counts only; signs come from the male-CNS cell in the model
    neurons = pd.read_parquet(CACHE / "male_cns_neurons.parquet")
    m = vnc_matched(neurons)
    m = m[m.mancBodyid.isin(ix.index)]
    r = ix[m.mancBodyid.to_numpy()].to_numpy()
    sub = W[np.ix_(r, r)]
    pi, po = np.nonzero(sub)
    b = m.bodyId.to_numpy(np.int64)
    out = pd.DataFrame(dict(pre=b[pi], post=b[po], weight=sub[pi, po].astype(np.int32)))
    OUT.mkdir(parents=True, exist_ok=True)
    out.to_parquet(OUT / "manc_on_mcns_edges.parquet")
    core = {}
    for ty, role in CORE_MANC.items():
        for bid in t.bodyId[t.type.eq(ty)].astype(np.int64):
            k = ix[bid]
            core[str(bid)] = dict(role=role, type=ty, neuromere=str(t.somaNeuromere.iloc[k]),
                                  side=str(t.somaSide.iloc[k]), in_total=float(W[:, k].sum()),
                                  out_total=float(W[k, :].sum()))
    (OUT / "manc_core.json").write_text(json.dumps(dict(check=chk, n_matched=int(len(m)), n_edges=int(len(out)),
                                                         core=core), indent=1))
    print(f"matched cells {len(m)}, MANC edges among them {len(out)}, synapses {int(out.weight.sum())}")


def _side(s: str) -> str:
    s = str(s).upper()
    return "L" if s.startswith("L") else "R" if s.startswith("R") else "?"


def audit(a) -> None:
    pug = Path(a.pug).expanduser()
    neurons = pd.read_parquet(CACHE / "male_cns_neurons.parquet")
    extra = pd.read_parquet(CACHE / "male_cns_extra.parquet", columns=["bodyId", "statusLabel"])
    edges = pd.read_parquet(CACHE / "male_cns_edges.parquet")
    manc = pd.read_parquet(OUT / "manc_on_mcns_edges.parquet")
    mcore = json.loads((OUT / "manc_core.json").read_text())
    m = vnc_matched(neurons)
    S = set(m.bodyId)
    # 1) dataset-wide matched-edge ratio (male CNS / MANC), edges with >= 10 MANC synapses
    mc = edges[edges.pre.isin(S) & edges.post.isin(S)]
    j = manc.merge(mc, on=["pre", "post"], how="left", suffixes=("_manc", "_mcns")).fillna({"weight_mcns": 0})
    big = j[j.weight_manc >= 10]
    lr = np.log((big.weight_mcns + 1) / (big.weight_manc + 1))
    g = float(np.exp(np.median(lr)))
    sim = j[(j.weight_manc >= 30) & (j.weight_manc <= 150)]
    lrs = np.log((sim.weight_mcns + 1) / (sim.weight_manc + 1)) - np.log(g)
    band = [float(np.quantile(lrs, q)) for q in (0.05, 0.5, 0.95)]
    both = j[(j.weight_manc >= 10) & (j.weight_mcns >= 10)]  # secondary (not pre-registered): edges in both
    g_both = float(np.exp(np.median(np.log(both.weight_mcns / both.weight_manc))))
    # 2) core edges per neuromere/side, male CNS and MANC (MANC counts read through the matched pairs)
    core = neurons[neurons.type.isin(CORE_MCNS)].copy()
    core["role"] = core.type.map(CORE_MCNS)
    core["seg"] = core.somaNeuromere.fillna("").astype(str) + core.somaSide.fillna("").astype(str).map(_side)
    st = extra.set_index("bodyId").statusLabel
    w_mc = edges.set_index(["pre", "post"]).weight
    w_ma = manc.set_index(["pre", "post"]).weight
    rows = []
    dn = core[core.role.eq("DNg100")]
    for seg, c in core[~core.role.eq("DNg100")].groupby("seg"):
        ids = {r: c.bodyId[c.role.eq(r)].tolist() for r in set(CORE_MCNS.values())}
        ids["DNg100"] = dn.bodyId.tolist()
        for pre, post in EDGES:
            if not ids.get(pre) or not ids.get(post):
                continue
            pairs = [(p, q) for p in ids[pre] for q in ids[post]]
            a_ = sum(int(w_mc.get(k, 0)) for k in pairs)
            b_ = sum(int(w_ma.get(k, 0)) for k in pairs)
            rows.append(dict(seg=seg, edge=f"{pre}>{post}", mcns=a_, manc=b_,
                             norm_log_ratio=round(float(np.log((a_ + 1) / (b_ + 1)) - np.log(g)), 3)))
    tab = pd.DataFrame(rows)
    e2i1 = tab[tab.edge.eq("E2>I1")]
    # 3) I1 input completeness, male CNS (our cache) and MANC (Pugliese's full matrix totals)
    i1 = core[core.role.eq("I1")]
    status = neurons.set_index("bodyId").status
    comp = []
    for _, r in i1.iterrows():
        inn = edges[edges.post.eq(r.bodyId)]
        trc = inn.pre.map(status).eq("Traced")
        comp.append(dict(seg=r.seg, bodyId=int(r.bodyId), status=r.status, statusLabel=st.get(r.bodyId),
                         post_total=int(r.post), in_from_neurons=int(inn.weight.sum()),
                         in_from_traced=int(inn.weight[trc].sum()),
                         traced_frac_of_post=round(float(inn.weight[trc].sum() / max(r.post, 1)), 3),
                         e2_share=round(float(tab[(tab.seg == r.seg) & tab.edge.eq("E2>I1")].mcns.sum()
                                              / max(inn.weight[trc].sum(), 1)), 3)))
    mi1 = {k: v for k, v in mcore["core"].items() if v["role"] == "I1"}
    # shared vs specific: I1's matched inputs, normalised log ratio per input partner (T1, both sides)
    spec = []
    for _, r in i1.iterrows():
        a_in = mc[mc.post.eq(r.bodyId)].set_index("pre").weight
        b_in = manc[manc.post.eq(r.bodyId)].set_index("pre").weight
        idx = b_in.index[b_in >= 10]
        if len(idx):
            v = np.log((a_in.reindex(idx).fillna(0) + 1) / (b_in[idx] + 1)) - np.log(g)
            spec.append(dict(seg=r.seg, n_inputs=int(len(idx)), median_norm_log_ratio=round(float(v.median()), 3),
                             sum_mcns=int(a_in.reindex(idx).fillna(0).sum()), sum_manc=int(b_in[idx].sum())))
    # 4) BANC and FANC (Pugliese's T1 extracts; type labels are MANC names)
    other = {}
    bt = pd.read_csv(pug / "banc t1 premotor" / "wTable_20260217_fullData_consistentColumns.csv")
    bW = np.abs(np.load(pug / "banc t1 premotor" / "W_20260217.npz")["arr_0"])
    other["BANC"] = _extract_edges(bt, bW, "cell_type", "side", ("BDN2", "DNg100"))
    # FANC's extract labels interneurons by hemilineage only (e.g. "16B"), so E2 and I1 can't be identified there
    res = dict(global_ratio_mcns_over_manc=round(g, 3), n_edges_ge10=int(len(big)),
               secondary_ratio_edges_in_both=round(g_both, 3), n_edges_both=int(len(both)),
               similar_size_band_norm_log_ratio=dict(q05=band[0], q50=band[1], q95=band[2], n=int(len(sim))),
               e2_i1=e2i1.to_dict("records"), core_edges=tab.to_dict("records"), i1_completeness=comp,
               i1_input_specificity=spec, manc_i1=mi1, other_animals=other,
               core_status={int(b): st.get(b) for b in core.bodyId})
    (OUT / "audit.json").write_text(json.dumps(res, indent=1, default=str))
    print(f"global male-CNS/MANC ratio {g:.3f} over {len(big)} matched edges >= 10; similar-size band "
          f"(norm log ratio) q05 {band[0]:.2f} q50 {band[1]:.2f} q95 {band[2]:.2f} (n {len(sim)})")
    print(tab[tab.edge.isin(["E2>I1", "E1>I1", "E1>E2", "DNg100>E1", "A002>I1"])].to_string(index=False))
    print(json.dumps(dict(i1_completeness=comp, i1_input_specificity=spec, manc_i1=mi1, other=other), indent=1,
                     default=str))


def _extract_edges(t: pd.DataFrame, W: np.ndarray, col: str, side: str | None, dn: tuple) -> dict:
    roles = t[col].map(lambda x: "DNg100" if x in dn else CORE_MANC.get(x))
    out = {}
    for pre, post in EDGES:
        pi = np.flatnonzero(roles.eq(pre).to_numpy()); qi = np.flatnonzero(roles.eq(post).to_numpy())
        if not pi.size or not qi.size:
            continue
        if side is None:
            out[f"{pre}>{post}"] = int(W[np.ix_(pi, qi)].sum())
            continue
        sd = t[side].map(_side).to_numpy()
        for s in ("L", "R"):  # ipsilateral pairs of the core interneurons; DNg100 from both sides
            p2 = pi if pre == "DNg100" else pi[sd[pi] == s]
            q2 = qi[sd[qi] == s]
            if p2.size and q2.size:
                out[f"{pre}>{post} T1{s}"] = int(W[np.ix_(p2, q2)].sum())
    out["n_cells"] = {r: int(roles.eq(r).sum()) for r in set(CORE_MANC.values())}
    return out


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("cmd", choices=("build", "audit"))
    ap.add_argument("--pug", default="~/pugliese_cpg/data")
    a = ap.parse_args()
    build(a) if a.cmd == "build" else audit(a)
