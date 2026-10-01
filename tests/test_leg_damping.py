"""joint:leg|damping (session 11): neutral 1 leaves the body unchanged; a value scales
every leg hinge DOF except the inter-tarsal chain (default-1 DOFs become c)."""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))


def test_leg_damping_is_neutral_at_one_and_sets_leg_dofs_only():
    from flyemu import passive
    from flyemu.body import Body
    from flyemu.registry import Registry
    base = Body(vision=False)
    d0 = base.sim.mj_model.dof_damping.copy()
    b = Body(vision=False)
    reg = Registry("minimal")
    passive.register(reg, b)                     # neutral: key read, nothing changed
    b_ref = Body(vision=False)
    reg_ref = Registry("minimal")
    reg_ref.overrides["joint:leg|passive_stiffness_source"] = 0.0
    assert np.array_equal(b.sim.mj_model.dof_damping, d0)
    n = passive.set_leg_damping(b_ref, 0.043)
    m = b_ref.sim.mj_model
    changed = np.flatnonzero(m.dof_damping != d0)
    assert n > 30 and changed.size == n and np.allclose(m.dof_damping[changed], 0.043 * d0[changed])
    assert "joint:leg|damping" in set(reg.inventory().entity + "|" + reg.inventory().property)
