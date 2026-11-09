"""egg_laying reads wneuro's HSN near-field 5-HT term at vm2 (inbox 02:45; wbody2, 9 Nov 2026).

Bars, written 9 Nov 03:28 CST before the wiring (reference run on 9413f77, main merged, nothing wired):
1. Neutral: under amine_synaptic=off (the default), 20 s at 1 ms on a brain of HSNL and HSNR with every organ, the 16
   sex muscles' V and activation, egg_5ht_occ and eggs laid are bit-identical to the reference.
2. Wired (scored by tests/test_worm_egg_nearfield.py, exact): under nicholson, vm2's 5-HT read is neuromod's pool plus
   neuromod.near_nM('serotonin', HSN) and vm1's is the pool alone.
3. Reported, no bar (wneuro runs the whole-worm adoption check): under nicholson, the near-field excess at vm2 and vm2's
   SER-1/SER-7 occupancy against the pool's, over the same 20 s.

Usage: python egg_near_check.py TAG [syn=off|nicholson] [secs=20] [ref=TAG] -> runs/worm/wbody2/egg_near_TAG.{json,npz}
"""
from __future__ import annotations

import json
import sys
import time
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[3]
OUT = ROOT / "runs/worm/wbody2"


def main():
    tag = sys.argv[1]
    a = dict(x.split("=", 1) for x in sys.argv[2:])
    syn, secs = a.get("syn", "off"), float(a.get("secs", 20))
    sys.path.insert(0, str(ROOT / "src"))
    from wormemu import brain as B
    tog = {} if syn == "off" else {"amine_synaptic": syn}
    b = B.Brain(B.sample_worm(None), toggles=tog, cells=["HSNL", "HSNR"])
    b.reset()
    keys = ("egg_vm_v_mV", "sex_muscle_activation", "egg_5ht_occ", "eggs_laid")
    extra = ("egg_5ht_occ_vm2", "egg_5ht_near_nM")
    rec = {k: [] for k in keys + extra}
    w0 = time.time()
    for _ in range(int(secs * 1000)):
        b.step(None, 1.0)
        mo = b.mech_out
        for k in keys + extra:
            if k in mo:
                rec[k].append(np.asarray(mo[k], float).copy())
    z = {k: np.array(v) for k, v in rec.items() if v}
    np.savez(OUT / f"egg_near_{tag}.npz", **z)
    res = dict(tag=tag, syn=syn, secs=secs, wall_s=time.time() - w0, eggs=float(z["eggs_laid"].sum()),
               occ_pool_median=float(np.median(z["egg_5ht_occ"])))
    if "egg_5ht_near_nM" in z:
        res.update(near_nM_median=float(np.median(z["egg_5ht_near_nM"])), near_nM_max=float(z["egg_5ht_near_nM"].max()),
                   occ_vm2_median=float(np.median(z["egg_5ht_occ_vm2"])))
    if "ref" in a:
        r = np.load(OUT / f"egg_near_{a['ref']}.npz")
        same = {k: bool(np.array_equal(r[k], z[k])) for k in keys}
        res["bar1_identical_to_" + a["ref"]] = same
        res["bar1"] = "pass" if all(same.values()) else "fail"
    (OUT / f"egg_near_{tag}.json").write_text(json.dumps(res, indent=1, default=lambda x: x.item()))
    print(json.dumps(res, default=lambda x: x.item()))


if __name__ == "__main__":
    main()
