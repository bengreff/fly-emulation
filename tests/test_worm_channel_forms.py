"""mech/channel_forms.py (DEBUG_TRIAGE line 1): egl19_kinetics / shl1_kinetics = off (the default) is the brain without
the module, bit for bit; each n24 form writes its constants into egl19, slo1_egl19, slo2_egl19 (EGL-19) or shl1 and
moves the brain; restore() puts BAAIWorm's literals back; brain.patch_shl1_form at its defaults is the vendored
shl1.mod bit for bit. The figure check is scripts/worm/channels_unit_check.py --forms. NEURON is one simulator per
process: each run is a subprocess."""
import json
import os
import subprocess
import sys

import numpy as np

from test_worm_neuromod import CELLS, ROOT

BRAIN = '''
import json, sys, numpy as np
from wormemu import mech
cells, toggles, reg = json.loads(sys.argv[1]), json.loads(sys.argv[2]), json.loads(sys.argv[3])
mech.REGISTRY[:] = reg
from wormemu.brain import Brain
b = Brain(toggles=toggles, cells=cells)
b.reset()
for c, a in (("AVBL", 40.0), ("ASHL", 30.0)):
    b.extra_pA[b.idx[c]] = a
V = [b.step().v_mV for k in range(300)]
h = b.h
g = {m: {k: float(getattr(h, f"{k}_{m}")) for k in ("vhm", "vhh", "btm", "cth")} for m in ("egl19", "slo1_egl19",
     "slo2_egl19")}
g["shl1"] = {k: float(getattr(h, f"{k}_shl1")) for k in ("vhm", "vhh", "mexp", "wf", "tmsc", "thfsc")}
print(json.dumps(dict(V=np.array(V).tolist(), g=g, mechs=[type(m).__module__ for m in b.mechs])))
'''

# one soma with BAAIWorm's egl19, slo1_egl19 and shl1, +20 pA: argv[1] = "patched" (brain._neuron) or "vendored"
SOMA = '''
import json, sys
sys.path.insert(0, sys.argv[2])
import channels_unit_check as U
from neuron import h
if sys.argv[1] == "patched":
    from wormemu.brain import _neuron
    h = _neuron()
else:
    h.nrn_load_dll(U._compile([U.ROOT / "third_party" / "baaiworm" / "mod" / f"{m}.mod"
                               for m in ("egl19", "slo1_egl19", "shl1")], "vendored"))
    h.load_file("stdrun.hoc")
s = h.Section(name="soma")
s.L = s.diam = 4.6
for m, var, g in (("egl19", "gbegl19", 0.3), ("slo1_egl19", "gbslo1", 0.2), ("shl1", "gbshl1", 1.0)):
    s.insert(m)
    setattr(s(0.5), f"{var}_{m}", g)
s.insert("pas")
s(0.5).pas.g, s(0.5).pas.e = 1e-4, -70.0
s(0.5).eca, s(0.5).ek = 60.0, -80.0
st = h.IClamp(s(0.5))
st.delay, st.dur, st.amp = 100.0, 600.0, 0.02
v = h.Vector()
v.record(s(0.5)._ref_v)
h.dt, h.tstop = 0.025, 800.0
h.finitialize(-60.0)
h.continuerun(800.0)
print(json.dumps(v.to_python()))
'''


def _run(script, *args):
    env = dict(os.environ, PYTHONPATH=str(ROOT / "src"))
    r = subprocess.run([sys.executable, "-c", script, *args], capture_output=True, text=True, env=env, cwd=ROOT,
                       timeout=900)
    assert r.returncode == 0, r.stderr[-2000:]
    return json.loads(r.stdout.strip().splitlines()[-1])


def _brain(toggles, reg):
    return _run(BRAIN, json.dumps(CELLS), json.dumps(toggles), json.dumps(list(reg)))


def test_off_is_without_module_and_forms_set_globals():
    from wormemu.mech import channel_forms as CF
    none = _brain(dict(), reg=("receptors",))
    off = _brain(dict(egl19_kinetics="off", shl1_kinetics="off"), reg=("channel_forms", "receptors"))
    assert np.array_equal(np.array(none["V"]), np.array(off["V"]))
    assert "wormemu.mech.channel_forms" not in off["mechs"]
    code = _brain(dict(egl19_kinetics="n24_code", shl1_kinetics="n24_code"), reg=("channel_forms", "receptors"))
    assert "wormemu.mech.channel_forms" in code["mechs"]
    for m in CF.EGL19_MODS:
        assert code["g"][m]["vhm"] == -4.4 and code["g"][m]["cth"] == -32.9723
        assert off["g"][m]["vhm"] == 5.6
    assert code["g"]["shl1"] == dict(vhm=0.26, vhh=-50.0, mexp=1.0, wf=0.8, tmsc=0.5, thfsc=1.0 / 3.0)
    assert off["g"]["shl1"]["mexp"] == 3.0 and off["g"]["shl1"]["tmsc"] == 0.4
    V0, V1 = np.array(off["V"]), np.array(code["V"])
    assert np.isfinite(V1).all() and np.abs(V1).max() < 200 and not np.allclose(V0, V1)


def test_values_specs_and_restore():
    from wormemu.mech import channel_forms as CF
    assert CF.values("off", "egl19") == {} and CF.values("off", "shl1") == {}
    p = {s.id: s.template for s in CF.SPECS}
    for f in ("n24_printed", "n24_code"):
        for ch in CF.TABLES:
            v = CF.values(f, ch)
            assert v and v == CF.values(f, ch, p)
            assert all(s.lo <= s.template <= s.hi for s in CF.SPECS)
    assert CF.values("n24_printed", "egl19")["vhm"] == -5.6 and "vhhb" not in CF.values("n24_printed", "egl19")

    class H:
        pass
    h = H()
    for m in CF.EGL19_MODS:
        for k, x in CF.values("n24_code", "egl19").items():
            setattr(h, f"{k}_{m}", x)
    for k, x in CF.values("n24_code", "shl1").items():
        setattr(h, f"{k}_shl1", x)
    CF.restore(h)
    for m in CF.EGL19_MODS[1:]:
        assert all(getattr(h, f"{k}_{m}") == r[0] for k, r in CF.EGL19.items())
    assert all(getattr(h, f"{k}_shl1") == v for k, v in CF.SHL1_FORM.items())


def test_patched_shl1_is_vendored():
    sw = str(ROOT / "scripts" / "worm")
    a, b = _run(SOMA, "patched", sw), _run(SOMA, "vendored", sw)
    assert a == b and max(a) - min(a) > 5.0
