"""Bar 1 of "Jiang 2022's AVL model as a B toggle" (docs/worm/night/2026-11-08_wbrain2.md; wbrain2, 9 Nov 2026), and
what the toggles change at build.

Neutral: wbody2's DMP sub-brain (probe_dvb.DMP) at the defaults, built with and without mech/cell_models in the
registry; 1 s settle, then 1 s of 10 pA into AVL and DVB; max |dV| over every cell and step (bar: 0).
On: avl_membrane jiang22, dvb_membrane jiang22_noexp2: AVL's and DVB's conductance-target bases (every dens_* and the
leak) and the pas g of every section (bar: all 0), and j22avl in every section of both.

  python scripts/worm/debug2/jiang22_neutral.py [--out file.json]
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
from probe_dvb import DMP  # noqa: E402

ON = {"avl_membrane": "jiang22", "dvb_membrane": "jiang22_noexp2"}


def trace(toggles=None, without=False):
    from wormemu import brain as B
    from wormemu import mech
    reg = list(mech.REGISTRY)
    if without:
        mech.REGISTRY[:] = [m for m in reg if m != "cell_models"]
    try:
        b = B.Brain(cells=DMP, toggles=toggles or {})
    finally:
        mech.REGISTRY[:] = reg
    b.reset()
    out = []
    for k in range(2000):
        for c in ("AVL", "DVB"):
            b.extra_pA[b.idx[c]] = 10.0 if k >= 1000 else 0.0
        out.append(np.array(b.step().v_mV))
    return b, np.array(out)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default="")
    a = ap.parse_args()
    _, v0 = trace(without=True)
    _, v1 = trace()
    dv = float(np.abs(v1 - v0).max())
    b, v2 = trace(ON)
    h = b.h
    built = {}
    for c in ("AVL", "DVB"):
        i = b.idx[c]
        bases = {nm: float(base[list(cells).index(i)]) for nm, (cells, pv, base, cur) in b._gt.items() if i in cells}
        secs = list(b.cells[i].all)
        built[c] = dict(nonzero_bases={k: x for k, x in bases.items() if x != 0.0}, n_bases=len(bases),
                        pas_g_max=max(seg.pas.g for s in secs for seg in s if hasattr(seg, "pas")),
                        j22_in_every_section=all(h.ismembrane("j22avl", sec=s) for s in secs), n_sections=len(secs),
                        v_last_mV=float(v2[-1, i]), v_max_step_mV=float(v2[1000:, i].max()))
    on_ok = all(not d["nonzero_bases"] and d["pas_g_max"] == 0.0 and d["j22_in_every_section"] for d in built.values())
    res = dict(neutral_max_abs_dV=dv, neutral_pass=dv == 0.0, on=built, on_pass=on_ok)
    print(json.dumps(res, indent=1))
    if a.out:
        Path(a.out).parent.mkdir(parents=True, exist_ok=True)
        Path(a.out).write_text(json.dumps(res, indent=1))


if __name__ == "__main__":
    main()
