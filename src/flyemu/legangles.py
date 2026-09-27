"""Leg angles as defined by Wang et al. 2025 eLife (PMC12324252), methods Eqs. 5-11:
theta levation-depression, phi protraction-retraction (0 = anterior), psi
extension-flexion (0 = straight), gamma pronation-supination (convention
unverified in s9). Thorax frame: x forward, y left, z up."""
from __future__ import annotations

import numpy as np


def paper_angles(pF_ctr, pF_fti, pT_titA, right: bool = True) -> np.ndarray:
    """theta, phi, psi, gamma (deg) in the thorax frame (x fwd, y left, z up)."""
    xp = np.array([0.0, -1.0, 0.0]) if right else np.array([0.0, 1.0, 0.0])  # toward the leg's side
    yp = np.array([1.0, 0.0, 0.0])
    zp = np.array([0.0, 0.0, 1.0])
    rF = pF_fti - pF_ctr
    rF /= np.linalg.norm(rF)
    rT = pT_titA - pF_fti
    rT /= np.linalg.norm(rT)
    xz = rF - (rF @ yp) * yp
    theta = np.degrees(np.arccos(np.clip(xz @ zp / np.linalg.norm(xz), -1, 1)))
    xy = rF - (rF @ zp) * zp
    phi = np.degrees(np.arccos(np.clip(xy @ yp / np.linalg.norm(xy), -1, 1)))
    psi = np.degrees(np.arccos(np.clip(rF @ rT, -1, 1)))
    z2 = rF
    y2 = np.cross(z2, zp)
    y2 /= np.linalg.norm(y2)
    x2 = np.cross(y2, z2)
    gamma = np.degrees(np.arctan2(rT @ y2, rT @ x2)) % 360
    return np.array([theta, phi, psi, gamma])
