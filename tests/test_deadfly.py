"""The dead-fly harness (src/flyemu/deadfly.py) must be correct before its
results are read (CONSTRUCTION.md principle 6)."""
from __future__ import annotations

import sys
from pathlib import Path

import mujoco as mj
import numpy as np
import pytest

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "src"))

from flyemu import deadfly  # noqa: E402


def test_limit_occupancy_counts_time_near_either_end():
    rng = np.array([[0.0, 1.0], [-1.0, 1.0]])
    q = np.array([[0.01, 0.0], [0.5, 0.95], [0.99, 0.0], [0.5, 0.0]])
    occ = deadfly.limit_occupancy(q, rng)        # band 3% of span
    assert occ.tolist() == [0.5, 0.25]


@pytest.fixture(scope="module")
def baseline():
    tr = deadfly.run(duration_ms=300)
    return tr, deadfly.score(tr)


def test_the_dead_fly_is_silent_and_starts_standing(baseline):
    tr, s = baseline
    assert s["valid_run"]["verdict"] == "pass"            # no divergence; ctrl all zero
    assert not tr.body_ground_contact[0]                   # trunk off the ground at t=0
    assert tr.thorax_z[0] > 1.0                            # standing height (mm)


def test_a_fly_held_up_by_stiff_legs_does_not_count_as_collapsed():
    """Control: the collapse metric can say no."""
    from flyemu.body import Body
    b = Body(vision=False)
    m = b.sim.mj_model
    for j in range(m.njnt):
        if m.jnt_type[j] != mj.mjtJoint.mjJNT_HINGE:
            continue
        nm = mj.mj_id2name(m, mj.mjtObj.mjOBJ_JOINT, j).split("/")[-1]
        if deadfly._group(nm) in ("leg", "tarsus"):
            m.jnt_stiffness[j] *= 300
            m.dof_damping[m.jnt_dofadr[j]] *= 10
    s = deadfly.score(deadfly.run(duration_ms=300, body=b))
    assert s["valid_run"]["verdict"] == "pass"
    assert s["collapse"]["verdict"] == "fail" and s["collapse"]["onset_ms"] is None


def test_a_diverged_run_is_flagged_invalid():
    """MuJoCo silently resets a diverging state; the harness must catch it."""
    from flyemu.body import Body
    b = Body(vision=False)
    m = b.sim.mj_model
    m.jnt_stiffness[:] *= 1e5
    s = deadfly.score(deadfly.run(duration_ms=50, body=b))
    assert s["valid_run"]["verdict"] == "fail"


def test_energy_never_rises_in_the_dead_fly(baseline):
    tr, s = baseline
    assert s["energy"]["max_rise_10ms"] <= 0
