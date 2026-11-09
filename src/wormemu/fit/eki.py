"""Ensemble Kalman inversion (weki, 8 Nov 2026; brief item 4; design and pre-registration: docs/worm/FIT_GENERAL.md).
NO FIT: this module is the method, tested on toy problems and a synthetic twin; nothing here reads real data.

The update is the stochastic EKI of EnsembleKalmanProcesses.jl (CliMA, src/EnsembleKalmanInversion.jl, opened
8 Nov 2026), in the optimiser's unbounded coordinates z of wormemu.params.Theta (members live inside the hard bounds by
construction, refinement 1):

    C_zg, C_gg   ensemble covariances (1/J, uncorrected, as EKP), C_zg optionally localised (Schur product with rho)
    z_j <- z_j + C_zg (C_gg + Gamma/dt)^-1 (y + eta_j - g_j),   eta_j ~ N(0, Gamma/dt)

Step dt from the data-misfit controller (Iglesias & Yang 2021, arXiv 2006.14980, as EKP's
LearningRateSchedulers.jl DataMisfitController runs it, opened 8 Nov 2026):

    Phi_j = 0.5 |Gamma^-1/2 (g_j - y)|^2,  q = max(M / (2 mean Phi), sqrt(M / (2 var Phi))),  dt = min(q, T - t)

and the run ends when t reaches T = 1. With sum(dt) = 1 and a linear-Gaussian problem the ensemble goes from the prior
to the posterior (the tempering limit; tests/test_worm_fit_eki.py checks it against the closed form).

Failures (refinements 2 and 3): a member whose forward run fails physicality, or whose values break a hard constraint,
is left out of the covariances; after the update it is redrawn from N(mean, cov) of the updated admissible members (EKP's
failsafe), up to `tries` draws that must pass `admissible`, else it keeps its last admissible z.

Neutral by default: inflation 1 (off) and no localisation (rho None). Localisation builders: `corr_rho` (keep a
parameter-observation pair only where the ensemble correlation is above k / sqrt(J), the null SD of a sample correlation
being about 1 / sqrt(J), derived) and `graph_rho` (structural zeros: no path in the interconnect graph from the
parameter's module to the observation's module).

    e = EKI(z0, y, gamma, seed=1)           # z0: J x p prior draws in z; gamma: M x M or the M diagonal variances
    while not e.done:
        g, ok = forward(e.z)                # J x M, and which members ran physical
        e.update(g, ok, admissible=None)    # admissible(z_row) -> bool: the hard constraints, on the new values
"""
from __future__ import annotations

from collections import deque

import numpy as np

# method settings (not worm quantities): value, label, basis
SETTINGS = {
    "terminate_at": (1.0, "derived", "sum of steps = 1: the Bayesian tempering endpoint (Iglesias & Yang 2021)"),
    "inflation": (1.0, "guessed", "neutral; the fit's value is picked on the synthetic twin (FIT_GENERAL.md section 5)"),
    "corr_k": (3.0, "guessed", "keep |corr| > 3 null SDs (1 / sqrt(J) each, derived)"),
    "redraw_tries": (100, "guessed", "redraws from the updated admissible ensemble before keeping the old z"),
    "jitter": (1e-10, "guessed", "diagonal added to C_gg + Gamma/dt before the solve"),
}
S = {k: v[0] for k, v in SETTINGS.items()}


def _gamma(gamma, m):
    g = np.asarray(gamma, float)
    return np.diag(g) if g.ndim == 1 else g


def misfit(g, y, gamma):
    """Phi_j = 0.5 (g_j - y)^T Gamma^-1 (g_j - y) for each row of g."""
    d = np.atleast_2d(g) - y
    return 0.5 * np.einsum("jm,jm->j", d, np.linalg.solve(_gamma(gamma, len(y)), d.T).T)


def dmc_step(phi, m, t, terminate_at=S["terminate_at"]):
    """The data-misfit controller's step (EKP DataMisfitController)."""
    var = np.var(phi, ddof=1) if len(phi) > 1 else 0.0
    q = max(m / (2 * np.mean(phi)), np.sqrt(m / (2 * var)) if var > 0 else 0.0)
    return float(min(q, terminate_at - t))


def corr_rho(z, g, k=S["corr_k"]):
    """1 where |corr(z_i, g_m)| > k / sqrt(J), else 0 (p x M)."""
    J = len(z)
    zs, gs = z.std(0), g.std(0)
    c = ((z - z.mean(0)).T @ (g - g.mean(0)) / J) / np.outer(np.where(zs > 0, zs, np.inf), np.where(gs > 0, gs, np.inf))
    return (np.abs(c) > k / np.sqrt(J)).astype(float)


def graph_rho(param_module, obs_modules, edges, hub=None):
    """Structural localisation: rho[i, m] = 1 if a directed path (or the same module) leads from parameter i's module to
    any module observation m is read from. edges: [(producer, key, consumer)] (wormemu.iograph.edges). hub: optional
    (writers, readers), modules that write the membrane (g_scale, I_pA, act_add) and modules that read it, joined
    through one node "membrane"."""
    nxt = {}
    for a, _, b in edges:
        nxt.setdefault(a, set()).add(b)
    if hub:
        for a in hub[0]:
            nxt.setdefault(a, set()).add("membrane")
        nxt.setdefault("membrane", set()).update(hub[1])
    reach = {}
    for src in set(param_module):
        seen, todo = {src}, deque([src])
        while todo:
            for b in nxt.get(todo.popleft(), ()):
                if b not in seen:
                    seen.add(b)
                    todo.append(b)
        reach[src] = seen
    obs = [{o} if isinstance(o, str) else set(o) for o in obs_modules]
    return np.array([[float(bool(reach[p] & o)) for o in obs] for p in param_module])


class EKI:
    def __init__(self, z0, y, gamma, seed=0, rho=None, inflation=S["inflation"], terminate_at=S["terminate_at"],
                 localise="fixed"):
        self.z = np.array(z0, float)
        self.y = np.asarray(y, float)
        self.gamma = _gamma(gamma, len(self.y))
        self.rng = np.random.default_rng(seed)
        self.rho, self.localise = rho, localise          # localise: "fixed" (rho as given) or "corr" (corr_rho x rho)
        self.inflation, self.T = inflation, terminate_at
        self.t, self.dts, self.history = 0.0, [], []

    @property
    def done(self):
        return self.t >= self.T - 1e-12

    def update(self, g, ok=None, admissible=None, dt=None, obs=None):
        """obs: the observation indices g's columns hold (a stochastic batch, FIT_GENERAL section 8); None = all."""
        g = np.asarray(g, float)
        J, M = g.shape
        y, gamma, rho = self.y, self.gamma, self.rho
        if obs is not None:
            obs = np.asarray(obs, int)
            y, gamma = y[obs], gamma[np.ix_(obs, obs)]
            rho = rho[:, obs] if np.ndim(rho) == 2 else rho
        if M != len(y):
            raise ValueError(f"g has {M} columns for {len(y)} observations")
        ok = np.ones(J, bool) if ok is None else np.asarray(ok, bool) & np.isfinite(g).all(1)
        if ok.sum() < 2:
            raise RuntimeError("fewer than 2 admissible members: no covariance")
        z, gk = self.z[ok], g[ok]
        phi = misfit(gk, y, gamma)
        dt = dmc_step(phi, M, self.t, self.T) if dt is None else dt
        zm, gm = z.mean(0), gk.mean(0)
        if self.inflation != 1.0:                         # neutral exactly at 1 (no round-off on the members)
            z = zm + self.inflation * (z - zm)
        Z = z - zm
        n = len(z)
        czg = Z.T @ (gk - gm) / n
        cgg = (gk - gm).T @ (gk - gm) / n
        if self.localise == "corr":
            rho = corr_rho(z, gk) * (1.0 if rho is None else rho)
        if rho is not None:
            czg = czg * rho
        gam = gamma / dt
        eta = self.rng.multivariate_normal(np.zeros(M), gam, size=n)
        A = cgg + gam + S["jitter"] * np.eye(M)
        znew = z + np.linalg.solve(A, (y + eta - gk).T).T @ czg.T
        out = self.z.copy()
        out[ok] = znew
        bad = ~ok
        if admissible is not None:
            bad |= ~np.array([bool(admissible(r)) if k else True for k, r in zip(ok, out)])
        good = ~bad
        if bad.any():
            mu = out[good].mean(0)
            cov = np.cov(out[good].T) if good.sum() > 1 else np.zeros((len(mu), len(mu)))
            for j in np.flatnonzero(bad):
                for _ in range(int(S["redraw_tries"])):
                    cand = self.rng.multivariate_normal(mu, np.atleast_2d(cov))
                    if admissible is None or admissible(cand):
                        out[j] = cand
                        break
                else:
                    out[j] = self.z[j]                    # keeps its last admissible point
        self.history.append(dict(t=self.t, dt=dt, phi_mean=float(phi.mean()), phi=phi, n_ok=int(ok.sum()),
                                 n_redrawn=int(bad.sum()), z_mean=out.mean(0), z_sd=out.std(0)))
        self.z, self.t = out, self.t + dt
        self.dts.append(dt)
        return self.z
