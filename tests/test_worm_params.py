"""The parameter API (wormemu.params): every number has a role, the vector is the active rule and gap numbers only,
its transforms round-trip, get/set reach a WormSpec, a scan number cannot be set, and the unknown count is inside
Ben's target (at most 2,000, ideally at most 1,000)."""
import numpy as np
import pytest

from wormemu import brain_layers, mech, params
from wormemu.brain import sample_worm


def test_every_spec_has_a_role():
    for s in list(brain_layers.SPECS) + mech.all_specs():
        assert params.role_of(s.label, s.role) in params.ROLES, s.id
    cat = params.catalog()
    assert set(cat.role) <= set(params.ROLES)
    assert not cat[cat.active & ~cat.role.isin(["rule", "gap"])].shape[0]


def test_vector_and_count():
    th = params.Theta()
    c = params.counts()
    assert c["vector"] == th.n == c["rule"] + c["gap"]
    assert th.n <= 1000
    assert not th.table.id.duplicated().any()
    assert np.isfinite(th.x0).all() and ((th.x0 >= th.lo) & (th.x0 <= th.hi)).all()
    assert (th.table["transform"].isin(["log", "logit", "bernoulli"])).all()
    # the rules are in, the rows they replace are out
    assert "syn_nchan_per_em_lacr" in th.ids and "syn_strength_per_pair" not in th.ids
    assert not any(i.startswith("dens_kqt1_") for i in th.ids)


def test_get_set_and_transforms():
    th = params.Theta()
    sp = sample_worm(None)
    x = th.get(sp)
    assert np.allclose(x, th.x0)
    assert np.allclose(th.from_z(th.to_z(x)), x, rtol=1e-9, atol=0)
    z = np.random.default_rng(0).normal(0, 2, th.n)
    y = th.from_z(z)
    assert ((y >= th.lo) & (y <= th.hi)).all()
    sp2 = th.set(sp, y)
    assert np.allclose(th.get(sp2), y)
    assert np.allclose(th.get(sp), x)                    # the original is untouched
    k = th.ids.index("pas_cm_uF_cm2")
    assert sp2.values["pas_cm_uF_cm2"] == y[k]


def test_scan_cannot_be_set():
    sp = sample_worm(None)
    with pytest.raises(params.ScanValue):
        params.set_value(sp, "rec_lacr_gamma_pS", 40.0)
    sp2 = params.set_value(sp, "pas_cm_uF_cm2", 1.2)
    assert sp2.values["pas_cm_uF_cm2"] == 1.2
    sp3 = params.set_value(sp, "res_syn_pair", 0.5, element="AVAL>AVBL")
    assert sp3.values["res_syn_pair"]["AVAL>AVBL"] == 0.5 and "res_syn_pair" not in sp.values
