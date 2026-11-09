"""wneuro item 4, line 14 diagnostic (8 Nov 2026 23:20 CST): which receptors carry RIS's Gi in neuromod_unit_check's
check 4 (RIS held at 0 mV, every other neuron at -80 mV, 600 s, template values), with and without the DMSR-1
autoreceptor, and with RIS's FLP-11 release removed. Per RIS entry at the end: ligand, receptor, Gi weight x
occupancy. Diagnostic only; the bar is written in neuromod_unit_check.py before it is scored.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "scripts" / "worm"))
import neuromod_unit_check as U  # noqa: E402
from wormemu.mech import neuromod as N  # noqa: E402

ris = U.NEURONS.index("RIS")
f11 = N.PRECURSORS.index("flp-11")
v = np.full(len(U.NEURONS), -80.0)
v[ris] = 0.0
out = {}
for name, add, no_f11 in (("with", None, False), ("without", {}, False), ("with_no_flp11", None, True),
                          ("without_no_flp11", {}, True)):
    m = U.make(expr_add=add)
    if no_f11:
        m.pep_share[:, f11] = 0.0
    for k in range(6000):
        m.step(U.ctx(v, k * 100.0), 100.0)
    c = m.pep.nM()
    rows = []
    for e in np.flatnonzero(m.e_cell == ris):
        cp = m.pep_W[ris] @ c[m.e_lig[e]] if m.e_pep[e] else 0.0
        occ = float(N._hill(np.array([cp]), np.array([m.e_ec50[e]]), m.p["gpcr_hill"])[0]) if m.e_pep[e] else 0.0
        rows.append(dict(lig=N.PRECURSORS[m.e_lig[e]] if m.e_pep[e] else str(m.e_lig[e]), nM=float(cp), occ=occ,
                         w_i=float(m.e_w[e][1]), gi_part=float(m.e_w[e][1] * occ)))
    rows.sort(key=lambda r: -r["gi_part"])
    out[name] = dict(ris_gi=float(m.G[ris, 1]), top=rows[:6])
    print(name, round(out[name]["ris_gi"], 4), [(r["lig"], round(r["nM"], 3), round(r["gi_part"], 4)) for r in rows[:5]])
(ROOT / "runs/worm/wneuro/ris_gi.json").write_text(json.dumps(out, indent=1))
