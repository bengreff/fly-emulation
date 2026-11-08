"""Probe, row 17 proprio: DVA stretch-channel Po in the senses_checks.proprio protocol (wtriage, 8 Nov 2026).

Pre-registered (8 Nov, before running; the run wrote its result at 13:26 CST):
  bar      the check's own sanity bars, unchanged: VB03 and SMDDL Po > 0.5 in their bend and < 0.1 in the opposite;
           DB03 the mirror; DVA Po > 0.5 in both the ventral and the dorsal bend (max over each 1 s window)
  ids      gaps the Po depends on (traced: mech/senses_proprio.strain and step): proprio_eps_half, proprio_eps_slope,
           proprio_tau_ms. Scan, fixed: proprio_radius_um 25, proprio_bfield_frac 0.2, proprio_smd_s1 0.1.
           Po does not depend on V, so the mechanism runs alone: the module's own strain() on the check's curvature
           arrays (senses_checks._kappa, 49 points), then its Po relaxation at dt 4 ms from the rest steady state.
  design   128 Sobol points in the bio box, seed 0
  also     rest Po (kappa 0) reported; DVA's mean strain under the half-body bend reported (the protocol's own number)
"""
from __future__ import annotations

import sys
from types import SimpleNamespace

import numpy as np

from probe_lib import Box, joint_bad, save

import senses_checks as SC
from wormemu.mech import senses_proprio as SP

IDS = ["proprio_eps_half", "proprio_eps_slope", "proprio_tau_ms"]
T = {s.id: s.template for s in SP.SPECS}


def strains():
    m = SP.Mech.__new__(SP.Mech)
    m.p = T
    m.cells = ["VB03", "DB03", "SMDDL", "SMDVL", "DVA"]
    m.kind = np.array(["b", "b", "smd", "smd", "dva"])
    m.sign = np.array([-1.0, 1.0, 1.0, -1.0, 1.0])
    m.s0 = np.array([0.3, 0.3, np.nan, np.nan, np.nan])        # a B cell whose anterior field lies in s 0-0.5
    m.split = False
    s = np.linspace(0, 1, 49)
    ob = lambda k: {"curvature_per_mm": k, "s": s}
    return {"rest": m.strain(ob(SC._kappa(per_mm=0.0))),
            "ventral": m.strain(ob(SC._kappa(s1=0.5, per_mm=-8.0))),
            "dorsal": m.strain(ob(SC._kappa(s1=0.5, per_mm=8.0))),
            "head_dorsal": m.strain(ob(SC._kappa(s1=0.1, per_mm=8.0)))}


def po_after(eps_rest, eps, h, sl, tau, win_ms=1000.0, dt=4.0):
    pinf = lambda e: 1.0 / (1.0 + np.exp(-(e - h) / sl))
    po = pinf(eps_rest)
    best = po.copy()
    for _ in range(int(win_ms / dt)):
        po = po + (pinf(eps) - po) * (1.0 - np.exp(-dt / tau))
        best = np.maximum(best, po)
    return best


def score(x, E):
    h, sl, tau = x
    P = {k: po_after(E["rest"], E[k], h, sl, tau) for k in ("ventral", "dorsal", "head_dorsal")}
    VB, DB, SMDD, SMDV, DVA = range(5)
    bars = dict(vb=P["ventral"][VB] > 0.5 and P["dorsal"][VB] < 0.1, db=P["dorsal"][DB] > 0.5 and P["ventral"][DB] < 0.1,
                dva=P["ventral"][DVA] > 0.5 and P["dorsal"][DVA] > 0.5,
                smd=P["head_dorsal"][SMDD] > 0.5 and P["head_dorsal"][SMDV] < 0.1)
    rest = 1.0 / (1.0 + np.exp(-(0.0 - h) / sl))
    return bars, dict(dva_ventral=float(P["ventral"][DVA]), vb_ventral=float(P["ventral"][VB]), rest=float(rest))


def main():
    E = strains()
    box = Box(IDS)
    base_bars, base = score([T[i] for i in IDS], E)
    X = box.design(128, which="bio", seed=0)
    rows = [score(x, E) for x in X]
    jb = np.array([len(joint_bad(dict(zip(IDS, x)))) for x in X])
    ok = np.array([all(b.values()) for b, _ in rows]) & (jb == 0)
    m = np.array([r["dva_ventral"] - 0.5 for _, r in rows])
    k = int(np.argmax(np.where(ok, np.minimum(m, 0.1 - np.array([r["rest"] for _, r in rows])), -9)))
    res = dict(check="row 17 proprio DVA Po", strains={k_: v.tolist() for k_, v in E.items()},
               cells=["VB03", "DB03", "SMDDL", "SMDVL", "DVA"], at_template=dict(bars=base_bars, **base),
               n=len(X), n_pass=int(ok.sum()), pass_fraction=float(ok.mean()), joint_bad=int((jb > 0).sum()),
               eps_half_pass_max=float(X[ok, 0].max()) if ok.any() else None,
               best=dict(zip(IDS, X[k].tolist())), best_detail=rows[k][1], best_edges=box.at_edge(X[k]),
               n_pass_rest_below_0p1=int(sum(1 for o, (_, r) in zip(ok, rows) if o and r["rest"] < 0.1)),
               bounds=box.describe())
    print(save("probe_dva", res))
    print({k_: v for k_, v in res.items() if k_ not in ("bounds", "strains")})
    print("strains", {k_: np.round(v, 4).tolist() for k_, v in E.items()})


if __name__ == "__main__":
    main()
