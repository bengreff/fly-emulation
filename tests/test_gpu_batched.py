"""Batched JAX simulator vs the CPU reference lif.Network on a toy network.

Runs on the JAX CPU backend in a few seconds; skipped if JAX is absent.
The whole-CNS comparison on the GPU is `scripts/gpu_bench.py equiv` (docs/GPU.md).
"""
import sys
from pathlib import Path

import numpy as np
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
jax = pytest.importorskip("jax")

from flyemu import lif  # noqa: E402
from flyemu.gpu.batched import BatchedNetwork  # noqa: E402
from flyemu.gpu.equivalence import compare, cpu_run, unpack  # noqa: E402

N, E, T = 400, 8000, 2000     # 200 ms at 0.1 ms
ELEC = (np.array([3, 70]), np.array([71, 72]), np.array([30.0, 30.0], np.float32))
_REF = {}


def _toy(seed=0, **extra):
    from flyemu.connectome import Connectome
    import pandas as pd
    rng = np.random.default_rng(seed)
    pre = np.sort(rng.integers(0, N, E))
    post = rng.integers(0, N, E).astype(np.int32)
    indptr = np.zeros(N + 1, np.int64)
    np.cumsum(np.bincount(pre, minlength=N), out=indptr[1:])
    nt = rng.choice(["acetylcholine", "gaba", "glutamate", "dopamine"], N, p=[.6, .25, .1, .05])
    sign = np.where(np.isin(nt, ["gaba", "glutamate"]), -1.0, 1.0).astype(np.float32)
    sign[nt == "dopamine"] = 0.0
    nrn = pd.DataFrame({"bodyId": np.arange(N), "type": [f"T{i % 9}" for i in range(N)],
                        "predictedNt": nt, "superclass": "central", "class": "x"})
    c = Connectome(nrn, indptr, post, rng.integers(1, 6, E).astype(np.float32), sign,
                   np.full(E, 0.9, np.float32))
    f = lambda v: np.full(N, v, np.float32)
    graded = rng.random(N) < 0.08
    spont = np.where(rng.random(N) < 0.05, 8.0, 0.0).astype(np.float32)
    p = lif.LIFParams(f(20.0), f(-52.0), rng.uniform(-46, -44, N).astype(np.float32), f(-52.0),
                      f(2.2), 5.0, rng.integers(1, 12, N), 0.0, True,
                      graded=graded, spont_mv=spont, mod_release=np.where(nt == "dopamine", 0, -1),
                      **extra)
    return c, p


def _stim(seed=1):
    rng = np.random.default_rng(seed)
    idx = np.arange(0, 40)
    mask = rng.random((T, idx.size)) < 50 * 0.1 / 1000     # 50 Hz Poisson, fixed draw
    ext = np.zeros(N, np.float32)
    ext[40:60] = 6.0
    return idx, mask, ext


ALL = {"adapt_mv": 1.0, "std_u": 0.2, "gabab_fraction": 0.3,
       "mod_sensitivity": np.tile([0.5, 0.0, 0.0], (N, 1)).astype(np.float32)}
SLOW = {"mglur_fraction": 0.3, "machr_fraction": 0.2, "nmda_fraction": 0.5,
        "glu_sign_post": np.where(np.arange(N) % 2, 1.0, 0.0).astype(np.float32)}



def _ich():
    """Rung-1 channels on every toy cell, per-cell densities (m8-like scale)."""
    from flyemu import channels
    rng = np.random.default_rng(3)
    m8 = {"A": 2.8, "M": 0.36, "h": 0.046, "T": 0.25, "NaP": 0.015, "Kv2": 0.22, "BK": 7.9, "SK": 0.5}
    g = {c: (m8[c] * rng.uniform(0.5, 1.5, N)).astype(np.float32) for c in channels.CHANNELS}
    return {"intrinsic": channels.Intrinsic(g=g, ca_per_spike=rng.uniform(0.5, 1.5, N).astype(np.float32),
                                            dt=0.1, ca_tau=37.86)}


ICH = _ich()


@pytest.mark.parametrize("extra,path", [
    ({}, {}), ({}, {"tiers": ()}), ({}, {"tiers": ((2, 16), (4, 64))}),
    (ALL, {}), (SLOW, {}), (ICH, {}), ({**ICH, **ALL}, {"tiers": ()}),
], ids=["m4-like-event", "m4-like-dense", "m4-like-event-overflow-to-dense",
        "adapt+std+gabab+mod-event", "mglur+machr+nmda-event", "rung1-channels-event",
        "rung1-channels+adapt+std+gabab+mod-dense"])
def test_member_matches_cpu_reference(extra, path):
    c, p = _toy(**extra)
    idx, mask, ext = _stim()
    key = tuple(sorted(extra))
    if key not in _REF:            # CPU reference, shared across input paths
        net = lif.Network(c, p, 0.1)
        net.elec = ELEC
        _REF[key] = cpu_run(net, T, ext, (idx, mask, 68.75))[0]
    ref = _REF[key]
    net2 = lif.Network(c, p, 0.1)
    net2.elec = ELEC
    g = BatchedNetwork(net2, B=2, **path)
    r = g.run(T, external_mv=ext, kicks=(idx, mask, 68.75), record="packed")
    for b in range(2):
        res = compare(ref, unpack(r["raster"], N, b), N, 0.1)
        assert res["spikes_cpu"] > 300
        # float32 summation order differs; demand agreement, not bit identity
        assert res["rate_corr_active"] > 0.98, res
        assert res["first_divergence_step"] is None or res["first_divergence_step"] > 300, res


def test_members_with_different_gains_match_separate_cpu_runs():
    c, p = _toy()
    idx, mask, ext = _stim()
    rng = np.random.default_rng(5)
    rel = rng.uniform(0.6, 1.4, (2, N)).astype(np.float32)
    inp = rng.uniform(0.6, 1.4, (2, N)).astype(np.float32)
    spont = np.stack([p.spont_mv, p.spont_mv * 1.5]).astype(np.float32)
    v_th = np.stack([p.v_th, p.v_th - rng.uniform(0, 1, N)]).astype(np.float32)
    tau_m = np.stack([p.tau_m, p.tau_m * rng.uniform(0.8, 1.2, N)]).astype(np.float32)
    g = BatchedNetwork(lif.Network(c, p, 0.1), B=2,
                       member={"release_gain": rel, "input_gain": inp, "spont_mv": spont,
                               "v_th": v_th, "tau_m": tau_m})
    r = g.run(T, external_mv=ext, kicks=(idx, mask, 68.75), record="packed")
    outs = []
    for b in range(2):
        from dataclasses import replace
        pb = replace(p, release_gain=rel[b], input_gain=inp[b], spont_mv=spont[b],
                     v_th=v_th[b], tau_m=tau_m[b])
        ref, _ = cpu_run(lif.Network(c, pb, 0.1), T, ext, (idx, mask, 68.75))
        res = compare(ref, unpack(r["raster"], N, b), N, 0.1)
        assert res["rate_corr_active"] > 0.98, res
        outs.append(res["spikes_cpu"])
    assert outs[0] != outs[1]      # the two variants really differ


def test_silence_one_member_only():
    c, p = _toy()
    idx, mask, ext = _stim()
    g = BatchedNetwork(lif.Network(c, p, 0.1), B=2)
    g.silence(np.arange(40, 200), members=[1])
    g.run(T, external_mv=ext, kicks=(idx, mask, 68.75))
    cnt = g.spike_counts()
    net = lif.Network(c, p, 0.1)
    net.silence(np.arange(40, 200))
    ref, _ = cpu_run(net, T, ext, (idx, mask, 68.75))
    ref_cnt = np.bincount(np.concatenate(ref), minlength=N)
    assert cnt[0].sum() != cnt[1].sum()
    assert np.corrcoef(cnt[1], ref_cnt)[0, 1] > 0.98


@pytest.mark.parametrize("extra", [{"presyn_inh_gain": 0.1}, {"kc_ltd_timing": 0.1}])
def test_unported_mechanisms_raise(extra):
    c, p = _toy(**extra)
    with pytest.raises(NotImplementedError):
        BatchedNetwork(lif.Network(c, p, 0.1), B=1)


def test_external_rows_equal_dense_external():
    c, p = _toy()
    idx, mask, ext = _stim()
    rows = np.flatnonzero(ext)
    a = BatchedNetwork(lif.Network(c, p, 0.1), B=2)
    b = BatchedNetwork(lif.Network(c, p, 0.1), B=2)
    for _ in range(4):                      # four 25 ms windows, as a closed loop would
        a.run(250, external_mv=ext, kicks=(idx, mask[:250], 68.75))
        b.run(250, external_mv=np.stack([ext[rows]] * 2), ext_rows=rows,
              kicks=(idx, mask[:250], 68.75))
    assert np.array_equal(a.spike_counts(), b.spike_counts())
    assert a.spike_counts().sum() > 0


def test_rung1_channels_refuse_per_member_v_rest():
    c, p = _toy(**ICH)
    with pytest.raises(NotImplementedError):
        BatchedNetwork(lif.Network(c, p, 0.1), B=2, member={"v_rest": np.float32(-50.0)})
