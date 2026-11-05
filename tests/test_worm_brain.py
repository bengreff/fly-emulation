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
    eca = b.soma[0](0.5).eca
    V, A = [], []
    for k in range(400):
        b.extra_pA[:5] = 20.0 if 150 <= k < 300 else 0.0
        o = b.step()
        V.append(o.v_mV); A.append(o.muscle_activation)
    return eca, np.array(V), np.array(A), o
eca, V, A, o = run()
_, V2, _, _ = run()
print(json.dumps(dict(eca=eca, finite=bool(np.isfinite(V).all()), vmin=float(V.min()), vmax=float(V.max()),
    same=bool(np.array_equal(V, V2)), shift=float(np.abs(V[200:300, 5:].mean(0) - V[50:150, 5:].mean(0)).max()),
    placed=dict(b.placed), n=len(b.cell_names), n_act=len(o.muscle_activation), amax=float(A.max()))))
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
    cm = a.v("pas_soma_cm")                                                        # guessed elements, per element
    lo, hi = a.led.parameters.set_index("param_id").loc["pas_soma_cm", ["bio_min", "bio_max"]]
    assert cm.nunique() > 1 and cm.between(lo, hi).all()


@pytest.mark.parametrize("toggles", [
    dict(wiring="cook", receptor_sign="on", bwm_coupling="on"),
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


def test_proprio_senses_anterior():
    """B-type neurons sense curvature anterior of the soma (Wen et al. 2012; ledger J12): a ventral bend in the front
    half excites VB and inhibits DB there, and a B neuron whose field lies wholly behind the bend gets nothing."""
    code = """
import json, numpy as np
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
