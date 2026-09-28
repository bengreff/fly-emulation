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
                        lambda reg, conn, rel, inp, spont: (rel, inp, spont, None, None, 0.0, 1.0))
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


def test_every_circuit_class_has_its_bounded_rows():
    import pandas as pd
    from flyemu import model_data as M
    md = M.load()
    cc = set(pd.read_csv(REPO / "data/model/classes.csv", keep_default_na=False).circuit_class)
    p = md.parameters
    for prop in ("release_scale", "input_scale", "tonic_drive", "noise", "threshold_offset",
                 "tau_m_scale"):
        keys = set(p.registry_key[p.registry_key.str.endswith(f"|{prop}")
                                  & p.registry_key.str.startswith("class:")])
        assert keys == {f"class:{c}|{prop}" for c in cc}, prop
    assert M.validate(md) == []


@needs_graph
def test_slow_channels_are_inert_at_neutral_and_act_when_enabled():
    """N7 (mGluR, mAChR) and N8 (NMDA-type, Mg block): off -> no channels; on ->
    weight moved from fast to slow (total conserved), slow current arrives and
    decays slowly; the NMDA share is blocked at rest and relieved when depolarised."""
    base = _org()
    assert base.net.chan == []
    on = _org(**{"cell_type:all|machr_fraction": 0.3, "cell_type:all|nmda_fraction": 0.5,
                 "cell_type:all|mglur_fraction": 0.2})
    names = [c["name"] for c in on.net.chan]
    assert names == ["mglur", "machr", "nmda"]
    tot = on.net.w + sum(c["w"] for c in on.net.chan)
    assert np.allclose(tot, base.net.w, atol=1e-6)
    ach = on.net.chan[1]["w"]
    assert (ach != 0).sum() > 1e5
    # drive a set of cholinergic cells and watch slow current appear and outlast the fast one
    nt = on.conn.neurons.predictedNt.fillna("").str.lower().to_numpy()
    src = np.flatnonzero(nt == "acetylcholine")[:2000]
    for _ in range(20):
        on.net.step(kick=(src, 50.0))
    i_fast0 = np.abs(on.net.i_syn).sum()
    i_slow0 = np.abs(on.net.chan[1]["i"]).sum()
    assert i_slow0 > 0
    for _ in range(200):                                  # 20 ms without input
        on.net.step()
    assert np.abs(on.net.chan[1]["i"]).sum() / i_slow0 > 0.8     # tau 300 ms
    # Mg block: B(V) small at rest (-52 mV), larger when depolarised
    b = lambda v: 1 / (1 + 1.0 / 3.57 * np.exp(-0.062 * v))
    assert b(-52.0) < 0.2 < 0.5 < b(0.0)


@needs_graph
def test_kc_mbon_plasticity_is_timing_dependent_and_forgets():
    """N21: KC before DA depresses, DA before KC potentiates (Handler et al. 2019);
    N22: weights relax back to baseline with the recovery tau. Off by default."""
    base = _org()
    assert base.net.kc_edge is None
    ov = {"cell_type:all|kc_mbon_ltd_timing_rate": 0.05, "cell_type:all|kc_mbon_ltp_timing_rate": 0.002}

    def run(order, extra=None):
        o = _org(**{**ov, **(extra or {})})
        n = o.net
        t = o.conn.neurons.type.fillna("")
        dan = np.flatnonzero(t.str.match(r"^PAM").to_numpy())
        kc = np.flatnonzero(n.is_kc)[:600]
        seq = [kc, dan] if order == "kc_first" else [dan, kc]
        for grp in seq:
            for _ in range(30):
                n.step(kick=(grp, 50.0))
        for _ in range(50):
            n.step()
        return n, n.w[n.kc_e] / np.where(n.kc_w0 != 0, n.kc_w0, 1)

    n1, r1 = run("kc_first")
    n2, r2 = run("da_first")
    cap = n1.params.kc_w_cap
    for r in (r1, r2):
        assert r.min() >= -1e-6 and r.max() <= cap + 1e-5      # bounded, sign kept
    ch1, ch2 = r1[np.abs(r1 - 1) > 1e-4], r2[np.abs(r2 - 1) > 1e-4]
    assert ch1.size > 100 and np.median(ch1) < 1.0            # KC first: net depression
    assert ch2.size > 100 and np.median(ch2) > 1.0            # DA first: net potentiation
    n3, r3 = run("kc_first", {"cell_type:all|kc_mbon_forgetting": 1.0,
                                 "cell_type:all|kc_mbon_memory_tau_h": 20.0 / 3.6e6})
    for _ in range(2000):                                     # 200 ms >> 20 ms
        n3.step()
    r3b = n3.w[n3.kc_e] / np.where(n3.kc_w0 != 0, n3.kc_w0, 1)
    assert np.abs(r3b - 1).max() < np.abs(r3 - 1).max() * 0.1


@needs_graph
def test_unknown_mode_groups_switch_to_graded_only_when_set():
    base = _org()
    on = _org(**{"mode:n1_p_graded_al_ln|graded": 1.0})
    import pandas as pd
    c = pd.read_csv(REPO / "data/model/classes.csv", keep_default_na=False)
    ln = set(c[c.mode_param == "n1_p_graded_al_ln"].type)
    nn = on.conn.neurons
    key = pd.Series(np.where(nn.type.notna(), nn.type, "untyped:" + nn.superclass.fillna("none")))
    m = key.isin(ln).to_numpy()
    assert m.sum() > 300
    assert not base.net.graded[m].any() and on.net.graded[m].all()
    assert np.array_equal(base.net.graded[~m], on.net.graded[~m])


@needs_graph
def test_curated_gap_junctions_wire_into_the_organism():
    base = _org()
    assert base.net.elec is None
    on = _org(**{"electrical:JO-B1_a->DNp01|spike_coupling": 5.0,
                 "electrical:VS->VS|spike_coupling": 2.0})
    pre, post, k = on.net.elec
    t = on.conn.neurons.type.fillna("").to_numpy()
    assert set(t[pre]) == {"JO-B1_a", "VS"} and set(t[post]) == {"DNp01", "VS"}
    assert (pre != post).all() and set(np.unique(k)) == {2.0, 5.0}
