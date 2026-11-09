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
from wormemu.mech import metabolism as me
from wormemu.mech import organs_intestine as gi
from wormemu.mech import organs_other as oo
from wormemu.mech import organs_pharynx as ph
from wormemu.mech import pumps as pu

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
        r = m.step(SimpleNamespace(obs={"head": {"food_OD": od}}, outputs={}), 1.0)["out"]
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
        r = m.step(SimpleNamespace(outputs={}), 1.0)
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
            rel = max(rel, sum(r["out"]["peptide_release"].values()))
            anterior = np.setdiff1d(m.bwm, m.post_cells)
            assert not r["I_pA"][anterior].any()
        assert 0.0 < i_post <= q["pbo5_g_nS"] * 30.0 + 1e-9
        assert set(r["out"]["peptide_release"]) == {"nlp-40@anterior_body", "nlp-40@posterior_body"}
        assert np.allclose(m.nlp_W.sum(1), 1.0) and not m.nlp_W[gi.RING <= 4, 2:].any()
        assert not m.nlp_W[gi.RING >= 6, :2].any()           # rings by length overlap: 1-4 anterior, 6-9 posterior
        # total molecules/s = nM/s x neuromod's posterior-body volume (400 um2 x 269 um) x 0.602 per um3 per nM
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
    m = gl.Mech(brain, {}, {"glia_cells": "off", "glia_v0_window": "first", "glia_kbuffer": "fixed", "glia_kcc3": "fixed"})
    for _, r in _glia_run(m, names, [c for c in names if c.endswith("L")], t_end=3.0):
        assert "I_pA" not in r and "afd_gc_scale" not in r["out"]


def _glia_taus(brain, names, left, params):
    q = {**gl.defaults(), **params}
    taus, peaks = {}, {}
    for form in ("kir", "null"):
        m = gl.Mech(brain, params, {"glia_cells": "off", "glia_v0_window": "first", "glia_kbuffer": form, "glia_kcc3": "fixed"})
        rows = _glia_run(m, names, left)
        k = np.array([r["out"]["amphid_k_mM"] for _, r in rows]) - q["glia_k_bath_mM"]
        t = np.array([x for x, _ in rows])
        assert k[:, 1].max() == 0.0 and k[t <= 1.0].max() == 0.0          # right side untouched; no load in v0
        i = int(np.argmax(k[:, 0]))
        assert abs(t[i] - 2.0) < 0.01
        after = k[i:, 0] / k[i, 0]
        taus[form] = float(t[i + int(np.argmax(after < np.exp(-1.0)))] - t[i])
        peaks[form] = float(k[i, 0])
        if form == "kir":
            I = rows[i][1]["I_pA"]
            assert (I[[names.index(c) for c in left]] > 0).all() and not I[names.index("X1")]
    return taus, peaks, q


def test_glia_k_buffer_recovers_at_the_kir41_constants_and_keeps_sides_apart():
    brain, names = _glia_brain()
    left = [c for c in names if c.endswith("L") and c != "X1"]
    # limit: a vanishing neuronal K+ leak leaves only the glial uptake and diffusion constants
    taus, _, q = _glia_taus(brain, names, left, {"glia_k_gleak_nS": 1e-4})
    assert abs(taus["kir"] - 1.0 / (1 / q["glia_kir_tau_s"] + 1 / q["glia_k_diff_tau_s"])) < 0.05
    assert abs(taus["null"] - q["glia_k_diff_tau_s"]) < 0.05
    # default leak: a raised E_K cuts the neurons' K+ efflux, which clears the ending faster than the glia alone
    taus_d, peaks_d, _ = _glia_taus(brain, names, left, {})
    assert taus_d["kir"] < taus["kir"] and taus_d["null"] < taus["null"] and taus_d["kir"] <= taus_d["null"]
    assert 0.2 < peaks_d["kir"] < 12.0


def test_glia_kcc3_scale_is_one_at_rest_rises_in_the_null_and_with_ending_k():
    brain, names = _glia_brain()
    wt = gl.Mech(brain, {}, {"glia_cells": "off", "glia_v0_window": "first"})
    rest = _glia_run(wt, names, [], t_end=20.0)
    assert all(abs(r["out"]["afd_gc_scale"]["AFDL"] - 1.0) < 1e-9 for _, r in rest)
    null = gl.Mech(brain, {}, {"glia_cells": "off", "glia_v0_window": "first", "glia_kcc3": "null"})
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


def test_gap_per_contact_is_its_own_row():
    """wbrain2's Request (9 Nov 2026): organs_other's and glia's per-contact gaps are their own ledger rows; a removed
    branch would have replaced them with the brain's median gap_strength_per_pair when params lacked them."""
    def never(pid):
        raise AssertionError(f"read {pid}")
    sp = SimpleNamespace(led=object(), v=never)
    m = oo.Mech(SimpleNamespace(idx={}, spec=sp), {}, dict(other_cells="off"))
    assert m.q["other_gap_nS_per_contact"] == oo.defaults()["other_gap_nS_per_contact"]
    assert oo.Mech(SimpleNamespace(idx={}, spec=sp), {"other_gap_nS_per_contact": 0.4},
                   dict(other_cells="off")).q["other_gap_nS_per_contact"] == 0.4
    brain, _ = _glia_brain()
    brain.spec = sp
    g = gl.Mech(brain, {"glia_gap_nS_per_contact": 0.3}, {"glia_cells": "off", "glia_v0_window": "first"})
    assert g.q["glia_gap_nS_per_contact"] == 0.3
    assert gl.Mech(brain, {}, {"glia_cells": "off", "glia_v0_window": "first"}).q["glia_gap_nS_per_contact"] == \
        gl.defaults()["glia_gap_nS_per_contact"]


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


def _met(toggles=None, p=None):
    lay = SimpleNamespace(p=p or {"met_intake_per_pump": 1e-5, "met_store_tau_h": 24.0})
    return me.Mech(SimpleNamespace(layers=lay), {}, toggles or {})


def _met_ctx(pumps=0, food=0.0, T=20.0, extra=0.0):
    return SimpleNamespace(obs={"head": {"food_OD": food, "temperature_C": T}},
                           outputs={"pumps": pumps, "pump_atp_excess_J_per_d": extra})


def test_deb_std_is_abj_with_no_acceleration_interval():
    q = me.defaults()
    q2 = dict(q, deb_e_hj_J=q["deb_e_hb_J"])
    a, b = me.Deb(q2, accel=True), me.Deb(q, accel=False)
    for d in (a, b):
        d.E_0 = None
        d._E = d.solve_e0(1.0)
    ya, _ = a.integrate(a._E[1], 4.0, 1.0)
    yb, _ = b.integrate(b._E[1], 4.0, 1.0)
    assert np.allclose(ya, yb, rtol=1e-9, atol=0.0) and a.E_0 == b.E_0


def test_deb_reproduces_amp_predictions():
    """The port gives AmP's own predicted a_b, t_p and R_i for the entry (scripts/worm/organs/check_metabolism.py)."""
    q = me.defaults()
    d = me.Deb(q)
    E0, yb, ab = d.solve_e0(1.0)
    _, tp = d.integrate(yb, 10.0, 1.0, until=lambda y: y[2] >= q["deb_e_hp_J"])
    assert abs(ab / 0.3257 - 1) < 0.01 and abs(tp / 2.934 - 1) < 0.01
    assert abs(yb[0] / yb[1] ** 3 / d.E_m - 1.0) < 1e-6                      # maternal effect: e_b = f = 1


def test_store_form_is_brain_layers_metabolism():
    p = {"met_intake_per_pump": 1e-5, "met_store_tau_h": 24.0}
    m = _met({"metabolism": "store"}, p)
    old = SimpleNamespace(p=p, on={"metabolism"}, store=0.0)
    for k in range(5000):
        pumps = k % 3 == 0
        Layers.metabolism(old, pumps, 0.5)
        r = m.step(_met_ctx(pumps=pumps), 0.5)
        assert r["out"]["energy_store"] == old.store
    assert _met({"metabolism": "off"}).step(_met_ctx(), 0.5) == {}


def test_deb_closed_loop_starves_without_food_and_holds_when_fixed():
    fed, hungry = _met({"met_feeding": "fixed"}), _met()
    e0 = fed.last["energy_state"]
    assert abs(e0 - 1.0) < 1e-6 and fed.last["egg_production_per_h"] > 0.0
    for _ in range(20):
        a = fed.step(_met_ctx(), 1000.0)["out"]
        b = hungry.step(_met_ctx(), 1000.0)["out"]
    assert abs(a["energy_state"] - 1.0) < 1e-6 and a["deb"]["f"] == 1.0
    assert a["energy_fraction"] == min(a["energy_state"], 1.0) and b["energy_fraction"] == b["energy_state"]
    assert b["energy_state"] < 1.0 and b["deb"]["f"] == 0.0 and b["egg_production_per_h"] < a["egg_production_per_h"]
    # f from pumps x food: 4.2 Hz on saturating food tends to the Holling response
    m = _met()
    m.rate_hz = 4.2
    assert abs(m.feeding({"food_OD": 1e6}) - 1.0) < 1e-5 and m.feeding({"food_OD": 0.5}) == pytest.approx(0.5)
    assert _met({"met_feeding": "food"}).feeding({"food_OD": 0.5}) == pytest.approx(0.5)


def test_deb_temperature_and_pump_load():
    d = me.Deb(me.defaults())
    assert d.tc(20.0) == pytest.approx(1.0) and d.tc(25.0) > 1.0 > d.tc(15.0)
    m = _met({"met_feeding": "fixed"})
    y = m.y.copy()
    base = m.deb.fluxes(y, 1.0, 1.0, 0.0)[1]
    more = m.deb.fluxes(y, 1.0, 1.0, 1e-3)[1]
    assert more["pS"] == pytest.approx(base["pS"] + 1e-3)
    assert more["pA"] - more["pC"] < base["pA"] - base["pC"]                 # the reserve pays (kappa rule)


def test_metabolism_specs_have_ranges_and_labels():
    from bioemu.ledger import LABELS
    for s in me.SPECS:
        assert s.lo <= s.template <= s.hi and s.label in LABELS and s.source and s.unit, s.id


def _pump_run(form, v_fn, t_end_ms, dt=5.0, mus=(False, True)):
    m = pu.Mech(None, {}, {"na_k_pump": form})
    rows, k = [], 0
    while k * dt < t_end_ms:
        r = m.step(SimpleNamespace(v=v_fn(k * dt), is_muscle=np.array(mus)), dt)
        rows.append(r)
        k += 1
    return m, rows


def test_pump_is_neutral_at_rest_and_rest_form_is_silent():
    rest = lambda t: np.array([-60.0, -31.0])
    m, rows = _pump_run("on", rest, 5000.0)
    assert all(np.abs(r["out"]["pump_current_pA"]).max() < 1e-12 for r in rows)
    assert np.allclose(rows[-1]["out"]["na_i_mM"], pu.defaults()["pump_na_rest_mM"])
    step = lambda t: np.array([-60.0, -31.0]) + (20.0 if 2000 <= t < 4000 else 0.0)
    m, rows = _pump_run("rest", step, 6000.0)
    assert all(np.abs(r["out"]["pump_current_pA"]).max() == 0.0 for r in rows)
    assert len({round(r["out"]["pump_atp_J_per_d"], 15) for r in rows[300:]}) == 1
    assert pu.Mech(None, {}, {"na_k_pump": "off"}).step(SimpleNamespace(v=np.zeros(2)), 5.0) == {}


def test_pump_na_recovers_at_the_linearised_rate_and_null_loses_the_resting_current():
    q = pu.defaults()
    p = pu.Pump(q, [False])
    na0, v0 = q["pump_na_rest_mM"], -60.0
    slope = float((p.i_p(np.array([na0 + 1e-4]), v0) - p.i_p(np.array([na0 - 1e-4]), v0))[0] / 2e-4)
    tau_lin = q["pump_vol_neuron_um3"] / (3.0 * pu.NA_MM_PER_PA_S_UM3 * slope)
    m, _ = _pump_run("on", lambda t: np.array([-60.0]), 1005.0, mus=(False,))
    m.na = m.na + 0.01                                                 # a small Na load, then free recovery
    ctx = SimpleNamespace(v=np.array([-60.0]), is_muscle=np.array([False]))
    for _ in range(int(tau_lin * 1000 / 5.0)):
        m.step(ctx, 5.0)
    assert abs((m.na[0] - na0) / 0.01 - np.exp(-1.0)) < 0.01
    m, rows = _pump_run("null", lambda t: np.array([-60.0, -31.0]), 3000.0)
    ip_rest = pu.Pump(q, [False, True]).i_p(np.full(2, na0), np.array([-60.0, -31.0]))
    assert np.allclose(rows[-1]["I_pA"], ip_rest) and (rows[-1]["out"]["na_i_mM"] > na0).all()


def test_temperature_conductance_reaches_awa():
    """wbrain2's Request (9 Nov 2026): the conductance Q10 also multiplies AWA's Liu conductances (dens_awa_<c>);
    at T_ref every factor is exactly 1, so the default experiment (20 C) is unchanged."""
    from wormemu.mech import AWA_G_SCALE_NAMES, G_SCALE_NAMES
    from wormemu.mech import temperature as tm
    p = {s.id: s.template for s in tm.SPECS}
    m = tm.Mech(SimpleNamespace(cell_names=["A", "B", "C"]), p, {})
    for T, phi in ((p["temp_ref_C"], 1.0), (p["temp_ref_C"] + 10.0, p["temp_q10_conductance"])):
        m.reset()
        g = m.step(SimpleNamespace(obs={"head": {"temperature_C": T}}), 1.0)["g_scale"]
        assert set(g) == set(G_SCALE_NAMES) | set(AWA_G_SCALE_NAMES)
        assert all(np.array_equal(x, np.full(3, phi)) for x in g.values())


def test_pump_scale_does_not_depend_on_the_build():
    """A neuron's I_max and g_Na scale by its area over pump_area_median_um2 (the full brain's median), not over the
    median of the cells built (9 Nov 2026; wbrain2's Request): one cell's pump is the same alone and with others."""
    q = pu.defaults()
    vol, area = [80.0, 300.0, 1200.0, 500.0], [88.4, 267.2, 1133.4, 900.0]
    many = pu.Pump(q, [False, False, False, True], (vol, area))
    alone = pu.Pump(q, [False], (vol[:1], area[:1]))
    assert alone.imax[0] == many.imax[0] == q["pump_imax_neuron_pA"] * area[0] / q["pump_area_median_um2"]
    assert alone.gna[0] == many.gna[0] and alone.vol[0] == many.vol[0] == vol[0]
    assert many.imax[3] == q["pump_imax_muscle_pA"] and many.vol[3] == q["pump_vol_muscle_um3"]


def test_pump_specs_have_ranges_and_labels():
    from bioemu.ledger import LABELS
    for s in pu.SPECS:
        assert s.lo <= s.template <= s.hi and s.label in LABELS and s.source and s.unit, s.id


ALL_B2 = r"""
import json, numpy as np
from wormemu import mech
B2 = ["muscle_bwm", "organs_pharynx", "organs_intestine", "organs_egglaying", "glia", "organs_other", "pumps",
      "metabolism"]
for m in B2:
    if m not in mech.REGISTRY:
        mech.REGISTRY.append(m)
from wormemu.brain import Brain
cells = ["AFDL", "AFDR", "AWCL", "ASEL", "RMEL", "RMER", "CEPDL", "PVDL", "CANL", "ALA", "HSNL", "HSNR", "VC03",
         "VC04", "AVL", "DVB", "dBWML1", "dBWMR1", "vBWML1", "dBWML8", "dBWMR8"]
b = Brain(cells=cells)
b.reset()
names = sorted(type(m).__module__.rsplit(".", 1)[1] for m in b.mechs)
fin = True
for _ in range(100):
    o = b.step(None, 5.0)
    fin = fin and bool(np.isfinite(o.v_mV).all())
mo = b.mech_out
keys = ["energy_state", "egg_production_per_h", "pressure_kPa", "coelomocyte_uptake_per_s", "afd_gc_scale",
        "amphid_k_mM", "na_i_mM", "pump_atp_J_per_d", "o2_pmol_per_min", "eggs_laid", "pumps", "expulsions"]
print(json.dumps({"mods": names, "finite": fin, "missing": [k for k in keys if k not in mo],
                  "e": mo.get("energy_state"), "eggs_h": mo.get("egg_production_per_h"),
                  "P": mo.get("pressure_kPa")}))
"""


def test_all_b2_modules_build_and_step_together_in_a_small_brain():
    r = _run(ALL_B2)
    assert r["finite"] and not r["missing"], r
    for m in ("glia", "metabolism", "organs_egglaying", "organs_other", "pumps"):
        assert m in r["mods"], r["mods"]
    assert 0.99 < r["e"] <= 1.0 + 1e-9 and r["eggs_h"] > 0.0 and abs(r["P"] - 40.0) < 1e-6


_PH_5HT = """
import json, sys
import numpy as np
from wormemu import brain as B
from wormemu.mech import neuromod as nm, organs_pharynx as ph
out = {}
for form in ("compartments", "lumped"):
    b = B.Brain(B.sample_worm(None), toggles={"monoamines": form}, cells=["NSML", "NSMR", "MCL", "MCR"])
    b.reset()
    p = next(m for m in b.mechs if isinstance(m, ph.Mech))
    n = next((m for m in b.mechs if isinstance(m, nm.Mech)), None)
    b.extra_pA[[b.idx["NSML"], b.idx["NSMR"]]] = 40.0
    for _ in range(300):
        b.step(None, 1.0)
    ref = float(n.ma.nM()[nm.AMINES.index("serotonin"), n.ma_comp[b.idx["NSML"]]]) if n is not None and n.on[nm.A] else None
    out[form] = dict(src=p._ser[0], c=p.serotonin_nM(), ref=ref, out=b.mech_out.get("pharynx_5ht_nM"))
print(json.dumps(out))
"""


def test_pharynx_reads_serotonin_from_neuromod_and_falls_back_to_the_layer():
    """wbody2 item 2 (A): with neuromod's monoamines on, the pharyngeal muscle's 5-HT is neuromod's pool at NSM
    (the layer's pool stays 0 then); with monoamines lumped it is brain_layers' pool."""
    r = _run(_PH_5HT)
    assert r["compartments"]["src"] == "neuromod" and r["compartments"]["c"] > 0
    assert r["compartments"]["c"] == r["compartments"]["ref"] == r["compartments"]["out"]
    assert r["lumped"]["src"] == "layer"


_PH_ROUTE = """
import json
from wormemu import brain as B
from wormemu.mech import organs_pharynx as ph
out = {}
for route in ("cook", "eat2", "both"):
    b = B.Brain(B.sample_worm(None), toggles={"ph_mc_route": route}, cells=["MCL", "MCR"])
    p = next(m for m in b.mechs if isinstance(m, ph.Mech))
    mc, seg, own = {b.idx["MCL"], b.idx["MCR"]}, {}, {id(x) for x in p.wsyn}
    for pp, pre, post, c in b.wsyn:
        if id(pp) in own and pre in mc:
            n = pp.get_segment().sec.name().replace("pharynx_", "")
            seg[n] = seg.get(n, 0.0) + pp.gmax
    out[route] = dict(seg=seg, n_eat2=len(p.eat2_syn))
print(json.dumps(out))
"""


def test_pharynx_mc_route_moves_mc_contacts_to_the_bordering_pm5():
    """ph_mc_route (wbody2, item 2 stage 2 port): cook puts MC's synapses on the mc2 marginal cells only; eat2 puts the
    same total conductance on pm5 cells only (each mc2 cell's share over its pm5 gap partners); both half each way."""
    r = _run(_PH_ROUTE)
    cook, eat2, both = (r[k]["seg"] for k in ("cook", "eat2", "both"))
    tot = sum(cook.values())
    assert tot > 0 and all(n.startswith("mc2") for n in cook) and r["cook"]["n_eat2"] == 0
    assert all(n.startswith("pm5") for n in eat2) and r["eat2"]["n_eat2"] > 0
    assert abs(sum(eat2.values()) - tot) < 1e-9 * tot
    for g in ("mc2", "pm5"):
        assert abs(sum(v for n, v in both.items() if n.startswith(g)) - tot / 2) < 1e-9 * tot
