"""fly2 s26 test R: does a KC->MBON memory last hours at measured resting rates? (DECISIONS 22 Oct 22:28)

Event-driven, one compartment. The N21/N22 update order is copied from lif.py: per DAN spike, restore toward w0
(s25 rule), then w *= clip(1 - r e^n, 0, 1) with the KC eligibility e (+1 per KC spike, tau 1 s); N22 relaxes w
to w0 with tau 3 h between events. Candidate forms C1 (e^n) and C2 (dopamine trace d^m) re-solve their rate so the
Hige pairing still gives a CS+ ratio of 0.10; nothing is fitted to R.

    .venv/bin/python scripts/probes/s26_retention.py --out runs/s26/retention.json
"""
from __future__ import annotations

import argparse
import json
import math
from pathlib import Path

import numpy as np

TAU_E, TAU_D, TAU_MEM = 1.0, 0.5, 3 * 3600.0          # s: KC eligibility, dopamine trace (lif.py), N22
HIGE_DAN = np.array([0.2, 0.7, 1.2, 1.7])             # s from odour onset (kc_mbon_pairing.py default)
N_KC, FRAC = 1000, 0.06


def pairing_ratio(r, n=1, m=0, kc_spikes=2.86, trials=2000, seed=0):
    """Hige pairing in the harness: CS+ charge ratio (sum q w / sum q, q = KC spikes in the odour, as in
    kc_mbon_pairing.py) after one 1 s odour with 4 DAN spike-steps at 2 Hz. 2.86 spikes per CS+ KC is the
    network's mean (runs/s24/kc/fit_s12.json)."""
    rng = np.random.default_rng(seed)
    out, qs = [], []
    for _ in range(trials):
        k = rng.poisson(kc_spikes)
        ts = np.sort(rng.uniform(0, 1.0, k))
        w, d, t_prev = 1.0, 0.0, None
        for t in HIGE_DAN:
            d = d * (math.exp(-(t - t_prev) / TAU_D) if t_prev is not None else 0.0) + 1.0
            t_prev = t
            e = float(np.exp(-(t - ts[ts <= t]) / TAU_E).sum())
            w *= min(max(1.0 - r * e ** n * d ** m, 0.0), 1.0)
        out.append(w)
        qs.append(k)
    q = np.array(qs, float)
    return float((q * np.array(out)).sum() / q.sum())


def solve_rate(n, m, target=0.10):
    lo, hi = 1e-6, 50.0
    for _ in range(60):
        mid = math.sqrt(lo * hi)
        lo, hi = (mid, hi) if pairing_ratio(mid, n, m) > target else (lo, mid)
    return math.sqrt(lo * hi)


def kc_rates(rng, hetero):
    if not hetero:
        return np.full(N_KC, 0.1)
    f = rng.exponential(0.125, N_KC)
    f[rng.random(N_KC) < 0.2] = 0.0
    return f


def retention(r_ltd, r_res, f_dan, n=1, m=0, hetero=False, hours=3.0, seed=1, checkpoints=(1.0, 2.3, 3.0),
              n22=True):
    rng = np.random.default_rng(seed)
    T = hours * 3600.0
    idx = rng.permutation(N_KC)
    k = int(FRAC * N_KC)
    csp, csm = idx[:k], idx[k:2 * k]
    naive = np.setdiff1d(np.arange(N_KC), csp)
    w0 = np.ones(N_KC)
    w = w0.copy()
    w[csp] = 0.10
    m0 = 1 - w[csp].mean() / w[csm].mean()
    t_dan = np.cumsum(rng.exponential(1.0 / f_dan, int(f_dan * T * 1.2) + 100))
    t_dan = t_dan[t_dan < T]
    f_kc = kc_rates(rng, hetero)
    # KC spikes: (time, cell); contribution to e at the next DAN spike folded in per interval
    counts = rng.poisson(f_kc * T)
    cell = np.repeat(np.arange(N_KC), counts)
    tk = rng.uniform(0, T, cell.size)
    o = np.argsort(tk)
    tk, cell = tk[o], cell[o]
    seg = np.searchsorted(t_dan, tk, side="left")          # KC spike lands before DAN spike seg
    keep = seg < t_dan.size
    tk, cell, seg = tk[keep], cell[keep], seg[keep]
    contrib = np.exp(-(t_dan[seg] - tk) / TAU_E)
    bounds = np.searchsorted(seg, np.arange(t_dan.size + 1), side="left")
    e = np.zeros(N_KC)
    d, t_prev = 0.0, 0.0
    marks = [h * 3600.0 for h in checkpoints]
    rows, mi = [], 0
    for j, t in enumerate(t_dan):
        while mi < len(marks) and t >= marks[mi]:
            rows.append(_row(checkpoints[mi], w, w0, csp, csm, naive))
            mi += 1
        dt = t - t_prev
        e *= math.exp(-dt / TAU_E)
        d = d * math.exp(-dt / TAU_D) + 1.0
        if n22:
            w += (w0 - w) * (1.0 - math.exp(-dt / TAU_MEM))
        a, b = bounds[j], bounds[j + 1]
        if b > a:
            np.add.at(e, cell[a:b], contrib[a:b])
        if r_res > 0:
            w += r_res * (w0 - w)
        if r_ltd > 0:
            w *= np.clip(1.0 - r_ltd * e ** n * d ** m, 0.0, 1.0)
        t_prev = t
    while mi < len(marks):
        rows.append(_row(checkpoints[mi], w, w0, csp, csm, naive))
        mi += 1
    return float(m0), rows


def _row(h, w, w0, csp, csm, naive):
    return {"h": h, "M": float(1 - w[csp].mean() / max(w[csm].mean(), 1e-12)),
            "W": float((w[naive] / w0[naive]).mean())}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default="runs/s26/retention.json")
    ap.add_argument("--hours", type=float, default=3.0)
    a = ap.parse_args()
    res = {"harness_check": {}, "rules": {}}
    hc = pairing_ratio(0.430)
    res["harness_check"] = {"r": 0.430, "cs_plus_ratio": hc, "band": [0.06, 0.14],
                            "pass": 0.06 <= hc <= 0.14}
    print(f"harness check: Hige pairing at r 0.430 -> CS+ {hc:.3f} (band 0.06-0.14)", flush=True)
    r_c1 = solve_rate(4, 0)
    r_c2 = solve_rate(1, 2)
    r_c3 = 1.0 - math.exp(-1.0 / (8.0 * TAU_MEM))     # 8 Hz rest -> memory tau 3 h from restoration alone
    hattori_c3 = 1.0 - (1.0 - r_c3) ** 200            # 10 stimulations x 20 spike-steps (s25 S)
    rules = {"R0": dict(r_ltd=0.430, r_res=0.0), "R1": dict(r_ltd=0.430, r_res=0.00289),
             "C1": dict(r_ltd=r_c1, r_res=0.0, n=4), "C2": dict(r_ltd=r_c2, r_res=0.0, m=2),
             "C3": dict(r_ltd=0.0, r_res=r_c3, n22=False), "C3_with_N22": dict(r_ltd=0.0, r_res=r_c3)}
    res["solved"] = {"C1_rate": r_c1, "C1_pairing": pairing_ratio(r_c1, 4, 0),
                     "C2_rate": r_c2, "C2_pairing": pairing_ratio(r_c2, 1, 2),
                     "C3_rate": r_c3, "C3_hattori_n10_pred": hattori_c3, "hattori_n10_measured": [0.40, 0.06]}
    print("solved:", json.dumps(res["solved"]), flush=True)
    e_m = 1.0 / math.e
    for name, kw in rules.items():
        res["rules"][name] = {}
        for hetero in (False, True):
            for f in (6.0, 8.0, 10.0):
                m0, rows = retention(f_dan=f, hetero=hetero, hours=a.hours, **kw)
                r23 = [r for r in rows if r["h"] == 2.3][0]
                ok = r23["M"] >= m0 * e_m and r23["W"] >= 0.5
                key = f"{'hetero' if hetero else 'uniform'}_{f:g}Hz"
                res["rules"][name][key] = {"M0": m0, "rows": rows, "pass": bool(ok)}
                print(f"{name} {key}: " + ", ".join(f"{r['h']}h M {r['M']:.3f} W {r['W']:.3f}" for r in rows)
                      + f" -> {'PASS' if ok else 'FAIL'}", flush=True)
        res["rules"][name]["pass_all"] = all(v["pass"] for v in res["rules"][name].values() if isinstance(v, dict))
    # R0 validity bound: largest resting DAN rate with W(2.3 h) >= 0.5 and M(2.3 h) >= M0/e (uniform KCs)
    lo, hi = 1e-5, 6.0
    for _ in range(25):
        mid = math.sqrt(lo * hi)
        m0, rows = retention(0.430, 0.0, mid, hours=2.3, checkpoints=(2.3,))
        ok = rows[0]["M"] >= m0 * e_m and rows[0]["W"] >= 0.5
        lo, hi = (mid, hi) if ok else (lo, mid)
    res["R0_max_resting_dan_hz"] = lo
    print(f"R0 passes R only below a resting DAN rate of {lo:.4f} Hz", flush=True)
    Path(a.out).parent.mkdir(parents=True, exist_ok=True)
    Path(a.out).write_text(json.dumps(res, indent=1))


if __name__ == "__main__":
    main()
