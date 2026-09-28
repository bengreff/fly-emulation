"""The fly's surroundings: the physical quantities its senses read.

Everything here is a scenario choice (**inferred**), not biology: where odour
sources are, what the air temperature and humidity are. A sense organ may only
read the world through the fields defined here, evaluated at the organ's own
position on the body, so no unobserved world state reaches the network except
through a receptor.

Units: position mm (MuJoCo world frame), odour concentration as a fraction of
saturated vapour-phase dilution (DoOR / Hallem-Carlson use 10^-2 dilutions),
temperature degC, relative humidity 0-1, CO2 volume fraction.
"""
from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np


@dataclass
class OdourSource:
    odour: str                 # DoOR odour identifier (InChIKey)
    position: np.ndarray       # mm
    peak: float                # dilution fraction at the source centre
    sigma_mm: float = 20.0     # width of a static Gaussian plume


@dataclass
class World:
    odours: list[OdourSource] = field(default_factory=list)
    temperature_c: float = 25.0
    humidity_rh: float = 0.5
    co2_fraction: float = 0.0004     # ambient air
    wind_mm_s: np.ndarray = field(default_factory=lambda: np.zeros(3))
    food: list = field(default_factory=list)   # extrasenses.FoodPatch
    # s10 B20: near-field sound as air particle velocity (mm/s amplitude, Hz), along
    # a world direction; read only by the antenna oscillator (extrasenses.py)
    sound_mm_s: float = 0.0
    sound_hz: float = 0.0
    sound_dir: np.ndarray = field(default_factory=lambda: np.array([1.0, 0.0, 0.0]))

    def odour_concentrations(self, pos: np.ndarray) -> dict[str, np.ndarray]:
        """Concentration of each odour at positions (n, 3); static plumes."""
        out: dict[str, np.ndarray] = {}
        for s in self.odours:
            d2 = ((pos - s.position) ** 2).sum(-1)
            out[s.odour] = out.get(s.odour, 0) + s.peak * np.exp(-d2 / (2 * s.sigma_mm ** 2))
        return out
