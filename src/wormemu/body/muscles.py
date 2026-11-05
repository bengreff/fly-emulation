"""The 95 body-wall muscles: identity, placement along the body, activation dynamics, stretch readout.

Identity (measured): Cook et al. 2019 names dBWML1-24, dBWMR1-24, vBWML1-23, vBWMR1-24 (WormAtlas: DL, DR, VR
24 cells, VL 23). Placement along the body (inferred, ledger rows WB4_*): cell i of a quadrant is centred at
s0 + (i - 0.5) * pitch with pitch = (s1 - s0) / 24 and spans two pitches, so neighbours overlap by half, standing in
for the two interlocking rows per quadrant. Which VL cell is absent is not established (BODY_PARAMS.md s6); the
layout numbers VL 1-23 on the first 23 positions, so the most posterior VL slot is empty (inferred, a choice).
"""
from __future__ import annotations

import numpy as np

QUADRANTS = ("DL", "DR", "VL", "VR")
COUNT = {"DL": 24, "DR": 24, "VL": 23, "VR": 24}


def muscle_names():
    out = []
    for q in QUADRANTS:
        pre = ("d" if q[0] == "D" else "v") + "BWM" + q[1]
        out += [(pre + str(i), q, i) for i in range(1, COUNT[q] + 1)]
    return out


NAMES = [n for n, _, _ in muscle_names()]
N_MUSCLES = len(NAMES)  # 95


class MuscleLayout:
    """Coverage weights of each muscle over the rod joints, and the quadrant signs."""

    def __init__(self, s_joint_frac: np.ndarray, s_start: float, s_end: float, edge_taper: float):
        self.s = s_joint_frac
        pitch = (s_end - s_start) / 24.0
        rows = muscle_names()
        self.quadrant = np.array([q for _, q, _ in rows])
        self.index = np.array([i for _, _, i in rows])
        self.centre = s_start + (self.index - 0.5) * pitch
        self.half = pitch  # half-length: each cell spans two pitches
        d = np.abs(self.s[:, None] - self.centre[None, :]) / self.half  # (joints, muscles)
        # flat over the cell with a cosine taper over the outer `edge_taper` fraction of each half
        w = np.clip((1.0 - d) / max(edge_taper, 1e-9), 0.0, 1.0)
        self.W = 0.5 - 0.5 * np.cos(np.pi * w)
        self.dorsal = np.array([q[0] == "D" for q in self.quadrant])
        self.sign = np.where(self.dorsal, 1.0, -1.0)  # +1 dorsal, -1 ventral
        self.qmask = {q: self.quadrant == q for q in QUADRANTS}
        self.qcover = {q: self.W[:, m].sum(1) for q, m in self.qmask.items()}

    def quadrant_drive(self, f: np.ndarray) -> dict:
        """Coverage-weighted mean of a per-muscle quantity f (e.g. force fraction) in each quadrant, per joint."""
        out = {}
        for q, m in self.qmask.items():
            c = self.qcover[q]
            out[q] = np.where(c > 1e-9, (self.W[:, m] @ f[m]) / np.maximum(c, 1e-9), 0.0)
        return out

    def net_drive(self, f: np.ndarray) -> np.ndarray:
        """Dorsal minus ventral drive per joint, in [-1, 1]; left and right quadrants average (planar body)."""
        d = self.quadrant_drive(f)
        return 0.5 * (d["DL"] + d["DR"]) - 0.5 * (d["VL"] + d["VR"])

    def per_muscle_mean(self, x_joint: np.ndarray) -> np.ndarray:
        """Coverage-weighted mean of a per-joint quantity over each muscle's span."""
        return (self.W.T @ x_joint) / np.maximum(self.W.sum(0), 1e-9)
