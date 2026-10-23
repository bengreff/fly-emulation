"""s20 N26 CRY-TIM light input (state:clock|light_input = 1): pulse assays shared by the smoke check and the fit.

Shifts are pulsed minus unpulsed twin (h, + advance), read `free_days` after the pulse in DD. Every run starts
`pre_days` of DD before the pulse so c and T settle on the limit cycle.
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))
sys.path.insert(0, str(Path(__file__).resolve().parent))
from flyemu.internal_state import Organs, default_params, tim_dd  # noqa: E402

DT = 20.0


def wrap(x: float) -> float:
    return (x + 12.0) % 24.0 - 12.0


def tim_params(**kw) -> dict:
    p = default_params()
    p["light_input"] = 1.0
    p.update(kw)
    return p


def _dark(o: Organs, s: float) -> None:
    o.step(s, light_lux=0.0)


def dd_shift(p: dict, ct: float, dur_s: float, lux: float, pre_days: float = 2.0, free_days: float = 4.0) -> float:
    ct0 = (ct - pre_days * 24.0 * 24.0 / p["period_h"]) % 24.0
    out = []
    for pulse in (True, False):
        o = Organs(p=p, z=complex(np.exp(1j * 2 * np.pi * ct0 / 24.0)), cry=0.0, tim=tim_dd(ct0, p.get("tim_dd")))
        for _ in range(int(pre_days * 24)):
            _dark(o, 3600.0)
        for _ in range(max(1, int(round(dur_s / DT)))):
            o.step(DT, light_lux=lux if pulse else 0.0)
        for _ in range(int(free_days * 24)):
            _dark(o, 3600.0)
        out.append(o.ct_h)
    return wrap(out[0] - out[1])


def ld_shift(p: dict, zt: float, dur_s: float, lux: float, ld_lux: float = 1000.0, days: int = 10,
             free_days: int = 4) -> float:
    """12:12 LD for `days`, then the pulse at ZT in the following night, then DD (Lamba-type assay)."""
    out = []
    for pulse in (True, False):
        o = Organs(p=p)
        for _ in range(days):
            for _ in range(12):
                o.step(3600.0, light_lux=ld_lux)
            for _ in range(12):
                _dark(o, 3600.0)
        for _ in range(12):
            o.step(3600.0, light_lux=ld_lux)
        pre = (zt - 12.0) * 3600.0
        o.step(pre, light_lux=0.0) if pre > 0 else None
        for _ in range(max(1, int(round(dur_s / DT)))):
            o.step(DT, light_lux=lux if pulse else 0.0)
        for _ in range(free_days * 24):
            _dark(o, 3600.0)
        out.append(o.ct_h)
    return wrap(out[0] - out[1])


def lights_on_ct(p: dict, lux: float = 1000.0, days: int = 20, ct0: float = 0.0) -> float:
    o = Organs(p=p, z=complex(np.exp(1j * 2 * np.pi * ct0 / 24.0)), cry=0.0, tim=tim_dd(ct0, p.get("tim_dd")))
    for _ in range(days):
        for _ in range(12):
            o.step(3600.0, light_lux=lux)
        for _ in range(12):
            _dark(o, 3600.0)
    return float(o.ct_h)


def zero_crossing(p: dict, dur_s: float = 3600.0, lux: float = 1000.0, lo: float = 12.0, hi: float = 24.0):
    cts = np.arange(lo, hi + 1e-9, 0.5)
    y = [dd_shift(p, c % 24, dur_s, lux) for c in cts]
    for c0, c1, y0, y1 in zip(cts, cts[1:], y, y[1:]):
        if y0 < 0 <= y1 and abs(y1 - y0) < 6:
            a, b = c0, c1
            for _ in range(12):
                m = 0.5 * (a + b)
                (a, b) = (m, b) if dd_shift(p, m % 24, dur_s, lux) < 0 else (a, m)
            return float(0.5 * (a + b) % 24)
    return None


def irc_half_lux(p: dict, ct: float, dur_s: float, lux_sat: float = 1000.0) -> float:
    """Lux at which the shift at `ct` reaches half its value at `lux_sat` (log bisection)."""
    full = abs(dd_shift(p, ct, dur_s, lux_sat))
    lo, hi = 1e-6, lux_sat
    for _ in range(30):
        m = np.sqrt(lo * hi)
        (lo, hi) = (m, hi) if abs(dd_shift(p, ct, dur_s, m)) < 0.5 * full else (lo, m)
    return float(np.sqrt(lo * hi))


if __name__ == "__main__":      # smoke: mechanism behaviour at the guessed defaults (no fit, no score)
    p = tim_params(ct_tim_h=6.5)
    print("lights-on CT (LD 1000 lux):", round(lights_on_ct(p), 2))
    for ct in (3, 9, 15, 21):
        print(f"CT{ct:2d}: " + "  ".join(f"{m:>3d} min {dd_shift(p, ct, m * 60.0, 1000.0):+.2f}" for m in (1, 5, 15, 60)))
