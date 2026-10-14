"""N29 (s13, fly2): fast receptor decay per connection class.

A seven-cell graph: an ORN drives a PN (row) and an LN (no row); a PN, a spiking GABAergic
cell and the graded APL drive one Kenyon cell. Claims: switch 0 builds nothing; switch 1
assigns each edge its row's decay (later rows win, nt: selects by transmitter); a spike's
current then decays with the row's tau while its charge equals the tau_s case; graded
presynaptic edges keep tau_s; silencing removes the moved weight; conductance synapses are
refused. The rows are measurements from culture and a compartmental fit, so these are
implementation checks, not validation.
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
from flyemu.registry import Policy, Registry, Status  # noqa: E402

DT = 0.1
KEY = "synapse:all|receptor_kinetics_per_connection"
N = 7


def _conn():
    nrn = pd.DataFrame({
        "bodyId": np.arange(10, 10 + N),
        "type": ["ORN_DM6", "DM6_adPN", "lLN2F_a", "DA1_lPN", "KCg-m", "LHLN_x", "APL"],
        "predictedNt": ["acetylcholine"] * 5 + ["gaba", "gaba"], "superclass": "x",
        "class": ["ORN", "ALPN", "ALLN", "ALPN", "Kenyon_Cell", "LHLN", "MBIN"]})
    # edges by presynaptic cell: 0->1, 0->2, 3->4, 5->4, 6->4
    return Connectome(nrn, np.array([0, 2, 2, 2, 3, 3, 4, 5], np.int64), np.array([1, 2, 4, 4, 4], np.int32),
                      np.ones(5, np.float32), np.array([1, 1, 1, 1, 1, -1, -1], np.float32),
                      np.ones(5, np.float32))


def _kin(on=True):
    r = Registry(Policy.MINIMAL)
    if on:
        r.overrides[KEY] = 1.0
    return lif._receptor_kinetics(r, _conn()), r


def _net(kin=None, cond=False):
    f = lambda v: np.full(N, v, np.float32)
    graded = np.zeros(N, bool)
    graded[6] = True
    p = lif.LIFParams(f(20.0), f(-52.0), f(-45.0), f(-52.0), f(2.0), 5.0, np.ones(N, np.int64), 0.0, False,
                      graded=graded, cond=cond, kin_edge=kin)
    return lif.Network(_conn(), p, DT)


def _kc_current(net, steps=1000):
    """Synaptic current into the Kenyon cell (fast plus channels) after one PN spike at step 0."""
    out = []
    for s in range(steps):
        net.step(kick=(np.array([3]), 50.0) if s == 0 else None)
        out.append(net.i_syn[4] + sum(c["i"][4] for c in net.chan))
    return np.array(out, np.float64)


def test_switch_neutral_builds_nothing():
    kin, _ = _kin(on=False)
    assert kin is None
    net = _net(None)
    assert net.chan == []


def test_switch_on_assigns_each_edge_its_row():
    kin, reg = _kin()
    assert kin["idx"].tolist() == [0, 2, 3, 4]           # the ORN->LN edge has no row
    assert np.allclose(kin["tau"], [1.1, 1.4, 3.7, 3.7])
    inv = reg.inventory()
    rows = inv[inv.property == "receptor_tau_decay"]
    assert len(rows) == 3 and set(rows.status.astype(str)) <= {Status.INFERRED.value, str(Status.INFERRED)}


def test_a_spike_decays_with_the_row_tau_and_keeps_its_charge():
    kin, _ = _kin()
    base, new = _kc_current(_net(None)), _kc_current(_net(kin))
    k = int(np.argmax(new))
    assert new[k] > 0 and new[k + 10] / new[k] == pytest.approx(np.exp(-10 * DT / 1.4), rel=1e-4)
    assert base[k + 10] / base[k] == pytest.approx(np.exp(-10 * DT / 5.0), rel=1e-4)
    assert new.sum() == pytest.approx(base.sum(), rel=1e-4)   # same charge, faster time course
    assert new[k] > 3 * base[k]


def test_graded_inputs_keep_tau_s_and_silencing_removes_moved_weight():
    kin, _ = _kin()
    net = _net(kin)
    kc = [c for c in net.chan if c.get("kin")]
    assert sorted(c["name"] for c in kc) == ["kin1.1", "kin1.4", "kin3.7"]
    assert net.W_graded[4, 0] != 0 and all(c["w"][4] == 0 for c in kc)    # APL edge stays in W_graded
    assert net.w[0] == 0 and net.w[2] == 0 and net.w[3] == 0 and net.w[1] != 0
    net.silence([3])
    assert all(c["w"][2] == 0 for c in kc)


def test_conductance_synapses_are_refused():
    kin, _ = _kin()
    with pytest.raises(NotImplementedError):
        _net(kin, cond=True)


def test_table_rows_are_sourced_and_in_range():
    t = pd.read_csv(REPO / "data/params/receptor_kinetics.csv", comment="#")
    assert len(t) >= 3
    for r in t.itertuples():
        assert Status(r.basis) in (Status.MEASURED, Status.DERIVED, Status.INFERRED)
        assert 0.1 <= r.tau_decay_ms <= 50
        assert isinstance(r.source, str) and r.source.strip() and isinstance(r.note, str)
        lif._stp_cells(_conn().neurons, r.pre), lif._stp_cells(_conn().neurons, r.post)
