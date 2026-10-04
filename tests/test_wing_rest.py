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
