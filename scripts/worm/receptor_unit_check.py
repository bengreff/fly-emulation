"""Row 7 unit checks for the receptor classes (wsyn.mod, mech/receptors.py), isolated: two bare sections, one wsyn,
both voltage-clamped. Bars are in docs/worm/night/2026-11-06_wbrain.md (written before running).

1. UNC-49 (gabacl) saturating GABA step: decay tau of the current vs Bamber et al. 2005 (149 +- 10 ms, B/C).
2. L-AChR vs ACR-16, the same ACh step: ratio of decay taus vs "about 40x" (PMC10480131).
3. NMJ GABA IPSC after a 2 ms presynaptic step at the template values: decay tau vs Liu et al. 2009 (24.8 +- 2.7 ms).
Also code checks: instantaneous mode gives half activation at T = EC50; the NMDA-like class's Mg block matches
Jahr and Stevens' B(V).

Usage: PYTHONPATH=src .venv/bin/python scripts/worm/receptor_unit_check.py [out.json]
"""
from __future__ import annotations

import json
import sys

import numpy as np
from scipy.optimize import curve_fit

from wormemu.brain import _neuron
from wormemu.mech import receptors as R

P = {s.id: s.template for s in R.SPECS}
DT = 0.025


def run(c, pre_steps, t_end, mode=2, tmax_mM=None, v_post=-60.0, extra=None):
    """Current (nA, outward positive) through one class-c wsyn; pre_steps [(t_on, t_off, mV)] over -60 mV."""
    h = _neuron()
    pre, post = h.Section(name="pre"), h.Section(name="post")
    for s in (pre, post):
        s.L = s.diam = 10.0
        s.insert("pas")
    syn = h.wsyn(post(0.5))
    h.setpointer(pre(0.5)._ref_v, "vpre", syn)
    syn.gmax, syn.Vth, syn.delta, syn.k = 0.001, -20.0, 5.0, 0.1166666666666666
    for q, x in {**R.site_params(P, c, mode), **(extra or {})}.items():
        setattr(syn, q, x)
    if tmax_mM is not None:
        syn.tmax = tmax_mM
    cp, cq = h.SEClamp(pre(0.5)), h.SEClamp(post(0.5))
    cp.rs = cq.rs = 1e-3
    cq.dur1, cq.amp1 = 1e9, v_post
    t = np.arange(0, t_end, DT)
    vp = np.full(len(t), -60.0)
    for a, b, v in pre_steps:
        vp[(t >= a) & (t < b)] = v
    vec, tvec = h.Vector(vp), h.Vector(t)               # both kept alive through the run
    cp.dur1, cp.amp1 = 1e9, -60.0
    vec.play(cp._ref_amp1, tvec, 1)
    ti, ii = h.Vector().record(h._ref_t), h.Vector().record(syn._ref_i)
    h.dt = DT
    h.finitialize(-60.0)
    h.continuerun(t_end)
    return np.array(ti), np.array(ii)


def decay_tau(t, i, t0, t1):
    """Single-exponential fit i = c + A exp(-(t - t_peak)/tau) from the peak (after t0) to t1."""
    m = (t >= t0) & (t <= t1)
    tt, y = t[m], np.abs(i[m])
    k = int(np.argmax(y))
    tt, y = tt[k:] - tt[k], y[k:]
    f = lambda x, c, A, tau: c + A * np.exp(-x / tau)             # noqa: E731
    p, _ = curve_fit(f, tt, y, p0=(y[-1], y[0] - y[-1], max(1.0, (tt[-1] - tt[0]) / 5)), maxfev=20000)
    return float(p[2]), float(p[0] / (p[0] + p[1]))


def main():
    res = {}
    t, i = run("gabacl", [(50, 1050, 50.0)], 1100, tmax_mM=10.0)
    tau, ssf = decay_tau(t, i, 50, 1050)
    res["unc49_step"] = dict(tau_ms=round(tau, 1), steady_over_peak=round(ssf, 3), bar="149 ms +- 10% (134-164)",
                             passed=bool(134.1 <= tau <= 163.9))
    tl, _ = decay_tau(*run("lacr", [(50, 20050, 50.0)], 20100, tmax_mM=10.0), 50, 20050)
    tn, _ = decay_tau(*run("acr16", [(50, 1050, 50.0)], 1100, tmax_mM=10.0), 50, 1050)
    res["lacr_vs_acr16"] = dict(lacr_tau_ms=round(tl, 1), acr16_tau_ms=round(tn, 1), ratio=round(tl / tn, 1),
                                bar="ratio 20-80", passed=bool(20 <= tl / tn <= 80))
    t, i = run("gabacl", [(50, 52, 50.0)], 400)
    tau, _ = decay_tau(t, i, 50, 400)
    pk = float(np.max(np.abs(i)))
    res["nmj_ipsc"] = dict(tau_ms=round(tau, 1), peak_nA_per_nS=round(pk / 1.0, 4), bar="24.8 +- 2.7 ms (22.1-27.5)",
                           passed=bool(22.1 <= tau <= 27.5))
    # code checks: half activation at T = EC50 (instantaneous); Mg block
    c = "lacr"
    sinf = 1.0 / (1 + np.exp((-20.0 - 50.0) / 5.0))
    t, i = run(c, [(0, 200, 50.0)], 200, mode=1, tmax_mM=P[f"rec_{c}_ec50_uM"] / 1000.0 / sinf, v_post=-60.0)
    g = i[-1] / (-60.0 - P[f"rec_{c}_erev_mV"]) / 0.001
    res["ec50_half"] = dict(open_fraction=round(float(g), 4), bar="0.5 +- 0.005", passed=bool(abs(g - 0.5) < 0.005))
    b = {}
    for v in (-60.0, 40.0):
        t, i = run("nmr", [(0, 3000, 50.0)], 3000, mode=1, tmax_mM=10.0, v_post=v)
        b[v] = i[-1] / (v - P["rec_nmr_erev_mV"])
    js = lambda v: 1 / (1 + np.exp(-0.062 * v) * 1.0 / 3.57)       # noqa: E731
    ratio, want = float(b[-60.0] / b[40.0]), float(js(-60.0) / js(40.0))
    res["mg_block"] = dict(g_ratio_m60_p40=round(ratio, 4), jahr_stevens=round(want, 4),
                           passed=bool(abs(ratio - want) < 1e-3 * want))
    print(json.dumps(res, indent=1))
    if len(sys.argv) > 1:
        open(sys.argv[1], "w").write(json.dumps(res, indent=1))


if __name__ == "__main__":
    main()
