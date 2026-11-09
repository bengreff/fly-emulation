"""Never-checked row 17 (wbrain2, 9 Nov 2026): AWA's diacetyl dose-response against Larsch, Ventimiglia, Bargmann and
Albrecht 2013 (PNAS 110:E4266, PMC3831453) Fig S6 and Fig 4D, pre-registered in the night file ("Item 9a").
Template worm, default toggles, the observation noise off (obs_noise_dff 0, readout only). 30 s settle, then per
concentration 50 s buffer and a 10 s diacetyl pulse, ascending (buffer, 1 nM to 100 uM in decades), then 10 s.
Nemadipine-A: Liu's gCa (dens_awa_ca, the AWA model's Ca current) scaled by 1 - f before reset (a drug, not a Spec).
Peak = max dF/F0 during the pulse minus max in the 10 s before it (Larsch's methods); the four-parameter sigmoid
F = Fmin + (Fmax - Fmin) / (1 + (EC50 / C)^beta) fitted to the six concentrations by least squares.
Usage: python awa_dose.py <full|alone> [f]     -> runs/worm/wbrain2/awa_dose/<build>_f<f>.json
       python awa_dose.py score                  (the night file's bars 1 to 3)
"""
from __future__ import annotations

import copy
import json
import sys
import time
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[3]
OUT = ROOT / "runs/worm/wbrain2/awa_dose"
AWA, DT = ("AWAL", "AWAR"), 4.0
CONC_UM = [0.0, 1e-3, 1e-2, 1e-1, 1.0, 10.0, 100.0]
SETTLE_MS, PERIOD_MS, PULSE_MS, TAIL_MS = 30000.0, 60000.0, 10000.0, 10000.0
BAR_EC50_NM = (11.0, 690.0)               # Larsch S6B, the lowest and highest of 22 animals (digitised)
LARSCH_NM, NEMA_NM = 30.6, 2500.0         # S6 median; Fig 4D with 10 uM nemadipine-A
KEEP = 5                                  # samples kept in the JSON: every 5th step (20 ms)


def t_on(k):
    return SETTLE_MS + k * PERIOD_MS + (PERIOD_MS - PULSE_MS)


def run(build, f):
    sys.path.insert(0, str(ROOT / "src"))
    from wormemu.brain import Brain, sample_worm
    from wormemu.interface import default_observation
    spec = copy.copy(sample_worm(None))
    spec.values = dict(spec.values)
    spec.values["obs_noise_dff"] = 0.0
    b = Brain(spec, cells=list(AWA) if build == "alone" else None)
    _, _, base, _ = b._gt["dens_awa_ca"]
    base *= 1.0 - f                       # reset scatters the base: the block holds for the whole run
    b.reset()
    ix = [b.idx[c] for c in AWA]
    n = int(round((t_on(len(CONC_UM) - 1) + PULSE_MS + TAIL_MS) / DT))
    t, v, ca, gc, stim = [], [], [], [], []
    for _ in range(n):
        c = 0.0
        for k, x in enumerate(CONC_UM):
            if t_on(k) <= b.t < t_on(k) + PULSE_MS:
                c = x
        o = default_observation(b.t)
        o.head["diacetyl_uM"] = c
        out = b.step(o, DT)
        t.append(b.t)
        v.append(out.v_mV[ix].tolist())
        ca.append(np.asarray(out.ca_uM)[ix].tolist())
        gc.append(np.asarray(out.gcamp_dff)[ix].tolist())
        stim.append(c)
    return dict(t=t, v=v, ca=ca, gc=gc, stim=stim)


def peaks(t, y):
    """Larsch's peak per concentration: max during the pulse minus max in the 10 s before it."""
    t, y = np.asarray(t), np.asarray(y)
    out = []
    for k in range(len(CONC_UM)):
        a = t_on(k)
        on, pre = (t > a) & (t <= a + PULSE_MS), (t > a - PULSE_MS) & (t <= a)
        out.append(float(y[on].max() - y[pre].max()))
    return out


def sigmoid(logc, fmin, fmax, logec, beta):
    return fmin + (fmax - fmin) / (1.0 + 10.0 ** ((logec - logc) * beta))


def fit(pk):
    """EC50 (nM) of the four-parameter sigmoid over the six concentrations; None if the fit fails."""
    from scipy.optimize import curve_fit
    x, y = np.log10(np.array(CONC_UM[1:]) * 1e3), np.array(pk[1:])     # log10 nM
    if not np.isfinite(y).all() or np.ptp(y) <= 0:
        return None
    best = None
    for l0 in (0.5, 1.5, 2.5, 3.5, 4.5):
        try:
            p, _ = curve_fit(sigmoid, x, y, p0=(y.min(), y.max(), l0, 1.0),
                             bounds=([-np.inf, -np.inf, -2.0, 0.2], [np.inf, np.inf, 7.0, 10.0]), maxfev=20000)
        except RuntimeError:
            continue
        sse = float(((sigmoid(x, *p) - y) ** 2).sum())
        if best is None or sse < best[0]:
            best = (sse, p)
    if best is None:
        return None
    fmin, fmax, logec, beta = best[1]
    return dict(ec50_nM=float(10 ** logec), fmin=float(fmin), fmax=float(fmax), beta=float(beta), sse=best[0])


def offline_gcamp(t, ca_uM, form):
    """GCaMP dF/F from the recorded Ca with the observation module's binding (a sensitivity, not the readout)."""
    sys.path.insert(0, str(ROOT / "src"))
    from wormemu.mech import observation as O
    P = O.P
    kd, n, R, th = (P[f"obs_{form}_{k}"] for k in ("kd_nM", "hill", "range", "thalf_ms"))
    B0 = O.hill(P["obs_ca_rest_nM"], kd, n)
    B, out, t_prev = B0, [], 0.0
    for tt, c in zip(t, ca_uM):
        B = O.binding_step(B, c * 1000.0, kd, n, th, tt - t_prev)
        t_prev = tt
        out.append(O.dff(B, B0, R))
    return out


def analyse(r):
    t = r["t"]
    res = {}
    for j, cell in enumerate(AWA):
        tr = {"gcamp6s": [g[j] for g in r["gc"]], "ca": [c[j] for c in r["ca"]]}
        tr["gcamp6f_offline"] = offline_gcamp(t, tr["ca"], "gcamp6f")
        tr["gcamp6s_offline"] = offline_gcamp(t, tr["ca"], "gcamp6s")
        res[cell] = {k: dict(peaks=peaks(t, y), fit=fit(peaks(t, y))) for k, y in tr.items()}
        v = np.array([x[j] for x in r["v"]])
        res[cell]["v_pre_pulse_mV"] = [float(v[(np.asarray(t) > t_on(k) - 1000) & (np.asarray(t) <= t_on(k))].mean())
                                       for k in range(len(CONC_UM))]
        res[cell]["v_max_pulse_mV"] = [float(v[(np.asarray(t) > t_on(k)) & (np.asarray(t) <= t_on(k) + PULSE_MS)].max())
                                       for k in range(len(CONC_UM))]
    return res


def score():
    R = {p.stem: json.loads(p.read_text()) for p in sorted(OUT.glob("*.json"))}
    for name, r in R.items():
        a = r["analysis"]
        print(f"{name} ({r['wall_s']} s wall)")
        for cell in AWA:
            for k in ("gcamp6s", "ca", "gcamp6f_offline"):
                x = a[cell][k]
                ec = x["fit"]["ec50_nM"] if x["fit"] else float("nan")
                print(f"  {cell} {k:16s} peaks {[round(p, 4) for p in x['peaks']]}  EC50 {ec:.3g} nM")
            print(f"  {cell} v before each pulse {[round(u, 1) for u in a[cell]['v_pre_pulse_mV']]}, "
                  f"max during {[round(u, 1) for u in a[cell]['v_max_pulse_mV']]}")
    base = R.get("full_f0")
    if base is None:
        return
    x = base["analysis"]["AWAL"]["gcamp6s"]
    ec = x["fit"]["ec50_nM"] if x["fit"] else float("nan")
    lo, hi = BAR_EC50_NM
    print(f"bar 1: AWAL EC50 {ec:.3g} nM (bar {lo} to {hi}): {'pass' if lo <= ec <= hi else 'FAIL'}")
    pk = x["peaks"]
    amp = (x["fit"]["fmax"] - x["fit"]["fmin"]) if x["fit"] else 0.0
    mono = all(pk[k + 1] >= pk[k] - 0.05 * max(pk) for k in range(1, 5))
    ok2 = amp >= 3 * max(pk[0], 0.0) and amp > 0 and mono
    print(f"bar 2: Fmax - Fmin {amp:.4f} vs 3 x buffer {3 * pk[0]:.4f}; non-decreasing 1 nM..10 uM: {mono}: "
          f"{'pass' if ok2 else 'FAIL'}")
    fs = sorted(float(n.split("_f")[1]) for n in R if n.startswith("full_f"))
    ecs = {f: R[f"full_f{f:g}"]["analysis"]["AWAL"]["gcamp6s"]["fit"] for f in fs}
    print("bar 3 EC50 by block:", {f: (round(e["ec50_nM"], 3) if e else None) for f, e in ecs.items()})
    if len(fs) > 1 and x["fit"]:
        k_ec = int(np.argmin(np.abs(np.log10(np.array(CONC_UM[1:]) * 1e3) - np.log10(ec)))) + 1
        for f in fs[1:]:
            p = R[f"full_f{f:g}"]["analysis"]["AWAL"]["gcamp6s"]["peaks"]
            d_sat = 1 - p[-1] / pk[-1] if pk[-1] else float("nan")
            d_ec = 1 - p[k_ec] / pk[k_ec] if pk[k_ec] else float("nan")
            e = ecs[f]
            print(f"  f {f}: EC50 shift {(e['ec50_nM'] / ec if e else float('nan')):.3g}x; 100 uM peak falls "
                  f"{d_sat:.3f}, the {CONC_UM[k_ec]} uM peak falls {d_ec:.3f} (c: {'pass' if d_sat < d_ec else 'FAIL'})")


if __name__ == "__main__":
    a = sys.argv[1:]
    if a[0] == "score":
        score()
    else:
        t0, build, f = time.time(), a[0], (float(a[1]) if len(a) > 1 else 0.0)
        r = run(build, f)
        res = dict(build=build, f=f, conc_uM=CONC_UM, analysis=analyse(r),
                   t=r["t"][::KEEP], v=r["v"][::KEEP], ca=r["ca"][::KEEP], gc=r["gc"][::KEEP], stim=r["stim"][::KEEP])
        res["wall_s"] = round(time.time() - t0, 1)
        OUT.mkdir(parents=True, exist_ok=True)
        (OUT / f"{build}_f{f:g}.json").write_text(json.dumps(res))
        print("saved", build, f, res["wall_s"], "s")
