"""wneuro near field on every other amine route (written Mon 9 Nov 2026 02:47 CST, before running; Director 02:46 item 2).

Question: item 6 found every amine GPCR near off from the pool (maximum occupancy under 0.1 at rest and on food). For
each route where Cook et al. 2019 has synapses from a release cell of the amine onto a neuron that expresses the
receptor, does the same near-field form as HSN onto vm2 (mech/neuromod near_nM with post: Nicholson's steady point
source, shared geometry, per-route site counts and release shares from Cook's counts) bring the receptor to its EC50
at the worm's own on-food drive, and if so where in the box?

Routes: (amine, receptor, post) for the 14 AMINE_PAIRS, post a neuron that expresses the receptor by neuromod's own
rule (CeNGEN class, > 0, EXPR_ADD; amine_potency.pairs), with at least one release cell of the amine (neuromod's
ma_rel) making Cook synapses onto it. The amine-gated channels (MOD-1, LGC-55, LGC-53) are left out: at synapses they
are the brain's synapse layer already (receptors.py), so a near-field read would count them twice. HSN onto vm2 is
probe_hsn_vm2's (vm2 is a muscle; no CeNGEN profile) and is not repeated.

Method. As probe_hsn_vm2.py: the template worm's Mech at the ledger values, pc_grid=bins, membrane read, built once in a
Brain, stepped alone (no NEURON) at 10 ms for 60 s, peptides off; every release cell's drive held at its on-food 20 s
mean and its release factor at its mean (release_drive_food1.02.json); every other cell at -80 mV; stores full at
t = 0. Release ma_release_per_s at 17 log-spaced values over 1e3-1e7, one run each; recorded, mean over the last 20 s:
each release cell's J (molecules/s) and the far field each post cell reads (its membrane weights over the bins).
Geometry: 512 scrambled Sobol points (seed 0) over the six shared near-field Specs inside their ranges:
syn_site_receptor_um 0.02-1 (log), ecs_alpha 0.09-1 (log), ecs_tortuosity 1-1.86, syn_half_space 1-2,
syn_site_spacing_um 0.5-20 (log), syn_release_share 0.1-1 (log); the same points at every release, plus the template.
The near field is linear in each pre cell's J, so it is computed through near_nM once per (route, pre cell, geometry)
at J = 1 and scaled by each run's J; the read is the largest pre cluster's (near_nM's rule).
Read at the receptor: C = far(post) + near.

Bars (before running). A route reaches if C >= the pair's EC50 (occupancy >= 0.5 at any Hill). Each route gets one
class: T reaches at the template release and template geometry; G reaches at the template release with some box
geometry but not the template's (interior if at least one such point has every coordinate more than 5% of its range
from an edge, log for the log ones); R reaches only with release above the template (the smallest release reported,
and whether any reaching point is interior, the release counted as a coordinate); N no point of the box reaches.
Per pair: the count of routes per class and the best route. "The same form applies" to a pair if it has a route; it
"changes item 6's conclusion" if any route is T or G. Reported, not adopted.
Also, per pair, one ceiling row (not in the box): every release cell of the amine at full drive (0 mV), template
release and geometry, the best route's C / EC50. And one cross-check (not a bar on the model): the generic Cook rule
applied to HSN onto vm2 at the template, against the HSN route's own value (expected about 2x lower: Cook counts 33
vulval synapses per HSNL, Patel 16, derived).

The steady form bounds the time-averaged occupancy from above (neuromod docstring), and placing the receptor at the
synapse is the generous assumption, so N is firm and T / G / R are upper bounds. The drive is the template's.

Addendum (Mon 9 Nov 2026 02:51 CST, after the first run, before re-running; no bar or class changes). Two reports
added. (1) Per route, the smallest release at which the pool alone (far >= EC50) reaches, beside the smallest with the
near field, so the near field's own effect on the release needed is visible. (2) The HSN cross-check found no vm2 cell
in the brain (cell_names are the 302 neurons and the body-wall muscles), so it now runs on a stand-in Mech over Cook's
whole cell list (neuromod alone; only near_nM is called), with the probe's own template J for HSNL and HSNR. The first
run's numbers are kept as probe_routes_run1.json.

Usage: python probe_routes.py -> runs/worm/wneuro/probe_routes.json
"""
from __future__ import annotations

import json
import sys
import time
from pathlib import Path
from types import SimpleNamespace

import numpy as np
from scipy.stats import qmc

ROOT = Path(__file__).resolve().parents[3]
for p in ("src", "scripts/worm", "scripts/worm/wneuro"):
    sys.path.insert(0, str(ROOT / p))
import at_ledger  # noqa: E402

at_ledger.patch()
from amine_potency import pairs  # noqa: E402
from probe_amine import setup  # noqa: E402
from wormemu.mech import neuromod as N  # noqa: E402

SECS, DT, LAST = 60.0, 10.0, 20.0
GEOM = {"syn_site_receptor_um": (0.02, 1.0, "log"), "ecs_alpha": (0.09, 1.0, "log"),
        "ecs_tortuosity": (1.0, 1.86, "lin"), "syn_half_space": (1.0, 2.0, "lin"),
        "syn_site_spacing_um": (0.5, 20.0, "log"), "syn_release_share": (0.1, 1.0, "log")}
REL = (1e3, 1e7)


def unit(lo, hi, sc, x):
    return np.log10(x / lo) / np.log10(hi / lo) if sc == "log" else (x - lo) / (hi - lo)


def run(nm, p0, v, release, posts, rel_cells):
    nm.p = {**p0, "ma_release_per_s": release}
    nm.reset()
    ctx = SimpleNamespace(v=v, outputs={})
    steps, n0 = int(round(SECS * 1000 / DT)), int(round((SECS - LAST) * 1000 / DT))
    acc, J, k = np.zeros_like(nm.ma.N), np.zeros_like(nm.ma_rel), 0
    for s in range(steps):
        nm.step(ctx, DT)
        if s >= n0:
            acc += nm.ma.nM()
            J += nm.ma_J
            k += 1
    C, J = acc / k, J / k
    far = {(row, c): float(nm.ma_W[c] @ C[row]) for row, c in posts}
    return far, J


def main():
    t0 = time.time()
    b, nm, p0, v, drive = setup()
    nm.synaptic = "nicholson"
    assert nm.grid == "bins"
    cn, out = nm.cook_counts()
    routes = []                                         # (pair label, amine row, ec50, post, [pre cells])
    for lab, row, cells, ec, _ in pairs(b, nm):
        if "(channel)" in lab:
            continue
        rel = np.flatnonzero(nm.ma_rel[:, row] > 0)
        for c in cells:
            pre = [int(r) for r in rel if cn[r, c] > 0]
            if pre:
                routes.append((lab, row, ec, int(c), pre))
    print(f"{len(routes)} routes", flush=True)
    keys = list(GEOM)
    U = qmc.Sobol(len(keys), scramble=True, seed=0).random(512)
    pts = [{k: float(lo * (hi / lo) ** x) if sc == "log" else float(lo + x * (hi - lo))
            for k, x, (lo, hi, sc) in zip(keys, u, GEOM.values())} for u in U]
    tmpl = {k: float(p0[k]) for k in keys}
    geos = [tmpl] + pts                                 # index 0 the template
    # unit fields: near_nM at J = 1 per (route, pre cell, geometry)
    unitf = []
    for lab, row, ec, c, pre in routes:
        A = np.zeros((len(geos), len(pre)))
        for g, geo in enumerate(geos):
            nm.p = {**p0, **geo}
            for j, r in enumerate(pre):
                A[g, j] = nm.near_nM(N.AMINES[row], [r], J=[1.0], post=c)
        unitf.append(A)
    posts = sorted({(row, c) for _, row, _, c, _ in routes})
    rels = np.logspace(3, 7, 17)
    C = np.zeros((len(rels), len(routes), len(geos)))   # read at the receptor, nM
    farr = np.zeros((len(rels), len(routes)))
    for i, rel in enumerate(rels):
        far, J = run(nm, p0, v, float(rel), posts, None)
        for k, (lab, row, ec, c, pre) in enumerate(routes):
            near = (unitf[k] * J[pre, row][None, :]).max(1)
            C[i, k] = far[(row, c)] + near
            farr[i, k] = far[(row, c)]
        print(f"release {rel:9.3g}: done ({time.time() - t0:.0f} s)", flush=True)
    it = int(np.argmin(abs(np.log10(rels) - 5)))         # template 1e5
    assert np.isclose(rels[it], p0["ma_release_per_s"])
    ec = np.array([r[2] for r in routes])
    reach = C >= ec[None, :, None]
    gu = np.array([[unit(*GEOM[k], geo[k]) for k in keys] for geo in geos])        # (geos, 6)
    g_edge = (np.minimum(gu, 1 - gu) < 0.05).any(1)
    r_u = unit(*REL, "log", rels)
    r_edge = np.minimum(r_u, 1 - r_u) < 0.05
    res = dict(n_routes=len(routes), routes=[], template_geometry=tmpl, releases=rels.tolist())
    for k, (lab, row, ec_, c, pre) in enumerate(routes):
        R = reach[:, k]
        if R[it, 0]:
            cls = "T"
        elif R[it, 1:].any():
            cls = "G"
        elif R[it + 1:].any():
            cls = "R"
        else:
            cls = "N"
        interior_g = bool((R[it, 1:] & ~g_edge[1:]).any())
        hi_idx = np.flatnonzero(R.any(1))
        min_rel = float(rels[hi_idx.min()]) if hi_idx.size else None
        interior_r = bool((R[:, 1:] & ~g_edge[None, 1:] & ~r_edge[:, None]).any())
        pool = np.flatnonzero(farr[:, k] >= ec_)
        min_rel_pool = float(rels[pool.min()]) if pool.size else None
        res["routes"].append(dict(pair=lab, post=nm.names[c], pre=[nm.names[r] for r in pre],
                                  cook=[int(cn[r, c]) for r in pre], n_out=[int(out[r]) for r in pre],
                                  ec50_nM=ec_, cls=cls, far_template_nM=float(farr[it, k]),
                                  C_template_nM=float(C[it, k, 0]), ratio_template=float(C[it, k, 0] / ec_),
                                  box_max_ratio_template_release=float(C[it, k, 1:].max() / ec_),
                                  frac_box_reach_template_release=float(R[it, 1:].mean()),
                                  interior_at_template_release=interior_g, min_release_reaching=min_rel,
                                  interior_any=interior_r, autapse=c in pre, min_release_pool_only=min_rel_pool,
                                  far_by_release_nM=farr[:, k].tolist(),
                                  C_template_geometry_by_release_nM=C[:, k, 0].tolist()))
    # per pair
    res["pairs"] = {}
    for lab in sorted({r[0] for r in routes}):
        rr = [x for x in res["routes"] if x["pair"] == lab]
        best = max(rr, key=lambda x: x["ratio_template"])
        res["pairs"][lab] = dict(n_routes=len(rr), by_class={c: sum(x["cls"] == c for x in rr) for c in "TGRN"},
                                 best_post=best["post"], best_pre=best["pre"], best_ratio_template=best["ratio_template"],
                                 best_box_max_ratio_template_release=max(x["box_max_ratio_template_release"] for x in rr),
                                 min_release_reaching=min((x["min_release_reaching"] for x in rr
                                                           if x["min_release_reaching"]), default=None),
                                 min_release_pool_only=min((x["min_release_pool_only"] for x in rr
                                                            if x["min_release_pool_only"]), default=None))
    # ceiling: every release cell of the amine at 0 mV, template release and geometry
    vc = v.copy()
    vc[np.flatnonzero(nm.ma_rel.sum(1) > 0)] = 0.0
    far, J = run(nm, p0, vc, float(p0["ma_release_per_s"]), posts, None)
    for lab in res["pairs"]:
        best = 0.0
        for k, (lb, row, ec_, c, pre) in enumerate(routes):
            if lb == lab:
                best = max(best, (far[(row, c)] + (unitf[k][0] * J[pre, row]).max()) / ec_)
        res["pairs"][lab]["ceiling_best_ratio"] = best
    # cross-check: the generic rule on HSN onto vm2, on a stand-in Mech over Cook's whole cell list
    hsn = [nm.names.index("HSNL"), nm.names.index("HSNR")]
    s5 = N.AMINES.index("serotonin")
    far, J = run(nm, p0, v, float(p0["ma_release_per_s"]), [], None)
    st = b.st
    allb = SimpleNamespace(st=st, cell_names=list(st.names), is_muscle=np.array([k != "neuron" for k in st.kind]),
                           spec=SimpleNamespace(values={}), layers=None)
    sm = N.Mech(allb, dict(p0), {"peptides": "off", "monoamines": "compartments", "amine_synaptic": "nicholson"})
    h2 = [sm.names.index("HSNL"), sm.names.index("HSNR")]
    vm2 = [k for k, x in enumerate(sm.names) if x.lower().startswith("vm2")]
    res["hsn_vm2_cross_check"] = dict(
        J_hsn=J[hsn, s5].tolist(), hsn_route_nM=sm.near_nM("serotonin", h2, J=J[hsn, s5]),
        generic_by_vm2={sm.names[c]: sm.near_nM("serotonin", h2, J=J[hsn, s5], post=c) for c in vm2})
    res["wall_s"] = time.time() - t0
    (ROOT / "runs/worm/wneuro/probe_routes.json").write_text(json.dumps(res, indent=1, default=float))
    for lab, d in res["pairs"].items():
        print(lab, json.dumps(d, default=float))
    print(json.dumps(res["hsn_vm2_cross_check"], default=float))
    print(f"wall {res['wall_s']:.0f} s")


if __name__ == "__main__":
    main()
