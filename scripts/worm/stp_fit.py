"""Row 24 template-setting fit (pre-registered in docs/worm/night/2026-11-06_wbrain.md, item 1): the cholinergic
grain's depletion rate, resting and maximal recovery rates and recovery-Ca decay time, by least squares to Liu,
Hollopeter and Jorgensen 2009's 1 Hz and 5 Hz ACh trains (tau 0.58 +- 0.11 s and 0.09 +- 0.02 s; steady state about
50% of the first response at both). numpy reference (mech.plasticity.numpy_reference), one L-AChR synapse,
presynaptic 10 ms steps from -60 to 0 mV (pulse length guessed). The held-out bars are in stp_unit_check.py.

Usage: PYTHONPATH=src .venv/bin/python scripts/worm/stp_fit.py [out.json]
"""
from __future__ import annotations

import json
import sys

import numpy as np
from scipy.optimize import curve_fit, least_squares

from wormemu.mech import plasticity as P
from wormemu.mech import receptors as R

DT = 0.5
T = {s.id: s.template for s in P.SPECS + R.SPECS}
REL = dict(delta=5.0, k=0.1166666666666666, Vth=-20.0)       # the ledger's syn_exc_* (BAAIWorm)
REC = R.site_params(T, "lacr", 2)
NPULSE = {0.2: 12, 1.0: 20, 5.0: 50, 10.0: 50, 20.0: 100}
FREE = ("stp_ach_beta_per_ms", "stp_ach_k0_per_s", "stp_ach_kmax_per_s", "stp_ach_tauD_ms")


def train(hz, n=None, pulse_ms=10.0):
    n = n or NPULSE[hz]
    per = int(round(1000.0 / hz / DT))
    v = np.full(n * per, -60.0)
    for k in range(n):
        v[k * per:k * per + int(pulse_ms / DT)] = 0.0
    return v, per


def amplitudes(p, hz, grain="ach", form="dittman_regehr"):
    v, per = train(hz)
    G, _ = P.numpy_reference(v, DT, P.wsyn_params(p, grain, form, hab=False), REL,
                             REC if grain == "ach" else R.site_params(T, "gabacl", 2))
    return G.reshape(-1, per).max(1)


def fit_tau(A, hz):
    """Single exponential with a plateau through the amplitudes normalised to the first: (tau s, plateau)."""
    a, t = A / A[0], np.arange(len(A)) / hz
    f = lambda t, tau, pl: pl + (1 - pl) * np.exp(-t / tau)
    (tau, pl), _ = curve_fit(f, t, a, p0=(1.0 / hz, a[-1]), bounds=([1e-4, 0.0], [1e3, 2.0]), maxfev=20000)
    return float(tau), float(pl)


TARGET = {1.0: (0.58, 0.11), 5.0: (0.09, 0.02)}


def resid(z):
    p = {**T, **dict(zip(FREE, np.exp(z)))}
    out = []
    for hz, (tau, sd) in TARGET.items():
        tm, pl = fit_tau(amplitudes(p, hz), hz)
        out += [np.log(tm / tau) / (sd / tau), (pl - 0.5) / 0.05]
    return np.array(out)


def main():
    lo = np.log([next(s.lo for s in P.SPECS if s.id == k) for k in FREE])
    hi = np.log([next(s.hi for s in P.SPECS if s.id == k) for k in FREE])
    best = None
    for start in ([0.1, 0.2, 5.0, 500.0], [0.3, 0.5, 20.0, 1000.0], [0.05, 0.05, 2.0, 200.0]):
        r = least_squares(resid, np.log(start), bounds=(lo, hi), diff_step=0.05, max_nfev=300)
        if best is None or r.cost < best.cost:
            best = r
    vals = dict(zip(FREE, np.exp(best.x).tolist()))
    p = {**T, **vals}
    res = dict(free=vals, cost=float(best.cost), residuals_sd=best.fun.tolist(),
               fit={str(hz): dict(zip(("tau_s", "plateau"), fit_tau(amplitudes(p, hz), hz))) for hz in TARGET},
               target={str(k): v for k, v in TARGET.items()}, pulse_ms=10.0, receptor="lacr", dt_ms=DT)
    print(json.dumps(res, indent=1))
    if len(sys.argv) > 1:
        open(sys.argv[1], "w").write(json.dumps(res, indent=1))


if __name__ == "__main__":
    main()
