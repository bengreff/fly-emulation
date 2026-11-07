"""Row 24 (mech/plasticity.py, wsyn.mod): stp and habituation off give the row 7 synapse exactly, on runs in the
brain, the nested forms nest, and the numpy reference has q = 1 when off. NEURON is one simulator per process, so
each brain runs in a subprocess (the test_worm_neuromod helper)."""
import numpy as np

from test_worm_neuromod import _run
from wormemu.mech import plasticity as P

T = {s.id: s.template for s in P.SPECS}


def test_off_is_row7():
    old = _run(dict(), reg=("receptors", "neuromod"))
    off = _run(dict(stp="off", habituation="off"), reg=("receptors", "plasticity", "neuromod"))
    on = _run(dict(), reg=("receptors", "plasticity", "neuromod"))
    V0, V1, V2 = (np.array(x["V"]) for x in (old, off, on))
    assert np.abs(V0 - V1).max() < 1e-9
    assert np.isfinite(V2).all() and np.abs(V2 - V0).max() > 1e-6
    assert "wormemu.mech.plasticity" in on["mechs"]


def test_forms_nest():
    dr = P.wsyn_params(T, "ach")
    tm, dep, off = (P.wsyn_params(T, "gaba", f) for f in ("tsodyks_markram", "depression", "off"))
    assert dr["kmax"] > dr["k0"] and tm["kmax"] == tm["k0"] and tm["F1"] < 1
    assert dep["F1"] == 1 and dep["kmax"] == dep["k0"] and off["beta"] == 0 and off["F1"] == 1
    assert P.wsyn_params(T, "ach", hab=True, touch=True)["beta_h"] > 0 == P.wsyn_params(T, "ach")["beta_h"]
    for s in P.SPECS:
        assert s.lo <= s.template <= s.hi, s.id


def test_reference_off_is_one():
    from wormemu.mech import receptors as R
    rec = R.site_params({s.id: s.template for s in R.SPECS}, "lacr", 2)
    rel = dict(delta=5.0, k=0.1166666666666666, Vth=-20.0)
    v = np.full(4000, -60.0)
    v[100:120] = 0.0
    _, q0 = P.numpy_reference(v, 0.5, P.wsyn_params(T, "ach", "off", hab=False), rel, rec)
    _, q1 = P.numpy_reference(v, 0.5, P.wsyn_params(T, "ach"), rel, rec)
    assert np.all(q0 == 1.0) and q1.min() < 0.7
