"""Calibrate-emulate-sample (weki, 8 Nov 2026; FIT_GENERAL.md section 9, the step after the EKI stops). NO FIT: the
method, tested on toy problems (tests/test_worm_fit_ces.py); nothing here reads real data or runs the worm.

Ported from CalibrateEmulateSample.jl (CliMA; github.com/CliMA/CalibrateEmulateSample.jl @ bffeb42, Apache-2.0,
opened 8 Nov 2026; Cleary, Garbuno-Inigo, Lan, Schneider & Stuart 2021, arXiv 2001.03689), its Gaussian-process path
with the settings its examples use (examples/Sinusoid):

    calibrate  every (z, G(z)) pair the EKI ran, in the optimiser's unbounded coordinates z (as fit/eki.py)
    encode     inputs:  u = S^-1/2 V' (z - mean z), S, V from the SVD of the training inputs' sample covariance
               outputs: w = S^-1/2 V' (g - mean g), S, V from the SVD of the noise covariance Gamma, so the encoded
               noise is I (Utilities/decorrelator.jl: decorrelate_sample_cov "in", decorrelate_structure_mat "out")
    emulate    one zero-mean GP per encoded output: squared-exponential kernel with one length per input (SEArd),
               hyperparameters (log lengths, log signal SD) at the marginal-likelihood maximum, bounds 1e-5 to 1e5,
               start 1; the noise variance fixed at the encoded Gamma's diagonal (GaussianProcess(GPJL(),
               noise_learn = false): alg_reg_noise 1, so regularisation = diag(encoded Gamma) = 1)
    sample     random-walk Metropolis in u (RWMHSampling): proposal N(u, step^2 C_prior,u), log density
               log N(w_obs; m(u), diag(var_f(u) + 1)) + log prior(u) (emulator_log_density_model with
               add_obs_noise_cov = true); step from optimize_stepsize's bracket-and-bisect to acceptance 0.25 +- 0.1
               on 2000-step trials from the prior mean (init_stepsize 0.1 in the example); chains start at the prior
               mean, the first 2000 steps discarded.

Not ported (documented, so a missing piece is not a silent difference): the random-feature emulators, pCN and Barker
proposals, autodiff, retain_var < 1 truncation and its null-space noise injection (a rank-deficient input covariance
raises here instead), learned white noise (noise_learn = true).

Use (FIT_GENERAL.md): the emulator is a search tool only. Every point reported from the posterior region is re-run on
the real model first; the output is the precision-needed column, each value's posterior SD over its prior SD.

    em = Emulator(Z, G, gamma)                     # Z: n x p inputs, G: n x M outputs, gamma: M x M or M variances
    post = sample(em, y, prior_mean, prior_cov, n=100_000, seed=1)
    post["z"], post["precision"]                   # posterior draws in z; posterior SD / prior SD per coordinate
"""
from __future__ import annotations

import numpy as np
from scipy.linalg import cho_factor, cho_solve
from scipy.optimize import minimize
from scipy.spatial.distance import cdist

# method settings (not worm quantities): value, label, basis
SETTINGS = {
    "log_bounds": ((np.log(1e-5), np.log(1e5)), "measured", "CES.jl optimize_hyperparameters! default kernbounds"),
    "rank_rtol": (1e-10, "guessed", "singular values below rtol x the largest count as rank-deficient"),
    "target_acc": (0.25, "measured", "CES.jl optimize_stepsize default"),
    "acc_tol": (0.1, "measured", "CES.jl optimize_stepsize default"),
    "trial_n": (2000, "measured", "CES.jl optimize_stepsize default N"),
    "max_iter": (20, "measured", "CES.jl optimize_stepsize default"),
    "max_expansions": (10, "measured", "CES.jl optimize_stepsize default"),
    "init_stepsize": (0.1, "measured", "CES.jl examples/Sinusoid/sample.jl"),
    "discard": (2000, "measured", "CES.jl examples/Sinusoid/sample.jl discard_initial"),
}
S = {k: v[0] for k, v in SETTINGS.items()}


class Decorrelator:
    """x -> S^-1/2 V' (x - mean), with S, V from the SVD of a symmetric matrix (decorrelator.jl), rows of V' signed
    so their first entry is positive."""

    def __init__(self, data, mat=None):
        data = np.atleast_2d(np.asarray(data, float))
        self.mean = data.mean(0)
        mat = np.cov(data.T, bias=False) if mat is None else np.atleast_2d(np.asarray(mat, float))
        _, s, vt = np.linalg.svd(mat)
        if s[-1] <= S["rank_rtol"] * s[0]:
            raise ValueError(f"rank-deficient structure matrix (smallest/largest singular value {s[-1] / s[0]:.2e}); "
                             "retain_var truncation is not ported")
        vt = vt * np.where(vt[:, :1] < 0, -1.0, 1.0)
        self.enc = vt / np.sqrt(s)[:, None]
        self.dec = vt.T * np.sqrt(s)[None, :]

    def encode(self, x):
        return (np.asarray(x, float) - self.mean) @ self.enc.T

    def decode(self, u):
        return np.asarray(u, float) @ self.dec.T + self.mean

    def encode_cov(self, c):
        return self.enc @ c @ self.enc.T

    def decode_cov(self, c):
        return self.dec @ c @ self.dec.T


def _r2(A, B, ell):
    """Scaled squared distances sum_d (a_d - b_d)^2 / ell_d^2 between the rows of A and B (n x m, never n x m x p)."""
    return cdist(A / ell, B / ell, "sqeuclidean")


class GP:
    """Zero-mean GP, SEArd kernel sf^2 exp(-r2/2) plus fixed noise variance `noise` (GaussianProcesses.jl GPE with
    SEArd and logNoise fixed)."""

    def __init__(self, X, y, noise=1.0):
        self.X, self.y, self.noise = np.asarray(X, float), np.asarray(y, float), float(noise)
        self.theta = np.zeros(self.X.shape[1] + 1)        # log lengths, log signal SD (start 1, as CES.jl)
        self._set(self.theta)

    def nlml(self, theta):
        """Negative log marginal likelihood and its gradient in theta = (log ell_1..p, log sf)."""
        X, y, n = self.X, self.y, len(self.y)
        ell, sf2 = np.exp(theta[:-1]), np.exp(2.0 * theta[-1])
        kf = sf2 * np.exp(-0.5 * _r2(X, X, ell))
        c = cho_factor(kf + self.noise * np.eye(n), lower=True)
        a = cho_solve(c, y)
        val = 0.5 * y @ a + np.sum(np.log(np.diag(c[0]))) + 0.5 * n * np.log(2.0 * np.pi)
        w = np.outer(a, a) - cho_solve(c, np.eye(n))      # dL/dtheta = 0.5 tr(w dK/dtheta)
        g = np.empty_like(theta)
        wk = w * kf
        for k in range(X.shape[1]):                       # dK/dlog ell_k = K_f (x_k - x'_k)^2 / ell_k^2
            dk = (X[:, k, None] - X[None, :, k]) / ell[k]
            g[k] = -0.5 * np.sum(wk * dk * dk)
        g[-1] = -0.5 * np.sum(w * 2.0 * kf)
        return val, g

    def optimise(self):
        lo, hi = S["log_bounds"]
        r = minimize(self.nlml, self.theta, jac=True, method="L-BFGS-B", bounds=[(lo, hi)] * len(self.theta))
        self._set(r.x)
        self.opt = r
        return self

    def _set(self, theta):
        self.theta = np.asarray(theta, float)
        self.ell, self.sf2 = np.exp(self.theta[:-1]), np.exp(2.0 * self.theta[-1])
        k = self.sf2 * np.exp(-0.5 * _r2(self.X, self.X, self.ell))
        self.c = cho_factor(k + self.noise * np.eye(len(self.y)), lower=True)
        self.alpha = cho_solve(self.c, self.y)

    def predict(self, Xs, add_noise=True):
        """Mean and variance at the rows of Xs (predict_y if add_noise, else predict_f)."""
        Xs = np.atleast_2d(Xs)
        ks = self.sf2 * np.exp(-0.5 * _r2(Xs, self.X, self.ell))
        mu = ks @ self.alpha
        v = cho_solve(self.c, ks.T)
        var = np.maximum(self.sf2 - np.sum(ks * v.T, 1), 0.0)
        return mu, var + (self.noise if add_noise else 0.0)


class Emulator:
    """Encoders plus one GP per encoded output (Emulator.jl with the default encoder schedule given Gamma)."""

    def __init__(self, Z, G, gamma, optimise=True):
        Z, G = np.asarray(Z, float), np.asarray(G, float)
        gam = np.diag(np.asarray(gamma, float)) if np.ndim(gamma) == 1 else np.asarray(gamma, float)
        self.zin = Decorrelator(Z)
        self.gout = Decorrelator(G, gam)
        U, W = self.zin.encode(Z), self.gout.encode(G)
        reg = np.diag(self.gout.encode_cov(gam))          # 1 by construction; kept as CES.jl computes it
        self.gps = [GP(U, W[:, i], noise=reg[i]) for i in range(W.shape[1])]
        if optimise:
            for gp in self.gps:
                gp.optimise()

    def predict(self, u, add_noise=True):
        """Encoded mean and diagonal variance at encoded inputs u (rows)."""
        out = [gp.predict(u, add_noise) for gp in self.gps]
        return np.stack([o[0] for o in out], -1), np.stack([o[1] for o in out], -1)

    def error(self, Z, G):
        """Held-out check: per encoded output, RMS error of the mean in units of the noise SD (encoded noise is 1)."""
        m, _ = self.predict(self.zin.encode(Z), add_noise=False)
        return np.sqrt(np.mean((m - self.gout.encode(G)) ** 2, 0))


class Forward:
    """The true map in the emulator's place (CES.jl ForwardMapWrapper): same encoders, exact G, variance = noise."""

    def __init__(self, em, g):
        self.em, self.g = em, g

    def predict(self, u, add_noise=True):
        z = self.em.zin.decode(np.atleast_2d(u))
        w = self.em.gout.encode(np.array([self.g(r) for r in z]))
        return w, np.ones_like(w)


class Posterior:
    """log density in encoded inputs u: emulated Gaussian likelihood of the encoded data plus the encoded prior."""

    def __init__(self, em, y, prior_mean, prior_cov, model=None):
        self.em, self.model = em, (em if model is None else model)
        self.w = em.gout.encode(np.asarray(y, float)[None, :])[0]
        self.m0 = em.zin.encode(np.asarray(prior_mean, float)[None, :])[0]
        self.c0 = em.zin.encode_cov(np.atleast_2d(np.asarray(prior_cov, float)))
        self.c0f = cho_factor(self.c0, lower=True)
        self.L = np.linalg.cholesky(self.c0)

    def logp(self, u):
        m, v = self.model.predict(u[None, :], add_noise=True)
        r = self.w - m[0]
        ll = -0.5 * np.sum(r * r / v[0] + np.log(2.0 * np.pi * v[0]))
        d = u - self.m0
        return ll - 0.5 * d @ cho_solve(self.c0f, d)


def rwm(post, n, step, seed=0, u0=None):
    """Random-walk Metropolis from u0 (default the prior mean): (chain n x p, acceptance ratio)."""
    rng = np.random.default_rng(seed)
    u = post.m0.copy() if u0 is None else np.array(u0, float)
    lp = post.logp(u)
    out, acc = np.empty((n, len(u))), 0
    for k in range(n):
        cand = u + step * post.L @ rng.standard_normal(len(u))
        lc = post.logp(cand)
        if np.log(rng.uniform()) < lc - lp:
            u, lp, acc = cand, lc, acc + 1
        out[k] = u
    return out, acc / n


def optimize_stepsize(post, seed=0, init=S["init_stepsize"]):
    """CES.jl's bracket-and-bisect: expand by 2 until the target acceptance is bracketed, then bisect geometrically;
    each trial a fresh S['trial_n']-step chain from the prior mean. Returns (step, [(step, acceptance)])."""
    tgt, tol, log, ok = S["target_acc"], S["acc_tol"], [], lambda a: abs(a - tgt) <= tol

    def acc_at(s):
        if len(log) >= S["max_iter"]:
            raise RuntimeError(f"optimize_stepsize: {S['max_iter']} trials without acceptance {tgt} +- {tol}: {log}")
        a = rwm(post, int(S["trial_n"]), s, seed=seed + len(log))[1]
        log.append((s, a))
        return a

    a = acc_at(init)
    if ok(a):
        return init, log
    lo = hi = init
    for _ in range(int(S["max_expansions"])):
        if a > tgt:
            lo, hi = hi, hi * 2.0
            a = acc_at(hi)
            if ok(a):
                return hi, log
            if a < tgt:
                break
        else:
            hi, lo = lo, lo / 2.0
            a = acc_at(lo)
            if ok(a):
                return lo, log
            if a > tgt:
                break
    else:
        raise RuntimeError(f"optimize_stepsize: target {tgt} not bracketed in {S['max_expansions']} expansions: {log}")
    while True:
        mid = np.sqrt(lo * hi)
        a = acc_at(mid)
        if ok(a):
            return mid, log
        lo, hi = (mid, hi) if a > tgt else (lo, mid)


def sample(em, y, prior_mean, prior_cov, n=100_000, seed=0, model=None):
    """Tuned RWM on the emulated (or, with model=Forward(...), the true) posterior; draws decoded to z."""
    post = Posterior(em, y, prior_mean, prior_cov, model)
    step, trials = optimize_stepsize(post, seed=seed + 1000)
    ch, acc = rwm(post, n + int(S["discard"]), step, seed=seed)
    z = em.zin.decode(ch[int(S["discard"]):])
    psd = np.sqrt(np.diag(np.atleast_2d(prior_cov)))
    return {"z": z, "mean": z.mean(0), "sd": z.std(0), "precision": z.std(0) / psd, "step": step,
            "acceptance": acc, "trials": trials}


def pairs(history):
    """Stack the calibrate step's (z, G(z)) pairs: history is a list of (Z_j, G_j, ok_j) per EKI iteration; members
    that failed physicality (ok False or non-finite G) are left out, as the EKI leaves them out."""
    Z, G = [], []
    for z, g, ok in history:
        z, g = np.asarray(z, float), np.asarray(g, float)
        keep = (np.ones(len(z), bool) if ok is None else np.asarray(ok, bool)) & np.isfinite(g).all(1)
        Z.append(z[keep])
        G.append(g[keep])
    return np.vstack(Z), np.vstack(G)
