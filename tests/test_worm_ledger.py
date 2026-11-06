"""The worm ledger (data/worm/model, built by scripts/worm/build_ledger.py) and its export docs/worm/ledger.json."""
import json
from pathlib import Path

import numpy as np
import pytest

from bioemu import ledger

ROOT = Path(__file__).resolve().parents[1]
MODEL = ROOT / "data" / "worm" / "model"


@pytest.fixture(scope="module")
def led():
    return ledger.load(MODEL)


def test_validates(led):
    assert ledger.validate(led) == []


def test_every_row_complete(led):
    p = led.parameters
    for r in p.itertuples():
        assert r.mechanism_id in set(led.mechanisms.id), r.param_id
        assert r.grain in ledger.GRAINS and r.label in ledger.LABELS, r.param_id
        assert r.fill_kind == ledger.FILL_KIND[r.label] and r.source_project in ledger.SOURCE_PROJECTS, r.param_id
        if r.label != "absent":
            assert np.isfinite(r.bio_min) and np.isfinite(r.bio_max) and r.prior_dist in ledger.PRIOR_DISTS, r.param_id


def test_precision_not_invented(led):
    p = led.parameters
    assert ((p.precision_needed == "not yet estimated") | (p.precision_method != "")).all()


def test_export_matches_ledger(led):
    out = json.loads((ROOT / "docs/worm/ledger.json").read_text())
    c = ledger.counts(led)
    assert out["totals"]["numbers"] == c["total_numbers"]
    assert out["totals"]["by_label"] == c["by_label"]
    sf = out["source_by_fill_kind"]["all"]
    assert sum(sum(v.values()) for v in sf.values()) == c["total_numbers"]
    assert sum(sum(v.values()) for v in out["source_by_fill_kind"]["physiology"].values()) == \
        out["totals_physiology"]["numbers"]


def test_absent_only_where_no_mechanism(led):
    """Thursday's bar: a number may be absent only if its mechanism has no implementation."""
    absent_mech = set(led.mechanisms.id[led.mechanisms.status == "absent"])
    for r in led.parameters.itertuples():
        t = led.values(r.param_id)
        n_absent = int((t.label == "absent").sum()) if t is not None else (int(r.n_values) if r.label == "absent" else 0)
        if n_absent:
            assert r.mechanism_id in absent_mech, r.param_id


def test_wiring_is_cook(led):
    """Every neuron-neuron Cook 2019 pair has a strength; 95 body-wall muscles, none called MCVL24."""
    chem = led.values("wire_chem_contacts")
    assert len(led.values("syn_strength_per_pair")) == len(chem) == 3709 and chem.value.sum() == 20965
    assert len(led.values("gap_strength_per_pair")) == len(led.values("wire_gap_contacts")) == 1091
    m = led.values("mpas_cm")
    assert len(m) == 95 and m.element.str.match(r"^[dv]BWM[LR]\d+$").all() and "MCVL24" not in set(m.baaiworm_cell)


def test_published_fits_labelled(led):
    p = led.parameters.set_index("param_id")
    assert p.loc["dens_shl1", "label"] == "published_fit" and p.loc["dens_shl1", "source_project"] == "BAAIWorm"
    assert (p[p.source_project == "c302"].label == "published_fit").all()
    assert p.loc["nano_gsc", "label"] == "guessed"


def test_measured_signs(led):
    """BRAIN_PORT 9: Roberts et al. 2016 measured AVA<->AVB and ASH->AVB inhibition; those 9 Cook pairs are inhibitory,
    labelled measured, and win over Fenyves (ASH->AVB was + there); AVA->AVA and AVB->AVB are untouched."""
    t = led.values("syn_sign_receptor").set_index("element")
    pairs = [f"{a}>{b}" for a in ("AVAL", "AVAR", "AVBL", "AVBR") for b in ("AVAL", "AVAR", "AVBL", "AVBR")
             if a[:3] != b[:3] and f"{a}>{b}" in t.index] + ["ASHL>AVBL", "ASHR>AVBR"]
    assert len(pairs) == 9                                                    # Cook has no AVAL>AVBR
    for p in pairs:
        r = t.loc[p]
        assert int(r.value) == 1 and r.label == "measured" and r.source_project == "literature", p
        assert r.source.startswith("Roberts et al. 2016"), p
    assert "overrides Fenyves" in t.loc["ASHL>AVBL"].source
    assert (t.loc[[p for p in ("AVAL>AVAR", "AVAR>AVAL", "AVBL>AVBR", "AVBR>AVBL")]].label != "measured").all()
