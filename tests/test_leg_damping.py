"""Session 12 B (leg damping): joint:leg|damping_source = 1 sets each leg hinge's
damping to tau x its own measured stiffness (passive.set_damping_from_stiffness;
F-DAMP-1)."""
from __future__ import annotations

import sys
from pathlib import Path

import mujoco as mj
import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from flyemu import passive  # noqa: E402
from flyemu.body import Body  # noqa: E402


def _leg_hinges(m):
    out = []
    for j in range(m.njnt):
        name = mj.mj_id2name(m, mj.mjtObj.mjOBJ_JOINT, j) or ""
        if m.jnt_type[j] == mj.mjtJoint.mjJNT_HINGE and name.count("tarsus") < 2 and \
                any(f"{leg}_" in name for leg in ("lf", "lm", "lh", "rf", "rm", "rh")):
            out.append(j)
    return out


def test_damping_is_tau_times_the_coupled_diagonal_and_spares_the_tarsal_chain():
    b = Body(vision=False)
    m = b.sim.mj_model
    before = m.dof_damping.copy()
    springs = passive.apply_coupled(b)
    n = passive.set_damping_from_stiffness(b, 0.05)
    hinges = _leg_hinges(m)
    assert n == len(hinges) > 0
    diag = {int(d): k for L, K in springs.K.items() for d, k in zip(springs.dofs[L], np.diag(K))}
    for j in hinges:
        dof = int(m.jnt_dofadr[j])
        k = diag.get(dof, float(m.jnt_stiffness[j]))
        assert k > 0 and np.isclose(m.dof_damping[dof], 0.05 * k)
    # every other DOF (tarsal chain, wings, head, abdomen, free joint) is untouched
    other = np.ones(m.nv, bool)
    other[[int(m.jnt_dofadr[j]) for j in hinges]] = False
    assert np.array_equal(m.dof_damping[other], before[other])


def test_relaxation_time_is_tau_for_an_isolated_joint():
    """With stiffness k and damping tau*k, a quasi-static joint relaxes with
    time constant tau; check the stored ratio, not a simulation."""
    b = Body(vision=False)
    m = b.sim.mj_model
    passive.apply(b, 1)
    passive.set_damping_from_stiffness(b, 0.02)
    for j in _leg_hinges(m):
        k = m.jnt_stiffness[j]
        assert np.isclose(m.dof_damping[m.jnt_dofadr[j]] / k, 0.02)
