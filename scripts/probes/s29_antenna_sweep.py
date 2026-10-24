"""s29 (fly2) B20: the antenna oscillator's velocity response, swept in the model (pre-registered, DECISIONS 23 Oct).

The a3/arista oscillator (extrasenses.Antenna) is built from a profile's registry values and driven by
theta_in = A sin(2 pi f t), with theta_in proportional to air particle velocity (as the JO sound term is). Arista
velocity over air velocity is then proportional to |d theta/dt| / A, which is what laser vibrometry measures
(vvib/vair). The best frequency is the peak of that ratio; Q is f0 over the -3 dB bandwidth. Network step 0.1 ms.

    PYTHONPATH=src python scripts/probes/s29_antenna_sweep.py --profile m10f5s29 --out runs/s29/antenna_m10f5s29.json
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np

from flyemu import profiles
from flyemu.extrasenses import Antenna
from flyemu.registry import Policy, Registry


def response(f0: float, q: float, f: float, dt_ms: float = 0.1, ms: float = 300.0) -> float:
    ant = Antenna(f0, q)
    n = int(round(ms / dt_ms))
    th = np.empty(n)
    for i in range(n):
        th[i] = ant.step(1e-3 * np.sin(2 * np.pi * f * i * dt_ms / 1000.0), dt_ms)[0]
    om = np.gradient(th, dt_ms / 1000.0)
    tail = om[n // 2:]                                   # steady state
    return float((tail.max() - tail.min()) / 2 / 1e-3)   # rad/s per rad of drive


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--profile", default="m10f5s29")
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    r = Registry(Policy.MINIMAL)
    profiles.apply(r, a.profile)
    f0 = float(r.overrides.get("antenna:a3|resonance_hz", 250.0))
    q = float(r.overrides.get("antenna:a3|quality_factor", 1.5))
    fs = np.arange(50.0, 1501.0, 5.0)
    g = np.array([response(f0, q, f) for f in fs])
    k = int(np.argmax(g))
    half = g[k] / np.sqrt(2)
    above = np.flatnonzero(g >= half)
    lo, hi = fs[above[0]], fs[above[-1]]
    res = dict(profile=a.profile, f0_set_hz=f0, q_set=q, best_frequency_hz=float(fs[k]),
               bandwidth_hz=[float(lo), float(hi)], q_from_bandwidth=float(fs[k] / (hi - lo)),
               gain_at_best_over_gain_at_50hz=float(g[k] / g[0]),
               note="velocity response; theta_in proportional to air particle velocity")
    Path(a.out).parent.mkdir(parents=True, exist_ok=True)
    Path(a.out).write_text(json.dumps(res, indent=1))
    print(json.dumps(res, indent=1))


if __name__ == "__main__":
    main()
