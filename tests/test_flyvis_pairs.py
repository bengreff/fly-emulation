"""s14 (fly2): flyvis type-pair strengths as a switched arm (data/params/flyvis_pair_strength.csv).

A five-cell graph: graded Mi1 (10 synapses) and Mi9 (4) drive a graded T4a; a spiking Tm3 and an
unrelated cell also drive it. Claims: switch 0 builds nothing and keeps every weight; switch 1 sets
the edges of the table's pairs from graded cells so that the steady-state voltage gain (T4a mV per
Mi1 mV, linear part of release) equals flyvis's alpha x synapse count, for any release range, release
at rest and release multiplier; our sign is kept (Mi9 inhibits); a spiking presynaptic cell and an
edge with no flyvis pair keep count x scale; conductance synapses keep the gain for small signals
at rest. Alpha is fitted to a
task (Lappalainen et al. 2024); these are implementation checks, not validation.
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
KEY = "cell_type:all|optic_lobe_flyvis_pair_strength"
TYPES = ["Mi1", "Mi9", "Tm3", "T4a", "IN_x"]
N = len(TYPES)
TAB = pd.read_csv(REPO / "data" / "params" / lif.FV_PAIR_TABLE, comment="#")
ALPHA = {t: float(TAB.alpha[TAB.pre.eq(f"type:^{t}$") & TAB.post.eq("type:^T4a$")].iloc[0]) for t in ("Mi1", "Mi9")}
COUNT = np.array([10.0, 4.0, 6.0, 5.0], np.float32)


def _conn():
    nrn = pd.DataFrame({"bodyId": np.arange(10, 10 + N), "type": TYPES,
                        "predictedNt": ["acetylcholine", "glutamate", "acetylcholine", "acetylcholine",
                                        "acetylcholine"], "superclass": "ol_intrinsic", "class": "x"})
    # one edge from each of cells 0, 1, 2 and 4 to T4a (cell 3)
    return Connectome(nrn, np.array([0, 1, 2, 3, 3, 4], np.int64), np.full(4, 3, np.int32), COUNT,
                      np.array([1, -1, 1, 1, 1], np.float32), np.full(4, 0.2, np.float32))


def _pairs(on=True):
    r = Registry(Policy.MINIMAL)
    if on:
        r.overrides[KEY] = 1.0
    return lif._flyvis_pairs(r, _conn())


def _net(fe=None, cond=False, rng=None, r0=None, gk=None):
    f = lambda v: np.full(N, v, np.float32)
    graded = np.array([1, 1, 0, 1, 0], bool)
    tau_m = np.array([1e6, 1e6, 10, 10, 10], np.float32)   # held presynaptic cells do not leak within a step
    p = lif.LIFParams(tau_m, f(-55.0), f(-45.0), f(-55.0), f(2.0), 5.0, np.ones(N, np.int64), 0.0, False,
                      cond=cond, graded=graded, graded_r0=r0, graded_range=rng, graded_k=gk, fv_edge=fe)
    return lif.Network(_conn(), p, DT)


def _gain(net, pre, dv=8.0, ms=150.0):
    """T4a steady-state change per mV of a presynaptic cell held above rest (inside its release range).
    float32 exponential Euler stalls ~2e-4 mV short of its fixed point at -55 mV, so the step is large."""
    out = []
    for d in (0.0, dv):
        n = _net(*net)
        for _ in range(int(ms / DT)):
            n.v[pre] = n.v_rest[pre] + d
            n.step()
        out.append(float(n.v[3]))
    return (out[1] - out[0]) / dv


def test_switch_neutral_builds_nothing():
    assert _pairs(on=False) is None
    assert np.allclose(_net(None).w[[2, 3]], COUNT[[2, 3]] * 0.2)


def test_switch_on_selects_table_pairs_only():
    fe = _pairs()
    assert fe["idx"].tolist() == [0, 1, 2]            # Mi1, Mi9, Tm3 -> T4a; IN_x has no pair
    net = _net(fe)
    assert net.fv_spiking_pre == 1                    # Tm3 spikes: no voltage-gain reading
    assert np.allclose(net.w[[2, 3]], COUNT[[2, 3]] * 0.2)


@pytest.mark.parametrize("rng,r0,gk", [(None, None, None),
                                       (np.full(N, 12.0, np.float32), np.full(N, 0.3, np.float32),
                                        np.full(N, 1.5, np.float32))])
def test_steady_state_gain_is_alpha_times_count(rng, r0, gk):
    fe = _pairs()
    args = (fe, False, rng, r0, gk)
    assert _gain(args, 0) == pytest.approx(ALPHA["Mi1"] * 10, rel=2e-3)
    assert _gain(args, 1) == pytest.approx(-ALPHA["Mi9"] * 4, rel=2e-3)   # our glutamate sign, inhibitory


def test_conductance_synapses_keep_the_gain_for_small_signals_at_rest():
    args = (_pairs(), True, None, None, None)
    assert _gain(args, 0, dv=1.0) == pytest.approx(ALPHA["Mi1"] * 10, rel=1e-2)
    assert _gain(args, 1, dv=1.0) == pytest.approx(-ALPHA["Mi9"] * 4, rel=1e-2)
