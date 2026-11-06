# BRAIN_PORT section 7, R1 and R2. argv: mode (r1off | r1on1 | r2off | r2on)
import sys, json, numpy as np
from wormemu.brain import Brain, sample_worm
mode = sys.argv[1]
spec = sample_worm(None)
if mode == "r1on1":
    spec.values["gap_rect_ratio"] = 1.0
if mode.startswith("r1"):
    cells = ["AVAL", "AVAR", "AVBL", "PVCL", "DA01", "VA01", "VA02", "DB01", "VB01", "VB02", "ALML", "PLML", "dBWML6"]
    b = Brain(spec, toggles=dict(wiring="cook", gap_rectification="off" if mode == "r1off" else "on"), cells=cells)
    b.reset(); V = []
    for k in range(400):
        b.extra_pA[:] = 0.0
        if 100 <= k < 300: b.extra_pA[b.idx["ALML"]] = b.extra_pA[b.idx["DA01"]] = 20.0
        V.append(b.step().v_mV)
    print(json.dumps(dict(V=np.array(V).tolist(), placed=dict(b.placed))))
else:
    cells = ["AVAL", "DA01", "VA01"]
    b = Brain(spec, toggles=dict(wiring="cook", gap_rectification="off" if mode == "r2off" else "on"), cells=cells)
    for pp in b.conn:
        if "gap" not in pp.hname():
            pp.weight = 0.0
    out = dict(placed=dict(b.placed))
    for src in cells:
        b.reset(); V = []
        for k in range(1200):
            b.extra_pA[:] = 0.0
            if 400 <= k < 800: b.extra_pA[b.idx[src]] = 20.0
            V.append(b.step().v_mV)
        V = np.array(V); d = V[750:800].mean(0) - V[350:400].mean(0)
        out[src] = {n: float(d[b.idx[n]] / d[b.idx[src]]) for n in cells if n != src}
        out[src + "_dV"] = float(d[b.idx[src]])
    print(json.dumps(out))
