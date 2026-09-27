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


def test_equilibrium_moves_with_the_spring_reference():
    """Probe check: the static solver must respond to the spring reference
    (an early-stopping optimiser once returned the start pose)."""
    import mujoco as mj
    from flyemu import passive
    from flyemu.body import Body
    from passive_rest_protocol import Leg
    b = Body(vision=False)
    passive.apply_coupled(b)
    b.reset()
    mj.mj_forward(b.sim.mj_model, b.sim.mj_data)
    leg = Leg(b, "rf")
    a0 = leg.equilibrium(0.0)
    i = leg.names.index("rf_trochanterfemur-rf_tibia-pitch")
    leg.ref[i] += 0.3
    a1 = leg.equilibrium(0.0)
    assert abs(a1[2] - a0[2]) > 5.0                       # psi follows a 17 deg FTi reference shift
