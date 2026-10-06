"""Session 12 B (sensor assignment): leg afferents by each cell's own entry nerve,
sense:mechano|assign_by_nerve = 2 (F-SENSE-NERVE-2)."""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from flyemu import sensory  # noqa: E402


def test_combined_type_names_take_their_parts_nerves():
    nerve = sensory.entry_nerves()
    assert "SNpp29,SNpp63" not in nerve                    # option 1 looked this up whole and missed
    assert sensory.type_nerves("SNpp29,SNpp63", nerve) == "ADMN"
    assert sensory.type_nerves("SApp06,SApp15", nerve) == "DMetaN"
    assert sensory.type_nerves(None, nerve) == ""


def test_option_two_puts_each_leg_sensor_on_its_own_nerve_and_side():
    from flyemu.organism import Organism
    org = Organism(policy="minimal", seed=0, overrides={"sense:mechano|assign_by_nerve": 2.0})
    own = sensory.cell_nerves()
    body = org.conn.neurons.bodyId.to_numpy()[org.aff.rows]
    nerves = [own.get(int(b), ("", "")) for b in body]
    seg = sensory.SEGMENT_OF_NERVE
    for (nv, sd), leg in zip(nerves, org.aff.leg):
        if nv in seg and sd in sensory.SIDE:
            assert leg == sensory.SIDE[sd] + seg[nv]
        # no cell entering by the wing, haltere or notum nerves is a leg sensor
        assert nv not in {"ADMN", "DMetaN", "PDMN", "PrN"}
    # the leg load channel is the leg campaniforms, two per leg
    load = org.aff.channel == "load"
    assert set(org.conn.neurons.type.to_numpy()[org.aff.rows[load]]) == {"SNpp53"}
    legs, counts = np.unique(org.aff.leg[load], return_counts=True)
    assert set(legs) == {"lf", "lm", "lh", "rf", "rm", "rh"} and counts.min() >= 2
