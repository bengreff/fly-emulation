"""Fit 1, cost probe: the 302-neuron brain (no muscles: no neuron-muscle gap or chemical pair exists, so neuronal
responses are exact), which receptor classes its neuron-neuron sites carry (sites and summed gmax per class), and how
fast it runs (bio s per wall s) at several mechanism step sizes. One process, threads capped by the caller.

    python probe.py [seconds_per_dt]
"""
import json
import sys
import time
from collections import Counter, defaultdict

import numpy as np

from wormemu import mech
from wormemu.brain import Brain, load_structure, sample_worm

if "observation" not in mech.REGISTRY:
    mech.REGISTRY.append("observation")


def main(bio_s=2.0):
    st = load_structure()
    neurons = [n for n, k in zip(st.names, st.kind) if k == "neuron"]
    t0 = time.time()
    b = Brain(sample_worm(None), toggles={"neuropal": "off"}, cells=neurons)
    build = time.time() - t0
    n_site, g_site = Counter(), defaultdict(float)
    for pp, i, j, c in b.wsyn:
        name = "graded" if c < 0 else mech.RECEPTOR_CLASSES[c]
        n_site[name] += 1
        g_site[name] += pp.gmax * 1000.0                   # uS -> nS
    out = dict(cells=len(b.cell_names), build_s=round(build, 1), registry=list(mech.REGISTRY),
               mechs=[type(m).__module__ for m in b.mechs], placed=dict(b.placed),
               classes={k: dict(sites=n_site[k], g_nS=round(g_site[k], 2)) for k in sorted(n_site)})
    print(json.dumps(out, indent=1), flush=True)
    b.reset()
    speed = {}
    for dt in (0.5, 1.0, 5.0, 10.0):
        b.reset()
        n = int(round(bio_s * 1000 / dt))
        t0 = time.time()
        for _ in range(n):
            o = b.step(dt_ms=dt)
        w = time.time() - t0
        speed[dt] = dict(wall_s=round(w, 2), bio_per_wall=round(bio_s / w, 3),
                         v_mean=round(float(np.mean(o.v_mV)), 2))
        print("dt", dt, speed[dt], flush=True)
    out["speed"] = speed
    json.dump(out, open("probe.json", "w"), indent=1)


if __name__ == "__main__":
    main(*(float(x) for x in sys.argv[1:2]))
