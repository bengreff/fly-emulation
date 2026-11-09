"""wneuro item 2 (written Sun 8 Nov 2026 23:19 CST, before running): head and vulval 5-HT on and off food, under the
new reading (neuromod_site=membrane: MOD-5 uptake and every 5-HT receptor read over the cell's membrane) against the
old one (soma), for wbody2's pumping and egg-laying. A re-measure, not a check: no bar, nothing tuned or adopted.

MOD-5's Km is 150 nM in both (measured, Ranganathan et al. 2001; the ledger already carried it, so at the ledger the
Km port changes nothing); ma_uptake_vmax_per_s stays guessed. Expected direction, reported not scored: head 5-HT
higher on food (NSM is active on food, Rhoades et al. 2019). wbody2's numbers to compare (pharyngeal sub-brain,
20 s, food_OD 1.02 vs 0, before this change): head 5-HT peak 0.0145 -> 1.05 nM, 0.88 nM at 20 s; MC SER-7 Gs
0.0005 -> 0.033; 0 pumps.

Method: the template worm at the ledger values, default toggles but neuromod_site; step(obs) with obs.head food_OD
set, dt 1 ms, SECONDS (20). Cells: sero = wbody2's pharyngeal sub-brain (pharynx_trace.PN) plus every serotonergic
or MOD-5 neuron outside it and the egg-laying circuit (HSN, VC01-06, ADF, AIM, RIH); whole = all 302. Records each
100 ms: 5-HT nM in the head compartment and in HSN's soma compartment (what organs_egglaying reads), 5-HT as NSM, HSN
and MC read it (Mech.cell_nM), MC's Gs; and pumps and eggs.

Usage: python sero_food.py [SECONDS] [cells=sero|whole] -> runs/worm/wneuro/sero_food_<cells>.json
"""
from __future__ import annotations

import json
import sys
import time
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[3]
for p in ("src", "scripts/worm", "scripts/worm/wbody2"):
    sys.path.insert(0, str(ROOT / p))
import at_ledger  # noqa: E402

at_ledger.patch()
from pharynx_trace import PN  # noqa: E402
from wormemu import brain as B  # noqa: E402
from wormemu.interface import default_observation  # noqa: E402
from wormemu.mech import neuromod as N  # noqa: E402

SERO = PN + ["HSNL", "HSNR", "VC01", "VC02", "VC03", "VC04", "VC05", "VC06", "ADFL", "ADFR", "AIML", "AIMR", "RIH"]


def one(secs, cells, site, food):
    b = B.Brain(B.sample_worm(None), toggles={"neuromod_site": site}, cells=cells)
    nm = next(m for m in b.mechs if type(m).__module__ == "wormemu.mech.neuromod")
    b.reset()
    row = N.AMINES.index("serotonin")
    hsn = b.idx["HSNL"]
    rd = {c: b.idx[c] for c in ("NSML", "HSNL", "MCL") if c in b.idx}
    rec = {k: [] for k in ["t", "head", "vulva"] + [f"read_{c}" for c in rd] + ["MC_gs"]}
    pumps = eggs = 0
    for k in range(int(round(secs * 1000))):
        obs = default_observation(b.t)
        obs.head["food_OD"] = food
        o = b.step(obs, 1.0)
        pumps += int(o.pumps)
        eggs += int(o.eggs_laid)
        if k % 100 == 99:
            c = nm.ma.nM()[row]
            rec["t"].append((k + 1) / 1000.0)
            rec["head"].append(float(c[0]))
            rec["vulva"].append(float(c[nm.ma_comp[hsn]]))
            for n, i in rd.items():
                rec[f"read_{n}"].append(nm.cell_nM(N.A, "serotonin", i))
            rec["MC_gs"].append(float(nm.G[rd["MCL"], 2]) if "MCL" in rd else float("nan"))
    s = {k: dict(max=float(np.max(v)), end=float(v[-1]), mean=float(np.mean(v))) for k, v in rec.items() if k != "t"}
    return dict(site=site, food_OD=food, pumps=pumps, eggs=eggs, vulva_comp=int(nm.ma_comp[hsn]),
                hsn_read_weights=nm.ma_W[hsn].round(3).tolist(), summary=s, trace=rec)


def main():
    secs = float(sys.argv[1]) if len(sys.argv) > 1 and "=" not in sys.argv[1] else 20.0
    which = next((a.split("=")[1] for a in sys.argv[1:] if a.startswith("cells=")), "sero")
    cells = SERO if which == "sero" else None
    t0 = time.time()
    runs = []
    for site in ("membrane", "soma"):
        for food in (0.0, 1.02):
            runs.append(one(secs, cells, site, food))
            r = runs[-1]
            print(site, food, "pumps", r["pumps"], "eggs", r["eggs"],
                  {k: round(v["max"], 4) for k, v in r["summary"].items()}, flush=True)
    res = dict(bio_s=secs, cells=which, wall_s=time.time() - t0, runs=runs)
    (ROOT / f"runs/worm/wneuro/sero_food_{which}.json").write_text(json.dumps(res, default=float))


if __name__ == "__main__":
    main()
