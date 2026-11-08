"""Probe, row 7: NMJ GABA IPSC decay (receptor_unit_check.py item 3) against Liu et al. 2009 (24.8 +/- 2.7 ms).

Pre-registered (8 Nov, before the first run; written 13:09-13:14 CST, committed 0b63769 at 13:18):
  bar      decay tau of the single-exponential fit from the peak, 22.1-27.5 ms (the check's own bar, unchanged)
  ids      the gaps the check reads (traced: mech/receptors.site_params for class gabacl, wsyn.mod):
           rec_tmax_gaba_uM, rec_gabacl_tau_rise_ms, rec_gabacl_ss_frac, rec_des_recover_ratio
           (rec_gabacl_tau_off_ms 24.8, ec50 19.6, hill 1.3, tau_des 149 are scan: fixed; the release rate k is
           BAAIWorm's 0.1167 /ms, scan, set in the check)
  design   128 Sobol points in the bio box + 128 in the hard box, seed 0
  also     at the best point: the row 7 UNC-49 step check (134-164 ms) must still pass
  diag     (not a probe, a cause check) the same IPSC with the release state made instantaneous (k x 1000), to
           separate the release time course from the receptor's tau_off
Starts from the ledger values (at_ledger.patch), not the code templates.
"""
from __future__ import annotations

import sys

import numpy as np

from probe_lib import Box, joint_bad, save

import at_ledger

at_ledger.patch(["receptors"])
import receptor_unit_check as RU  # noqa: E402

IDS = ["rec_tmax_gaba_uM", "rec_gabacl_tau_rise_ms", "rec_gabacl_ss_frac", "rec_des_recover_ratio"]
LO, HI = 22.1, 27.5


def ipsc(over=None, extra=None):
    P0 = dict(RU.P)
    RU.P.update(over or {})
    try:
        t, i = RU.run("gabacl", [(50, 52, 50.0)], 400, extra=extra)
        tau, _ = RU.decay_tau(t, i, 50, 400)
        ts, ii = RU.run("gabacl", [(50, 1050, 50.0)], 1100, tmax_mM=10.0)
        tstep, _ = RU.decay_tau(ts, ii, 50, 1050)
    except Exception as e:                       # a failed fit is a non-pass, recorded
        print("fail", over, e, flush=True)
        tau, tstep = np.nan, np.nan
    finally:
        RU.P.clear()
        RU.P.update(P0)
    return tau, tstep


def main():
    box = Box(IDS)
    res = dict(check="row 7 NMJ GABA IPSC decay", bar=f"{LO}-{HI} ms", source="Liu et al. 2009 via receptor_unit_check")
    base, base_step = ipsc()
    res["at_ledger"] = dict(tau_ms=base, unc49_step_ms=base_step)
    res["diag_release_instant"] = dict(tau_ms=ipsc(extra={"k": 0.1166666666666666 * 1000})[0])
    for which in ("bio", "hard"):
        X = box.design(128, which=which, seed=0)
        taus, steps, bad = [], [], []
        for x in X:
            over = dict(zip(IDS, x))
            tau, ts = ipsc(over)
            taus.append(tau)
            steps.append(ts)
            bad.append(len(joint_bad(over)))
        taus, steps, bad = np.array(taus), np.array(steps), np.array(bad)
        ok = (taus >= LO) & (taus <= HI) & (bad == 0)
        both = ok & (steps > 134.1) & (steps < 163.9)
        miss = np.where(taus < LO, LO - taus, np.where(taus > HI, taus - HI, 0.0))
        k = int(np.nanargmin(np.abs(taus - 24.8)))
        res[which] = dict(n=len(X), n_pass=int(ok.sum()), n_pass_with_unc49=int(both.sum()),
                          pass_fraction=float(ok.mean()), tau_min=float(np.nanmin(taus)), tau_max=float(np.nanmax(taus)),
                          best=dict(zip(IDS, X[k].tolist())), best_tau=float(taus[k]), best_unc49_step=float(steps[k]),
                          best_edges=box.at_edge(X[k], which=which), best_in_bio=box.in_bio(X[k]),
                          min_miss_ms=float(np.nanmin(miss)), joint_bad=int((bad > 0).sum()),
                          pass_points=X[ok].tolist())
        print(which, res[which]["n_pass"], res[which]["tau_min"], res[which]["tau_max"], flush=True)
    res["bounds"] = box.describe()
    print(save("probe_nmj_ipsc", res))
    print({k: v for k, v in res.items() if k not in ("bio", "hard", "bounds")})


if __name__ == "__main__":
    main()
