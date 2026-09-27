"""B7 tarsal adhesion released by load and shear (session 9).

Legacy: grip per leg = the long-tendon MN pool's drive (neural switch only).
With the gate, a leg's grip also needs its tarsi to be on a surface (summed
normal load above `contact_min`) and is released when the tangential load
exceeds `peel_ratio` x normal load (pads detach by peeling under shear).
Thresholds are guessed within bounds (parameters.csv b7_*).
"""
from __future__ import annotations

import numpy as np

CONTACT_MIN_UN = 0.1      # uN of normal load that counts as "on the surface" (guessed)
PEEL_RATIO = 1.0          # tangential / normal load that peels the pad off (guessed)


def gate(contact_forces: np.ndarray, n_legs: int = 6, contact_min: float = CONTACT_MIN_UN,
         peel_ratio: float = PEEL_RATIO) -> np.ndarray:
    """contact_forces: (n_legs * segments, 3) world-frame forces on the tarsal
    segments, legs in order. Returns 0/1 per leg."""
    f = np.asarray(contact_forces, float).reshape(n_legs, -1, 3).sum(axis=1)
    normal = f[:, 2]
    shear = np.linalg.norm(f[:, :2], axis=1)
    return ((normal > contact_min) & (shear <= peel_ratio * np.maximum(normal, 0))).astype(np.float32)
