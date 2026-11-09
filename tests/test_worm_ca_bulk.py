"""mech/capool.py's ca_bulk: cadifpmp (NEURON's radial-diffusion, buffer and pump pool, ported as nmodl/cabulk.mod) is
a readout only, so v and the Eq. 28 cai every channel reads are bit-identical to off; off is the default; under
cadifpmp the GCaMP readout reads the bulk pool, so it moves. The port's own checks (mass balance, linear decay against
the derived time constant, the readout chain's half-fall) are scripts/worm/debug2/ca_bulk_check.py port. NEURON is
one simulator per process: each brain runs in a subprocess."""
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
V, CA, G = [], [], []
for k in range(300):
    o = b.step()
    V.append(o.v_mV); CA.append(b._read(b._pc).copy()); G.append(b.mech_out["gcamp_dff"])
cb = b.mech_out.get("ca_bulk_uM")
print(json.dumps(dict(V=np.array(V).tolist(), CA=np.array(CA).tolist(), G=np.array(G).tolist(),
                 bulk=None if cb is None else [None if not np.isfinite(x) else float(x) for x in cb],
                 muscle=b.is_muscle.tolist(), tog=b.toggles.get("ca_bulk"))))
'''
REG = ("capool", "receptors", "observation")


def _run(toggles):
    env = dict(os.environ, PYTHONPATH=str(ROOT / "src"))
    tg = {"channel_noise": "off", "gcamp": "gcamp6s", "neuropal": "off", **toggles}
    r = subprocess.run([sys.executable, "-c", SCRIPT, json.dumps(CELLS), json.dumps(tg), json.dumps(list(REG))],
                       capture_output=True, text=True, env=env, cwd=ROOT, timeout=600)
    assert r.returncode == 0, r.stderr[-2000:]
    return json.loads(r.stdout.strip().splitlines()[-1])


def test_bulk_pool_is_a_readout_only():
    d = _run({})
    off = _run({"ca_bulk": "off"})
    on = _run({"ca_bulk": "cadifpmp"})
    assert d["tog"] in (None, "off") and d["bulk"] is None
    assert np.array_equal(np.array(d["G"]), np.array(off["G"]))
    assert np.array_equal(np.array(off["V"]), np.array(on["V"]))
    assert np.array_equal(np.array(off["CA"]), np.array(on["CA"]))
    mus = np.array(on["muscle"])
    assert all((x is None) == m for x, m in zip(on["bulk"], mus))       # a pool in every neuron soma, none in muscle
    assert all(0.0 < x < 100.0 for x in on["bulk"] if x is not None)
    g0, g1 = np.array(off["G"])[:, ~mus], np.array(on["G"])[:, ~mus]
    assert np.abs(g1 - g0).max() > 1e-3
