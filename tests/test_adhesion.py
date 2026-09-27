"""B7 adhesion gate (src/flyemu/adhesion.py)."""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "src"))

from flyemu import adhesion  # noqa: E402


def _forces(per_leg):
    f = np.zeros((30, 3))
    for leg, v in per_leg.items():
        f[leg * 5 + 4] = v                      # distal tarsus
    return f


def test_no_contact_no_grip_and_shear_peels():
    g = adhesion.gate(_forces({0: (0, 0, 2.0), 1: (3.0, 0, 2.0), 2: (0, 0, 0.0),
                               3: (0.5, 0.5, 2.0)}))
    assert g.tolist() == [1, 0, 0, 1, 0, 0]


def test_legacy_organism_grip_is_untouched_by_default():
    import pytest
    if not (REPO / "data/cache/male_cns_edges.parquet").exists():
        pytest.skip("graph not fetched")
    from flyemu.organism import Organism
    org = Organism(policy="minimal", profile="m4", min_synapses=5)
    assert org.adhesion_gate is False
    org2 = Organism(policy="minimal", profile="m4", min_synapses=5,
                    overrides={"adhesion:leg|detachment": 1.0})
    assert org2.adhesion_gate is True
    org2.nm.grip[:] = 1.0
    obs = org2.body.observe()
    org2.sense(0, obs)
    org2.motor_step(np.array([], dtype=int))                # runs with the gate
