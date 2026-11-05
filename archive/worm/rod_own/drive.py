"""Prescribed muscle drive (no brain): a dorsoventral travelling wave, for the gait tests and as the stand-in
driver until the brain's motor output lands (docs/worm/INTERFACE.md).

Dorsal muscles u = a0 (1 + sin phi)/2, ventral u = a0 (1 - sin phi)/2, phi = 2 pi (f t - s_m / lambda), s_m = the
muscle's centre (fraction of body length), so the wave runs head to tail (forward crawling). a0 ramps in over the
first period. a0 is a stand-in for neural drive amplitude (brain side), fitted per medium in the gait test.
"""
from __future__ import annotations

import numpy as np


class TravellingWave:
    def __init__(self, body, f_hz: float, wavelength_frac: float, a0: float, ramp_periods: float = 1.0,
                 direction: int = +1):
        self.f = f_hz
        self.lam = wavelength_frac
        self.a0 = a0
        self.ramp = ramp_periods / f_hz
        self.dir = direction  # +1 head-to-tail wave (forward), -1 tail-to-head (reversal)
        self.centre = body.mus.centre
        self.dorsal = body.mus.dorsal

    def __call__(self, t: float) -> np.ndarray:
        phi = 2 * np.pi * (self.f * t - self.dir * self.centre / self.lam)
        a = self.a0 * min(1.0, t / self.ramp) if self.ramp > 0 else self.a0
        s = np.sin(phi)
        return np.where(self.dorsal, 0.5 * a * (1 + s), 0.5 * a * (1 - s))
