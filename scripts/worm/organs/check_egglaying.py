"""Row 15 unit check: the egg-laying circuit's active/inactive pattern, isolated (bar in the worgans night file).

A brain of only HSNL/R and VC01-06 (BAAIWorm membranes, Cook wiring among them, the code's default toggles) with
wormemu.mech.organs_egglaying registered; egg production fixed (the module's default, no metabolism); the default
observation; dt 5 ms. Runs wild type, then the unc-103 null (egg_unc103=off), and scores Waggoner 1998 / Zhang 2010's
pattern: clusters (eggs < 180 s apart), intracluster and intercluster intervals, and the null's eggs in utero.

Usage: PYTHONPATH=src .venv/bin/python scripts/worm/organs/check_egglaying.py HOURS OUT.json
"""
import json
import sys
import time
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "src"))

from wormemu import mech  # noqa: E402

if "organs_egglaying" not in mech.REGISTRY:
    mech.REGISTRY.append("organs_egglaying")

from wormemu.brain import Brain  # noqa: E402

CELLS = ["HSNL", "HSNR"] + [f"VC0{k}" for k in range(1, 7)]
GAP_S = 180.0
DT = 5.0


def clusters(t, gap=GAP_S):
    """Egg times (s) -> list of clusters (lists of times)."""
    out = []
    for x in t:
        if out and x - out[-1][-1] < gap:
            out[-1].append(x)
        else:
            out.append([x])
    return out


def run(hours, toggles, label):
    b = Brain(cells=CELLS, toggles=toggles)
    b.reset()
    m = next(x for x in b.mechs if type(x).__module__.endswith("organs_egglaying"))
    hsn = [b.idx["HSNL"], b.idx["HSNR"]]
    n = int(round(hours * 3.6e6 / DT))
    rec = int(round(10000.0 / DT))
    eggs, U, occ, tyr, act = [], [], [], [], []
    hsn_hi = 0
    w0 = time.time()
    for k in range(n):
        o = b.step(None, DT)
        if o.eggs_laid:
            eggs.append(b.t / 1000.0)
        hsn_hi += int(np.mean(o.v_mV[hsn]) > -30.0)
        mo = b.mech_out
        occ.append(mo["egg_5ht_occ"])
        tyr.append(mo["uv1_tyramine_uM"])
        act.append(mo["egg_vm_act"])
        if k % rec == 0:
            U.append((b.t / 1000.0, m.U))
        if k % (rec * 60) == 0:
            print(f"  {label} t {b.t / 60000:.1f} min  eggs {len(eggs)}  U {m.U:.2f}  wall {time.time() - w0:.0f} s",
                  flush=True)
    U = np.array(U)
    last = U[U[:, 0] >= U[-1, 0] - 3600.0, 1]
    cl = clusters(eggs)
    intra = [b_ - a for c in cl for a, b_ in zip(c[:-1], c[1:])]
    inter = [c2[0] - c1[-1] for c1, c2 in zip(cl[:-1], cl[1:])]
    return {"eggs": len(eggs), "egg_times_s": eggs, "clusters": [len(c) for c in cl],
            "n_clusters_ge2": sum(len(c) >= 2 for c in cl), "intra_mean_s": float(np.mean(intra)) if intra else None,
            "inter_mean_min": float(np.mean(inter)) / 60.0 if inter else None,
            "eggs_per_cluster": float(np.mean([len(c) for c in cl])) if cl else None,
            "uterus_last_h_mean": float(np.mean(last)), "uterus_end": float(U[-1, 1]),
            "hsn_frac_above_m30": hsn_hi / n, "occ5_max": float(np.max(occ)), "tyr_max_uM": float(np.max(tyr)),
            "vm_act_max": float(np.max(act)), "vm_act_mean": float(np.mean(act)), "wall_s": time.time() - w0,
            "n_syn": m.n_syn, "n_gap": m.n_gap}


def main():
    hours, out = float(sys.argv[1]), Path(sys.argv[2])
    res = {"hours": hours, "dt_ms": DT}
    res["wt"] = run(hours, {}, "wt")
    out.write_text(json.dumps(res, indent=1))
    res["unc103_null"] = run(hours, {"egg_unc103": "off"}, "null")
    w, z = res["wt"], res["unc103_null"]
    s = {"clusters": w["n_clusters_ge2"] >= 3,
         "intra": w["intra_mean_s"] is not None and 5.0 <= w["intra_mean_s"] <= 60.0,
         "inter": w["inter_mean_min"] is not None and 10.0 <= w["inter_mean_min"] <= 60.0,
         "falsifier": z["uterus_last_h_mean"] <= 0.7 * w["uterus_last_h_mean"]}
    s["pass"] = all(s.values())
    res["score"] = s
    out.write_text(json.dumps(res, indent=1))
    print(json.dumps({k: (v if not isinstance(v, dict) else {a: b for a, b in v.items() if a != "egg_times_s"})
                      for k, v in res.items()}, indent=1))


if __name__ == "__main__":
    main()
