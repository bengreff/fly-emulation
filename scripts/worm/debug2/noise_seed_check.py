"""Check for the brain's noise seed (wbrain2, 9 Nov 2026; weki's FIT_GENERAL section 7). One configuration per
process (NEURON is one simulator per process): a 10-cell sub-brain on the default toggles (quantal and channel noise
on, GCaMP6s and NeuroPAL on) runs 600 steps with 20 pA into AWAL for steps 50-200; the soma voltages, the GCaMP
readout and the NeuroPAL ids are saved to runs/worm/wbrain2/noise_seed/<tag>.npz.
Usage: python noise_seed_check.py run <tag> <worm seed|none> [<noise seed|none>]
       python noise_seed_check.py score     (the night file's four bars, from the saved runs)
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[3]
OUT = ROOT / "runs/worm/wbrain2/noise_seed"
CELLS = ["AWAL", "AIYL", "AIZL", "AIBL", "RIAL", "AVAL", "AVBL", "RIML", "AFDL", "ASEL"]


def _int(x):
    return None if x == "none" else int(x)


def run(tag, ws, ns=None, given=False):
    sys.path.insert(0, str(ROOT / "src"))
    from wormemu import brain as B
    spec = B.sample_worm(ws)
    b = B.Brain(spec, cells=CELLS, noise_seed=ns) if given else B.Brain(spec, cells=CELLS)
    b.reset()
    vs, gs = [], []
    for k in range(600):
        b.extra_pA[b.idx["AWAL"]] = 20.0 if 50 <= k < 200 else 0.0
        vs.append(np.array(b.step().v_mV, float))
        gs.append(np.array(b.mech_out["gcamp_dff"], float))
    ids = np.array(b.mech_out.get("neuropal_id", []), int)
    vals = np.array([float(np.sum(np.asarray(v, float))) for _, v in sorted(spec.values.items())
                     if np.asarray(v).dtype.kind in "fi"])
    OUT.mkdir(parents=True, exist_ok=True)
    np.savez(OUT / f"{tag}.npz", v=np.array(vs), g=np.array(gs), ids=ids, vals=vals)
    print(tag, "worm seed", ws, "noise seed", ns if given else "(not passed)", "saved")


def score():
    L = {p.stem: np.load(p) for p in OUT.glob("*.npz")}

    def same(a, b):
        return all(np.array_equal(L[a][k], L[b][k]) for k in ("v", "g", "ids", "vals"))

    def dv(a, b):
        return float(np.max(np.abs(L[a]["v"] - L[b]["v"])))

    print("1. None = old code, worm None:", same("new_none_none", "ref_none"), " worm 3:", same("new_3_none", "ref_3"))
    print("2. noise 3 = None, worm 3:", same("new_3_3", "new_3_none"))
    d = dv("new_3_7", "new_3_none")
    print("3. noise 7 vs None, worm 3: max |dV|", round(d, 3), "mV; values equal",
          np.array_equal(L["new_3_7"]["vals"], L["new_3_none"]["vals"]), "; ids equal",
          np.array_equal(L["new_3_7"]["ids"], L["new_3_none"]["ids"]),
          "; GCaMP max |d|", round(float(np.max(np.abs(L["new_3_7"]["g"] - L["new_3_none"]["g"]))), 4))


if __name__ == "__main__":
    a = sys.argv[1:]
    if a[0] == "run":
        run(a[1], _int(a[2]), _int(a[3]) if len(a) > 3 else None, given=len(a) > 3)
    else:
        score()
