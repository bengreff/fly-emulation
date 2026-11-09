"""brain.step's conductance route (wbrain2, 9 Nov 2026; weki's LGC-55 item): a module returning G_nS and GE_pA gives
the soma g (E - V) at the present V, the same as a SensG at e placed directly, and stays stable at a 4 ms exchange
step at a conductance where the held I_pA form diverges. The full check is scripts/worm/debug2/implicit_g_check.py.
NEURON is one simulator per process, so each brain runs in a subprocess."""
import json
import os
import subprocess
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]

SCRIPT = '''
import json, sys, types, numpy as np
from wormemu import mech
FORM, E, G = "{form}", -41.0, 4.15
d = types.ModuleType("dummy_g")
d.MECHANISMS = [("dummy_g", "Test: a constant conductance onto one soma", "test", "on")]
d.SPECS = []
class Mech:
    def __init__(self, brain, params, toggles):
        self.n = len(brain.cell_names)
        if FORM == "pp":
            self.pp = brain.h.SensG(brain.soma[0](0.5))
            self.pp.e, self.pp.g = E, 0.0
    def reset(self):
        pass
    def step(self, ctx, dt_ms):
        g = G if ctx.t_ms >= 100.0 else 0.0
        if FORM == "pp":
            self.pp.g = g * 1e-3
            return {{}}
        x = np.full(self.n, g)
        return {{"G_nS": x, "GE_pA": x * E}}
d.Mech = Mech
sys.modules["dummy_g"] = d
mech.REGISTRY.append("dummy_g")
from wormemu.brain import Brain
b = Brain(cells=["HSNL"], toggles=dict(quantal_noise="off", channel_noise="off"))
b.reset()
v = [float(b.step(None, 4.0).v_mV[0]) for _ in range(150)]
g_on = float(b._gs[0].g)
b.reset()
print(json.dumps(dict(v=v, g_on=g_on, g_reset=float(b._gs[0].g))))
'''


def _run(form):
    env = dict(os.environ, PYTHONPATH=str(ROOT / "src"))
    r = subprocess.run([sys.executable, "-c", SCRIPT.format(form=form)], capture_output=True, text=True, env=env,
                       cwd=ROOT, timeout=600)
    assert r.returncode == 0, r.stderr[-2000:]
    return json.loads(r.stdout.strip().splitlines()[-1])


def test_conductance_route_is_implicit():
    g, pp = _run("g"), _run("pp")
    v, vp = np.array(g["v"]), np.array(pp["v"])
    assert np.max(np.abs(v - vp)) < 1e-6                     # g (E - V) through G and G x E = a SensG at e
    assert np.isfinite(v).all() and np.abs(v[-50:] + 41.0).max() < 2.0   # stable at 4 ms, settles near E
    assert abs(g["g_on"] - 4.15e-3) < 1e-12 and g["g_reset"] == 0.0     # uS on the soma's SensG; reset clears it
