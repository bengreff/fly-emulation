"""AWA inward rectifier forms (DEBUG_TRIAGE line 7, wbrain2, 8 Nov 2026): mech/senses_chem's awa_kir toggle, the mod's
kir_form and the CPU reference senses_checks.liu_kir.

"as_printed" must be the old equation exactly; "smooth_min" (the default, the authors' code form) must be outward above
E_K, ohmic well below it and saturate at gKir I0 (4 pA). The NEURON mod must match the CPU reference in both forms.

NEURON is one simulator per process, so the mod runs in its own subprocess."""
import json
import os
import subprocess
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts" / "worm"))
import senses_checks as S  # noqa: E402

from wormemu.mech import senses_chem  # noqa: E402

V = np.array([-150.0, -100.0, -84.0, -79.0, -75.0, -60.0, -50.0, -30.0, 0.0, 40.0])


def test_default_and_forms():
    on = {t[0]: t[3] for t in senses_chem.MECHANISMS}
    assert on["awa_kir"] == "smooth_min" and senses_chem.AWA_KIR == ("smooth_min", "as_printed")


def test_as_printed_is_the_old_equation():
    P = dict(S.LIU, kir="as_printed")
    old = -P["gKir"] * (P["beta"] * np.log1p(np.exp(-(V - P["vK"] + P["I0"]) / P["beta"])) + P["I0"])
    assert np.array_equal(S.liu_kir(V, P), old)
    assert np.all(old < 0)                         # the reason for the fix: inward at every voltage


def test_smooth_min_is_a_k_rectifier():
    P = S.LIU
    i = S.liu_kir(V, P)
    assert np.all(np.sign(i[V != P["vK"]]) == np.sign(V[V != P["vK"]] - P["vK"]))       # reverses at E_K
    assert np.isclose(S.liu_kir(np.array([P["vK"] - 60.0]), P)[0], P["gKir"] * -60.0, rtol=1e-3)   # ohmic below
    assert np.isclose(S.liu_kir(np.array([40.0]), P)[0], P["gKir"] * P["I0"], rtol=1e-6)   # saturates above
    assert np.all(np.diff(i) >= 0)


MOD = """
import json, sys
from wormemu.brain import _neuron
h = _neuron()
s = h.Section(name="awa")
s.L = s.diam = (150.0 / 3.141592653589793) ** 0.5          # area 150 um2: C = 1.5 pF at cm 1
s.cm, s.nseg = 1.0, 1
s.insert("awa_liu")
out = {}
for form in (0, 1):
    s.kir_form_awa_liu = form
    r = []
    for v in json.loads(sys.argv[1]):
        h.finitialize(v)
        h.fcurrent()
        r.append(s(0.5).awa_liu.iKir * 150e-8 * 1e9)           # mA/cm2 x cm2 -> pA
    out[form] = r
print(json.dumps(out))
"""


def test_mod_matches_cpu_both_forms():
    env = dict(os.environ, PYTHONPATH=str(ROOT / "src"))
    r = subprocess.run([sys.executable, "-c", MOD, json.dumps(V.tolist())], capture_output=True, text=True, env=env,
                       cwd=ROOT, timeout=600)
    assert r.returncode == 0, r.stderr[-2000:]
    out = json.loads(r.stdout.strip().splitlines()[-1])
    for form, k in (("smooth_min", "0"), ("as_printed", "1")):
        assert np.allclose(out[k], S.liu_kir(V, dict(S.LIU, kir=form)), rtol=2e-3, atol=2e-3), (form, out[k])


def test_awa_gscale_spares_synapses():
    """Liu's membrane replaces AWA's channels and leak only: _awa_gscale zeroes every dens_* and the leak for AWA and
    leaves "release" and "rec_<class>" to the brain (wbrain2, 9 Nov 2026: they were 0, silencing AWA's synapses)."""
    from wormemu.mech import G_SCALE_NAMES
    m = senses_chem.Mech.__new__(senses_chem.Mech)
    m.n, m.awa_idx = 4, np.array([1])
    g = m._awa_gscale()
    assert not any(k == "release" or k.startswith("rec_") for k in g)
    chans = [k for k in G_SCALE_NAMES if k.startswith("dens_")] + ["leak"]
    assert sorted(g) == sorted(chans)
    for k in chans:
        assert g[k].tolist() == [1.0, 0.0, 1.0, 1.0]
