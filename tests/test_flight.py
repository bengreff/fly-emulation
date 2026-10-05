"""Task 8 flight apparatus (s10): wing DOFs by function (F-WING-1), the
wingbeat generator (B10) inside the organism's single motor path, halteres in
antiphase (B13 partial), and the legacy path untouched."""
import sys
from pathlib import Path

import numpy as np
import pytest

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "src"))
needs_graph = pytest.mark.skipif(not (REPO / "data/cache/male_cns_edges.parquet").exists(),
                                 reason="no graph cache")


def test_generator_kinematics_have_the_declared_shape():
    from flyemu.flight import WingKinematics
    k = WingKinematics()
    t = np.linspace(0, 1 / k.f_hz, 400, endpoint=False)
    q = np.array([k.targets(x)[0] for x in t])
    stroke = np.degrees(q[:, 0])
    assert abs((stroke.max() - stroke.min()) - 2 * k.stroke_amp_deg) < 0.5
    # rotation flips sign twice per beat, at the stroke reversals
    r = q[:, 2] - np.radians(k.rot_mean_deg)
    assert (np.diff(np.sign(r)) != 0).sum() == 2
    # velocity targets are the derivative of position targets
    dt = 1e-7
    for x in (0.0003, 0.0021):
        num = (k.targets(x + dt)[0] - k.targets(x - dt)[0]) / (2 * dt)
        assert np.allclose(num, k.targets(x)[1], rtol=1e-4, atol=1e-3)


@needs_graph
def test_forced_generator_beats_the_wings_through_motor_step():
    import mujoco as mj
    from flyemu.organism import Organism
    org = Organism(policy="minimal", profile="m4", min_synapses=5, timestep_ms=0.05,
                   overrides={"flight:wings|generator": 2.0, "joint:wing|range_by_function": 1.0})
    m, d = org.body.sim.mj_model, org.body.sim.mj_data
    w = org.flight.wing
    yaw, hal = [], []
    for s in range(int(5 * 1000 / 218 / 0.05)):         # 5 wingbeats, brain silent
        org.motor_step(np.zeros(0, np.int64))
        yaw.append(d.qpos[w.q_adr[0]]); hal.append(d.qpos[org.flight.haltere.q_adr[0]])
    assert sum(x.number for x in d.warning) == 0
    yaw = np.degrees(np.array(yaw[len(yaw) // 2:]))
    assert 120 < yaw.max() - yaw.min() < 160               # ~140 deg stroke
    c = np.corrcoef(yaw - yaw.mean(), np.array(hal[len(hal) // 2:]))[0, 1]
    assert c < -0.8                                          # halteres in antiphase


@needs_graph
def test_generator_off_leaves_m4_untouched():
    from flyemu.organism import Organism
    org = Organism(policy="minimal", profile="m4", min_synapses=5)
    assert org.flight is None
    r = org.body.sim.mj_model.jnt_range
    names = [org.body.sim.mj_model.joint(j).name for j in range(org.body.sim.mj_model.njnt)]
    j = names.index(f"{org.body.fly.name}/c_thorax-l_wing-yaw")
    assert np.allclose(np.degrees(r[j]), (-15.0, 15.0))


@needs_graph
def test_steering_mns_change_their_wing_only():
    from flyemu.organism import Organism
    org = Organism(policy="minimal", profile="m4", min_synapses=5, timestep_ms=0.05,
                   overrides={"flight:wings|generator": 2.0, "joint:wing|range_by_function": 1.0})
    fm = org.flight
    t = org.conn.neurons.type.fillna("").to_numpy()
    inst = org.conn.neurons.instance.fillna("").to_numpy()
    b2L = np.flatnonzero((t == "b2 MN") & np.char.endswith(inst.astype(str), "_L"))
    assert b2L.size
    for s in range(2000):                         # 100 ms of 200 Hz b2_L firing
        fm.step(b2L if s % 100 == 0 else np.zeros(0, np.int64), np.zeros(org.body.n_actuators))
    assert fm.wing.mod[0, 0] > 1.0 and fm.wing.mod[1, 0] == 0.0     # left amplitude up only


@needs_graph
def test_haltere_coriolis_signal_is_linear_in_rotation_rate_and_side_antisymmetric():
    """Battery item: 'haltere signal linear in body rotation rate' (B13/N16), read as a
    phase-locked afferent would: the drive demodulated by the haltere stroke direction."""
    from flyemu.organism import Organism
    org = Organism(policy="minimal", profile="m4", min_synapses=5, timestep_ms=0.05,
                   overrides={"flight:wings|generator": 2.0, "joint:wing|range_by_function": 1.0,
                              "sense:cs_coriolis|gain": 0.001})
    ch = org.extra.channels["haltere_cs"]
    jl, jr = org.extra.joint_ids["haltere_cs"]
    d = org.body.sim.mj_data
    for _ in range(600):                                  # beat up to speed
        org.motor_step(np.zeros(0, np.int64))
    # evaluate on identical body states: rewind is not available, so compare at the same
    # states by computing all rates at each state
    res = {}
    for yaw in (0.0, 1.0, 2.0, -1.0):
        res[yaw] = []
    for _ in range(4):
        for _k in range(23):
            org.motor_step(np.zeros(0, np.int64))
        obs = org.body.observe()
        keep = d.qvel[3:6].copy()
        jv = obs["joint_velocities"]
        for yaw in res:
            d.qvel[3:6] = [0.0, 0.0, yaw]
            dr = org.extra.drive(org.world, org.body, obs, org.timestep_ms)[ch.rows]
            res[yaw].append([dr[ch.side == 0].mean() * np.sign(jv[jl]),
                             dr[ch.side == 1].mean() * np.sign(jv[jr])])
        d.qvel[3:6] = keep
    r = {k: np.array(v).mean(0) for k, v in res.items()}
    e1, e2, em = r[1.0] - r[0.0], r[2.0] - r[0.0], r[-1.0] - r[0.0]
    assert abs(e1[0]) > 1e-3 and np.sign(e1[0]) == -np.sign(e1[1])     # sides antisymmetric
    assert np.allclose(e2, 2 * e1, rtol=0.2)                            # linear in rate
    assert np.allclose(em, -e1, rtol=0.2)                               # odd in rate


def test_membrane_only_aero_removes_the_overlapping_vein_mesh():
    import mujoco as mj
    from flyemu import flight
    from flyemu.body import Body
    b = Body(vision=False)
    m = b.sim.mj_model
    gid = lambda n: mj.mj_name2id(m, mj.mjtObj.mjOBJ_GEOM, f"{b.fly.name}/{n}")  # noqa: E731
    assert m.geom_fluid[gid("l_wing_brown")][0] == 1.0           # legacy: both meshes lift
    done = flight.apply_aero(b, 3.1)
    assert sorted(done) == [f"{b.fly.name}/l_wing_membrane", f"{b.fly.name}/r_wing_membrane"]
    assert m.geom_fluid[gid("l_wing_brown")][0] == 0.0 and m.geom_fluid[gid("r_wing_brown")][0] == 0.0
    assert m.geom_fluid[gid("l_wing_membrane")][4] == 3.1


def _blade_body():
    import mujoco as mj
    from flyemu import flight
    from flyemu.body import Body
    b = Body(vision=False)
    m, d = b.sim.mj_model, b.sim.mj_data
    m.opt.gravity[:] = 0.0
    hook = flight.apply_blade_element(b)
    mj.mj_forward(m, d)
    return b, m, d, hook


def test_blade_element_reproduces_the_robofly_in_steady_wind():
    """aero:wing|model 1 (F-FLIGHT-3): in a uniform wind the hook's force on a still
    wing is the robofly lift and drag on the membrane planform; MuJoCo's own lift and
    drag on the membrane are off."""
    import mujoco as mj
    from flyemu import flight
    b, m, d, hook = _blade_body()
    g = mj.mj_name2id(m, mj.mjtObj.mjOBJ_GEOM, "flybody/l_wing_membrane")
    assert m.geom_fluid[g][0] == 1.0 and not m.geom_fluid[g][1:6].any()
    R, sz = d.geom_xmat[g].reshape(3, 3), m.geom_size[g]
    o = np.argsort(sz)
    n, c = R[:, o[0]], R[:, o[1]]
    U = 1000.0
    q = 0.5 * m.opt.density * U ** 2 * np.pi * sz[o[1]] * sz[o[2]]
    for deg in (5.0, 30.0, 45.0, 70.0, 85.0):
        a = np.radians(deg)
        u = np.cos(a) * c + np.sin(a) * n
        m.opt.wind[:] = U * u
        hook(d)
        F = hook.force[0]
        cl, cd = flight.robofly_coefficients(np.array([deg]))
        assert np.isclose(F @ u / q, cd[0], rtol=1e-6)
        assert np.isclose(F @ (-np.sin(a) * c + np.cos(a) * n) / q, cl[0], rtol=1e-6)
        assert hook.parts[0, 2] @ hook.parts[0, 2] == 0.0      # still wing: no rotational force


def test_blade_rotational_force_follows_the_pitch_joint_not_the_cone_spin():
    """The stroke sweeps a cone that spins the wing about its span without changing
    alpha; only the pitch (rotation) joint rate drives the rotational term."""
    import mujoco as mj
    from flyemu import flight
    b, m, d, hook = _blade_body()
    jid = {fn: mj.mj_name2id(m, mj.mjtObj.mjOBJ_JOINT, f"flybody/c_thorax-l_wing-{flight.FN[fn]}")
           for fn in ("stroke", "deviation", "rotation")}
    d.qpos[m.jnt_qposadr[jid["stroke"]]] = np.radians(86.0)
    d.qpos[m.jnt_qposadr[jid["deviation"]]] = np.radians(40.0)
    d.qpos[m.jnt_qposadr[jid["rotation"]]] = np.radians(-30.0)
    d.qvel[:] = 0.0
    d.qvel[m.jnt_dofadr[jid["stroke"]]] = 1500.0
    hook(d)
    assert np.linalg.norm(hook.parts[0, 0]) > 0 and not hook.parts[0, 2].any()
    d.qvel[m.jnt_dofadr[jid["rotation"]]] = 2000.0
    hook(d)
    assert np.linalg.norm(hook.parts[0, 2]) > 0
