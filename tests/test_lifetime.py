"""s29 (fly2): N32 homeostatic set point, N34 other-site plasticity, N31 sleep/wake synaptic scale (lifetime.py).

A six-cell graph: an afferent onto the giant fibre (LC4 -> DNp01), a GABAergic LN onto a uniglomerular PN, and two
unconnected cells for the homeostat (an alpha/beta KC, up only; APL, graded, down only). Claims: each switch at 0
builds nothing and is in the inventory (neutral); each rule moves in the stated direction and only there. Time
constants are shortened by override so the rules act within a test. These are implementation checks, not
validation.
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pytest
import yaml

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "src"))

from flyemu import lif, lifetime, stubs  # noqa: E402
from flyemu.connectome import Connectome  # noqa: E402
from flyemu.registry import Policy, Registry  # noqa: E402

DT = 0.1
QUIET = {"cell_type:all|background_noise": 0.0}


def _conn():
    nrn = pd.DataFrame({
        "bodyId": np.arange(10, 16),
        "type": ["LC4", "DNp01", "lLN2F_a", "DM6_adPN", "KCab-m", "APL"],
        "predictedNt": ["acetylcholine", "acetylcholine", "gaba", "acetylcholine", "acetylcholine", "gaba"],
        "superclass": "x", "subclass": "x",
        "class": ["LC", "DN", "ALLN", "ALPN", "Kenyon_Cell", "MBIN"]})
    # edges: 0->1 (row 0), 2->3 (row 2)
    return Connectome(nrn, np.array([0, 1, 1, 2, 2, 2, 2], np.int64), np.array([1, 3], np.int32),
                      np.ones(2, np.float32), np.array([1, 1, -1, 1, 1, -1], np.float32), np.ones(2, np.float32))


def _net(over: dict):
    r = Registry(Policy.MINIMAL)
    r.overrides.update({**QUIET, **over})
    p = lif.default_params(r, _conn(), timestep_ms=DT)
    return lif.Network(_conn(), p, DT), r


def _keys(r):
    inv = r.inventory()
    return set(inv.entity + "|" + inv.property)


def test_switches_off_are_neutral_and_inventoried():
    net, r = _net({})
    assert net.hs is None and net.site is None and net.struct is None and not net._life
    assert {"cell_type:all|homeostatic_plasticity", "synapse:other_sites|plasticity",
            "synapse:all|structural_plasticity"} <= _keys(r)


def test_built_rows_left_the_stubs_and_are_partial():
    mech = {m["id"]: m for m in yaml.safe_load((REPO / "data/model/mechanisms.yaml").read_text())}
    for mid in ("N31", "N32", "N34"):
        assert mid not in {v[0] for v in stubs.STUBS.values()}
        assert mech[mid]["status"] == "partial"


def _pending(net, cell):
    return float(net.delay[:, cell].sum())


def test_n34_gf_afferent_depresses_and_recovers():
    net, r = _net({"synapse:other_sites|plasticity": 1.0})
    st = net.site
    assert st["sites"][st["row"][st["pos"][0]]] == "gf_afferent_habituation"
    assert st["sites"][st["row"][st["pos"][1]]] == "al_ln_pn_potentiation"
    net.step(kick=(np.array([0]), 40.0))
    first = _pending(net, 1)
    assert st["y"][st["pos"][0]] == pytest.approx(0.95)
    for _ in range(30):
        net.step()
    net.step(kick=(np.array([0]), 40.0))
    assert _pending(net, 1) == pytest.approx(first * st["y"][st["pos"][0]] / 0.95, rel=1e-3)   # used y before it fell
    y = st["y"][st["pos"][0]]
    assert y < 0.95
    lifetime.site_tick(st, 10_000.0)                    # one tau (10 s) of rest
    assert st["y"][st["pos"][0]] == pytest.approx(1 - (1 - y) * np.exp(-1), rel=1e-6)
    assert "connection:gf_afferent_habituation|site_u" in _keys(r)


def test_n34_ln_to_pn_potentiates_toward_its_cap():
    net, _ = _net({"synapse:other_sites|plasticity": 1.0})
    st = net.site
    k = st["pos"][1]
    net.step(kick=(np.array([2]), 40.0))
    assert st["y"][k] == pytest.approx(1 + 1e-4 * 0.5)


def test_n32_kc_rises_only_apl_falls_only():
    over = {"cell_type:all|homeostatic_plasticity": 1.0, "cell_type:all|homeostat_tau_days": 1e-6,
            "cell_type:all|homeostat_sensor_tau_s": 0.01, "cell_type:all|homeostat_capture_ms": 200.0}

    def run(kc_after, apl_after):
        net, _ = _net(over)
        ext = np.zeros(6, np.float32)
        for s in range(5000):
            after = s >= 2000
            ext[4] = kc_after if after else 20.0
            ext[5] = apl_after if after else 4.0
            net.step(external_mv=ext)
        hs = net.hs
        return dict(zip(net.conn.neurons.type.to_numpy()[hs["idx"]], hs["h"]))

    h = run(kc_after=16.0, apl_after=6.0)               # KC too quiet, APL too active
    assert 0.0 < h["KCab-m"] <= 5.0 and -5.0 <= h["APL"] < -0.5
    h = run(kc_after=24.0, apl_after=2.0)               # KC too active, APL too quiet: neither may move
    assert h["KCab-m"] == 0.0 and h["APL"] == 0.0


def test_n31_scale_rises_awake_falls_asleep_and_scales_synapses():
    net, _ = _net({"synapse:all|structural_plasticity": 1.0, "synapse:all|structural_tau_wake_h": 1e-4,
                   "synapse:all|structural_tau_sleep_h": 1e-4})
    for _ in range(10_000):                             # 1 s awake; tau 360 ms
        net.step()
    s = net.struct["s"]
    assert s == pytest.approx(1.35 - 0.35 * np.exp(-1000 / 360), rel=2e-3)
    net.step(kick=(np.array([0]), 40.0))
    off, _ = _net({})
    off.step(kick=(np.array([0]), 40.0))
    assert _pending(net, 1) == pytest.approx(_pending(off, 1) * net.struct["s"], rel=1e-4)
    net.set_asleep(True)
    for _ in range(10_000):
        net.step()
    assert 1.0 < net.struct["s"] < 1.0 + (s - 1.0) * np.exp(-2.5)
