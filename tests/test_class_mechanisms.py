"""N3/N5 at class grain (session 10): per-circuit-class release/input scale,
tonic drive and noise (lif._class_scales; rows in data/model/parameters.csv).

Neutral equivalence: at the neutral values the network is bit-identical to one
built without the mechanism. Claim: a class value acts on that class only.
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pytest

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "src"))

needs_graph = pytest.mark.skipif(
    not (REPO / "data/cache/male_cns_edges.parquet").exists(), reason="no graph cache")


def _org(monkeypatch=None, **ov):
    from flyemu.organism import Organism
    return Organism(policy="minimal", profile="m4", min_synapses=5, overrides=ov)


@needs_graph
def test_class_mechanisms_are_bit_identical_at_neutral(monkeypatch):
    from flyemu import lif
    a = _org()
    monkeypatch.setattr(lif, "_class_scales",
                        lambda reg, conn, rel, inp, spont: (rel, inp, spont, None, None))
    b = _org()
    assert np.array_equal(a.net.w, b.net.w)
    assert np.array_equal(np.broadcast_to(a.net.spont, (a.conn.n,)),
                          np.broadcast_to(b.net.spont, (b.conn.n,)))
    assert a.net.params.noise_class_mv is None and a.net.params.tonic_class_mv is None
    for _ in range(50):          # identical dynamics under the same stimulus
        k = (np.arange(0, a.conn.n, 997), 20.0)
        assert np.array_equal(a.net.step(kick=k), b.net.step(kick=k))
    inv = a.reg.inventory()
    keys = set(inv.entity + "|" + inv.property)
    assert {"class:DN|release_scale", "class:MN_leg|input_scale", "class:KC|tonic_drive",
            "class:optic_columnar|noise"} <= keys


@needs_graph
def test_a_class_value_acts_on_that_class_only():
    from flyemu.lif import circuit_classes
    base = _org()
    on = _org(**{"class:DN|release_scale": 2.0, "class:MN_leg|input_scale": 0.5,
                 "class:KC|tonic_drive": 3.0, "class:KC|noise": 1.0})
    cls = circuit_classes(on.conn)
    pre = np.repeat(np.arange(on.conn.n), np.diff(on.conn.indptr))
    post = on.conn.indices
    dn, mn = cls[pre] == "DN", cls[post] == "MN_leg"
    nz = base.net.w != 0
    assert np.allclose(on.net.w[dn & ~mn & nz], 2.0 * base.net.w[dn & ~mn & nz], rtol=1e-6)
    assert np.allclose(on.net.w[mn & ~dn & nz], 0.5 * base.net.w[mn & ~dn & nz], rtol=1e-6)
    assert np.allclose(on.net.w[dn & mn & nz], 1.0 * base.net.w[dn & mn & nz], rtol=1e-6)
    assert np.array_equal(on.net.w[~dn & ~mn], base.net.w[~dn & ~mn])
    kc = cls == "KC"
    d = np.broadcast_to(on.net.spont, (on.conn.n,)) - np.broadcast_to(base.net.spont, (on.conn.n,))
    assert np.allclose(d[kc], 3.0) and not d[~kc].any()
    nc = on.net.params.noise_class_mv
    assert nc is not None and np.all(nc[kc] == 1.0) and not nc[~kc].any()


def test_every_circuit_class_has_four_bounded_rows():
    import pandas as pd
    from flyemu import model_data as M
    md = M.load()
    cc = set(pd.read_csv(REPO / "data/model/classes.csv", keep_default_na=False).circuit_class)
    p = md.parameters
    for prop in ("release_scale", "input_scale", "tonic_drive", "noise"):
        keys = set(p.registry_key[p.registry_key.str.endswith(f"|{prop}")
                                  & p.registry_key.str.startswith("class:")])
        assert keys == {f"class:{c}|{prop}" for c in cc}, prop
    assert M.validate(md) == []
