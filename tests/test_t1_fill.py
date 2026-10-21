"""s20 (fly2, T1F): inferred T1 fill (connectome.t1_fill, connectome:T1|fill_from_other_animals).

A five-cell graph: A (type IN_A) and U (untyped) drive B (type IN_B, soma T1, left) and C (type IN_B, soma T2,
left); A also drives D (type IN_B, soma T1, right). A patched table holds one factor for (IN_A, IN_B, L).
Claims: switch 0 changes nothing; switch 1 scales only A -> B (the T1 left-side cell of the table's pair),
keeps every edge (none added or removed, the sub-threshold edge stays out) and leaves signs alone.
Structural checks, not validation.
"""
from __future__ import annotations

import gzip
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "src"))

from flyemu import connectome  # noqa: E402
from flyemu.registry import Policy, Registry  # noqa: E402

KEY = "connectome:T1|fill_from_other_animals"
A, U, B, C, D = 1, 2, 3, 4, 5


@pytest.fixture
def graph(tmp_path, monkeypatch):
    t = tmp_path / "t1_fill.csv.gz"
    with gzip.open(t, "wt") as f:
        f.write("# test table\npre_type,post_type,post_side,factor\nIN_A,IN_B,L,1.5\nIN_A,IN_B,R,1.0\n")
    monkeypatch.setattr(connectome, "T1_FILL", t)
    n = pd.DataFrame(dict(bodyId=[A, U, B, C, D], type=["IN_A", None, "IN_B", "IN_B", "IN_B"],
                          instance=["a", "u", "b", "c", "d"], status="Traced", superclass="vnc_intrinsic",
                          **{"class": None},
                          somaNeuromere=["T1", "T1", "T1", "T2", "T1"], somaSide=["L", "L", "L", "L", "R"],
                          predictedNt="acetylcholine", size=1000.0))
    e = pd.DataFrame(dict(pre=[A, U, A, A, U], post=[B, B, C, D, D], weight=[10, 8, 10, 10, 3]))  # U->D below cut
    return n, e


def _build(g, on):
    r = Registry(Policy.MINIMAL)
    if on:
        r.overrides[KEY] = 1.0
    return connectome.build(r, neurons=g[0], edges=g[1], min_synapses=5), r


def _edges(c):
    pre = c.neurons.bodyId.to_numpy()[np.repeat(np.arange(c.n), np.diff(c.indptr))]
    post = c.neurons.bodyId.to_numpy()[c.indices]
    return {(int(a), int(b)): float(w) for a, b, w in zip(pre, post, c.weight_syn)}


def test_neutral_changes_nothing(graph):
    c, _ = _build(graph, False)
    assert _edges(c) == {(A, B): 10, (U, B): 8, (A, C): 10, (A, D): 10}


def test_fill_scales_only_the_t1_pair_and_adds_no_edge(graph):
    c0, _ = _build(graph, False)
    c1, _ = _build(graph, True)
    assert _edges(c1) == {(A, B): pytest.approx(15.0), (U, B): 8, (A, C): 10, (A, D): 10}
    assert set(_edges(c1)) == set(_edges(c0))
    assert np.array_equal(c1.sign, c0.sign)
