"""Probe, row 15: the egg-laying circuit's active/inactive pattern (scripts/worm/organs/check_egglaying.py, unchanged).

Pre-registered (8 Nov 13:47 CST, before the first run):
  cause    traced first (egg_5ht.py, 10 s): HSN rests at -53.6 mV (0.65 % of the time above -30 mV), vulval 5-HT
           0.33 nM against EC50s of 30 (SER-7) and 1000 nM (SER-1); 15 nM even at full drive at the ledger release.
  ids      the 17 gap numbers the check reads between HSN and an egg (traced in mech/organs_egglaying and
           mech/neuromod): egg_stretch_half, egg_stretch_hill, egg_stretch_g_nS, egg_5ht_g_nS, egg_nlp3_g_nS,
           egg_act_khalf_mM, egg_act_hill, egg_vm_act_on, egg_vm_act_off, egg_ret_gain_pA, egg_uv1_tyr_uM_per_egg,
           egg_uv1_tyr_tau_s, egg_lgc55_g_nS, egg_production_per_h, ma_release_per_s, ma_degrade_tau_s,
           ma_ec50_serotonin_ser-1_nM. HSN's and VC's membranes are scan (BAAIWorm) and not searched.
  design   64 Sobol points in the bio box, seed 0
  stage 1  wild type, 3 bio-h, the check's own run(): bars 1-3 (>= 3 clusters of >= 2 eggs; intracluster mean 5-60 s;
           intercluster mean 10-60 min). A point failing stage 1 fails the check.
  stage 2  the unc-103 null (bar 4: uterus over the last hour <= 0.7 x wild type) at stage-1 passers only.
  cutoff   points not finished by 16:50 CST are reported as not run; the pass fraction is over finished points.
  verdict  any point passing both stages -> D; none -> not D (the class then rests on the structural evidence).
Each point writes runs/worm/triage/probe_egg/NNN.json as it finishes (the laptop may sleep; backhouse keeps going).
Stopped 8 Nov 14:10 CST with no point finished: 525 s wall per 10 bio-min on backhouse (about 2.6 h a point, 17 h for
64 at 10 workers). Row 15 is classed on the structural evidence; this probe is the phase-2 spec, unchanged.
Amended 8 Nov 14:51 CST, before any point finished (the Director's answer 3): the three other 5-HT path gaps from
line vi join the ids (ma_store_molecules, ma_synth_tau_s, ma_tau_ms; 20 ids, so the Sobol design changes). The run
is overnight on backhouse: it sleeps until 22:00, 16 single-thread workers, a 16 h timeout, a done-file. The 16:50
cutoff becomes the timeout: points not finished when it fires are reported as not run. Bars, stages and verdict
unchanged. Caveat as in line vi: this brain has no MOD-5 cells, so no 5-HT reuptake.

Usage (backhouse): python probe_egg.py [--workers=W] [--stage2]
"""
from __future__ import annotations

import json
import os
import sys
import time

import numpy as np

from probe_lib import OUT, Box, joint_bad, save

IDS = ["egg_stretch_half", "egg_stretch_hill", "egg_stretch_g_nS", "egg_5ht_g_nS", "egg_nlp3_g_nS",
       "egg_act_khalf_mM", "egg_act_hill", "egg_vm_act_on", "egg_vm_act_off", "egg_ret_gain_pA",
       "egg_uv1_tyr_uM_per_egg", "egg_uv1_tyr_tau_s", "egg_lgc55_g_nS", "egg_production_per_h", "ma_release_per_s",
       "ma_degrade_tau_s", "ma_ec50_serotonin_ser-1_nM", "ma_store_molecules", "ma_synth_tau_s", "ma_tau_ms"]
HOURS = 3.0
DIR = OUT / "probe_egg"


def stage1_ok(w):
    return bool(w["n_clusters_ge2"] >= 3 and w["intra_mean_s"] is not None and 5.0 <= w["intra_mean_s"] <= 60.0
                and w["inter_mean_min"] is not None and 10.0 <= w["inter_mean_min"] <= 60.0)


def point(a):
    k, x, null = a
    f = DIR / (f"{k:03d}_null.json" if null else f"{k:03d}.json")
    if f.exists():
        return json.loads(f.read_text())
    import at_ledger
    at_ledger.patch()
    from probe_run import override
    override(dict(zip(IDS, map(float, x))))
    sys.path.insert(0, str(OUT.parents[2] / "scripts" / "worm" / "organs"))
    import check_egglaying as CE
    t0 = time.time()
    try:
        r = CE.run(HOURS, {"egg_unc103": "off"} if null else {}, "null" if null else f"p{k}")
        r.pop("egg_times_s", None)
    except Exception as e:                         # a crash is a non-pass, recorded
        r = {"error": f"{type(e).__name__}: {e}"[:300]}
    r.update(k=k, x=dict(zip(IDS, map(float, x))), wall_s=time.time() - t0)
    f.write_text(json.dumps(r, indent=1, default=float))
    return r


def main():
    workers = next((int(a[10:]) for a in sys.argv if a.startswith("--workers=")), 8)
    DIR.mkdir(parents=True, exist_ok=True)
    box = Box(IDS)
    X = box.design(64, which="bio", seed=0)
    jb = [len(joint_bad(dict(zip(IDS, x)))) for x in X]
    import multiprocessing as mp
    jobs = [(k, x, "--stage2" in sys.argv) for k, x in enumerate(X)]
    if "--stage2" in sys.argv:
        jobs = [j for j in jobs if (DIR / f"{j[0]:03d}.json").exists()
                and stage1_ok(json.loads((DIR / f"{j[0]:03d}.json").read_text()))]
    with mp.get_context("fork").Pool(workers, maxtasksperchild=1) as pool:
        pool.map(point, jobs, chunksize=1)
    rows = [json.loads((DIR / f"{k:03d}.json").read_text()) if (DIR / f"{k:03d}.json").exists() else None
            for k in range(len(X))]
    s1 = [bool(r and "error" not in r and stage1_ok(r)) for r in rows]
    res = dict(probe="egg", n=len(X), n_finished=sum(r is not None for r in rows), n_stage1=sum(s1),
               n_joint_bad=sum(b > 0 for b in jb), bounds=box.describe(),
               points=[dict(k=k, stage1=s, joint_bad=jb[k], edges=box.at_edge(X[k]),
                            eggs=r and r.get("eggs"), clusters=r and r.get("n_clusters_ge2"),
                            intra=r and r.get("intra_mean_s"), inter=r and r.get("inter_mean_min"),
                            vm_act_max=r and r.get("vm_act_max"), occ5_max=r and r.get("occ5_max"),
                            hsn_hi=r and r.get("hsn_frac_above_m30"), error=r and r.get("error"))
                       for k, (r, s) in enumerate(zip(rows, s1))])
    print(save("probe_egg", res))
    print("egg finished", res["n_finished"], "stage1 pass", res["n_stage1"], flush=True)


if __name__ == "__main__":
    os.environ.setdefault("OMP_NUM_THREADS", "1")
    main()
