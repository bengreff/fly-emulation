"""Row 26 channel-noise unit checks (bars in docs/worm/night/2026-11-06_wbrain.md, written before running): the
expansion and OU update of mech.noise alone (checks 1-3, numpy), then one neuron's soma in NEURON (check 4).

Usage: PYTHONPATH=src .venv/bin/python scripts/worm/chnoise_unit_check.py [out.json]
"""
from __future__ import annotations

import json
import sys

import numpy as np

from wormemu.mech import noise as NZ


def check_weights(rng):
    worst = 0.0
    for ch, (_, subs, _) in NZ.CHANNEL_GATES.items():
        for _, gates in subs:
            pw = [n for _, _, n, _ in gates]
            J, b = NZ.terms(pw)
            x, t = rng.uniform(0, 1, (len(pw), 200)), rng.uniform(0.1, 100, (len(pw), 200))
            W, _ = NZ.weights(x, t, pw, J, b)
            p = np.prod(x ** np.array(pw)[:, None], axis=0)
            worst = max(worst, float(np.abs(W.sum(1) - (p - p * p)).max()))
    return dict(max_abs_err=worst, passed=bool(worst < 1e-12))


def acf(x, lags, dt):
    x = x - x.mean(axis=0)
    v = (x * x).mean()
    return v, [float((x[int(round(L / dt)):] * x[:-int(round(L / dt))]).mean() / v) for L in lags]


def markov_vs_ou(gates, N=200, R=40, T_ms=20000.0, dt=0.25, seed=2):
    """gates [(x, tau, power)] at fixed voltage. Exact Markov: every subunit of every channel a two-state process
    with exact transition probabilities over dt; open fraction = mean over channels of all-subunits-open. OU: the
    expansion's terms, point updates. R independent populations; open-fraction variance and normalised ACF."""
    rng = np.random.default_rng(seed)
    lags = (1.0, 5.0, 20.0)
    nsteps = int(T_ms / dt)
    subs = [(x, tau) for x, tau, n in gates for _ in range(n)]
    S = np.array([rng.random((R, N)) < x for x, _ in subs])            # start stationary
    stay = np.array([x + (1 - x) * np.exp(-dt / tau) for x, tau in subs])[:, None, None]
    go = np.array([x * (1 - np.exp(-dt / tau)) for x, tau in subs])[:, None, None]
    fm = np.empty((nsteps, R))
    for k in range(nsteps):
        u = rng.random(S.shape)
        S = np.where(S, u < stay, u < go)
        fm[k] = S.all(axis=0).mean(axis=1)
    pw = [n for *_, n in gates]
    x = np.array([[g[0]] for g in gates])
    tau = np.array([[g[1]] for g in gates])
    J, b = NZ.terms(pw)
    W, r = NZ.weights(x, tau, pw, J, b)
    s2 = np.broadcast_to(W / N, (R, W.shape[1]))
    tJ = np.broadcast_to(1.0 / r, (R, W.shape[1]))
    y = np.sqrt(s2) * rng.standard_normal(s2.shape)
    e = np.exp(-dt / tJ)
    fo = np.empty((nsteps, R))
    for k in range(nsteps):
        y = y * e + np.sqrt(s2 * (1 - e * e)) * rng.standard_normal(s2.shape)
        fo[k] = y.sum(axis=1)
    p = float(np.prod(x[:, 0] ** np.array(pw)))
    vm, am = acf(fm, lags, dt)
    vo, ao = acf(fo, lags, dt)
    C = lambda t: np.prod([(g[0] ** 2 + g[0] * (1 - g[0]) * np.exp(-t / g[1])) ** g[2] for g in gates]) - p * p
    return dict(var_markov=vm, var_ou=vo, var_exact=(p - p * p) / N, var_ratio=vm / vo, acf_markov=am, acf_ou=ao,
                acf_exact=[float(C(L) / C(0)) for L in lags],
                passed=bool(abs(vm / vo - 1) < 0.03 and max(abs(a - c) for a, c in zip(am, ao)) < 0.03))


def step_mean(rng, dt=1.0, R=20000, steps=200):
    out, ok = {}, True
    for tau in (0.5, 5.0, 500.0):
        s2 = np.ones(R)
        t = np.full(R, tau)
        y = rng.standard_normal(R)
        ms = np.empty((steps, R))
        for k in range(steps):
            y, m = NZ.ou_step(y, s2, t, dt, rng.standard_normal(R), rng.standard_normal(R))
            ms[k] = m
        u = dt / tau
        want = 2 * tau ** 2 * (u - 1 + np.exp(-u)) / dt ** 2
        var = float(ms.var(axis=1).mean())
        last = ms[-1]
        z = float(last.mean() / (last.std() / np.sqrt(R)))
        out[str(tau)] = dict(var=var, analytic=want, ratio=var / want, mean_z=z)
        ok &= abs(var / want - 1) < 0.03 and abs(z) < 3
    out["passed"] = bool(ok)
    return out


def neuron_limits(cell="AVAL", seconds=2.0):
    """One neuron, soma clamped at -30 mV (gates deterministic, so the injected current scales exactly): current sd
    at the template unit conductances and at 1/100 of them; the same seed replays; channels per soma."""
    from wormemu.brain import Brain
    b = Brain(cells=[cell], toggles=dict(quantal_noise="off", channel_noise="diffusion"))
    nz = next(m for m in b.mechs if type(m).__module__ == "wormemu.mech.noise").c
    h = b.h
    cl = h.SEClamp(b.soma[0](0.5))
    cl.dur1, cl.amp1, cl.rs = 1e9, -30.0, 1e-3

    def run():
        b.reset()
        I = []
        for _ in range(int(seconds * 1000)):
            b.step()
            I.append(b.mech_out["channel_noise"]["I_rms_pA"])
        return np.array(I)

    I1 = run()
    I1b = run()
    sg = b.soma[0](0.5)              # units: the module's Gmax against NEURON's own Ca current (EGL-19, UNC-2, CCA-1)
    i_neuron_pA = sg.ica * sg.area() * 10.0              # mA/cm2 x um2 = 10 pA
    i_module_pA = 0.0
    for g in nz.groups:
        if g["ch"] in ("egl19", "unc2", "cca1"):
            mm = getattr(sg, g["ch"])
            i_module_pA += float(nz._read(g["gb"])[0] * g["area"][0] * mm.m ** (2 if g["ch"] == "cca1" else 1) * mm.h
                                 * (sg.v - 60.0))
    units = dict(neuron_pA=i_neuron_pA, module_pA=i_module_pA,
                 passed=bool(abs(i_module_pA / i_neuron_pA - 1) < 1e-6))
    per = {g["ch"]: float(nz._read(g["gb"])[0] * g["area"][0] * sum(s["w"] for s in g["subs"]) / g["gam"])
           for g in nz.groups}
    for g in nz.groups:
        g["gam"] /= 100.0
    I2 = run()
    ratio = float(np.sqrt(np.mean(I1 ** 2)) / np.sqrt(np.mean(I2 ** 2)))
    return dict(cell=cell, units=units, I_rms_pA=float(np.sqrt(np.mean(I1 ** 2))), ratio_gamma_over_100=ratio,
                replay=bool(np.array_equal(I1, I1b)), channels=per, channels_total=float(sum(per.values())),
                passed=bool(abs(ratio / 10 - 1) < 0.05 and np.array_equal(I1, I1b) and units["passed"]))


def main():
    rng = np.random.default_rng(1)
    res = dict(weights=check_weights(rng),
               markov_one_gate=markov_vs_ou([(0.3, 5.0, 1)]),
               markov_m3h=markov_vs_ou([(0.4, 2.0, 3), (0.6, 20.0, 1)]),
               step_mean=step_mean(rng))
    print(json.dumps(res, indent=1, default=float), flush=True)
    res["neuron"] = neuron_limits()
    print(json.dumps(res["neuron"], indent=1, default=float))
    if len(sys.argv) > 1:
        open(sys.argv[1], "w").write(json.dumps(res, indent=1, default=float))


if __name__ == "__main__":
    main()
