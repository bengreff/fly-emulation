"""The eLife angle definitions (scripts/passive_rest_protocol.py) on known geometry."""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "scripts"))
sys.path.insert(0, str(REPO / "src"))

from passive_rest_protocol import paper_angles  # noqa: E402

O = np.zeros(3)


def test_levation_protraction_and_flexion_angles():
    down, fwd, right = np.array([0, 0, -1.0]), np.array([1.0, 0, 0]), np.array([0, -1.0, 0])
    th, ph, ps, _ = paper_angles(O, down, down * 2)            # femur down, tibia straight on
    assert np.isclose(th, 180) and np.isclose(ps, 0)
    fr = (fwd + right) / np.sqrt(2)
    th, ph, ps, _ = paper_angles(O, fr, fr + down)              # femur forward-right, tibia down
    assert np.isclose(ph, 45) and np.isclose(th, 90) and np.isclose(ps, 90)
    _, ph, _, _ = paper_angles(O, -fwd, -fwd * 2)               # femur backward
    assert np.isclose(ph, 180)
    th, ph, _, _ = paper_angles(O, right, right * 2)            # femur out to the right side
    assert np.isclose(th, 90) and np.isclose(ph, 90)
