"""mech/glia (row 11, item 8): the K+ load forms (glia_k_load leak | channels, Sibille et al. 2015 eq. 25) and the
resting reference window (glia_v0_window first | settled). Spec: docs/worm/night/wbody2/glia_port_spec.md."""
import json
import os
import subprocess
import sys
from pathlib import Path
from types import SimpleNamespace

import numpy as np

from wormemu.brain_layers import AMPHID
from wormemu.mech import glia

ROOT = Path(__file__).resolve().parents[1]


def _run_mech(toggles, v_of_t, t_end):
    names = sorted(AMPHID)
    brain = SimpleNamespace(idx={n: i for i, n in enumerate(names)}, spec=None)
    m = glia.Mech(brain, {}, {"glia_cells": "off", **toggles})
    t, rows = 0.0, []
    while t < t_end:
        rows.append(m.step(SimpleNamespace(v=np.full(len(names), v_of_t(t)), t_ms=t), 5.0))
        t += 5.0
    return m, rows


def test_defaults_are_the_leak_form_over_the_first_second():
    v = lambda t: -65.0 + 5.0 * (t >= 1500.0)
    _, a = _run_mech({}, v, 4000.0)
    _, b = _run_mech({"glia_k_load": "leak", "glia_v0_window": "first"}, v, 4000.0)
    for x, y in zip(a, b):
        assert np.array_equal(x["out"]["amphid_k_mM"], y["out"]["amphid_k_mM"])
        assert np.array_equal(x["I_pA"], y["I_pA"])


def test_settled_window_leaves_out_the_start_up():
    """A start-up step in the first second sets the first window's v0 below the later rest; the settled window
    (1-2 s) does not see it, so a cell that is steady after 1 s loads nothing."""
    v = lambda t: -65.0 if t < 1000.0 else -60.0
    m1, r1 = _run_mech({"glia_v0_window": "first"}, v, 4000.0)
    m2, r2 = _run_mech({"glia_v0_window": "settled"}, v, 4000.0)
    bath = m1.q["glia_k_bath_mM"]
    assert (r1[-1]["out"]["amphid_k_mM"] > bath + 0.01).all()
    assert np.array_equal(r2[-1]["out"]["amphid_k_mM"], np.full(2, bath))
    assert np.allclose(m2.v0, -60.0)


CHANNELS = r"""
import json, numpy as np
from wormemu import mech
if "glia" not in mech.REGISTRY:
    mech.REGISTRY.append("glia")
from wormemu.brain import Brain
from wormemu.mech import glia as gl
b = Brain(cells=["AWCL", "AWCR", "ASHL", "ASHR"], toggles={"glia_k_load": "channels"})
b.reset()
m = next(x for x in b.mechs if isinstance(x, gl.Mech))
secs = [[s for s in b.cells[i].all if b.h.ismembrane("k_ion", sec=s)] for i in m.amph]
base = [[s.ek for s in ss] for ss in secs]
clamp = None
while b.t < 2000.0:
    if clamp is None and b.t >= 1200.0:
        clamp = b.h.SEClamp(b.soma[b.idx["AWCL"]](0.5))
        clamp.dur1, clamp.amp1, clamp.rs = 1e9, -20.0, 0.01
    r = b.step(None, 5.0)
kb, q = m.q["glia_k_bath_mM"], m.q
dek = q["glia_rt_f_mV"] * np.log(m.ko / kb)
err = max(abs(s.ek - (e + dek[sd])) for ss, e0, sd in zip(secs, base, m.amph_side) for s, e in zip(ss, e0))
from types import SimpleNamespace
injects = "I_pA" in m.step(SimpleNamespace(v=r.v_mV, t_ms=b.t), 5.0)
print(json.dumps({"ko": m.ko.tolist(), "bath": kb, "ek_err": err, "n_sec": sum(map(len, secs)), "injects": injects}))
"""


def _run(code):
    env = dict(os.environ, PYTHONPATH=str(ROOT / "src"))
    r = subprocess.run([sys.executable, "-c", code], capture_output=True, text=True, env=env, timeout=600)
    assert r.returncode == 0, r.stderr[-3000:]
    return json.loads(r.stdout.strip().splitlines()[-1])


def test_channels_form_moves_ek_on_the_k_sections_and_injects_nothing():
    """AWCL clamped to -20 mV: its gated K+ current loads the left ending, the left side's K+ sections carry the
    Nernst shift of that K+, and the module injects no current."""
    r = _run(CHANNELS)
    assert r["n_sec"] > 0 and r["ek_err"] < 1e-9, r
    assert r["ko"][0] > r["bath"] + 0.01, r
    assert not r["injects"], r
