"""Ladder rung 8 step 1 (s12, N29): short-term plasticity per connection class.

One presynaptic ORN-typed cell drives a PN-class and an LN-class cell; each
spike's delivered amplitude is read from the delay buffer. Claims: switch 0
builds nothing and values above 1 are refused; with tau_facil = 0 the per-edge
rule equals the per-cell depression rule; each edge follows the published
single-component model A -> f A per spike with its own recovery (Nagel 2015 for
ORN->PN, Nagel & Wilson 2016 for ORN->LN); facilitation gives the analytic
Markram 1998 paired-pulse ratio. The table rows are fits, so these are
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
KEY = "synapse:all|per_synapse_parameters"


def _conn():
    nrn = pd.DataFrame({"bodyId": [10, 11, 12], "type": ["ORN_DM6", "DM6_adPN", "lLN2F_a"],
                        "predictedNt": "acetylcholine", "superclass": "x",
                        "class": ["ORN", "ALPN", "ALLN"]})
    return Connectome(nrn, np.array([0, 2, 2, 2], np.int64), np.array([1, 2], np.int32),
                      np.ones(2, np.float32), np.ones(3, np.float32), np.ones(2, np.float32))


def _net(std_u=0.0, std_tau=893.0, stp=None):
    f = lambda v: np.full(3, v, np.float32)
    p = lif.LIFParams(f(20.0), f(-52.0), f(-45.0), f(-52.0), f(2.0), 5.0, np.ones(3, np.int64),
                      0.0, False, std_u=np.array([std_u, 0, 0], np.float32),
                      std_tau_rec=f(std_tau), stp_edge=stp)
    return lif.Network(_conn(), p, DT)


def _amps(net, times_ms):
    """Amplitude delivered to cells 1 and 2 by each presynaptic spike at times_ms."""
    want = {int(round(t / DT)) for t in times_ms}
    out = []
    for s in range(max(want) + 1):
        spk = net.step(kick=(np.array([0]), 50.0) if s in want else None)
        if s in want:
            assert 0 in spk
            out.append(net.delay[0, 1:].copy())   # D = 1: this step's scheduled input
    return np.array(out)


def _stp(U, tau_rec, tau_f):
    return {"idx": np.array([0, 1]), "U": np.asarray(U, float),
            "tau_rec": np.asarray(tau_rec, float), "tau_f": np.asarray(tau_f, float)}


def test_switch_neutral_builds_nothing_and_unbuilt_values_are_refused():
    assert lif._stp_connections(Registry(Policy.MINIMAL), _conn()) is None
    r = Registry(Policy.MINIMAL)
    r.overrides[KEY] = 2.0
    with pytest.raises(NotImplementedError):
        lif._stp_connections(r, _conn())


def test_switch_on_applies_the_table_rows_by_target_class():
    r = Registry(Policy.MINIMAL)
    r.overrides[KEY] = 1.0
    e = lif._stp_connections(r, _conn())
    assert e["idx"].tolist() == [0, 1]
    assert np.allclose(e["U"], [0.22, 0.25]) and np.allclose(e["tau_rec"], [893, 1566])
    inv = r.inventory()
    rows = inv[inv.property == "stp_U"]
    assert set(rows.status) == {Status.DERIVED.value} or set(rows.status) == {Status.DERIVED}


def test_table_rows_are_sourced_and_in_range():
    t = pd.read_csv(REPO / "data/params/stp_connections.csv", comment="#")
    assert len(t) >= 2
    for r in t.itertuples():
        Status(r.basis)
        assert 0 < r.U <= 1 and r.tau_rec_ms > 0 and r.tau_facil_ms >= 0
        assert isinstance(r.source, str) and r.source.strip()
        lif._stp_cells(_conn().neurons, r.pre), lif._stp_cells(_conn().neurons, r.post)


def test_per_edge_rule_equals_per_cell_depression_without_facilitation():
    times = [5, 25, 40, 200, 210, 1000, 1003]
    a = _amps(_net(std_u=0.22), times)
    b = _amps(_net(stp=_stp([0.22, 0.22], [893, 893], [0, 0])), times)
    assert a[0, 0] == pytest.approx(1.0)
    assert np.allclose(a, b, rtol=2e-4)
    assert a[2, 0] < 0.7      # it does depress


def test_each_edge_follows_its_published_depression_fit():
    times = [5 + 100 * k for k in range(10)]     # 10 Hz, the protocol of both papers
    got = _amps(_net(stp=_stp([0.22, 0.25], [893, 1566], [0, 0])), times)
    for col, (f, tau) in enumerate([(0.78, 893.0), (0.75, 1566.0)]):
        a = [1.0]
        for _ in range(9):
            a.append(1.0 - (1.0 - f * a[-1]) * np.exp(-100.0 / tau))
        assert np.allclose(got[:, col], a, rtol=1e-5)
    assert got[-1, 1] < got[-1, 0]   # LN input depresses more (Nagel & Wilson 2016)


def test_facilitation_gives_the_markram_paired_pulse_ratio():
    U, tf, isi = 0.1, 100.0, 20.0
    got = _amps(_net(stp=_stp([U, U], [1e-6, 1e-6], [tf, tf])), [5, 5 + isi])
    um = U * np.exp(-isi / tf)
    assert got[1, 0] / got[0, 0] == pytest.approx((um + U * (1 - um)) / U, rel=1e-5)
