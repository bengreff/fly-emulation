"""B4 antagonist Hill muscles (src/flyemu/muscles.py)."""
from __future__ import annotations

import sys
from pathlib import Path

import mujoco as mj
import numpy as np

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "src"))

from flyemu import muscles  # noqa: E402


def test_curves_equal_mujocos_own_muscle_gain():
    rng = np.random.default_rng(0)
    for _ in range(300):
        lmin, lmax = rng.uniform(0.3, 0.9), rng.uniform(1.1, 2.0)
        vmax, fvmax, F0 = rng.uniform(2, 20), rng.uniform(1.1, 1.8), rng.uniform(1, 300)
        lr = np.array([0.4, 0.6])
        prm = np.array([0.75, 1.05, F0, 1.0, lmin, lmax, vmax, 0.0, fvmax])
        L0 = (lr[1] - lr[0]) / (prm[1] - prm[0])
        ln, vel = rng.uniform(0.3, 0.7), rng.uniform(-3, 3)
        ref = mj.mju_muscleGain(ln, vel, lr, 1.0, prm)
        L = prm[0] + (ln - lr[0]) / L0
        V = vel / (L0 * vmax)
        ours = -F0 * muscles.gain_length(L, lmin, lmax) * muscles.gain_velocity(V, fvmax)
        assert np.isclose(ours, ref, rtol=1e-9, atol=1e-9), (ln, vel, ours, ref)


def _pair():
    one = lambda v: np.array([v, v], float)  # noqa: E731
    return muscles.MusclePairs(np.array(["j", "j"]), np.array([1.0, -1.0]), one(100.0), one(0.02),
                               one(0.1), one(0.5), one(1.6), one(10.0), one(1.4), one(0.0))


def test_zero_activation_gives_zero_torque():
    """Neutral equivalence: a silent motor pool adds nothing to the body."""
    p = muscles.MusclePairs.load()
    q = np.random.default_rng(1).uniform(-0.5, 0.5, len(p.F0))
    assert np.all(p.torques(np.zeros(len(p.F0)), q, q) == 0)


def test_co_contraction_stiffens_the_joint_without_net_torque():
    """What net-torque actuators cannot do: equal co-contraction gives zero net
    torque at rest but a restoring torque when the joint is displaced."""
    p = _pair()
    for a in (0.2, 1.0):
        act = np.full(2, a)
        assert abs(p.torques(act, np.zeros(2), np.zeros(2)).sum()) < 1e-12
        tq = p.torques(act, np.full(2, 0.5), np.zeros(2)).sum()
        assert tq < 0                                           # restoring
    k_lo = -p.torques(np.full(2, 0.2), np.full(2, 0.5), np.zeros(2)).sum()
    k_hi = -p.torques(np.full(2, 1.0), np.full(2, 0.5), np.zeros(2)).sum()
    assert k_hi > 4 * k_lo                                      # stiffness scales with activation


def test_shortening_weakens_and_lengthening_strengthens():
    p = _pair()
    a = np.array([1.0, 0.0])
    f0 = p.forces(a, np.zeros(2), np.zeros(2))[0]
    f_short = p.forces(a, np.zeros(2), np.full(2, 5.0))[0]     # +qdot: the + muscle shortens
    f_long = p.forces(a, np.zeros(2), np.full(2, -5.0))[0]
    assert f_short < f0 < f_long <= 1.4 * f0


def test_units_saturate_at_fused_tetanus():
    a = muscles.activation_from_units(np.array([0.0, 2.5, 5.0, 50.0]), np.ones(4), fused=5.0)
    assert a.tolist() == [0.0, 0.5, 1.0, 1.0]


def test_table_covers_every_leg_dof_with_an_antagonist_pair():
    p = muscles.MusclePairs.load()
    joints = set(p.joint)
    assert len(joints) == 42                                   # 6 legs x 7 hinges above the tarsal chain
    for j in joints:
        assert sorted(p.direction[p.joint == j]) == [-1.0, 1.0]
    assert np.all(p.F0 > 0) and np.all(p.r > 0) and np.all(p.L0 > 0)


def test_hill_mode_on_the_organism_is_silent_at_rest_and_flexes_with_flexor_units():
    import pytest
    if not (REPO / "data/cache/male_cns_edges.parquet").exists():
        pytest.skip("graph not fetched")
    from flyemu.organism import Organism
    org = Organism(policy="minimal", profile="m4", min_synapses=5,
                   overrides={"muscle:leg|model": 1.0})
    h, d = org.hill, org.body.sim.mj_data
    z = np.zeros(org.nm.n_actuators)
    assert np.abs(h.torque(org.nm, d, z)[h.leg_actuators]).max() == 0.0
    fl = [i for i, mm in enumerate(h.mn_muscle)
          if mm >= 0 and "tibia-pitch" in h.p.joint[mm] and h.p.direction[mm] == -1]
    assert len(fl) > 0
    h.units.r[fl] = h.units.fused[fl]                         # these units fully active
    t = h.torque(org.nm, d, z)
    tib = [i for i in h.leg_actuators if org.body.actuator_names[i].endswith("_tibia-pitch-motor")]
    assert len(tib) == 6 and np.all(t[tib] < 0)
    other = [i for i in h.leg_actuators if i not in tib]
    assert np.all(t[other] == 0)


def test_slow_units_twitch_late_and_fast_units_early():
    u = muscles.MotorUnits(np.array(["fast", "slow"]), facil_delta=0.0)
    trace = []
    for k in range(10000):                                    # 1 s at 0.1 ms, one spike at t=0
        u.step(np.array([k == 0, k == 0]), 0.1)
        trace.append(u.r.copy())
    peak_ms = np.argmax(np.array(trace), axis=0) * 0.1
    assert peak_ms[0] < 20 and peak_ms[1] > 500


def test_tetanus_saturates_and_facilitation_grows_the_second_spike():
    u = muscles.MotorUnits(np.array(["fast"]), fused_hz=100.0, facil_delta=0.0)
    for k in range(5000):                                     # 400 Hz for 0.5 s
        u.step(np.array([k % 25 == 0]), 0.1)
    assert u.activation()[0] == 1.0
    def second_increment(delta):
        v = muscles.MotorUnits(np.array(["fast"]), facil_delta=delta)
        v.step(np.array([True]), 0.1)
        for _ in range(49):
            v.step(np.array([False]), 0.1)
        before = v.u[0] * np.exp(-0.1 / v.tau_d[0])
        v.step(np.array([True]), 0.1)
        return v.u[0] - before
    assert np.isclose(second_increment(0.0), 1.0)             # neutral: equal increments
    assert second_increment(0.3) > 1.2


def test_bypassing_the_motor_path_in_hill_mode_raises():
    """s9: a probe with its own loop called Neuromuscular.step directly and
    silently ran without muscles. Under Hill mode that must fail loudly."""
    import pytest
    if not (REPO / "data/cache/male_cns_edges.parquet").exists():
        pytest.skip("graph not fetched")
    from flyemu.organism import Organism
    org = Organism(policy="minimal", profile="m4", min_synapses=5,
                   overrides={"muscle:leg|model": 1.0})
    with pytest.raises(RuntimeError, match="motor_step"):
        org.nm.step(np.array([], dtype=int), 0.1)
    org.motor_step(np.array([], dtype=int))                     # the sanctioned path works
    with pytest.raises(RuntimeError):
        org.nm.step(np.array([], dtype=int), 0.1)               # and re-arms the guard
