"""Row 26 (mech/noise.py): quantal_noise=off with channel_noise=off is the brain without the module (qn = 1 is
neutral in wsyn.mod), each form runs finite in the brain and changes it, and the Specs are inside their bounds. The
generators' own checks are scripts/worm/noise_unit_check.py and chnoise_unit_check.py. Quantal noise reaches the
organ modules' synapses (post -1), which they append after noise is built. NEURON is one simulator per process: each
brain runs in a subprocess."""
import json
import os
import subprocess
import sys

import numpy as np

from test_worm_neuromod import ROOT, _run
from wormemu.mech import noise as NZ

WITHOUT = ("receptors", "plasticity", "slow_signalling", "learning", "neuromod")
WITH = WITHOUT + ("noise",)


def test_off_is_without_module():
    none = _run(dict(), reg=WITHOUT)
    off = _run(dict(quantal_noise="off", channel_noise="off"), reg=WITH)
    V0, V1 = np.array(none["V"]), np.array(off["V"])
    assert np.abs(V0 - V1).max() < 1e-12
    assert "wormemu.mech.noise" not in off["mechs"] and off["noise"] == {}   # off: not built (registry contract)


def test_quantal_runs_and_acts():
    on = _run(dict(channel_noise="off"), reg=WITH)
    off = _run(dict(quantal_noise="off", channel_noise="off"), reg=WITH)
    V1, V0 = np.array(on["V"]), np.array(off["V"])
    assert np.isfinite(V1).all() and np.abs(V1).max() < 200
    assert np.abs(V1 - V0).max() > 1e-3
    nz = on["noise"]
    assert nz["vesicles_per_s"] > 0 and 0 < nz["qn_sd"] < 100


def test_channel_runs_and_acts():
    on = _run(dict(quantal_noise="off"), reg=WITH)
    off = _run(dict(quantal_noise="off", channel_noise="off"), reg=WITH)
    V1, V0 = np.array(on["V"]), np.array(off["V"])
    assert np.isfinite(V1).all() and np.abs(V1).max() < 200
    assert np.abs(V1 - V0).max() > 1e-3
    cn = on["chnoise"]
    assert cn["I_rms_pA"] > 0 and cn["channels_median"] > 0


def test_specs_and_form():
    for s in NZ.SPECS:
        assert s.lo <= s.template <= s.hi, s.id
        assert s.label in ("measured", "derived", "inferred", "guessed", "published_fit"), s.id
    assert NZ.form(None) == "off" and NZ.form("quantal") == "quantal"
    assert NZ.cform("on") == "diffusion" and NZ.cform(None) == "off"


ORGAN = '''
import json
from wormemu.brain import Brain
b = Brain(cells=["HSNL", "HSNR", "VC04", "VC05", "AVBL"])
b.reset()
q = next(m.q for m in b.mechs if type(m).__module__ == "wormemu.mech.noise")
for _ in range(100):
    b.step(None, 1.0)
post = [j for _, _, j, _ in b.wsyn]
org = [i for i, j in enumerate(post) if j < 0]
print(json.dumps(dict(n=len(b.wsyn), nq=len(q.shot.gq), org=len(org), mask=[bool(q.to_muscle[i]) for i in org],
                      qn=[float(b.wsyn[i][0].qn) for i in org], gd=[float(b.wsyn[i][0].gd) for i in org])))
'''


def test_quantal_reaches_organ_synapses():
    """The egg-laying module's HSN and VC synapses onto the vulval muscles get quantal noise (default registry)."""
    r = subprocess.run([sys.executable, "-c", ORGAN], capture_output=True, text=True, cwd=ROOT, timeout=600,
                       env=dict(os.environ, PYTHONPATH=str(ROOT / "src")))
    assert r.returncode == 0, r.stderr[-2000:]
    o = json.loads(r.stdout.strip().splitlines()[-1])
    assert o["org"] > 0 and o["nq"] == o["n"]
    assert not any(o["mask"])                            # post -1 is an organ cell, not one of the brain's muscles
    assert any(g > 0 and q != 1.0 for g, q in zip(o["gd"], o["qn"]))
