"""T1F count audit, before and after the inferred T1 fill (fly2, 20 Oct; DECISIONS 20 Oct 22:02). No simulation.

Applies `connectome.t1_fill` (the model's own code) to the male-CNS edge table twice: raw counts (cut 1, the F-XCONN-1
metric) and the model's kept edges (cut 5). Reports: edge set unchanged; synapses added onto T1 cells; the
synapse-weighted factor distribution and the largest single additions; the per-cell matched-input ratio male CNS /
MANC per neuromere (F-XCONN-1: cells with >= 500 MANC matched inputs; MANC counts from xconn_counts.py build);
I1 (IN16B036) inputs and E2 (INXXX466) -> I1 per neuromere and side; raw edges below the cut that the fill would
lift over it. Output runs/s20/t1fill/audit.json and docs/media/s20_fly2_t1fill_audit.png.

    uv run python scripts/connectome/t1_fill_audit.py
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "src")); sys.path.insert(0, str(REPO / "scripts" / "probes"))
from flyemu import connectome  # noqa: E402
from flyemu.registry import Policy, Registry  # noqa: E402
from xconn_counts import OUT as XOUT, vnc_matched  # noqa: E402

OUT = REPO / "runs" / "s20" / "t1fill"
FIG = REPO / "docs" / "media" / "s20_fly2_t1fill_audit.png"
KEY = "connectome:T1|fill_from_other_animals"
E2, I1 = "INXXX466", "IN16B036"


def filled(neurons: pd.DataFrame, e: pd.DataFrame) -> pd.DataFrame:
    r = Registry(Policy.MINIMAL)
    r.overrides[KEY] = 1.0
    return connectome.t1_fill(r, neurons, e)


def seg(n: pd.DataFrame) -> pd.Series:
    return n.somaNeuromere.fillna("").astype(str) + n.somaSide.map(connectome._side)


def main() -> None:
    nr, ed = connectome.load_tables()
    nr = nr[(nr.status == "Traced") | nr.type.notna()].reset_index(drop=True)
    ed = ed[ed.pre.isin(nr.bodyId) & ed.post.isin(nr.bodyId)].reset_index(drop=True)
    t1 = set(nr.bodyId[nr.somaNeuromere.astype(str).eq("T1") & nr.type.notna()])
    res = {}
    for cut in (1, 5):
        e0 = ed[ed.weight >= cut].reset_index(drop=True)
        e1 = filled(nr, e0)
        assert len(e1) == len(e0) and (e1.pre.to_numpy() == e0.pre.to_numpy()).all() \
            and (e1.post.to_numpy() == e0.post.to_numpy()).all(), "edge set changed"
        f = e1.weight.to_numpy() / e0.weight.to_numpy()
        assert (f >= 1 - 1e-6).all() and not (f[~e0.post.isin(t1).to_numpy()] > 1 + 1e-6).any()
        on = e0.post.isin(t1).to_numpy()
        add = e1.weight.to_numpy() - e0.weight.to_numpy()
        w0 = e0.weight.to_numpy()[on]
        fo = f[on]
        o = np.argsort(fo)
        cw = np.cumsum(w0[o]) / w0.sum()
        res[f"cut{cut}"] = dict(
            edges_onto_t1=int(on.sum()), edges_scaled=int((fo > 1 + 1e-6).sum()),
            syn_onto_t1_before=int(w0.sum()), syn_onto_t1_after=round(float(e1.weight.to_numpy()[on].sum())),
            syn_weighted_factor={str(q): round(float(fo[o][np.searchsorted(cw, q)]), 3) for q in (0.1, 0.5, 0.9, 0.99)},
            syn_all_before=int(e0.weight.sum()), syn_all_after=round(float(e1.weight.sum())))
        if cut == 5:
            ty = nr.set_index("bodyId").type
            top = e0.assign(after=e1.weight, add=add, factor=f).nlargest(15, "add")
            top["pre_type"], top["post_type"] = top.pre.map(ty), top.post.map(ty)
            res["top_additions_cut5"] = top[["pre", "post", "pre_type", "post_type", "weight", "after", "factor"]] \
                .round(2).to_dict("records")
            ek, e1k = e0, e1
        else:
            eraw, e1raw = e0, e1
    below = eraw[(eraw.weight < 5) & eraw.post.isin(t1).to_numpy()]
    fb = (e1raw.weight / eraw.weight)[below.index]
    res["below_cut_would_cross"] = dict(edges=int((below.weight * fb >= 5).sum()),
                                        syn_raw=int(below.weight[below.weight * fb >= 5].sum()))
    # per-cell matched-input ratio (F-XCONN-1 metric), raw counts
    m = vnc_matched(nr)
    S = set(m.bodyId)
    manc = pd.read_parquet(XOUT / "manc_on_mcns_edges.parquet")
    manc = manc[manc.pre.isin(S) & manc.post.isin(S)]
    min_ = manc.groupby("post").weight.sum()
    big = min_[min_ >= 500].index
    mm = eraw.pre.isin(S).to_numpy() & eraw.post.isin(big).to_numpy()
    cell = pd.DataFrame(dict(before=eraw.weight[mm].groupby(eraw.post[mm]).sum(),
                             after=e1raw.weight[mm].groupby(eraw.post[mm]).sum())).reindex(big).fillna(0)
    cell["manc"] = min_[big]
    cell["nm"] = cell.index.map(nr.set_index("bodyId").somaNeuromere.astype(str))
    rat = {}
    for nm, g in cell.groupby("nm"):
        if len(g) >= 50:
            rb, ra = g.before / g.manc, g.after / g.manc
            rat[nm] = dict(n=int(len(g)), before=round(float(rb.median()), 3), after=round(float(ra.median()), 3),
                           before_q05_q95=[round(float(rb.quantile(q)), 2) for q in (0.05, 0.95)],
                           after_q05_q95=[round(float(ra.quantile(q)), 2) for q in (0.05, 0.95)],
                           above_1_after=round(float((ra > 1).mean()), 3))
    res["per_cell_matched_input_ratio"] = rat
    # where the deficit sits: MANC synapses on matched cell pairs present in the male CNS vs absent (raw counts)
    mp = manc.merge(eraw.assign(fill=e1raw.weight)[["pre", "post", "weight", "fill"]], on=["pre", "post"],
                    how="left", suffixes=("_manc", "_mcns")).fillna({"weight_mcns": 0, "fill": 0})
    mp["nm"] = mp.post.map(nr.set_index("bodyId").somaNeuromere.astype(str))
    dec = {}
    for nm in ("T1", "T2", "T3"):
        g = mp[mp.nm.eq(nm)]
        p = g.weight_mcns > 0
        dec[nm] = dict(manc_syn=int(g.weight_manc.sum()),
                       share_on_pairs_absent_in_mcns=round(float(g.weight_manc[~p].sum() / g.weight_manc.sum()), 3),
                       mcns_over_manc_on_present_pairs=round(float(g.weight_mcns[p].sum() / g.weight_manc[p].sum()), 3),
                       after_fill_on_present_pairs=round(float(g.fill[p].sum() / g.weight_manc[p].sum()), 3))
    res["deficit_decomposition"] = dec
    # I1 and E2 -> I1
    core = nr[nr.type.isin([E2, I1])].copy()
    core["seg"] = seg(core)
    mcore = json.loads((XOUT / "manc_core.json").read_text())["core"]
    manc_i1 = {v["neuromere"] + v["side"][:1].upper(): v["in_total"] for v in mcore.values() if v["role"] == "I1"}
    i1 = []
    for _, r in core[core.type.eq(I1)].sort_values("seg").iterrows():
        e2 = core.bodyId[core.type.eq(E2) & core.seg.eq(r.seg)]
        row = dict(seg=r.seg, bodyId=int(r.bodyId), manc_in_total=manc_i1.get(r.seg))
        for nm, (a, b) in dict(raw=(eraw, e1raw), kept=(ek, e1k)).items():
            into = (a.post == r.bodyId).to_numpy()
            fe2 = into & a.pre.isin(e2).to_numpy()
            row[f"in_{nm}_before"] = int(a.weight[into].sum())
            row[f"in_{nm}_after"] = round(float(b.weight[into].sum()))
            row[f"e2_{nm}_before"] = int(a.weight[fe2].sum())
            row[f"e2_{nm}_after"] = round(float(b.weight[fe2].sum()), 1)
        i1.append(row)
    res["i1"] = i1
    res["table"] = json.loads((REPO / "data" / "params" / "t1_fill.json").read_text())
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "audit.json").write_text(json.dumps(res, indent=1, default=str))
    print(json.dumps({k: v for k, v in res.items() if k != "table"}, indent=1, default=str))

    fig, ax = plt.subplots(1, 3, figsize=(16, 4.8))
    bins = np.linspace(0, 2, 41)
    for nm, c in (("T2", "#9aa5b1"), ("T3", "#5c6b7a")):
        g = cell[cell.nm.eq(nm)]
        ax[0].hist(g.before / g.manc, bins, histtype="step", color=c, lw=1.5, label=f"{nm} (untouched)")
    g = cell[cell.nm.eq("T1")]
    ax[0].hist(g.before / g.manc, bins, histtype="step", color="#d95f02", lw=2, label="T1 before")
    ax[0].hist(g.after / g.manc, bins, histtype="step", color="#1b9e77", lw=2, label="T1 after fill")
    ax[0].axvline(1, color="k", lw=0.6)
    ax[0].set(xlabel="per-cell matched input, male CNS / MANC (raw counts)", ylabel="cells (>= 500 MANC inputs)",
              title="F-XCONN-1 metric before / after")
    ax[0].legend(frameon=False, fontsize=8)
    on = ek.post.isin(t1).to_numpy()
    fk = (e1k.weight / ek.weight).to_numpy()[on]
    ax[1].hist(np.log2(fk), np.linspace(0, 6, 49), weights=ek.weight.to_numpy()[on], color="#7570b3")
    ax[1].set(xlabel="log2 fill factor (kept edges onto T1 cells)", ylabel="synapses (before fill)",
              title=f"factor, synapse-weighted; {int((fk > 1).sum())} of {int(on.sum())} edges scaled")
    d = pd.DataFrame(i1)
    x = np.arange(len(d))
    ax[2].bar(x - 0.27, d.in_raw_before, 0.27, color="#d95f02", label="male CNS before")
    ax[2].bar(x, d.in_raw_after, 0.27, color="#1b9e77", label="after fill")
    ax[2].bar(x + 0.27, d.manc_in_total.fillna(0), 0.27, color="#666", label="MANC (all inputs from neurons)")
    ax[2].set_xticks(x, d.seg)
    ax[2].set(ylabel="I1 (IN16B036) input synapses, raw", title="I1 inputs by neuromere (only T1 is filled)")
    ax[2].legend(frameon=False, fontsize=8)
    fig.suptitle("T1F inferred T1 fill (connectome:T1|fill_from_other_animals): count audit, inferred", fontsize=11)
    fig.tight_layout()
    FIG.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(FIG, dpi=110)
    print("wrote", FIG)


if __name__ == "__main__":
    main()
