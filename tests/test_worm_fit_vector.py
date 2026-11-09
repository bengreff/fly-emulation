"""The EKI vector (wormemu.fit.vector) on the real params.Theta, no simulation: which numbers it holds, the z round
trip, the dict a forward passes builds the same worm as Theta.set, the joint-constraint check, prior draws, and the
battery targets. No data is fitted."""
import numpy as np
import pytest

from wormemu import datamodel
from wormemu.brain import sample_worm
from wormemu.fit import vector as V
from wormemu.fit import vitals


@pytest.fixture(scope="module")
def v():
    return V.Vector()


def test_mask(v):
    T = v.T
    out = set(T.ids) - set(v.ids)
    assert v.p == T.n - 15                                           # FIT_GENERAL section 1: less the bernoulli rows
    assert all(T.kind[T.ids.index(i)] in ("log", "logit") for i in v.ids)
    assert len(out) == 15 and "obs_noise_dff" not in v.ids and not any(i.startswith("scene_") for i in v.ids)
    assert not any("[" in i for i in v.ids)                          # the element rows are the bernoulli ones


def test_round_trip_and_template(v):
    rng = np.random.default_rng(0)
    z = rng.normal(size=v.p)
    x = v.values(z)
    assert np.allclose(v.z(x), z, atol=1e-9)
    out = np.setdiff1d(np.arange(v.T.n), v.keep)
    assert np.array_equal(x[out], v.base[out])                       # the rest stays at the template
    assert np.all((x >= v.T.lo) & (x <= v.T.hi))
    zt = v.z(v.base)
    assert np.allclose(v.values(zt), v.base, rtol=1e-9)


def test_dict_builds_the_same_worm(v):
    z = np.random.default_rng(1).normal(size=v.p)
    a = v.spec(z).values
    b = datamodel._theta(sample_worm(None), v.theta(z)).values
    for i, pid in zip(v.ids, v.T.table.pid.iloc[v.keep]):
        assert a[pid] == pytest.approx(b[pid], rel=1e-12), i
    el = next(i for i in v.T.ids if "[" in i)                       # an element row now passes (main 27f7276)
    assert vitals.battery_theta({el: 1.0})[el] == 1.0


def test_template_admissible_and_prior(v):
    assert v.broken(v.z(v.base)) == []
    z0, rate = v.prior(6, seed=20261109)
    assert z0.shape == (6, v.p) and 0.01 <= rate <= 1.0
    assert all(v.admissible(z) for z in z0)
    assert not np.allclose(z0[0], v.z(v.base))                       # no member starts at the template


def test_targets_match_the_battery_order():
    names, y, sig = V.targets()
    assert len(names) == len(y) == len(sig) == 10 and np.all(sig > 0)
    assert names[0].startswith("food:") and names[-1].startswith("nofood:")
    assert not any(n.split(":")[1] in ("dmp_period_s", "egg_inactive_min", "egg_intra_s") for n in names)
