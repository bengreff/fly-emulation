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

Usage (backhouse, one process per condition and toggle):
    python adopt_near.py COND SECONDS OUTDIR TOGGLE     COND food | nofood, TOGGLE off | nicholson
writes OUTDIR/COND.json and COND.npz (the battery's) and OUTDIR/COND_vulva5ht.npz and COND_vulva5ht.json.
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
    orig = egg.Mech.concentrations

    def wrapped(self):
        c5, c3 = orig(self)
        nm, pool = self.nm, None
        if nm and len(self.hsn) and nm.on.get(nmod.A):
            pool = float(nm.ma.nM()[nmod.AMINES.index("serotonin"), nm.ma_comp[self.hsn[0]]])
        t = getattr(self, "_t_ms", None)
        rec.append((np.nan if t is None else t, c5, np.nan if pool is None else pool))
        ec.update(ser1=float(self.ec5[0]), ser7=float(self.ec5[1]))      # the EC50s the module itself reads
        return c5, c3

    orig_step = egg.Mech.step

    def step(self, ctx, dt_ms):
        self._t_ms = float(ctx.t_ms)
        return orig_step(self, ctx, dt_ms)

    egg.Mech.concentrations, egg.Mech.step = wrapped, step
    out = vitals.run(None, cond, float(seconds), outdir, toggles={"amine_synaptic": toggle})
    a = np.array(rec, float).reshape(-1, 3)
    outdir = Path(outdir)
    np.savez_compressed(outdir / f"{cond}_vulva5ht.npz", t_ms=a[:, 0], c5_nM=a[:, 1], pool_nM=a[:, 2])
    e7, e1 = ec.get("ser7"), ec.get("ser1")
    keep = a[:, 0] >= 1000.0 * vitals.SETTLE_S
    c = a[keep, 1]
    summ = dict(cond=cond, toggle=toggle, n_calls=int(len(a)), n_kept=int(keep.sum()),
                c5_mean_nM=float(np.mean(c)) if len(c) else None,
                c5_p5_p95_nM=[float(x) for x in np.percentile(c, [5, 95])] if len(c) else None,
                pool_mean_nM=float(np.nanmean(a[keep, 2])) if len(c) else None, ec50_ser7_nM=e7, ec50_ser1_nM=e1)
    if len(c) and e7:
        for lab, k in (("ser7", e7), ("ser1", e1)):
            occ = c / (c + k)
            summ[f"occ_{lab}_mean"] = float(occ.mean())
            summ[f"occ_{lab}_p5_p95"] = [float(x) for x in np.percentile(occ, [5, 95])]
    summ["physical"] = out["physicality"]["physical"]
    summ["eggs"] = out["readouts"].get("eggs")
    (outdir / f"{cond}_vulva5ht.json").write_text(json.dumps(summ, indent=1, default=float))
    print(json.dumps(summ, default=float), flush=True)


if __name__ == "__main__":
    main(*sys.argv[1:5])
