"""The EKI run loop on disk (wormemu.fit.driver) on toy maps: a run killed mid-iteration and resumed ends identical to
one that was never stopped, finished members are not re-run, each stop rule fires, a process pool gives the same
answer as one process (with simulation noise seeded per iteration), stochastic batches, and the seed-agreement check.
No worm, no data."""
import json

import numpy as np
import pytest

from wormemu.fit.driver import Driver, seed_agreement

A = np.array([[1.0, 0.5], [-0.3, 1.2], [0.8, -0.7]])
GAM = np.diag([0.2, 0.3, 0.25])
Y = A @ np.array([0.7, -0.4]) + np.array([0.1, -0.2, 0.05])
Z0 = np.random.default_rng(0).normal(size=(12, 2))


def linear(z, k, obs):
    return A @ z, True


def noisy(z, k, obs):
    """Simulation noise from one seed per iteration, shared by every member (FIT_GENERAL section 7)."""
    return A @ z + np.random.default_rng(1000 + k).normal(0.0, 0.05, 3), True


class Crashes:
    """The linear map, killed (an exception) on call number `at`; counts every call it gets."""
    def __init__(self, at=None):
        self.at, self.n = at, 0

    def __call__(self, z, k, obs):
        self.n += 1
        if self.n == self.at:
            raise KeyboardInterrupt("the laptop lid")
        return linear(z, k, obs)


def test_resume_after_a_crash_is_identical(tmp_path):
    ref = Driver(tmp_path / "ref", Z0, Y, GAM, linear, seed=3)
    why = ref.run()
    assert why == "t reached 1"
    f = Crashes(at=12 * 2 + 5)                                    # mid-way through iteration 2's members
    d = Driver(tmp_path / "cut", Z0, Y, GAM, f, seed=3)
    with pytest.raises(KeyboardInterrupt):
        d.run()
    assert d.k == 2 and len(list((tmp_path / "cut" / "it2").glob("m*.json"))) == 4
    g = Crashes()
    r = Driver(tmp_path / "cut", Z0, Y, GAM, g, seed=99)          # the seed is ignored: the generator state is read
    assert r.k == 2
    assert r.run() == why
    assert g.n == 12 * (ref.k + 1) - 2 * 12 - 4                   # only the members without a result ran again
    assert r.k == ref.k
    assert np.array_equal(r.e.z, ref.e.z) and r.e.t == ref.e.t
    Zr, Gr = ref.pairs()
    Zc, Gc = r.pairs()
    assert np.array_equal(Zr, Zc) and np.array_equal(Gr, Gc) and len(Zr) == 12 * (ref.k + 1)
    assert (tmp_path / "cut" / "STOP").read_text().strip() == why


def test_resume_refuses_other_data(tmp_path):
    Driver(tmp_path, Z0, Y, GAM, linear)
    with pytest.raises(ValueError):
        Driver(tmp_path, Z0, Y + 1.0, GAM, linear)


def test_iteration_cap_and_plateau_report_model_error(tmp_path):
    d = Driver(tmp_path / "cap", Z0, Y, GAM, linear, stops={"max_iter": 2})
    assert d.run().startswith("2 iterations with t =") and d.k == 2
    p = Driver(tmp_path / "plat", Z0, Y, GAM, linear)              # the rule on a written log (the DMC step jumps
    row = {"n_ok": 12, "J": 12}                                     # to t = 1 on toy maps before any plateau)
    p.log = [{**row, "phi_per_obs": 10.0 * 0.999 ** i} for i in range(10)]
    assert p.stop_reason().startswith("plateau") and "model error" in p.stop_reason()
    p.log = p.log[:9]
    assert p.stop_reason() is None                                  # not before 10 iterations
    p.log = [{**row, "phi_per_obs": 10.0 * 0.996 ** i} for i in range(12)]
    assert p.stop_reason() is None                                  # 2 % over 5 iterations is still progress


class _FailsMost:
    """About 30 % of runs succeed wherever the member is (a hash of its value), so the stop is the rejection rule."""
    def __call__(self, z, k, obs):
        return A @ z, bool((1e4 * abs(z[0])) % 1.0 < 0.3)


def test_rejection_stop(tmp_path):
    z0 = np.random.default_rng(1).normal(size=(40, 2))
    d = Driver(tmp_path, z0, Y, GAM * 1e-4, _FailsMost(), stops={"max_iter": 50})
    assert d.run() == "more than half the members rejected in each of the last 3 iterations" and d.k == 3
    log = json.loads(str(np.load(tmp_path / "state_3.npz")["log"]))
    assert all(2 <= x["n_ok"] < 20 for x in log)


def test_fewer_than_two_members_stops(tmp_path):
    d = Driver(tmp_path, Z0, Y, GAM, lambda z, k, obs: (A @ z, False))
    assert d.run().startswith("fewer than 2 of 12 members ran in iteration 0")


def test_process_pool_matches_one_process(tmp_path):
    a = Driver(tmp_path / "one", Z0, Y, GAM, noisy, seed=5)
    a.run()
    b = Driver(tmp_path / "pool", Z0, Y, GAM, noisy, processes=2, seed=5)
    b.run()
    assert np.array_equal(a.e.z, b.e.z) and a.k == b.k
    G0 = np.array([json.loads((tmp_path / "pool" / "it0" / f"m{j}.json").read_text())["g"] for j in range(12)])
    assert np.allclose(G0 - Z0 @ A.T, (G0 - Z0 @ A.T)[0])          # common random numbers: one noise per iteration


B6 = np.vstack([A, -A])                                             # 6 observations; each batch scores 0 and 3 more
Y6 = B6 @ np.array([0.7, -0.4]) + np.array([0.1, -0.2, 0.05, 0.0, 0.1, -0.1])
GAM6 = np.diag([0.2, 0.3, 0.25, 0.2, 0.3, 0.25])


def batch(k):
    return [0] + sorted(np.random.default_rng(7 + k).choice(np.arange(1, 6), 3, replace=False).tolist())


class Batched:
    def __init__(self):
        self.seen = []

    def __call__(self, z, k, obs):
        self.seen.append((k, list(obs)))
        return B6[obs] @ z, True


def test_stochastic_batches(tmp_path):
    f = Batched()
    d = Driver(tmp_path, Z0, Y6, GAM6, f, batch=batch, seed=2)
    assert d.run() == "t reached 1"
    for k in range(d.k + 1):
        assert json.loads((tmp_path / f"it{k}" / "obs.json").read_text()) == batch(k)
        assert all(o == batch(k) for kk, o in f.seen if kk == k)
    Z, G = d.pairs()                                                # the observation in every batch: 0
    assert G.shape == (12 * (d.k + 1), 1) and np.allclose(G[:, 0], Z @ B6[0])
    Z1, G1 = d.pairs(cols=[0, batch(0)[1]])
    assert len(Z1) >= 12 and np.allclose(G1, Z1 @ B6[[0, batch(0)[1]]].T)
    with pytest.raises(ValueError):                                 # a forward that ignores obs is caught
        Driver(tmp_path / "bad", Z0, Y6, GAM6, lambda z, k, obs: (B6 @ z, True), batch=batch).run()


def test_seed_agreement():
    rng = np.random.default_rng(3)
    m = np.array([0.4, -1.0, 0.0])
    sd = np.array([0.1, 0.2, 1.0])                                  # the third coordinate is not informed
    same = [m + sd * rng.normal(size=(128, 3)) for _ in range(3)]
    r = seed_agreement(same)
    assert r["informed"] == [0, 1] and r["passed"] is True and r["frac_agree"] == 1.0
    off = same[:2] + [same[2] + np.array([0.5, 0.0, 0.0])]          # one seed lands 5 SD away on coordinate 0
    r = seed_agreement(off)
    assert r["disagree"] == [0] and r["frac_agree"] == 0.5 and r["passed"] is False
    assert seed_agreement([rng.normal(size=(50, 2)) for _ in range(3)])["passed"] is None   # nothing informed
