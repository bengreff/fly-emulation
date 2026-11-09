"""Organ chemical synapses and the receptor forms (wbody2, 8 Nov 2026; an A found in item 2's trace): the pharynx,
enteric and egg-laying modules placed every chemical synapse from a brain neuron as BAAIWorm's graded synapse
(brain._syn), whatever receptor_kinetics says. So the default receptor form (kinetic, per class) never reached them,
and neither did anything that acts on wsyn synapses: neuromod's release gain (the SER-7 route, 5-HT raising MC's
release: Hobson et al. 2006), drugs, learning's release gains.

The fix (organs_nrn.chem_synapse): receptor_kinetics off (or sign_rule allexc) keeps brain._syn exactly; graded mode
places one wsyn mode 0 (the brain's own BAAIWorm-equivalent form); instantaneous and kinetic place one wsyn per
receptor class by the brain's rule for a postsynaptic cell with no CeNGEN profile (pharyngeal muscle and marginal
cells, enteric muscles: the transmitter's default class of the synapse's sign) or for muscle (egg-laying muscles:
receptors.pair_classes post_muscle, as the body-wall NMJ), at the same total conductance per contact times the class's
unit conductance over L-AChR's (the brain's NMJ rule without structure_rules). Each is listed in brain.wsyn with
post index -1 (not a brain cell).

Bar (written before running the fixed code):
    off      receptor_kinetics=off: every recorded organ voltage bit-identical to the reference saved on the
             unfixed code (max |dV| == 0)
    graded   receptor_kinetics=graded: max |dV| <= 1e-9 mV against the unfixed code's graded reference (the
             brain's own BAAIWorm equivalence bar, tests/test_worm_receptors.py)
    classes  default toggles: every organ chemical synapse is a wsyn listed in brain.wsyn with post index -1, and the
             class counts are as the rule says (reported per organ)
    release  default toggles: brain._apply_g_scale({"release": f}) with f = 2 at MCL, 1 elsewhere, sets the relgain
             of every MCL organ wsyn to 2 and of no other organ wsyn (needs the brain to build its synapse gains
             after the mechanisms: a Request to wbrain2; until then this part fails, and is reported)
Setup: a sub-brain of the pharyngeal neurons (pharynx_trace.PN), the defecation neurons (dmp_trace.DMP) and every
neuron with a chemical synapse onto a sex muscle; ledger values; 40 pA x 30 ms pulses at 4 Hz from 0.5 s into MCL,
MCR, M3L, M3R, AVL, DVB and the egg-laying presynaptic neurons; 3 bio s at 1 ms steps; every organ cell's soma V
recorded at every 0.5 ms step. One subprocess per build (fresh NEURON).
Usage: python organ_synapse_check.py ref      save the references (run on the unfixed code)
       python organ_synapse_check.py          the four parts -> runs/worm/wbody2/organ_synapse_check.json
"""
from __future__ import annotations

import json
import subprocess
import sys
import time
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[3]
OUT = ROOT / "runs/worm/wbody2"
SECS, HZ, MS, PA = 3.0, 4.0, 30.0, 40.0
MODULES = (("organs_pharynx", "syn_pharynx"), ("organs_intestine", "syn_enteric"), ("organs_egglaying", "syn_sex"))


def build(rk):
    sys.path.insert(0, str(ROOT / "src"))
    sys.path.insert(0, str(ROOT / "scripts" / "worm"))
    sys.path.insert(0, str(ROOT / "scripts" / "worm" / "wbody2"))
    import at_ledger
    at_ledger.patch()
    from wormemu import brain as B
    from wormemu.interface import SEX_MUSCLES
    from wormemu.brain_structure import load_structure
    from pharynx_trace import PN
    from dmp_trace import DMP
    st = load_structure()
    nm = st.names
    egg = sorted({nm[i] for i, j, n in st.chem if nm[j] in SEX_MUSCLES and nm[i] not in SEX_MUSCLES})
    cells = list(dict.fromkeys(PN + DMP + egg))
    spec = B.sample_worm(None)
    b = B.Brain(spec, toggles={} if rk is None else {"receptor_kinetics": rk}, cells=cells)
    drive = [c for c in ["MCL", "MCR", "M3L", "M3R", "AVL", "DVB"] + egg if c in b.idx]
    return b, egg, drive


def mods(b):
    from wormemu import mech
    out = {}
    for name, kind in MODULES:
        m = sys.modules.get(f"wormemu.mech.{name}")
        out[name] = next((x for x in b.mechs if m is not None and isinstance(x, m.Mech)), None)
    return out


def run(rk):
    b, egg, drive = build(rk)
    h = b.h
    ms = mods(b)
    names, vecs = [], []
    for name, m in ms.items():
        for c, s in sorted((getattr(m, "sec", None) or {}).items()):
            names.append(f"{name}:{c}")
            vecs.append(h.Vector().record(s(0.5)._ref_v))
    inj = [b.idx[c] for c in drive]
    b.reset()
    for k in range(int(SECS * 1000)):
        b.extra_pA[:] = 0.0
        if k >= 500 and (k - 500) % (1000.0 / HZ) < MS:
            b.extra_pA[inj] = PA
        b.step(None, 1.0)
    v = np.array([np.array(x) for x in vecs])
    placed = {k: int(x) for k, x in b.placed.items() if k.startswith(("syn_pharynx", "syn_enteric", "syn_sex"))}
    return b, ms, names, v, placed, egg, drive


def classes_and_release(b, ms):
    """The organ wsyn entries (pp, pre, post, class) and the release part of the bar."""
    from wormemu import mech
    org = set()
    for m in ms.values():
        for pp in getattr(m, "wsyn", None) or ():
            org.add(id(pp))
    rows = [(pp, pre, post, c) for pp, pre, post, c in b.wsyn if id(pp) in org]
    by = {}
    for pp, pre, post, c in rows:
        k = "graded" if c < 0 else mech.RECEPTOR_CLASSES[c]
        by[k] = by.get(k, 0) + 1
    n_org = sum(len(getattr(m, "wsyn", None) or ()) for m in ms.values())
    f = np.ones(len(b.cell_names))
    mcl = b.idx["MCL"]
    f[mcl] = 2.0
    b._apply_g_scale({"release": f})
    rel = [(pre, float(pp.relgain)) for pp, pre, post, c in rows]
    ok_rel = bool(rows) and all((g == 2.0) if pre == mcl else (g == 1.0) for pre, g in rel)
    out = dict(n_organ_wsyn=n_org, n_listed=len(rows), post_minus_1=all(p == -1 for _, _, p, _ in rows),
               by_class=by, release_mcl=[g for pre, g in rel if pre == mcl],
               release_others_max=max([g for pre, g in rel if pre != mcl] or [1.0]), release_pass=ok_rel)
    out.update(request_probe(b, rows, mcl))
    return out


def request_probe(b, rows, mcl):
    """Not part of the bar: the Request to wbrain2, tried here. Rebuild only the synapse half of brain._g_targets
    after the mechanisms (the channel half would re-read base values the mechanisms have already edited), then (1) the
    release part again, and (2) the hazard the post >= 0 guard is for: a rec_<class> gain of 3 at the last brain cell
    only, which an organ synapse (post -1) would pick up through numpy's index -1."""
    from wormemu import mech
    h, w = b.h, b.wsyn
    rel, rec = h.PtrVector(len(w)), h.PtrVector(len(w))
    for k, (pp, _, _, _) in enumerate(w):
        rel.pset(k, pp._ref_relgain)
        rec.pset(k, pp._ref_recgain)
    pre, post, cls = (np.array([x[i] for x in w]) for i in (1, 2, 3))
    b._sg = (pre, post, cls, rel, rec, np.ones(len(w)), np.ones(len(w)))
    f = np.ones(len(b.cell_names))
    f[mcl] = 2.0
    b._apply_g_scale({"release": f})
    ok = all((float(pp.relgain) == 2.0) if p0 == mcl else (float(pp.relgain) == 1.0) for pp, p0, _, _ in rows)
    b._apply_g_scale({})
    used = sorted({mech.RECEPTOR_CLASSES[c] for _, _, _, c in rows if c >= 0})
    g = np.ones(len(b.cell_names))
    g[-1] = 3.0
    b._apply_g_scale({f"rec_{c}": g for c in used})
    hit = sum(float(pp.recgain) == 3.0 for pp, _, _, _ in rows)
    b._apply_g_scale({})
    return dict(release_pass_after_rebuild=ok, organ_wsyn_hit_by_last_cell_rec_gain=int(hit))


def child(mode):
    rk = None if mode == "default" else mode
    b, ms, names, v, placed, egg, drive = run(rk)
    res = dict(mode=mode, names=names, placed=placed, egg_pre=egg, drive=drive,
               n_syn={k: int(getattr(m, "n_syn", 0)) for k, m in ms.items() if m is not None})
    if mode == "default":
        res.update(classes_and_release(b, ms))
    np.save(OUT / f"organ_synapse_{mode}.npy", v)
    print(json.dumps(res))


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    if len(sys.argv) >= 3 and sys.argv[1] == "child":
        child(sys.argv[2])
        return
    ref = len(sys.argv) >= 2 and sys.argv[1] == "ref"
    t0, res = time.time(), {}
    for mode in (("off", "graded") if ref else ("off", "graded", "default")):
        r = subprocess.run([sys.executable, __file__, "child", mode], capture_output=True, text=True)
        if r.returncode:
            print(r.stderr[-3000:])
            raise SystemExit(f"{mode} failed")
        res[mode] = json.loads(r.stdout.strip().splitlines()[-1])
        v = np.load(OUT / f"organ_synapse_{mode}.npy")
        if ref:
            np.save(OUT / f"organ_synapse_ref_{mode}.npy", v)
            (OUT / f"organ_synapse_ref_{mode}.json").write_text(json.dumps(res[mode]))
        elif mode in ("off", "graded"):
            r0 = np.load(OUT / f"organ_synapse_ref_{mode}.npy")
            n0 = json.loads((OUT / f"organ_synapse_ref_{mode}.json").read_text())["names"]
            same = n0 == res[mode]["names"] and r0.shape == v.shape
            res[mode]["max_abs_dv_mV"] = float(np.max(np.abs(v - r0))) if same else None
        res[mode]["v_max_mV"] = float(v.max())
        print(mode, {k: x for k, x in res[mode].items() if k not in ("names",)}, flush=True)
    if ref:
        print(f"references saved, {time.time() - t0:.0f} s")
        return
    d = res["default"]
    verdict = dict(off=res["off"]["max_abs_dv_mV"] == 0.0,
                   graded=res["graded"]["max_abs_dv_mV"] is not None and res["graded"]["max_abs_dv_mV"] <= 1e-9,
                   classes=d["n_organ_wsyn"] > 0 and d["n_listed"] == d["n_organ_wsyn"] and d["post_minus_1"],
                   release=d["release_pass"])
    out = dict(bar=__doc__.split("Bar (written before running the fixed code):")[1].split("Setup:")[0].strip(),
               results={k: {kk: x for kk, x in r.items() if kk != "names"} for k, r in res.items()},
               verdict=verdict, wall_s=time.time() - t0)
    (OUT / "organ_synapse_check.json").write_text(json.dumps(out, indent=1))
    print(verdict, f"{out['wall_s']:.0f} s")


if __name__ == "__main__":
    main()
