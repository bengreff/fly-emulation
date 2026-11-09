"""Maturation's rule (wormemu.fit.maturation) on a toy plant with a known fixed point: Ca = floor + a s, with a
first-order Ca lag. No NEURON here; the single-cell test runs on backhouse (scripts/worm/fit/maturation_ephys.py)."""
from types import SimpleNamespace

import numpy as np
import pytest

from wormemu.fit import maturation as MT

FLOOR, TAU_CA_MS = 0.05, 50.0


class Toy:
    def __init__(self, a, names=("A", "B")):
        self.cell_names = list(names) + ["C"]
        self.a = np.append(np.asarray(a, float), 0.0)
        self.ca = FLOOR + self.a

    def drive(self, m, seconds, dt=1.0):
        for _ in range(int(1000 * seconds / dt)):
            g = m.step(SimpleNamespace(ca=self.ca), dt)["g_scale"]["dens_unc2"]
            self.ca = MT.relax(self.ca, FLOOR + self.a * g, TAU_CA_MS, dt)
        return m


def test_converges_to_known_fixed_point_with_the_codes_sign():
    toy = Toy([0.02, 0.01])
    tgt = {"A": FLOOR + 0.02 * 1.6, "B": FLOOR + 0.01 * 0.6}         # s* = 1.6 (Ca too low) and 0.6 (too high)
    m = MT.Maturation(toy, tgt, ca_start={"A": FLOOR + 0.02, "B": FLOOR + 0.01})
    toy.drive(m, 3.0)
    assert m.s[0] > 1.0 and m.s[1] < 1.0                              # Ca below target grows densities
    toy.drive(m, 300.0)
    assert m.s == pytest.approx([1.6, 0.6], rel=2e-3)
    assert m.converged().all()


def test_neutral_at_target():
    toy = Toy([0.02, 0.01])
    m = MT.Maturation(toy, {"A": FLOOR + 0.02, "B": FLOOR + 0.01})
    toy.drive(m, 30.0)
    assert m.s == pytest.approx([1.0, 1.0], abs=1e-9)


def test_bound_holds_without_windup():
    toy = Toy([0.02, 0.01])
    m = MT.Maturation(toy, {"A": FLOOR + 0.02 * 9.0, "B": FLOOR + 0.01}, ca_start={"A": FLOOR + 0.02})
    toy.drive(m, 200.0)
    mu = float(m.mu[0])
    toy.drive(m, 100.0)
    assert m.s[0] == MT.P["mat_s_hi"] and m.mu[0] == mu < MT.P["mat_s_hi"] + 0.2   # held: no windup
    assert m.converged()[0]                                           # at its bound and still: reported as such
    m.tgt[0] = FLOOR + 0.02 * 2.0                                     # reachable again: leaves the bound promptly
    toy.drive(m, 60.0)
    assert m.s[0] < MT.P["mat_s_hi"] - 0.5


def test_start_does_not_move_the_fixed_point():
    out = []
    for start in (1.0, MT.P["mat_s_lo"]):                            # built, and a nascent quarter-density cell
        toy = Toy([0.02], names=("A",))
        m = MT.Maturation(toy, {"A": FLOOR + 0.02 * 1.3}, ca_start={"A": FLOOR + 0.02}, start=start)
        toy.drive(m, 300.0)
        out.append(float(m.s[0]))
    assert out[0] == pytest.approx(1.3, rel=2e-3) and out[1] == pytest.approx(out[0], rel=2e-3)


def test_eq4_rates_from_built_densities_keep_one_multiplier():
    """The published per-channel rule (absolute g_i, rates r_i = k g_i_built, from the nascent state g = m = 0) keeps
    g_i / g_i_built the same for every channel: the reduction maturation.py runs."""
    gb = np.array([0.026, 0.006, 0.0011, 0.0005])                    # built densities (AFDL's shl1, egl19, irk, kvs1)
    w = np.array([-0.5, 3.0, -0.2, -0.4])                             # each channel's effect on Ca (toy)
    r, tgt, tau_g, tau_m, dt = gb / 0.01, FLOOR + 0.004, 2000.0, 20000.0, 1.0
    g, mi, ca = np.zeros(4), np.zeros(4), FLOOR
    for _ in range(400_000):
        mi = mi + r * (tgt - ca) * dt / tau_m
        g = np.maximum(MT.relax(g, mi, tau_g, dt), 0.0)
        ca = MT.relax(ca, FLOOR + float(w @ g), TAU_CA_MS, dt)
        s = g / gb
        assert np.ptp(s) <= 1e-9 * max(1.0, s.max())
    assert ca == pytest.approx(tgt, rel=1e-3)


def test_frozen_keeps_multipliers_across_reset():
    fz = MT.Frozen(3, np.array([0, 2]), np.array([0.5, 2.0]))
    g1 = fz.step(None, 1.0)["g_scale"]
    fz.reset()
    g2 = fz.step(None, 1.0)["g_scale"]
    assert set(g1) == {f"dens_{c}" for c in MT.REGULATED} and "dens_nca" not in g1
    assert g2["dens_shl1"].tolist() == [0.5, 1.0, 2.0] == g1["dens_shl1"].tolist()


def test_bulk_read_follows_the_pool_not_eq28():
    """ca_read 'bulk' senses mech/capool's ca_bulk_uM output and ignores ctx.ca (held flat at the Eq. 28 floor here,
    as the built cells hold it); without that output it raises instead of sensing nothing."""
    toy = Toy([0.02, 0.01])
    tgt = {"A": FLOOR + 0.02 * 1.6, "B": FLOOR + 0.01 * 0.6}
    m = MT.Maturation(toy, tgt, ca_start={"A": FLOOR + 0.02, "B": FLOOR + 0.01}, ca_read="bulk")
    flat = np.full(3, FLOOR)
    for _ in range(300000):
        g = m.step(SimpleNamespace(ca=flat, outputs={MT.BULK_KEY: toy.ca}), 1.0)["g_scale"]["dens_unc2"]
        toy.ca = MT.relax(toy.ca, FLOOR + toy.a * g, TAU_CA_MS, 1.0)
    assert m.s == pytest.approx([1.6, 0.6], rel=2e-3)
    m2 = MT.Maturation(toy, tgt, ca_read="bulk", params={"mat_settle_s": 0.5})
    with pytest.raises(KeyError):
        for _ in range(1000):
            m2.step(SimpleNamespace(ca=flat, outputs={}), 1.0)
    with pytest.raises(ValueError):
        MT.Maturation(toy, tgt, ca_read="cytosol")
