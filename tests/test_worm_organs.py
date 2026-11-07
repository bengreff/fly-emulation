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
