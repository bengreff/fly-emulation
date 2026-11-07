"""Row 1 check (bars in docs/worm/night/2026-11-06_wneuron.md, written before running): mech/cells_passive.
(a) the brain builds 56 glia whose names equal WormAtlas's; (b) AMshL's passive step response (I / g and C / g);
(c) the end-organ cells carry exactly Cook's gaps to built cells; (d) endorgan_cells on against off in I2L, I5, M4.

Usage: PYTHONPATH=src .venv/bin/python scripts/worm/cells_passive_check.py SUPPORT_TEXT GLR_TEXT [out.json]
The two WormAtlas pages as text (curl with the tags stripped): wormatlas.org/hermaphrodite/neuronalsupport/
mainframe.htm (names the 50 sensillar glia; the GLRs only as a class) and wormatlas.org/hermaphrodite/muscleGLR/
mainframe.htm (the six GLR names, partly as "GLRDL/R" shorthand, expanded here). One NEURON per subprocess.
"""
from __future__ import annotations

import json
import os
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
NAME = re.compile(r"\b(AMs[ho][LR]|PHsh[LR]|PHso[12][LR]|ILs[ho](?:DL|DR|VL|VR|L|R)|OLQs[ho](?:DL|DR|VL|VR)|"
                  r"OLLs[ho][LR]|CEPs[ho](?:DL|DR|VL|VR)|ADEs[ho][LR]|PDEs[ho][LR]|GLR(?:DL|DR|VL|VR|L|R))\b")
WATCH = ["I2L", "I5", "M4"]
CHILD = """
import json, sys
import numpy as np
from wormemu.brain import Brain, sample_worm
mode = sys.argv[1]
if mode == "clamp":                       # (b): AMshL alone, stepped at a fine dt
    b = Brain(sample_worm(None), cells=["AIYL"])
    m = next(m for m in b.mechs if type(m).__module__ == "wormemu.mech.cells_passive")
    h, sec = b.h, m.sec["AMshL"]
    b.reset()
    out = {}
    for dt in (0.025, 0.5):
        h.dt = dt
        b.reset()
        h.dt = dt
        st = h.IClamp(sec(0.5))
        st.delay, st.dur, st.amp = h.t + 50.0, 200.0, 0.010          # nA
        t, v = [], []
        while h.t < st.delay + 250.0:
            h.fadvance()
            t.append(h.t); v.append(sec(0.5).v)
        out[str(dt)] = dict(t=t, v=v, delay=st.delay)
        st.amp = 0.0
    area = sec(0.5).area()
    out.update(C_pF=sec.cm * area * 0.01, g_nS=sec(0.5).g_pas * area * 10.0, e_leak=sec(0.5).e_pas)
    print(json.dumps(out))
    sys.exit()
tog = {"endorgan_cells": "off"} if mode == "endo_off" else {}
b = Brain(sample_worm(None), toggles=tog)
gm = next(m for m in b.mechs if type(m).__module__ == "wormemu.mech.glia")
cp = next(m for m in b.mechs if type(m).__module__ == "wormemu.mech.cells_passive")
b.reset()
V = []
for k in range(1000):
    o = b.step()
    V.append([float(o.v_mV[b.idx[c]]) for c in %s])
print(json.dumps(dict(glia=sorted(gm.sec) + sorted(n for n in cp.sec if n not in ("e2D", "e2VL", "e2VR", "e3D",
                      "e3VL", "e3VR", "g1AL", "g1AR")), gaps=cp.gaps, V=V)))
""" % json.dumps(WATCH)


def run(mode):
    r = subprocess.run([sys.executable, "-c", CHILD, mode], capture_output=True, text=True, cwd=ROOT,
                       env={**os.environ, "PYTHONPATH": str(ROOT / "src")}, timeout=1800)
    assert r.returncode == 0, r.stderr[-3000:]
    return json.loads(r.stdout.strip().splitlines()[-1])


def step_fit(x, I_pA):
    """Steady change and the 63% time of a step response."""
    import numpy as np
    t, v = np.array(x["t"]), np.array(x["v"])
    v0 = v[t < x["delay"]][-1]
    on = (t >= x["delay"]) & (t <= x["delay"] + 200.0)
    dv = v[on][-1] - v0
    tt, vv = t[on] - x["delay"], v[on] - v0
    k = int(np.argmax(vv >= (1 - np.exp(-1)) * dv))
    t63 = tt[k - 1] + (tt[k] - tt[k - 1]) * ((1 - np.exp(-1)) * dv - vv[k - 1]) / (vv[k] - vv[k - 1])
    return dict(dv_mV=float(dv), t63_ms=float(t63))


def main():
    import numpy as np
    sys.path.insert(0, str(ROOT / "src"))
    from wormemu.brain_structure import load_structure
    from wormemu.mech import cells_passive as C
    res = {}
    text = " ".join(Path(f).read_text() for f in sys.argv[1:3])
    text = re.sub(r"\b([A-Za-z0-9]+?)(D|V)?L/R\b", lambda m: f"{m[1]}{m[2] or ''}L {m[1]}{m[2] or ''}R", text)
    atlas = sorted(set(NAME.findall(text)))
    on, off, cl = run("on"), run("endo_off"), run("clamp")
    res["a"] = dict(wormatlas=atlas, n_wormatlas=len(atlas), built=sorted(on["glia"]), n_built=len(on["glia"]))
    res["a_passed"] = bool(len(atlas) == 56 and sorted(on["glia"]) == atlas)
    want = dict(dv_mV=10.0 / cl["g_nS"], t63_ms=cl["C_pF"] / cl["g_nS"])
    res["b"] = {dt: {**step_fit(cl[dt], 10.0), "want": want} for dt in ("0.025", "0.5")}
    for r in res["b"].values():
        r["rel_err"] = {k: r[k] / want[k] - 1 for k in want}
    res["b"].update(C_pF=cl["C_pF"], g_nS=cl["g_nS"])
    res["b_passed"] = bool(all(abs(e) < 0.01 for e in res["b"]["0.025"]["rel_err"].values()))
    st = load_structure()
    mine = set(C.EPITHELIUM + C.GLANDS)
    cook = sorted((st.names[i], st.names[j], int(n)) for i, j, n in st.gap if {st.names[i], st.names[j]} & mine)
    got = sorted(tuple(g) for g in on["gaps"])
    res["c"] = dict(cook=cook, built=got, n_cook=len(cook), n_built=len(got))
    res["c_passed"] = bool(cook == got)
    dv = np.abs(np.array(on["V"]) - np.array(off["V"])).max(0)
    res["d"] = {c: float(x) for c, x in zip(WATCH, dv)}
    print(json.dumps({k: res[k] for k in ("a_passed", "b_passed", "c_passed", "d")}, indent=1))
    print(json.dumps({k: (res["b"][k]["dv_mV"], res["b"][k]["t63_ms"], res["b"][k]["rel_err"])
                      for k in ("0.025", "0.5")}))
    print(res["a"]["n_wormatlas"], res["a"]["n_built"], res["c"]["n_cook"], res["c"]["n_built"])
    out = Path(sys.argv[3]) if len(sys.argv) > 3 else ROOT / "runs/worm/night_wneuron/cells_passive_check.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(res, indent=1))


if __name__ == "__main__":
    main()
