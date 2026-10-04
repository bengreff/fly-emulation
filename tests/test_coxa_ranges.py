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
