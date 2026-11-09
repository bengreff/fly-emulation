"""wormemu.fit.eki on problems with a known answer (brief item 4). No NEURON and no real data.

1. linear-Gaussian: the ensemble at t = 1 matches the closed-form posterior;
2. a nonlinear toy: the ensemble lands on the generating point;
3. failures and constraints: failed members never enter the update, and every member stays admissible;
4. localisation: a parameter the observations cannot see keeps its prior draws exactly;
5. synthetic twin on the excretory canal (mech.organs_other.Osmo, the model's own code, 4 gap numbers): hidden values
   drawn inside the box, data generated with noise, values recovered. Criterion written before the first run: each
   hidden value within a factor 1.25 of the final ensemble median and inside the ensemble's 2.5-97.5 % range.
"""
import numpy as np
import pytest

from wormemu.fit import eki as E


def run(e, forward, admissible=None, max_iter=60):
    for _ in range(max_iter):
        if e.done:
            break
        g, ok = forward(e.z)
        e.update(g, ok, admissible)
    return e


def test_linear_gaussian_matches_the_closed_form_posterior():
    rng = np.random.default_rng(1)
    p, m, J = 4, 6, 4000
    A = rng.normal(size=(m, p))
    gam = np.full(m, 0.3 ** 2)
    y = A @ np.array([0.5, -1.0, 0.2, 0.8]) + rng.normal(0, 0.3, m)
    post = np.linalg.inv(np.eye(p) + A.T @ np.diag(1 / gam) @ A)
    mean = post @ A.T @ (y / gam)
    e = run(E.EKI(rng.normal(size=(J, p)), y, gam, seed=2), lambda z: (z @ A.T, None))
    assert e.done and sum(e.dts) == pytest.approx(1.0)
    assert len(e.dts) > 1                                             # the controller took several steps
    assert e.z.mean(0) == pytest.approx(mean, abs=0.03)
    assert np.cov(e.z.T) == pytest.approx(post, abs=0.02)


def test_one_full_step_is_the_kalman_update():
    rng = np.random.default_rng(3)
    p, m, J = 3, 3, 6000
    A = rng.normal(size=(m, p))
    gam = np.full(m, 0.5)
    y = rng.normal(size=m)
    post = np.linalg.inv(np.eye(p) + A.T @ np.diag(1 / gam) @ A)
    e = E.EKI(rng.normal(size=(J, p)), y, gam, seed=4)
    e.update(e.z @ A.T, dt=1.0)
    assert e.z.mean(0) == pytest.approx(post @ A.T @ (y / gam), abs=0.04)


def G_toy(z):
    z = np.atleast_2d(z)
    return np.stack([z[:, 0], z[:, 1] + 0.5 * z[:, 0] ** 2, np.exp(0.3 * z[:, 1]), np.sin(z[:, 0] - z[:, 1])], 1)


def test_nonlinear_toy_recovers_the_generating_point():
    zt = np.array([0.7, -0.4])
    y = G_toy(zt)[0]
    rng = np.random.default_rng(5)
    e = run(E.EKI(rng.normal(size=(200, 2)), y, np.full(4, 0.01 ** 2), seed=6), lambda z: (G_toy(z), None))
    assert e.done
    assert e.z.mean(0) == pytest.approx(zt, abs=0.02)


def test_failed_members_are_left_out_and_constraints_hold():
    zt = np.array([0.7, -0.4])
    y = G_toy(zt)[0]
    rng = np.random.default_rng(7)
    z0 = rng.normal(size=(200, 2))
    adm = lambda r: r[0] > r[1]                                       # a hard constraint the answer satisfies
    z0 = z0[[adm(r) for r in z0]][:100]
    seen = []

    def forward(z):
        g = G_toy(z)
        ok = z[:, 0] < 1.5                                            # "unphysical" beyond z0 = 1.5
        g[~ok] = np.nan                                               # a failed run returns garbage
        seen.append(ok.copy())
        return g, ok

    e = run(E.EKI(z0, y, np.full(4, 0.02 ** 2), seed=8), forward, adm)
    assert all(adm(r) for r in e.z)
    assert any((~s).any() for s in seen)                              # failures did happen
    assert all(h["n_ok"] == int(s.sum()) for h, s in zip(e.history, seen))
    assert e.z.mean(0) == pytest.approx(zt, abs=0.05)


def test_localisation_keeps_unseen_parameters_at_their_prior_draws():
    rng = np.random.default_rng(9)
    p, J = 20, 30
    z0 = rng.normal(size=(J, p))
    A = np.zeros((3, p))
    A[:, :2] = rng.normal(size=(3, 2))
    y = rng.normal(size=3)
    fwd = lambda z: (z @ A.T, None)
    rho = E.graph_rho(["a", "a"] + ["c"] * (p - 2), [["b"]] * 3, [("a", "k", "b")])
    assert rho[:2].all() and not rho[2:].any()
    loc = run(E.EKI(z0, y, np.full(3, 0.1), seed=10, rho=rho), fwd)
    raw = run(E.EKI(z0, y, np.full(3, 0.1), seed=10), fwd)
    assert np.array_equal(loc.z[:, 2:], z0[:, 2:])                    # untouched
    assert raw.z[:, 2:].std(0).mean() < z0[:, 2:].std(0).mean()      # without it: spurious updates (collapse)


def test_graph_rho_paths_and_hub():
    edges = [("a", "x", "b"), ("b", "y", "c")]
    assert E.graph_rho(["a", "c"], ["c", "a"], edges).tolist() == [[1.0, 1.0], [1.0, 0.0]]   # c sees only c
    hub = E.graph_rho(["c"], ["d"], edges, hub=(["c"], ["d"]))
    assert hub.tolist() == [[1.0]]


# --- synthetic twin: the excretory canal -------------------------------------------------------------------------
TWIN = ("osmo_dosm_mOsm", "osmo_e_vol_kPa", "osmo_lp_per_kPa_s", "osmo_canal_gain")
H = 3600.0
T_CANAL = np.arange(1, 17) * 900.0                                    # every 15 min for 4 h
T_NULL = np.array([0.5, 1, 2, 4, 8, 16, 32, 64]) * H
NOISE_V = 0.005                                                       # guessed: 0.5 % of body volume per reading


def osmo_forward(x, extra=200.0, null=True):
    """Body volume v: canal form with the medium `extra` mOsm above the template for 2 h, then back (every 15 min),
    then (null) the canal-ablated form from v = 1 (T_NULL)."""
    from wormemu.mech import organs_other as oo
    q = oo.defaults()
    out = []
    for row in np.atleast_2d(x):
        q.update(dict(zip(TWIN, row)))
        o, ys, t = oo.Osmo(q, "canal"), [], 0.0
        for tt in T_CANAL:
            while t < tt - 1e-9:
                o.step(60.0, extra if t < 2 * H else 0.0)
                t += 60.0
            ys.append(o.v)
        if null:
            o, t = oo.Osmo(q, "null"), 0.0                            # canal ablated (Nelson & Riddle 1984 form)
            for tt in T_NULL:
                o.step(tt - t)
                t = tt
                ys.append(o.v)
        out.append(ys)
    return np.array(out)


def test_synthetic_twin_recovers_the_excretory_canal():
    from wormemu.mech import organs_other as oo
    spec = {s.id: s for s in oo.SPECS}
    lo, hi = np.log([spec[k].lo for k in TWIN]), np.log([spec[k].hi for k in TWIN])
    to_x = lambda z: np.exp(lo + (hi - lo) / (1 + np.exp(-z)))       # Theta's log-logit transform
    rng = np.random.default_rng(20261108)
    x_true = to_x(np.log((u := rng.uniform(0.1, 0.9, 4)) / (1 - u)))  # hidden, inside the box
    y = osmo_forward(x_true)[0] + rng.normal(0, NOISE_V, len(T_CANAL) + len(T_NULL))
    u0 = rng.uniform(size=(100, 4))                                   # the log-uniform prior on the box
    e = run(E.EKI(np.log(u0 / (1 - u0)), y, np.full(len(y), NOISE_V ** 2), seed=11),
            lambda z: (osmo_forward(to_x(z)), None), max_iter=40)
    xs = to_x(e.z)
    med = np.median(xs, 0)
    lo95, hi95 = np.percentile(xs, [2.5, 97.5], axis=0)
    assert e.done
    assert np.all(np.abs(np.log(med / x_true)) < np.log(1.25)), (x_true, med)
    assert np.all((lo95 <= x_true) & (x_true <= hi95)), (x_true, lo95, hi95)
