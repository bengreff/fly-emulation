"""mech/channels (row 4): Nicoletti 2024's channels in the CeNGEN-detected classes; the baaiworm form is neutral.

NEURON is one simulator per process, so each brain runs in its own subprocess."""
import json
import os
import subprocess
import sys
from pathlib import Path

import numpy as np

from wormemu.mech import channels as C

ROOT = Path(__file__).resolve().parents[1]
CELLS = ["AIYL", "AFDL", "AWAL", "AVAL", "RIML", "VB03", "dBWML6"]

SCRIPT = """
import json, sys
from wormemu import mech
drop, toggles = json.loads(sys.argv[1]), json.loads(sys.argv[2])
if drop:
    mech.REGISTRY.remove("channels")
from wormemu.brain import Brain, sample_worm
b = Brain(sample_worm(None), toggles=toggles, cells=json.loads(sys.argv[3]))
b.reset()
V = []
for k in range(300):
    b.extra_pA[:3] = 15.0 if 100 <= k < 200 else 0.0
    V.append(b.step().v_mV.tolist())
got = {n: {ch: getattr(b.soma[i](0.5), ch).gbar for ch in ("kqt1", "unc103", "exp2", "slo1iso", "slo2iso")
           if hasattr(b.soma[i](0.5), ch)} for n, i in b.idx.items()}
print(json.dumps(dict(V=V, got=got, names=b.cell_names, unit=getattr(b.h, "cai_to_uM_slo1iso", None),
                      va=getattr(b.h, "va_kqt1", None))))
"""


def _run(drop, toggles):
    env = dict(os.environ, PYTHONPATH=str(ROOT / "src"))
    r = subprocess.run([sys.executable, "-c", SCRIPT, json.dumps(drop), json.dumps(toggles), json.dumps(CELLS)],
                       capture_output=True, text=True, env=env, cwd=ROOT, timeout=600)
    assert r.returncode == 0, r.stderr[-2000:]
    return json.loads(r.stdout.strip().splitlines()[-1])


def test_specs():
    """One density Spec per (channel, detecting class), every template inside its bounds and never negative; the
    fitted classes carry the published value (0 where the published model omits the channel)."""
    d = {s.id: s for s in C.SPECS}
    assert all(s.lo <= s.template <= s.hi and s.lo >= 0 for s in C.SPECS if s.id.startswith("dens_"))
    assert d["dens_kqt1_AIY"].label == "published_fit"
    assert np.isclose(d["dens_kqt1_AIY"].template, 0.2e-9 / 65.89e-8)
    assert d["dens_unc103_RIM"].template == 0.0 and d["dens_unc103_RIM"].label == "published_fit"
    assert d["dens_exp2_AFD"].label == "guessed"                           # no cell was fitted with EXP-2
    assert "dens_kqt1_AVA" not in d                                         # kqt-1 not detected in AVA
    for ch, rows in C.KINETICS.items():                                     # every kinetic PARAMETER is a Spec
        assert rows and all(f"kin_{ch}_{n}" in d for n, _, _ in rows)


def test_baaiworm_form_neutral():
    """channel_library = baaiworm is BAAIWorm as ported: identical voltages to a brain without the module."""
    a = _run(True, {})
    b = _run(False, dict(channel_library="baaiworm"))
    assert np.array_equal(np.array(a["V"]), np.array(b["V"]))
    assert not any(b["got"].values())


def test_library_on():
    """Default form: each neuron gets the channels its CeNGEN class detects, at its class Spec; the SLO mods read
    cai in uM; the added channels move the voltages."""
    r = _run(False, {})
    d = {s.id: s.template for s in C.SPECS}
    assert r["got"]["AIYL"] == {"kqt1": d["dens_kqt1_AIY"], "slo1iso": d["dens_slo1iso_AIY"],
                                "slo2iso": d["dens_slo2iso_AIY"]}
    assert set(r["got"]["AFDL"]) == {"kqt1", "exp2", "slo1iso", "slo2iso"}
    assert r["got"]["dBWML6"] == {}
    assert r["unit"] == 1.0 and r["va"] == d["kin_kqt1_va"]
    V, V0 = np.array(r["V"]), np.array(_run(False, dict(channel_library="baaiworm"))["V"])
    assert np.isfinite(V).all() and np.abs(V - V0)[:, r["names"].index("AFDL")].max() > 0.1
