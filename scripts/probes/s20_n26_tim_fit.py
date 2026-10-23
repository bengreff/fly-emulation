"""s20 N26 CRY-TIM refit (state:clock|light_input = 1; registration in DECISIONS, s20 N26 CRY-TIM refit).

Fitted: k_tim and ct_tim_h. Set by rule at every evaluation (alternated to a joint fixed point):
- cry_rate_per_lux_h: the model's 10 min IRC half-max at CT20 is Vinayak 2013's 600 nW/cm2 blue = 0.372 lux
  (inferred at 470 nm);
- tim_kdeg_per_h: a 10 min 1000 lux pulse at CT15 leaves `--tang-frac` (0.10) of unpulsed TIM 1 h after the
  pulse ends (Tang et al. 2010: DN/LNd TIM 'undetectable' after a saturating 10 min ZT15 pulse; 10% inferred).
Fixed from the reads: TIM_DD (Shafer 2002 Fig. 6D), tim_tau_rec_h (its derived bound); cry_tau_h guessed
(internal_state defaults or --set overrides).
Targets: DD PRC zero crossing CT 18.5 (60 min, 1000 lux), DD CT15 delay -4.05 h (same pulse), LD ZT15 delay
-3.1 h (5 min, 1500 lux), lights-on in 12:12 LD (1000 lux) at CT 0.

The assays are those of s20_n26_tim.py (pulsed minus unpulsed twin), sped up by sharing the pre-pulse run:
one DD run or one LD entrainment, copied at the pulse time. Both twins then run `settle_h` past the pulse, by
which time CRY has decayed and the Stuart-Landau angle turns at 2 pi / period in both (the amplitude term is
radial), so later days add nothing to the shift. `--check` compares these with the s20_n26_tim.py reference.

    .venv/bin/python scripts/probes/s20_n26_tim_fit.py --out runs/s20/n26/tim_fit.json
"""
from __future__ import annotations

import argparse
import copy
import json
import sys
import time
from pathlib import Path

import numpy as np
from scipy.optimize import minimize

sys.path.insert(0, str(Path(__file__).resolve().parent))
from s20_n26_tim import DT, Organs, dd_shift, ld_shift, lights_on_ct, tim_params, wrap  # noqa: E402
from flyemu.internal_state import TIM_DD, tim_dd  # noqa: E402

VINAYAK_LUX = 0.6 * 0.62          # 600 nW/cm2 blue at CT20, 10 min; 1 uW/cm2 = 0.62 lux at 470 nm (inferred)
VINAYAK_120_LUX = 0.004 * 0.62    # 4 nW/cm2, 120 min: consistency only
TARGETS = {"zc": 18.5, "dd15": -4.05, "ld15": -3.1, "on": 0.0}
BANDS = {"zc": 1.0, "dd15": 1.5, "ld15": 1.5, "on": 2.0}   # +-h for zc and on; x/÷ for the delays


def _pulse_pair(o0: Organs, dur_s: float, lux: float, settle_h: float) -> float:
    out = []
    for lx in (lux, 0.0):
        o = copy.copy(o0)
        for _ in range(max(1, int(round(dur_s / DT)))):
            o.step(DT, light_lux=lx)
        o.step(settle_h * 3600.0, light_lux=0.0)
        out.append(o.ct_h)
    return wrap(out[0] - out[1])


class DD:
    """One dark run from CT `start` after `pre_days` (as dd_shift), copied at any later CT."""

    def __init__(self, p: dict, start: float = 11.0, pre_days: float = 2.0, settle_h: float = 12.0):
        ct0 = (start - pre_days * 24.0 * 24.0 / p["period_h"]) % 24.0
        o = Organs(p=p, z=complex(np.exp(1j * 2 * np.pi * ct0 / 24.0)), cry=0.0, tim=tim_dd(ct0, p.get("tim_dd")))
        o.step(pre_days * 24 * 3600.0, light_lux=0.0)
        self.p, self.base, self.start, self.settle_h, self.memo = p, o, start, settle_h, {}

    def at(self, ct: float) -> Organs:
        o = copy.copy(self.base)
        lag = (ct - self.start) % 24.0 * self.p["period_h"] / 24.0
        if lag > 0:
            o.step(lag * 3600.0, light_lux=0.0)
        return o

    def shift(self, ct: float, dur_s: float, lux: float) -> float:
        key = (round(ct, 6), dur_s, lux)
        if key not in self.memo:
            self.memo[key] = _pulse_pair(self.at(ct), dur_s, lux, self.settle_h)
        return self.memo[key]

    def zero_crossing(self, dur_s: float = 3600.0, lux: float = 1000.0, lo: float = 12.0, hi: float = 24.0):
        cts = np.arange(lo, hi + 1e-9, 1.0)
        y = [self.shift(c, dur_s, lux) for c in cts]
        for c0, c1, y0, y1 in zip(cts, cts[1:], y, y[1:]):
            if y0 < 0 <= y1 and abs(y1 - y0) < 6:
                a, b = c0, c1
                for _ in range(7):
                    m = 0.5 * (a + b)
                    (a, b) = (m, b) if self.shift(m, dur_s, lux) < 0 else (a, m)
                return float(0.5 * (a + b) % 24), y
        return None, y

    def half_lux(self, ct: float, dur_s: float, lux_sat: float = 1000.0) -> float:
        full = abs(self.shift(ct, dur_s, lux_sat))
        lo, hi = 1e-7, lux_sat
        for _ in range(26):
            m = np.sqrt(lo * hi)
            (lo, hi) = (m, hi) if abs(self.shift(ct, dur_s, m)) < 0.5 * full else (lo, m)
        return float(np.sqrt(lo * hi))


class LD:
    """12:12 LD entrainment from CT 0 at the first lights-on, copied at the last lights-off (as ld_shift)."""

    def __init__(self, p: dict, ld_lux: float = 1000.0, days: int = 20, settle_h: float = 12.0):
        o = Organs(p=p)
        self.on = []
        for _ in range(days):
            self.on.append(o.ct_h)
            o.step(12 * 3600.0, light_lux=ld_lux)
            o.step(12 * 3600.0, light_lux=0.0)
        self.on.append(o.ct_h)
        o.step(12 * 3600.0, light_lux=ld_lux)
        self.base, self.settle_h = o, settle_h

    def shift(self, zt: float, dur_s: float, lux: float) -> float:
        o = copy.copy(self.base)
        if zt > 12:
            o.step((zt - 12.0) * 3600.0, light_lux=0.0)
        return _pulse_pair(o, dur_s, lux, self.settle_h)


def settle(p: dict) -> float:
    return max(8.0, 10.0 * p["cry_tau_h"] + 2.0)


def tim_left(p: dict, ct: float = 15.0, dur_s: float = 600.0, lux: float = 1000.0, after_h: float = 1.0,
             o0: Organs | None = None) -> float:
    """TIM pulsed / unpulsed, `after_h` after a pulse ending in DD (Tang 2010's fixation). The dark pre-run
    `o0` doesn't depend on the light values, so set_kdeg passes one in."""
    o0 = DD(p, start=ct).at(ct) if o0 is None else o0
    out = []
    for lx in (lux, 0.0):
        o = copy.copy(o0)
        o.p = p
        for _ in range(max(1, int(round(dur_s / DT)))):
            o.step(DT, light_lux=lx)
        o.step(after_h * 3600.0, light_lux=0.0)
        out.append(o.tim)
    return out[0] / out[1]


def set_kdeg(p: dict, frac: float) -> dict:
    lo, hi = np.log(0.1), np.log(50.0)
    o0 = DD(p, start=15.0).at(15.0)
    for _ in range(24):
        m = 0.5 * (lo + hi)
        (lo, hi) = (m, hi) if tim_left(dict(p, tim_kdeg_per_h=float(np.exp(m))), o0=o0) > frac else (lo, m)
    return dict(p, tim_kdeg_per_h=float(np.exp(0.5 * (lo + hi))))


def set_rules(p: dict, frac: float, iters: int = 8) -> tuple[dict, float, float]:
    """Joint fixed point of the two rules. cry_rate: only a*L enters c, so a *= half / target."""
    p = dict(p)
    half = np.nan
    for _ in range(iters):
        k0 = p["tim_kdeg_per_h"]
        p = set_kdeg(p, frac)
        half = DD(p, start=19.0, settle_h=settle(p)).half_lux(20.0, 600.0)
        ok = abs(np.log(half / VINAYAK_LUX)) < 0.005 and abs(np.log(p["tim_kdeg_per_h"] / k0)) < 0.005
        if ok:
            break
        p["cry_rate_per_lux_h"] *= half / VINAYAK_LUX
    return p, half, tim_left(p)


def evaluate(p: dict, frac: float = 0.10, full: bool = False) -> dict:
    p, half10, left = set_rules(p, frac)
    sh = settle(p)
    dd = DD(p, settle_h=sh)
    zc, prc = dd.zero_crossing()
    ld = LD(p, settle_h=sh)
    r = {"cry_rate_per_lux_h": p["cry_rate_per_lux_h"], "tim_kdeg_per_h": p["tim_kdeg_per_h"],
         "half10_lux": half10, "tim_left_tang": left, "zc": zc,
         "dd15": dd.shift(15.0, 3600.0, 1000.0), "ld15": ld.shift(15.0, 300.0, 1500.0), "on": wrap(ld.on[-1]),
         "on_drift_h": abs(wrap(ld.on[-1] - ld.on[-2])), "prc60_ct12_24": prc}
    res = {"zc": (zc - TARGETS["zc"]) / BANDS["zc"] if zc is not None else 10.0,
           "on": r["on"] / BANDS["on"]}
    for k in ("dd15", "ld15"):
        res[k] = np.log(r[k] / TARGETS[k]) / np.log(BANDS[k]) if r[k] * TARGETS[k] > 0 else 10.0
    r["resid"] = res
    r["loss"] = float(sum(v * v for v in res.values()))
    r["pass"] = {k: bool(abs(v) <= 1.0) for k, v in res.items()}
    if full:
        r["half120_lux"] = DD(p, start=19.0, settle_h=sh).half_lux(20.0, 7200.0)
        r["tim_left_vinayak_ct20"] = tim_left(p, ct=20.0, lux=VINAYAK_LUX, after_h=0.0)
        dd5 = DD(p, start=0.0, settle_h=sh)
        r["prc60_full"] = {int(c): dd5.shift(float(c), 3600.0, 1000.0) for c in range(0, 24)}
        r["prc5_full"] = {int(c): dd5.shift(float(c), 300.0, 1500.0) for c in range(0, 24)}
        r["dd15_by_min"] = {m: dd.shift(15.0, m * 60.0, 1000.0) for m in (1, 5, 15, 30, 60, 120)}
    return r


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default="runs/s20/n26/tim_fit.json")
    ap.add_argument("--set", nargs="*", default=[], help="name=value overrides of the fixed values")
    ap.add_argument("--check", action="store_true", help="fast assays against the s20_n26_tim.py reference")
    ap.add_argument("--tang-frac", type=float, default=0.10)
    ap.add_argument("--drop-ct", type=float, default=None, help="variant: TIM_DD without the point at this CT")
    a = ap.parse_args()
    base = tim_params(**{k: float(v) for k, v in (s.split("=") for s in a.set)})
    if a.drop_ct is not None:
        base["tim_dd"] = tuple(pt for pt in TIM_DD if pt[0] != a.drop_ct)
    if a.check:
        q = dict(base, ct_tim_h=6.5)
        dd, ld = DD(q, start=0.0), LD(q)
        rows = [("dd ct15 60m", dd.shift(15, 3600, 1000), dd_shift(q, 15, 3600, 1000)),
                ("dd ct21 10m", dd.shift(21, 600, 1000), dd_shift(q, 21, 600, 1000)),
                ("dd ct3 60m", dd.shift(3, 3600, 1000), dd_shift(q, 3, 3600, 1000)),
                ("ld zt15 5m", ld.shift(15, 300, 1500), ld_shift(q, 15, 300, 1500, days=20)),
                ("lights-on", wrap(ld.on[-1]), wrap(lights_on_ct(q, days=20)))]
        for n, f, r in rows:
            print(f"{n:12s} fast {f:+.4f}  reference {r:+.4f}  diff {f - r:+.4f}")
        return
    t0, log = time.time(), []

    def loss(x):
        p = dict(base, k_tim=float(np.exp(x[0])), ct_tim_h=float(x[1] % 24.0))
        r = evaluate(p, a.tang_frac)
        log.append({"k_tim": p["k_tim"], "ct_tim_h": p["ct_tim_h"], **{k: r[k] for k in
                    ("loss", "zc", "dd15", "ld15", "on", "cry_rate_per_lux_h", "tim_kdeg_per_h")}})
        print(json.dumps(log[-1]), f"{time.time() - t0:.0f}s", flush=True)
        return r["loss"]

    grid = [(lk, ct) for lk in np.log([0.3, 1.0, 3.0, 10.0, 30.0]) for ct in np.arange(0.0, 24.0, 2.0)]
    gl = [loss(np.array(g)) for g in grid]
    order = np.argsort(gl)
    best = None
    for i in order[:2]:                           # two starts: the best two grid cells
        m = minimize(loss, np.array(grid[i]), method="Nelder-Mead",
                     options={"xatol": 0.01, "fatol": 1e-3, "maxfev": 60, "initial_simplex":
                              np.array(grid[i]) + np.array([[0, 0], [0.5, 0], [0, 1.5]])})
        if best is None or m.fun < best.fun:
            best = m
    p = dict(base, k_tim=float(np.exp(best.x[0])), ct_tim_h=float(best.x[1] % 24.0))
    r = evaluate(p, a.tang_frac, full=True)
    out = {"args": vars(a), "fixed": {k: base[k] for k in ("cry_tau_h", "tim_tau_rec_h", "period_h", "mu_per_h")},
           "tim_dd": base.get("tim_dd", TIM_DD), "fitted": {"k_tim": p["k_tim"], "ct_tim_h": p["ct_tim_h"]},
           "targets": TARGETS, "bands": BANDS, "result": r, "all_pass": all(r["pass"].values()),
           "grid_best": [log[i] for i in order[:5]], "log": log, "seconds": time.time() - t0}
    Path(a.out).parent.mkdir(parents=True, exist_ok=True)
    Path(a.out).write_text(json.dumps(out, indent=1, default=float))
    print("WROTE", a.out, "all_pass", out["all_pass"])


if __name__ == "__main__":
    main()
