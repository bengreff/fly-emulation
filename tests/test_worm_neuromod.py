"""Rows 9, 10, 28 (mech/neuromod.py): the lumped form is brain_layers' old layer exactly (neutral equivalence), the
compartment form runs inside the brain and scales conductances, and the module's unit checks hold. NEURON is one
simulator per process, so each brain runs in a subprocess."""
import json
import os
import subprocess
import sys
from pathlib import Path

import numpy as np

from wormemu.brain_structure import load_structure
from wormemu.mech import neuromod as N

ROOT = Path(__file__).resolve().parents[1]
CELLS = ["AVAL", "AVAR", "AVBL", "ASHL", "RIS", "ALA", "NSML", "ADFL", "CEPDL", "RIML", "RICL", "PVCL", "DA01",
         "VB01", "dBWML6"]

SCRIPT = '''
import json, sys, numpy as np
from wormemu import mech
cells, toggles, reg = json.loads(sys.argv[1]), json.loads(sys.argv[2]), json.loads(sys.argv[3])
mech.REGISTRY[:] = reg
from wormemu.brain import Brain
b = Brain(toggles=toggles, cells=cells)
b.reset()
for c, a in (("AVBL", 40.0), ("ASHL", 30.0), ("RIS", 10.0), ("CEPDL", 10.0)):
    b.extra_pA[b.idx[c]] = a
V = []
for k in range(300):
    V.append(b.step().v_mV)
nm = b.mech_out.get("neuromod", {})
print(json.dumps(dict(V=np.array(V).tolist(), mechs=[type(m).__module__ for m in b.mechs], neuromod=nm)))
'''


def _run(toggles, reg=("receptors", "neuromod")):
    env = dict(os.environ, PYTHONPATH=str(ROOT / "src"))
    r = subprocess.run([sys.executable, "-c", SCRIPT, json.dumps(CELLS), json.dumps(toggles), json.dumps(list(reg))],
                       capture_output=True, text=True, env=env, cwd=ROOT, timeout=600)
    assert r.returncode == 0, r.stderr[-2000:]
    return json.loads(r.stdout.strip().splitlines()[-1])


def test_lumped_is_old_layer():
    old = _run(dict(peptides="on", monoamines="on"), reg=("receptors",))
    none = _run(dict(peptides="off", monoamines="off"), reg=("receptors",))
    new = _run(dict(peptides="lumped", monoamines="lumped"))
    V, V0, V1 = (np.array(x["V"]) for x in (old, none, new))
    assert np.abs(V - V0).max() > 1e-6                     # the old layer does something here
    assert np.abs(V - V1).max() < 1e-9                     # and the lumped form is it
    assert "wormemu.mech.neuromod" in new["mechs"] and new["neuromod"] == {}


def test_compartments_run_in_brain():
    for f in ("compartments", "well_mixed"):
        r = _run(dict(peptides=f, monoamines=f))
        V = np.array(r["V"])
        assert np.isfinite(V).all() and np.abs(V).max() < 200
        nm = r["neuromod"]
        assert nm["pep_total_molecules"] > 0 and nm["ma_serotonin_max_nM"] > 0 and nm["pep_n_receptor_sites"] > 0
        assert np.isfinite(list(nm.values())).all()


def test_tables():
    st = load_structure()
    assert len(N.PAIRS) == 147 and len(N.PRECURSORS) == 53
    for s in N.SPECS:
        assert s.lo <= s.template <= s.hi, s.id
        assert s.label in ("measured", "derived", "inferred", "guessed", "published_fit"), s.id
    for rg, (f, _, label, _) in N.GPCR_COUPLING.items():
        assert f in "qisu" and label in ("measured", "inferred", "guessed"), rg
    assert all(g in st.gene_index for g in N.G_ALPHA + tuple(N.TRANSPORTERS.values()))
    assert st.expr("dmsr-1", "RIS") == 0 and ("RIS", "dmsr-1") in N.EXPR_ADD      # the added autoreceptor
    assert N.form("on") == "compartments" and N.form(False) == "off"


def test_unit_checks():
    env = dict(os.environ, PYTHONPATH=str(ROOT / "src"))
    r = subprocess.run([sys.executable, str(ROOT / "scripts" / "worm" / "neuromod_unit_check.py")],
                       capture_output=True, text=True, env=env, cwd=ROOT, timeout=600)
    assert r.returncode == 0, r.stderr[-2000:]
    res = json.loads(r.stdout[r.stdout.index("{"):])
    for k in ("code_checks", "bolus", "limit_well_mixed"):
        assert res[k]["passed"], (k, res[k])
    w = res["ris_self_limit"]                              # reported; the feedback itself is asserted
    assert w["with"]["flp11_head_nM_end"] < w["without"]["flp11_head_nM_end"] and w["with"]["ris_gi"] > 0.1
