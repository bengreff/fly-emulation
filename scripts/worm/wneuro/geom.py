"""wneuro item 1 (c): where is each cell's membrane along the body, relative to neuromod's compartments?
Diagnostic only. Prints soma y (the atlas neuromod uses) and the y range and membrane area of each cell's segments
(BAAIWorm 3D points) per compartment. Usage: python geom.py [CELL ...]"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "src"))
from wormemu import brain as B  # noqa: E402
from wormemu.mech import neuromod as nmod  # noqa: E402

cells = sys.argv[1:] or ["AVL", "DVB"]
b = B.Brain(B.sample_worm(None), cells=cells)
nm = next(m for m in b.mechs if isinstance(m, nmod.Mech))
print("edges (soma-y um):", nm.edges)
for c in cells:
    j = b.idx[c]
    ys = np.array([xyz[1] for _, xyz in b.segs[j]])
    area = np.array([seg.area() for seg, _ in b.segs[j]])
    sec = b.soma[j]
    soma_xyz = (sec.x3d(0), sec.y3d(0), sec.z3d(0))
    comp = np.clip(np.searchsorted(nm.edges, ys, side="right") - 1, 0, 3)
    share = np.bincount(comp, area, minlength=4) / area.sum()
    print(c, "atlas soma y", nm.y[j], "hoc soma xyz", np.round(soma_xyz, 1), "segs", len(ys),
          "seg y min/max", round(ys.min(), 1), round(ys.max(), 1), "area um2", round(area.sum(), 1),
          "area share by compartment", np.round(share, 3), "soma comp", nm.pep_comp[j])
# presynaptic sites (BAAIWorm's placement, port302a connections.csv: chemical synapses where the cell is pre) per
# compartment, counted by site and by weight; partners outside this brain are counted too (their pre segment is ours)
rows = b._read_port302a()
for c in cells:
    j = b.idx[c]
    ys = np.array([xyz[1] for _, xyz in b.segs[j]])
    pre = [(i, w) for a, i, _, _, cat, w in rows if a == c and cat == "syn"]
    if not pre:
        print(c, "no placed presynaptic sites")
        continue
    k = np.clip(np.searchsorted(nm.edges, ys[[i for i, _ in pre]], side="right") - 1, 0, 3)
    print(c, "presynaptic sites", len(pre), "share by compartment (sites)", np.round(np.bincount(k, minlength=4) /
          len(pre), 3), "(weight)", np.round(np.bincount(k, [w for _, w in pre], minlength=4) /
                                            sum(w for _, w in pre), 3))
