"""Task 12 internal state (internal_state.py): S1-S4, N20 (minimal), N25, N26.

Neutral equivalence (switch off in m4: no object, sense() unchanged) and what
each state variable claims, on the pure ODE (fast) and on the organism.
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pytest

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "src"))

from flyemu.internal_state import Organs, default_params, tim_dd  # noqa: E402

HAVE_GRAPH = (REPO / "data/cache/male_cns_edges.parquet").exists()
P = default_params()


def run(o, hours, dt=60.0, **kw):
    for _ in range(int(hours * 3600 / dt)):
        o.step(dt, **kw)
    return o


# --- S3 crop and gut ---------------------------------------------------------

def test_crop_fills_only_while_touching_food_and_empties_with_its_tau():
    o = Organs(P)
    run(o, 0.1, dt=1.0, food_sugar_M=0.5, touching_food=False)
    assert o.crop_nl == 0.0
    run(o, 60 / 3600, dt=1.0, food_sugar_M=0.5, touching_food=True)
    c0 = o.crop_nl
    assert 0.5 * P["ingest_nl_s"] * 60 < c0 <= P["ingest_nl_s"] * 60
    assert o.crop_sugar == pytest.approx(0.5 * c0, rel=0.1)     # M x nL = nmol
    run(o, P["tau_crop_s"] / 3600, dt=1.0)                        # one tau, not touching
    assert o.crop_nl == pytest.approx(c0 * np.exp(-1), rel=0.03)
    # ingestion stops at crop capacity
    run(o, 2.0, dt=1.0, touching_food=True, food_sugar_M=0.1)
    assert o.crop_nl < P["crop_max_nl"]


# --- S1 / S2 energy ----------------------------------------------------------

def test_sugar_falls_with_activity_and_recovers_on_feeding():
    rest = run(Organs(P), 2)
    act = run(Organs(P), 2, activity=1.0)
    assert act.sugar_mM < rest.sugar_mM - 2
    assert act.hunger > 0.2 and rest.hunger == 0.0
    fat_before = act.fat
    run(act, 5 / 60, food_sugar_M=1.0, touching_food=True)
    run(act, 4)
    assert act.hunger == 0.0 and act.sugar_mM >= rest.sugar_mM - 1
    assert act.fat > fat_before                                # meal stored (DILP-like)


def test_akh_like_release_when_sugar_is_low():
    ctl = run(Organs(P), 0.5)
    o = Organs(P)
    o.sugar *= 0.5                                            # hypoglycaemic
    o.step(60.0)
    assert o.akh > Organs(P).akh                              # AKH-like level rises when low
    run(o, 0.5)
    assert o.fat < ctl.fat                                    # extra release from the store
    assert o.sugar_mM > 0.9 * P["conc0_mM"]                   # glycaemia restored
    # without a store there is no release
    e = Organs(P, fat=0.0)
    e.sugar *= 0.5
    run(e, 0.5)
    assert e.sugar_mM < 0.5 * P["conc0_mM"]


def test_starvation_exhausts_the_store_in_days_not_hours():
    o = Organs(P)
    t = 0
    while o.fat > 1.0 and t < 10 * 86400:
        o.step(600.0)
        t += 600
    assert 24 * 3600 < t < 5 * 86400


# --- S4 water ----------------------------------------------------------------

def test_water_loss_rises_with_dryness_heat_and_activity_and_drinking_quenches():
    base = run(Organs(P), 3, humidity_rh=0.8)
    dry = run(Organs(P), 3, humidity_rh=0.1)
    hot = run(Organs(P), 3, humidity_rh=0.8, temperature_c=32)
    act = run(Organs(P), 3, humidity_rh=0.8, activity=1.0)
    assert dry.water_nl < base.water_nl and hot.water_nl < base.water_nl and act.water_nl < base.water_nl
    assert dry.thirst > base.thirst
    run(dry, 3 / 60, touching_food=True)                       # plain water
    run(dry, 3)
    assert dry.thirst < 0.1


# --- N26 clock ----------------------------------------------------------------

def _period_h(o, days=4, dt=120.0):
    wraps, prev = [], o.ct_h
    for _ in range(int(days * 86400 / dt)):
        o.step(dt)
        if o.ct_h < prev - 12:
            wraps.append(o.t_s)
        prev = o.ct_h
    return np.diff(wraps).mean() / 3600


def test_free_running_period_is_the_parameter_and_within_bounds():
    for per in (23.0, 24.0, 25.0):
        q = dict(P, period_h=per)
        assert _period_h(Organs(q)) == pytest.approx(per, abs=0.1)
    assert 22 <= P["period_h"] <= 26


def _ld(o, days, dt=120.0, lux=500.0):
    for _ in range(int(days * 86400 / dt)):
        o.step(dt, light_lux=lux if (o.t_s % 86400) < 43200 else 0.0)
    return o


def test_light_entrains_and_shifts_phase():
    ends = [_ld(Organs(P, z=complex(np.exp(1j * a))), 6).ct_h for a in (0.0, 1.5, 3.1, 4.6)]
    d = [(e - ends[0] + 12) % 24 - 12 for e in ends]
    assert max(abs(x) for x in d) < 0.5                       # all phases converge
    assert abs((ends[0] + 12) % 24 - 12) < 1.5                # CT0 within 1.5 h of lights-on
    dark = run(Organs(P, z=-1 + 0j), 24, dt=120.0)
    lit = _ld(Organs(P, z=-1 + 0j), 1)
    assert abs((lit.ct_h - dark.ct_h + 12) % 24 - 12) > 1.0   # one light day shifts the phase



def test_cry_tim_light_input_is_night_gated_and_starts_entrained():
    """s20 N26, state:clock|light_input = 1 (CRY-dependent TIM degradation; DECISIONS 22 Oct 23:02, 23:55):
    a run started in the light starts with TIM already cleared (no start-up kick); a pulse moves the phase only
    when TIM is up (night); the neutral path never touches c or T."""
    q = dict(P, light_input=1.0, k_tim=0.789, ct_tim_h=7.59)          # the s20 fit (fitted values)
    z15 = complex(np.exp(1j * 2 * np.pi * 1.5 / 24))
    o = Organs(q, z=z15)
    assert o.cry > 0.99 and o.tim < 1e-3                               # ZT 1.5 after 12:12 LD
    o.step(60.0, light_lux=1000.0)
    assert o.ct_h == pytest.approx(1.5 + 60 / 3600, abs=2e-3)

    def shift(ct):
        z = complex(np.exp(1j * 2 * np.pi * ct / 24))
        a, b = (Organs(q, z=z, cry=0.0, tim=tim_dd(ct)) for _ in range(2))      # DD start state
        a.step(600.0, light_lux=1000.0)
        b.step(600.0, light_lux=0.0)
        run(a, 8)
        run(b, 8)
        return (a.ct_h - b.ct_h + 12) % 24 - 12
    assert abs(shift(6.0)) < 0.1                                        # subjective day: dead zone
    assert shift(15.0) < -1.0 and shift(21.0) > 1.0                     # early delay, late advance
    n = Organs(P, z=z15)
    c0, t0 = n.cry, n.tim
    run(n, 1, light_lux=1000.0)
    assert (n.cry, n.tim) == (c0, t0)                                   # neutral 0 leaves c and T alone

# --- N25 sleep homeostat -------------------------------------------------------

def test_clock_starts_at_the_registered_phase():
    """s12: state:clock|initial_ct sets the CT at t = 0 (0 = the m4-m9r convention; m9c uses the
    male-cns specimen's ZT 1.5), and the tonic clock drive follows it from the first step."""
    import pandas as pd
    from flyemu import internal_state
    from flyemu.connectome import Connectome
    from flyemu.registry import Policy, Registry
    nrn = pd.DataFrame({"bodyId": [-1, -2, -3], "type": ["DN1pA", "LNd_b", "other"],
                        "predictedNt": "acetylcholine", "superclass": "x", "class": "x"})
    conn = Connectome(nrn, np.zeros(4, np.int64), np.zeros(0, np.int32), np.zeros(0, np.float32),
                      np.zeros(3, np.float32), np.zeros(0, np.float32))
    for ct0 in (0.0, 1.5):
        reg = Registry(Policy.MINIMAL)
        reg.overrides.update({"state:organs|model": 1.0, "state:clock|initial_ct": ct0,
                              "state:coupling|clock_gain": 7.75})
        st = internal_state.build(reg, conn)
        assert st.organs.ct_h == pytest.approx(ct0, abs=1e-9)
        t = st.tonic()
        assert t[0] == pytest.approx(7.75 * np.cos(2 * np.pi * (ct0 - 2.0) / 24), abs=1e-5)    # morning
        assert t[1] == pytest.approx(7.75 * np.cos(2 * np.pi * (ct0 - 10.0) / 24), abs=1e-5)   # evening
        assert t[2] == 0


def test_sleep_pressure_rises_awake_decays_in_rest_and_switches_with_hysteresis():
    o = Organs(P)
    p0 = o.pressure
    run(o, 12, activity=0.5)
    assert o.pressure > p0 and not o.asleep and o.switch
    run(o, 2 / 60, activity=0.0)                               # < 5 min inactive: not yet asleep
    assert not o.asleep
    hi = o.pressure
    run(o, 8, activity=0.0)
    assert o.asleep and o.pressure < hi and not o.switch


# --- the organism ---------------------------------------------------------------

@pytest.fixture(scope="module")
def orgs():
    if not HAVE_GRAPH:
        pytest.skip("no graph cache")
    from flyemu.organism import Organism
    kw = dict(policy="minimal", profile="m4", min_synapses=5)
    return (Organism(**kw), Organism(**kw),
            Organism(**kw, overrides={"state:organs|model": 1.0}))


def test_switch_off_leaves_no_state_and_sense_unchanged(orgs):
    a, b, _ = orgs
    assert a.organs is None
    inv = a.reg.inventory()
    assert float(inv.set_index(inv.entity + "|" + inv.property).loc["state:organs|model", "value"]) == 0
    obs = a.body.observe()
    got = a.sense(1, obs)
    obs_b = b.body.observe()
    want = b.aff.drive(obs_b)
    if b.vis is not None:
        want = want + b.vis.last()
    want = want + b.chem.drive(b.world, b.body.sim.mj_data.xpos)
    want = want + b.extra.drive(b.world, b.body, obs_b, b.timestep_ms)
    assert np.array_equal(got, want)


def test_each_population_gets_drive_only_when_its_state_says_so(orgs):
    from flyemu.internal_state import labellum_food
    _, _, org = orgs
    st = org.organs
    r = st.rows
    for k in ("isn", "ipc", "sugar_grn", "water_grn", "clock_morning", "clock_evening", "dfb"):
        assert r[k].size > 0, k
    o = st.organs
    o.akh = o.dilp = 0.5
    o.switch = False
    st._refresh()
    t = st.tonic()
    assert np.all(t[r["isn"]] == 0) and np.all(t[r["ipc"]] == 0) and np.all(t[r["dfb"]] == 0)
    clock = np.concatenate([r["clock_morning"], r["clock_evening"]])
    other = np.setdiff1d(np.arange(org.conn.n), clock)
    assert np.all(t[other] == 0)                              # only clock cells carry drive now
    o.akh, o.switch = 0.9, True                               # hungry, sleep switch on
    st._refresh()
    t = st.tonic()
    assert np.all(t[r["isn"]] > 0) and np.all(t[r["dfb"]] > 0) and np.all(t[r["ipc"]] == 0)
    o.akh, o.dilp = 0.1, 0.9                                  # sated
    st._refresh()
    assert np.all(st.tonic()[r["ipc"]] > 0) and np.all(st.tonic()[r["isn"]] == 0)
    # GRN gain: scales the taste drive already there, nothing without it
    base = np.zeros(org.conn.n, dtype=np.float32)
    base[r["sugar_grn"]] = 10.0
    o.akh = 0.5
    assert np.all(st.taste_extra(base) == 0)
    o.akh = 1.0
    ex = st.taste_extra(base)
    assert np.allclose(ex[r["sugar_grn"]], 10.0 * st.p["g_sugar_hunger"]) and np.all(ex[r["water_grn"]] == 0)
    # the organism path: advances the organs every update_ms; no food, no ingestion
    assert labellum_food(org) == (False, 0.0)
    t0 = o.t_s
    obs = org.body.observe()
    for s in range(int(st.update_ms / org.timestep_ms) + 1):
        org.sense(s, obs)
    assert o.t_s > t0 and o.crop_nl == 0.0


def test_pump_activity_scales_ingestion():
    """B17 (s10): ingestion = pump activity x contact; pump 0 -> nothing swallowed."""
    a, b, c = Organs(P), Organs(P), Organs(P)
    for o, pump in ((a, 1.0), (b, 0.5), (c, 0.0)):
        run(o, 30 / 3600, dt=1.0, food_sugar_M=0.2, touching_food=True, pump=pump)
    assert c.crop_nl == 0.0 and 0.4 < b.crop_nl / a.crop_nl < 0.6


@pytest.mark.skipif(not HAVE_GRAPH, reason="no graph cache")
def test_pump_gating_reads_the_pump_mns():
    from flyemu.organism import Organism
    org = Organism(policy="minimal", profile="m4", min_synapses=5,
                   overrides={"state:organs|model": 1.0, "state:crop|pump_gated": 1.0})
    st = org.organs
    t = org.conn.neurons.type.fillna("").to_numpy()
    assert set(t[st.pump_cells]) == {"MN11D", "MN11V", "MN12D"}
    for s in range(1000):                       # 100 ms, pump MNs at 100 Hz
        org._last_spiked = st.pump_cells if s % 100 == 0 else np.zeros(0, np.int64)
        st.drive(org, org.timestep_ms, np.zeros(org.conn.n, np.float32))
    assert st.pump_rate > 5.0


def test_sourced_values_are_neutral_off_and_inside_their_bounds():
    """s19: state:organs|values_from_sources = 0 leaves the s10 defaults; the sourced values sit in their bounds."""
    from flyemu import internal_state as S
    base = S.default_params()
    assert base == {r[0]: float(r[5]) for r in S.PARAMS}
    src = S.default_params(sourced=True)
    assert set(S.SOURCED) <= set(base)
    for f, (v, lo, hi, label, *_r) in S.SOURCED.items():
        assert lo <= v <= hi and src[f] == v, f
        assert label in {"measured", "derived", "inferred", "guessed"}, f
    assert {f: src[f] for f in base if f not in S.SOURCED} == {f: base[f] for f in base if f not in S.SOURCED}


def test_sleep_sourced_values_are_neutral_off_and_switch_the_threshold_form():
    """s20: state:sleep|values_from_sources = 0 leaves N25 as in s10; 1 sets the Abhilash values, 24 h cosine."""
    from flyemu import internal_state as S
    base, src = S.default_params(), S.default_params(sleep_sourced=True)
    for f, (v, lo, hi, label, *_r) in S.SLEEP_SOURCED.items():
        assert lo <= v <= hi and src[f] == v, f
        assert label in {"measured", "derived", "inferred", "guessed"}, f
    assert {f: src[f] for f in base if f not in S.SLEEP_SOURCED} == {f: base[f] for f in base
                                                                      if f not in S.SLEEP_SOURCED}
    assert "sleep_sourced" not in base and src["sleep_sourced"] == 1.0
    # at CT 6 the s10 drive is c_amp cos(pi) = -0.1 (12 h harmonic); the one-cycle drive is cos(pi/2) = 0
    for q, thr in ((base, base["th_hi"] - base["c_amp"]), (src, src["th_hi"])):
        o = S.Organs(q, z=complex(0.0, 1.0))          # ct = 6 h
        assert abs(o.ct_h - 6.0) < 1e-9
        o.pressure = thr + 0.004
        o.step(1.0, activity=1.0)
        assert o.switch, q.get("sleep_sourced")
        o2 = S.Organs(q, z=complex(0.0, 1.0)); o2.pressure = thr - 0.004
        o2.step(1.0, activity=1.0)
        assert not o2.switch


def test_homeostat_mode_is_neutral_off_and_its_rates_are_exact():
    """s22: state:sleep|homeostat = 0 leaves N25 as in s10; mode 1 is the ER5 need and 8 stochastic dFB cells."""
    from flyemu import internal_state as S
    base, hom = S.default_params(), S.default_params(homeostat=True)
    assert "homeostat" not in base and hom.pop("homeostat") == 1.0 and hom == base
    o = run(S.Organs(base), 6, activity=1.0)                  # mode 0: the dFB cells are never touched
    assert o.dfb_on.shape == (S.N_DFB,) and not o.dfb_on.any()
    q = S.default_params(homeostat=True)
    kr, g = q["dfb_restart_per_min"] / 60.0, q["need_gain"]
    k1, f0 = S.dfb_rates(q, 1.0, 0.0)
    k0, f1 = S.dfb_rates(q, 0.0, 1.0)
    assert np.isclose(k1, kr) and np.isclose(k0, kr / (1.0 + g))  # the measured restart is the rate at full need
    assert np.isclose(f1, f0 * (1.0 + q["light_arousal"]))
    # the exact two-state transition composes: two steps of dt equal one of 2 dt
    def m(dt):
        stay, turn = S.dfb_transition(k1, f0, dt)
        return np.array([[1 - turn, turn], [1 - stay, stay]])
    assert np.allclose(m(30.0) @ m(30.0), m(60.0))
    # the need rises awake and falls asleep
    o = S.Organs(q, pressure=0.2)
    run(o, 4, activity=1.0)
    hi = o.pressure
    assert hi > 0.2
    o.switch = True
    run(o, 2, activity=0.0)
    assert o.asleep and o.pressure < hi


def test_homeostat_drives_each_dfb_cell_by_its_own_state(orgs):
    _, _, org = orgs
    st, o, r = org.organs, org.organs.organs, org.organs.rows
    assert len(o.dfb_on) == len(r["dfb"])
    pattern = np.arange(len(r["dfb"])) % 2 == 0
    saved = (st.p.get("homeostat"), o.dfb_on.copy(), o.switch)
    try:
        st.p["homeostat"], o.dfb_on[:], o.switch = 1.0, pattern, False
        st._refresh()
        assert np.allclose(st.tonic()[r["dfb"]], st.p["g_dfb_mv"] * pattern)
    finally:
        if saved[0] is None:
            st.p.pop("homeostat", None)
        else:
            st.p["homeostat"] = saved[0]
        o.dfb_on[:], o.switch = saved[1], saved[2]
        st._refresh()
