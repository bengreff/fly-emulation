"""Rows 18, 19, 24b (mech/slow_signalling.py, mech/learning.py): homeostasis=lumped is brain_layers' old bias
current exactly, the new forms build and run in the brain, associative on equals off for a fed worm, and the Specs
are inside their bounds. NEURON is one simulator per process: each brain runs in a subprocess."""
import numpy as np

from test_worm_neuromod import _run
from wormemu.mech import learning as LN
from wormemu.mech import slow_signalling as SS

OLD = ("receptors", "plasticity", "neuromod")
NEW = ("receptors", "plasticity", "slow_signalling", "learning", "neuromod")


def test_lumped_homeostasis_is_old_layer():
    old = _run(dict(homeostasis="on"), reg=OLD)
    none = _run(dict(homeostasis="off"), reg=OLD)
    new = _run(dict(homeostasis="lumped", slow_signalling="off", associative="off"), reg=NEW)
    V, V0, V1 = (np.array(x["V"]) for x in (old, none, new))
    assert np.abs(V - V0).max() > 1e-6
    assert np.abs(V - V1).max() < 1e-9
    assert "wormemu.mech.slow_signalling" in new["mechs"] and "wormemu.mech.learning" not in new["mechs"]


def test_new_forms_run_and_fed_worm_is_neutral():
    on = _run(dict(), reg=NEW)
    off = _run(dict(associative="off"), reg=NEW)
    V1, V0 = np.array(on["V"]), np.array(off["V"])
    assert np.isfinite(V1).all() and np.abs(V1 - V0).max() < 1e-9
    assert {"wormemu.mech.slow_signalling", "wormemu.mech.learning"} <= set(on["mechs"])


def test_specs():
    for s in SS.SPECS + LN.SPECS:
        assert s.lo <= s.template <= s.hi, s.id
        assert s.label in ("measured", "derived", "inferred", "guessed", "published_fit"), s.id
    assert SS.form("homeostasis", "on") == "oleary" and SS.form("slow_signalling", True) == "states"
