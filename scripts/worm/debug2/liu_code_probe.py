"""Probe (wbrain2, 8 Nov 2026; DEBUG_TRIAGE line 7 remainder): Liu et al. 2018's AWA model as the authors ran it vs
as printed, one difference at a time, on the CPU. A probe only: nothing here is a default.

The authors' code (github.com/wormwhisperer/CElegansAWAActionPotentialAnalysis, qiangstoch3c.py `full_model`, the
version whose numbers equal Table S4: gK3 = 0.3 x 1.3 = gKr 0.39, gK5 = 0.7 x 1.3 = gKa 0.91, vc3 23; no licence, so
re-written here from its equations, not copied) differs from the bioRxiv 359935 equations and Table S4 in:
  kir   I_Kir = gKir (I0 - beta log(1 + exp(-(v - vK - I0)/beta)))       printed: -gKir(beta log(1 + exp(-(v - vK + I0)/beta)) + I0)
  cinfi 0.5 (1 + tanh((v - vc2)/dvc2)) / mx, mx = 3.612/4                   printed: (tanh(..) + 1)/c0, c0 = 0.55
  tc2   160 / cosh((v - vc3)/(2 dvc3))                                     printed: 160 / cosh((v - vc3)/dvc3)
  kr    gate (1 - bk), bk' = (hinf(v, -42, 5) - bk)/1800 (inactivating)    printed: kr' = (hinf(v, -42, 5) - kr)/1800
  ka    hinf(v, -32, 2), tau = 27000 + (3000 - 27000) 0.5 (1 + tanh(v + 52)/20)
                                                                           printed: hinf(v, -52, 20), tau from (-32, 4)
  cap   C = 1.5e-3 with pA, nS, mV, ms (membrane tau 0.006 ms)             Table S4: C = 1.5 pF (tau 6 ms)
`stochastic` adds the code's channel noise (run_model: after each step the Ca1, Ca2, Kr-inactivation and Ka gates
move by Poisson(|rate| n dt) sign(rate) / n, with n = 1000 Ca and nBK = nKB K channels; the code's job lists use
nBK = nKB in 100-5000). Fixed dt and a backward-Euler membrane here (the code: odeint, dt <= 0.25 ms); no clipping,
as in the code.

Usage: PYTHONPATH=src .venv/bin/python scripts/worm/debug2/liu_code_probe.py [OUT.json]
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
from scipy.integrate import solve_ivp
from scipy.optimize import brentq

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from senses_checks import spike_features  # noqa: E402

DIFFS = ("kir", "cinfi", "tc2", "kr", "ka", "cap")
P = dict(gCa=0.1, vCa=120.0, f=0.4, tc1=1.0, vc1=-21.6, dvc1=9.17, vc2=16.2, dvc2=-16.1, vc3=23.0, dvc3=24.0,
         mx=3.612 / 4, c0=0.55, vK=-84.0, gK1=1.5, gK2=1.0, gK3=0.1, gKr=0.39, gKa=0.91, gKir=0.8, I0=5.0, beta=5.0,
         gL=0.25, vL=-65.0)


def h(v, a, b):
    return 0.5 * (1.0 + np.tanh((v - a) / b))


def model(printed):
    """printed: the set of DIFFS taken as printed; the rest as the authors' code."""
    pr = set(printed)
    C = 1.5 if "cap" in pr else 1.5e-3

    def cinf(v):
        a = h(v, P["vc1"], P["dvc1"])
        i = (np.tanh((v - P["vc2"]) / P["dvc2"]) + 1) / P["c0"] if "cinfi" in pr else h(v, P["vc2"], P["dvc2"]) / P["mx"]
        return a * i

    def tc2(v):
        return 160.0 / np.cosh((v - P["vc3"]) / (P["dvc3"] if "tc2" in pr else 2 * P["dvc3"]))

    def kir(v):
        if "kir" in pr:
            return -P["gKir"] * (P["beta"] * np.log1p(np.exp(-(v - P["vK"] + P["I0"]) / P["beta"])) + P["I0"])
        return P["gKir"] * (P["I0"] - P["beta"] * np.logaddexp(0.0, -(v - P["vK"] - P["I0"]) / P["beta"]))

    def kr_inf(v):                                # the open fraction's target (code: 1 - bk)
        return h(v, -42.0, 5.0) if "kr" in pr else 1.0 - h(v, -42.0, 5.0)

    def ka_inf(v):
        return h(v, -52.0, 20.0) if "ka" in pr else h(v, -32.0, 2.0)

    def ka_tau(v):
        if "ka" in pr:
            return 27000.0 + 0.5 * (3000.0 - 27000.0) * (np.tanh((v + 32.0) / 4.0) + 1)
        return 27000.0 + (3000.0 - 27000.0) * 0.5 * (1 + np.tanh(v + 52.0) / 20.0)

    def gates_inf(v):
        A = cinf(v)
        c = A / (1 + A)
        return np.array([c, c, h(v, 2.0, 10.0), h(v, 13.0, 20.0), h(v, -25.0, 5.0), kr_inf(v), ka_inf(v)])

    def current(v, s):
        c1, c2, k1, k2, k3, kr, ka = s
        iCa = P["gCa"] * (c1 + P["f"] * c2) * (v - P["vCa"])
        iK = (P["gK1"] * k1 + P["gK2"] * k2 + P["gK3"] * k3 + P["gKr"] * h(v, -42.0, 5.0) * kr
              + P["gKa"] * ka) * (v - P["vK"])
        return iCa + iK + kir(v) + P["gL"] * (v - P["vL"])

    def rhs(t, y, I_fn):
        v, s = y[0], y[1:]
        c1, c2, k1, k2, k3, kr, ka = s
        A, t2 = cinf(v), tc2(v)
        return np.array([(-current(v, s) + I_fn(t)) / C,
                         (A * (1 - c2) - c1) / P["tc1"] - (c1 - c2) / t2, (c1 - c2) / t2,
                         (h(v, 2.0, 10.0) - k1) / 30.0, (h(v, 13.0, 20.0) - k2) / 1000.0,
                         (h(v, -25.0, 5.0) - k3) / 1000.0, (kr_inf(v) - kr) / 1800.0, (ka_inf(v) - ka) / ka_tau(v)])

    def rest():
        f = lambda v: current(v, gates_inf(v))                 # noqa: E731
        vs = np.linspace(-120, 40, 1601)
        fs = np.array([f(v) for v in vs])
        return [brentq(f, vs[k], vs[k + 1]) for k in range(len(vs) - 1) if np.sign(fs[k]) != np.sign(fs[k + 1])]
    return rhs, rest, gates_inf


def stochastic(currents, seeds, n_k=500, n_ca=1000, T=5000.0, t_pre=500.0, dt=0.05):
    """The authors' code form with their channel noise, all (current, seed) traces at once. Returns t (from step onset),
    V [trace, time] and the (current, seed) of each trace."""
    rhs, rest, gates_inf = model(())
    pairs = [(I, sd) for I in currents for sd in seeds]
    I_step = np.array([p[0] for p in pairs], float)
    rng = np.random.default_rng(seeds[0] * 7919 + len(pairs))
    v0 = rest()[0]
    S = np.tile(gates_inf(v0), (len(pairs), 1)).T.copy()          # c1, c2, k1, k2, k3, open Kr fraction, ka
    bk = 1.0 - S[5]
    v = np.full(len(pairs), v0)
    C = 1.5e-3

    def i_ion(v, S, bk):
        c1, c2, k1, k2, k3, _, ka = S
        return (P["gCa"] * (c1 + P["f"] * c2) * (v - P["vCa"])
                + (P["gK1"] * k1 + P["gK2"] * k2 + P["gK3"] * k3 + P["gKr"] * h(v, -42.0, 5.0) * (1 - bk)
                   + P["gKa"] * ka) * (v - P["vK"])
                + P["gKir"] * (P["I0"] - P["beta"] * np.logaddexp(0.0, -(v - P["vK"] - P["I0"]) / P["beta"]))
                + P["gL"] * (v - P["vL"]))

    def flip(rate, n):
        return rng.poisson(np.abs(rate * dt * n)) * np.sign(rate) / n

    n_pre, n_on = int(t_pre / dt), int(T / dt)
    out = np.empty((len(pairs), n_on))
    for k in range(n_pre + n_on):
        c1, c2, k1, k2, k3, _, ka = S
        m1, m2 = h(v, P["vc1"], P["dvc1"]), h(v, P["vc2"], P["dvc2"])
        t2 = 80.0 / np.cosh((v - P["vc3"]) / (2 * P["dvc3"]))
        dc1 = (m1 * m2 / P["mx"] * (1 - c2) - c1) / P["tc1"] - (c1 - c2) / (2 * t2)
        dc2 = (c1 - c2) / (2 * t2)
        dbk = (h(v, -42.0, 5.0) - bk) / 1800.0
        tka = 27000.0 + (3000.0 - 27000.0) * 0.5 * (1 + np.tanh(v + 52.0) / 20.0)
        dka = (h(v, -32.0, 2.0) - ka) / tka
        S[0], S[1] = c1 + flip(dc1, n_ca), c2 + flip(dc2, n_ca)
        bk = bk + flip(dbk, n_k)
        S[6] = ka + flip(dka, n_k)
        for j, b, tau in ((2, (2.0, 10.0), 30.0), (3, (13.0, 20.0), 1000.0), (4, (-25.0, 5.0), 1000.0)):
            S[j] = h(v, *b) + (S[j] - h(v, *b)) * np.exp(-dt / tau)
        I = I_step if k >= n_pre else 0.0
        vn = v.copy()
        for _ in range(4):                                         # Newton on C (vn - v)/dt = I - i_ion(vn)
            F = C * (vn - v) / dt - I + i_ion(vn, S, bk)
            dF = C / dt + (i_ion(vn + 1e-4, S, bk) - i_ion(vn - 1e-4, S, bk)) / 2e-4
            vn = vn - F / dF
        v = vn
        if k >= n_pre:
            out[:, k - n_pre] = v
    return np.arange(n_on) * dt, out, pairs


def run(printed, steps=range(1, 31), T=1000.0, t_on=100.0):
    rhs, rest, gates_inf = model(printed)
    roots = rest()
    v0 = roots[0]
    res = dict(printed=sorted(printed), rest_roots_mV=[round(r, 2) for r in roots])
    for I in steps:
        I_fn = lambda t, I=I: I if t_on <= t < t_on + T else 0.0      # noqa: E731
        ts = np.arange(0, t_on + T + 0.01, 0.05)
        sol = solve_ivp(rhs, (0, ts[-1]), np.concatenate([[v0], gates_inf(v0)]), method="LSODA", t_eval=ts,
                        args=(I_fn,), rtol=1e-8, atol=1e-10, max_step=0.5)
        sel = sol.t >= t_on
        f = spike_features(sol.t[sel], sol.y[0][sel])
        if f:
            res.update(first_step_pA=I, first=f)
            break
    return res


def stochastic_summary(currents=(2, 4, 6, 8, 10, 12, 16), seeds=(1, 2, 3), n_k=500):
    t, V, pairs = stochastic(currents, seeds, n_k=n_k)
    rows = []
    for (I, sd), v in zip(pairs, V):
        dv = np.gradient(v, t)
        up = np.nonzero((dv[1:] > 5.0) & (dv[:-1] <= 5.0))[0]
        f = spike_features(t, v)
        rows.append(dict(I_pA=I, seed=sd, n_upstrokes=int(len(up)), plateau_mV=round(float(np.median(v[t > 500])), 1),
                         first=f))
    return dict(n_k=n_k, rows=rows)


if __name__ == "__main__":
    if sys.argv[1:2] == ["stochastic"]:
        out = stochastic_summary(n_k=int(sys.argv[2]) if len(sys.argv) > 2 else 500)
        s = json.dumps(out, indent=1)
        print(s)
        if len(sys.argv) > 3:
            Path(sys.argv[3]).write_text(s)
        sys.exit()
    out = {"code": run(())}
    for d in DIFFS:
        out[f"code_but_{d}_printed"] = run((d,))
    out["printed_all"] = run(DIFFS)
    out["printed_but_kir_code"] = run(tuple(d for d in DIFFS if d != "kir"))
    out["bars"] = ("Liu 2018: rest -75.3 (Fig 2E fit), threshold -34.0 +- 0.6, amplitude 25.8 +- 0.8, peak -8.1 +- 0.6, "
                   "half-width 18.0 +- 0.8 ms (SEM)")
    s = json.dumps(out, indent=1)
    print(s)
    if len(sys.argv) > 1:
        Path(sys.argv[1]).write_text(s)
