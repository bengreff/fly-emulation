"""The worm brain (src/wormemu/brain.py): sample_worm draws, and a small NEURON brain on a cell subset.

NEURON is one simulator per process, so each brain runs in its own subprocess."""
import json
import os
import subprocess
import sys
from pathlib import Path

import numpy as np
import pytest

from wormemu.brain import sample_worm

ROOT = Path(__file__).resolve().parents[1]
CELLS = ["ALML", "ALMR", "AVM", "PLML", "PLMR", "AVAL", "AVAR", "AVBL", "AVBR", "PVCL", "PVCR", "DA01", "DD01",
         "VB01", "dBWML6", "dBWML7", "dBWMR6", "dBWMR7"]

SCRIPT = """
import json, sys, numpy as np
from wormemu.brain import Brain, sample_worm
cells, toggles, seed = json.loads(sys.argv[1]), json.loads(sys.argv[2]), json.loads(sys.argv[3])
b = Brain(sample_worm(seed), toggles=toggles, cells=cells)
def run():
    b.reset()
    eca, dmp = b.soma[0](0.5).eca, b.layers.dmp_t
    V, A = [], []
    for k in range(400):
        b.extra_pA[:5] = 20.0 if 150 <= k < 300 else 0.0
        o = b.step()
        V.append(o.v_mV); A.append(o.muscle_activation)
    return eca, dmp, np.array(V), np.array(A), o
eca, dmp, V, A, o = run()
_, dmp2, V2, _, _ = run()
print(json.dumps(dict(eca=eca, finite=bool(np.isfinite(V).all()), vmin=float(V.min()), vmax=float(V.max()),
    same=bool(np.array_equal(V, V2)), shift=float(np.abs(V[200:300, 5:].mean(0) - V[50:150, 5:].mean(0)).max()),
    placed=dict(b.placed), n=len(b.cell_names), n_act=len(o.muscle_activation), amax=float(A.max()), dmp=[dmp, dmp2])))
"""


def _run(toggles, seed=None):
    env = dict(os.environ, PYTHONPATH=str(ROOT / "src"))
    r = subprocess.run([sys.executable, "-c", SCRIPT, json.dumps(CELLS), json.dumps(toggles), json.dumps(seed)],
                       capture_output=True, text=True, env=env, cwd=ROOT, timeout=600)
    assert r.returncode == 0, r.stderr[-2000:]
    return json.loads(r.stdout.strip().splitlines()[-1])


def test_sample_worm():
    t, a, b = sample_worm(None), sample_worm(7), sample_worm(7)
    assert t.v("salt_gain_pA") == t.led.parameters.set_index("param_id").value_template["salt_gain_pA"]
    assert a.v("salt_gain_pA") == b.v("salt_gain_pA") != t.v("salt_gain_pA")      # guessed: drawn, reproducibly
    assert a.v("kin_cca1_vhm") == t.v("kin_cca1_vhm")                              # published fit: fixed
    assert (a.v("dens_shl1") == t.v("dens_shl1")).all()
    assert (a.v("wire_chem_contacts") == t.v("wire_chem_contacts")).all()          # structure: fixed
    s, s0 = a.v("syn_strength_per_pair"), t.v("syn_strength_per_pair")             # one shared factor per row
    lo, hi = a.led.parameters.set_index("param_id").loc["syn_strength_per_pair", ["bio_min", "bio_max"]]
    free = (s > lo) & (s < hi)
    assert free.any() and np.allclose((s / s0)[free], (s / s0)[free].iloc[0])
    e = a.v("mpas_epas")                                                           # guessed elements, per element
    lo, hi = a.led.parameters.set_index("param_id").loc["mpas_epas", ["bio_min", "bio_max"]]
    assert e.nunique() > 1 and e.between(lo, hi).all()
    assert (a.v("pas_soma_cm") == t.v("pas_soma_cm")).all()                       # derived (9 Nov fill): fixed


@pytest.mark.parametrize("toggles", [
    dict(wiring="cook", receptor_sign="on", bwm_coupling="on", bwm_gap_liu="off", innexin_identity="on"),
    dict(wiring="baaiworm", literature_overrides="off"),
])
def test_small_brain(toggles):
    r = _run(toggles)
    assert r["finite"] and r["same"] and r["n"] == len(CELLS) and r["n_act"] == 95
    assert -100 < r["vmin"] and r["vmax"] < 60
    assert r["shift"] >= 1.0                       # the touch input reaches an unstimulated cell
    if toggles["wiring"] == "cook":
        assert r["placed"]["syn_nmj"] > 0 and r["placed"]["gap_bwm"] > 0
        assert 120 < r["eca"] < 140                # the Ca units fix (literature_overrides on)
    else:
        assert "syn_mn" in r["placed"] or "syn_nmj" in r["placed"]


def test_drawn_brain_runs():
    r = _run(dict(wiring="cook"), seed=3)
    assert r["finite"] and r["same"]


def test_template_layers_fixed():
    """The template worm's stochastic layers (defecation phase, egg-laying times, GCaMP noise) replay across brains
    and resets; before 5 Nov an unseeded generator gave every template run its own defecation phase."""
    a, b = _run(dict(wiring="cook")), _run(dict(wiring="cook"))
    assert a["dmp"][0] == a["dmp"][1] == b["dmp"][0]


def test_proprio_senses_anterior():
    """B-type neurons sense curvature anterior of the soma (Wen et al. 2012; ledger J12): a ventral bend in the front
    half excites VB and inhibits DB there, and a B neuron whose field lies wholly behind the bend gets nothing."""
    code = """
import json, numpy as np
from wormemu import mech
mech.REGISTRY[:] = []          # unit test of brain_layers' lumped proprio form (senses_proprio's nested "lumped")
from wormemu.brain import Brain, sample_worm
from wormemu.interface import BodyToBrain
b = Brain(sample_worm(None), toggles=dict(wiring="cook", sens_proprio="on"), cells=["VB03", "DB02", "VB11"])
o = BodyToBrain()
o.curvature_per_mm = np.where(o.s < 0.3, -5.0, 0.0)
I = b.layers.sensory_current(vars(o), 1.0)
print(json.dumps({n: [float(I[b.idx[n]]), float(b.layers.pos[b.idx[n]])] for n in ["VB03", "DB02", "VB11"]}))
"""
    env = dict(os.environ, PYTHONPATH=str(ROOT / "src"))
    r = subprocess.run([sys.executable, "-c", code], capture_output=True, text=True, env=env, cwd=ROOT, timeout=600)
    assert r.returncode == 0, r.stderr[-2000:]
    x = json.loads(r.stdout.strip().splitlines()[-1])
    assert x["VB03"][0] > 0 > x["DB02"][0]
    assert x["VB11"][1] - 0.4 > 0.3 and x["VB11"][0] == 0.0       # field (0.4 long) starts behind the bend


def test_muscle_active():
    """muscle_active on: c302's muscle membrane at c302's own values, finite and reproducible in a small brain."""
    r = _run(dict(wiring="cook", muscle_active="on", bwm_membrane="off", muscle_ca="sigmoid"))
    assert r["finite"] and r["same"] and -100 < r["vmin"] and r["vmax"] < 60
    code = """
import json
from neuron import h
from wormemu.brain import Brain, sample_worm, MUSCLE_ACTIVE
b = Brain(sample_worm(None), toggles=dict(wiring="cook", muscle_active="on", bwm_membrane="off", muscle_ca="sigmoid"), cells=["DA01", "dBWML6"])
seg, ref = b.soma[b.idx["dBWML6"]](0.5), h.Section(name="ref")
nml = {("Leak", "gmax"): 2e-6, ("Leak", "e"): -20.0, ("k_slow_muscle", "gmax"): 4.5833751019872582e-4,
       ("k_fast_muscle", "gmax"): 4.2711643917483308e-5, ("ca_boyle_muscle", "gmax"): 8.12775772264702e-4,
       ("CaPoolMuscle", "decayConstant"): 60.811870945509265, ("CaPoolMuscle", "rho"): 0.002238919e-8}
worst = 0.0
for mod, pars in MUSCLE_ACTIVE.items():
    ref.insert(mod)
    for name in pars:
        want = nml.get((mod, name), getattr(getattr(ref(0.5), mod), name))     # else the generated mod's default
        worst = max(worst, abs(getattr(getattr(seg, mod), name) - want) / abs(want))
print(json.dumps(dict(worst=worst, passive=hasattr(seg, "pas"))))
"""
    env = dict(os.environ, PYTHONPATH=str(ROOT / "src"))
    p = subprocess.run([sys.executable, "-c", code], capture_output=True, text=True, env=env, cwd=ROOT, timeout=600)
    assert p.returncode == 0, p.stderr[-2000:]
    x = json.loads(p.stdout.strip().splitlines()[-1])
    assert x["worst"] < 1e-5 and not x["passive"]          # the generated mods round to 6 significant figures


def test_gap_rectification():
    """gap_rectification on: AVAL-DA01 junctions pass current from the motor neuron into AVAL at the full conductance
    and back at 1 / gap_rect_ratio of it (Liu 2017), conserving current; off, symmetric."""
    code = """
import json
from wormemu import mech
mech.REGISTRY[:] = []          # the junction alone: registered mechanisms (pumps, Q10, receptors) would move the voltages
from wormemu.brain import Brain, sample_worm
out = {}
for tg in ("off", "on"):
    b = Brain(sample_worm(None), toggles=dict(wiring="cook", gap_rectification=tg), cells=["AVAL", "DA01"])
    b.reset()
    gaps = [pp for pp in b.conn if "gap" in pp.hname()]
    ava, da = b.soma[b.idx["AVAL"]], b.soma[b.idx["DA01"]]
    for name, va, vd in (("mn_high", -40.0, -30.0), ("ava_high", -30.0, -40.0)):
        for sec, v in ((ava, va), (da, vd)):
            for seg in (s for x in sec.wholetree() for s in x):
                seg.v = v
        b.h.fcurrent()
        out[tg + name] = [abs(sum(pp.i for pp in gaps)), sum(abs(pp.i) for pp in gaps)]
    out[tg + "placed"] = dict(b.placed)
    out["ratio"] = sample_worm(None).v("gap_rect_ratio")
print(json.dumps(out))
"""
    env = dict(os.environ, PYTHONPATH=str(ROOT / "src"))
    p = subprocess.run([sys.executable, "-c", code], capture_output=True, text=True, env=env, cwd=ROOT, timeout=600)
    assert p.returncode == 0, p.stderr[-2000:]
    x = json.loads(p.stdout.strip().splitlines()[-1])
    assert x["onplaced"].get("gap_nn_rect", 0) > 0 and "gap_nn_rect" not in x["offplaced"]
    for k in ("offmn_high", "offava_high", "onmn_high", "onava_high"):
        assert x[k][0] < 1e-12 * x[k][1]                   # the two halves carry equal and opposite currents
    assert x["offmn_high"][1] == pytest.approx(x["offava_high"][1])
    assert x["onmn_high"][1] == pytest.approx(x["offmn_high"][1])                    # motor neuron -> AVAL: full
    assert x["onava_high"][1] == pytest.approx(x["offava_high"][1] / x["ratio"])    # AVAL -> motor neuron
