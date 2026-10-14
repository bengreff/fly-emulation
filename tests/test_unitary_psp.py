"""s14 (fly2): measured unitary PSP per identified connection (data/params/unitary_psp.csv).

A four-cell graph: PSI (acetylcholine) drives one DLMn a, b and one DLMn c-f; an unrelated
cholinergic cell also drives the DLMn a, b. Claims: switch 0 builds nothing and keeps every weight;
switch 1 sets only the PSI edges, and one PSI spike then gives each DLMn a passive PSP peak equal to
the table's 4.71 mV; the other edge keeps its count x scale weight; a sign that disagrees with the
recording (PSI with no transmitter) is refused; conductance synapses are refused. The value is
Fayyazuddin 2006's; these are implementation checks, not validation.
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
KEY = "connectome:identified|unitary_psp_from_recordings"
N = 4
PSP = 4.71


def _conn(psi_sign=1.0):
    nrn = pd.DataFrame({"bodyId": np.arange(10, 10 + N), "type": ["PSI", "DLMn a, b", "DLMn c-f", "IN_x"],
                        "predictedNt": ["acetylcholine", "glutamate", "glutamate", "acetylcholine"],
                        "superclass": "x", "class": "x"})
    # edges by presynaptic cell: 0->1, 0->2, 3->1
    return Connectome(nrn, np.array([0, 2, 2, 2, 3], np.int64), np.array([1, 2, 1], np.int32),
                      np.array([17.0, 40.0, 5.0], np.float32), np.array([psi_sign, -1, -1, 1], np.float32),
                      np.full(3, 0.2, np.float32))


def _psp(on=True, psi_sign=1.0):
    r = Registry(Policy.MINIMAL)
    if on:
        r.overrides[KEY] = 1.0
    return lif._unitary_psp(r, _conn(psi_sign)), r


def _net(pe=None, cond=False, tau_m=20.0):
    f = lambda v: np.full(N, v, np.float32)
    p = lif.LIFParams(f(tau_m), f(-52.0), f(-45.0), f(-52.0), f(2.0), 5.0, np.ones(N, np.int64), 0.0, False,
                      cond=cond, psp_edge=pe)
    return lif.Network(_conn(), p, DT)


def _peak(net, pre, post, steps=600):
    v0, vmax = float(net.v[post]), -np.inf
    for s in range(steps):
        net.step(kick=(np.array([pre]), 50.0) if s == 0 else None)
        vmax = max(vmax, float(net.v[post]))
    return vmax - v0


def test_switch_neutral_builds_nothing():
    pe, _ = _psp(on=False)
    assert pe is None
    assert np.allclose(_net(None).w, [17 * 0.2, 40 * 0.2, 5 * 0.2])


def test_switch_on_sets_the_recorded_peak_on_the_psi_edges_only():
    pe, reg = _psp()
    assert pe["idx"].tolist() == [0, 1]
    assert np.allclose(pe["psp_mv"], [PSP, PSP])
    inv = reg.inventory()
    rows = inv[inv.property == "unitary_psp_peak"]
    assert sorted(rows.status.astype(str)) == sorted([str(Status.MEASURED.value), str(Status.INFERRED.value)])
    for tau_m in (20.0, 4.4):
        net = _net(pe, tau_m=tau_m)
        assert net.w[2] == pytest.approx(5 * 0.2)               # the other edge keeps count x scale
        assert _peak(net, 0, 1) == pytest.approx(PSP, rel=1e-3)
        assert _peak(_net(pe, tau_m=tau_m), 0, 2) == pytest.approx(PSP, rel=1e-3)


def test_sign_disagreeing_with_the_recording_is_refused():
    with pytest.raises(ValueError, match="nt_from_physiology"):
        _psp(psi_sign=0.0)


def test_conductance_synapses_refused():
    pe, _ = _psp()
    with pytest.raises(NotImplementedError):
        _net(pe, cond=True)
