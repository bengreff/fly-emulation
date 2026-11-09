"""Item 8's classification probe (wbrain2, 9 Nov 2026): why gap_ava_va5.py's coupling coefficients come out the wrong
way round. Liu, Chen, Mailler and Wang 2017 measured the input resistance in situ: AVA 2.50 +- 0.19 GOhm (n 9),
VA5 3.47 +- 0.18 GOhm (n 22). This measures ours the same way (soma current clamp, dV / I, last 200 ms of a 1 s step
vs the 200 ms before it) and the CC at +30 pA, in four builds:
    alone    each cell on its own (cells=[AVAR] and cells=[VA05]): the membrane only
    pair     cells=[AVAR, VA05]: the membrane plus the AVA-VA05 junction, no rest of the network
    full     the whole brain, template (what gap_ava_va5.py ran)
    floor    the whole brain with gap_open_channels_per_em at its range floor (1/6 channel per EM contact)
    floor2   floor, and every innexin unitary conductance at its floor (50 pS): 8.3 pS per EM contact
    floor3   floor2, and the hypodermis, glia and end-organ per-contact gaps at their floor (0.05 nS)
Quantal and channel noise off, default toggles otherwise; extra toggles as key=value arguments (other_cells=off drops
the hypodermis, whose Cook gaps reach AVAL, AVAR and 57 other cells), added to the output name. Each build also sums
the gap conductance placed on AVAR. "nosyn" silences the chemical synapses onto AVAR (a decomposition, not a model).
Usage: python gap_rin_probe.py <alone [AVAR|VA05]|pair|full|floor|floor2|floor3> [toggle=value ...] [nosyn]   -> runs/worm/wbrain2/gap/rin_*.json
       python gap_rin_probe.py score
"""
from __future__ import annotations

import copy
import json
import sys
import time
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[3]
OUT = ROOT / "runs/worm/wbrain2/gap"
AVA, VA, DT = "AVAR", "VA05", 5.0
PULSES = [-10.0, 30.0]
LIU_GOHM = {AVA: 2.50, VA: 3.47}


TG = dict(a.split("=", 1) for a in sys.argv[2:] if "=" in a)
NOSYN = "nosyn" in sys.argv[2:]


def spec_for(form):
    """The template worm, or one of the floor builds (also used by gap_ava_va5.py)."""
    sys.path.insert(0, str(ROOT / "src"))
    from wormemu import brain as B
    spec = B.sample_worm(None)
    if form.startswith("floor"):
        spec = copy.copy(spec)
        spec.values = dict(spec.values)
        spec.values["gap_open_channels_per_em"] = 1.0 / 6.0
        if form in ("floor2", "floor3"):         # and every innexin's unitary conductance at its floor, 50 pS
            from wormemu.mech import structure_rules as SR
            spec.values.update({s.id: s.lo for s in SR.SPECS if s.id.startswith("gap_unitary_")})
            spec.values["gap_innexin_unitary"] = 50.0
        if form == "floor3":                     # and the non-neural per-contact gaps at theirs (wbody2's Specs)
            spec.values.update({k: 0.05 for k in ("other_gap_nS_per_contact", "glia_gap_nS_per_contact",
                                                  "endo_gap_nS_per_contact")})
    return spec


def build(form, cells):
    from wormemu import brain as B
    spec = spec_for(form)
    placed, orig = [], B.Brain._gap

    def rec(self, seg_a, seg_b, g_uS, kind, into=None, ratio=1.0):
        orig(self, seg_a, seg_b, g_uS, kind, into=into, ratio=ratio)
        placed.append((seg_a.sec.name(), seg_b.sec.name(), g_uS, ratio, None if into is None else into.sec.name()))

    B.Brain._gap = rec
    b = B.Brain(spec, toggles=dict(quantal_noise="off", channel_noise="off", **TG), cells=cells)
    B.Brain._gap = orig
    own = {seg.sec.name(): b.cell_names[i] for i in range(len(b.cell_names)) for seg, _ in b.segs[i]}
    n_off = 0
    if NOSYN:                                    # the chemical synapses onto AVAR silenced (decomposition only)
        for pp in b.conn:
            nm = pp.hname().split("[")[0]
            if ("wsyn" in nm or "_syn" in nm) and own.get(pp.get_segment().sec.name()) == AVA:
                if hasattr(pp, "gmax"):
                    pp.gmax = 0.0
                else:
                    pp.weight = 0.0
                n_off += 1
    g_ava = g_ava_va = 0.0
    for sa, sb, g, ratio, into in placed:
        ca, cb = own.get(sa), own.get(sb)
        if AVA in (ca, cb):
            g_ava += g * 1e3                      # nS, the full (forward) weight of every junction on AVAR
            if {ca, cb} == {AVA, VA}:
                g_ava_va += g * 1e3
    return b, dict(n_gaps_total=len(placed), g_gap_on_AVAR_nS=g_ava, g_AVAR_VA05_nS=g_ava_va, syn_off_on_AVAR=n_off)


def run_for(b, ms, f=None):
    out = []
    for _ in range(int(round(ms / DT))):
        b.step(None, DT)
        if f is not None:
            out.append(f())
    return np.array(out)


def measure(b, cells):
    b.reset()
    run_for(b, 2000.0)
    ix = {c: b.idx[c] for c in cells}

    def sample():
        return [b.soma[ix[c]](0.5).v for c in cells]
    rows = []
    for inj in cells:
        for a in PULSES:
            pre = run_for(b, 200.0, sample)
            b.extra_pA[ix[inj]] = a
            during = run_for(b, 1000.0, sample)
            b.extra_pA[ix[inj]] = 0.0
            run_for(b, 800.0)
            d = during[-40:].mean(axis=0) - pre.mean(axis=0)
            k = cells.index(inj)
            r = dict(inj=inj, I_pA=a, v_rest=float(pre.mean(axis=0)[k]), dV_mV=float(d[k]),
                     R_in_GOhm=float(d[k] / a))
            if len(cells) == 2:
                r["cc_pct"] = float(100.0 * d[1 - k] / d[k])
            rows.append(r)
            print(r, flush=True)
    return rows


def main(form):
    t0 = time.time()
    if form == "alone":
        c = next((a for a in sys.argv[2:] if "=" not in a and a != "nosyn"), AVA)    # one cell per process (one simulator each)
        b, info = build(form, [c])
        rows = measure(b, [c])
        name = f"rin_alone_{c}"
    else:
        b, info = build(form, [AVA, VA] if form == "pair" else None)
        rows = measure(b, [AVA, VA])
        name = f"rin_{form}"
    name += "".join(f"_{k}-{v}" for k, v in TG.items()) + ("_nosyn" if NOSYN else "")
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / f"{name}.json").write_text(json.dumps(dict(form=form, toggles=TG, **info, rows=rows,
                                                     wall_s=round(time.time() - t0, 1)), indent=1))
    print("saved", name, info, round(time.time() - t0, 1), "s")


def score():
    for p in sorted(OUT.glob("rin_*.json")):
        r = json.loads(p.read_text())
        print(f"{p.stem}: gap on AVAR {r['g_gap_on_AVAR_nS']:.2f} nS ({r['g_AVAR_VA05_nS']:.3f} to VA05)")
        for x in r["rows"]:
            cc = f", CC {x['cc_pct']:.2f} %" if "cc_pct" in x else ""
            print(f"   into {x['inj']} {x['I_pA']:+.0f} pA: rest {x['v_rest']:.1f} mV, R_in {x['R_in_GOhm']:.3f} GOhm "
                  f"(Liu {LIU_GOHM[x['inj']]}){cc}")


if __name__ == "__main__":
    if sys.argv[1] == "score":
        score()
    else:
        main(sys.argv[1])
