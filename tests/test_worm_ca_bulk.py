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


OUTWARD = '''
import json, numpy as np
from wormemu import brain as wb
h = wb._neuron()
h.celsius = 6.3
s = h.Section(name="soma")
s.L = s.diam = 2.82
for m in ("pas", "egl19", "cabulk"):
    s.insert(m)
seg = s(0.5)
seg.pas.g, seg.pas.e, seg.egl19.gbegl19, seg.cabulk.ca0 = 5e-5, -90.0, 0.01, 0.05
h.caom_cabulk = 2.0
clamp = h.SEClamp(seg)
clamp.rs, clamp.dur1 = 1e-3, 1e9
h.dt, h.secondorder = 0.5, 0
out = {}
for arm in ("open", "none"):                     # after a load at -20 mV, +90 mV (above EGL-19's 60 mV reversal)
    seg.egl19.gbegl19 = 0.01                     # with the channel kept, or removed after the switch's first step
    clamp.amp1 = -90.0                           # (that step's ica is still from v at -20 mV: fadvance's order)
    h.finitialize(-90.0)
    C, I = [], []
    for v, n in ((-20.0, 400), (90.0, 400)):
        clamp.amp1 = v
        for k in range(n):
            h.fadvance()
            C.append(seg.cabulk.cabmem); I.append(seg.ica)
            if v > 0 and k == 0 and arm == "none":
                seg.egl19.gbegl19 = 0.0
    out[arm] = dict(cabmem=C, ica=I)
print(json.dumps(out))
'''


def test_outward_ica_is_not_an_efflux():
    """BAAIWorm's Ca channels reverse at a fixed 60 mV, so above it their ica is outward; cabulk takes only inward Ca
    (cainternm's rule). Fed the outward ica, the solver stopped (weki's AIY x 0.627 at +35 pA): ca[0] drained to 0."""
    env = dict(os.environ, PYTHONPATH=str(ROOT / "src"))
    r = subprocess.run([sys.executable, "-c", OUTWARD], capture_output=True, text=True, env=env, cwd=ROOT, timeout=300)
    assert r.returncode == 0, r.stderr[-2000:]
    d = json.loads(r.stdout.strip().splitlines()[-1])
    up, none = d["open"], d["none"]
    assert min(up["ica"][401:]) > 0 and max(none["ica"][401:]) == 0     # outward through the channel, or no current
    assert np.array_equal(up["cabmem"][:401], none["cabmem"][:401])     # the same load
    assert min(up["cabmem"]) > 0
    assert np.array_equal(up["cabmem"], none["cabmem"])                 # an outward ica takes no Ca out
