"""Never-checked row 8 (wbrain2, 9 Nov 2026): AVA-VA5 gap coupling against Liu, Chen, Mailler and Wang 2017 (Nat
Commun 8:14818, PMC5364397, CC-BY) Fig 6, digitised in the night file ("Item 8"). The full brain at the template,
default toggles, quantal and channel noise off.
    vc  somatic SEClamps (rs 10 MOhm) hold AVA and VA05 at -30 mV; the other cell steps -110 to +50 mV (20 mV, 250 ms,
        500 ms apart); I_j = the held cell's clamp current (inward negative, pA), last 50 ms of the step minus the 50
        ms before it; beside it the direct junctional current, the AVA-VA05 gap halves on the held cell summed
    cc  no clamps; +-10, 20, 30 pA into VA05 for 1 s, 1 s apart, then into AVA; CC = dV(other) / dV(injected), means
        of the last 200 ms of the step vs the 200 ms before it
Usage: python gap_ava_va5.py <vc|cc> [AVAR|AVAL] [floor|floor2|floor3]   -> runs/worm/wbrain2/gap/<mode>_<cell>[_<form>].json
       (the form is a build of gap_rin_probe.py: gap conductances at their range floors; default the template)
       python gap_ava_va5.py score                   (the night file's five bars)
"""
from __future__ import annotations

import json
import sys
import time
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[3]
OUT = ROOT / "runs/worm/wbrain2/gap"
VA, DT, HOLD = "VA05", 5.0, -30.0
STEPS = [-110.0, -90.0, -70.0, -50.0, -10.0, 10.0, 30.0, 50.0]      # -30 is the holding level itself
AMPS = [-30.0, -20.0, -10.0, 10.0, 20.0, 30.0]
BARS = {"1_ava_held_va5_to_+50_pA": (-12.7, -2.5), "2_va5_held_ava_to_-110_pA": (0.0, 10.1),
        "3_cc_into_va5_+30_pct": (3.3, 21.1), "4_cc_into_ava_+30_pct": (0.0, 9.7)}
FIG = {"vc_ava_held": {-110.0: 1.8, 50.0: -7.6}, "vc_va5_held": {-110.0: 5.0, 50.0: -1.2},   # pA, keyed by the
       "cc_into_va5": {-30: 3.8, -20: 3.8, -10: 2.8, 10: 8.1, 20: 10.9, 30: 12.2},           # stepped cell's level
       "cc_into_ava": {-30: 3.6, -20: 4.0, -10: 4.3, 10: 3.4, 20: 3.1, 30: 3.4}}             # (digitised)


def build(ava, form="template"):
    sys.path.insert(0, str(ROOT / "src"))
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    from wormemu import brain as B
    from gap_rin_probe import spec_for
    placed, orig = [], B.Brain._gap

    def rec(self, seg_a, seg_b, g_uS, kind, into=None, ratio=1.0):
        n0 = len(self.conn)
        orig(self, seg_a, seg_b, g_uS, kind, into=into, ratio=ratio)
        placed.append((seg_a, seg_b, g_uS, ratio, into, self.conn[n0:]))

    B.Brain._gap = rec
    b = B.Brain(spec_for(form), toggles=dict(quantal_noise="off", channel_noise="off"))
    B.Brain._gap = orig
    owner = {seg.sec.name(): b.cell_names[i] for i in range(len(b.cell_names)) for seg, _ in b.segs[i]}
    halves = {ava: [], VA: []}                     # the AVA-VA05 junction halves, by the cell each sits on
    g_into_ava = g_back = 0.0
    for sa, sb, g, ratio, into, pps in placed:
        ca, cb = owner.get(sa.sec.name()), owner.get(sb.sec.name())      # organ sections are not in segs
        if {ca, cb} != {ava, VA}:
            continue
        halves[ca].append(pps[0])
        halves[cb].append(pps[1])
        rect_to_ava = into is not None and owner.get(into.sec.name()) == ava
        g_into_ava += g * 1e3
        g_back += g * 1e3 / (ratio if rect_to_ava else 1.0)
    return b, halves, dict(n_junctions=len(halves[ava]), g_into_ava_nS=g_into_ava, g_into_va5_nS=g_back)


def run_for(b, ms, f=None):
    out = []
    for _ in range(int(round(ms / DT))):
        b.step(None, DT)
        if f is not None:
            out.append(f())
    return np.array(out)


def vc(ava, form):
    b, halves, info = build(ava, form)
    h = b.h
    cl = {}
    for c in (ava, VA):
        k = h.SEClamp(b.soma[b.idx[c]](0.5))
        k.dur1, k.amp1, k.rs = 1e9, HOLD, 10.0
        cl[c] = k
    b.reset()
    run_for(b, 1000.0)
    res = {}
    for held, stepped in ((ava, VA), (VA, ava)):
        def sample():
            return (cl[held].i * 1e3, sum(pp.i for pp in halves[held]) * 1e3)   # clamp = membrane current; junction (inward -)
        rows = []
        for vs in STEPS:
            pre = run_for(b, 50.0, sample)
            cl[stepped].amp1 = vs
            during = run_for(b, 250.0, sample)
            cl[stepped].amp1 = HOLD
            run_for(b, 450.0)
            rows.append(dict(v_step=vs, v_j=HOLD - vs, I_j_pA=float(during[-10:, 0].mean() - pre[:, 0].mean()),
                             I_direct_pA=float(during[-10:, 1].mean() - pre[:, 1].mean())))
            print(held, "held,", stepped, "to", vs, rows[-1], flush=True)
        res["vc_ava_held" if held == ava else "vc_va5_held"] = rows
    return dict(mode="vc", ava=ava, form=form, **info, **res)


def cc(ava, form):
    b, halves, info = build(ava, form)
    b.reset()
    run_for(b, 2000.0)
    ia, iv = b.idx[ava], b.idx[VA]

    def sample():
        return (b.soma[ia](0.5).v, b.soma[iv](0.5).v)
    res = {}
    for inj, other, key in ((iv, ia, "cc_into_va5"), (ia, iv, "cc_into_ava")):
        rows = []
        for a in AMPS:
            pre = run_for(b, 200.0, sample)
            b.extra_pA[inj] = a
            during = run_for(b, 1000.0, sample)
            b.extra_pA[inj] = 0.0
            run_for(b, 800.0)
            d = during[-40:].mean(axis=0) - pre.mean(axis=0)
            dv_inj, dv_oth = (d[1], d[0]) if inj == iv else (d[0], d[1])
            rows.append(dict(I_inj_pA=a, dV_injected_mV=float(dv_inj), dV_other_mV=float(dv_oth),
                             cc_pct=float(100.0 * dv_oth / dv_inj), v_pre_injected=float(pre.mean(axis=0)[1 if inj == iv else 0])))
            print(key, rows[-1], flush=True)
        res[key] = rows
    return dict(mode="cc", ava=ava, form=form, **info, **res)


def score():
    for ava, sfx in (("AVAR", ""), ("AVAL", ""), ("AVAR", "_floor"), ("AVAR", "_floor2"), ("AVAR", "_floor3")):
        f1, f2 = OUT / f"vc_{ava}{sfx}.json", OUT / f"cc_{ava}{sfx}.json"
        if not (f1.exists() and f2.exists()):
            print(ava + sfx, "missing")
            continue
        V, C = json.loads(f1.read_text()), json.loads(f2.read_text())
        a = {r["v_step"]: r for r in V["vc_ava_held"]}
        v = {r["v_step"]: r for r in V["vc_va5_held"]}
        ci = {r["I_inj_pA"]: r for r in C["cc_into_va5"]}
        ca = {r["I_inj_pA"]: r for r in C["cc_into_ava"]}
        got = {"1_ava_held_va5_to_+50_pA": a[50.0]["I_j_pA"], "2_va5_held_ava_to_-110_pA": v[-110.0]["I_j_pA"],
               "3_cc_into_va5_+30_pct": ci[30.0]["cc_pct"], "4_cc_into_ava_+30_pct": ca[30.0]["cc_pct"]}
        print(f"{ava}{sfx}: {V['n_junctions']} AVA-VA05 junctions, {V['g_into_ava_nS']:.4f} nS into AVA, "
              f"{V['g_into_va5_nS']:.4f} nS back")
        for k, x in got.items():
            lo, hi = BARS[k]
            print(f"  {k}: {x:.3f} (bar {lo} to {hi}) {'pass' if lo <= x <= hi else 'FAIL'}")
        d1 = abs(a[50.0]["I_j_pA"]) > abs(a[-110.0]["I_j_pA"])
        d2 = abs(v[-110.0]["I_j_pA"]) > abs(v[50.0]["I_j_pA"])
        print(f"  5_direction: AVA held |{a[50.0]['I_j_pA']:.3f}| vs |{a[-110.0]['I_j_pA']:.3f}|, VA5 held "
              f"|{v[-110.0]['I_j_pA']:.3f}| vs |{v[50.0]['I_j_pA']:.3f}|: {'pass' if d1 and d2 else 'FAIL'}")
        print("  direct junctional current (pA):", {k: [round(r["I_direct_pA"], 3) for r in V[k]] for k in
                                                    ("vc_ava_held", "vc_va5_held")})
        print("  CC into VA5:", [round(ci[x]["cc_pct"], 2) for x in AMPS], " fig", list(FIG["cc_into_va5"].values()))
        print("  CC into AVA:", [round(ca[x]["cc_pct"], 2) for x in AMPS], " fig", list(FIG["cc_into_ava"].values()))


if __name__ == "__main__":
    a = sys.argv[1:]
    if a[0] == "score":
        score()
    else:
        t0, cell, form = time.time(), (a[1] if len(a) > 1 else "AVAR"), (a[2] if len(a) > 2 else "template")
        r = (vc if a[0] == "vc" else cc)(cell, form)
        r["wall_s"] = round(time.time() - t0, 1)
        OUT.mkdir(parents=True, exist_ok=True)
        (OUT / f"{a[0]}_{cell}{'' if form == 'template' else '_' + form}.json").write_text(json.dumps(r, indent=1))
        print("saved", a[0], cell, r["wall_s"], "s")
