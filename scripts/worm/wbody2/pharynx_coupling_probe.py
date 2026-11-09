"""Item 2 stage (2) probe (wbody2, 8 Nov 2026): can a brief MC event make a pump at some in-range value of the two
guessed couplings between MC and the muscle? Diagnostic only: nothing here is adopted (class D if a value passes).

Published shape (the bar, written before running): one MC event per pump. Each pharyngeal muscle AP is preceded by
an EPSP-like E1 spike, MC's input (Raizen & Avery 1994, as quoted in PMC4791602; Hobson et al. 2006: E1 present in
>90 % of wild-type pumps, <5 % in ser-7). So 4 Hz brief MC events should give about one pump each.
Pass: pumps >= 0.8 x MC pulses in the window, at some (ph_gap_nS_per_contact, ph_marginal_area_um2) inside their
guessed ranges (0.5-50 nS, 100-2000 um2).

Setup: the pharyngeal sub-brain (pharynx_trace.PN), ledger values, default toggles; diagnostic current into MCL
and MCR: 40 pA x 30 ms pulses at 4 Hz from 0.5 s (MC reaches +12 to +27 mV per pulse, measured). One subprocess
per grid point (fresh NEURON). `nmj=X` also sets the shared NMJ conductance per EM contact (nmj_strength_per_pair,
ledger 0.447 nS, range 0.1-2) that MC's synapses onto the marginal cells use.
Usage: python pharynx_coupling_probe.py [nmj=X]  -> runs/worm/wbody2/pharynx_coupling_probe[_nmjX].json
"""
from __future__ import annotations

import json
import subprocess
import sys
import time
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[3]
GAPS = [0.5, 5.0, 20.0, 50.0]
AREAS = [100.0, 500.0, 2000.0]
SECS, HZ, MS, PA = 3.0, 4.0, 30.0, 40.0


def one(gap, area, nmj=None):
    sys.path.insert(0, str(ROOT / "src"))
    sys.path.insert(0, str(ROOT / "scripts" / "worm"))
    sys.path.insert(0, str(ROOT / "scripts" / "worm" / "wbody2"))
    import at_ledger
    at_ledger.patch()
    from wormemu import brain as B
    from wormemu.mech import organs_pharynx as P
    from pharynx_trace import PN
    spec = B.sample_worm(None)
    spec.values["ph_gap_nS_per_contact"] = gap
    spec.values["ph_marginal_area_um2"] = area
    if nmj is not None:
        spec.values["nmj_strength_per_pair"] = spec.values["nmj_strength_per_pair"] * 0.0 + nmj
    b = B.Brain(spec, toggles={}, cells=PN)
    ph = next(m for m in b.mechs if isinstance(m, P.Mech))
    assert abs(ph.q["ph_gap_nS_per_contact"] - gap) < 1e-9 and abs(ph.q["ph_marginal_area_um2"] - area) < 1e-9
    h = b.h
    v4 = h.Vector().record(ph.sec[P.PHARYNX_MUSCLES[P.METACORPUS[0]]](0.5)._ref_v)
    vm = h.Vector().record(ph.sec["mc2V"](0.5)._ref_v)
    vmc = h.Vector().record(b.soma[b.idx["MCL"]](0.5)._ref_v)
    inj = [b.idx["MCL"], b.idx["MCR"]]
    b.reset()
    pumps, a4max, n_pulse = 0, 0.0, 0
    for k in range(int(SECS * 1000)):
        b.extra_pA[:] = 0.0
        on = k >= 500 and (k - 500) % (1000.0 / HZ) < MS
        if on:
            b.extra_pA[inj] = PA
            n_pulse += (k - 500) % (1000.0 / HZ) == 0
        o = b.step(None, 1.0)
        pumps += int(o.pumps)
        a4max = max(a4max, float(ph.act[P.METACORPUS].mean()))
    v4, vm, vmc = (np.array(x)[500:] for x in (v4, vm, vmc))
    return dict(gap_nS=gap, marginal_um2=area, nmj_nS=nmj, pulses=int(n_pulse), pumps=pumps, pm4_v_max=float(v4.max()),
                pm4_v_med=float(np.median(v4)), mc2V_max=float(vm.max()), MCL_max=float(vmc.max()), a4_max=a4max)


def main():
    if len(sys.argv) >= 3 and "=" not in sys.argv[1]:
        print(json.dumps(one(*(float(x) for x in sys.argv[1:4]))))
        return
    nmj = next((a.split("=")[1] for a in sys.argv[1:] if a.startswith("nmj=")), None)
    rows, t0 = [], time.time()
    for g in GAPS:
        for a in AREAS:
            r = subprocess.run([sys.executable, __file__, str(g), str(a)] + ([nmj] if nmj else []), capture_output=True,
                               text=True, check=True)
            rows.append(json.loads(r.stdout.strip().splitlines()[-1]))
            print(rows[-1], flush=True)
    ok = [r for r in rows if r["pumps"] >= 0.8 * r["pulses"]]
    res = dict(bar="pumps >= 0.8 x MC pulses at some in-range (gap, marginal area)", nmj_nS=nmj, secs=SECS, pulse=[PA, MS, HZ],
               rows=rows, passing=ok, verdict="D (a value passes)" if ok else "no in-range value passes",
               wall_s=time.time() - t0)
    out = ROOT / f"runs/worm/wbody2/pharynx_coupling_probe{'_nmj' + nmj if nmj else ''}.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(res, indent=1))
    print(res["verdict"], f"{res['wall_s']:.0f} s")


if __name__ == "__main__":
    main()
