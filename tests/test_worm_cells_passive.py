"""mech/cells_passive (row 1): the 46 sensillar glia (isolated) and the wired end organs as passive cells.

NEURON is one simulator per process, so each brain runs in its own subprocess."""
import json
import os
import subprocess
import sys
from pathlib import Path

import numpy as np

from wormemu.brain_structure import load_structure
from wormemu.mech import cells_passive as C

ROOT = Path(__file__).resolve().parents[1]
CELLS = ["I2L", "I2R", "I5", "M4", "M2L", "M3L", "AIYL"]

SCRIPT = """
import json, sys
from wormemu.brain import Brain, sample_worm
b = Brain(sample_worm(None), toggles=json.loads(sys.argv[1]), cells=json.loads(sys.argv[2]))
cp = next((m for m in b.mechs if type(m).__module__ == "wormemu.mech.cells_passive"), None)
b.reset()
V = []
for k in range(300):
    b.extra_pA[:] = 10.0 if 100 <= k < 200 else 0.0
    V.append(b.step().v_mV.tolist())
print(json.dumps(dict(V=V, names=b.cell_names, cells=sorted(cp.sec) if cp else [], gaps=cp.gaps if cp else [])))
"""


def _run(toggles):
    env = dict(os.environ, PYTHONPATH=str(ROOT / "src"))
    r = subprocess.run([sys.executable, "-c", SCRIPT, json.dumps(toggles), json.dumps(CELLS)], capture_output=True,
                       text=True, env=env, cwd=ROOT, timeout=600)
    assert r.returncode == 0, r.stderr[-2000:]
    return json.loads(r.stdout.strip().splitlines()[-1])


def test_specs_and_names():
    """Templates inside bounds; 46 distinct glia, none a Cook node (if a wiring set adds one, wire it)."""
    assert all(s.lo <= s.template <= s.hi for s in C.SPECS)
    assert len(set(C.GLIA_SENSILLA)) == 46
    st = load_structure()
    assert not set(C.GLIA_SENSILLA) & set(st.names)
    assert set(C.EPITHELIUM + C.GLANDS) <= set(st.names)


def test_glia_sensilla_isolated():
    """The 46 glia carry no connection: on and off give identical neuron voltages."""
    a = _run(dict(endorgan_cells="off"))
    b = _run(dict(endorgan_cells="off", glia_sensilla="off"))
    assert len(a["cells"]) == 46 and not b["cells"]
    assert np.array_equal(np.array(a["V"]), np.array(b["V"]))


def test_endorgan_wired():
    """e3VL-I2L, e3VR-I2R and g1A-I5/M2L/M3L/M4 gaps exist and load those neurons."""
    on, off = _run({}), _run(dict(endorgan_cells="off"))
    pairs = {frozenset(g[:2]) for g in on["gaps"]}
    for p in (("e3VL", "I2L"), ("e3VR", "I2R"), ("g1AL", "I5"), ("g1AL", "M4"), ("g1AR", "M4"), ("g1AL", "M3L")):
        assert frozenset(p) in pairs
    V, V0 = np.array(on["V"]), np.array(off["V"])
    assert np.isfinite(V).all() and np.abs(V - V0)[:, on["names"].index("M4")].max() > 0.1
