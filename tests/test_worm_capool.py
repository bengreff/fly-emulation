"""mech/capool.py: ca_pool_units=off is the brain without the module (not built), and total_current sets each neuron
soma's vcell to V_cell / (10 A_soma), leaves muscles alone and makes the Ca pool move. The steady-state check against
Nicoletti 2019 Eq. 28 is scripts/worm/capool_unit_check.py. NEURON is one simulator per process: each brain runs in a
subprocess."""
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
print(json.dumps(dict(V=np.array(V).tolist(), CA=np.array(CA).tolist(), vcell=vc, area=ar,
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
    assert "wormemu.mech.capool" not in off["mechs"] and "wormemu.mech.capool" in on["mechs"]
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
