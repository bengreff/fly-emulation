"""s19 N26: light-pulse phase-response curve and LD entrainment of the lumped clock (DECISIONS 22 Oct 04:44).

Runs the Organs ODE (the same code m10f uses) in constant darkness, gives one light pulse at a chosen CT, and
reads the steady phase shift after `free_days` (positive = advance, hours). Entrainment: 12:12 LD for
`days`, then the model CT at lights-on.

    .venv/bin/python scripts/probes/s19_n26_prc.py prc --dur-min 10 --lux 1000 --out runs/s19/n26/prc.json
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))
from flyemu.internal_state import Organs, default_params

DT = 20.0  # s, the Organs sub-step


def _wrap_h(x: float) -> float:
    return (x + 12.0) % 24.0 - 12.0


def shift_h(p: dict, ct: float, dur_s: float, lux: float, free_days: float = 4.0) -> float:
    """Phase shift (h, + advance) of a pulse given at `ct` on the limit cycle, read `free_days` later in DD."""
    org = Organs(p=p, z=complex(np.exp(1j * 2 * np.pi * ct / 24.0)))
    n_on = max(1, int(round(dur_s / DT)))
    for _ in range(n_on):
        org.step(DT, light_lux=lux)
    t = n_on * DT
    t_end = t + free_days * 86400.0
    while t < t_end:
        org.step(min(3600.0, t_end - t), light_lux=0.0)
        t = min(t + 3600.0, t_end)
    ref = (ct + t / 3600.0 * 24.0 / p["period_h"]) % 24.0
    return _wrap_h(org.ct_h - ref)


def prc(p: dict, dur_s: float, lux: float, cts=None) -> list[dict]:
    cts = np.arange(0.0, 24.0, 1.0) if cts is None else cts
    return [{"ct": float(c), "shift_h": round(shift_h(p, float(c), dur_s, lux), 4)} for c in cts]


def entrained_ct_at_lights_on(p: dict, lux: float, days: int = 20, ct0: float = 0.0) -> float:
    org = Organs(p=p, z=complex(np.exp(1j * 2 * np.pi * ct0 / 24.0)))
    for _ in range(days):
        for _ in range(12):
            org.step(3600.0, light_lux=lux)
        for _ in range(12):
            org.step(3600.0, light_lux=0.0)
    return float(org.ct_h)


def zero_crossing_ct(p: dict, dur_s: float, lux: float, lo: float = 12.0, hi: float = 24.0) -> float | None:
    """CT of the model PRC's delay-to-advance crossing inside [lo, hi] (bisection on a 0.5 h scan)."""
    cts = np.arange(lo, hi + 1e-9, 0.5)
    y = [shift_h(p, c % 24, dur_s, lux) for c in cts]
    for c0, c1, y0, y1 in zip(cts, cts[1:], y, y[1:]):
        if y0 < 0 <= y1 and abs(y1 - y0) < 6:                  # skip the type-0 jump
            a, b = c0, c1
            for _ in range(20):
                m = 0.5 * (a + b)
                (a, b) = (m, b) if shift_h(p, m % 24, dur_s, lux) < 0 else (a, m)
            return float(0.5 * (a + b) % 24)
    return None


def fit(p: dict, dur_s: float, lux: float, zero_ct: float, delay_ct: float, delay_h: float, iters: int = 4) -> dict:
    """ct_light from the zero crossing, then k_light from the delay at delay_ct; alternate (both move under
    strong pulses). DECISIONS 22 Oct 04:44."""
    p = dict(p)
    p["ct_light_h"] = (zero_ct + 12.0) % 24.0                 # weak-pulse solution as the start
    for _ in range(iters):
        lo, hi = 1e-3, 500.0                                    # log bisection on k: delay grows with k
        for _ in range(40):
            k = np.sqrt(lo * hi); p["k_light_per_h"] = k
            (lo, hi) = (k, hi) if shift_h(p, delay_ct, dur_s, lux) > delay_h else (lo, k)
        p["k_light_per_h"] = float(np.sqrt(lo * hi))
        zc = zero_crossing_ct(p, dur_s, lux)
        if zc is None:
            break
        p["ct_light_h"] = float((p["ct_light_h"] + (zero_ct - zc) + 12.0) % 24.0 - 12.0) % 24.0
    return {"k_light_per_h": p["k_light_per_h"], "ct_light_h": p["ct_light_h"],
            "zero_ct_model": zero_crossing_ct(p, dur_s, lux),
            "delay_model_h": shift_h(p, delay_ct, dur_s, lux)}


def irc_half_lsat(p: dict, ct: float, dur_s: float) -> float:
    """Saturation level L/(L+l50) at which the model's |shift| at `ct` is half its saturated value.
    Shift depends on light only through L/(L+l50), so the half-max intensity is l50 * x / (1 - x)."""
    def sh(x):
        return abs(shift_h(p, ct, dur_s, x / (1 - x) * p["l50_lux"]))
    top = sh(0.999)
    lo, hi = 1e-6, 0.999
    for _ in range(40):
        m = np.sqrt(lo * hi)
        (lo, hi) = (m, hi) if sh(m) < 0.5 * top else (lo, m)
    return float(np.sqrt(lo * hi))


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("mode", choices=["prc", "entrain", "fit", "irc"])
    ap.add_argument("--ct", type=float, default=20.0)
    ap.add_argument("--zero-ct", type=float)
    ap.add_argument("--delay-ct", type=float)
    ap.add_argument("--delay-h", type=float)
    ap.add_argument("--dur-min", type=float, default=10.0)
    ap.add_argument("--lux", type=float, default=1000.0)
    ap.add_argument("--set", nargs="*", default=[], help="param=value overrides (Organs params)")
    ap.add_argument("--cts", type=float, nargs="*")
    ap.add_argument("--out", type=Path)
    a = ap.parse_args()
    p = default_params()
    for kv in a.set:
        k, v = kv.split("=")
        p[k] = float(v)
    if a.mode == "prc":
        res = {"params": {k: p[k] for k in ("k_light_per_h", "l50_lux", "ct_light_h", "mu_per_h", "period_h")},
               "dur_min": a.dur_min, "lux": a.lux, "prc": prc(p, a.dur_min * 60.0, a.lux, a.cts)}
    elif a.mode == "irc":
        x = irc_half_lsat(p, a.ct, a.dur_min * 60.0)
        res = {"ct": a.ct, "dur_min": a.dur_min, "half_lsat": x, "half_lux": x / (1 - x) * p["l50_lux"],
               "params": {k: p[k] for k in ("k_light_per_h", "l50_lux", "ct_light_h")}}
    elif a.mode == "fit":
        res = {"dur_min": a.dur_min, "lux": a.lux, "l50_lux": p["l50_lux"], "target": {
            "zero_ct": a.zero_ct, "delay_ct": a.delay_ct, "delay_h": a.delay_h},
            "fit": fit(p, a.dur_min * 60.0, a.lux, a.zero_ct, a.delay_ct, a.delay_h)}
    else:
        res = {"lux": a.lux, "ct_at_lights_on": entrained_ct_at_lights_on(p, a.lux)}
    txt = json.dumps(res, indent=1)
    if a.out:
        a.out.parent.mkdir(parents=True, exist_ok=True)
        a.out.write_text(txt)
    print(txt)


if __name__ == "__main__":
    main()
