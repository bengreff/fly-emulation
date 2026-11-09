"""The vital-signs battery's readouts, physicality check and scoring on synthetic records with known answers
(wormemu.fit.vitals). No simulation runs here; the battery itself runs on backhouse (VITAL_SIGNS.md)."""
import numpy as np
import pytest

from wormemu.fit import vitals as V
from wormemu.interface import BWM_NAMES

DT_S = V.EXCHANGE_MS / 1000.0


def synthetic(seconds=60.0, pump_hz=3.0, dmp_s=50.0, bwm_hz=0.5, eggs=(), seed=0):
    rng = np.random.default_rng(seed)
    t = np.arange(1, int(seconds / DT_S) + 1) * DT_S
    neur = ["AIYL", "AIYR", "AFDL", "AFDR", "AWAL", "AWAR"] + [f"N{k}" for k in range(30)]
    cells = neur + list(BWM_NAMES)
    n = len(t)
    v = np.full((n, len(cells)), -50.0)
    v[:, 0:2], v[:, 2:4], v[:, 4:6] = -54.0, -79.0, -75.0
    v += rng.normal(0, 0.1, v.shape)
    nb = len(BWM_NAMES)
    vb = np.full((n, nb), -25.0)
    for j in range(nb // 2):                                     # half the muscles fire at bwm_hz, 2 ms spikes
        ph = rng.uniform(0, 1.0 / bwm_hz)
        on = ((t - ph) % (1.0 / bwm_hz)) < 0.01
        vb[on, j] = 10.0
    v[:, len(neur):] = vb
    lat = rng.normal(size=(n, 2))                                # 2 latent signals drive every neuron's GCaMP
    lat = np.cumsum(lat, axis=0) * 0.001                       # dF/F stays above -1 (F > 0), as a real trace does
    g = lat @ rng.normal(size=(2, len(neur))) + rng.normal(0, 0.01, (n, len(neur)))
    gc = np.full((n, len(cells)), np.nan)
    gc[:, :len(neur)] = g
    ca = np.full((n, len(cells)), 0.05)
    pumps = np.zeros(n)
    k = np.arange(1, n + 1)
    pumps[np.floor(k * DT_S * pump_hz + 1e-9) != np.floor((k - 1) * DT_S * pump_hz + 1e-9)] = 1
    ex = np.zeros(n)
    for x in np.arange(dmp_s / 2, seconds, dmp_s):
        ex[np.searchsorted(t, x)] = 1
    eg = np.zeros(n)
    for x in eggs:
        eg[np.searchsorted(t, x)] += 1
    ic = np.full((n, 20), 0.1)
    for x in np.arange(dmp_s / 2, seconds, dmp_s):
        ic[:, 18:20] += 0.8 * np.exp(-((t - x + 3.0) / 1.0) ** 2)[:, None]      # int9L, int9R (the pacemaker)
        ic[:, 9] += 0.8 * np.exp(-((t - x + 20.0) / 1.0) ** 2)                 # int4R peaking apart: must not count
    return {"t_ms": 1000.0 * t, "cells": cells, "v_mV": v, "ca_uM": ca, "gcamp_dff": gc, "pumps": pumps,
            "expulsions": ex, "eggs_laid": eg, "out:intestine_ca_uM": ic}


def test_readouts_recover_known_values():
    res = synthetic(seconds=160.0)
    r = V.readouts(res, "food", 160.0)
    assert r["rest_AIY"] == pytest.approx(-54.0, abs=0.1)
    assert r["rest_AFD"] == pytest.approx(-79.0, abs=0.1)
    assert r["rest_AWA"] == pytest.approx(-75.0, abs=0.1)
    assert r["pump_hz"] == pytest.approx(3.0, rel=0.02)
    assert r["expulsions"] == 3 and r["dmp_period_s"] == pytest.approx(50.0, abs=DT_S)
    assert r["int_ca_period_s"] == pytest.approx(50.0, abs=0.1)
    assert r["bwm_rest_mV"] == pytest.approx(-25.0, abs=0.01)
    assert r["bwm_frac_firing"] == pytest.approx((len(BWM_NAMES) // 2) / len(BWM_NAMES))
    assert r["bwm_spike_hz"] == pytest.approx(0.5, rel=0.05)
    assert r["pc3_frac"] > 0.95                                # two latents: the top 3 PCs hold nearly everything
    assert r["eggs"] == 0 and r["egg_intra_s"] is None


def test_dmp_needs_two_intervals():
    r = V.readouts(synthetic(seconds=80.0), "food", 80.0)        # expulsions at 25 and 75 s: one interval
    assert r["expulsions"] == 2 and r["dmp_period_s"] is None


def test_pc_frac_independent_vs_lowrank():
    rng = np.random.default_rng(1)
    x = rng.normal(size=(2000, 50))
    f, n = V.pc_frac(x)
    assert n == 50 and f == pytest.approx(3 / 50, abs=0.02)      # white noise: about k / N
    x[:, 10] = 3.0                                               # a flat column is dropped
    assert V.pc_frac(x)[1] == 49


def test_egg_bouts():
    bouts, intra, inactive = V.egg_bouts([10, 30, 50, 1300, 1320, 2600])
    assert len(bouts) == 3 and intra == [20, 20, 20] and inactive == [1250, 1280]


def test_physicality_flags():
    res = synthetic(seconds=10.0)
    assert V.physicality(res, (-80.0, 60.0))["physical"]
    res["v_mV"][100, 3] = -95.0
    res["out:intestine_ca_uM"][50, 2] = -0.01
    p = V.physicality(res, (-80.0, 60.0))
    assert not p["physical"] and p["v_out_cells"] == 1 and p["v_out_worst"][0][0] == "AFDR"
    assert "out:intestine_ca_uM" in p["negative"]
    res["ca_uM"][5, 5] = np.nan
    assert not V.physicality(res, (-80.0, 60.0))["finite"]


def test_physicality_flags_step_alternation():
    res = synthetic(seconds=10.0)
    v = res["v_mV"]
    L = V.ALT_STEPS                                       # -50 surround: a block of L samples gives L reversals
    v[200:200 + L, 4] = -50.0 + 10.0 * (-1.0) ** np.arange(L)
    v[600:600 + L - 1, 6] = -50.0 + 10.0 * (-1.0) ** np.arange(L - 1)                     # one short
    v[900:903, 7] = (-40.0, 20.0, -40.0)                                                   # one fast spike
    p = V.physicality(res, (-80.0, 60.0))
    assert not p["physical"] and p["v_out_cells"] == 0
    assert p["alt_cells"] == 1 and p["alt_worst"] == [(res["cells"][4], V.ALT_STEPS)]


def test_score_statuses():
    r = V.readouts(synthetic(seconds=160.0, pump_hz=3.4), "food", 160.0)
    s = V.score(r, "food")
    assert s["egg_intra_s"]["status"] == "too short"
    assert "pump_hz_off" not in s
    sg = V.SIGN["pump_hz"]
    old = (sg.mean, sg.sd, sg.lo, sg.hi)
    sg.mean, sg.sd, sg.lo, sg.hi = 3.46, 0.85, None, None
    try:
        assert V.score(r, "food")["pump_hz"]["status"] == "in"
        r2 = dict(r, pump_hz=0.0)
        assert V.score(r2, "food")["pump_hz"]["status"] == "miss"
        r3 = dict(r, dmp_period_s=None)
        assert V.score(r3, "food")["dmp_period_s"]["status"] in ("not produced", "no bar")
    finally:
        sg.mean, sg.sd, sg.lo, sg.hi = old


def test_plate_is_on_the_experiment():
    from wormemu.body.metaworm import AGAR_FILM
    for cond, env in V.PLATES.items():
        ex = V.experiment(cond, 2.0)
        assert ex.world == dict(AGAR_FILM) and ex.env == env and ex.scene == {"field": "cone_published"}


def test_experiment_is_entire_worm():
    ex = V.experiment("food", 2.0)
    assert ex.body == "on" and ex.toggles == V.BATTERY_TOGGLES and ex.every_ms == pytest.approx(V.EXCHANGE_MS)
    with pytest.raises(ValueError):
        V.experiment("lawn", 2.0)


def test_f_over_fmean_cancels_f0():
    """The GCaMP signs read F / mean F (Atanas's normalisation), so the reference F0 drops out: the same F read
    against two different F0 gives the same pc3 and range."""
    rng = np.random.default_rng(3)
    f = 1.0 + 0.3 * np.abs(rng.normal(size=(400, 20)))           # F in units of some F0
    a, b = f - 1.0, f / 1.7 - 1.0                                # dF/F0 against F0 and against 1.7 F0
    assert np.allclose(V.f_over_fmean(a), V.f_over_fmean(b))
    assert np.allclose(V.f_over_fmean(a).mean(axis=0), 1.0)


def test_noise_sd_on_slow_signal():
    """White noise of SD 0.04 under an exponentially correlated signal of SD S = 0.3 (frames 0.6 s, tau 5 s, so
    a = exp(-0.12)), as Atanas's traces are read. 2 D1 - D2 is exact for a signal whose autocovariance falls linearly
    over two frames; for an exponential it reads s^2 + S^2 (1 - a)^2 (derived), 0.052 here, still well under D1."""
    rng = np.random.default_rng(4)
    n, m, a, S, sd = 20000, 8, np.exp(-0.6 / 5.0), 0.3, 0.04
    s = np.zeros((n, m))
    for k in range(1, n):
        s[k] = a * s[k - 1] + rng.normal(0, S * np.sqrt(1 - a * a), m)
    x = s + rng.normal(0, sd, (n, m))
    tot, nse, sig = V.noise_sd(x)
    assert np.median(nse) == pytest.approx(np.sqrt(sd ** 2 + S ** 2 * (1 - a) ** 2), rel=0.1)
    assert np.median(sig) == pytest.approx(S, rel=0.05)
    d1 = np.sqrt(np.var(np.diff(x, axis=0), axis=0) / 2)
    assert np.median(d1) > 1.5 * np.median(nse)


def test_battery_values_set_per_experiment():
    """The battery's instrument noise (Atanas's, measured) sits on top of whatever theta the caller gives."""
    assert V.battery_theta(None) == V.BATTERY_VALUES
    assert V.battery_theta({"obs_noise_dff": 0.2, "x": 1.0}) == {"x": 1.0, **V.BATTERY_VALUES}
    assert 0.026 <= V.ATANAS_NOISE_DFF <= 0.068


def test_observations_sigma_rules_and_missing_signs():
    r = {"bio_s": 200.0, "rest_AWA": -60.0, "pc3_frac": 0.1, "gcamp_range": 0.6, "pump_hz": 0.0, "dmp_period_s": None,
         "egg_inactive_min": None, "egg_intra_s": None, "bwm_rest_mV": -30.0, "bwm_spike_hz": 2.9, "rest_AIY": -50.0}
    off = {"bio_s": 200.0, "rest_AWA": -61.0, "pump_hz_off": 0.0, "bwm_rest_mV": -31.0, "bwm_spike_hz": 2.8}
    names, g, y, sig = V.observations({"food": {"readouts": r}, "nofood": off})
    d = {n: (a, b, c) for n, a, b, c in zip(names, g, y, sig)}
    assert "food:rest_AIY" not in d and "food:ca_rest_uM" not in d          # no bar, no observation
    assert d["food:rest_AWA"][1:] == (-75.3, 4.7)                           # the published SD
    assert d["food:pc3_frac"][2] == pytest.approx((0.506 - 0.353) / 3.29)   # percentile band
    assert d["nofood:pump_hz_off"][1:] == pytest.approx((0.88, 0.425))      # inferred band: midpoint, quarter width
    assert d["food:bwm_spike_hz"][1:] == (0.73, 0.73)
    assert np.isnan(d["food:dmp_period_s"][0]) and np.isnan(d["food:egg_intra_s"][0])   # not produced / too short
    assert d["nofood:bwm_rest_mV"][0] == -31.0 and "nofood:pc3_frac" not in d
    n2, g2, *_ = V.observations({"food": r}, ids={"rest_AWA", "pc3_frac"})
    assert n2 == ["food:rest_AWA", "food:pc3_frac"] and np.isfinite(g2).all()
