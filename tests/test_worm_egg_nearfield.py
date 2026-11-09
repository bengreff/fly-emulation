"""egg_laying's vm2 5-HT read and wneuro's HSN near-field term (neuromod amine_synaptic; wbody2, 9 Nov 2026, inbox
02:45). Off (the default): every vm reads the pool, the code before. nicholson: vm2 reads the pool plus
neuromod.near_nM('serotonin', HSN), vm1 the pool alone. Check: scripts/worm/wbody2/egg_near_check.py."""
import numpy as np
import pytest

pytest.importorskip("neuron")

from wormemu import brain as B  # noqa: E402
from wormemu.mech import organs_egglaying as E  # noqa: E402


def _trace(tog, ms=300):
    """One brain at a time (NEURON is global): HSNL and HSNR with every organ; records, at the last step, what
    egg_laying used (pool 5-HT, near field) and set (the vm conductances or clamp currents)."""
    b = B.Brain(B.sample_worm(None), toggles=tog, cells=["HSNL", "HSNR"])
    b.reset()
    m = next(x for x in b.mechs if isinstance(x, E.Mech))
    used = {}
    conc, near = m.concentrations, m.near_5ht

    def conc_w():
        r = conc()
        used.setdefault("c5", r[0])
        return r

    def near_w():
        used["near"] = near()
        used["near_direct"] = None if m.nm is False or m.nm is None else m.nm.near_nM("serotonin", m.hsn)
        return used["near"]
    m.concentrations, m.near_5ht = conc_w, near_w
    for _ in range(ms):
        used.clear()
        b.step(None, 1.0)
    vm = [n for n in E.SEX_MUSCLES if n in E.VM]
    g = {n: pp.g * 1000.0 for n, pp in zip(vm, m.gvm)} if m.gvm else {}
    amp = {n: c.amp for n, c in zip(E.SEX_MUSCLES, m.clamp) if n in E.VM} if m.clamp else {}
    out = dict(used=dict(used), g=g, amp=amp, mo={k: b.mech_out[k] for k in ("egg_5ht_occ", "egg_5ht_occ_vm2",
                                                                               "egg_5ht_near_nM")}, ec5=m.ec5.copy())
    del b, m
    return out


def test_off_every_vm_reads_the_pool():
    r = _trace({})
    assert r["used"]["near"] is None
    assert r["mo"]["egg_5ht_near_nM"] == 0.0 and r["mo"]["egg_5ht_occ_vm2"] == r["mo"]["egg_5ht_occ"]
    assert len(set(r["g"].values())) == 1


@pytest.mark.parametrize("solver", ["implicit", "explicit"])
def test_nicholson_vm2_reads_pool_plus_near_field_and_vm1_the_pool(solver):
    r = _trace({"amine_synaptic": "nicholson", "egg_g_solver": solver})
    u, mo, ec5 = r["used"], r["mo"], r["ec5"]
    assert u["near"] > 0.0 and u["near"] == u["near_direct"] and mo["egg_5ht_near_nM"] == u["near"]
    c = u["c5"]
    assert mo["egg_5ht_occ"] == float(np.mean(c / (c + ec5)))
    assert mo["egg_5ht_occ_vm2"] == float(np.mean((c + u["near"]) / (c + u["near"] + ec5)))
    assert mo["egg_5ht_occ_vm2"] > mo["egg_5ht_occ"]
    x = r["g"] if solver == "implicit" else r["amp"]
    vm1 = {v for n, v in x.items() if n.startswith("vm1")}
    vm2 = {v for n, v in x.items() if n.startswith("vm2")}
    if solver == "implicit":
        assert len(vm1) == 1 and len(vm2) == 1 and vm2.pop() > vm1.pop()
    else:                                     # currents differ by V too; vm2 gets more inward current on average
        assert np.mean(list(vm2)) > np.mean(list(vm1))
