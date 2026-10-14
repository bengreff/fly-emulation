"""s14 (fly2): CT1 as per-column compartments (connectome.ct1_compartments, cell_type:CT1|compartments_by_column).

A six-cell graph with a patched raw pull: CT1_L receives Mi1 in two medulla columns and drives T4a there,
drives T5a in one lobula column, drives LT33 in a lobula column and a lobula-plate column, and contacts
CT1_R. Claims: switch 0 changes nothing; switch 1 makes one compartment per (cell, M10/Lo1, column),
splits each CT1 connection by its column ROIs, leaves synapses outside ME/LO column ROIs and CT1 -> CT1
on the trunk, keeps every synapse and the cell's size, copies the sign; and the flyvis CT1(M10)/CT1(Lo1)
pair rows then select the compartment edges only. Structural checks, not validation.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "src"))

from flyemu import connectome, lif  # noqa: E402
from flyemu.registry import Policy, Registry  # noqa: E402

KEY = "cell_type:CT1|compartments_by_column"
CT1L, CT1R, MI1, T4A, T5A, LT33 = 10, 11, 20, 30, 40, 50


def _cols(**k):
    d = {c.replace("__", "_"): {"post": v} for c, v in k.items()}
    d["ME(R)"] = {"post": sum(k.values())}          # a non-column ROI the split must ignore
    return json.dumps(d)


RAW = [  # pre, post, weight, roiInfo, direction
    (MI1, CT1L, 6, _cols(ME_R_col_01_01=4, ME_R_col_01_02=2), "in"),
    (CT1L, T4A, 7, _cols(ME_R_col_01_01=5, ME_R_col_01_02=1), "out"),     # 1 synapse outside the columns
    (CT1L, T5A, 5, _cols(LO_R_col_01_01=5), "out"),
    (CT1L, LT33, 5, _cols(LO_R_col_01_01=2, LOP_R_col_01_01=3), "out"),  # lobula plate stays on the trunk
    (CT1L, CT1R, 5, _cols(ME_R_col_01_01=5), "out"),
    (T4A, CT1L, 3, _cols(ME_R_col_01_01=3), "in"),                        # below the threshold
]


@pytest.fixture
def raw(tmp_path, monkeypatch):
    d = pd.DataFrame(RAW, columns=["pre", "post", "weight", "roiInfo", "direction"])
    for k in ("in", "out"):
        d[d.direction == k].to_parquet(tmp_path / f"ct1_{k}.parquet")
    monkeypatch.setattr(connectome, "CT1_RAW", tmp_path)
    nrn = pd.DataFrame({"bodyId": [CT1L, CT1R, MI1, T4A, T5A, LT33],
                        "type": ["CT1", "CT1", "Mi1", "T4a", "T5a", "LT33"],
                        "instance": ["CT1_L", "CT1_R", "Mi1_R", "T4a_R", "T5a_R", "LT33_R"],
                        "superclass": "ol_intrinsic", "class": None, "status": "Traced",
                        "size": [1000.0, 800.0, 10.0, 10.0, 10.0, 50.0],
                        "predictedNt": ["gaba", "gaba", "acetylcholine", "acetylcholine", "acetylcholine",
                                        "acetylcholine"]})
    edges = pd.concat([d[["pre", "post", "weight"]],
                       pd.DataFrame({"pre": [MI1], "post": [T4A], "weight": [9]})], ignore_index=True)
    return nrn, edges


def _build(raw, on):
    r = Registry(Policy.MINIMAL)
    if on:
        r.overrides[KEY] = 1.0
    return connectome.build(r, neurons=raw[0], edges=raw[1], min_synapses=5), r


def _edges(c):
    pre = c.neurons.bodyId.to_numpy()[np.repeat(np.arange(c.n), np.diff(c.indptr))]
    post = c.neurons.bodyId.to_numpy()[c.indices]
    return {(int(a), int(b)): float(w) for a, b, w in zip(pre, post, c.weight_syn)}


def test_switch_neutral_changes_nothing(raw):
    c, _ = _build(raw, False)
    assert c.n == 6 and "ct1_compartment" not in c.neurons
    assert _edges(c) == {(MI1, CT1L): 6, (CT1L, T4A): 7, (CT1L, T5A): 5, (CT1L, LT33): 5, (CT1L, CT1R): 5,
                         (MI1, T4A): 9}


def test_split_by_column(raw):
    c, _ = _build(raw, True)
    nn = c.neurons
    comp = nn[nn.ct1_compartment.isin(["M10", "Lo1"])].set_index("bodyId")
    assert sorted(comp.instance) == ["CT1_L/Lo1/LO_R_col_01_01", "CT1_L/M10/ME_R_col_01_01",
                                     "CT1_L/M10/ME_R_col_01_02"]
    assert (comp.compartment_of == CT1L).all() and (comp.type == "CT1").all()
    sid = {i.split("/", 2)[2]: b for b, i in comp.instance.items()}
    m1, m2, l1 = sid["ME_R_col_01_01"], sid["ME_R_col_01_02"], sid["LO_R_col_01_01"]
    assert _edges(c) == {(MI1, m1): 4, (MI1, m2): 2, (m1, T4A): 5, (m2, T4A): 1, (CT1L, T4A): 1,
                         (l1, T5A): 5, (l1, LT33): 2, (CT1L, LT33): 3, (CT1L, CT1R): 5, (MI1, T4A): 9}
    ix = nn.index[nn.type.eq("CT1")]
    assert np.all(c.sign[ix] == -1)
    assert nn.loc[nn.compartment_of.eq(CT1L), "size"].sum() == pytest.approx(1000.0)
    assert nn.loc[nn.bodyId.eq(CT1R), "size"].item() == pytest.approx(800.0)   # only CT1 -> CT1: unchanged


def test_flyvis_ct1_rows_select_compartment_edges_only(raw):
    c, r = _build(raw, True)
    r.overrides["cell_type:all|optic_lobe_flyvis_pair_strength"] = 1.0
    fe = lif._flyvis_pairs(r, c)
    e = list(_edges(c))
    got = {e[i] for i in fe["idx"]}
    nn = c.neurons.set_index("bodyId")
    kind = lambda b: nn.ct1_compartment.get(b, "") or nn.type[b]
    assert {(kind(a), kind(b)) for a, b in got} == {("Mi1", "M10"), ("M10", "T4a"), ("Lo1", "T5a"),
                                                     ("Mi1", "T4a")}
    tab = pd.read_csv(REPO / "data" / "params" / lif.FV_PAIR_TABLE, comment="#").set_index("flyvis_pair").alpha
    a = dict(zip([e[i] for i in fe["idx"]], fe["alpha"]))
    m1 = nn.index[nn.instance.eq("CT1_L/M10/ME_R_col_01_01")][0]
    assert a[(MI1, m1)] == pytest.approx(tab["Mi1->CT1(M10)"])
