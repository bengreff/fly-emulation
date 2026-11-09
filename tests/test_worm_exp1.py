"""enteric_exp1 (organs_intestine, wbody2 9 Nov 2026): the enteric muscles' GABA-cation sites as EXP-1 (Beg & Jorgensen
2003), nested `brain` (the brain's gabacat class) the default. Spec: docs/worm/night/wbody2/exp1_port_spec.md."""
import numpy as np
import pytest

pytest.importorskip("neuron")

from wormemu import brain as B  # noqa: E402
from wormemu import mech  # noqa: E402


def _trace(tog, ms=200):
    """Build a DVB-only brain, read its enteric wsyn, run ms 1 ms steps; one brain at a time (NEURON is global)."""
    b = B.Brain(B.sample_worm(None), toggles=tog, cells=["DVB"])
    b.reset()
    m = next(x for x in b.mechs if type(x).__module__.endswith("organs_intestine"))
    k = [c for _, _, post, c in b.wsyn if post == -1][-len(m.wsyn):] if m.wsyn else []
    par = [(w.ec50, w.hill, w.erev, w.gmax, w.tau_rise, w.tau_off, w.tau_des, w.ss, w.mode) for w in m.wsyn]
    gc = b._rk_par.get("gabacat") if getattr(b, "_rk_par", None) else None
    ev = []
    for _ in range(ms):
        b.step(None, 1.0)
        ev.append(np.asarray(b.mech_out["enteric_v_mV"], float).copy())
    out = dict(exp1=m.exp1, q=dict(m.q), cls=k, par=par, gabacat=gc, ev=np.array(ev))
    del b, m
    return out


def test_default_is_brain_and_explicit_brain_is_identical():
    r0, r1 = _trace({}), _trace({"enteric_exp1": "brain"})
    assert r0["exp1"] == "brain" and r0["par"] and r0["par"] == r1["par"]
    gc = r0["gabacat"]
    assert all(p[:3] == (gc["ec50"], gc["hill"], gc["erev"]) for p in r0["par"])
    assert np.array_equal(r0["ev"], r1["ev"])


def test_beg2003_sets_exp1_dose_response_and_reversal_only():
    r0, r1 = _trace({}, 1), _trace({"enteric_exp1": "beg2003"}, 1)
    q = r1["q"]
    assert (q["exp1_ec50_uM"], q["exp1_hill"], q["exp1_erev_mV"]) == (26.4, 1.8, -5.54)
    assert len(r0["par"]) == len(r1["par"]) > 0
    assert set(r1["cls"]) == {mech.RECEPTOR_CLASSES.index("gabacat")}
    for p0, p1 in zip(r0["par"], r1["par"]):
        assert p1[:3] == pytest.approx((0.0264, 1.8, -5.54))
        assert p1[3:] == p0[3:]


@pytest.mark.parametrize("rk", ["graded", "off"])
def test_beg2003_changes_nothing_without_a_dose_response(rk):
    r0, r1 = _trace({"receptor_kinetics": rk}), _trace({"receptor_kinetics": rk, "enteric_exp1": "beg2003"})
    assert r0["par"] == r1["par"]
    assert np.array_equal(r0["ev"], r1["ev"])
