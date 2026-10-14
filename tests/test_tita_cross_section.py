"""muscle:leg|tita_specific_tension (s13 fly2, S1 fix 2): 0 keeps the guessed tibia-tarsus placeholder; > 0 sets
only the TiTa rows from the flybody tibia cross-section x specific tension, with L0 travelling with r."""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from flyemu import muscles  # noqa: E402


@pytest.mark.parametrize("midhind", [False, True])
def test_only_tita_rows_change_and_strain_per_radian_is_kept(midhind):
    a = muscles.MusclePairs.load(midhind=midhind)
    b = muscles.tita_from_cross_section(a, 28.0)
    tita = np.array([muscles.TITA_JOINT.match(j) is not None for j in a.joint])
    assert tita.sum() == 12
    for f in ("F0", "r", "L0"):
        assert np.array_equal(getattr(a, f)[~tita], getattr(b, f)[~tita])
    assert np.allclose(b.r[tita] / b.L0[tita], a.r[tita] / a.L0[tita])
    assert np.array_equal(a.q_ref, b.q_ref) and list(a.joint) == list(b.joint)


def test_values_follow_the_mesh_geometry():
    g = pd.read_csv(muscles.GEOMETRY_TABLE, comment="#")
    g = g[g.segment == "tibia"]
    b = muscles.tita_from_cross_section(muscles.MusclePairs.load(midhind=True), 9.0)
    for j, f, r in zip(b.joint, b.F0, b.r):
        m = muscles.TITA_JOINT.match(j)
        if m is None:
            continue
        gp = g[g.leg.str[1] == m.group(2)]
        assert np.isclose(f, gp.area_mid_mm2.mean() * 9.0 * 1e3)
        assert np.isclose(r, gp.width_dist_mm.mean() / 2)
    # hind TiTa: 0.0041 mm^2 x 9 mN/mm^2 ~ 37 uN at r ~ 0.053 mm, about 10x the placeholder's 0.2 uN*mm
    lh = [i for i, j in enumerate(b.joint) if j.startswith("lh_tibia-")]
    assert 9.0 < (b.F0[lh] * b.r[lh]).min() / 0.2 < 11.0


def test_out_of_range_refused():
    with pytest.raises(ValueError):
        muscles.tita_from_cross_section(muscles.MusclePairs.load(), -1.0)
