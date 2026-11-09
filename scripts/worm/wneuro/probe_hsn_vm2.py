"""wneuro Open 7 near field, feasibility probe (written Mon 9 Nov 2026 02:00 CST, before running; Director 01:40 item 2).

Question: with HSN's 5-HT read at its release sites onto vm2 (amine_synaptic=nicholson, mech/neuromod near_nM), does any
geometry and release rate inside their ranges bring the vm2 receptor's 5-HT up to SER-7's EC50 (30 nM, measured,
Hobson et al. 2006) at the worm's own drive? Same for SER-1 (1340 nM, measured, Xie 2005 via Dernovici 2006). If it
passes only at a range edge, say so (that would point at the release rate or the heterologous EC50s, item 6).

Method. As probe_amine.py: the template worm's Mech (neuromod) at the ledger values, pc_grid=bins (the default),
membrane read, built once in a Brain, then stepped alone (no NEURON) at 10 ms for 60 s, peptides off; every release
cell's drive held at its measured on-food 20 s mean and its release factor R at its mean (release_drive_food1.02.json,
recorded under four with the old store; probe_amine's 01:55 addendum: bins moves HSN's 5-HT read by under 0.2 nM);
every other cell at -80 mV; stores full at t = 0. Release: ma_release_per_s at 17 log-spaced values over its range
1e3-1e7 (the template 1e5 among them), one run each; recorded, mean over the last 20 s: HSNL's and HSNR's 5-HT release
J (molecules/s) and the far field, the pool at HSNL's bin (what organs_egglaying reads now). Geometry: 512 scrambled
Sobol points (seed 0) over the seven near-field Specs inside their bio ranges (hsn_vm2_site_receptor_um 0.02-1 and
ecs_alpha 0.09-1 log-uniform; ecs_tortuosity 1-1.86, syn_half_space 1-2, hsn_vm2_sites 12-24, hsn_vm2_region_um 5-15
uniform; hsn_vm2_release_share 0.1-1 log-uniform), the same points at every release value, plus the template geometry.
Read at the vm2 receptor: C = far + near_nM("serotonin", [HSNL, HSNR], J) (both HSNs synapse on every vm2 cell, Cook
2019; their sites interleaved over the region, which is the generous arrangement).

Bars (before running): reaches SER-7 if C >= 30 nM; reaches SER-1 if C >= 1340 nM (occupancy >= 0.5 at Hill 1).
Feasible = at least one (release, geometry) point reaches. "Only at an edge" = every reaching point has at least one
coordinate (log for the log-uniform ones and the release) within 5% of its range from an edge (probe_amine's rule).
Reported, not adopted: per release value the fraction of geometry points that reach; at the template release, the
reaching points, interior or edge; at the template geometry, the smallest release that reaches; the rank correlation of
each coordinate with log C at the template release. Consistency check (not a bar on the model): the far field at the
template must reproduce probe_amine_bins's vulva SER-7 ratio x 30 nM within 2%.
Also, one ceiling row (not in the box): HSNL and HSNR at full drive (0 mV), template release and geometry.

The steady form bounds the time-averaged occupancy from above (neuromod docstring), so "does not reach" is firm and
"reaches" is an upper bound. The drive is the template's; whether HSN's drive is right is the activity side.

Usage: python probe_hsn_vm2.py -> runs/worm/wneuro/probe_hsn_vm2.json
"""
from __future__ import annotations

import json
import sys
import time
from pathlib import Path
from types import SimpleNamespace

import numpy as np
from scipy.stats import qmc, spearmanr

ROOT = Path(__file__).resolve().parents[3]
for p in ("src", "scripts/worm", "scripts/worm/wneuro"):
    sys.path.insert(0, str(ROOT / p))
import at_ledger  # noqa: E402

at_ledger.patch()
from probe_amine import setup  # noqa: E402
from wormemu.mech import neuromod as N  # noqa: E402

SECS, DT, LAST = 60.0, 10.0, 20.0
GEOM = {"hsn_vm2_site_receptor_um": (0.02, 1.0, "log"), "ecs_alpha": (0.09, 1.0, "log"),
        "ecs_tortuosity": (1.0, 1.86, "lin"), "syn_half_space": (1.0, 2.0, "lin"), "hsn_vm2_sites": (12, 24, "lin"),
        "hsn_vm2_region_um": (5.0, 15.0, "lin"), "hsn_vm2_release_share": (0.1, 1.0, "log")}
REL = (1e3, 1e7)


def to_unit(k, x):
    lo, hi, sc = GEOM[k] if k in GEOM else (*REL, "log")
    return (np.log10(x / lo) / np.log10(hi / lo)) if sc == "log" else (x - lo) / (hi - lo)


def run(nm, p0, v, release):
    nm.p = {**p0, "ma_release_per_s": release}
    nm.reset()
    ctx = SimpleNamespace(v=v, outputs={})
    hsn = [nm.names.index("HSNL"), nm.names.index("HSNR")]
    s5 = N.AMINES.index("serotonin")
    k_h = int(nm.ma_comp[hsn[0]])
    steps, n0 = int(round(SECS * 1000 / DT)), int(round((SECS - LAST) * 1000 / DT))
    far, J = [], []
    for k in range(steps):
        nm.step(ctx, DT)
        if k >= n0:
            far.append(nm.ma.nM()[s5, k_h])
            J.append(nm.ma_J[hsn, s5].copy())
    return float(np.mean(far)), np.mean(J, 0)


def main():
    t0 = time.time()
    b, nm, p0, v, drive = setup()
    nm.synaptic = "nicholson"
    assert nm.grid == "bins"
    hsn = [nm.names.index("HSNL"), nm.names.index("HSNR")]
    e7, e1 = float(p0["ma_ec50_serotonin_ser-7_nM"]), float(p0["ma_ec50_serotonin_ser-1_nM"])
    rels = np.logspace(3, 7, 17)
    keys = list(GEOM)
    U = qmc.Sobol(len(keys), scramble=True, seed=0).random(512)
    pts = []
    for u in U:
        pt = {}
        for k, x in zip(keys, u):
            lo, hi, sc = GEOM[k]
            pt[k] = float(lo * (hi / lo) ** x) if sc == "log" else float(lo + x * (hi - lo))
        pts.append(pt)
    tmpl = {k: float(p0[k]) for k in keys}
    res = dict(ec50_ser7_nM=e7, ec50_ser1_nM=e1, template_geometry=tmpl, by_release=[], drive_hsn={
        c: drive[c] for c in ("HSNL", "HSNR")})

    def near(p_geo, J):
        nm.p = {**nm.p, **p_geo}
        return nm.near_nM("serotonin", hsn, J=J)

    all_reach7, all_reach1 = [], []
    for rel in rels:
        far, J = run(nm, p0, v, float(rel))
        nt = near(tmpl, J)
        C = np.array([far + near(pt, J) for pt in pts])
        row = dict(release=float(rel), far_nM=far, J_hsn=J.tolist(), near_template_nM=nt,
                   C_template_nM=far + nt, C_box_max_nM=float(C.max()), C_box_median_nM=float(np.median(C)),
                   frac_reach_ser7=float((C >= e7).mean()), frac_reach_ser1=float((C >= e1).mean()))
        if np.isclose(rel, 1e5):
            row["C_box"] = C.tolist()
        res["by_release"].append(row)
        for pt, c in zip(pts, C):
            full = {**pt, "ma_release_per_s": float(rel)}
            if c >= e7:
                all_reach7.append((full, float(c)))
            if c >= e1:
                all_reach1.append((full, float(c)))
        print(f"release {rel:9.3g}: far {far:.3f} nM, J {J.round(0)}, template C {far + nt:.2f} nM, box max "
              f"{C.max():.1f}, SER-7 {row['frac_reach_ser7']:.3f}, SER-1 {row['frac_reach_ser1']:.3f}", flush=True)

    def edge(full):
        u = [to_unit(k, x) for k, x in full.items()]
        return any(min(x, 1 - x) < 0.05 for x in u)

    res["summary"] = {}
    for lab, reach in (("ser-7", all_reach7), ("ser-1", all_reach1)):
        e = [edge(f) for f, _ in reach]
        at_t = [(f, c) for f, c in reach if np.isclose(f["ma_release_per_s"], 1e5)]
        res["summary"][lab] = dict(n_reach=len(reach), n_total=len(pts) * len(rels), n_edge=int(sum(e)),
                                   n_interior=int(len(e) - sum(e)), feasible=bool(reach),
                                   only_at_edge=bool(reach) and all(e),
                                   n_reach_at_template_release=len(at_t),
                                   n_interior_at_template_release=int(sum(not edge(f) for f, _ in at_t)),
                                   min_release_reaching=float(min(f["ma_release_per_s"] for f, _ in reach))
                                   if reach else None,
                                   interior_examples=[f for f, _ in reach if not edge(f)][:5])
    for lab, ec in (("ser-7", e7), ("ser-1", e1)):
        ok = [r["release"] for r in res["by_release"] if r["C_template_nM"] >= ec]
        res["summary"][lab]["template_geometry_min_release"] = min(ok) if ok else None
    t = next(r for r in res["by_release"] if np.isclose(r["release"], 1e5))
    C = np.array(t["C_box"])
    res["rank_corr_log_C_template_release"] = {k: float(spearmanr([pt[k] for pt in pts], np.log(C))[0])
                                               for k in keys}
    pa = ROOT / "runs/worm/wneuro/probe_amine_bins.json"
    if pa.exists():
        ref = json.loads(pa.read_text())["template"]["vulva ser-7"] * e7
        res["consistency_far_vs_probe_amine"] = dict(far_nM=t["far_nM"], probe_amine_nM=ref,
                                                     rel_err=abs(t["far_nM"] / ref - 1), passed=abs(t["far_nM"] / ref
                                                                                                  - 1) < 0.02)
    vc = v.copy()
    vc[hsn] = 0.0
    far, J = run(nm, p0, vc, float(p0["ma_release_per_s"]))
    res["ceiling_full_drive"] = dict(far_nM=far, J_hsn=J.tolist(), near_template_nM=near(tmpl, J),
                                     C_template_nM=far + near(tmpl, J))
    res["wall_s"] = time.time() - t0
    (ROOT / "runs/worm/wneuro/probe_hsn_vm2.json").write_text(json.dumps(res, indent=1, default=float))
    print(json.dumps({k: v for k, v in res.items() if k not in ("by_release",)}, indent=1, default=float))


if __name__ == "__main__":
    main()
