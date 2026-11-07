"""Fit 1 objective (docs/worm/FIT1.md): reduced chi-square of the model's statistic against Randi 2023's published
dF/F, over the terms whose stimulated neuron is in `targets` (the off-diagonal pairs and the autoresponses).
sigma_ij^2 = s_trial^2 / n_ij + s_floor^2 (fit1_targets.py)."""
import numpy as np


def load(path):
    z = np.load(path, allow_pickle=False)
    return z["terms"], float(z["s_trial"]) if "s_trial" in z else None, float(z["s_floor"]) if "s_floor" in z else None


def sigma(T, s_trial, s_floor):
    return np.sqrt(s_trial ** 2 / np.maximum(T["n"], 1) + s_floor ** 2)


def model_values(T, stat, names, targets):
    """The model's value for each term (NaN where the term's stimulated neuron is not in targets)."""
    ni = {n: k for k, n in enumerate(names)}
    tj = {t: k for k, t in enumerate(targets)}
    m = np.full(len(T), np.nan)
    for k, (i, j) in enumerate(zip(T["resp"], T["stim"])):
        if j in tj and i in ni:
            m[k] = stat[ni[i], tj[j]]
    return m


def chi2(T, m, s_trial, s_floor):
    ok = np.isfinite(m)
    r = (m[ok] - T["y"][ok]) / sigma(T[ok], s_trial, s_floor)
    return float(np.mean(r ** 2)) if ok.any() else np.nan, int(ok.sum())


def scores(T, m, s_trial, s_floor):
    """Loss and the descriptive scores (sign agreement and r on significant off-diagonal pairs)."""
    ok = np.isfinite(m)
    off = T["resp"] != T["stim"]
    sig = ok & off & (T["q"] < 0.05)
    out = dict(chi2=chi2(T, m, s_trial, s_floor)[0], n=int(ok.sum()),
               chi2_off=chi2(T[off], m[off], s_trial, s_floor)[0], chi2_self=chi2(T[~off], m[~off], s_trial, s_floor)[0],
               n_sig=int(sig.sum()))
    if sig.sum() > 2:
        out["sign_agree_sig"] = float(np.mean(np.sign(m[sig]) == np.sign(T["y"][sig])))
        out["r_sig"] = float(np.corrcoef(m[sig], T["y"][sig])[0, 1]) if np.std(m[sig]) > 0 else np.nan
    if (ok & off).sum() > 2 and np.std(m[ok & off]) > 0:
        out["r_off"] = float(np.corrcoef(m[ok & off], T["y"][ok & off])[0, 1])
    return out
