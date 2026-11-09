"""Neutral check for building the brain's synapse gain table after the mechanisms (wbrain2, 9 Nov 2026; wbody2's
Request 23:52). A sub-brain with chemical synapses runs 300 steps with release and rec_<class> multipliers changing
every step; the soma voltages are saved (`ref`) or compared with the saved run (default). Bar: max |dV| == 0.
Usage: python syn_gains_neutral.py ref | check | nog     (nog: the same run with no multipliers, to show they act)
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[3]
OUT = ROOT / "runs/worm/wbrain2/syn_gains_neutral.npy"
CELLS = ["AWAL", "AIYL", "AIZL", "AIBL", "RIAL", "AVAL", "AVBL", "RIML", "AFDL", "ASEL"]


def main(mode):
    sys.path.insert(0, str(ROOT / "src"))
    from wormemu import brain as B, mech
    b = B.Brain(cells=CELLS)
    b.reset()
    n = len(b.cell_names)
    rng = np.random.default_rng(0)
    pre, post, cls = b._sg[:3]
    used = sorted({mech.RECEPTOR_CLASSES[i] for i in cls if i >= 0})

    class Gains:                                 # mech-shaped: the brain multiplies its g_scale in before fadvance
        g = {}

        def reset(self):
            pass

        def step(self, ctx, dt_ms):
            return {"g_scale": self.g}

    gm = Gains()
    b.mechs.append(gm)
    vs = []
    for k in range(300):
        g = {"release": 1 + rng.random(n)}
        for c in used:
            g[f"rec_{c}"] = 0.5 + rng.random(n)
        gm.g = {} if mode == "nog" else g
        b.extra_pA[b.idx["AWAL"]] = 20.0 if 50 <= k < 200 else 0.0
        vs.append(np.array(b.step().v_mV, float))
    v = np.array(vs)
    print("wsyn", len(b.wsyn), "sg", len(pre), "classes", sorted(set(int(i) for i in cls)))
    if mode == "ref":
        OUT.parent.mkdir(parents=True, exist_ok=True)
        np.save(OUT, v)
        print("saved", v.shape)
    else:
        r = np.load(OUT)
        d = float(np.max(np.abs(v - r)))
        print("max |dV|", d, ("PASS" if d == 0.0 else "FAIL") if mode == "check" else "(nog: the multipliers' effect)")


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "check")
