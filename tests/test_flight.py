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


def test_measured_wing_length_scales_the_strips_about_the_hinge():
    """aero:wing|size_source 1 (F-FLIGHT-3): strips, chords and widths scale by
    R_measured / R_scan about the hinge, so the second moment of area (lift at fixed
    angular kinematics) scales by k^4 and the planform by k^2."""
    import mujoco as mj
    from flyemu import flight
    from flyemu.body import Body
    hooks = []
    for L in (None, flight.WING_LENGTH_FEMALE_MM):
        b = Body(vision=False)
        hooks.append(flight.apply_blade_element(b, length_mm=L))
    m = b.sim.mj_model
    k = flight.WING_LENGTH_FEMALE_MM / flight.WING_LENGTH_SCAN_MM
    for w, s in enumerate(flight.SIDES):
        j = mj.mj_name2id(m, mj.mjtObj.mjOBJ_JOINT, f"flybody/c_thorax-{s}_wing-{flight.FN['rotation']}")
        jp = m.jnt_pos[j]
        (a, b_) = (np.linalg.norm(h.pts[w] - jp, axis=1) for h in hooks)
        assert np.allclose(b_, k * a)
        S2 = [float((h.c[w] * h.dr[w] * np.linalg.norm(h.pts[w] - jp, axis=1) ** 2).sum()) for h in hooks]
        assert np.isclose(S2[1] / S2[0], k ** 4)
        assert np.isclose((hooks[1].c[w] * hooks[1].dr[w]).sum() / (hooks[0].c[w] * hooks[0].dr[w]).sum(), k ** 2)
        assert hooks[1].x0[w] == hooks[0].x0[w]                 # pitch-axis chord fraction unchanged


def test_measured_planform_area_rescales_only_the_chords():
    """area_mm2 (s12 robotic-fly test, D. hydei R x mean chord): the planform equals the
    given area; strip positions and the chord shape are those of the length scaling."""
    from flyemu import flight
    from flyemu.body import Body
    base = flight.apply_blade_element(Body(vision=False), length_mm=2.99)
    hook = flight.apply_blade_element(Body(vision=False), length_mm=2.99, area_mm2=2.831)
    for w in range(2):
        assert np.isclose((hook.c[w] * hook.dr[w]).sum(), 2.831)
        assert np.allclose(hook.pts[w], base.pts[w])
        assert np.allclose(hook.c[w] / base.c[w], hook.c[w][0] / base.c[w][0])


def test_hydei_planform_puts_the_measured_chords_on_the_same_strips():
    """planform "hydei" (s12, DECISIONS 21:17): Muijres 2014's measured chord/L against
    r/L on the model's strips; positions unchanged, the area as given, and the second
    moment of area that of the measured wing (r2/L 0.584; the ellipse's is 0.539)."""
    import mujoco as mj
    from flyemu import flight
    from flyemu.body import Body
    base = flight.apply_blade_element(Body(vision=False), length_mm=2.99, area_mm2=2.831)
    b = Body(vision=False)
    hook = flight.apply_blade_element(b, length_mm=2.99, area_mm2=2.831, planform="hydei")
    m = b.sim.mj_model
    for w, s in enumerate(flight.SIDES):
        jp = m.jnt_pos[mj.mj_name2id(m, mj.mjtObj.mjOBJ_JOINT, f"flybody/c_thorax-{s}_wing-{flight.FN['rotation']}")]
        assert np.allclose(hook.pts[w], base.pts[w])
        assert np.isclose((hook.c[w] * hook.dr[w]).sum(), 2.831)
        r = (hook.pts[w] - jp) @ hook.span[w]
        R = r[-1] + hook.dr[w] / 2
        r2 = [np.sqrt((h.c[w] * r ** 2).sum() / h.c[w].sum()) / R for h in (hook, base)]
        assert abs(r2[0] - 0.584) < 0.01 and abs(r2[1] - 0.539) < 0.01


def _wing_joint_axes(m, d, side):
    import mujoco as mj
    from flyemu import flight
    jid = [mj.mj_name2id(m, mj.mjtObj.mjOBJ_JOINT, f"flybody/c_thorax-{side}_wing-{flight.FN[f]}")
           for f in ("stroke", "deviation", "rotation")]
    return [m.jnt_qposadr[j] for j in jid], [m.jnt_dofadr[j] for j in jid], np.array([d.xaxis[j] for j in jid]).T


def _measured_pose(b, m, d, side, phi, dev, alpha):
    """Put one wing at a stroke-frame pose (Muijres convention) via wing_pose_ik."""
    import mujoco as mj
    from flyemu import flight
    q, err = flight.wing_pose_ik(b, side, *flight.stroke_frame_vectors(phi, dev, alpha, side))
    assert err < 1e-3
    adr, dof, _ = _wing_joint_axes(m, d, side)
    d.qpos[adr] = q
    d.qvel[:] = 0.0
    mj.mj_kinematics(m, d)
    return dof, _wing_joint_axes(m, d, side)[2]


def test_blade_rotational_force_follows_rotation_in_the_stroke_frame_not_the_cone_spin():
    """The stroke sweeps a cone about the stroke-plane normal that spins the wing about
    its span without changing alpha; only rotation relative to the stroke frame drives
    the rotational term. (The model's hinge axes are not the stroke frame, F-WING-3, so
    no single joint is 'the stroke'; the joint rates are solved for each motion.)"""
    from flyemu import flight
    b, m, d, hook = _blade_body()
    flight.open_wing_ranges(b)
    dof, A = _measured_pose(b, m, d, "l", 20.0, 10.0, 45.0)      # off the stroke plane
    n = flight.stroke_normal()                                    # thorax at identity
    d.qvel[dof] = np.linalg.solve(A, 3000.0 * n)                  # a pure cone about n
    hook(d)
    assert np.linalg.norm(hook.parts[0, 0]) > 0 and np.linalg.norm(hook.parts[0, 2]) < 1e-9 * np.linalg.norm(hook.parts[0, 0])
    sp = d.xmat[hook.bid[0]].reshape(3, 3) @ hook.span[0]
    d.qvel[dof] = np.linalg.solve(A, 3000.0 * n + 2000.0 * sp)    # plus rotation about the span
    hook(d)
    assert np.linalg.norm(hook.parts[0, 2]) > 0
    assert hook.rot_rate == "stroke_frame"


def test_blade_rotational_force_adds_to_lift_when_alpha_rises():
    """Sane & Dickinson 2002: rotation that raises the angle of attack during
    translation adds force on the lift side; rotation that lowers it subtracts."""
    import mujoco as mj
    from flyemu import flight
    b, m, d, hook = _blade_body()
    flight.open_wing_ranges(b)
    dof, A = _measured_pose(b, m, d, "l", 0.0, 0.0, 50.0)
    sp = d.xmat[hook.bid[0]].reshape(3, 3) @ hook.span[0]
    t = np.cross(sp, flight.stroke_normal())                      # stroke direction, unit
    m.opt.wind[:] = 1000.0 * t                                    # wing moves along -t
    for s in (1.0, -1.0):
        d.qvel[:] = 0.0
        hook(d)
        a0 = hook.alpha[0].mean()
        d.qvel[dof] = np.linalg.solve(A, s * 500.0 * sp)
        hook(d)
        qp = d.qpos.copy()
        mj.mj_integratePos(m, qp, d.qvel, 1e-5)
        dd = mj.MjData(m); dd.qpos[:] = qp; dd.qvel[:] = 0.0
        lift, rot = hook.parts[0, 0].copy(), hook.parts[0, 2].copy()
        hook(dd)
        rising = hook.alpha[0].mean() > a0
        assert (rot @ lift > 0) == rising


def test_stroke_frame_spin_is_the_measured_rotation_rate():
    """For poses built from stroke-frame angles, the hook's rotation rate equals the
    rate of the measured rotation angle (left wing +, right wing -)."""
    import mujoco as mj
    from flyemu import flight
    b, m, d, hook = _blade_body()
    flight.open_wing_ranges(b)
    dt = 1e-6
    for side, sgn in (("l", 1.0), ("r", -1.0)):
        k = flight.SIDES.index(side)
        adr, dof, _ = _wing_joint_axes(m, d, side)
        q0, _ = flight.wing_pose_ik(b, side, *flight.stroke_frame_vectors(25.0, -8.0, 50.0, side))
        q1, _ = flight.wing_pose_ik(b, side, *flight.stroke_frame_vectors(25.3, -8.1, 52.0, side), q_start=q0)
        d.qpos[adr] = q0; d.qvel[:] = 0.0; d.qvel[dof] = (q1 - q0) / dt
        mj.mj_kinematics(m, d); mj.mj_comPos(m, d); mj.mj_comVel(m, d)
        v = np.zeros(6)
        mj.mj_objectVelocity(m, d, mj.mjtObj.mjOBJ_XBODY, hook.bid[k], v, 0)
        sp = d.xmat[hook.bid[k]].reshape(3, 3) @ hook.span[k]
        spin = flight.stroke_frame_spin(v[:3], sp, flight.stroke_normal())
        assert np.isclose(spin, sgn * np.radians(2.0) / dt, rtol=0.02)


def test_wing_pose_ik_recovers_generator_poses_on_both_wings():
    """wing_pose_ik (used to impose measured kinematics) recovers the hinge angles
    of known wing poses from the membrane's span and leading-edge directions."""
    import mujoco as mj
    from flyemu import flight
    from flyemu.body import Body
    b = Body(vision=False)
    flight.apply_wing_ranges(b)
    m = b.sim.mj_model
    d = mj.MjData(m)
    kin = flight.WingKinematics(rot_amp_deg=55.0)
    th = mj.mj_name2id(m, mj.mjtObj.mjOBJ_BODY, "flybody/c_thorax")
    for side in flight.SIDES:
        g, i_s, i_c, le = flight.wing_axes(b, side)
        out = flight.wing_span_sign(b, side)
        adr = [m.jnt_qposadr[mj.mj_name2id(m, mj.mjtObj.mjOBJ_JOINT, f"flybody/c_thorax-{side}_wing-{flight.FN[f]}")]
               for f in ("stroke", "deviation", "rotation")]
        for t in (0.0, 0.0011, 0.0034):
            q, _ = kin.targets(t)
            d.qpos[adr] = q
            mj.mj_kinematics(m, d)
            Rt, Rg = d.xmat[th].reshape(3, 3), d.geom_xmat[g].reshape(3, 3)
            qs, err = flight.wing_pose_ik(b, side, out * (Rt.T @ Rg[:, i_s]), le * (Rt.T @ Rg[:, i_c]))
            assert err < 1e-3 and np.allclose(qs, q, atol=1e-5)


def test_s10_generator_crosses_the_wings_and_measured_poses_do_not():
    """F-WING-3: the s10 joint-space generator's mid-downstroke swings each wing
    over the dorsum to the far side; a measured mid-downstroke pose (Muijres 2014
    convention) fitted by wing_pose_ik stays on its own side."""
    import mujoco as mj
    from flyemu import flight
    from flyemu.body import Body
    b = Body(vision=False)
    flight.open_wing_ranges(b)
    m = b.sim.mj_model
    d = mj.MjData(m)
    th = mj.mj_name2id(m, mj.mjtObj.mjOBJ_BODY, "flybody/c_thorax")
    q_gen, _ = flight.WingKinematics().targets(0.0011)
    for side in flight.SIDES:
        g, i_s, _, _ = flight.wing_axes(b, side)
        out, lat = flight.wing_span_sign(b, side), (1.0 if side == "l" else -1.0)
        adr, _, _ = _wing_joint_axes(m, d, side)
        for q, own in ((q_gen, False),
                       (flight.wing_pose_ik(b, side, *flight.stroke_frame_vectors(0.0, 0.0, 50.0, side))[0], True)):
            d.qpos[adr] = q
            mj.mj_kinematics(m, d)
            span = out * (d.xmat[th].reshape(3, 3).T @ d.geom_xmat[g].reshape(3, 3)[:, i_s])
            assert (span[1] * lat > 0.5) == own


@needs_graph
def test_measured_beat_keeps_each_wing_on_its_side_and_steers():
    """flight:wings|kinematics 1 (F-WING-3 fix): the measured beat, PD-tracked through
    motor_step inside the measured ranges, sweeps the measured stroke amplitude with each
    wing on its own side; a b2 (amplitude) MN burst on the left widens the left stroke."""
    import mujoco as mj
    from flyemu import flight
    from flyemu.organism import Organism
    org = Organism(policy="minimal", profile="m4", min_synapses=5, timestep_ms=0.05,
                   overrides={"flight:wings|generator": 2.0, "flight:wings|kinematics": 1.0,
                              "joint:wing|range_by_function": 2.0})
    m, d = org.body.sim.mj_model, org.body.sim.mj_data
    assert isinstance(org.flight.wing.kin, flight.StrokeFrameKinematics)
    b = org.body
    th = mj.mj_name2id(m, mj.mjtObj.mjOBJ_BODY, "flybody/c_thorax")
    n, f = flight.stroke_normal(), np.array([np.cos(np.radians(flight.STROKE_PLANE_DEG)), 0.0,
                                             -np.sin(np.radians(flight.STROKE_PLANE_DEG))])
    geo = {s: (flight.wing_axes(b, s), flight.wing_span_sign(b, s)) for s in flight.SIDES}

    def phis():
        out = []
        for s in flight.SIDES:
            (g, i_s, _, _), sg = geo[s]
            sp = sg * (d.xmat[th].reshape(3, 3).T @ d.geom_xmat[g].reshape(3, 3)[:, i_s])
            lat = 1.0 if s == "l" else -1.0
            assert sp[1] * lat > 0.0                       # never over the dorsum
            p = sp - (sp @ n) * n
            out.append(np.degrees(np.arctan2(-(p @ f), p[1] * lat)))
        return out

    per = int(round(1000 / 218 / 0.05))
    ph = []
    for s in range(10 * per):
        org.motor_step(np.zeros(0, np.int64))
        if s >= 6 * per:
            ph.append(phis())
    assert sum(x.number for x in d.warning) == 0
    pp = np.ptp(np.array(ph), axis=0)
    assert np.all(abs(pp - 131.6) < 10.0)                  # Muijres 2014 stroke, 131.6 deg p-p
    t = org.conn.neurons.type.fillna("").to_numpy()
    inst = org.conn.neurons.instance.fillna("").to_numpy().astype(str)
    b2L = np.flatnonzero((t == "b2 MN") & np.char.endswith(inst, "_L"))
    ph = []
    for s in range(10 * per):                              # 50 Hz b2_L firing
        org.motor_step(b2L if s % 400 == 0 else np.zeros(0, np.int64))
        if s >= 6 * per:
            ph.append(phis())
    pp2 = np.ptp(np.array(ph), axis=0)
    assert pp2[0] > pp[0] + 2.0 and abs(pp2[1] - pp[1]) < 1.0


def test_blade_added_mass_is_the_flat_plate_reaction_to_normal_acceleration():
    """aero:wing|added_mass 1 (s12): accelerating a wing along its own normal in still
    air gives -rho pi c^2/4 dr dv_n/dt summed over the strips, along the normal; a
    second call in the same step keeps it; switched off it is zero."""
    import mujoco as mj
    from flyemu import flight
    from flyemu.body import Body
    for on in (True, False):
        b = Body(vision=False)
        m, d = b.sim.mj_model, b.sim.mj_data
        hook = flight.apply_blade_element(b, length_mm=2.99, area_mm2=2.831, planform="hydei", added_mass=on)
        mj.mj_forward(m, d)
        n = d.xmat[hook.bid[0]].reshape(3, 3) @ hook.normal[0]
        dt, v1, v2 = 5e-5, 100.0, 160.0                          # mm/s along the left wing normal
        d.time, d.qvel[:] = 0.0, 0.0
        d.qvel[:3] = v1 * n
        hook(d)
        d.time = dt
        d.qvel[:3] = v2 * n
        hook(d)
        want = -m.opt.density * np.pi / 4 * (hook.c[0] ** 2 * hook.dr[0]).sum() * (v2 - v1) / dt * n
        got = hook.parts[0, 3].copy()
        if on:
            assert np.allclose(got, want, rtol=1e-6)
            hook(d)
            assert np.allclose(hook.parts[0, 3], want, rtol=1e-6)
            assert np.allclose(hook.force[0], hook.parts[0].sum(0))
        else:
            assert not got.any()
