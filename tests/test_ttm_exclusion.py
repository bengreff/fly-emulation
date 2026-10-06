"""Session 12 B: with the B15 TTM hook on, jump:ttm|exclude_from_hill = 1 takes
TTMn out of the mid-leg CTr extensor Hill pool, where it was counted a second
time (scripts/probes/ttm_double_count.py; F-MUSCLE-MH-1)."""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))


def _pools(v: int):
    from flyemu.organism import Organism
    from flyemu.profiles import WORKING_PROFILE
    org = Organism(policy="minimal", profile=WORKING_PROFILE, seed=0,
                   overrides={"jump:ttm|exclude_from_hill": float(v)})
    assert org.ttm is not None and org.hill is not None
    tt = np.flatnonzero(org.conn.neurons.type.fillna("").to_numpy()[org.nm.mn_index] == "TTMn")
    return tt, org.hill.mn_muscle[tt].copy(), org.hill.W.copy(), org.hill.w[tt].copy()


def test_ttmn_leaves_the_hill_pool_only_when_switched():
    tt0, joined0, W0, w = _pools(0)              # one whole-CNS build at a time
    tt1, joined1, W1, _ = _pools(1)
    assert len(tt0) == 2 and np.array_equal(tt0, tt1)
    assert (joined0 >= 0).all()                  # the legacy double count
    assert (joined1 < 0).all()
    assert np.allclose(W1[joined0], W0[joined0] - w)
    other = np.setdiff1d(np.arange(len(W0)), joined0)
    assert np.array_equal(W0[other], W1[other])
