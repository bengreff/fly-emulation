"""The brain's synapse gains reach synapses a mechanism places (wbrain2, 9 Nov 2026; wbody2's Request 23:52): the
organ modules append wsyn synapses onto non-brain cells to brain.wsyn with post -1, so the gain table is built after
the mechanisms, the presynaptic release gain reaches them, and no per-cell receptor gain does (post -1 would read the
last brain cell's). NEURON is one simulator per process, so the brain runs in a subprocess."""
import json
import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

SCRIPT = '''
import json, sys, types, numpy as np
from wormemu import mech
d = types.ModuleType("dummy_organ_syn")
d.MECHANISMS = [("dummy_organ_syn", "Test: one wsyn from AVAL onto a non-brain section, and fixed gains", "test", "on")]
d.SPECS = []
class Mech:
    def __init__(self, brain, params, toggles):
        h = brain.h
        self.sec = h.Section(name="dummy_organ_cell")
        self.sec.insert("pas")
        self.pp = h.wsyn(self.sec(0.5))
        h.setpointer(brain.soma[brain.idx["AVAL"]](0.5)._ref_v, "vpre", self.pp)
        self.pp.gmax, self.pp.mode = 1e-4, 0
        brain.wsyn.append((self.pp, brain.idx["AVAL"], -1, mech.RECEPTOR_CLASSES.index("glr")))
        self.n, self.i = len(brain.cell_names), brain.idx["AVAL"]
    def reset(self):
        pass
    def step(self, ctx, dt_ms):
        rel = np.ones(self.n); rel[self.i] = 2.0
        rec = np.ones(self.n); rec[-1] = 3.0
        return dict(g_scale={"release": rel, "rec_glr": rec})
d.Mech = Mech
sys.modules["dummy_organ_syn"] = d
mech.REGISTRY.append("dummy_organ_syn")
from wormemu.brain import Brain
b = Brain(cells=["AVAL", "AVBL", "PVCL"])
b.reset()
m = next(x for x in b.mechs if isinstance(x, Mech))
k = next((j for j, (pp, _, _, _) in enumerate(b.wsyn) if pp is m.pp), None)
pre, post = b._sg[0], b._sg[1]
b.step()
after = (float(m.pp.relgain), float(m.pp.recgain))
b.reset()
print(json.dumps(dict(listed=k is not None, post=int(post[k]) if k is not None and k < len(post) else None,
                      n_table=len(pre), n_wsyn=len(b.wsyn), after=after,
                      reset=(float(m.pp.relgain), float(m.pp.recgain)))))
'''


def test_mechanism_synapse_gets_release_gain_only():
    env = dict(os.environ, PYTHONPATH=str(ROOT / "src"))
    r = subprocess.run([sys.executable, "-c", SCRIPT], capture_output=True, text=True, env=env, cwd=ROOT, timeout=600)
    assert r.returncode == 0, r.stderr[-2000:]
    out = json.loads(r.stdout.strip().splitlines()[-1])
    assert out["listed"] and out["n_table"] == out["n_wsyn"] and out["post"] == -1   # built after the mechanisms
    rel, rec = out["after"]                     # the other mechanisms' release gains multiply in (neuromod: 1 - 3e-12)
    assert abs(rel - 2.0) < 1e-6 and rec == 1.0  # AVAL's release gain reaches it; the last cell's rec_glr does not
    assert out["reset"] == [1.0, 1.0]
