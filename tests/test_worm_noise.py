"""Row 26 (mech/noise.py): quantal_noise=off with channel_noise=off is the brain without the module (qn = 1 is
neutral in wsyn.mod), each form runs finite in the brain and changes it, and the Specs are inside their bounds. The
generators' own checks are scripts/worm/noise_unit_check.py and chnoise_unit_check.py. NEURON is one simulator per
process: each brain runs in a subprocess."""
import numpy as np

from test_worm_neuromod import _run
from wormemu.mech import noise as NZ

WITHOUT = ("receptors", "plasticity", "slow_signalling", "learning", "neuromod")
WITH = WITHOUT + ("noise",)


def test_off_is_without_module():
    none = _run(dict(), reg=WITHOUT)
    off = _run(dict(quantal_noise="off", channel_noise="off"), reg=WITH)
    V0, V1 = np.array(none["V"]), np.array(off["V"])
    assert np.abs(V0 - V1).max() < 1e-12
    assert "wormemu.mech.noise" not in off["mechs"] and off["noise"] == {}   # off: not built (registry contract)


def test_quantal_runs_and_acts():
    on = _run(dict(channel_noise="off"), reg=WITH)
    off = _run(dict(quantal_noise="off", channel_noise="off"), reg=WITH)
    V1, V0 = np.array(on["V"]), np.array(off["V"])
    assert np.isfinite(V1).all() and np.abs(V1).max() < 200
    assert np.abs(V1 - V0).max() > 1e-3
    nz = on["noise"]
    assert nz["vesicles_per_s"] > 0 and 0 < nz["qn_sd"] < 100


def test_channel_runs_and_acts():
    on = _run(dict(quantal_noise="off"), reg=WITH)
    off = _run(dict(quantal_noise="off", channel_noise="off"), reg=WITH)
    V1, V0 = np.array(on["V"]), np.array(off["V"])
    assert np.isfinite(V1).all() and np.abs(V1).max() < 200
    assert np.abs(V1 - V0).max() > 1e-3
    cn = on["chnoise"]
    assert cn["I_rms_pA"] > 0 and cn["channels_median"] > 0


def test_specs_and_form():
    for s in NZ.SPECS:
        assert s.lo <= s.template <= s.hi, s.id
        assert s.label in ("measured", "derived", "inferred", "guessed", "published_fit"), s.id
    assert NZ.form(None) == "off" and NZ.form("quantal") == "quantal"
    assert NZ.cform("on") == "diffusion" and NZ.cform(None) == "off"
