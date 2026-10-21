"""T1A count audit (fly2, DECISIONS 20 Oct 22:44): level 2 vs level 1 of connectome:T1|fill_from_other_animals.

At the raw cut (1) and the model cut (5): edges and synapses added onto T1 cells; the per-cell matched-input ratio
against MANC (the F-XCONN-1 metric, as t1_fill_audit.py, raw counts); I1 (IN16B036) input and E2 -> I1; and how
many added synapses land on cell pairs that MANC's body-matched graph also connects (a check of the guessed
partner identity). Writes runs/s20/t1fill/audit_add.json.

    uv run python scripts/connectome/t1_add_audit.py
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import pandas as pd

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "src"))
sys.path.insert(0, str(REPO / "scripts" / "probes"))

from flyemu import connectome  # noqa: E402
from flyemu.registry import Policy, Registry  # noqa: E402
from xconn_counts import OUT as XOUT, vnc_matched  # noqa: E402

OUT = REPO / "runs" / "s20" / "t1fill"
KEY = "connectome:T1|fill_from_other_animals"
E2, I1 = "INXXX466", "IN16B036"


def level(nr: pd.DataFrame, e: pd.DataFrame, lvl: float, cut: int) -> pd.DataFrame:
    r = Registry(Policy.MINIMAL)
    r.overrides[KEY] = lvl
    return connectome.t1_fill(r, nr, e, cut)


def main() -> None:
    nr, ed = connectome.load_tables()
    nr = nr[(nr.status == "Traced") | nr.type.notna()].reset_index(drop=True)
    ed = ed[ed.pre.isin(nr.bodyId) & ed.post.isin(nr.bodyId)].reset_index(drop=True)
    ty = nr.set_index("bodyId").type
    t1 = set(nr.bodyId[nr.somaNeuromere.astype(str).eq("T1") & nr.type.notna()])
    m = vnc_matched(nr)
    S = set(m.bodyId)
    manc = pd.read_parquet(XOUT / "manc_on_mcns_edges.parquet")
    manc = manc[manc.pre.isin(S) & manc.post.isin(S)]
    min_ = manc.groupby("post").weight.sum()
    big = min_[min_ >= 500].index
    res = {}
    for cut in (1, 5):
        e0 = ed[ed.weight >= cut].reset_index(drop=True)
        e1, e2 = level(nr, e0, 1.0, cut), level(nr, e0, 2.0, cut)
        new = e2.iloc[len(e1):]
        assert len(e2) >= len(e1) and (e2.weight.iloc[:len(e1)].to_numpy() == e1.weight.to_numpy()).all()
        assert new.post.isin(t1).all() and not new.merge(e0, on=["pre", "post"]).shape[0], "added an existing pair"
        on1 = e1.post.isin(t1)
        hit = new.merge(manc[["pre", "post"]], on=["pre", "post"])
        d = dict(edges_added=int(len(new)), syn_added=round(float(new.weight.sum())),
                 syn_onto_t1_level1=round(float(e1.weight[on1].sum())),
                 syn_onto_t1_level2=round(float(e1.weight[on1].sum() + new.weight.sum())),
                 type_pairs_added=int(len(new.assign(a=new.pre.map(ty), b=new.post.map(ty))[["a", "b"]]
                                          .drop_duplicates())),
                 added_syn_on_pairs_manc_connects=round(float(hit.weight.sum())),
                 added_edges_on_pairs_manc_connects=int(len(hit)))
        for name, e in (("level1", e1), ("level2", e2)):
            i1 = e.post.map(ty).eq(I1)
            d[f"I1_input_{name}"] = round(float(e.weight[i1].sum()))
            d[f"E2_to_I1_{name}"] = round(float(e.weight[i1 & e.pre.map(ty).eq(E2)].sum()))
        if cut == 1:
            rat = {}
            for name, e in (("level1", e1), ("level2", e2)):
                mm = e.pre.isin(S).to_numpy() & e.post.isin(big).to_numpy()
                c = e.weight[mm].groupby(e.post[mm]).sum().reindex(big).fillna(0) / min_[big]
                nm = pd.Series(big, index=big).map(nr.set_index("bodyId").somaNeuromere.astype(str))
                rat[name] = {k: round(float(g.median()), 3) for k, g in c.groupby(nm) if len(g) >= 50}
            d["per_cell_matched_input_ratio"] = rat
        res[f"cut{cut}"] = d
    (OUT / "audit_add.json").write_text(json.dumps(res, indent=1))
    print(json.dumps(res, indent=1))


if __name__ == "__main__":
    main()
