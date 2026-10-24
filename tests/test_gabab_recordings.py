"""N7 (s29, fly2): GABA-B shares of recorded types (`cell_type:all|gabab_from_recordings`).

A four-cell graph: a GABAergic LN inhibits a uniglomerular PN, a second LN and a Kenyon cell.
Claims: switch 0 leaves every share at the default 0 (neutral); switch 1 gives the PN its
derived 0.54 (Wilson & Laurent 2005) and the LN its 0, and leaves unrecorded types alone;
with the charge basis, the slow pool carries 0.54 of the PN's GABA charge. These are
implementation checks, not validation.
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "src"))

from flyemu import lif  # noqa: E402
from flyemu.connectome import Connectome  # noqa: E402
from flyemu.registry import Policy, Registry  # noqa: E402

DT = 0.1
KEY = "cell_type:all|gabab_from_recordings"


def _conn():
    nrn = pd.DataFrame({
        "bodyId": np.arange(10, 14),
        "type": ["lLN2F_a", "DM6_adPN", "v2LN30", "KCg-m"],
        "predictedNt": ["gaba", "acetylcholine", "gaba", "acetylcholine"], "superclass": "x", "subclass": "x",
        "class": ["ALLN", "ALPN", "ALLN", "Kenyon_Cell"]})
    # edges: 0->1, 0->2, 0->3
    return Connectome(nrn, np.array([0, 3, 3, 3, 3], np.int64), np.array([1, 2, 3], np.int32),
                      np.ones(3, np.float32), np.array([-1, 1, -1, 1], np.float32), np.ones(3, np.float32))


def _params(on: bool, basis: bool = True):
    r = Registry(Policy.MINIMAL)
    if on:
        r.overrides[KEY] = 1.0
    if basis:
        r.overrides["cell_type:all|slow_share_basis"] = 1.0
    return lif.default_params(r, _conn(), timestep_ms=DT), r


def test_switch_off_is_neutral():
    p, r = _params(on=False)
    assert np.all(np.asarray(p.gabab_fraction) == 0.0)
    inv = r.inventory().set_index(["entity", "property"])
    assert ("cell_type:all", "gabab_from_recordings") in inv.index


def test_switch_on_sets_recorded_types_only():
    p, r = _params(on=True)
    f = lif._arr(p.gabab_fraction, 4)
    assert f[1] == pytest.approx(0.54) and f[0] == 0.0 and f[2] == 0.0 and f[3] == 0.0
    inv = r.inventory()
    rows = inv[inv.property == "gabab_fraction_rec"]
    assert set(rows.entity) == {"cell_type:^.*_(adPN|lPN)$", "cell_type:^(lLN|l2LN|v2LN|vLN|il3LN).*"}


def test_charge_basis_moves_the_recorded_share_of_charge():
    p, _ = _params(on=True)
    net = lif.Network(_conn(), p, DT)
    e = 0                                     # LN -> PN edge
    tau_s = float(lif._arr(p.tau_s, 4)[1])
    fast, slow = float(net.w[e]), float(net.w_slow[e])
    q_fast, q_slow = fast * tau_s, slow * p.gabab_tau_ms
    assert q_slow / (q_fast + q_slow) == pytest.approx(0.54, rel=1e-4)
    assert net.w_slow[1] == 0.0 and net.w_slow[2] == 0.0   # LN and KC keep all-fast GABA
