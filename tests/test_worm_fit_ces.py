"""Calibrate-emulate-sample (wormemu.fit.ces) on toy problems with known answers: the encoders, the GP's marginal
likelihood gradient and fit, the step tuning, a linear-Gaussian posterior against its closed form, and EKI then CES on
a nonlinear map against MCMC on the true map. No worm, no data."""
import numpy as np
import pytest

from wormemu.fit import ces as C
from wormemu.fit import eki as E


def test_decorrelator_round_trip_and_unit_noise():
    rng = np.random.default_rng(0)
    gam = np.array([[2.0, 0.6, 0.0], [0.6, 1.0, 0.3], [0.0, 0.3, 0.5]])
    G = rng.multivariate_normal([1.0, -2.0, 0.5], gam, size=500)
    d = C.Decorrelator(G, gam)
    assert np.allclose(d.decode(d.encode(G)), G)
    assert np.allclose(d.encode_cov(gam), np.eye(3))
    assert np.allclose(d.decode_cov(np.eye(3)), gam)
    z = C.Decorrelator(G)                                         # sample covariance: encoded data are white
    assert np.allclose(np.cov(z.encode(G).T), np.eye(3), atol=1e-12)
    with pytest.raises(ValueError):
        C.Decorrelator(np.c_[G[:, 0], G[:, 0]])                   # rank-deficient: truncation not ported


def test_gp_gradient_and_fit():
    rng = np.random.default_rng(1)
    X = rng.uniform(-2, 2, (40, 2))
    y = np.sin(2.0 * X[:, 0]) + 0.1 * X[:, 1] + rng.normal(0, 0.05, 40)
    gp = C.GP(X, y, noise=0.05 ** 2)
    th = np.array([0.1, 0.8, -0.2])
    val, g = gp.nlml(th)
    fd = np.array([(gp.nlml(th + e)[0] - gp.nlml(th - e)[0]) / 2e-6 for e in 1e-6 * np.eye(3)])
    assert g == pytest.approx(fd, rel=1e-4, abs=1e-6)
    gp.optimise()
    assert gp.opt.success
    assert gp.ell[0] < gp.ell[1]                                  # the wiggly input gets the short length
    Xs = rng.uniform(-1.8, 1.8, (200, 2))
    mu, var = gp.predict(Xs, add_noise=False)
    err = mu - (np.sin(2.0 * Xs[:, 0]) + 0.1 * Xs[:, 1])
    assert np.sqrt(np.mean(err ** 2)) < 0.05
    assert np.mean(np.abs(err) < 2.0 * np.sqrt(var + 1e-12)) > 0.8   # the GP's own error bars cover the error


def test_stepsize_lands_in_the_acceptance_window():
    rng = np.random.default_rng(2)
    Z = rng.normal(size=(60, 3))
    G = Z @ np.diag([1.0, 2.0, 0.5])
    em = C.Emulator(Z, G, np.ones(3), optimise=False)
    post = C.Posterior(em, np.zeros(3), np.zeros(3), np.eye(3), model=C.Forward(em, lambda z: z * [1.0, 2.0, 0.5]))
    step, log = C.optimize_stepsize(post, seed=3)
    assert abs(log[-1][1] - C.S["target_acc"]) <= C.S["acc_tol"] and log[-1][0] == step


def test_linear_gaussian_posterior_matches_closed_form():
    """G(z) = A z, prior N(0, I), noise Gamma: the posterior is Gaussian with covariance (I + A' Gamma^-1 A)^-1. The
    emulator is trained on 200 prior draws; bars (guessed): mean within 0.15 posterior SD, SD within 12 %."""
    rng = np.random.default_rng(4)
    A = np.array([[1.0, 0.5], [-0.3, 1.2], [0.8, -0.7]])
    gam = np.diag([0.2, 0.3, 0.25])
    z_true = np.array([0.7, -0.4])
    y = A @ z_true + rng.multivariate_normal(np.zeros(3), gam)
    Z = rng.normal(size=(200, 2))
    em = C.Emulator(Z, Z @ A.T, gam)
    ztest = rng.normal(size=(100, 2))
    assert np.all(em.error(ztest, ztest @ A.T) < 0.1)             # under a tenth of a noise SD
    gi = np.linalg.inv(gam)
    cov = np.linalg.inv(np.eye(2) + A.T @ gi @ A)
    mean = cov @ A.T @ gi @ y
    p = C.sample(em, y, np.zeros(2), np.eye(2), n=40_000, seed=5)
    sd = np.sqrt(np.diag(cov))
    assert np.all(np.abs(p["mean"] - mean) < 0.15 * sd)
    assert p["sd"] == pytest.approx(sd, rel=0.12)
    assert np.all(p["precision"] < 1.0)                           # the data narrowed both values


def test_eki_then_ces_on_a_nonlinear_map():
    """The FIT_GENERAL order: EKI from the prior (J 40, controller to t = 1), every (z, G(z)) pair kept, then CES.
    Compared with RWM on the true map (ces.Forward, the same sampler and encoders). Bars (guessed): mean within
    0.3 true-posterior SD, SD ratio 0.7 to 1.4, per coordinate."""
    def g(z):
        z = np.atleast_2d(z)
        return np.c_[np.exp(0.5 * z[:, 0]), z[:, 0] + z[:, 1] ** 2 / 4.0, np.sin(z[:, 1]) + 0.3 * z[:, 0]]

    rng = np.random.default_rng(6)
    gam = np.diag([0.05, 0.05, 0.05])
    y = g(np.array([0.5, 0.8]))[0] + rng.multivariate_normal(np.zeros(3), gam)
    e = E.EKI(rng.normal(size=(40, 2)), y, gam, seed=7)
    hist = []
    while not e.done:
        G = g(e.z)
        hist.append((e.z.copy(), G, None))
        e.update(G)
    hist.append((e.z.copy(), g(e.z), None))
    Z, G = C.pairs(hist)
    em = C.Emulator(Z, G, gam)
    fwd = C.Forward(em, lambda z: g(z)[0])
    p = C.sample(em, y, np.zeros(2), np.eye(2), n=30_000, seed=8)
    t = C.sample(em, y, np.zeros(2), np.eye(2), n=30_000, seed=9, model=fwd)
    assert np.all(np.abs(p["mean"] - t["mean"]) < 0.3 * t["sd"])
    assert np.all((p["sd"] / t["sd"] > 0.7) & (p["sd"] / t["sd"] < 1.4))


def test_pairs_drop_failed_members():
    z = np.arange(8.0).reshape(4, 2)
    g = np.c_[z[:, 0], z[:, 1]]
    g[2, 0] = np.nan
    Z, G = C.pairs([(z, g, np.array([True, False, True, True]))])
    assert Z.tolist() == [[0.0, 1.0], [6.0, 7.0]] and G.shape == (2, 2)
