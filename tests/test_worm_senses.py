"""wbody's sensory modules without NEURON: specs, the touch indentation readout and channel kinetics, the cascade's
resting state, the proprio sign convention, temperature's Q10 arithmetic, the environment's neutral form and
its O2 field against the equation's analytic solution."""
import numpy as np
import pytest

from wormemu.brain_layers import SPECS as LAYER_SPECS
from wormemu.body import environment
from wormemu.mech import senses_chem, senses_proprio, senses_touch, temperature

MODS = (senses_chem, senses_touch, senses_proprio, temperature, environment)
LABELS = {"measured", "derived", "inferred", "guessed", "published_fit"}


def test_specs_unique_bounded_labelled():
    ids = [s.id for m in MODS for s in m.SPECS]
    assert len(ids) == len(set(ids))
    assert not set(ids) & {s.id for s in LAYER_SPECS}
    for m in MODS:
        mids = {t[0] for t in m.MECHANISMS}
        for s in m.SPECS:
            assert s.lo <= s.template <= s.hi, s.id
            assert s.label in LABELS, (s.id, s.label)
            assert s.source, s.id
            assert s.mechanism in mids, (s.id, s.mechanism)


def test_indentation_inverts_eq12():
    p = {s.id: s.template for s in senses_touch.SPECS}
    eq = (p["touch_pressure_kPa"], p["touch_radius_um"], p["touch_probe_radius_um"], p["touch_a1"], p["touch_a2"],
          p["touch_a3"])
    F = np.array([0.0, 0.5, 5.0, 50.0])
    w = senses_touch.indentation_um(F, *eq)
    pk, R, Rb, a1, a2, a3 = eq
    back = a1 * pk * 1e-3 * R * w * (1 + a2 * Rb / R) * (1 + a3 * w / R)
    assert np.allclose(back, F, rtol=1e-12, atol=1e-12)


def test_touch_channels_rest_and_on_off():
    p = {s.id: s.template for s in senses_touch.SPECS}
    ch = senses_touch.Channels([0], [50], [p["touch_g0"]], [p["touch_g1_per_um"]], p)
    rest = ch.step(np.array([0.0]), 4.0)[0]
    assert 0 < rest < 0.02
    on = max(ch.step(np.array([6.0]), 4.0)[0] for _ in range(1))
    hold = [ch.step(np.array([6.0]), 4.0)[0] for _ in range(100)]
    off = ch.step(np.array([0.0]), 4.0)[0]
    assert on > 5 * rest and off > 5 * rest and hold[-1] < 2 * rest
    assert np.isclose(ch.pc + ch.po + (1 - ch.pc - ch.po), 1.0) and (1 - ch.pc - ch.po) >= 0


def test_usuyama_cascade_stationary_at_rest():
    from wormemu.mech import senses_cgmp
    p = {s.id: s.template for s in senses_cgmp.network_specs("AWC")}
    c = senses_cgmp.Cascade(p, 1)
    x0 = c.x.copy()
    c.advance(1.0, np.array([0.001]), np.array([1.0]))
    assert np.allclose(c.x, x0, rtol=1e-2, atol=1e-6)


@pytest.mark.parametrize("kappa,vb,db", [(-8.0, True, False), (8.0, False, True)])
def test_proprio_signs(kappa, vb, db):
    m = senses_proprio.Mech.__new__(senses_proprio.Mech)      # only the strain readout, no brain
    m.p = {s.id: s.template for s in senses_proprio.SPECS}
    m.cells, m.kind = ["VB05", "DB04"], np.array(["b", "b"])
    m.sign, m.s0 = np.array([-1.0, 1.0]), np.array([0.6, 0.6])
    eps = m.strain({"curvature_per_mm": np.full(49, kappa), "s": np.linspace(0, 1, 49)})
    assert (eps[0] > 0) == vb and (eps[1] > 0) == db


def test_q10_factors():
    p = {s.id: s.template for s in temperature.SPECS}
    assert all(v == 1.0 for v in temperature.factors(p["temp_ref_C"], p).values())
    f = temperature.factors(p["temp_ref_C"] + 10, p)
    assert all(np.isclose(f[c], p[f"temp_q10_{c}"]) for c in temperature.CLASSES)


def test_environment_uniform_is_default_plate():
    e = environment.Environment(toggles=environment.UNIFORM, events=environment.standard_events())
    for t in (0.0, 3000.0, 5100.0, 8600.0):
        r = e.sample(t, (0.3, 0.1), (-0.7, 0.0), np.linspace(0, 1, 49))
        assert r["head"] == {} and r["tail"] == {} and r["tap"] == 0 and r["nose_force_uN"] == 0
        assert not r["contact_force_uN"].any()


def test_environment_o2_edge_matches_analytic():
    """A uniform lawn (no rim) of radius 20 mm: the steady O2 across the edge against the 1D half-plane solution
    O = O_am - (q/f)(1 - exp(-d/lam)/2) inside, O_am - (q/f) exp(d/lam)/2 outside, lam = sqrt(D/f). Bar: 10 % of q/f
    (grid 50 um ~ lam), interior within 1 %."""
    p = environment.P
    e = environment.Environment(params={"lawn_rim_ratio": 1.0, "lawn_radius_mm": 20.0, "lawn_edge_ahead_mm": 0.0},
                                toggles={"env_salt": "uniform", "env_temp": "uniform"})
    q, f, D = p["o2_lawn_sink_pct_s"], p["o2_f_per_s"], p["o2_D_cm2_s"] * 100
    lam, drop = np.sqrt(D / f), p["o2_lawn_sink_pct_s"] / p["o2_f_per_s"]
    d = np.linspace(-0.3, 0.3, 25)                           # depth into the lawn (edge at a = 0, lawn ahead)
    O = e.o2_at(np.stack([d, np.zeros_like(d)], 1))
    ana = np.where(d >= 0, p["o2_ambient_pct"] - drop * (1 - np.exp(-d / lam) / 2),
                   p["o2_ambient_pct"] - drop * np.exp(d / lam) / 2)
    assert np.max(np.abs(O - ana)) <= 0.1 * drop
    assert abs(e.o2_at(np.array([[10.0, 0.0]]))[0] - (p["o2_ambient_pct"] - drop)) <= 0.01 * drop
