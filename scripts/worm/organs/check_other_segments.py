"""Line 20 neutral check (wbody2 item 6, 8 Nov 2026): organs_other now segments its passive cells by NEURON's d_lambda
rule (hyp 35, exc_cell 5; was 1). Is that neutral at DC for the rest of the worm?

Bar (written before running). The template worm's values (at_ledger), a sub-brain of every cell with a Cook gap to
hyp, hmc, exc_cell or exc_gl, zero input, 3 s at the brain's step, built twice: nseg by the rule and nseg 1 (the old
build, by replacing organs_nrn.d_lambda_nseg). Neutral if every partner's mean V over the last 1 s differs by at most
0.5 mV, every cell's 0 mV up-crossing count by at most 1, and each organ cell's midpoint V by at most 0.5 mV.
Reported, not barred: each organ cell's DC input resistance at its midpoint, standalone, nseg 1 vs the rule (derived
beforehand for hyp: a sealed cable of half-length 0.96 lambda_DC gives tanh(0.96) / 0.96 = 0.77 of the isopotential
input conductance, so about 1.29x the resistance; exc_cell 1.005x).

Usage: python check_other_segments.py   -> runs/worm/organs/check_other_segments.json
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "scripts" / "worm"))
SECS = 3.0


def standalone(seg_rule):
    from neuron import h
    from wormemu.mech import organs_nrn, organs_other as oo
    q = oo.defaults()
    out = {}
    for n in oo.OTHER_CELLS:
        sec = h.Section(name=f"t_{n}")
        sec.nseg, sec.diam = 1, 10.0
        sec.L = q[f"other_area_{n}_um2"] / (np.pi * sec.diam)
        sec.cm = 1.0
        sec.nseg = organs_nrn.d_lambda_nseg(sec) if seg_rule else 1
        sec.insert("pas")
        sec.g_pas = 1.0 / (q["other_rm_kohm_cm2"] * 1000.0)
        sec.e_pas = 0.0
        imp = h.Impedance()
        imp.loc(0.5, sec=sec)
        imp.compute(0.0)
        out[n] = dict(nseg=int(sec.nseg), L_um=float(sec.L), rin_MOhm=float(imp.input(0.5, sec=sec)))
        del imp, sec
    return out


def run(seg_rule):
    import at_ledger
    at_ledger.patch()
    from wormemu import brain as B
    from wormemu.brain_structure import load_structure
    from wormemu.mech import organs_nrn, organs_other as oo
    if not seg_rule:
        organs_nrn.d_lambda_nseg = lambda sec, f_hz=100.0, frac=0.1: 1
    st = load_structure()
    nm, mine = st.names, set(oo.OTHER_CELLS)
    partners = sorted({nm[j] if nm[i] in mine else nm[i] for i, j, _ in st.gap
                       if (nm[i] in mine) != (nm[j] in mine)})
    b = B.Brain(B.sample_worm(None), cells=partners)
    have = [n for n in partners if n in b.idx]
    other = next(m for m in b.mechs if m.__class__.__module__.endswith("organs_other"))
    b.reset()
    idx = [b.idx[n] for n in have]
    vs, ov = [], []
    for k in range(int(SECS * 1000)):
        o = b.step(None, 1.0)
        vs.append(np.asarray(o.v_mV)[idx])
        ov.append([float(s(0.5).v) for s in other.sec.values()])
    vs, ov = np.array(vs), np.array(ov)
    up = ((vs[:-1] < 0) & (vs[1:] >= 0)).sum(0)
    return dict(partners=have, missing=sorted(set(partners) - set(have)), n_gap=other.n_gap,
                nseg={n: int(s.nseg) for n, s in other.sec.items()}, vmean_last1s=vs[-1000:].mean(0).tolist(),
                upcross=up.tolist(), organ_v_last1s=dict(zip(other.sec, ov[-1000:].mean(0).tolist())),
                standalone=standalone(seg_rule))


def main():
    import subprocess
    if len(sys.argv) > 1:
        print(json.dumps(run(sys.argv[1] == "rule")))
        return
    r = {}
    for mode in ("rule", "one"):
        p = subprocess.run([sys.executable, __file__, mode], capture_output=True, text=True)
        if p.returncode:
            raise SystemExit(p.stderr[-2000:])
        r[mode] = json.loads(p.stdout.strip().splitlines()[-1])
    a, c = r["rule"], r["one"]
    dv = np.abs(np.array(a["vmean_last1s"]) - np.array(c["vmean_last1s"]))
    dup = np.abs(np.array(a["upcross"]) - np.array(c["upcross"]))
    dorg = {n: abs(a["organ_v_last1s"][n] - c["organ_v_last1s"][n]) for n in a["organ_v_last1s"]}
    worst = int(np.argmax(dv)) if len(dv) else None
    res = dict(bar=__doc__.split("Bar (written before running). ")[1].split("\n\nUsage")[0],
               n_partners=len(a["partners"]), missing=a["missing"], n_gap=a["n_gap"], nseg_rule=a["nseg"],
               nseg_one=c["nseg"], max_dv_partner_mV=float(dv.max()) if len(dv) else 0.0,
               worst_partner=a["partners"][worst] if worst is not None else None,
               max_dupcross=int(dup.max()) if len(dup) else 0, organ_dv_mV=dorg,
               organ_v_rule=a["organ_v_last1s"], organ_v_one=c["organ_v_last1s"],
               rin_MOhm=dict(rule={n: v["rin_MOhm"] for n, v in a["standalone"].items()},
                             one={n: v["rin_MOhm"] for n, v in c["standalone"].items()}),
               rin_ratio={n: a["standalone"][n]["rin_MOhm"] / c["standalone"][n]["rin_MOhm"] for n in a["standalone"]},
               upcross_rule=dict(zip(a["partners"], a["upcross"])))
    res["bar_pass"] = bool(res["max_dv_partner_mV"] <= 0.5 and res["max_dupcross"] <= 1
                           and all(v <= 0.5 for v in dorg.values()))
    out = ROOT / "runs/worm/organs/check_other_segments.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(res, indent=1))
    print(json.dumps({k: v for k, v in res.items() if k not in ("bar", "upcross_rule")}, indent=1))


if __name__ == "__main__":
    main()
