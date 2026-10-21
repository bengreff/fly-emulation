"""s20 (fly2, N30 first build): an axon compartment where spikes start, for the cells of
data/params/two_compartment.csv (pre-registered DECISIONS 20 Oct 23:30).

A five-cell graph: PSI (acetylcholine) drives one DLMn a, b and one DLMn c-f; an unrelated
cholinergic cell also drives the DLMn a, b, which inhibits a fifth cell. Claims: switch 0 builds
nothing; switch 1 lists both DLMn and moves only the PSI edges onto their axons; with the measured
unitary PSP on, one PSI spike gives a SOMA peak equal to the table's 4.71 mV (axon passive) while the
axon peak is larger; with the shared threshold the DLMn spike starts on the axon, the soma is never
reset, and the spike reaches the DLMn's own target; a large soma input still fires the cell through the
axon; a run override replaces a class value; the GPU, conductance synapses and a slow copy on an axon
edge are refused. These are implementation checks, not validation. The mechanism tests pin the class values to
the s20 guessed-geometry pair (q 0.07, rho 1.6) by override, where the axon fires; the table's own values
(s21 option B, derived from the MN5 skeletons) are checked where the table is read.
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
KEY = "cell_type:all|two_compartments_where_point_fails"
PSP_KEY = "connectome:identified|unitary_psp_from_recordings"
N = 5
PSP = 4.71


def _conn():
    nrn = pd.DataFrame({"bodyId": np.arange(10, 10 + N),
                        "type": ["PSI", "DLMn a, b", "DLMn c-f", "IN_x", "IN_z"],
                        "predictedNt": ["acetylcholine", "glutamate", "glutamate", "acetylcholine", "acetylcholine"],
                        "superclass": "x", "class": "x"})
    # edges by presynaptic cell: 0->1, 0->2, 1->4, 3->1
    return Connectome(nrn, np.array([0, 2, 3, 3, 4, 4], np.int64), np.array([1, 2, 4, 1], np.int32),
                      np.array([17.0, 40.0, 10.0, 5.0], np.float32), np.array([1, -1, -1, 1, 1], np.float32),
                      np.full(4, 0.2, np.float32))


S20 = {"cell_class:MN|axon_membrane_share": 0.07, "cell_class:MN|soma_axon_coupling": 1.6}


def _reg(two=True, psp=True, s20=True, **over):
    r = Registry(Policy.MINIMAL)
    if s20:
        r.overrides.update(S20)
    if two:
        r.overrides[KEY] = 1.0
    if psp:
        r.overrides[PSP_KEY] = 1.0
    r.overrides.update(over)
    return r


def _net(reg, cond=False, v_th=-45.0):
    """v_th is the DLMn threshold (soma and axon); the other cells keep -45 mV."""
    c = _conn()
    f = lambda v: np.full(N, v, np.float32)
    th = f(-45.0)
    th[[1, 2]] = v_th
    p = lif.LIFParams(f(20.0), f(-52.0), th, f(-52.0), f(2.0), 5.0, np.ones(N, np.int64), 0.0, False,
                      cond=cond, psp_edge=lif._unitary_psp(reg, c), two_comp=lif._two_compartments(reg, c))
    return lif.Network(c, p, DT)


def _run(net, kick_cell, kick_mv, steps=600):
    vs, va, sp = [], [], []
    for s in range(steps):
        out = net.step(kick=(np.array([kick_cell]), kick_mv) if s == 0 else None)
        vs.append(net.v.copy())
        va.append(net.c2["v"].copy() if net.c2 is not None else None)
        sp.append(out)
    return np.array(vs), (np.array(va) if net.c2 is not None else None), sp


def test_switch_neutral_builds_nothing():
    reg = _reg(two=False)
    assert lif._two_compartments(reg, _conn()) is None
    net = _net(reg)
    assert net.c2 is None


def test_only_the_psi_edges_land_on_the_axons():
    reg = _reg(psp=False, s20=False)
    tc = lif._two_compartments(reg, _conn())
    assert tc["cells"].tolist() == [1, 2] and tc["edge_idx"].tolist() == [0, 1]
    assert np.allclose(tc["q"], 0.104) and np.allclose(tc["rho"], 3.80)
    net = _net(reg)
    # an axon edge keeps its synaptic charge (weight / q); the other edges keep count x scale
    assert np.allclose(net.w, [17 * 0.2 / 0.104, 40 * 0.2 / 0.104, -10 * 0.2, 5 * 0.2], rtol=1e-6)
    inv = reg.inventory()
    q = inv[inv.property == "axon_membrane_share"]
    assert len(q) == 1 and str(q.status.iloc[0]) == str(Status.INFERRED.value)
    assert "EM geometry" in str(q.method.iloc[0])
    site = inv[inv.property == "spike_initiation_compartment"]
    assert sorted(site.status.astype(str)) == sorted([str(Status.MEASURED.value), str(Status.INFERRED.value)])


def test_soma_peak_equals_the_recorded_value_and_the_axon_sees_more():
    net = _net(_reg(), v_th=0.0)          # axon threshold out of reach: the passive pair, as calibrated
    vs, va, sp = _run(net, 0, 50.0)
    for cell in (1, 2):
        j = net.c2["pos"][cell]
        soma, axon = vs[:, cell].max() + 52.0, va[:, j].max() + 52.0
        assert soma == pytest.approx(PSP, rel=1e-3)
        assert axon > 2.0 * soma
    assert all(cell not in s for s in sp for cell in (1, 2))


def test_spike_starts_on_the_axon_and_reaches_the_target():
    net = _net(_reg())
    vs, va, sp = _run(net, 0, 50.0, steps=300)
    first = {c: next(i for i, s in enumerate(sp) if c in s) for c in (1, 2)}
    assert all(first[c] < 30 for c in (1, 2))            # PSI delay 1 step + axon rise, within 3 ms
    assert -52.0 + 0.05 < vs[first[1], 1] < -45.0        # soma depolarised, not reset, below threshold
    assert vs[first[1] + 5:, 4].min() < -52.0 - 1e-3     # DLMn a, b's inhibitory output arrived


def test_a_large_soma_input_fires_the_cell_through_the_axon():
    net = _net(_reg())
    _, _, sp = _run(net, 3, 0.0, steps=1)                # settle one step
    net.v[1] = -30.0                                     # soma far above threshold; soma cannot spike
    hits = []
    for _ in range(40):
        out = net.step()
        hits.append(1 in out)
    assert any(hits)


def test_override_replaces_a_class_value_as_a_run_override():
    reg = _reg(**{"cell_class:MN|axon_membrane_share": 0.15, "cell_class:MN|soma_axon_coupling": 25.0})
    tc = lif._two_compartments(reg, _conn())
    assert np.allclose(tc["q"], 0.15) and np.allclose(tc["rho"], 25.0)
    net = _net(reg, v_th=0.0)
    vs, _, _ = _run(net, 0, 50.0)
    assert vs[:, 1].max() + 52.0 == pytest.approx(PSP, rel=1e-3)
    inv = reg.inventory()
    assert str(inv[inv.property == "axon_membrane_share"].method.iloc[0]) == "run override"


def test_refusals():
    with pytest.raises(NotImplementedError):
        _net(_reg(psp=False), cond=True)
    net = _net(_reg())
    net.chan.append({"w": np.ones(4, np.float32)})
    with pytest.raises(NotImplementedError, match="slow copy"):
        net._two_comp_refusals()
    pytest.importorskip("jax")
    from flyemu.gpu.batched import BatchedNetwork
    with pytest.raises(NotImplementedError, match="N30"):
        BatchedNetwork(_net(_reg(psp=False)), B=1)


def test_general_compartment_count_still_refused():
    with pytest.raises(NotImplementedError, match="n_compartments"):
        lif._two_compartments(_reg(**{"cell_type:all|n_compartments": 3.0}), _conn())
