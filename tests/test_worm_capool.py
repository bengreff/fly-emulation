"""mech/capool.py: ca_pool_units=off is the brain without the module's effect, and total_current sets each neuron
soma's vcell to V_cell / (10 A_soma), leaves muscles alone and makes the Ca pool move. slo_ca_source: single_channel
(the default) is neutral; tuner_gbar sets each SLO cell's gsc to its summed SLO density (DEBUG_TRIAGE item 4). The
steady-state check against Nicoletti 2019 Eq. 28 is scripts/worm/capool_unit_check.py. kcnl_density: network (the
default) keeps cell_param's gbkcnl, tuner zeroes it (night file 8 Nov, KCNL). NEURON is one simulator per
process: each brain runs in a subprocess."""
import json
import os
import subprocess
import sys

import numpy as np

from test_worm_neuromod import CELLS, ROOT

SCRIPT = '''
import json, sys, numpy as np
from wormemu import mech
cells, toggles, reg = json.loads(sys.argv[1]), json.loads(sys.argv[2]), json.loads(sys.argv[3])
mech.REGISTRY[:] = reg
from wormemu.brain import Brain
b = Brain(toggles=toggles, cells=cells)
b.reset()
for c, a in (("AVBL", 40.0), ("ASHL", 30.0)):
    b.extra_pA[b.idx[c]] = a
V, CA = [], []
for k in range(300):
    o = b.step()
    V.append(o.v_mV); CA.append(o.ca_uM)
vc = [[float(sg.cainternm.vcell) if hasattr(sg, "cainternm") else None for sg in s] for s in b.soma]
ar = [float(sum(sg.area() for sg in s)) for s in b.soma]
SLO = ("slo1_egl19", "slo1_unc2", "slo2_egl19", "slo2_unc2")
gsc = [[float(getattr(s(0.5), m).gsc) for m in SLO if hasattr(s(0.5), m)] for s in b.soma]
gb = [sum(float(getattr(getattr(s(0.5), m), "gbslo" + m[3])) for m in SLO if hasattr(s(0.5), m)) for s in b.soma]
print(json.dumps(dict(V=np.array(V).tolist(), CA=np.array(CA).tolist(), vcell=vc, area=ar, gsc=gsc, gb=gb,
                 muscle=b.is_muscle.tolist(), mechs=[type(m).__module__ for m in b.mechs])))
'''


def _run(toggles, reg):
    env = dict(os.environ, PYTHONPATH=str(ROOT / "src"))
    r = subprocess.run([sys.executable, "-c", SCRIPT, json.dumps(CELLS), json.dumps(toggles), json.dumps(list(reg))],
                       capture_output=True, text=True, env=env, cwd=ROOT, timeout=600)
    assert r.returncode == 0, r.stderr[-2000:]
    return json.loads(r.stdout.strip().splitlines()[-1])


def test_off_is_without_module_and_total_scales():
    none = _run(dict(), reg=("receptors",))
    off = _run(dict(ca_pool_units="off"), reg=("capool", "receptors"))
    on = _run(dict(), reg=("capool", "receptors"))
    assert np.abs(np.array(none["V"]) - np.array(off["V"])).max() < 1e-12
    assert "wormemu.mech.capool" in on["mechs"]           # off is built too (slo_ca_source is on) but inert
    for v0, v1, a, m in zip(off["vcell"], on["vcell"], on["area"], on["muscle"]):
        for x0, x1 in zip(v0, v1):
            if x0 is None:
                continue
            assert abs(x1 - (x0 if m else x0 / (10.0 * a))) < 1e-12 * x0
    ex0 = np.array(off["CA"])[:, ~np.array(off["muscle"])] - 0.05
    ex1 = np.array(on["CA"])[:, ~np.array(on["muscle"])] - 0.05
    V1 = np.array(on["V"])
    assert np.isfinite(V1).all() and np.abs(V1).max() < 200
    assert ex1.max() > 10 * ex0.max() > 0


def test_slo_ca_source_neutral_and_tuner():
    d = _run(dict(), reg=("capool", "receptors"))
    sc = _run(dict(slo_ca_source="single_channel"), reg=("capool", "receptors"))
    tu = _run(dict(slo_ca_source="tuner_gbar"), reg=("capool", "receptors"))
    assert np.array_equal(np.array(d["V"]), np.array(sc["V"]))
    assert all(x == 0.04 for g in d["gsc"] for x in g)
    has = [i for i, g in enumerate(tu["gsc"]) if g and tu["gb"][i] > 0]
    assert has and all(np.allclose(tu["gsc"][i], tu["gb"][i]) for i in has)
    assert not np.allclose(np.array(tu["V"])[:, has], np.array(d["V"])[:, has])


KCNL = '''
import json, sys, re
from wormemu import mech
mech.REGISTRY[:] = ["capool"]
from wormemu.brain import Brain
b = Brain(toggles=json.loads(sys.argv[1]), cells=["AVAL", "AIYL", "AFDL"])
h = b.h
g = {c: [float(sg.kcnl.gbkcnl) for sec in o.all if h.ismembrane("kcnl", sec=sec) for sg in sec]
     for c, o in zip(b.cell_names, b.cells)}
print(json.dumps(g))
'''


def test_kcnl_density_network_and_tuner():
    """network (the default) keeps cell_param's gbkcnl (AVAL 0.005, AIYL 0.00063, AFDL 0); tuner zeroes it."""
    env = dict(os.environ, PYTHONPATH=str(ROOT / "src"))
    out = {}
    for form in ("network", "tuner"):
        r = subprocess.run([sys.executable, "-c", KCNL, json.dumps(dict(kcnl_density=form))],
                           capture_output=True, text=True, env=env, cwd=ROOT, timeout=600)
        assert r.returncode == 0, r.stderr[-2000:]
        out[form] = json.loads(r.stdout.strip().splitlines()[-1])
    net, tun = out["network"], out["tuner"]
    assert net["AVAL"] and all(x == 0.005 for x in net["AVAL"])
    assert net["AIYL"] and all(x == 0.00063 for x in net["AIYL"])
    assert all(x == 0.0 for x in net["AFDL"])
    assert all(x == 0.0 for c in tun for x in tun[c]) and tun["AVAL"]
