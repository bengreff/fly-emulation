"""Session 12 B: motor_unit:nonleg|torque_source 1 replaces the shared torque per
spike of non-leg motor neurons with the per-group values of
data/params/nonleg_motor_forces.csv, and leaves leg motor neurons alone."""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from flyemu import neuromuscular as N  # noqa: E402
from flyemu.registry import Registry  # noqa: E402

ACTS = ["fly/c_thorax-c_head-yaw-motor", "fly/c_head-c_rostrum-pitch-motor", "fly/c_head-l_antenna-pitch-motor",
        "fly/c_abdomen2-c_abdomen3-pitch-motor", "fly/c_thorax-l_wing-yaw-motor", "fly/c_thorax-r_haltere-pitch-motor",
        "fly/lf_coxa-lf_trochanterfemur-pitch-motor", "fly/c_haustellum-r_labrum-pitch-motor"]


def _run(v: int):
    reg = Registry("minimal")
    reg.overrides["motor_unit:nonleg|torque_source"] = float(v)
    fps = np.full(len(ACTS), 10.0, np.float32); fps[6] = 0.5     # a leg unit from motor_forces.csv
    tau = np.full(len(ACTS), 30.0, np.float32)
    N._nonleg_forces(reg, ACTS, fps, tau)
    return reg, fps, tau


def test_switch_off_keeps_the_shared_value():
    _, fps, tau = _run(0)
    assert np.allclose(fps[:6], 10.0) and fps[6] == np.float32(0.5) and np.allclose(tau, 30.0)


def test_switch_on_sets_every_non_leg_group_from_the_table_and_no_leg():
    t = pd.read_csv(N.NONLEG_TABLE, comment="#", keep_default_na=False)
    reg, fps, tau = _run(1)
    assert fps[6] == np.float32(0.5) and tau[6] == np.float32(30.0)      # leg untouched
    names = pd.Series([a.split("/")[-1] for a in ACTS])
    for i, n in enumerate(names):
        if i == 6:
            continue
        rows = t[[bool(pd.Series([n]).str.contains(r, regex=True)[0]) for r in t.actuator_regex]]
        assert len(rows) == 1, (n, rows.group.tolist())                  # exactly one group per actuator
        assert fps[i] == np.float32(rows.torque_uNmm.iloc[0])
        assert float(rows.low.iloc[0]) <= fps[i] <= float(rows.high.iloc[0])
    assert set(t.basis) <= {"measured", "derived", "inferred", "guessed"}
    assert (t.source.str.len() > 0).all() and (t.derivation.str.len() > 0).all()
    keys = {k.split("|")[0] for k in reg._reqs}
    for g in ("head", "proboscis_rostrum", "antenna", "abdomen3", "wing", "haltere", "proboscis_labrum"):
        assert f"motor_unit:nonleg_{g}" in keys, g


def test_every_non_leg_actuator_of_the_body_has_exactly_one_row():
    t = pd.read_csv(N.NONLEG_TABLE, comment="#", keep_default_na=False)
    geom = pd.read_csv(Path(N.NONLEG_TABLE).parents[1] / "derived" / "nonleg_joint_geometry_flybody.csv", comment="#")
    joints = [f"{p}-{c}" for c, p in zip(geom.child, geom.parent) if not c.startswith("lf_")]
    for j in joints:
        n = sum(bool(pd.Series([j + "-yaw-motor"]).str.contains(r, regex=True)[0]) for r in t.actuator_regex)
        assert n == 1, (j, n)
