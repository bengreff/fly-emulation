"""The mechanism registry (src/wormemu/mech): a registered module's current reaches its cell, its conductance
multiplier reaches NEURON, its outputs reach the brain, and its SPECS and MECHANISMS reach the registry functions
build_ledger reads. NEURON is one simulator per process, so each brain runs in a subprocess."""
import json
import os
import subprocess
import sys
from pathlib import Path

from wormemu import mech
from wormemu.brain_layers import Spec

ROOT = Path(__file__).resolve().parents[1]
CELLS = ["AVAL", "AVAR", "AVBL", "PVCL", "DA01", "VB01", "dBWML6"]

DUMMY = '''
import sys, types, numpy as np
from wormemu import mech
from wormemu.brain_layers import Spec
d = types.ModuleType("dummy_mech")
d.MECHANISMS = [("dummy_inject", "Test: a fixed current into one cell", "test", "on")]
d.SPECS = [Spec("dummy_pA", "dummy_inject", "pA", 30.0, 0.0, 100.0)]
class Mech:
    def __init__(self, brain, params, toggles):
        self.i = brain.idx["AVBL"]; self.n = len(brain.cell_names); self.amp = params["dummy_pA"]; self.k = 0
    def reset(self):
        self.k = 0
    def step(self, ctx, dt_ms):
        self.k += 1
        I = np.zeros(self.n); I[self.i] = self.amp if 100 <= self.k < 300 else 0.0
        g = np.ones(self.n); g[self.i] = 2.0
        return dict(I_pA=I, g_scale={"leak": g}, out=dict(dummy_steps=1, peptide_release={"flp-11": 0.5}))
d.Mech = Mech
sys.modules["dummy_mech"] = d
mech.REGISTRY.append("dummy_mech")
'''

SCRIPT = DUMMY + '''
import json
from wormemu.brain import Brain
cells, toggles = json.loads(sys.argv[1]), json.loads(sys.argv[2])
b = Brain(toggles=toggles, cells=cells)
b.reset()
V = []
for k in range(400):
    o = b.step()
    V.append(o.v_mV)
V = np.array(V)
i, j = b.idx["AVBL"], b.idx["AVAL"]
cs, _, base, _ = b._gt["leak"]
gl = float(b.soma[i](0.5).pas.g) / float(base[list(cs).index(i)])
print(json.dumps(dict(built=len(b.mechs), toggle=b.toggles["dummy_inject"], v250=float(V[250, i]),
                      finite=bool(np.isfinite(V).all()), leak_ratio=gl,
                      out=b.mech_out.get("dummy_steps"), rel=b.mech_out.get("peptide_release"))))
'''


def _run(toggles):
    env = dict(os.environ, PYTHONPATH=str(ROOT / "src"))
    r = subprocess.run([sys.executable, "-c", SCRIPT, json.dumps(CELLS), json.dumps(toggles)], capture_output=True,
                       text=True, env=env, cwd=ROOT, timeout=600)
    assert r.returncode == 0, r.stderr[-2000:]
    return json.loads(r.stdout.strip().splitlines()[-1])


def test_dummy_mechanism_reaches_the_brain():
    on = _run(dict(wiring="cook"))
    assert on["built"] >= 1 and on["toggle"] == "on" and on["finite"]
    assert on["out"] == 1 and on["rel"] == {"flp-11": 0.5}
    assert abs(on["leak_ratio"] - 2.0) < 1e-9          # g_scale doubled AVBL's somatic leak
    off = _run(dict(wiring="cook", dummy_inject="off"))
    assert off["toggle"] == "off" and off["built"] == on["built"] - 1 and off["out"] is None   # off: not built
    assert on["v250"] - off["v250"] > 2.0                # 30 pA into AVBL depolarises it


def test_registry_feeds_the_ledger_builder():
    """build_ledger reads mech.all_specs() and mech.all_mechanisms(); a registered module's rows appear there."""
    import types
    d = types.ModuleType("dummy_mech_ledger")
    d.MECHANISMS = [("dummy_inject", "Test", "test", "on")]
    d.SPECS = [Spec("dummy_pA", "dummy_inject", "pA", 30.0, 0.0, 100.0)]
    sys.modules["dummy_mech_ledger"] = d
    reg = list(mech.REGISTRY) + ["dummy_mech_ledger"]
    assert "dummy_pA" in {s.id for s in mech.all_specs(reg)}
    assert ("dummy_inject", "Test", "test", "on") in mech.all_mechanisms(reg)
    for s in mech.all_specs():                           # the real registry: every spec is well formed
        assert s.lo <= s.template <= s.hi, s
    ids = [s.id for s in mech.all_specs()]
    assert len(ids) == len(set(ids))


def test_merge():
    acc = mech.merge({}, dict(a=1.0, r={"x": 1.0}))
    mech.merge(acc, dict(a=2.0, r={"x": 0.5, "y": 1.0}))
    assert acc == dict(a=3.0, r={"x": 1.5, "y": 1.0})
