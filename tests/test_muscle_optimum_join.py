"""muscle:leg|optimum_join (session 11): 0 keeps every muscle's optimum at the
flybody zero pose (s9); 1 moves only the joined coxa-trochanter and femur-tibia
pitch rows to the anatomical join table."""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))


def test_optimum_join_is_neutral_at_zero_and_moves_only_joined_rows():
    from flyemu import muscles
    p0 = muscles.MusclePairs.load()
    assert np.all(p0.q_ref == 0.0)
    p1 = muscles.MusclePairs.load(optimum=True)
    o = pd.read_csv(muscles.OPTIMUM_TABLE, comment="#")
    moved = p1.q_ref != p0.q_ref
    joined = {(j, float(d)) for j, d in zip(o.joint, o.direction)}
    for j, d, mv in zip(p1.joint, p1.direction, moved):
        assert mv == ((j, float(d)) in joined and dict(zip(zip(o.joint, o.direction.astype(float)), o.q_opt_rad))[(j, float(d))] != 0.0)
    assert set(o.label[o.joint.str.contains("lf_|rf_")]) == {"derived"}
    assert set(o.label[~o.joint.str.contains("lf_|rf_")]) == {"guessed"}
    assert (o.match_err_deg <= 1.0).all()


def test_ft_flexor_scale_touches_only_femur_tibia_flexors():
    import numpy as np
    from flyemu.muscles import MusclePairs
    p = MusclePairs.load()
    ft = np.array([("_trochanterfemur-" in j) and j.endswith("_tibia-pitch") for j in p.joint])
    sel = ft & (p.direction < 0)
    assert sel.sum() == 6
    F = np.where(sel, p.F0 * 40.0, p.F0)
    assert np.allclose(F[~sel], p.F0[~sel]) and np.allclose(F[sel], 40 * p.F0[sel])
