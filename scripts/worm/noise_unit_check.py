"""Row 26 unit checks (bars in docs/worm/night/2026-11-06_wbrain.md, written before running): mech.noise's shot-noise
generator alone (checks 1-4, numpy) and one wsyn in NEURON (check 5's single-synapse part).

Usage: PYTHONPATH=src .venv/bin/python scripts/worm/noise_unit_check.py [out.json]
"""
from __future__ import annotations

import json
import sys

import numpy as np

from wormemu.mech import noise as NZ
from wormemu.mech import receptors as R

T = {s.id: s.template for s in NZ.SPECS}
RT = {s.id: s.template for s in R.SPECS}
DT = 1.0
GQ = NZ.quantal_g_uS(T, RT, "lacr")
TAU = RT["rec_lacr_tau_off_ms"]
CV = T["noise_amp_cv"]


def run(rate_per_s, n, seconds, gq=GQ, seed=1, burn_ms=100):
    """n synapses whose deterministic conductance gives rate_per_s at the quantal size GQ (a different gq at the
    same conductance changes the rate by GQ/gq); returns (Shot, qn samples after burn-in, G samples, gd)."""
    gd = np.full(n, rate_per_s / 1000.0 * GQ * TAU)
    s = NZ.Shot(np.full(n, gq), np.full(n, TAU), CV, seed)
    qs, gs = [], []
    for k in range(int(seconds * 1000 / DT)):
        qn, _ = s.step(gd, DT)
        if k * DT >= burn_ms:
            qs.append(qn.copy())
            gs.append(s.G.copy())
    return s, np.array(qs), np.array(gs), gd


def main():
    res = {}
    s, _, _, _ = run(26.3, 100, 10.0, burn_ms=0)
    rate = s.n_ves / (100 * 10.0)
    peak = GQ * s.a_sum / s.n_ves * abs(RT["rec_lacr_erev_mV"] - T["noise_hold_mV"]) * 1000.0
    res["generator"] = dict(g_quantal_nS=GQ * 1000, vesicles_per_s=rate, mean_peak_pA=peak,
                            passed=bool(abs(rate / 26.3 - 1) < 0.02 and abs(peak / 17.6 - 1) < 0.02))
    e = np.exp(-DT / TAU)
    c = GQ * (TAU / DT) * (1 - e)
    mv = {}
    ok = True
    for r in (26.3, 1e3, 1e5):
        _, qs, gs, gd = run(r, 200, 20.0)
        lam = r / 1000.0
        exact = c ** 2 * lam * DT * (1 + CV ** 2) / (1 - e ** 2)
        campbell = lam * GQ ** 2 * (1 + CV ** 2) * TAU / 2
        var = float(gs.var())
        mv[str(r)] = dict(mean_qn=float(qs.mean()), var_over_exact=var / exact, var_over_campbell=var / campbell)
        ok &= abs(qs.mean() - 1) < 0.01 and abs(var / exact - 1) < 0.03 and abs(var / campbell - 1) < 0.10
    res["mean_variance"] = dict(**mv, passed=bool(ok))
    _, q1, _, _ = run(1e3, 200, 5.0)
    _, q2, _, _ = run(1e3, 200, 5.0, gq=GQ / 100)
    ratio = float(q1.std() / q2.std())
    res["limit"] = dict(sd_qn=float(q1.std()), sd_qn_gq_over_100=float(q2.std()), ratio=ratio,
                        passed=bool(abs(ratio / 10 - 1) < 0.05))
    a, b, c2 = (run(1e3, 20, 1.0, seed=sd)[1] for sd in (5, 5, 6))
    res["seeds"] = dict(same=bool(np.array_equal(a, b)), other_differs=bool(not np.array_equal(a, c2)),
                        passed=bool(np.array_equal(a, b) and not np.array_equal(a, c2)))
    res["neuron_mean"] = neuron_mean()
    print(json.dumps(res, indent=1, default=float))
    if len(sys.argv) > 1:
        open(sys.argv[1], "w").write(json.dumps(res, indent=1, default=float))


def neuron_mean(rate_per_s=2000.0, seconds=20.0):
    """One lacr wsyn, presynapse clamped at rest (-65 mV), postsynapse at -60 mV; gmax set so the resting release
    implies rate_per_s vesicles. Mean synaptic current with the noise against qn = 1."""
    from wormemu.brain import _neuron
    h = _neuron()
    secs = []
    for nm in ("pre", "post"):
        sc = h.Section(name=nm)
        sc.L = sc.diam = 5.0
        sc.insert("pas")
        secs.append(sc)
    pre, post = secs
    syn = h.wsyn(post(0.5))
    h.setpointer(pre(0.5)._ref_v, "vpre", syn)
    for k, v in R.site_params(RT, "lacr", 2).items():
        setattr(syn, k, v)
    cl = []
    for sc, v in ((pre, -65.0), (post, -60.0)):
        c = h.SEClamp(sc(0.5))
        c.dur1, c.amp1, c.rs = 1e9, v, 1e-3
        cl.append(c)
    h.dt, h.secondorder = 0.5, 0
    syn.gmax = 1.0
    h.finitialize(-65.0)
    h.fadvance()
    syn.gmax = rate_per_s / 1000.0 * GQ * TAU / syn.gd
    out = {}
    for noisy in (False, True):
        h.finitialize(-65.0)
        s = NZ.Shot([GQ], [TAU], CV, 3)
        cur = []
        for _ in range(int(seconds * 1000 / DT)):
            if noisy:
                syn.qn = float(s.step([syn.gd], DT)[0][0])
            for _ in range(2):
                h.fadvance()
                cur.append(syn.i)
        syn.qn = 1.0
        out["noisy" if noisy else "det"] = (float(np.mean(cur)), float(np.std(cur)), s.n_ves / seconds)
    rel = out["noisy"][0] / out["det"][0] - 1
    return dict(det_nA=out["det"][0], noisy_nA=out["noisy"][0], noisy_sd_nA=out["noisy"][1],
                vesicles_per_s=out["noisy"][2], rel_err=rel, passed=bool(abs(rel) < 0.02))


if __name__ == "__main__":
    main()
