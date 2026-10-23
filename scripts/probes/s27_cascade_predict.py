"""s27 (fly2): why C1 (KC coincidence e^4) failed test R, and what a rutabaga/dunce cAMP-PKA cascade predicts for R.

Part 1 (C1, s26 harness rule): at rest (KC 0.1 Hz, DAN 6/8/10 Hz, Poisson) every DAN spike sees the KC eligibility
e (+1 per KC spike, tau 1 s). A coincidence is a DAN spike with e >= 1/e (a KC spike within about one tau). C1's
criterion is the pairing's own per-event strength: a resting event crosses it when its e is at least the median e
at the four Hige pairing DAN spikes. Reported: the fraction of resting coincidences that cross it, the share of the
resting depressive drive they carry, and the resting / pairing drive ratio against the R bound.

Part 2 (cascade): cyclase drive per KC = Ca(t)^n x D(t), Ca = KC calcium (+1 per KC spike, tau_ca),
D = dopamine-side activation of the cyclase (+1 per DAN spike, tau_d = the coincidence window). Ca x D is the
multiplicative (maximally supralinear) coincidence; n is the Ca cooperativity (4 Ca2+ sites on calmodulin is the
ceiling). cAMP c = that drive low-passed by tau_c (dunce PDE removal); PKA drive = integral of c^h (h the PKA
cooperativity, expansive regime: saturation only lowers discrimination). All power laws, so the ratio needs no scale
or K. Every choice sits at the discrimination-maximising end, so a fail here is a fail for the sourced cascade.
Test R per KC, as the s26 harness: w = exp(-k x PKA drive); k solved so one Hige pairing leaves the charge-weighted
CS+ ratio (sum q w / sum q, q = odour spikes) at 0.10; pass needs the naive weight W >= 0.5 after 2.3 h of rest
(N22 relaxation, tau 3 h, included), averaged over 24 KCs sharing one DAN train. The ratio of mean drives
(rest / pairing <= ln 2 / ln 10 = 0.301) is also written but is not the test: the mean pairing drive is carried by
4-5 spike KCs, while the charge-weighted target is set by the 2-3 spike KCs.

    .venv/bin/python scripts/probes/s27_cascade_predict.py
"""
from __future__ import annotations

import json
import math
from pathlib import Path

import numpy as np
from scipy.signal import lfilter

REPO = Path(__file__).resolve().parents[2]
TAU_E, R_C1, HOURS = 1.0, 0.223, 2.3            # s26: eligibility tau, C1 rate re-solved to Hige
TAU_MEM = 3 * 3600.0                            # s26: N22 relaxation
HIGE_DAN = np.array([0.2, 0.7, 1.2, 1.7])
KC_REST, KC_ODOUR = 0.1, 2.86                   # Hz at rest (Turner 2008); spikes per CS+ KC in the 1 s odour
BOUND = math.log(2) / math.log(10)


def c1_part(f_dan: float, rng) -> dict:
    T = HOURS * 3600
    tk = np.sort(rng.uniform(0, T, rng.poisson(KC_REST * T)))
    td = np.sort(rng.uniform(0, T, rng.poisson(f_dan * T)))
    # eligibility at each DAN spike: sum over earlier KC spikes (only the last ~10 matter at tau 1 s)
    idx = np.searchsorted(tk, td)
    e = np.zeros(td.size)
    for back in range(1, 12):
        j = idx - back
        ok = j >= 0
        e[ok] += np.exp(-(td[ok] - tk[j[ok]]) / TAU_E)
    # pairing: e at the 4 DAN spikes, many trials
    ep = []
    for _ in range(20000):
        ts = rng.uniform(0, 1.0, rng.poisson(KC_ODOUR))
        ep += [float(np.exp(-(t - ts[ts <= t]) / TAU_E).sum()) for t in HIGE_DAN]
    ep = np.array(ep)
    e_med = float(np.median(ep[ep > 0]))
    drive = lambda x: -np.log(np.clip(1 - R_C1 * x ** 4, 1e-12, 1))
    coinc = e >= math.exp(-1)
    cross = coinc & (e >= e_med)
    e_sat = R_C1 ** -0.25                                        # r e^4 >= 1: one event zeroes the weight
    d_rest = drive(e)
    pair_drive = float(drive(ep).sum() / (ep.size / 4))          # per trial (one pairing), per KC
    return {"f_dan": f_dan, "kc_spikes_rest": int(tk.size), "dan_spikes_rest": int(td.size),
            "coincidences": int(coinc.sum()), "e_median_pairing": e_med,
            "frac_coinc_crossing": float(cross.sum() / coinc.sum()),
            "n_crossing": int(cross.sum()), "e_saturating": e_sat, "n_saturating_rest": int((e >= e_sat).sum()),
            "saturating_per_pairing": float((ep >= e_sat).sum() / (ep.size / 4)), "pairing_events_crossing_per_pairing": float((ep >= e_med).sum() / (ep.size / 4)),
            "share_of_rest_drive_from_crossing": float(d_rest[cross].sum() / d_rest.sum()),
            "rest_drive_2p3h": float(d_rest.sum()), "pairing_drive": pair_drive,
            "ratio_rest_over_pairing": float(d_rest.sum() / pair_drive),
            "suppression_needed": float(d_rest.sum() / pair_drive / BOUND)}


def train(times, T, dt):
    x = np.zeros(int(round(T / dt)) + 1)
    np.add.at(x, np.minimum((times / dt).astype(int), x.size - 1), 1.0)
    return x


def trace(x, tau, dt):
    a = math.exp(-dt / tau)
    return lfilter([1.0], [1.0, -a], x)


def solve_k(P, q, target=0.10):
    """Depression rate k (w = exp(-k drive)) giving the Hige CS+ charge ratio sum q w / sum q = target."""
    lo, hi = 1e-30, 1e30
    for _ in range(200):
        mid = math.sqrt(lo * hi)
        lo, hi = (mid, hi) if (q * np.exp(-mid * P)).sum() / q.sum() > target else (lo, mid)
    return math.sqrt(lo * hi)


def cascade_set(f_dan, tau_ca, tau_d, rng, ns=(1, 2, 4), tau_cs=(1.0, 10.0, 60.0), hs=(1, 2), trials=200,
                n_rest=24, dt=0.005) -> list[dict]:
    """Rest and pairing drives for one (tau_ca, tau_d), every (n, tau_c, h). Test R per KC: k solved so one Hige
    pairing leaves the charge-weighted CS+ ratio at 0.10 (s26 harness target), then W = mean naive weight after
    2.3 h of rest over n_rest KCs (one shared DAN train), without and with N22 relaxation (tau 3 h)."""
    T = HOURS * 3600
    td = rng.uniform(0, T, rng.poisson(f_dan * T))
    d = trace(train(td, T, dt), tau_d, dt)
    rest = {(n, tc, h): [] for n in ns for tc in tau_cs for h in hs}
    for _ in range(n_rest):
        ca = trace(train(rng.uniform(0, T, rng.poisson(KC_REST * T)), T, dt), tau_ca, dt)
        for n in ns:
            g = ca ** n * d
            for tc in tau_cs:
                c = trace(g, tc, dt)
                for h in hs:
                    rest[(n, tc, h)].append(float((c ** h).sum() * dt))
    # pairing excess with common random numbers: the same background with and without the odour KC burst and the
    # 4 Hige DAN pulses, paired at 180 s (3 x the slowest tau) and scored to 300 s after
    t0, Tp = 180.0, 480.0
    exc = {k: [] for k in rest}
    qs = []
    for _ in range(trials):
        bk = rng.uniform(0, Tp, rng.poisson(KC_REST * Tp))
        bd = rng.uniform(0, Tp, rng.poisson(f_dan * Tp))
        qs.append(rng.poisson(KC_ODOUR))
        pk = np.r_[bk, t0 + rng.uniform(0, 1.0, qs[-1])]
        pd = np.r_[bd, t0 + HIGE_DAN]
        arms = [(trace(train(x, Tp, dt), tau_ca, dt), trace(train(y, Tp, dt), tau_d, dt))
                for x, y in ((pk, pd), (bk, bd))]
        for n in ns:
            g = [a ** n * b for a, b in arms]
            for tc in tau_cs:
                c = [trace(x, tc, dt) for x in g]
                for h in hs:
                    exc[(n, tc, h)].append(float((c[0] ** h - c[1] ** h).sum() * dt))
    out, q = [], np.array(qs, float)
    for (n, tc, h), rl in rest.items():
        x, R = np.array(exc[(n, tc, h)]), np.array(rl)
        k = solve_k(np.maximum(x, 0.0), q)
        lam = k * R / T + 1.0 / TAU_MEM                          # N22: dw/dt = -k p w + (1 - w) / TAU_MEM
        w_n22 = (1.0 / TAU_MEM) / lam * (1.0 - np.exp(-lam * T)) + np.exp(-lam * T)
        w1 = float(np.mean([math.exp(-k * x[q == 1].mean())])) if (q == 1).any() else None

        def w_at(s):                                             # W with N22 if every resting drive were cut s-fold
            la = k * R / s / T + 1.0 / TAU_MEM
            return float(((1.0 / TAU_MEM) / la * (1.0 - np.exp(-la * T)) + np.exp(-la * T)).mean())
        lo, hi = 1.0, 1e12
        for _ in range(100):
            mid = math.sqrt(lo * hi)
            lo, hi = (lo, mid) if w_at(mid) >= 0.5 else (mid, hi)
        out.append({"f_dan": f_dan, "tau_ca": tau_ca, "tau_d": tau_d, "n": n, "tau_c": tc, "h": h,
                    "rest_drive_2p3h_mean": float(R.mean()), "pairing_excess_mean": float(x.mean()),
                    "ratio_rest_over_pairing_mean": float(R.mean() / x.mean()), "k": k,
                    "w_cs_plus_1spike_kc": w1, "w_cs_plus_by_count": {int(c): float(np.exp(-k * x[q == c]).mean())
                                                                      for c in range(0, 6) if (q == c).any()},
                    "W_2p3h": float(np.exp(-k * R).mean()), "W_2p3h_n22": float(w_n22.mean()),
                    "pass_R": bool(w_n22.mean() >= 0.5), "rest_suppression_to_pass": hi})
    return out


def main() -> None:
    rng = np.random.default_rng(27)
    out = {"bound": BOUND, "c1": [c1_part(f, rng) for f in (6.0, 8.0, 10.0)], "cascade": []}
    for tau_ca in (0.1, 0.5, 1.0):               # KC bouton Ca decay, s (range bracket, inferred)
        for tau_d in (0.5, 15.0):                # lif.py DA trace; Tomchik 2009 forward window (DA 15 s ahead still synergistic)
            out["cascade"] += cascade_set(8.0, tau_ca, tau_d, rng)
    p = REPO / "runs" / "s27" / "cascade_predict.json"
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(out, indent=1))
    for c in out["c1"]:
        print("C1", {k: (round(v, 4) if isinstance(v, float) else v) for k, v in c.items()})
    for c in out["cascade"]:
        print("CAS", {k: (round(v, 4) if isinstance(v, float) else v) for k, v in c.items()})


if __name__ == "__main__":
    main()
