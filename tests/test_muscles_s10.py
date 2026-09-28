"""Session 10 body muscles: anatomical coxa muscles with moment-arm vectors
(muscle:leg|coxa_model) and motor-unit fatigue (motor_unit:leg|fatigue_*)."""
from __future__ import annotations

import sys
import warnings
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "src"))

from flyemu import muscles  # noqa: E402

HAVE_GRAPH = (REPO / "data/cache/male_cns_edges.parquet").exists()
LEGS = ("lf", "lm", "lh", "rf", "rm", "rh")


def _s9_units_step(u, hit, dt_ms):
    """Session 9 MotorUnits.step, verbatim: the neutral reference."""
    u.f = 1.0 + (u.f - 1.0) * np.exp(-dt_ms / u.facil_tau)
    u.u *= np.exp(-dt_ms / u.tau_d)
    u.u[hit] += u.f[hit]
    u.f[hit] += u.facil_delta
    u.r += (u.u - u.r) * (1.0 - np.exp(-dt_ms / u.tau_r))


def _train(n_units, n_steps, rate_hz, seed=0, dt=0.1):
    rng = np.random.default_rng(seed)
    return rng.random((n_steps, n_units)) < rate_hz * dt / 1000.0


# --- fatigue ------------------------------------------------------------------

def test_fatigue_neutral_is_bit_identical_to_session9():
    cls = np.array(["fast", "intermediate", "slow", "fast"])
    new = muscles.MotorUnits(cls, facil_delta=0.1, fatigue_fraction=0.0, fatigue_tau_ms=37.0)
    ref = muscles.MotorUnits(cls, facil_delta=0.1)
    for hit in _train(4, 4000, 150.0):
        new.step(hit, 0.1)
        _s9_units_step(ref, hit, 0.1)
        assert np.array_equal(new.r, ref.r) and np.array_equal(new.u, ref.u)


def test_fatigue_lowers_force_in_a_sustained_train_and_recovers():
    cls = np.array(["fast", "slow"])
    kw = dict(fused_hz=1e6, facil_delta=0.0)                   # no saturation clip: read raw state
    fat = muscles.MotorUnits(cls, fatigue_fraction=0.1, fatigue_tau_ms=500.0, **kw)
    fresh = muscles.MotorUnits(cls, **kw)
    hit = lambda k: np.array([k % 100 == 0] * 2)             # noqa: E731  100 Hz
    for k in range(10000):                                     # 1 s at 100 Hz
        fat.step(hit(k), 0.1)
        fresh.step(hit(k), 0.1)
    assert fat.r[0] < 0.6 * fresh.r[0]                         # fast unit fatigued
    assert fat.r[1] == fresh.r[1]                              # slow unit is fatigue-resistant
    x_end = fat.x[0]
    for _ in range(20000):                                     # 2 s rest = 4 tau
        fat.step(np.array([False, False]), 0.1)
    assert fat.x[0] > 0.97 and x_end < 0.5                     # resource recovers
    # a single-spike force after recovery is back near the rested one
    a, b = fat, muscles.MotorUnits(cls, fatigue_fraction=0.1, fatigue_tau_ms=500.0, **kw)
    a.u[:] = a.r[:] = 0.0
    a.step(np.array([True, True]), 0.1)
    b.step(np.array([True, True]), 0.1)
    assert a.u[0] > 0.97 * b.u[0]


def test_fatigue_saturates_cumulative_impulse_within_tens_of_spikes():
    """Azevedo 2020 (read s10): fast/intermediate force-per-spike curves
    saturate at ~10 spikes. With depletion d per spike the cumulative impulse
    of n spikes is (1 - (1 - d)^n) / d; the prior centre d = 0.1 reaches 65%
    of its limit by 10 spikes."""
    u = muscles.MotorUnits(np.array(["fast"]), fused_hz=1e6, fatigue_fraction=0.1,
                           fatigue_tau_ms=1e9)
    total = 0.0
    for k in range(10):
        before = u.u[0]
        u.step(np.array([True]), 0.1)
        total += u.u[0] - before * np.exp(-0.1 / u.tau_d[0])
    assert np.isclose(total, (1 - 0.9 ** 10) / 0.1)


# --- coxa muscles: table ------------------------------------------------------

def test_coxa_table_covers_every_hinge_in_both_directions():
    c = muscles.CoxaMuscles.load()
    assert len(c.F0) == 42                                     # 7 FlyMimic coxa muscles x 6 legs
    for leg in LEGS:
        sel = c.leg == leg
        for k in range(3):
            r = c.R[sel, k]
            assert r.max() > 0.005 and r.min() < -0.005, (leg, k)   # >= 5 um each way
    t = pd.read_csv(muscles.COXA_TABLE, comment="#")
    assert set(t[t.leg == "lf"].label) == {"derived"} and set(t[t.leg != "lf"].label) == {"guessed"}


def test_coxa_torque_is_the_projected_vector_and_length_is_consistent():
    """Virtual work: torque_j = r_j F and dL/dq_j = -r_j / L0 (normalised)."""
    c = muscles.CoxaMuscles.load()
    rng = np.random.default_rng(3)
    q = rng.uniform(-0.2, 0.2, (len(c.F0), 3))
    a = rng.uniform(0, 1, len(c.F0))
    F = c.forces(a, q, np.zeros_like(q))
    assert np.allclose(c.torques(a, q, np.zeros_like(q)), c.R * F[:, None])
    eps = 1e-6
    for j in range(3):
        dq = np.zeros_like(q)
        dq[:, j] = eps
        assert np.allclose((c.lengths(q + dq) - c.lengths(q)) / eps, -c.R[:, j] / c.L0, rtol=1e-5)
    assert np.all(c.torques(np.zeros(len(c.F0)), q, q) == 0)   # silent pool: no torque


def test_coxa_muscle_roles_at_the_coxa_tip():
    """Literature roles (Cheong et al. PMC13384506; Azevedo 2024 Table A1):
    promotors and anterior rotator swing the coxa forward, remotor and posterior
    rotator backward, adductor inward. Checked on the rotation about each
    muscle's torque axis, recovered from its flybody arms, at the coxa tip
    (the foot depends on the downstream pose)."""
    from flyemu.body import Body
    import mujoco as mj
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        body = Body(model="flybody", vision=False)
    m = body.sim.mj_model
    d = mj.MjData(m)
    mj.mj_forward(m, d)
    pre = f"{body.fly.name}/"
    c = muscles.CoxaMuscles.load()
    role = pd.read_csv(muscles.COXA_TABLE, comment="#").groupby(["leg", "muscle"]).role.first()
    for i in range(len(c.F0)):
        leg = c.leg[i]
        B = np.array([d.xaxis[mj.mj_name2id(m, mj.mjtObj.mjOBJ_JOINT, pre + j)] for j in c.joint[i]])
        M = np.linalg.solve(B, c.R[i])                         # torque axis (world = thorax at spawn)
        b = lambda n: d.xpos[mj.mj_name2id(m, mj.mjtObj.mjOBJ_BODY, pre + n)]  # noqa: E731
        v = np.cross(M, b(f"{leg}_trochanterfemur") - b(f"{leg}_coxa"))
        lat = v[1] * (1 if leg[0] == "l" else -1)
        want = role[(leg, c.name[i])]
        ok = {"protraction": v[0] > 0, "retraction": v[0] < 0, "adduction": lat < 0}[want]
        assert ok, (leg, c.name[i], want, v)


# --- coxa muscles: organism ---------------------------------------------------

@pytest.fixture(scope="module")
def orgs():
    if not HAVE_GRAPH:
        pytest.skip("graph not fetched")
    from flyemu.organism import Organism
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        base = Organism(policy="minimal", profile="m4", min_synapses=5,
                        overrides={"muscle:leg|model": 1.0})
        neutral = Organism(policy="minimal", profile="m4", min_synapses=5,
                           overrides={"muscle:leg|model": 1.0, "muscle:leg|coxa_model": 0.0,
                                      "motor_unit:leg|fatigue_fraction": 0.0})
        coxa = Organism(policy="minimal", profile="m4", min_synapses=5,
                        overrides={"muscle:leg|model": 1.0, "muscle:leg|coxa_model": 1.0})
    return base, neutral, coxa


def test_neutral_switches_give_identical_hill_torques_over_a_spike_train(orgs):
    base, neutral, _ = orgs
    rng = np.random.default_rng(0)
    for _ in range(300):
        sp = base.nm.mn_index[rng.random(len(base.nm.mn_index)) < 0.03]
        t0 = base.motor_step(sp)
        t1 = neutral.motor_step(sp)
        assert np.array_equal(t0, t1)
    assert np.array_equal(base.body.sim.mj_data.qpos, neutral.body.sim.mj_data.qpos)


def test_coxa_mns_join_anatomical_muscles_by_type(orgs):
    _, _, org = orgs
    h = org.hill
    types = org.conn.neurons.type.fillna("").to_numpy()[org.nm.mn_index]
    coxa_types = set(h.coxa.mn_type)
    k = np.isin(types, list(coxa_types))
    assert k.sum() == 62 and np.all(h.mn_group[k] >= 0) and np.all(h.mn_muscle[k] == -1)
    assert not any(muscles.is_coxa_joint(j) for j in h.p.joint)      # pairs replaced on the coxa
    has = h.coxa_group >= 0
    assert has.sum() == 30                                     # promotor MNs exist for front legs only
    assert set(h.coxa.name[~has]) == {"tergopleural_promotor_a", "tergopleural_promotor_b",
                                      "pleural_promotor"}
    assert set(h.coxa.leg[~has]) == {"lm", "lh", "rm", "rh"}
    for leg in LEGS:                                           # driven muscles on every hinge, both ways
        R = h.coxa.R[(h.coxa.leg == leg) & has]
        assert np.all(R.max(0) > 0.005) and np.all(R.min(0) < -0.005)


def test_coxa_model_silent_at_rest_and_stable_under_random_drive(orgs):
    _, _, org = orgs
    h, d = org.hill, org.body.sim.mj_data
    z = np.zeros(org.nm.n_actuators)
    assert np.abs(h.torque(org.nm, d, z)[h.leg_actuators]).max() == 0.0
    rng = np.random.default_rng(1)
    for _ in range(500):
        sp = org.nm.mn_index[rng.random(len(org.nm.mn_index)) < 0.03]
        tq = org.motor_step(sp)
    assert np.all(np.isfinite(tq)) and np.all(np.isfinite(d.qpos))
    assert not any(w.number for w in d.warning)
    # the coxa muscles deliver torque on all three hinges of every leg
    act = [i for i, a in enumerate(org.body.actuator_names) if "c_thorax-" in a and "_coxa-" in a]
    assert len(act) == 18 and np.count_nonzero(tq[act]) == 18
