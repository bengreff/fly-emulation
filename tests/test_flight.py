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
