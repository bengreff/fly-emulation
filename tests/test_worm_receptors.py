"""Row 7, receptor classes (mech/receptors.py, nmodl/wsyn.mod): the graded mode reproduces BAAIWorm's two synapse
mods exactly (neutral equivalence), the kinetic and instantaneous modes run, the class assignment follows
transmitter, CeNGEN and polarity, and the isolated unit checks hold. NEURON is one simulator per process, so each
brain runs in a subprocess."""
import json
import os
import subprocess
import sys
from pathlib import Path

import numpy as np

from wormemu.brain_structure import load_structure
from wormemu.mech import receptors as R

ROOT = Path(__file__).resolve().parents[1]
CELLS = ["AVAL", "AVAR", "AVBL", "ASHL", "PVCL", "DA01", "DD01", "VB01", "dBWML6", "vBWML7"]

SCRIPT = '''
import json, sys, numpy as np
from wormemu.brain import Brain
cells, toggles = json.loads(sys.argv[1]), json.loads(sys.argv[2])
b = Brain(toggles=toggles, cells=cells)
b.reset()
b.extra_pA[b.idx["AVBL"]] = 40.0
b.extra_pA[b.idx["ASHL"]] = 30.0
V = []
for k in range(600):
    V.append(b.step().v_mV)
print(json.dumps(dict(V=np.array(V).tolist(), placed=dict(b.placed), n_wsyn=len(b.wsyn))))
'''


def _run(toggles):
    env = dict(os.environ, PYTHONPATH=str(ROOT / "src"))
    r = subprocess.run([sys.executable, "-c", SCRIPT, json.dumps(CELLS), json.dumps(toggles)], capture_output=True,
                       text=True, env=env, cwd=ROOT, timeout=600)
    assert r.returncode == 0, r.stderr[-2000:]
    return json.loads(r.stdout.strip().splitlines()[-1])


def test_graded_mode_is_baaiworm():
    nm = dict(peptides="off", monoamines="off")           # neuromod's release factor acts on wsyn only
    off = _run(dict(wiring="cook", receptor_kinetics="off", **nm))
    gr = _run(dict(wiring="cook", receptor_kinetics="graded", **nm))
    assert off["n_wsyn"] == 0 and gr["n_wsyn"] > 0
    assert np.abs(np.array(off["V"]) - np.array(gr["V"])).max() < 1e-9      # the old synapse inside wsyn


def test_kinetic_and_instantaneous_run():
    for mode in ("kinetic", "instantaneous"):
        r = _run(dict(wiring="cook", receptor_kinetics=mode))
        V = np.array(r["V"])
        assert np.isfinite(V).all() and np.abs(V).max() < 200
        assert any(k.startswith("wsyn_") and "graded" not in k for k in r["placed"]), r["placed"]
        assert r["placed"].get("syn_nmj", 0) + r["placed"].get("syn_nmj_inh", 0) > 0


def test_pair_classes():
    st = load_structure()
    cl = dict(R.pair_classes(st, "ASHL", "AVA"))
    assert set(cl) <= {"glr", "nmr", "glucl"} and abs(sum(cl.values()) - 1) < 1e-12 and "glr" in cl
    assert all(R.CLASSES[c][1] == -1 for c, _ in R.pair_classes(st, "ASHL", "AVA", "-"))   # polarity filter
    assert dict(R.pair_classes(st, "DA01", None, post_muscle=True, lacr_share=0.3)) == {"lacr": 0.3, "acr16": 0.7}
    assert R.pair_classes(st, "DD01", None, post_muscle=True) == [("gabacl", 1.0)]
    none = next(n for n, k in zip(st.names, st.kind) if k == "neuron" and not st.transmitter.get(n))
    assert R.pair_classes(st, none, "AVA") == []                                   # BAAIWorm's graded synapse
    for c, (lg, sg, genes, rule, _) in R.CLASSES.items():
        assert lg in R.LIGANDS and sg in (-1, 1) and rule in ("all", "any")
        assert all(g in st.gene_index for g in genes), c


def test_unit_checks():
    env = dict(os.environ, PYTHONPATH=str(ROOT / "src"))
    r = subprocess.run([sys.executable, str(ROOT / "scripts" / "worm" / "receptor_unit_check.py")],
                       capture_output=True, text=True, env=env, cwd=ROOT, timeout=600)
    assert r.returncode == 0, r.stderr[-2000:]
    res = json.loads(r.stdout[r.stdout.index("{"):])
    for k in ("unc49_step", "lacr_vs_acr16", "ec50_half", "mg_block"):
        assert res[k]["passed"], (k, res[k])
    assert np.isfinite(res["nmj_ipsc"]["tau_ms"])        # the composite check is reported, not asserted
