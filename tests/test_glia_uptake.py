"""N33 (s23, DECISIONS 24 Oct 02:28): astrocytic uptake sets the fast decay of glutamatergic edges.

A six-cell graph: spiking glutamatergic cells 0 and 1 drive cells 2 and 3, a cholinergic cell 4 and a graded
glutamatergic cell 5 drive cell 2. Claims: switch 0 and switch 1 at healthy uptake build nothing; a GAT uptake
other than 1 and an Eaat1 uptake outside 0-1 are refused; with uptake lowered, a glutamatergic edge decays with
tau R / (1 + (R - 1) u) from its N29 row decay where it has one, else tau_s, and keeps its u = 1 peak, while
cholinergic and graded edges are unchanged; conductance synapses are refused. R is MacNamee 2016's larval ratio,
so these are implementation checks, not validation.
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "src"))

from flyemu import lif  # noqa: E402
from flyemu.connectome import Connectome  # noqa: E402
from flyemu.registry import Policy, Registry  # noqa: E402

DT = 0.1
N = 6
R = 2.9


def _conn():
    nrn = pd.DataFrame({
        "bodyId": np.arange(10, 10 + N), "type": ["GLU_a", "GLU_b", "X", "Y", "ACH_a", "GLU_g"],
        "predictedNt": ["glutamate", "glutamate", "acetylcholine", "acetylcholine", "acetylcholine", "glutamate"],
        "superclass": "x", "class": "x"})
    # edges by presynaptic cell: 0->2, 1->3, 4->2, 5->2
    return Connectome(nrn, np.array([0, 1, 2, 2, 2, 3, 4], np.int64), np.array([2, 3, 2, 2], np.int32),
                      np.ones(4, np.float32), np.array([1, 1, 1, 1, 1, 1], np.float32), np.ones(4, np.float32))


def _uptake(on=True, **state):
    r = Registry(Policy.MINIMAL)
    if on:
        r.overrides["state:glia|uptake_model"] = 1.0
    for k, v in state.items():
        r.overrides[f"state:glia|{k}"] = v
    return lif._glia_uptake(r, _conn()), r


def _net(up=None, kin=None, cond=False):
    f = lambda v: np.full(N, v, np.float32)
    graded = np.zeros(N, bool)
    graded[5] = True
    p = lif.LIFParams(f(20.0), f(-52.0), f(-45.0), f(-52.0), f(2.0), 5.0, np.ones(N, np.int64), 0.0, False,
                      graded=graded, cond=cond, kin_edge=kin, uptake_edge=up)
    return lif.Network(_conn(), p, DT)


def _current(net, cell, post, steps=1500):
    """Synaptic current into `post` (fast plus channels) after one spike of `cell` at step 0."""
    out = []
    for s in range(steps):
        net.step(kick=(np.array([cell]), 50.0) if s == 0 else None)
        out.append(net.i_syn[post] + sum(c["i"][post] for c in net.chan))
    return np.array(out, np.float64)


def test_switch_neutral_and_healthy_uptake_build_nothing():
    assert _uptake(on=False)[0] is None
    up, reg = _uptake()                         # switch on, uptake at the healthy 1
    assert up is None and _net(up).chan == []
    inv = reg.inventory()
    assert (inv.property == "eaat1_block_decay_ratio").any()   # R is read whenever the switch is on


def test_gat_loss_and_out_of_range_uptake_are_refused():
    with pytest.raises(NotImplementedError):
        _uptake(gat_uptake=0.5)
    with pytest.raises(ValueError):
        _uptake(eaat1_uptake=1.5)


def test_block_slows_glutamatergic_decay_and_keeps_its_peak():
    up, _ = _uptake(eaat1_uptake=0.0)
    assert up["idx"].tolist() == [0, 1, 3] and up["factor"] == pytest.approx(R)
    base, new = _current(_net(None), 0, 2), _current(_net(up), 0, 2)
    k = int(np.argmax(new))
    assert new[k] == pytest.approx(base[k], rel=1e-4)                       # peak kept
    assert new[k + 10] / new[k] == pytest.approx(np.exp(-10 * DT / (R * 5.0)), rel=1e-4)
    q = (1 - np.exp(-DT / 5.0)) / (1 - np.exp(-DT / (R * 5.0)))
    assert new.sum() / base.sum() == pytest.approx(q, rel=2e-2)             # charge grows with the decay
    assert np.allclose(_current(_net(up), 4, 2), _current(_net(None), 4, 2))   # cholinergic edge unchanged
    net = _net(up)
    assert [c["name"] for c in net.chan] == [f"upt{R * 5.0:g}"]
    assert net.chan[0]["w"][3] == 0 and net.W_graded[2, 0] != 0             # graded edge stays in W_graded


def test_partial_uptake_scales_the_n29_row_decay():
    up, _ = _uptake(eaat1_uptake=0.5)
    fac = R / (1 + (R - 1) * 0.5)
    assert up["factor"] == pytest.approx(fac)
    kin = {"idx": np.array([0]), "tau": np.array([2.0])}                    # an N29 row on edge 0->2
    base, new = _current(_net(None, kin), 0, 2), _current(_net(up, kin), 0, 2)
    k = int(np.argmax(new))
    assert new[k] == pytest.approx(base[k], rel=1e-4)
    assert new[k + 10] / new[k] == pytest.approx(np.exp(-10 * DT / (2.0 * fac)), rel=1e-4)
    net = _net(up, kin)
    assert all(c["w"][0] == 0 for c in net.chan if c["name"].startswith("kin"))   # moved out of the N29 channel
    names = sorted(c["name"] for c in net.chan if c["name"].startswith("upt"))
    assert names == sorted([f"upt{2.0 * fac:g}", f"upt{5.0 * fac:g}"])


def test_conductance_synapses_are_refused():
    up, _ = _uptake(eaat1_uptake=0.0)
    with pytest.raises(NotImplementedError):
        _net(up, cond=True)
