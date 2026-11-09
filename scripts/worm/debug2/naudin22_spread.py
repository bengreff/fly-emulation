"""AFDL's untraced 1.9 mV, the morphology candidate (docs/worm/night/2026-11-08_wbrain2.md, "AFDL's untraced 1.9 mV",
added before this ran; wbrain2, 9 Nov 2026). Embedded AFDL alone, afd_membrane naudin22, sens_thermo off,
n22_C_pF 4.008 (the published nS whole), -15 pA into the soma from 2 s to 7 s (1 ms steps): every segment's v at
7 s, the area-weighted mean and the spread, against the one-compartment CPU reference's -89.97 mV.

  python scripts/worm/debug2/naudin22_spread.py OUT.json
"""
import json
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import single_cell_sanity as S  # noqa: E402

orig = S.B.sample_worm


def worm(seed):
    w = orig(seed)
    w.values["n22_C_pF"] = 4.008
    return w


S.B.sample_worm = worm
br = S.build(cells=["AFDL"], extra={"afd_membrane": "naudin22", "sens_thermo": "off"})
br.reset()
br.extra_pA[:] = 0.0
for k in range(7000):
    if k == 2000:
        br.extra_pA[:] = -15.0
    vs = float(br.step(None, 1.0).v_mV[0])
cell = br.cells[0]
v, a, names = [], [], []
for sec in cell.all:
    for seg in sec:
        v.append(float(seg.v))
        a.append(float(seg.area()))
        names.append(sec.name())
v, a = np.array(v), np.array(a)
res = dict(soma_v_mV=vs, area_mean_v_mV=float((v * a).sum() / a.sum()), v_min=float(v.min()), v_max=float(v.max()),
           n_seg=len(v), area_um2=float(a.sum()), cpu_ref_mV=-89.97)
res["area_mean_minus_cpu_mV"] = res["area_mean_v_mV"] - res["cpu_ref_mV"]
res["traced"] = abs(res["area_mean_minus_cpu_mV"]) <= 0.5
far = int(np.argmax(v))
res["most_depolarised"] = dict(section=names[far], v_mV=float(v[far]))
print(res)
Path(sys.argv[1]).write_text(json.dumps(res, indent=1))
