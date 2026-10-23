"""N19 receptor-map mode (s19, neuromod.py): sign rule, pool kinetics, bath hold, neutral path, GPU refusal.

Toy networks only (a few seconds); the whole-brain off-path identity is checked by spike hash on backhouse.
"""
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from flyemu import lif, neuromod  # noqa: E402

N, E, T = 300, 6000, 3000     # 300 ms at 0.1 ms


def _toy(seed=0, **extra):
    from flyemu.connectome import Connectome
    rng = np.random.default_rng(seed)
    pre = np.sort(rng.integers(0, N, E))
    post = rng.integers(0, N, E).astype(np.int32)
    indptr = np.zeros(N + 1, np.int64)
    np.cumsum(np.bincount(pre, minlength=N), out=indptr[1:])
    nt = rng.choice(["acetylcholine", "gaba", "glutamate", "octopamine", "serotonin"], N,
                    p=[.6, .2, .1, .05, .05])
    sign = np.where(np.isin(nt, ["gaba", "glutamate"]), -1.0, 1.0).astype(np.float32)
    sign[np.isin(nt, ["octopamine", "serotonin"])] = 0.0
    nrn = pd.DataFrame({"bodyId": np.arange(N), "type": [f"T{i % 9}" for i in range(N)],
                        "predictedNt": nt, "superclass": "central", "class": "x"})
    c = Connectome(nrn, indptr, post, rng.integers(1, 6, E).astype(np.float32), sign,
                   np.full(E, 0.9, np.float32))
    f = lambda v: np.full(N, v, np.float32)
    spont = np.where(rng.random(N) < 0.1, 9.0, 0.0).astype(np.float32)
    p = lif.LIFParams(f(20.0), f(-52.0), rng.uniform(-46, -44, N).astype(np.float32), f(-52.0),
                      f(2.2), 5.0, rng.integers(1, 12, N), 0.0, True, spont_mv=spont, **extra)
    return c, p, nt


def _map(nt, sens, tau_on=(340.0, 340.0, 70.0, 340.0), tau_off=(1400.0, 5900.0, 4080.0, 5900.0), K=10.0):
    rel = np.full(len(nt), -1, np.int8)
    for k, pool in enumerate(neuromod.POOLS):
        rel[nt == pool] = k
    return {"sens": np.asarray(sens, np.float32), "release": rel,
            "n_release": np.array([(rel == k).sum() for k in range(4)]),
            "tau_on_ms": np.array(tau_on), "tau_off_ms": np.array(tau_off), "K": K}


def _run(c, p, steps=T, kick=None):
    net = lif.Network(c, p, 0.1)
    out = []
    for t in range(steps):
        out.append(net.step(kick=kick(t) if kick else None).copy())
    return net, out


def test_sign_rule_is_the_preregistered_one():
    """DECISIONS 21 Oct 21:56: Gs/Gq +1, Gi/o -1, non-canonical 0; TA has no receptor in the tables."""
    assert neuromod.SIGN["dopamine"] == {"Dop1R1": 1, "Dop1R2": 1, "Dop2R": -1, "DopEcR": 0}
    assert set(neuromod.SIGN["octopamine"].values()) == {1}
    assert neuromod.SIGN["serotonin"] == {"5-HT2A": 1, "5-HT2B": 1, "5-HT7": 1, "5-HT1A": -1, "5-HT1B": -1}
    assert neuromod.SIGN["tyramine"] == {}
    genes = [g for s in neuromod.SIGN.values() for g in s]
    P = pd.DataFrame(np.full((2, len(genes)), 0.5), columns=genes)
    P.loc[1, "Dop2R"] = 1.0
    net = neuromod.net_expression(P)
    assert net[0].tolist() == [0.5, 2.0, 0.5, 0.0]       # DA 0.5+0.5-0.5; OA 4x0.5; 5-HT 3x0.5-2x0.5
    assert net[1, 0] == 0.0


def test_zero_sensitivity_map_is_identical_to_the_legacy_off_path():
    c, p, nt = _toy()
    _, a = _run(c, p)
    c, p2, nt = _toy(mod_map=_map(nt, np.zeros((N, 4))))
    _, b = _run(c, p2)
    assert sum(x.size for x in a) > 100
    assert all(np.array_equal(x, y) for x, y in zip(a, b))


def test_pool_kinetics_follow_tau_on_then_tau_off():
    """One spike from every OA cell: m rises with tau_on and falls with tau_off, peak near 1 spike per cell."""
    c, p, nt = _toy()
    p.spont_mv = np.zeros(N, np.float32)
    c.weight_syn[:] = 0.0                           # no network: the pool sees only the kicked spikes
    oa = np.flatnonzero(nt == "octopamine")
    p.mod_map = _map(nt, np.zeros((N, 4)))
    net = lif.Network(c, p, 1.0)
    trace = []
    for t in range(20000):
        net.step(kick=(oa, 40.0) if t == 0 else None)
        trace.append(net.modmap["m"][1])
    m = np.array(trace)
    t_pk = int(np.argmax(m))
    ton, toff = 340.0, 5900.0
    expect_pk = ton * toff / (toff - ton) * np.log(toff / ton)
    assert abs(t_pk - expect_pk) < 0.05 * expect_pk
    assert 0.8 < m.max() < 1.0
    late = m[8000:16000]
    tau_fit = -1.0 / np.polyfit(np.arange(late.size), np.log(late), 1)[0]
    assert abs(tau_fit - toff) < 0.02 * toff


def test_bath_hold_sets_gain_to_one_plus_s():
    c, p, nt = _toy()
    sens = np.zeros((N, 4), np.float32)
    sens[:, 1] = np.linspace(-1.5, 2.0, N)
    p.mod_map = _map(nt, sens)
    net = lif.Network(c, p, 0.1)
    np.testing.assert_array_equal(net.modmap_gain(), np.ones(N, np.float32))
    net.hold_modulator("octopamine", 1.0)
    np.testing.assert_allclose(net.modmap_gain(), np.maximum(0.0, 1.0 + sens[:, 1]), rtol=1e-6)
    net.hold_modulator("octopamine", None)
    np.testing.assert_array_equal(net.modmap_gain(), np.ones(N, np.float32))


def test_gpu_path_refuses_the_receptor_map():
    pytest.importorskip("jax")
    from flyemu.gpu.batched import BatchedNetwork
    c, p, nt = _toy(mod_map=None)
    p.mod_map = _map(nt, np.zeros((N, 4)))
    with pytest.raises(NotImplementedError, match="N19"):
        BatchedNetwork(lif.Network(c, p, 0.1), B=1)
