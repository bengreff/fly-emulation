"""The run's noise seed (wbrain2, 9 Nov 2026; FIT_GENERAL section 7, common random numbers): Brain(noise_seed=)
seeds quantal and channel noise, brain_layers and the observation noise; None is the worm's seed, so nothing
changes by default; the NeuroPAL labelling stays the worm's; Experiment.noise_seed reaches the Brain. The full
check against the code before the change is scripts/worm/debug2/noise_seed_check.py. NEURON is one simulator per
process: each brain runs in a subprocess."""
import json
import os
import subprocess
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]

SUB = """
import json, numpy as np
from wormemu.brain import Brain, sample_worm
b = Brain(sample_worm(3), cells=["AWAL", "AIYL", "AIZL", "AIBL", "RIAL", "AVAL"]{kw})
b.reset()
v = []
for k in range(200):
    b.extra_pA[b.idx["AWAL"]] = 20.0 if 20 <= k < 120 else 0.0
    v.append(b.step().v_mV.tolist())
print(json.dumps(dict(v=v, seed=b.noise_seed, ids=np.asarray(b.mech_out["neuropal_id"]).tolist())))
"""

EXP = """
import json
from wormemu import brain, datamodel as D
seen = {}
class Stop(Exception):
    pass
def fake(spec, **kw):
    seen.update(kw)
    raise Stop
brain.Brain = fake
for ns in (None, 11):
    try:
        D.simulate(None, D.Experiment(duration_ms=5, seed=3, noise_seed=ns))
    except Stop:
        pass
    seen[str(ns)] = seen.pop("noise_seed", "missing")
print(json.dumps(seen))
"""


def _run(code):
    env = dict(os.environ, PYTHONPATH=str(ROOT / "src"))
    r = subprocess.run([sys.executable, "-c", code], capture_output=True, text=True, env=env, cwd=ROOT, timeout=900)
    assert r.returncode == 0, r.stderr[-2000:]
    return json.loads(r.stdout.strip().splitlines()[-1])


def test_noise_seed_default_is_the_worm_seed_and_changes_only_the_noise():
    dflt, same, other = (_run(SUB.format(kw=kw)) for kw in ("", ", noise_seed=3", ", noise_seed=7"))
    assert dflt["seed"] == 3 and same["seed"] == 3 and other["seed"] == 7
    assert np.array_equal(np.array(dflt["v"]), np.array(same["v"]))     # None = the worm's seed, bit for bit
    assert np.abs(np.array(other["v"]) - np.array(dflt["v"])).max() > 1e-3   # another noise seed: other noise
    assert dflt["ids"] == other["ids"]                                     # the NeuroPAL labelling is the worm's


def test_experiment_passes_the_noise_seed():
    seen = _run(EXP)
    assert seen["None"] is None and seen["11"] == 11


GUARD = """
import json
from wormemu.brain import Brain
b = Brain(cells=["AWAL", "AIYL"])
try:
    b.step()
    msg = "no error"
except RuntimeError as e:
    msg = str(e)
b.reset()
b.step()
print(json.dumps(dict(msg=msg, t=b.t)))
"""


def test_step_before_reset_is_a_clear_error():
    r = _run(GUARD)                       # was: noise's Poisson draw failed on the unset states ("lam value too large")
    assert "before Brain.reset()" in r["msg"] and r["t"] == 1.0
