"""wneuro item 2 trace (written Mon 9 Nov 2026 00:44 CST, before running): why the membrane read lowers vulval 5-HT
by about 40% (sero_food: off food, mean 0.424 nM membrane vs 0.697 soma; the soma read still rising at 20 s).
A diagnostic, no bar.

Release into HSN's compartment is J = ma_release_per_s x q x S x R per release cell (q drive from V, S store, R the
G-protein release factor). Uptake moves the other way: under the membrane read HSN's own MOD-5 sits 65% in the anterior
body, which would raise the vulval pool, so a lower pool must come from release (q or R) or from another cell's
uptake. Rule written before running: the factor whose mean ratio (soma / membrane) over the last 10 s is furthest from
1 among q, S and R of HSNL/R names the route; if R, the G protein that differs most and HSN's 5-HT receptors (CeNGEN,
neuromod's rule) name the receptor; if q, V and HSN's 5-HT-gated channels.
Addendum 00:51, after the first run (R 1.73x, Gs 9.6x; HSN's 5-HT GPCRs SER-4 and SER-5 cannot be occupied at 1 nM
against 1000 nM): the end-of-run dump of HSNL's receptor entries (peptides included, which the site toggle also
moves), ranked by their Gs or Gi part, names the receptor.

Method: sero_food's cells (wbody2's pharyngeal sub-brain plus the 5-HT, MOD-5 and egg-laying cells), the template
worm at the ledger values, food_OD 0, 20 s at 1 ms, neuromod_site = membrane, then soma. Every 100 ms for HSNL and
HSNR: V, q, S, R, G (q, i/o, s), the 5-HT each reads; the vulval pool; the 5-HT release and MOD-5 uptake in HSN's
compartment summed over cells.

Usage: python sero_trace.py [SECONDS] -> runs/worm/wneuro/sero_trace.json
"""
from __future__ import annotations

import json
import sys
import time
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[3]
for p in ("src", "scripts/worm", "scripts/worm/wbody2", "scripts/worm/wneuro"):
    sys.path.insert(0, str(ROOT / p))
import at_ledger  # noqa: E402

at_ledger.patch()
from sero_food import SERO  # noqa: E402
from wormemu import brain as B  # noqa: E402
from wormemu.interface import default_observation  # noqa: E402
from wormemu.mech import neuromod as N  # noqa: E402


def receptors_of(b, nm, cell):
    classes = set(b.st.cengen_classes)
    cls = N.cengen_class(nm.names[cell], classes)
    gp = [rg for lg, rg in N.AMINE_PAIRS if lg == "serotonin" and
          (1.0 if (cls, rg) in N.EXPR_ADD else b.st.expr(rg, cls)) > 0]
    ch = [N.N_EXTRA[row] for row, cells, *_ in nm.extrasyn if N.AMINES[row] == "serotonin" and cell in set(cells)]
    return dict(gpcr=gp, channels=ch, transporter=b.st.expr("mod-5", cls) > 0)


def one(secs, site):
    b = B.Brain(B.sample_worm(None), toggles={"neuromod_site": site}, cells=SERO)
    nm = next(m for m in b.mechs if type(m).__module__ == "wormemu.mech.neuromod")
    b.reset()
    s5 = N.AMINES.index("serotonin")
    hs = {c: b.idx[c] for c in ("HSNL", "HSNR")}
    k_v = int(nm.ma_comp[hs["HSNL"]])
    rel_v = [c for c in np.flatnonzero(nm.ma_rel[:, s5]) if nm.ma_comp[c] == k_v]
    rec = {"vulva": [], "release_vulva_per_s": []}
    for n in hs:
        for f in ("V", "q", "S", "R", "Gq", "Gi", "Gs", "read"):
            rec[f"{n}_{f}"] = []
    for k in range(int(round(secs * 1000))):
        obs = default_observation(b.t)
        obs.head["food_OD"] = 0.0
        o = b.step(obs, 1.0)
        if k % 100 == 99:
            R = nm.release_factor()
            rec["vulva"].append(float(nm.ma.nM()[s5, k_v]))
            rec["release_vulva_per_s"].append(float(sum(nm.p["ma_release_per_s"] * nm.q_ma[c] * nm.store[c, s5]
                                                        * R[c] for c in rel_v)))
            for n, c in hs.items():
                for f, x in (("V", o.v_mV[c]), ("q", nm.q_ma[c]), ("S", nm.store[c, s5]), ("R", R[c]),
                             ("Gq", nm.G[c, 0]), ("Gi", nm.G[c, 1]), ("Gs", nm.G[c, 2]),
                             ("read", nm.cell_nM(N.A, "serotonin", c))):
                    rec[f"{n}_{f}"].append(float(x))
    h = len(rec["vulva"]) // 2
    c, cp_, ca_ = hs["HSNL"], nm.pep.nM(), nm.ma.nM()
    rows = []                                              # HSNL's receptor entries at the end (as ris_gi.py)
    for e in np.flatnonzero(nm.e_cell == c):
        x = float(nm.pep_W[c] @ cp_[nm.e_lig[e]]) if nm.e_pep[e] else float(nm.ma_W[c] @ ca_[nm.e_lig[e]])
        occ = float(N._hill(np.array([x]), np.array([nm.e_ec50[e]]), nm.p["gpcr_hill"])[0])
        rows.append(dict(lig=N.PRECURSORS[nm.e_lig[e]] if nm.e_pep[e] else N.AMINES[nm.e_lig[e]], nM=x,
                         ec50=float(nm.e_ec50[e]), occ=occ, w=[float(w) for w in nm.e_w[e]],
                         gs_part=float(nm.e_w[e][2] * occ), gi_part=float(nm.e_w[e][1] * occ)))
    rows.sort(key=lambda r: -max(r["gs_part"], r["gi_part"]))
    return dict(site=site, vulva_comp=k_v, release_cells_in_vulva=[nm.names[c] for c in rel_v],
                hsn_receptors=receptors_of(b, nm, hs["HSNL"]), hsnl_top_entries=rows[:8],
                last10_mean={k: float(np.mean(v[h:])) for k, v in rec.items()}, trace=rec)


def main():
    secs = float(sys.argv[1]) if len(sys.argv) > 1 else 20.0
    t0 = time.time()
    runs = {site: one(secs, site) for site in ("membrane", "soma")}
    m, s = runs["membrane"]["last10_mean"], runs["soma"]["last10_mean"]
    ratio = {k: (s[k] / m[k] if m[k] else float("nan")) for k in m}
    res = dict(bio_s=secs, wall_s=time.time() - t0, ratio_soma_over_membrane=ratio, runs=runs)
    (ROOT / "runs/worm/wneuro/sero_trace.json").write_text(json.dumps(res, indent=1, default=float))
    print("receptors HSNL", runs["membrane"]["hsn_receptors"], "release cells in vulva", runs["membrane"]["release_cells_in_vulva"])
    for site, r in runs.items():
        print(site, [(x["lig"], round(x["nM"], 4), x["ec50"], round(x["gs_part"], 3), round(x["gi_part"], 3))
                     for x in r["hsnl_top_entries"][:5]])
    for k in m:
        print(f"{k:24s} membrane {m[k]:.4g}  soma {s[k]:.4g}  ratio {ratio[k]:.3f}")


if __name__ == "__main__":
    main()
