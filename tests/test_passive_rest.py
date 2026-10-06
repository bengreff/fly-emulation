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


def test_rest_mirror_gives_left_legs_the_right_values():
    """joint:leg|rest_mirror 1: every left joint takes its right partner's fitted reference;
    the right legs (the measured side) are unchanged."""
    import re

    import pandas as pd
    from flyemu.passive import REST_TABLE, REST_TABLE_COXA, REST_TABLE_CTR, mirror_rest_table
    for f in (REST_TABLE, REST_TABLE_COXA, REST_TABLE_CTR):
        t = pd.read_csv(f, comment="#")
        m = mirror_rest_table(t)
        assert sorted(m.joint) == sorted(t.joint)
        ref = dict(zip(m.joint, m.spring_ref_rad))
        right = t[t.leg.str.startswith("r")]
        assert len(right) * 2 == len(t)
        for j, v in zip(right.joint, right.spring_ref_rad):
            assert ref[j] == v
            assert ref[re.sub(r"(^|-)r([fmh])_", r"\1l\2_", j)] == v


def test_damping_mirror_gives_left_legs_the_right_values():
    """joint:leg|damping_mirror 1: every left leg hinge DOF (not the inter-tarsal chain) takes
    its right partner's damping; the right legs are unchanged."""
    import re

    import mujoco as mj
    from flyemu import passive
    from flyemu.body import Body
    b = Body(vision=False)
    passive.apply_coupled(b)
    passive.set_damping_from_stiffness(b, 0.05)
    m = b.sim.mj_model
    pre = f"{b.fly.name}/"
    names = {(mj.mj_id2name(m, mj.mjtObj.mjOBJ_JOINT, j) or "").removeprefix(pre): j for j in range(m.njnt)}
    before = m.dof_damping.copy()
    n = passive.mirror_leg_damping(b)
    left = [k for k in names if re.search(r"(^|[_-])l[fmh]_", k) and k.count("tarsus") < 2]
    assert n == len(left) == 21
    for k in left:
        r = names[re.sub(r"(^|[_-])l([fmh])_", r"\1r\2_", k)]
        assert m.dof_damping[m.jnt_dofadr[names[k]]] == before[m.jnt_dofadr[r]]
        assert m.dof_damping[m.jnt_dofadr[r]] == before[m.jnt_dofadr[r]]


def test_m9r_carries_the_gate_force_per_spike():
    """A profile name means one model: m9r holds the force_per_spike every gate ran with (s12)."""
    from flyemu import profiles
    from flyemu.registry import Policy, Registry

    reg = Registry(Policy.MINIMAL)
    profiles.apply(reg, "m9r")
    v = reg.require("motor_unit:all", "force_per_spike", units="uN*mm", model_use="test",
                    subsystem="neuromuscular", instances=1, minimal=1.0)
    assert v == 10.0
    reg2 = Registry(Policy.MINIMAL)
    reg2.overrides["motor_unit:all|force_per_spike"] = 3.0      # an explicit --set still wins
    profiles.apply(reg2, "m9r")
    assert reg2.overrides["motor_unit:all|force_per_spike"] == 3.0
