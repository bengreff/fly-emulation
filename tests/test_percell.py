"""Per-cell rules within cell type (session 11, src/flyemu/percell.py).

Neutral equivalence: at exponents 0 the network is bit-identical to one built
without the rules. Claims: each type keeps its geometric-mean input gain; a larger
cell of a type gets a smaller gain; motor neurons follow their own exponent.
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "src"))

needs_graph = pytest.mark.skipif(
    not (REPO / "data/cache/male_cns_edges.parquet").exists(), reason="no graph cache")


def _org(**ov):
    from flyemu.organism import Organism
    return Organism(policy="minimal", profile="m4", min_synapses=5, overrides=ov)


def test_the_ratio_keeps_each_types_geometric_mean_and_ignores_the_undefined():
    from flyemu.percell import within_type_ratio
    v = np.array([1.0, 4.0, 2.0, 5.0, np.nan, 3.0, 0.0])
    t = pd.Series(["a", "a", "b", "", "c", "d", "d"])
    r = within_type_ratio(v, t)
    assert np.allclose(r[:2], [2.0, 0.5])                 # G_a = 2
    assert r[2] == 1.0 and r[3] == 1.0 and r[4] == 1.0    # singleton, untyped, no size
    assert r[5] == 1.0 and r[6] == 1.0                    # zero size -> only one valid cell
    assert np.isclose(np.exp(np.log(r[:2]).mean()), 1.0)


@needs_graph
def test_per_cell_rules_are_bit_identical_at_neutral(monkeypatch):
    from flyemu import percell
    a = _org()
    monkeypatch.setattr(percell, "input_gain_factors", lambda reg, conn: None)
    b = _org()
    assert np.array_equal(a.net.w, b.net.w)
    assert np.array_equal(a.net.input_gain, b.net.input_gain)
    inv = a.reg.inventory()
    keys = set(inv.entity + "|" + inv.property)
    assert {"cell_type:all|within_type_size_exponent", "cell_type:motor|within_type_size_exponent",
            "cell_type:all|within_type_input_exponent"} <= keys


@needs_graph
def test_size_rule_lowers_the_gain_of_larger_cells_within_type_only():
    base = _org()
    on = _org(**{"cell_type:all|within_type_size_exponent": 1.0,
                 "cell_type:motor|within_type_size_exponent": 1.5})
    n = on.conn.neurons.reset_index(drop=True)
    from flyemu.percell import incomplete
    g = on.net.input_gain / base.net.input_gain
    lg = pd.Series(np.log(g))
    bad = incomplete(n["post"].to_numpy(float), n.type)
    assert np.all(g[bad] == 1.0)          # reconstruction-incomplete cells are left alone
    # each type keeps its geometric-mean gain over its complete cells (float32 precision)
    ok = ~bad
    k = pd.Series(ok).groupby(n.type.fillna("").to_numpy()).transform("sum").to_numpy()
    typed = n.type.notna() & pd.Series(k >= 2) & pd.Series(ok)
    gm = lg[typed.to_numpy()].groupby(n.type[typed].to_numpy()).mean()
    assert np.abs(gm).max() < 1e-4
    # larger cell -> smaller gain, with the declared exponent
    t = n.type[typed].value_counts().index[0]
    m = (n.type == t).to_numpy() & ok
    s = n["size"].to_numpy(float)[m]
    slope = np.polyfit(np.log(s), lg[m], 1)[0]
    motor = n.superclass.isin(["vnc_motor", "cb_motor"]).to_numpy()
    assert np.isclose(slope, -1.5 if motor[m][0] else -1.0, atol=1e-3)
    mt = n.type[typed & n.superclass.eq("vnc_motor")].value_counts().index[0]
    mm = (n.type == mt).to_numpy() & ok
    assert np.isclose(np.polyfit(np.log(n["size"].to_numpy(float)[mm]), lg[mm], 1)[0], -1.5, atol=1e-3)
    # untyped cells are untouched
    assert np.all(g[n.type.isna().to_numpy()] == 1.0)


@needs_graph
def test_unclear_cells_take_their_hemilineage_transmitter_only_when_switched_on():
    """s11 development rule (connectome:unclear|nt_by_development; neutral 0)."""
    from flyemu import connectome
    from flyemu.registry import Policy, Registry
    fill = pd.read_csv(REPO / "data/derived/nt_hemilineage_fill.csv")
    assert (fill[fill.rule == "hemilineage"].purity >= 0.9).all()
    assert set(fill[fill.rule == "motor class"].superclass) == {"vnc_motor"}
    out = {}
    for v in (0.0, 1.0):
        reg = Registry(Policy.MINIMAL)
        reg.overrides.update({"connectome:all|nt_source_consensus": 1.0,
                              "connectome:unclear|nt_by_development": v})
        out[v] = connectome.build(reg, min_synapses=5)
    a, b = out[0.0].neurons, out[1.0].neurons
    na, nb = a.predictedNt.fillna("unclear"), b.predictedNt.fillna("unclear")
    changed = (na != nb).to_numpy()
    assert (na[changed] == "unclear").all()
    assert set(b.bodyId[changed]) <= set(fill.bodyId)
    assert changed.sum() > 500
    m = b.bodyId.isin(fill.bodyId).to_numpy() & changed
    assert (nb[m].to_numpy() == b.bodyId[m].map(fill.set_index("bodyId").nt).to_numpy()).all()


@needs_graph
def test_s4a_switches_are_neutral_by_default_and_touch_leg_mns_only():
    """S4a arms R (between-type leg-MN size law) and G (glutamate onto leg MNs +1), DECISIONS 13 Oct 23:31."""
    from flyemu.percell import incomplete, leg_motor_mask
    base = _org()
    inv = base.reg.inventory()
    keys = set(inv.entity + "|" + inv.property)
    assert {"cell_type:leg_motor|between_type_size_exponent",
            "cell_type:leg_motor|glutamate_receptor_sign"} <= keys
    leg = leg_motor_mask(base.conn)
    assert 300 < leg.sum() < 450
    # R: leg-MN types follow (median volume / type geometric-mean volume)^1.49; others untouched
    r = _org(**{"cell_type:leg_motor|between_type_size_exponent": 1.49})
    g = r.net.input_gain / base.net.input_gain
    assert np.all(g[~leg] == 1.0) and np.array_equal(r.net.w != 0, base.net.w != 0)
    n = base.conn.neurons.reset_index(drop=True)
    ok = leg & ~incomplete(n["post"].to_numpy(float), n.type)   # incomplete cells: not in the reference
    lt = pd.DataFrame({"t": n.type[ok].to_numpy(), "lg": np.log(g[ok]),
                       "lv": np.log(n["size"].to_numpy(float)[ok])})
    gm = lt.groupby("t").mean()
    assert np.polyfit(gm.lv, gm.lg, 1)[0] == pytest.approx(-1.49, abs=1e-3)
    # G: glutamatergic edges onto leg MNs turn excitatory; every other edge is unchanged
    gl = _org(**{"cell_type:leg_motor|glutamate_receptor_sign": 1.0})
    post = base.conn.indices
    pre = np.repeat(np.arange(base.conn.n), np.diff(base.conn.indptr))
    glu = n.predictedNt.fillna("").str.lower().eq("glutamate").to_numpy()[pre]
    on = glu & leg[post]
    assert on.sum() > 1000
    assert np.all(gl.net.w[on] > 0) and np.any(base.net.w[on] < 0)
    assert np.array_equal(gl.net.w[~on], base.net.w[~on])
    assert np.allclose(np.abs(gl.net.w[on]), np.abs(base.net.w[on]))


def test_s4b_scale_is_neutral_by_default_and_scales_leg_mn_input_only():
    """S4b fit quantity (DECISIONS 14 Oct): one shared premotor-to-leg-MN synaptic scale, neutral 1."""
    from flyemu.percell import leg_motor_mask
    base = _org()
    inv = base.reg.inventory()
    assert "cell_type:leg_motor|synaptic_input_scale" in set(inv.entity + "|" + inv.property)
    leg = leg_motor_mask(base.conn)
    s = _org(**{"cell_type:leg_motor|synaptic_input_scale": 4.0})
    g = s.net.input_gain / base.net.input_gain
    assert np.all(g[~leg] == 1.0) and np.allclose(g[leg], 4.0)
    on = leg[base.conn.indices]                    # w carries the postsynaptic gain (lif.py)
    assert np.array_equal(s.net.w[~on], base.net.w[~on])
    assert np.allclose(s.net.w[on], 4.0 * base.net.w[on], rtol=1e-6)
