"""Worker B2's mechanisms (src/wormemu/mech/muscle_*, organs_*, glia, metabolism, pumps): unit checks against one
published measurement each, and the nested simpler forms' neutral-equivalence and limit tests. NEURON runs in a
subprocess (one simulator per process)."""
import json
import os
import subprocess
import sys
from pathlib import Path
from types import SimpleNamespace

import numpy as np
import pytest

from wormemu.brain_layers import Layers
from wormemu.interface import BWM_NAMES
from wormemu.mech import muscle_bwm as mb
from wormemu.mech import organs_egglaying as ge
from wormemu.mech import glia as gl
from wormemu.mech import organs_intestine as gi
from wormemu.mech import organs_other as oo
from wormemu.mech import organs_pharynx as ph

ROOT = Path(__file__).resolve().parents[1]
DU_DATA = Path(os.environ.get("DU_MUSCLE_REPO", "/tmp/worgans/C.elegans-Muscle")) / "data" / "spikes.npy"


def _run(code, *args):
    env = dict(os.environ, PYTHONPATH=str(ROOT / "src"))
    r = subprocess.run([sys.executable, "-c", code, *args], capture_output=True, text=True, env=env, timeout=600)
    assert r.returncode == 0, r.stderr[-3000:]
    return json.loads(r.stdout.strip().splitlines()[-1])


# --- row 12 ---------------------------------------------------------------------------------------------------
def test_du_muscle_reproduces_the_recording():
    """Du 2025's WT cell, the paper's protocol: 4, 4, 3, 3 APs at 30, 25, 20, 15 pA (the recording's counts), rest
    within 5 mV of -31 mV, peaks above +20 mV."""
    V, ca, t = mb.du_step_protocol()
    want = (4, 4, 3, 3)
    if DU_DATA.exists():
        rec = np.load(DU_DATA)
        want = tuple(mb.upcrossings(rec[:, i]) for i in range(4))
    for i in range(4):
        assert abs(mb.upcrossings(V[:, i]) - want[i]) <= 1
        assert abs(V[t < 57, i].mean() + 31.0) < 5.0 and V[:, i].max() > 20.0
    assert np.all(np.isfinite(ca)) and ca.min() >= 0


def _fake_brain():
    return SimpleNamespace(h=None, bwm=np.arange(len(BWM_NAMES)), mact=False)


def _v_drive(n=4000):
    rng = np.random.default_rng(0)
    return -45.0 + 30.0 * np.sin(np.arange(n)[:, None] / 300.0 + rng.uniform(0, 6, len(BWM_NAMES)))


def test_nested_old_muscle_layer_is_equivalent():
    """muscle_ca=sigmoid + muscle_activation=rise_decay on the passive muscle = brain_layers' lumped layer exactly."""
    p = {s.id: s.template for s in __import__("wormemu.brain_layers", fromlist=["SPECS"]).SPECS}
    old = SimpleNamespace(p=p, on={"muscle_ca", "muscle_activation"}, act=np.zeros(len(BWM_NAMES)))
    m = mb.Mech(_fake_brain(), p, {"bwm_membrane": "off", "muscle_ca": "sigmoid", "muscle_activation": "rise_decay",
                                   "bwm_gap_liu": "off"})
    for v in _v_drive():
        a_old = Layers.muscle_activation(old, v, 1.0)
        a_new = m.step(SimpleNamespace(v=v), 1.0)["act_add"]
        assert np.array_equal(a_old, a_new)


def test_bbc2012_is_rise_decay_in_the_equal_tau_small_dt_limit():
    p = {"mact_tau_rise_ms": 100.0, "mact_tau_decay_ms": 100.0}
    tg = {"bwm_membrane": "off", "muscle_ca": "sigmoid", "bwm_gap_liu": "off"}
    a = mb.Mech(_fake_brain(), p, dict(tg, muscle_activation="bbc2012"))
    b = mb.Mech(_fake_brain(), p, dict(tg, muscle_activation="rise_decay"))
    worst = 0.0
    for v in _v_drive()[:, :]:
        x = a.step(SimpleNamespace(v=v), 0.5)["act_add"]
        y = b.step(SimpleNamespace(v=v), 0.5)["act_add"]
        worst = max(worst, float(np.abs(x - y).max()))
    assert worst < 2e-3


def test_activation_off_is_zero():
    m = mb.Mech(_fake_brain(), {}, {"bwm_membrane": "off", "muscle_ca": "off", "muscle_activation": "off",
                                    "bwm_gap_liu": "off"})
    assert not m.step(SimpleNamespace(v=_v_drive(1)[0]), 1.0)["act_add"].any()


DU_NRN = """
import json, numpy as np
from neuron import h
from wormemu.mech import muscle_bwm as mb, organs_nrn
organs_nrn.load_organ_mods(h); h.load_file("stdrun.hoc")
q = {s.id: s.template for s in mb.SPECS}
h.dt, h.secondorder = 0.01, 0
sec = h.Section(name="m"); sec.L, sec.diam = 20.0, 5.0; sec.insert("du_bwm")
ar = organs_nrn.area_um2(sec); mb.configure(sec, q, ar); sec(0.5).du_bwm.published_init = 1
sec.cm = q["bwm_du_c_pF"] * 100.0 / ar
st = h.IClamp(sec(0.5)); st.delay, st.dur, st.amp = 57.8, 200.0, 30.0 / 0.75 / 1000
h.finitialize(-30.0); vv = []
while h.t < 300 - 1e-9:
    h.fadvance(); vv.append(sec(0.5).v)
vv = np.array(vv)
print(json.dumps(((np.flatnonzero((vv[:-1] < 0) & (vv[1:] >= 0)) + 1) * 0.01).tolist()))
"""


def test_du_mod_matches_the_numpy_reference():
    """The NEURON mod and the CPU reference are the same equations: spike times within 1 ms at dt 0.01 ms."""
    nrn = np.array(_run(DU_NRN))
    V, _, t = mb.du_step_protocol(amps_pA=(30.0,), dt=0.01, t_end=300.0)
    ref = (np.flatnonzero((V[:-1, 0] < 0) & (V[1:, 0] >= 0)) + 1) * 0.01
    assert len(nrn) == len(ref) == 4
    assert np.abs(nrn - ref).max() < 1.0


# --- row 13 ---------------------------------------------------------------------------------------------------
PH_AP = """
import json
from neuron import h
from wormemu.mech import organs_nrn, organs_pharynx as P
organs_nrn.load_organ_mods(h)
q = P.defaults()
t, v, ca = P.ap_protocol(h, q, 42.0, dt=0.5)
f = P.ap_features(t, v)
f["ca"] = float(ca.max())
t0, v0, _ = P.ap_protocol(h, q, 30.0, dt=0.5, t_end=400.0)
f["sub_peak"] = float(v0.max())
print(json.dumps(f))
"""


def test_pharynx_ap_matches_sherman_harel_table3():
    """One isolated compartment, 40 ms step just above threshold, dt 0.5 ms: rest -73 +- 1 mV, peak 34 +- 3 mV, total
    duration 100-250 ms, plateau 20-30 mV, undershoot below -67 mV (TB recordings, S&H Table 3); 30 pA does not fire."""
    f = _run(PH_AP)
    assert -74 <= f["rest"] <= -72 and 31 <= f["peak"] <= 37 and 100 <= f["duration"] <= 250
    assert 20 <= f["plateau"] <= 30 and f["undershoot"] <= -67 and f["ca"] > 1e-5
    assert f["sub_peak"] < -20


def _ph_clock(q, on=True):
    return SimpleNamespace(p=q, on={"pharynx"} if on else set(), pump_phase=0.0, pumps=0)


def test_pharynx_clock_form_is_brain_layers_pharynx():
    """pharynx=clock reproduces brain_layers' lumped oscillator exactly (activation and pumps, food on and off)."""
    q = ph.defaults()
    old = _ph_clock(q)
    m = ph.Mech(SimpleNamespace(), q, {"pharynx": "clock"})
    for k in range(6000):
        od = 0.5 if k < 3000 else 0.0
        a_old, n_old = Layers.pharynx(old, od, 1.0)
        r = m.step(SimpleNamespace(obs={"head": {"food_OD": od}}), 1.0)["out"]
        assert r["pumps"] == n_old and float(r["pharynx_activation"][0]) == a_old
    assert m.pumps_total == old.pumps >= 9


def test_pharynx_activation_limits():
    q = ph.defaults()
    assert ph.activation(np.array([0.0]), q)[0] == 0.0
    assert abs(ph.activation(np.array([q["ph_sh_k1_b_M"]]), q)[0] - 0.5) < 1e-12
    assert ph.activation(np.array([1.0]), q)[0] > 0.999


def test_pharynx_off_is_silent():
    m = ph.Mech(SimpleNamespace(), ph.defaults(), {"pharynx": "off"})
    r = m.step(SimpleNamespace(obs={}), 1.0)["out"]
    assert r["pumps"] == 0 and not r["pharynx_activation"].any()


# --- row 14: intestine and defecation ---------------------------------------------------------------------------
def _gut_brain(t0_ms=1234.0):
    """Enough of a brain for the intestine Mech without NEURON: 302 neurons named n0.., AVL and DVB, then the BWM."""
    names = [f"n{k}" for k in range(300)] + ["AVL", "DVB"] + list(BWM_NAMES)
    bp = np.tile(np.linspace(0.0, 1.0, 24), 4)[:len(BWM_NAMES)]
    q = gi.defaults()
    layers = SimpleNamespace(bwm_pos=bp, dmp_t=t0_ms, p=dict(q))
    return SimpleNamespace(cell_names=names, bwm=np.arange(302, 302 + len(BWM_NAMES)), layers=layers,
                           idx={n: i for i, n in enumerate(names)}), q


def test_intestine_wave_runs_posterior_to_anterior_and_itr1_null_is_flat():
    """Coarse (dt 5 ms) version of check_intestine.py: period near 49 s, int9 first, the wave reaches int1-int2;
    IP3R flux 0 leaves no transient (Dal Santo 1999)."""
    t, C, _, _ = gi.run_isolated(None, 300.0, 5.0, every=2)
    r9 = C[:, gi.RING == 9].mean(1)
    r2 = C[:, gi.RING == 2].mean(1)
    thr = r9.min() + 0.5 * (r9.max() - r9.min())
    up9 = t[1:][(r9[1:] >= thr) & (r9[:-1] < thr)]
    up2 = t[1:][(r2[1:] >= thr) & (r2[:-1] < thr)]
    assert len(up9) >= 5 and 45.0 <= np.diff(up9[1:]).mean() <= 52.0
    assert len(up2) >= 4 and 0.0 < up2[1] - up9[1] < 40.0
    _, Cn, _, _ = gi.run_isolated(None, 300.0, 5.0, ip3r=0.0, every=2)
    assert np.ptp(Cn[t > 20.0], axis=0).max() < 0.01 * np.ptp(r9)          # relaxes to rest, no transient


def test_pbo5_half_open_at_ph50_and_cleft_rests_at_rest_ph():
    q = gi.defaults()
    cl = gi.Cleft(q)
    assert abs(cl.ph - q["int_cleft_ph_rest"]) < 1e-12
    cl.dh = 10.0 ** (-q["pbo5_ph50"]) * 1e9 - 10.0 ** (-q["int_cleft_ph_rest"]) * 1e9
    assert abs(cl.ph - q["pbo5_ph50"]) < 1e-9 and abs(cl.p_open() - 0.5) < 1e-9


def test_defecation_timer_form_is_brain_layers_defecation():
    """defecation=timer reproduces brain_layers' clock exactly (boost, enteric activation, expulsions)."""
    brain, q = _gut_brain()
    m = gi.Mech(brain, q, {"defecation": "timer"})
    old = SimpleNamespace(p=q, on={"defecation"}, dmp_t=brain.layers.dmp_t, bwm_pos=brain.layers.bwm_pos)
    n_exp = 0
    for _ in range(100000):
        b0, e0, x0 = Layers.defecation(old, 1.0)
        r = m.step(SimpleNamespace(), 1.0)
        assert np.array_equal(r["act_add"], b0) and np.array_equal(r["out"]["enteric_activation"], e0)
        assert r["out"]["expulsions"] == x0
        n_exp += x0
    assert n_exp == 3                                       # at 4, 49 and 94 s from t0 = 1.234 s


def test_defecation_off_is_silent_and_ip3r_drives_posterior_bwm_and_avl_dvb():
    brain, q = _gut_brain()
    off = gi.Mech(brain, q, {"defecation": "off"})
    r = off.step(SimpleNamespace(), 1.0)
    assert "I_pA" not in r and r["out"]["expulsions"] == 0 and not r["out"]["enteric_activation"].any()
    v = np.full(len(brain.cell_names), -30.0)
    for form in ("release_only", "direct"):
        m = gi.Mech(brain, q, {"defecation": "ip3r", "enteric_muscle": "off", "nlp40_aex2": form})
        ctx = SimpleNamespace(v=v, outputs={})
        i_post, i_aex, rel = 0.0, 0.0, 0.0
        for _ in range(60000):                                # 60 s at 1 ms: at least one wave
            r = m.step(ctx, 1.0)
            i_post = max(i_post, float(r["I_pA"][m.post_cells].max()))
            i_aex = max(i_aex, float(r["I_pA"][m.aex2_cells].max()))
            rel = max(rel, r["out"]["peptide_release"]["nlp-40@posterior_body"])
            anterior = np.setdiff1d(m.bwm, m.post_cells)
            assert not r["I_pA"][anterior].any()
        assert 0.0 < i_post <= q["pbo5_g_nS"] * 30.0 + 1e-9
        assert set(r["out"]["peptide_release"]) == {"nlp-40@posterior_body"}
        # molecules/s = nM/s x neuromod's posterior-body volume (400 um2 x 269 um) x 0.602 molecules per um3 per nM
        assert 0.0 < rel <= q["nlp40_release_nM_per_s"] * 400.0 * 269.0 * 0.602214 * (1 + 1e-9)
        if form == "direct":
            assert 0.0 < i_aex <= q["aex2_gain_pA"]
        else:
            assert i_aex == 0.0                               # neuromod applies AEX-2, not this module


# --- row 15: egg-laying circuit (organs_egglaying) ------------------------------------------------------------------
def _egg_brain(seed=7):
    names = ["HSNL", "HSNR"] + [f"n{k}" for k in range(10)]
    p = dict(ge._OLD)
    layers = SimpleNamespace(p=p, rng=np.random.default_rng(seed))
    return SimpleNamespace(cell_names=names, idx={n: i for i, n in enumerate(names)}, layers=layers), p


def test_egg_laying_timer_form_is_brain_layers_egg_laying():
    """egg_laying=timer draws the same states and eggs as brain_layers' two-state timer from the same generator."""
    brain, p = _egg_brain()
    m = ge.Mech(brain, {}, {"egg_laying": "timer"})
    old = SimpleNamespace(p=p, on={"egg_laying"}, rng=np.random.default_rng(7), egg_active=False, egg_t_next=0.0,
                          egg_vm_t=-1e9)
    t, laid = 0.0, 0
    for _ in range(200000):                                    # 200 min at 60 ms
        r = m.step(SimpleNamespace(t_ms=t), 60.0)
        a0, e0 = Layers.egg_laying(old, t + 60.0, 60.0)
        assert r["out"]["eggs_laid"] == e0 and np.all(r["out"]["sex_muscle_activation"] == a0)
        laid += e0
        t += 60.0
    assert laid > 0


def test_egg_laying_off_is_silent():
    brain, _ = _egg_brain()
    r = ge.Mech(brain, {}, {"egg_laying": "off"}).step(SimpleNamespace(t_ms=0.0), 1.0)
    assert "I_pA" not in r and r["out"]["eggs_laid"] == 0 and not r["out"]["sex_muscle_activation"].any()


def test_unc103_density_keeps_an_undriven_vulval_muscle_at_rest():
    """The fitted UNC-103 (Kr) density holds the Du membrane at rest with no input; without it the cell fires on its
    own (the gate Collins & Koelle 2013 describe)."""
    q = ge.defaults()
    counts = {}
    for gkr in (q["egg_unc103_gkr_nS"], 0.0):
        mu = mb.DuMuscle(1, {"bwm_du_gkr_nS": gkr})
        v = np.empty(20000)
        for k in range(20000):                                 # 4 s at 0.2 ms
            mu.step(np.zeros(1), 0.2)
            v[k] = mu.V[0]
        counts[gkr] = mb.upcrossings(v[5000:])
    assert counts[q["egg_unc103_gkr_nS"]] == 0 and counts[0.0] >= 5


def test_egg_specs_have_ranges_and_labels():
    from bioemu.ledger import LABELS
    ids = [s.id for s in ge.SPECS]
    assert len(ids) == len(set(ids))
    for s in ge.SPECS:
        assert s.lo <= s.template <= s.hi and s.label in LABELS, s.id


# --- row 11: glia (glia) --------------------------------------------------------------------------------------------
def _glia_brain():
    from wormemu.brain_layers import AMPHID
    names = sorted(AMPHID) + ["X1", "X2"]
    return SimpleNamespace(idx={c: i for i, c in enumerate(names)}, cell_names=names, spec=None), names


def _glia_run(m, names, drive_cells, t_drive=(1.0, 2.0), t_end=30.0, dt=5.0, v_rest=-60.0, v_on=-40.0):
    rows, t = [], 0.0
    while t < t_end * 1000.0:
        v = np.full(len(names), v_rest)
        if t_drive[0] * 1000.0 <= t < t_drive[1] * 1000.0:
            v[[names.index(c) for c in drive_cells]] = v_on
        r = m.step(SimpleNamespace(t_ms=t, v=v, outputs={}), dt)
        t += dt
        rows.append((t / 1000.0, r))
    return rows


def test_glia_fixed_forms_are_silent():
    brain, names = _glia_brain()
    m = gl.Mech(brain, {}, {"glia_cells": "off", "glia_kbuffer": "fixed", "glia_kcc3": "fixed"})
    for _, r in _glia_run(m, names, [c for c in names if c.endswith("L")], t_end=3.0):
        assert "I_pA" not in r and "afd_gc_scale" not in r["out"]


def test_glia_k_buffer_recovers_at_the_kir41_constants_and_keeps_sides_apart():
    brain, names = _glia_brain()
    left = [c for c in names if c.endswith("L") and c != "X1"]
    q = gl.defaults()
    taus = {}
    for form in ("kir", "null"):
        m = gl.Mech(brain, {}, {"glia_cells": "off", "glia_kbuffer": form, "glia_kcc3": "fixed"})
        rows = _glia_run(m, names, left)
        k = np.array([r["out"]["amphid_k_mM"] for _, r in rows]) - q["glia_k_bath_mM"]
        t = np.array([x for x, _ in rows])
        assert k[:, 1].max() == 0.0 and k[t <= 1.0].max() == 0.0          # right side untouched; no load in v0
        i = int(np.argmax(k[:, 0]))
        assert abs(t[i] - 2.0) < 0.01
        after = k[i:, 0] / k[i, 0]
        taus[form] = float(t[i + int(np.argmax(after < np.exp(-1.0)))] - t[i])
        if form == "kir":
            I = rows[i][1]["I_pA"]
            assert (I[[names.index(c) for c in left]] > 0).all() and not I[names.index("X1")]
    assert abs(taus["kir"] - 1.0 / (1 / q["glia_kir_tau_s"] + 1 / q["glia_k_diff_tau_s"])) < 0.05
    assert abs(taus["null"] - q["glia_k_diff_tau_s"]) < 0.05


def test_glia_kcc3_scale_is_one_at_rest_rises_in_the_null_and_with_ending_k():
    brain, names = _glia_brain()
    wt = gl.Mech(brain, {}, {"glia_cells": "off"})
    rest = _glia_run(wt, names, [], t_end=20.0)
    assert all(abs(r["out"]["afd_gc_scale"]["AFDL"] - 1.0) < 1e-9 for _, r in rest)
    null = gl.Mech(brain, {}, {"glia_cells": "off", "glia_kcc3": "null"})
    s = _glia_run(null, names, [], t_end=30.0)[-1][1]["out"]["afd_gc_scale"]
    q = gl.defaults()
    want = (1 + (q["glia_cl_bath_mM"] + q["glia_kcc3_dcl_mM"]) / q["glia_gcy8_cl_ic50_mM"]) / \
        (1 + q["glia_cl_bath_mM"] / q["glia_gcy8_cl_ic50_mM"])
    assert want > 1.0 and abs(s["AFDL"] - want) < 1e-9 and abs(s["AFDR"] - want) < 1e-9
    wt.reset()
    left = [c for c in names if c.endswith("L") and c != "X1"]
    rows = _glia_run(wt, names, left, t_drive=(1.0, 6.0), t_end=6.0)
    s = rows[-1][1]["out"]["afd_gc_scale"]
    assert s["AFDL"] > 1.0 and abs(s["AFDR"] - 1.0) < 1e-9             # K+ at the left ending slows KCC-3


def test_glia_specs_have_ranges_and_labels():
    from bioemu.ledger import LABELS
    for s in gl.SPECS:
        assert s.lo <= s.template <= s.hi and s.label in LABELS and s.source and s.unit, s.id


def _other(**toggles):
    return oo.Mech(SimpleNamespace(idx={}, spec=None), {}, dict(other_cells="off", **toggles))


def _other_run(m, s, dt_s=1.0, obs=None):
    ctx = SimpleNamespace(obs=obs, outputs={})
    return [m.step(ctx, dt_s * 1000.0)["out"] for _ in range(int(s / dt_s))]


def test_excretory_fixed_form_holds_the_setpoint_and_canal_holds_it_at_rest():
    q = oo.defaults()
    for form in ("fixed", "off", "canal", "on"):
        o = _other_run(_other(excretory_osmo=form), 3600.0)[-1]
        assert abs(o["pressure_kPa"] - q["osmo_p_set_kPa"]) < 1e-9 and abs(o["body_fluid_volume_rel"] - 1.0) < 1e-12


def test_excretory_null_fills_at_the_analytic_rate_and_canal_corrects_a_hypertonic_shift():
    q = oo.defaults()
    lp, E, ps = q["osmo_lp_per_kPa_s"], q["osmo_e_vol_kPa"], q["osmo_p_set_kPa"]
    dpi = oo.RT_KPA_PER_MOSM * q["osmo_dosm_mOsm"]
    v_inf = 1.0 + (dpi - ps) / E
    tau = 1.0 / (lp * E)
    o = _other_run(_other(excretory_osmo="null"), tau, dt_s=10.0)[-1]
    assert abs((o["body_fluid_volume_rel"] - 1.0) / (v_inf - 1.0) - (1.0 - np.exp(-1.0))) < 1e-3
    # 30 mOsm extra outside: the body shrinks, the canal stops bailing (it cannot pump water in), no NaN
    hyper = {"head": {"osmolarity_mOsm": 30.0}}
    o = _other_run(_other(excretory_osmo="canal"), 3600.0, dt_s=10.0, obs=hyper)[-1]
    assert o["body_fluid_volume_rel"] < 1.0 and o["pressure_kPa"] < ps and np.isfinite(o["pressure_kPa"])


def test_coelomocyte_clearance_is_count_times_cell_clearance_over_volume():
    q = oo.defaults()
    k = q["cc_count"] * q["cc_clearance_um3_per_s"] / q["cc_pc_volume_um3"]
    assert abs(k - 1.0e-3) < 1e-4
    assert _other_run(_other(), 1.0)[-1]["coelomocyte_uptake_per_s"] == pytest.approx(k)
    assert _other_run(_other(coelomocytes="null"), 1.0)[-1]["coelomocyte_uptake_per_s"] == 0.0
    assert "coelomocyte_uptake_per_s" not in _other_run(_other(coelomocytes="off"), 1.0)[-1]


def test_other_specs_have_ranges_and_labels():
    from bioemu.ledger import LABELS
    for s in oo.SPECS:
        assert s.lo <= s.template <= s.hi and s.label in LABELS and s.source and s.unit, s.id
