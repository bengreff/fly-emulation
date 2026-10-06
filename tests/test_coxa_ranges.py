"""Session 12 B2: flybody's leg-specific coxa ranges behind joint:coxa|range_source,
and the rest angles refitted inside them (F-COXA-2)."""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from flyemu import passive  # noqa: E402
from flyemu.body import Body  # noqa: E402
from flyemu.registry import Registry  # noqa: E402


def _coxa_ranges(b) -> dict:
    m = b.sim.mj_model
    pre = f"{b.fly.name}/"
    return {(m.joint(j).name or "").removeprefix(pre): tuple(m.jnt_range[j])
            for j in range(m.njnt) if "c_thorax-" in (m.joint(j).name or "") and "_coxa-" in (m.joint(j).name or "")}


def test_switch_off_keeps_the_legacy_envelopes():
    b = Body(vision=False)
    before = _coxa_ranges(b)
    assert passive.register_coxa(Registry("minimal"), b) == []
    assert _coxa_ranges(b) == before
    # the legacy envelopes are symmetric about q0 = 0: pitch +-45, roll +-25, yaw +-30 deg
    assert np.allclose(np.degrees(before["c_thorax-lm_coxa-pitch"]), (-45, 45))


def test_switch_on_sets_the_eighteen_table_ranges():
    t = pd.read_csv(passive.COXA_TABLE, comment="#").set_index("joint")
    assert len(t) == 18
    reg = Registry("minimal")
    reg.overrides["joint:coxa|range_source"] = 1.0
    b = Body(vision=False)
    assert len(passive.register_coxa(reg, b)) == 18
    got = _coxa_ranges(b)
    for j, r in t.iterrows():
        assert np.allclose(got[j], (r.lo_rad, r.hi_rad)), j
    # leg-specific: the mid coxa pitch range is narrower than the front's
    assert got["c_thorax-lm_coxa-pitch"][1] < got["c_thorax-lf_coxa-pitch"][1]


def test_refitted_rest_angles_lie_inside_the_flybody_ranges():
    b = Body(vision=False)
    passive.apply_coupled(b)
    passive.apply_coxa_ranges(b)
    passive.set_rest_angles(b, passive.REST_TABLE)          # s9 fit: front coxa pitch -45 deg is outside
    assert {"c_thorax-lf_coxa-pitch", "c_thorax-rf_coxa-pitch"} <= set(passive.springs_outside_range(b))
    passive.set_rest_angles(b, passive.REST_TABLE_COXA)
    assert not [j for j in passive.springs_outside_range(b) if "_coxa-" in j]


def test_registry_neutral_is_the_legacy_body():
    reg = Registry("minimal")
    assert float(reg.require("joint:coxa", "range_source", units="enum", model_use="", subsystem="body_mechanics",
                             minimal=0, minimal_note="")) == 0


def _ctr_ranges(b) -> dict:
    m = b.sim.mj_model
    pre = f"{b.fly.name}/"
    return {(m.joint(j).name or "").removeprefix(pre): tuple(np.degrees(m.jnt_range[j]))
            for j in range(m.njnt) if "_coxa-" in (m.joint(j).name or "") and "trochanterfemur-pitch" in (m.joint(j).name or "")}


def test_ctr_switch_off_keeps_the_legacy_envelope():
    b = Body(vision=False)
    assert passive.register_ctr(Registry("minimal"), b) == []
    assert all(np.allclose(r, (-100, 100)) for r in _ctr_ranges(b).values())


def test_ctr_lower_bound_is_the_fold_and_the_s9_front_mid_references_lie_past_it():
    """F-COXA-2: below the lower bound the femur would pass through the coxa (the
    coxa-femur flexion angle rises again), and the s9 front/mid CTr spring
    references (-60..-71 deg) lie there."""
    import mujoco as mj
    reg = Registry("minimal")
    reg.overrides["joint:ctr|range_source"] = 1.0
    b = Body(vision=False)
    assert len(passive.register_ctr(reg, b)) == 6
    m = b.sim.mj_model
    d = mj.MjData(m)
    jid = lambda s: mj.mj_name2id(m, mj.mjtObj.mjOBJ_JOINT, f"{b.fly.name}/{s}")  # noqa: E731
    s9 = pd.read_csv(passive.REST_TABLE, comment="#").set_index("joint")
    for leg in ("lf", "lm", "lh", "rf", "rm", "rh"):
        ctr, thc, fti = (jid(f"{leg}_coxa-{leg}_trochanterfemur-pitch"), jid(f"c_thorax-{leg}_coxa-pitch"),
                         jid(f"{leg}_trochanterfemur-{leg}_tibia-pitch"))
        lo, hi = m.jnt_range[ctr]

        def flex(q):
            d.qpos[:] = m.qpos0
            d.qpos[m.jnt_qposadr[ctr]] = q
            mj.mj_kinematics(m, d)
            u, v = d.xanchor[thc] - d.xanchor[ctr], d.xanchor[fti] - d.xanchor[ctr]
            return np.degrees(np.arccos(u @ v / np.linalg.norm(u) / np.linalg.norm(v)))
        step = np.radians(5.0)
        assert flex(lo - step) > flex(lo) < flex(lo + step), leg
        assert flex(hi) > 120.0, leg                              # well extended at the upper bound
        ref = s9.loc[f"{leg}_coxa-{leg}_trochanterfemur-pitch", "spring_ref_rad"]
        assert (ref < lo) == (leg[1] in "fm"), leg


def test_ctr_refitted_rest_angles_lie_inside_the_ctr_ranges():
    reg = Registry("minimal")
    reg.overrides["joint:ctr|range_source"] = 1.0
    reg.overrides["joint:leg|spring_reference"] = 3.0
    b = Body(vision=False)
    passive.apply_coupled(b)
    passive.register_ctr(reg, b)
    assert passive.register_rest(reg, b) == 30
    assert not [j for j in passive.springs_outside_range(b) if "trochanterfemur-pitch" in j]
