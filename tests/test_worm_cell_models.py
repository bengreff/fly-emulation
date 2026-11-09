"""mech/cell_models (wbrain2, 9 Nov 2026): Jiang et al. 2022's AVL model as the avl_membrane toggle and its DVB borrow
(dvb_membrane jiang22_noexp2), and Naudin et al. 2022's AFD model as afd_membrane naudin22. Defaults change nothing;
the Specs are the mods' numbers; each mod matches its CPU reference (scripts/worm/debug2/jiang22_ref.py,
naudin22_afd_check.py); a swapped cell keeps none of BAAIWorm's membrane.

NEURON is one simulator per process, so the NEURON parts run in their own subprocesses."""
import json
import os
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts" / "worm" / "debug2"))

from wormemu.mech import cell_models as M  # noqa: E402

MODFILE = ROOT / "src" / "wormemu" / "nmodl" / "cells" / "jiang22_avl.mod"
N22FILE = ROOT / "src" / "wormemu" / "nmodl" / "cells" / "naudin22_afd.mod"


def _mod_params(path=MODFILE):
    text = path.read_text()
    block = text[text.index("PARAMETER {"):]
    block = block[:block.index("}")]
    return {m.group(1): float(m.group(2)) for m in re.finditer(r"^\s*(\w+)\s*=\s*([-+0-9.eE]+)", block, re.M)}


def test_defaults_neutral():
    on = {t[0]: t[3] for t in M.MECHANISMS}
    assert on == {"avl_membrane": "baaiworm", "dvb_membrane": "baaiworm", "jiang22_egl36_weights": "printed",
                  "afd_membrane": "baaiworm"}
    assert M.jiang_cells({}) == [] and M.naudin_cells({}) == []
    assert M.jiang_cells({"avl_membrane": "jiang22", "dvb_membrane": "jiang22_noexp2"}) == ["AVL", "DVB"]
    assert M.naudin_cells({"afd_membrane": "naudin22"}) == ["AFDL", "AFDR"]
    assert M.jiang_cells({"afd_membrane": "naudin22"}) == []


def test_specs_are_the_mods_numbers():
    p = _mod_params()
    s = {x.id: x for x in M.SPECS}
    for n in M.KIN:
        assert p[n] == s[f"j22_{n}"].template, n
    assert p["w36_f"] == s["j22_w36_f"].template == 0.33 and s["j22_w36_f_code"].template == 0.31
    for g, x in M.G_NS.items():
        assert abs(p[g] - x / (1000.0 * s["j22_C_pF"].template)) < 1e-15, g
        assert s[f"j22_AVL_{g}"].template == x
        assert s[f"j22_DVB_{g}"].template == (0.0 if g == "g_EXP2" else x)


def test_naudin_specs_are_the_mods_numbers():
    p = _mod_params(N22FILE)
    s = {x.id: x for x in M.SPECS}
    assert s["n22_C_pF"].template == M.N22_C_PF == 6.6
    for n, (v, *_rest) in M.N22_KIN.items():
        assert p[n] == s[f"n22_{n}"].template == v, n
    for g, x in M.N22_G.items():
        assert s[f"n22_{g}"].template == x
        assert abs(p[g] / (x / (1000.0 * M.N22_C_PF)) - 1) < 1e-7, g     # the mod's defaults are rounded to 8 digits


def test_naudin_reference_is_s2_table():
    from naudin22_afd_check import P
    assert {k: P[k] for k in ("gCa", "gKir", "gK", "gL")} == {"gCa": M.N22_G["g_Ca"], "gKir": M.N22_G["g_Kir"],
                                                              "gK": M.N22_G["g_K"], "gL": M.N22_G["g_L"]}
    pairs = dict(e_Ca="ECa", e_K="EK", e_L="EL", vh_mCa="vmCa", k_mCa="kmCa", vh_Kir="vKir", k_Kir="kKir",
                 vh_mK="vmK", k_mK="kmK", vh_hK="vhK", k_hK="khK")
    for n, r in pairs.items():
        assert M.N22_KIN[n][0] == P[r], n
    for n, r in dict(tau_mCa="tmCa", tau_mK="tmK", tau_hK="thK").items():
        assert abs(M.N22_KIN[n][0] - 100.0 * P[r]) < 1e-9, n             # ds -> ms
    assert abs(M.N22_C_PF - 100.0 * P["C"]) < 1e-12


def test_specs_match_the_reference():
    from jiang22_ref import WT
    for n, (v, _, _) in M.KIN.items():
        if n.startswith("w36"):
            continue
        assert WT[n] == v, n
    for g, x in M.G_NS.items():
        assert WT[g] == x, g


PORT = """
import json, sys
sys.path.insert(0, "scripts/worm/debug2")
from jiang22_port_check import neuron_sweep, metrics
import jiang22_port_check as C
from jiang22_ref import SETS, sweep
from wormemu.brain import _neuron
C.SECS = 3.0
h = _neuron()
p = SETS["dvb"]
_, y = sweep(p, 6.0, 3.0)
print(json.dumps(dict(ref=metrics(y[0][:3000]), neuron=metrics(neuron_sweep(h, p, 6.0, 0.025)))))
"""

N22PORT = """
import json, sys
import numpy as np
sys.path.insert(0, "scripts/worm/debug2")
import naudin22_afd_check as C
from wormemu.brain import _neuron
h = _neuron()
out = []
for amp in (-15.0, 25.0):
    ref, v = C.reference(amp), C.neuron_sweep(h, amp, 0.025)
    n = min(len(ref), len(v))
    ref, v = ref[:n], v[:n]
    out.append(dict(dv=float(np.abs(v - ref).max()), dss=float(v[5000:6000].mean() - ref[5000:6000].mean())))
print(json.dumps(out))
"""

BUILD = """
import json, sys
import numpy as np
from wormemu import brain as B, mech
cells, swap, inject, mod, clean = json.loads(sys.argv[1])
def run(tg, without=False):
    reg = list(mech.REGISTRY)
    if without:
        mech.REGISTRY[:] = [m for m in reg if m != "cell_models"]
    try:
        b = B.Brain(cells=cells, toggles=tg)
    finally:
        mech.REGISTRY[:] = reg
    b.reset()
    v = []
    for k in range(400):
        b.extra_pA[b.idx[inject]] = 10.0 if k >= 200 else 0.0
        v.append(list(b.step().v_mV))
    return b, np.array(v)
_, v0 = run({}, without=True)
_, v1 = run({})
b, _ = run(swap)
on = [c for c in cells if c != clean]
bases = [float(base[list(cs).index(b.idx[c])]) for c in on
         for nm, (cs, pv, base, cur) in b._gt.items() if b.idx[c] in cs]
pas = [seg.pas.g for c in on for s in b.cells[b.idx[c]].all for seg in s]
ins = all(b.h.ismembrane(mod, sec=s) for c in on for s in b.cells[b.idx[c]].all)
cl = not any(b.h.ismembrane(mod, sec=s) for s in b.cells[b.idx[clean]].all)
print(json.dumps(dict(dv=float(np.abs(v1 - v0).max()), bases=bases, pas=pas, ins=ins, clean=cl)))
"""


def _sub(code, *args):
    env = dict(os.environ, PYTHONPATH=str(ROOT / "src"))
    r = subprocess.run([sys.executable, "-c", code, *args], capture_output=True, text=True, env=env, cwd=ROOT,
                       timeout=900)
    assert r.returncode == 0, r.stderr[-2000:]
    return json.loads(r.stdout.strip().splitlines()[-1])


def test_mod_matches_cpu_reference():
    out = _sub(PORT)
    r, n = out["ref"], out["neuron"]
    assert r and n
    assert abs(n["peak"] - r["peak"]) <= 0.5 and abs(n["threshold"] - r["threshold"]) <= 0.5
    assert abs(n["half_width_ms"] / r["half_width_ms"] - 1) <= 0.02


def test_naudin_mod_matches_cpu_reference():
    for r in _sub(N22PORT):
        assert r["dv"] <= 1.0 and abs(r["dss"]) <= 0.5


def _swap(cells, swap, inject, mod, clean):
    out = _sub(BUILD, json.dumps([cells, swap, inject, mod, clean]))
    assert out["dv"] == 0.0
    assert out["bases"] and all(x == 0.0 for x in out["bases"])
    assert out["pas"] and all(x == 0.0 for x in out["pas"])
    assert out["ins"] and out["clean"]


def test_default_bit_identical_and_swap_complete():
    _swap(["AVL", "DVB", "PVR"], {"avl_membrane": "jiang22", "dvb_membrane": "jiang22_noexp2"}, "DVB", "j22avl", "PVR")


def test_afd_default_bit_identical_and_swap_complete():
    _swap(["AFDL", "AFDR", "AIYL"], {"afd_membrane": "naudin22"}, "AFDL", "n22afd", "AIYL")
