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


def test_measured_leg_springs_are_about_seventy_times_too_weak():
    """F-PASSIVE-1: the unit reading mN*m/deg is the one under which the fly
    falls with measured springs and stands only when they are scaled ~70x,
    as the paper states. (N*m/deg would be 1000x stiffer and stand.)"""
    from flyemu import passive
    from flyemu.body import Body
    res = {}
    for scale in (1, 10, 100):
        b = Body(vision=False)
        passive.apply(b, 1, scale=scale)
        res[scale] = deadfly.score(deadfly.run(duration_ms=300, body=b))["collapse"]
    assert res[1]["verdict"] == "pass" and res[10]["verdict"] == "pass"
    assert res[100]["onset_ms"] is None


def test_folded_wings_leave_no_spring_outside_its_range():
    from flyemu import passive
    from flyemu.body import Body
    b = Body(vision=False)
    assert passive.springs_outside_range(b) == ["c_thorax-l_wing-yaw", "c_thorax-r_wing-yaw"]
    passive.fold_wings(b)
    assert passive.springs_outside_range(b) == []


def test_measured_table_maps_onto_real_joints():
    from flyemu import passive
    from flyemu.body import Body
    k = passive.apply(Body(vision=False), 1)
    assert len(k) == 2 * 3 * 7                       # 2 sides x 3 legs x 7 hinges
    assert min(k.values()) > 0.1 and max(k.values()) < 3.3


def test_coupled_springs_reduce_to_mujocos_springs_when_diagonal():
    """Neutral equivalence for the coupled-spring hook (F-PASSIVE-2)."""
    from flyemu import passive
    from flyemu.body import Body
    b = Body(vision=False)
    m, d = b.sim.mj_model, b.sim.mj_data
    passive.apply(b, 1)
    b.reset()
    names = ["c_thorax-rf_coxa-yaw", "c_thorax-rf_coxa-roll", "rf_trochanterfemur-rf_tibia-pitch"]
    js = [mj.mj_name2id(m, mj.mjtObj.mjOBJ_JOINT, "flybody/" + n) for n in names]
    dofs = np.array([m.jnt_dofadr[j] for j in js])
    qa = np.array([m.jnt_qposadr[j] for j in js])
    cs = passive.CoupledSprings(b, {"rf": np.diag(m.jnt_stiffness[js])}, {"rf": dofs},
                                {"rf": qa}, {"rf": m.qpos_spring[qa].copy()})
    d.qpos[qa] += np.array([0.1, -0.2, 0.3])
    mj.mj_forward(m, d)
    cs(d)
    assert np.allclose(d.qfrc_applied[dofs], d.qfrc_spring[dofs])


def test_coupled_springs_are_positive_definite_and_seventy_times_too_weak():
    from flyemu import passive
    from flyemu.body import Body
    b = Body(vision=False)
    sp = passive.apply_coupled(b)
    assert all(np.linalg.eigvalsh(K).min() > 0 for K in sp.K.values())    # no springless direction
    s1 = deadfly.score(deadfly.run(duration_ms=300, body=b))
    assert s1["valid_run"]["verdict"] == "pass" and s1["collapse"]["verdict"] == "pass"
    assert s1["energy"]["max_rise_10ms"] <= 0                               # hook energy counted
    b = Body(vision=False)
    passive.apply_coupled(b, scale=100)
    s100 = deadfly.score(deadfly.run(duration_ms=300, body=b))
    assert not s100["collapse"]["trunk_on_ground_at_end"]


def test_fitted_rest_angles_reach_both_mujoco_and_the_coupled_springs():
    from flyemu import passive
    from flyemu.body import Body
    b = Body(vision=False)
    sp = passive.apply_coupled(b)
    before = {L: q.copy() for L, q in sp.qref.items()}
    n = passive.set_rest_angles(b)
    assert n == 30                                                   # 6 legs x 5 joints
    assert any(not np.allclose(sp.qref[L], before[L]) for L in sp.qref)
    m = b.sim.mj_model
    j = mj.mj_name2id(m, mj.mjtObj.mjOBJ_JOINT, "flybody/rh_coxa-rh_trochanterfemur-pitch")
    k = list(sp.qadr["rh"]).index(m.jnt_qposadr[j])
    assert np.isclose(sp.qref["rh"][k], m.qpos_spring[m.jnt_qposadr[j]])
