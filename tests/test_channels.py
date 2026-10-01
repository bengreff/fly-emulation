"""Ladder rung 1 (session 11): intrinsic conductances per type (src/flyemu/channels.py).

Single unconnected cells driven by a declared current step (mV of steady
depolarisation in the leak-only cell). Claims: neutral equivalence (all
conductances 0 equals the leak-only membrane; switch 0 builds nothing), rest is
preserved with every channel on, and each channel produces its textbook
signature: Ih sag and rebound, A-type first-spike delay, SK/BK adaptation,
T-type rebound depolarisation.
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "src"))

from flyemu import channels, lif  # noqa: E402
from flyemu.connectome import Connectome  # noqa: E402
from flyemu.registry import Registry  # noqa: E402

DT = 0.1


def _conn(n):
    nrn = pd.DataFrame({"bodyId": np.arange(n), "type": [f"T{i}" for i in range(n)],
                        "predictedNt": "acetylcholine", "superclass": "central", "class": "x"})
    indptr = np.zeros(n + 1, np.int64)
    indptr[1:] = 1
    return Connectome(nrn, indptr, np.array([1], np.int32), np.array([1.0], np.float32),
                      np.array([0.0], np.float32), np.array([0.9], np.float32))


def _net(g: dict | None, n=2, graded=False):
    f = lambda v: np.full(n, v, np.float32)
    ich = None
    if g is not None:
        gg = {c: np.asarray(g.get(c, np.zeros(n)), np.float32) for c in channels.CHANNELS}
        ich = channels.Intrinsic(g=gg, ca_per_spike=f(1.0), dt=DT)
    p = lif.LIFParams(f(20.0), f(-52.0), f(-45.0), f(-52.0), f(2.2), 5.0, np.ones(n, np.int64), 0.0, True,
                      graded=np.full(n, graded), intrinsic=ich)
    return lif.Network(_conn(n), p, DT)


def _run(net, drive, ms):
    """drive: (n,) mV or callable t_ms -> (n,). Returns v trace (steps, n) and spike times per cell."""
    vs, sp = [], [[] for _ in range(net.conn.n)]
    for s in range(int(ms / DT)):
        d = drive(s * DT) if callable(drive) else drive
        for i in net.step(external_mv=np.asarray(d, np.float32)):
            sp[i].append(s * DT)
        vs.append(net.v.copy())
    return np.array(vs), sp


def test_switch_neutral_builds_nothing_and_zero_conductance_equals_leak_only():
    reg = Registry("minimal")
    assert channels.from_registry(reg, _conn(2), timestep_ms=DT) is None
    a, b = _net(None), _net({})
    drive = lambda t: np.array([4.0, 12.0]) if 20 <= t < 220 else np.zeros(2)
    va, sa = _run(a, drive, 300)
    vb, sb = _run(b, drive, 300)
    assert np.max(np.abs(va - vb)) < 1e-3
    assert sa == sb and len(sa[1]) > 3


def test_rest_is_preserved_with_every_channel_on():
    g = {c: np.full(2, prior) for c, (_, _, _, prior) in channels.CHANNELS.items()}
    net = _net(g)
    v, sp = _run(net, np.zeros(2), 500)
    assert np.max(np.abs(v[-1] - (-52.0))) < 0.01 and not any(sp)


def test_ih_gives_sag_and_rebound():
    net = _net({"h": [0.0, 1.0]})
    step = lambda t: np.full(2, -25.0) if 50 <= t < 550 else np.zeros(2)
    v, _ = _run(net, step, 800)
    hyp = v[int(60 / DT):int(550 / DT)]
    sag = hyp[-1] - hyp.min(axis=0)
    after = v[int(555 / DT):int(700 / DT)].max(axis=0) - (-52.0)
    assert sag[0] < 0.05 and sag[1] > 1.0, sag
    assert after[0] < 0.05 and after[1] > 0.5, after


def test_a_type_delays_the_first_spike_near_threshold():
    # guessed kinetics: the delay is modest at the prior (3x leak) and grows with density
    net = _net({"A": [0.0, 3.0, 10.0]}, n=3)
    _, sp = _run(net, lambda t: np.full(3, 7.5) if t >= 10 else np.zeros(3), 400)
    first = [s[0] for s in sp]
    assert first[1] - first[0] > 3.0 and first[2] - first[1] > 10.0, first
    assert len(sp[2]) < len(sp[0])


def test_sk_and_bk_cause_spike_frequency_adaptation():
    net = _net({"SK": [0.0, 1.0], "BK": [0.0, 1.0]})
    _, sp = _run(net, np.full(2, 14.0), 500)
    isi = [np.diff(s) for s in sp]
    ratio = [i[-1] / i[0] for i in isi]
    assert ratio[0] < 1.05 and ratio[1] > 1.3, ratio


def test_t_type_gives_rebound_depolarisation():
    net = _net({"T": [0.0, 1.0]}, graded=True)
    step = lambda t: np.full(2, -25.0) if 50 <= t < 350 else np.zeros(2)
    v, _ = _run(net, step, 500)
    peak = v[int(352 / DT):].max(axis=0) - (-52.0)
    assert peak[0] < 0.05 and peak[1] > 2.0, peak
