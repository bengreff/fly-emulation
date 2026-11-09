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
    lat = np.cumsum(lat, axis=0) * 0.01
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
        ic[:, 9] += 0.8 * np.exp(-((t - x + 3.0) / 1.0) ** 2)
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


def test_plate_patches_and_restores():
    from wormemu.body import loop
    orig = loop.Body
    with V.plate({"env_food": "off"}):
        assert loop.Body is not orig and issubclass(loop.Body, orig)
    assert loop.Body is orig


def test_experiment_is_entire_worm():
    ex = V.experiment("food", 2.0)
    assert ex.body == "on" and ex.toggles == V.BATTERY_TOGGLES and ex.every_ms == pytest.approx(V.EXCHANGE_MS)
    with pytest.raises(ValueError):
        V.experiment("lawn", 2.0)
