"""mech/ca_volume (row 6): each neuron's bulk Ca pool sized by its own volume; the fixed form is neutral.

NEURON is one simulator per process, so each brain runs in its own subprocess."""
import json
import os
import subprocess
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
CELLS = ["AVAL", "AIYL", "AWCL", "dBWML6"]

SCRIPT = """
import json, sys
from wormemu import mech
drop, toggles = json.loads(sys.argv[1]), json.loads(sys.argv[2])
if drop:
    mech.REGISTRY.remove("ca_volume")
from wormemu.brain import Brain, sample_worm
from wormemu.mech import ca_volume, capool
b = Brain(sample_worm(None), toggles=toggles, cells=json.loads(sys.argv[3]))
b.reset()
V, CA = [], []
for k in range(300):
    b.extra_pA[:] = 20.0 if 100 <= k < 200 else 0.0
    o = b.step()
    V.append(o.v_mV.tolist())
    CA.append([b.soma[i](0.5).cai for i in range(len(b.cell_names))])
i = b.idx["AVAL"]
area = sum(s.area() for s in b.soma[i])
print(json.dumps(dict(V=V, CA=CA, names=b.cell_names, vols=ca_volume.volumes(b, i),
                      v_eff=b.soma[i](0.5).cainternm.vcell * capool.MA_CM2_TO_PA_UM2 * area,
                      muscle_vcell=b.soma[b.idx["dBWML6"]](0.5).cainternm.vcell
                      if hasattr(b.soma[b.idx["dBWML6"]](0.5), "cainternm") else None)))
"""


def _run(drop, toggles):
    env = dict(os.environ, PYTHONPATH=str(ROOT / "src"))
    r = subprocess.run([sys.executable, "-c", SCRIPT, json.dumps(drop), json.dumps(toggles), json.dumps(CELLS)],
                       capture_output=True, text=True, env=env, cwd=ROOT, timeout=600)
    assert r.returncode == 0, r.stderr[-2000:]
    return json.loads(r.stdout.strip().splitlines()[-1])


def test_fixed_form_neutral():
    """ca_pool_volume = fixed is the ledger's one V_cell: identical voltages and Ca to a brain without the module."""
    a, b = _run(True, {}), _run(False, dict(ca_pool_volume="fixed"))
    assert np.array_equal(np.array(a["V"]), np.array(b["V"])) and np.array_equal(np.array(a["CA"]), np.array(b["CA"]))
    assert np.isclose(b["v_eff"], 31.16)


def test_whole_cell_and_soma_forms():
    """Default whole_cell sizes AVAL's pool by its whole-cell volume, soma by its soma; muscles keep B2's pool; the
    pool size changes the Ca under drive."""
    w, s, f = _run(False, {}), _run(False, dict(ca_pool_volume="soma")), _run(False, dict(ca_pool_volume="fixed"))
    assert np.isclose(w["v_eff"], w["vols"][0]) and np.isclose(s["v_eff"], s["vols"][1])
    assert w["vols"][1] < w["vols"][0]
    assert w["muscle_vcell"] == f["muscle_vcell"]
    k = w["names"].index("AVAL")
    ex = {n: np.array(r["CA"])[:, k].max() - 0.05 for n, r in (("w", w), ("s", s), ("f", f))}
    assert np.isfinite(np.array(w["CA"])).all() and ex["s"] > ex["w"] > 0 and not np.isclose(ex["w"], ex["f"])


def test_neuromorpho_form():
    """The alternative reconstruction: AVAL's pool takes Nicoletti 2024's NeuroMorpho volume (129.6 um3)."""
    n = _run(False, dict(ca_pool_volume="neuromorpho"))
    assert np.isclose(n["v_eff"], 129.6)
