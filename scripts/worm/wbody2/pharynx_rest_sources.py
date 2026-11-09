"""Item 2 stage 2 (wbody2, 9 Nov 2026): what holds the coupled pharynx at -65 mV, and how MC still reaches the muscle
in the eat-2 null. Diagnostic only, nothing adopted.

Measured before (pharynx_stage2_probe.py, 00:47): cook, MC undriven, at 490 ms pm5 -65.0 mV; organ chemical synapses
cut -68.5; neuron-pm gaps cut -58.2; all inputs cut -72.2 (leak reversal -73). pharynx_stage2_check.py bar 5 (00:47):
under eat2 with the EAT-2 synapses at 0, MC pulses still move pm by up to 1.62 mV against the undriven null.
A  rest     cook, MC undriven, 0.5 s: at 490 ms each organ chemical synapse's current into the pharyngeal cells, summed
            by presynaptic neuron, with that neuron's V (the synapses release by a sigmoid around Vth -20 mV, so a
            neuron near rest releases almost nothing; a large share means a depolarised presynaptic neuron)
B  route    eat2 with EAT-2 at 0, MC driven (the check's pulses) vs undriven, 1 s: every brain cell's peak |dV|, and
            for those moving > 1 mV their organ synapses (the route of bar 5's 1.62 mV)
C  whole    (added 00:51, after A showed MCL resting at -42 mV in the sub-brain, where the whole brain held it at
            -70 mV on 8 Nov) the check's bar 3 setup in the whole brain (cells=None), cook and eat2, 3 s. Bar, written
            before running: under eat2, pumps >= 0.8 x MC pulses (the check's bar 3, unchanged). Reported: pm5 and MCL
            V at 490 ms, pm5 peak after 500 ms
D  mask     (added 00:55, after C: on main's mask MC rests near -42 mV, wbrain2's line 15/16 fix, remainder D, its night
            file 22:49; under the old mask cengen_all it rested at -70 mV) the check's bar 3 setup in the sub-brain with
            expression_map=cengen_all, cook and eat2, 3 s: a counterfactual, not a candidate (the old mask is the A that
            wbrain2 fixed). Bar, written before running: under eat2, pumps >= 0.8 x MC pulses. Reported as C
Usage: python pharynx_rest_sources.py [C | D]  -> runs/worm/wbody2/pharynx_rest_sources.json (C: _whole.json)
"""
from __future__ import annotations

import json
import subprocess
import sys
from collections import defaultdict
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[3]
OUT = ROOT / "runs/worm/wbody2"
HZ, MS, PA = 4.0, 30.0, 40.0


def one(cfg):
    sys.path.insert(0, str(ROOT / "src"))
    sys.path.insert(0, str(ROOT / "scripts" / "worm"))
    sys.path.insert(0, str(ROOT / "scripts" / "worm" / "wbody2"))
    import at_ledger
    at_ledger.patch()
    from wormemu import brain as B
    from wormemu.mech import organs_pharynx as P
    from pharynx_trace import PN
    spec = B.sample_worm(None)
    tg = {"ph_mc_route": cfg["route"], **cfg.get("tog", {})}
    b = B.Brain(spec, toggles=tg, cells=None if cfg.get("whole") else PN)
    ph = next(m for m in b.mechs if isinstance(m, P.Mech))
    if cfg.get("null"):
        for pp in ph.eat2_syn:
            pp.gmax = 0.0
    h = b.h
    tv = h.Vector().record(h._ref_t)
    rn = [n for n in b.cell_names if n in PN] if cfg.get("whole") else b.cell_names
    vn = {n: h.Vector().record(b.soma[b.idx[n]](0.5)._ref_v) for n in rn}
    vp = {n: h.Vector().record(ph.sec[n](0.5)._ref_v) for n in ph.names if n.startswith("pm5")}
    ids = {id(pp) for pp in ph.wsyn}
    own = [(pp, pre) for pp, pre, post, _ in b.wsyn if post == -1 and id(pp) in ids]
    inj = [b.idx["MCL"], b.idx["MCR"]]
    b.reset()
    secs = cfg["secs"]
    out = {}
    pumps = n_pulse = 0
    for k in range(int(secs * 1000)):
        b.extra_pA[:] = 0.0
        if cfg.get("mc") and k >= 500 and (k - 500) % (1000.0 / HZ) < MS:
            b.extra_pA[inj] = PA
            n_pulse += (k - 500) % (1000.0 / HZ) == 0
        pumps += int(b.step(None, 1.0).pumps)
        if k == 489:
            by = defaultdict(float)
            for pp, pre in own:
                by[b.cell_names[pre]] += float(pp.i) * 1000.0            # nA -> pA, outward positive
            out["syn_pA_by_pre"] = {n: round(x, 3) for n, x in sorted(by.items(), key=lambda kv: kv[1])}
            out["v_pre_490"] = {n: round(float(b.soma[b.idx[n]](0.5).v), 2) for n in by}
    t = np.array(tv)
    out.update(pumps=pumps, pulses=int(n_pulse))
    if cfg.get("whole") or cfg.get("tog"):
        i, late = int(np.searchsorted(t, 490.0)), t >= 500.0
        P5 = np.array([np.array(x) for x in vp.values()])
        out.update(pm5_490=round(float(P5[:, i].mean()), 2), pm5_max=round(float(P5[:, late].max()), 2),
                   MCL_490=round(float(np.array(vn["MCL"])[i]), 2), MCR_490=round(float(np.array(vn["MCR"])[i]), 2))
        return {k: v for k, v in out.items() if k not in ("syn_pA_by_pre", "v_pre_490")}
    out["V"] = {n: np.array(x).tolist() for n, x in vn.items()}
    out["t"] = t.tolist()
    out["n_syn_by_pre"] = {b.cell_names[p]: sum(1 for _, q in own if q == p) for p in sorted({q for _, q in own})}
    return out


def sub(cfg):
    r = subprocess.run([sys.executable, __file__, "one", json.dumps(cfg)], capture_output=True, text=True)
    if r.returncode:
        raise RuntimeError(r.stderr[-3000:])
    return json.loads(r.stdout.strip().splitlines()[-1])


def main():
    if len(sys.argv) >= 3 and sys.argv[1] == "one":
        print(json.dumps(one(json.loads(sys.argv[2]))))
        return
    if len(sys.argv) >= 2 and sys.argv[1] == "D":
        c = {r: sub(dict(route=r, mc=True, secs=3.0, tog={"expression_map": "cengen_all"})) for r in ("cook", "eat2")}
        c["pass_"] = c["eat2"]["pumps"] >= 0.8 * c["eat2"]["pulses"]
        (OUT / "pharynx_rest_sources_mask.json").write_text(json.dumps(c, indent=1))
        print(json.dumps(c, indent=1))
        return
    if len(sys.argv) >= 2 and sys.argv[1] == "C":
        c = {r: sub(dict(route=r, mc=True, secs=3.0, whole=True)) for r in ("cook", "eat2")}
        c["pass_"] = c["eat2"]["pumps"] >= 0.8 * c["eat2"]["pulses"]
        (OUT / "pharynx_rest_sources_whole.json").write_text(json.dumps(c, indent=1))
        print(json.dumps(c, indent=1))
        return
    a = sub(dict(route="cook", mc=False, secs=0.5))
    q = sub(dict(route="eat2", mc=False, null=True, secs=1.0))
    z = sub(dict(route="eat2", mc=True, null=True, secs=1.0))
    late = np.array(q["t"]) >= 500.0
    dv = {n: float(np.max(np.abs(np.array(z["V"][n])[late] - np.array(q["V"][n])[late]))) for n in q["V"]}
    moved = {n: round(x, 3) for n, x in sorted(dv.items(), key=lambda kv: -kv[1]) if x > 1.0}
    res = dict(A=dict(syn_pA_by_pre=a["syn_pA_by_pre"], v_pre_490=a["v_pre_490"], n_syn_by_pre=a["n_syn_by_pre"],
                      total_pA=round(sum(a["syn_pA_by_pre"].values()), 3),
                      v_rest_490={n: round(float(np.array(a["V"][n])[-11]), 2) for n in a["V"]}),
               B=dict(moved_gt_1mV=moved, organ_syn_of_moved={n: q["n_syn_by_pre"].get(n, 0) for n in moved}))
    (OUT / "pharynx_rest_sources.json").write_text(json.dumps(res, indent=1))
    print(json.dumps(res, indent=1)[:6000])


if __name__ == "__main__":
    main()
