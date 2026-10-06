"""Session 12 B (wings at rest): the wing-muscle role table and the nerve-based
afferent assignment (F-WING-2, F-SENSE-NERVE-1)."""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from flyemu import neuromuscular, sensory  # noqa: E402


def test_wing_role_rows_replace_existing_legacy_rows():
    roles = pd.read_csv(neuromuscular.WING_ROLES_TABLE, comment="#", keep_default_na=False)
    legacy = pd.read_csv(neuromuscular.MOTOR_TABLE, comment="#")
    for r in roles.replaces:
        if r:
            assert r in set(legacy.type_regex), r
    by = roles.set_index("type_regex")
    # stroke is wing-yaw on this body (F-WING-1); the basalars extend, iii1 folds
    assert by.loc["^b1 MN$|^b2 MN$|^b3 MN$", "target"] == "c_thorax-{s}_wing-yaw"
    assert by.loc["^b1 MN$|^b2 MN$|^b3 MN$", "sign"] == 1
    assert by.loc["^iii1 MN$", "target"] == "c_thorax-{s}_wing-yaw"
    assert by.loc["^iii1 MN$", "sign"] == -1
    # indirect power muscles get no direct hinge torque
    for rx in ("^DLMn", "^DVMn"):
        assert by.loc[rx, "target"].startswith("NONE:")


def test_leg_nerve_rule():
    assert sensory.enters_by_leg_nerve("MesoLN;MetaLN;ProLN") is True
    assert sensory.enters_by_leg_nerve("DProN;MesoLN") is True
    assert sensory.enters_by_leg_nerve("ADMN") is False
    assert sensory.enters_by_leg_nerve("DMetaN") is False
    assert sensory.enters_by_leg_nerve("PrN") is False
    assert sensory.enters_by_leg_nerve("") is None


def test_the_wing_nerve_campaniforms_that_drove_the_wing_premotor_cells_are_not_leg_sensors():
    nerve = sensory.entry_nerves()
    for t in ("SNpp30", "SNpp31", "SNpp32", "SNpp33"):
        assert nerve[t] == "ADMN"
        assert sensory.enters_by_leg_nerve(nerve[t]) is False


def test_nerve_switch_moves_wing_nerve_campaniforms_from_leg_load_to_wing_strain():
    from flyemu.organism import Organism
    org = Organism(policy="minimal", seed=0, overrides={"sense:mechano|assign_by_nerve": 1.0})
    n = org.conn.neurons.reset_index(drop=True)
    snpp = org.conn.index_of(n.bodyId[n.type.isin(["SNpp30", "SNpp31", "SNpp32", "SNpp33"])].to_numpy())
    snpp = snpp[snpp >= 0]
    assert len(snpp) > 0
    assert not np.isin(snpp, org.aff.rows).any()
    assert np.isin(snpp, org.extra.channels["wing_cs"].rows).all()
    legacy = Organism(policy="minimal", seed=0)
    assert np.isin(snpp, legacy.aff.rows).any()       # the legacy rule drove them as leg load


def test_wing_stiffness_switch_sets_the_bergou_value_on_every_wing_hinge():
    import mujoco as mj
    from flyemu import passive
    from flyemu.body import Body
    from flyemu.registry import Registry
    assert abs(passive.WING_STIFFNESS_BERGOU - 5.214) < 1e-3     # 91 pN*m/deg in uN*mm/rad
    for src, k in ((0.0, 1.0), (1.0, passive.WING_STIFFNESS_BERGOU)):
        reg = Registry("minimal")
        reg.overrides["joint:wing|stiffness_source"] = src
        b = Body(vision=False)
        passive.register_wings(reg, b)
        m = b.sim.mj_model
        wing = [j for j in range(m.njnt) if "_wing-" in (mj.mj_id2name(m, mj.mjtObj.mjOBJ_JOINT, j) or "")]
        assert len(wing) == 6 and np.allclose(m.jnt_stiffness[wing], k)


def test_neck_mirror_switch_gives_mirror_image_neurons_opposite_yaw_and_roll_signs():
    from flyemu.organism import Organism
    import mujoco as mj
    signs = {}
    for k in (0.0, 1.0):
        org = Organism(policy="minimal", profile="m9t", min_synapses=5, seed=12,
                       overrides={"motor_map:neck|mirror_sides": k})
        m, nm = org.body.sim.mj_model, org.nm
        names = [mj.mj_id2name(m, mj.mjtObj.mjOBJ_ACTUATOR, i) or "" for i in range(m.nu)]
        motor = [x.split("/")[-1] for x in names if x.endswith("-motor")]
        inst = org.conn.neurons.instance.fillna("").to_numpy()[nm.mn_index]
        side = np.array([s[-1] if s[-2:] in ("_L", "_R") else "" for s in inst])
        act = np.array(motor)[nm.actuator_index]
        signs[k] = {a: {sd: nm.drive_sign[(act == a) & (side == sd)] for sd in "LR"}
                    for a in ("c_thorax-c_head-yaw-motor", "c_thorax-c_head-roll-motor", "c_thorax-c_head-pitch-motor")}
    for a, by in signs[0.0].items():
        assert (by["L"] > 0).all() and (by["R"] > 0).all()
    for a, by in signs[1.0].items():
        assert len(by["L"]) and len(by["R"])
        assert (by["L"] > 0).all()
        assert (by["R"] < 0).all() if "pitch" not in a else (by["R"] > 0).all()


def _wing_contacts(on_abdomen: bool):
    import mujoco as mj
    from flyemu import flight, passive
    from flyemu.body import Body
    from flyemu.deadfly import place_standing
    b = Body(vision=False)
    passive.fold_wings(b)
    if on_abdomen:
        passive.rest_wings_on_abdomen(b)
    flight.apply_wing_ranges(b)
    b.reset()
    place_standing(b)
    m, d = b.sim.mj_model, b.sim.mj_data
    mj.mj_forward(m, d)
    out = []
    for i in range(d.ncon):
        c = d.contact[i]
        names = (m.geom(c.geom1).name, m.geom(c.geom2).name)
        if any("_wing" in n for n in names):
            out.append((names, float(c.dist)))
    q = {m.joint(j).name.split("/")[-1]: float(d.qpos[m.jnt_qposadr[j]]) for j in range(m.njnt)
         if "_wing-" in m.joint(j).name}
    k = {m.joint(j).name.split("/")[-1]: float(m.qpos_spring[m.jnt_qposadr[j]]) for j in range(m.njnt)
         if "_wing-" in m.joint(j).name}
    return out, q, k


def test_folded_wings_rest_on_the_abdomen_not_inside_it():
    """F-WING-5: flybody's folded pose puts the wings inside abdominal segments 1-4;
    joint:wing|folded_pose 1 lifts them onto it, inside the wing ranges, spring there too."""
    before, q0, _ = _wing_contacts(False)
    assert any("abdomen" in n[0] + n[1] and dist < -40e-3 for n, dist in before)
    after, q1, k1 = _wing_contacts(True)
    assert after == []
    for n, v in q1.items():
        assert k1[n] == v                      # spring reference at the start pose
        ax = n.rsplit("-", 1)[1]
        lo, hi = np.radians(__import__("flyemu.flight", fromlist=["x"]).WING_RANGE_DEG[ax])
        assert lo <= v <= hi
    assert q1["c_thorax-l_wing-yaw"] > q1["c_thorax-r_wing-yaw"] > 0   # left on top, both lifted
