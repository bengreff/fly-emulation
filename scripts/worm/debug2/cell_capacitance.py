"""Never-checked row 2: whole-cell capacitance of AFD, AWA and AWC against Ramot, MacInnis and Goodman 2008 (Nat
Neurosci 11:908, PMC2587641, Methods), on Goodman et al. 1998's protocol (Neuron 20:763, PMC4444786: a 10 ms, 20 mV
pulse from -74 mV). Bars in docs/worm/night/2026-11-08_wbrain2.md ("whole-cell capacitance", written before this
ran; wbrain2, 9 Nov 2026). Default template worm, each cell built alone in its own process. Run from the repo root.

  python scripts/worm/debug2/cell_capacitance.py OUT.json        # all cells and the bars
  python scripts/worm/debug2/cell_capacitance.py one CELL RS_MOHM  # one cell, JSON on stdout's last line
"""
import json
import os
import subprocess
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[3]
RAMOT = {"AFD": (2.2, 0.4, 56, 35.0), "AWA": (2.8, 0.4, 8, 25.0), "AWC": (3.1, 0.4, 5, 29.0)}  # pF mean, SD, n; Rs
GOODMAN_SLOPE = 1.07                     # ASER C_in / C_iso at 1 uF/cm2 (Goodman 1998 Fig 2B, +- 0.08, 95% CI)
HOLD_MV, STEP_MV, T_HOLD, T_STEP, DT = -74.0, 20.0, 200.0, 10.0, 0.005


def pulse(b, soma, rs):
    h = b.h
    cl = h.SEClamp(soma(0.5))
    cl.rs = rs                           # SEClamp.rs is in MOhm
    cl.dur1, cl.amp1 = T_HOLD, HOLD_MV
    cl.dur2, cl.amp2 = T_STEP, HOLD_MV + STEP_MV
    cl.dur3, cl.amp3 = 5.0, HOLD_MV
    ti, tt = h.Vector().record(cl._ref_i), h.Vector().record(h._ref_t)
    h.dt = DT
    h.finitialize(HOLD_MV)
    while h.t < T_HOLD + T_STEP + 1.0:
        h.fadvance()
    i, t = np.array(ti), np.array(tt)
    w = (t >= T_HOLD) & (t < T_HOLD + T_STEP)
    end = (t >= T_HOLD + T_STEP - 1.0) & (t < T_HOLD + T_STEP)
    i_end = float(i[end].mean())
    q = float(np.trapezoid(i[w] - i_end, t[w]))           # nA ms = pC
    w1 = (t >= T_HOLD) & (t < T_HOLD + 1.0)               # post hoc, reported: the first 1 ms only
    q1 = float(np.trapezoid(i[w1] - i[w1][-1], t[w1]))
    cl.rs = 1e9                                       # park the clamp (high resistance) before it is dropped
    return dict(C_in_pF=1000.0 * q / STEP_MV, C_in_1ms_pF=1000.0 * q1 / STEP_MV, i_end_nA=i_end,
                i_hold_nA=float(i[t < T_HOLD][-1]), i_peak_nA=float(i[w].max()))


def one(cell, rs):
    sys.path.insert(0, str(ROOT / "src"))
    from wormemu.brain import Brain
    b = Brain(cells=[cell])
    b.reset()
    h, k = b.h, b.idx[cell]
    soma, secs = b.soma[k], list(b.cells[k].all)
    area = sum(seg.area() for s in secs for seg in s)
    c_iso = sum(seg.area() * s.cm for s in secs for seg in s) * 0.01   # um2 x uF/cm2 -> pF
    cms = sorted({round(float(s.cm), 9) for s in secs})
    r = dict(cell=cell, n_sections=len(secs), area_um2=area, cm_uF_cm2=cms, C_iso_pF=c_iso,
             soma_area_um2=sum(seg.area() for seg in soma), rs_MOhm=rs)
    r["active"] = pulse(b, soma, rs)
    names = set()
    for s in secs:
        mech = {m.name() for seg in s for m in seg if not m.is_ion()} - {"pas"}
        for m in mech:
            s.uninsert(m)
        names |= mech
    r["uninserted"] = sorted(names)
    r["passive"] = pulse(b, soma, rs)
    r["passive_over_iso"] = r["passive"]["C_in_pF"] / c_iso
    print(json.dumps(r))


def sub(cell, rs):
    env = dict(os.environ, PYTHONPATH=str(ROOT / "src"))
    p = subprocess.run([sys.executable, __file__, "one", cell, str(rs)], capture_output=True, text=True, env=env,
                       cwd=ROOT, timeout=1800)
    assert p.returncode == 0, p.stderr[-3000:]
    return json.loads(p.stdout.strip().splitlines()[-1])


if __name__ == "__main__":
    if sys.argv[1] == "one":
        one(sys.argv[2], float(sys.argv[3]))
        sys.exit()
    res = {"cells": {}, "classes": {}}
    for cls, (m, sd, n, rs) in RAMOT.items():
        lo, hi = m - 2 * sd, m + 2 * sd
        for side in "LR":
            r = sub(cls + side, rs)
            r["bar1"] = bool(lo <= r["C_iso_pF"] <= hi)
            r["bar2"] = bool(abs(r["passive_over_iso"] - 1.0) <= 0.10)
            res["cells"][cls + side] = r
            print(cls + side, {x: r[x] for x in ("area_um2", "cm_uF_cm2", "C_iso_pF", "passive_over_iso",
                                                  "bar1", "bar2")}, "active C_in", r["active"]["C_in_pF"],
                  flush=True)
        a = np.mean([res["cells"][cls + s]["area_um2"] for s in "LR"])
        res["classes"][cls] = dict(measured_pF=(m, sd, n), band_pF=(lo, hi), model_mean_area_um2=float(a),
                                   implied_cm_uF_cm2=m / (a * 0.01),
                                   implied_cm_band=((m - 2 * sd) / (a * 0.01), (m + 2 * sd) / (a * 0.01)))
    for c in ("ASEL", "ASER"):                       # reported: Goodman 1998, 0.5-3 pF across the larval stages
        res["cells"][c] = sub(c, 19.0)
        print(c, res["cells"][c]["C_iso_pF"], res["cells"][c]["passive_over_iso"], flush=True)
    res["bar1_passed"] = all(res["cells"][c]["bar1"] for c in res["cells"] if "bar1" in res["cells"][c])
    res["bar2_passed"] = all(res["cells"][c]["bar2"] for c in res["cells"] if "bar2" in res["cells"][c])
    print("classes", res["classes"], "bar1", res["bar1_passed"], "bar2", res["bar2_passed"], flush=True)
    Path(sys.argv[1]).parent.mkdir(parents=True, exist_ok=True)
    Path(sys.argv[1]).write_text(json.dumps(res, indent=1))
