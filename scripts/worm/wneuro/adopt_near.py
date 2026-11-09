"""wneuro item 1 (Director 02:46), whole-worm adoption check for amine_synaptic=nicholson as the default (written Mon 9
Nov 2026 03:02 CST, before wbody2's read existed and before any run; the bar does not depend on the run).

Question: once organs_egglaying reads the vulval 5-HT as the pool plus neuromod's near field (HSN onto vm2, the read
wbody2 wires under the toggle), does making the near field the default leave the entire worm physical and every
passing vital sign passing? And what vulval SER-7 occupancy does it give?

Method. weki's battery unchanged (wormemu.fit.vitals.run: the entire worm, body on, the plate at its defaults, 150
bio s, body exchange 4.167 ms, GCaMP7f readout), food and nofood, on one code tree (the commit that has wbody2's read,
with main merged), twice: amine_synaptic=off (the reference) and amine_synaptic=nicholson. If wbody2 or weki has run
the battery on that exact tree under the default (off), that run is the reference and only nicholson is run here
(the off read is 0 by construction, so a second off run would repeat it). Instrumentation only: this script wraps
organs_egglaying.Mech.concentrations to record its 5-HT return value at every call, with the pool part (neuromod's
bin at HSNL, as the module read before the wiring) beside it; nothing it records feeds back.

Bars (before any run):
  1. physicality stays yes in food and nofood under nicholson (finite, V inside reversal bounds, conc >= 0, no step
     alternation: the battery's own physicality row);
  2. no vital sign whose status is pass under off turns to a miss under nicholson, in either condition.
Adopt (recommend nicholson as the default, off nested) if 1 and 2 both hold; otherwise recommend keeping off and name
the sign that turned. A sign that moves but keeps its status is reported, not a reason either way.
Reported, no bar: vulval SER-7 and SER-1 occupancy at Hill 1 (EC50s from the ledger, 30 and 1340 nM) under each
toggle, the mean and the 5th-95th percentile over t >= 5 s (the battery's SETTLE_S), from the recorded 5-HT; the
near field's share of it; eggs laid and the vm Ca the battery records. Behavioural success is not evidence of correct
physiology, so eggs moving would be reported, not counted for the adoption.
Gate (the rule's "a gate"): the read's limit test (test_amine_synaptic: off returns 0 and leaves every pool value
unchanged; nicholson matches Nicholson's closed form) green on that tree. Figure: the vulval 5-HT and SER-7 occupancy
against time, both toggles, both conditions, viewed before recommending.

Addendum (Mon 9 Nov 03:43 CST, before any 150 s run, no bar changed): wbody2's wiring (d3c2129) adds the near
field inside Mech.step, for vm2 only (vm1 keeps the pool), and concentrations() still returns the pool. So the record
moves to step's own outputs: at every step, the pool (concentrations()) and egg_5ht_near_nM; vm2's 5-HT is their sum
and the occupancies above are vm2's (vm1's are the pool's, reported beside them). The sidecar files move to
OUTDIR/vulva/, because `vitals table` reads every *.json in OUTDIR. A `bars` mode applies bars 1 and 2 to the stored
battery JSONs (the statuses `vitals table` prints, today's bars on the stored readouts; the battery calls a passing
sign "in", so bar 2 reads: no sign "in" under off is "miss" under nicholson; a move to "not produced" counts as
turning too, and is named).

Usage (backhouse, one process per condition and toggle):
    python adopt_near.py COND SECONDS OUTDIR TOGGLE     COND food | nofood, TOGGLE off | nicholson
writes OUTDIR/COND.json and COND.npz (the battery's) and OUTDIR/vulva/COND_vulva5ht.npz and COND_vulva5ht.json.
    python adopt_near.py bars OFF_DIR NICHOLSON_DIR     bars 1 and 2 per condition, and the verdict
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np

from wormemu.fit import vitals
from wormemu.mech import neuromod as nmod
from wormemu.mech import organs_egglaying as egg


def main(cond, seconds, outdir, toggle):
    assert toggle in nmod.SYNAPTIC, toggle
    rec, ec = [], {}
    orig_step = egg.Mech.step

    def step(self, ctx, dt_ms):
        r = orig_step(self, ctx, dt_ms)
        o = r.get("out", {})
        if "egg_5ht_near_nM" in o:                                   # the circuit form (timer and off record nothing)
            rec.append((float(ctx.t_ms), self.concentrations()[0], float(o["egg_5ht_near_nM"])))
            ec.update(ser1=float(self.ec5[0]), ser7=float(self.ec5[1]))   # the EC50s the module itself reads
        return r

    egg.Mech.step = step
    out = vitals.run(None, cond, float(seconds), outdir, toggles={"amine_synaptic": toggle})
    a = np.array(rec, float).reshape(-1, 3)
    vd = Path(outdir) / "vulva"
    vd.mkdir(parents=True, exist_ok=True)
    np.savez_compressed(vd / f"{cond}_vulva5ht.npz", t_ms=a[:, 0], c5_nM=a[:, 1] + a[:, 2], pool_nM=a[:, 1],
                        near_nM=a[:, 2])
    e7, e1 = ec.get("ser7"), ec.get("ser1")
    keep = a[:, 0] >= 1000.0 * vitals.SETTLE_S
    pool, near = a[keep, 1], a[keep, 2]
    c = pool + near
    pct = lambda x: [float(y) for y in np.percentile(x, [5, 95])]
    summ = dict(cond=cond, toggle=toggle, n_steps=int(len(a)), n_kept=int(keep.sum()), ec50_ser7_nM=e7,
                ec50_ser1_nM=e1)
    if len(c):
        summ.update(c5_vm2_mean_nM=float(c.mean()), c5_vm2_p5_p95_nM=pct(c), pool_mean_nM=float(pool.mean()),
                    near_mean_nM=float(near.mean()), near_share=float(near.mean() / c.mean()) if c.mean() else None)
    if len(c) and e7:
        for lab, k in (("ser7", e7), ("ser1", e1)):
            for where, x in (("vm2", c), ("vm1", pool)):
                occ = x / (x + k)
                summ[f"occ_{lab}_{where}_mean"] = float(occ.mean())
                summ[f"occ_{lab}_{where}_p5_p95"] = pct(occ)
    summ["physical"] = out["physicality"]["physical"]
    summ["eggs"] = out["readouts"].get("eggs")
    (vd / f"{cond}_vulva5ht.json").write_text(json.dumps(summ, indent=1, default=float))
    print(json.dumps(summ, default=float), flush=True)


def bars(off_dir, nich_dir):
    """Bars 1 and 2 (docstring) from the stored battery JSONs; prints per condition and the verdict."""
    ok = True
    for cond in ("food", "nofood"):
        r0, r1 = (json.loads((Path(d) / f"{cond}.json").read_text()) for d in (off_dir, nich_dir))
        s0, s1 = vitals.score(r0["readouts"], cond), vitals.score(r1["readouts"], cond)
        phys = bool(r1["physicality"]["physical"])
        turned = [f"{k} -> {(s1.get(k) or {}).get('status')}" for k, v in s0.items()
                  if v["status"] == "in" and (s1.get(k) or {}).get("status") != "in"]
        moved = [f"{k} {v['status']} -> {(s1.get(k) or {}).get('status')}" for k, v in s0.items()
                 if v["status"] != "in" and (s1.get(k) or {}).get("status") != v["status"]]
        print(f"{cond}: bar 1 physical under nicholson {'yes' if phys else 'NO'}; bar 2 passing signs under off "
              f"{sum(1 for v in s0.values() if v['status'] == 'in')}, turned {turned or 'none'}; "
              f"other status changes {moved or 'none'}")
        ok = ok and phys and not turned
    print("verdict:", "both bars hold: recommend nicholson as the default" if ok else "a bar fails: keep off")


if __name__ == "__main__":
    if sys.argv[1] == "bars":
        bars(*sys.argv[2:4])
    else:
        main(*sys.argv[1:5])
