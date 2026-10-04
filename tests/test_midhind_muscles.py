"""Session 12 B (mid/hind leg muscles): muscle:leg|midhind_source = 1 replaces the
copied mid/hind muscles with front-leg members scaled by measured segment size
(scripts/build_midhind_muscles.py; F-MUSCLE-MH-1)."""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from flyemu import muscles  # noqa: E402


def test_switch_replaces_only_mid_and_hind_rows():
    a, b = muscles.MusclePairs.load(), muscles.MusclePairs.load(midhind=True)
    assert list(a.joint) == list(b.joint) and list(a.direction) == list(b.direction)
    front = np.array([not pd.Series([j]).str.contains(muscles.MIDHIND_LEG).item() for j in a.joint])
    fa = {(j, d): f for j, d, f in zip(a.joint, a.direction, a.F0)}
    fb = {(j, d): f for j, d, f in zip(b.joint, b.direction, b.F0)}
    for j, d in zip(a.joint[front], a.direction[front]):
        assert fa[(j, d)] == fb[(j, d)]
    # the femur-tibia pair of the mid leg follows the measured femur cross-section
    sc = pd.read_csv(muscles.TABLE.parent / "leg_muscle_midhind_scale.csv", comment="#")
    k = sc[(sc.position == "m") & (sc.muscle == "LFTibia_extensor_93932")].F0_factor.item()
    j = "lm_trochanterfemur-lm_tibia-pitch"
    assert np.isclose(fb[(j, 1.0)], fa[(j, 1.0)] * k, rtol=1e-3)


def test_coxa_muscles_scale_with_the_coxal_opening():
    a, b = muscles.CoxaMuscles.load(), muscles.CoxaMuscles.load(midhind=True)
    assert list(zip(a.leg, a.name)) == list(zip(b.leg, b.name))
    sc = pd.read_csv(muscles.TABLE.parent / "leg_muscle_midhind_scale.csv", comment="#")
    for leg, name, fa, fb, ra, rb in zip(a.leg, a.name, a.F0, b.F0, a.R, b.R):
        if leg[1] == "f":
            assert fa == fb and np.allclose(ra, rb)
            continue
        row = sc[(sc.position == leg[1]) & (sc.muscle == "LFC_" + name)].iloc[0]
        assert np.isclose(fb, fa * row.F0_factor, rtol=1e-3)
        assert np.allclose(rb, ra * row.r_factor, rtol=1e-3, atol=2e-6)


def test_every_derived_row_is_labelled():
    t = pd.read_csv(muscles.MIDHIND_TABLE, comment="#")
    assert set(t.label) == {"inferred", "guessed"}
    assert set(t[t.label == "guessed"].joint.str.extract(r"(tibia-[lr][mh]_tarsus1)")[0].notna()) == {True}
