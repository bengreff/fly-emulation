"""The AFD cyclase reads mech/glia's afd_gc_scale (glia KCC-3 -> Cl- -> GCY-8; senses_chem's cascade).

NEURON is one simulator per process, so each brain runs in its own subprocess."""
import json
import os
import subprocess
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]

SCRIPT = """
import json, sys
import numpy as np
from wormemu.brain import Brain, sample_worm
kcc, scale = sys.argv[1], json.loads(sys.argv[2])
b = Brain(sample_worm(None), toggles=dict(glia_kcc3=kcc), cells=["AFDL", "AFDR", "AIYL", "AIYR", "ASHL"])
if scale is not None:            # write afd_gc_scale straight into senses_chem's ctx, as mech/glia would
    m = next(m for m in b.mechs if type(m).__module__ == "wormemu.mech.senses_chem")
    step0 = m.step
    def step(ctx, dt_ms):
        ctx.outputs["afd_gc_scale"] = {"AFDL": scale, "AFDR": scale}
        return step0(ctx, dt_ms)
    m.step = step
b.reset()
V, cg, sc = [], [], []
for k in range(2000):
    o = b.step()
    V.append(float(o.v_mV[b.idx["AFDL"]]))
    cg.append(b.mech_out.get("afd_cgmp_uM", np.nan))
    sc.append(b.mech_out.get("afd_gc_scale", {}).get("AFDL", 1.0))
print(json.dumps(dict(V=V, cgmp=cg, scale=sc)))
"""


def _run(kcc, scale=None):
    env = dict(os.environ, PYTHONPATH=str(ROOT / "src"))
    r = subprocess.run([sys.executable, "-c", SCRIPT, kcc, json.dumps(scale)], capture_output=True, text=True,
                       env=env, cwd=ROOT, timeout=600)
    assert r.returncode == 0, r.stderr[-2000:]
    return json.loads(r.stdout.strip().splitlines()[-1])


def test_afd_gc_scale_moves_afd():
    """glia_kcc3 = fixed writes no scale (default 1); a written scale of 1 is identical to none; a scale of 2 raises
    AFD's cGMP and moves its voltage, a scale of 0.5 lowers cGMP."""
    none, one, two, half = _run("fixed"), _run("fixed", 1.0), _run("fixed", 2.0), _run("fixed", 0.5)
    assert none["scale"][-1] == 1.0
    assert np.array_equal(none["V"], one["V"]) and np.array_equal(none["cgmp"], one["cgmp"])
    assert two["cgmp"][-1] > 1.05 * none["cgmp"][-1] > 1.05 * half["cgmp"][-1]
    assert abs(two["V"][-1] - none["V"][-1]) > 0.5


def test_kcc3_null_end_to_end():
    """mech/glia's kcc-3 null raises the scale above 1 and, through the hook, AFD's cGMP above wild type."""
    on, null = _run("on"), _run("null")
    assert null["scale"][-1] > 1.01 and abs(on["scale"][-1] - 1.0) < 0.05
    assert null["cgmp"][-1] > on["cgmp"][-1]
