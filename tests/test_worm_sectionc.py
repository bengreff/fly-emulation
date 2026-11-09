"""KNOWLEDGE_GAPS section C mechanisms (7 Nov 2026): AMsh glia GABA onto ASH (mech/glia_release) and DVA's
compression/tension split (mech/senses_proprio dva_strain_split). Both are off by default and neutral when off.

NEURON is one simulator per process, so each brain runs in its own subprocess."""
import json
import os
import subprocess
import sys
from pathlib import Path

import numpy as np

from wormemu import mech
from wormemu.mech import glia_release, senses_proprio

ROOT = Path(__file__).resolve().parents[1]
CELLS = ["ASHL", "ASHR", "DVA", "AVAL", "VA05", "dBWML6"]
SCRIPT = """
import json, sys
import numpy as np
from wormemu.brain import Brain, sample_worm
from wormemu.interface import default_observation
spec = sample_worm(None)
spec.values.update(json.loads(sys.argv[3]))
b = Brain(spec, toggles=json.loads(sys.argv[1]), cells=json.loads(sys.argv[2]))
b.reset()
V, out = [], {}
for k in range(200):
    o = default_observation(b.t)
    if k >= 50:
        o.nose_force_uN = 5.0
        o.curvature_per_mm = np.full(len(o.curvature_per_mm), 8.0 if k < 125 else -8.0)
    V.append(b.step(o).v_mV.tolist())
    out = {k2: b.mech_out.get(k2) for k2 in ("glia_amsh_act", "dva_twk16_po", "glia_amine_nM", "neuromod", "k2p")}
print(json.dumps(dict(V=V, names=b.cell_names, out=out)))
"""


def _run(toggles, values=None):
    env = dict(os.environ, PYTHONPATH=str(ROOT / "src"))
    r = subprocess.run([sys.executable, "-c", SCRIPT, json.dumps(toggles), json.dumps(CELLS), json.dumps(values or {})],
                       capture_output=True, text=True, env=env, cwd=ROOT, timeout=600)
    assert r.returncode == 0, r.stderr[-2000:]
    return json.loads(r.stdout.strip().splitlines()[-1])


def test_off_by_default_and_labelled():
    on = {t[0]: t[3] for m in mech.modules() for t in m.MECHANISMS}
    assert all(on[k] == "off" for k in ("glia_gaba", "glia_serotonin", "dva_strain_split", "pathogen_sickness",
                                        "unc58_na_leak"))
    for s in glia_release.SPECS + [s for s in senses_proprio.SPECS if s.mechanism == "dva_strain_split"]:
        assert s.label in ("guessed", "inferred") and s.lo <= s.template <= s.hi


def test_dva_split_strain_sign():
    """Split: DVA's TRP-4 strain is the ventral fibre's compression (kappa < 0), 0 under ventral tension."""
    m = senses_proprio.Mech.__new__(senses_proprio.Mech)
    m.p = {s.id: s.template for s in senses_proprio.SPECS}
    m.cells, m.kind, m.sign, m.s0, m.split = ["DVA"], np.array(["dva"]), np.array([1.0]), np.array([np.nan]), True
    obs = {"curvature_per_mm": np.full(49, 8.0), "s": np.linspace(0, 1, 49)}
    assert m.strain(obs)[0] == 0.0
    obs["curvature_per_mm"] = -obs["curvature_per_mm"]
    assert np.isclose(m.strain(obs)[0], 8e-3 * m.p["proprio_radius_um"])


def test_glia_gaba_and_dva_split_act_and_are_neutral_off():
    """Off (explicitly) equals the default bit for bit; on, nose touch activates AMsh and moves ASH, tension opens
    TWK-16 on DVA."""
    d, off = _run({}), _run({"glia_gaba": "off", "dva_strain_split": "off", "unc58_na_leak": "off",
                             "glia_serotonin": "off", "pathogen_sickness": "off"})
    assert np.array_equal(np.array(d["V"]), np.array(off["V"]))
    on = _run({"glia_gaba": "on", "dva_strain_split": "on"})
    a = on["out"]["glia_amsh_act"]
    assert a and a["L"] > 0.0 and on["out"]["dva_twk16_po"] is not None
    i = on["names"].index("ASHL")
    assert not np.allclose(np.array(on["V"])[60:, i], np.array(d["V"])[60:, i])


def test_pathogen_exposure_from_infection_hours():
    """mech/pathogen: off writes nothing; on, the exposure is 1 - exp(-h / tau) and 0 for a naive worm."""
    from wormemu.mech import pathogen
    p = {s.id: s.template for s in pathogen.SPECS}
    assert pathogen.Mech(None, p, {}).step(None, 1.0) == {}
    pathogen.INFECTION_H = 20.0
    try:
        x = pathogen.Mech(None, p, {"pathogen_sickness": "on"}).step(None, 1.0)["out"]["pathogen_exposure"]
    finally:
        pathogen.INFECTION_H = 0.0
    assert np.isclose(x, 1 - np.exp(-20.0 / p["pathogen_load_tau_h"]))
    assert pathogen.Mech(None, p, {"pathogen_sickness": "on"}).step(None, 1.0)["out"]["pathogen_exposure"] == 0.0


def test_glia_serotonin_reaches_the_head_compartment():
    """glia_serotonin on: nose touch writes AMsh 5-HT, which neuromod adds to the head compartment (a large
    glia_5ht_max_nM so it stands above the worm's own 5-HT)."""
    big = {"glia_5ht_max_nM": 1e6, "glia_amsh_tau_s": 0.01}
    d, r = _run({}, big), _run({"glia_serotonin": "on"}, big)
    assert r["out"]["glia_amine_nM"]["serotonin"] > 1e5
    assert r["out"]["neuromod"]["ma_serotonin_max_nM"] > d["out"]["neuromod"]["ma_serotonin_max_nM"] + 1e4


def test_unc58_leak_depolarises_its_cells():
    """unc58_na_leak on: a Na+-permeable leak (reversal -15 mV) in the unc-58 cells moves them toward -15 mV."""
    d, on = _run({}, {"unc58_g_S_cm2": 2e-5}), _run({"unc58_na_leak": "on"}, {"unc58_g_S_cm2": 2e-5})
    assert on["out"]["k2p"]["unc58_cells"] > 0 and on["out"]["k2p"]["unc58_g_max_nS"] > 0
    v0, v1 = np.array(d["V"])[40], np.array(on["V"])[40]
    # Only cells below the reversal: one within a mV or two above it carries almost no leak current of its own, and its
    # depolarised neighbours (the leak's other cells) can push it further up (VA05 at -14.0 mV, 8 Nov, after the
    # expression-mask fix; -20.8 mV under the old mask, where it moved toward -15).
    moved = (np.abs(v1 - v0) > 1e-3) & (v0 < -17.0)
    assert moved.any() and np.all(np.abs(v1[moved] + 15.0) < np.abs(v0[moved] + 15.0))
