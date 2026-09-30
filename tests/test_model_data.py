"""The construction data model (data/model/, src/flyemu/model_data.py).

CONSTRUCTION.md task 1: every unknown has bounds, a basis, a prior, a label and
one mechanism; no orphan mechanisms; no registry key the model reads without a
row; the existing profile is a view of the table (its values lie inside the
bounds and equal the table's current_m4 column).
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "src"))

from flyemu import model_data as M  # noqa: E402

HAVE_GRAPH = (REPO / "data/cache/male_cns_edges.parquet").exists()


@pytest.fixture(scope="module")
def md():
    return M.load()


@pytest.fixture(scope="module")
def live_inventory():
    if not HAVE_GRAPH:
        pytest.skip("run scripts/fetch_male_cns.py first")
    from flyemu import profiles
    from flyemu.organism import Organism
    org = Organism(policy="minimal", profile="m4", min_synapses=profiles.WORKING_MIN_SYNAPSES)
    return org.reg.inventory()


def test_the_tables_are_valid(md):
    assert M.validate(md) == []


def test_the_validator_catches_what_it_claims(md):
    p = md.parameters.copy()
    i = p.index[p.param_id == "n2_v_rest"][0]
    p.loc[i, "current_m4"] = -80.0           # outside [-70, -45]
    p.loc[i, "bound_source"] = ""
    j = p.index[p.param_id == "n5_efficacy"][0]
    p.loc[j, "mechanism_id"] = "Z9"
    bad = M.validate(M.ModelData(md.mechanisms, p, md.structural))
    assert any("n2_v_rest: current_m4 -80.0 outside" in b for b in bad)
    assert any("n2_v_rest: bound without a source" in b for b in bad)
    assert any("n5_efficacy: unknown mechanism 'Z9'" in b for b in bad)
    assert any("N5: orphan mechanism" in b for b in bad) is False  # N5 still owns other rows
    m = md.mechanisms.copy()
    m.loc[m.id == "N23", ["status", "absent_reason"]] = ["absent", None]   # a tier C absent case
    assert any("N23: tier C absent without absent_reason" in b
               for b in M.validate(M.ModelData(m, md.parameters, md.structural)))


def test_the_template_has_56_mechanisms(md):
    assert (~md.mechanisms.infrastructure).sum() == 56


def test_every_key_the_model_reads_has_exactly_one_owner(md, live_inventory):
    keys = (live_inventory.entity + "|" + live_inventory.property).unique()
    cov = M.coverage(md, keys)
    assert cov[cov.n_rows == 0].key.tolist() == []
    assert M.ambiguous_keys(md, keys) == []


def test_the_m4_profile_is_a_view_of_the_table(md, live_inventory):
    """For every row with one concrete registry key, the live m4 value equals
    current_m4 (so current_m4 inside the bounds means m4 is inside them)."""
    live = {f"{r.entity}|{r.property}": r.value for r in live_inventory.itertuples()}
    checked = 0
    for r in md.parameters.itertuples():
        k = r.registry_key
        if not k or "*" in k or pd.isna(r.current_m4):
            continue
        assert k in live, f"{r.param_id}: {k} not read by the model"
        try:
            v = float(live[k])
        except (TypeError, ValueError):     # table-valued key (e.g. per-MN twitch tau)
            continue
        assert v == pytest.approx(r.current_m4, rel=1e-9), r.param_id
        checked += 1
    assert checked >= 40


def test_samples_stay_in_bounds_and_are_reproducible(md):
    p = md.parameters.set_index("param_id")
    for seed in range(10):
        s = M.sample(md, seed, stage=2)
        assert ((s >= p.bio_min) & (s <= p.bio_max)).all(), s[(s < p.bio_min) | (s > p.bio_max)]
    assert M.sample(md, 3, 2).equals(M.sample(md, 3, 2))
    assert not M.sample(md, 3, 2).equals(M.sample(md, 4, 2))


def test_stage_zero_is_the_current_model(md):
    """Neutral equivalence of the sampler: stage 0 releases nothing, so every
    wired value is the model's current value."""
    s0 = M.sample(md, 0, stage=0)
    p = md.parameters.set_index("param_id")
    cur = p.current_m4.dropna()
    assert np.allclose(s0[cur.index], cur)
    ov = M.registry_overrides(md, s0)
    for k, v in ov.items():
        row = p[p.registry_key == k].iloc[0]
        if not pd.isna(row.current_m4):
            assert v == row.current_m4


def test_classes_cover_the_modelled_graph_and_agree_with_the_model(md):
    c = pd.read_csv(REPO / "data/model/classes.csv", keep_default_na=False)
    assert c.n_cells.sum() == 167_111                    # male-cns, traced or typed (F-COUNT-2)
    assert not c.type.duplicated().any()
    assert set(c["mode"]) <= {"spiking", "graded", "unknown"}
    assert (c.mode_label != "").all() and (c.mode_source != "").all()
    # every unknown mode has a prior row in parameters.csv
    params = set(md.parameters.param_id)
    unk = c[c["mode"] == "unknown"]
    assert (unk.mode_param != "").all() and set(unk.mode_param) <= params
    # the types the model already runs graded are graded here
    for t in ("R1-R6", "R7", "R8", "L1", "L2", "L3", "APL"):
        rows = c[c.type.str.match(rf"^{t}") if t != "R1-R6" else c.type.str.match(r"^R[1-6]")]
        assert len(rows) and (rows["mode"] == "graded").all(), t
    # identities the construction depends on (LESSONS: ring cells, commands)
    cc = c.set_index("type").circuit_class
    assert cc["EPG"] == "cx_ring" and cc["Delta7"] == "cx_ring"
    assert cc["MDN"] == "DN" and cc["DNg100"] == "DN"
    assert cc["T4a"] == "T4T5"


def test_legacy_values_outside_bounds_are_reported_not_hidden(md):
    v = M.legacy_outside_bounds(md)
    assert any(x.startswith("b3_k_pro_retpro") for x in v)    # m4 1.0 vs measured 0.109


def test_template_switches_are_real_owned_switches(md):
    for k in M.TEMPLATE_SWITCHES:
        owners = M.owners(md, k)
        assert owners and all(src in ("structural", "switch") for src, *_ in owners), k


def test_every_key_the_working_model_reads_has_exactly_one_owner(md):
    """s10: m5 and m6 (the adopted templates) read keys that m4 never does; s11: m7 is working."""
    if not HAVE_GRAPH:
        pytest.skip("run scripts/fetch_male_cns.py first")
    from flyemu import profiles
    from flyemu.organism import Organism
    inv = Organism(policy="minimal", profile=profiles.WORKING_PROFILE, min_synapses=5).reg.inventory()
    keys = (inv.entity + "|" + inv.property).unique()
    cov = M.coverage(md, keys)
    assert cov[cov.n_rows == 0].key.tolist() == []
    assert M.ambiguous_keys(md, keys) == []


def test_ledger_rows_name_a_real_mechanism_and_a_consistent_fidelity(md):
    """Ledger v3 (session 11): every measurable quantity names the mechanism that
    carries it, and 'not simulated' agrees between model state and fidelity."""
    import yaml
    onto = yaml.safe_load((REPO / "data" / "ontology" / "fly_information.yaml").read_text())
    ids = set(md.mechanisms.id)
    for e in onto:
        assert e["mech"] in ids | {"none"}, e["quantity"]
        assert e["fidelity"] in {"element", "type", "class", "global", "none"}, e["quantity"]
        assert (e["fidelity"] == "none") == (e["model"] == "absent"), e["quantity"]
