"""wneuro Open 7, the pool grid in the live worm (written Mon 9 Nov 2026 01:06 CST, before running). A re-measure, not a
check: no bar, nothing adopted (pc_grid stays `four` by default until the Director's gate).

Question: what does pc_grid=bins (8 um, grid_check.py) change in the template worm where it matters: 5-HT at the vulva
(what organs_egglaying reads: HSN's soma bin), 5-HT in the head and at MC (pumping), NLP-40 at DVB and AVL (the
defecation chain)? And what does it cost in wall time?

Expected (from grid_check, static, written down before running, not scored): the organ's vulval read rises by up to
2.6x (the four-compartment form read 0.39 of the exact value at HSN's source bin); the head's volume mean (the named
view) moves little (the bins conserve the same molecules; MOD-5 is near linear at c << Km 150 nM); reads of cells far
from a source fall. Falsifier for "a representation change, not a new source of molecules": the whole-body 5-HT total
differs by more than 10% between the grids.

Method: the template worm at the ledger values (at_ledger.patch), all 302 neurons, default toggles but pc_grid,
step(obs) with obs.head food_OD set, dt 1 ms, SECONDS (20). Every 100 ms: 5-HT head mean (named view), the organ's
vulval read (organs_egglaying.concentrations, else HSN's soma bin), 5-HT as HSNL, NSML and MCL read it (Mech.cell_nM),
MC's Gs, the whole-body 5-HT molecules; NLP-40 as DVB and AVL read it, their Gs; pumps, eggs.

Usage: python grid_live.py GRID FOOD [SECONDS] -> runs/worm/wneuro/grid_live_<grid>_<food>.json
"""
from __future__ import annotations

import json
import sys
import time
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[3]
for p in ("src", "scripts/worm"):
    sys.path.insert(0, str(ROOT / p))
import at_ledger  # noqa: E402

at_ledger.patch()
from wormemu import brain as B  # noqa: E402
from wormemu.interface import default_observation  # noqa: E402
from wormemu.mech import neuromod as N  # noqa: E402


def main():
    grid, food = sys.argv[1], float(sys.argv[2])
    secs = float(sys.argv[3]) if len(sys.argv) > 3 else 20.0
    t0 = time.time()
    b = B.Brain(B.sample_worm(None), toggles={"pc_grid": grid})
    nm = next(m for m in b.mechs if type(m).__module__ == "wormemu.mech.neuromod")
    egg = next((m for m in b.mechs if type(m).__module__ == "wormemu.mech.organs_egglaying"), None)
    b.reset()
    t1 = time.time()
    s5, n40 = N.AMINES.index("serotonin"), N.PRECURSORS.index("nlp-40")
    ix = {c: b.idx[c] for c in ("HSNL", "NSML", "MCL", "DVB", "AVL")}
    keys = ["head", "vulva_organ", "vulva_bin", "read_HSNL", "read_NSML", "read_MCL", "MC_gs", "total_5ht",
            "max_5ht_bin", "nlp40_DVB", "nlp40_AVL", "DVB_gs", "AVL_gs"]
    rec = {k: [] for k in ["t"] + keys}
    pumps = eggs = 0
    for k in range(int(round(secs * 1000))):
        obs = default_observation(b.t)
        obs.head["food_OD"] = food
        o = b.step(obs, 1.0)
        pumps += int(o.pumps)
        eggs += int(o.eggs_laid)
        if k % 100 == 99:
            c = nm.ma.nM()[s5]
            rec["t"].append((k + 1) / 1000.0)
            rec["head"].append(float(nm.ma.named_nM()[s5, 0]))
            rec["vulva_organ"].append(float(egg.concentrations()[0]) if egg else float("nan"))
            rec["vulva_bin"].append(float(c[nm.ma_comp[ix["HSNL"]]]))
            for n in ("HSNL", "NSML", "MCL"):
                rec[f"read_{n}"].append(nm.cell_nM(N.A, "serotonin", ix[n]))
            rec["MC_gs"].append(float(nm.G[ix["MCL"], 2]))
            rec["total_5ht"].append(float(nm.ma.N[s5].sum()))
            rec["max_5ht_bin"].append(float(c.max()))
            rec["nlp40_DVB"].append(nm.cell_nM(N.P, "nlp-40", ix["DVB"]))
            rec["nlp40_AVL"].append(nm.cell_nM(N.P, "nlp-40", ix["AVL"]))
            rec["DVB_gs"].append(float(nm.G[ix["DVB"], 2]))
            rec["AVL_gs"].append(float(nm.G[ix["AVL"], 2]))
    s = {k: dict(max=float(np.max(v)), end=float(v[-1]), mean=float(np.mean(v))) for k, v in rec.items() if k != "t"}
    res = dict(grid=grid, food_OD=food, bio_s=secs, n_bins=int(nm.ma.N.shape[1]), build_s=t1 - t0,
               step_wall_s=time.time() - t1, pumps=pumps, eggs=eggs, summary=s, trace=rec)
    (ROOT / f"runs/worm/wneuro/grid_live_{grid}_{food}.json").write_text(json.dumps(res, default=float))
    print(json.dumps(dict(grid=grid, food=food, build_s=round(t1 - t0, 1), step_wall_s=round(res["step_wall_s"], 1),
                          pumps=pumps, eggs=eggs, **{k: round(v["mean"], 4) for k, v in s.items()})))


if __name__ == "__main__":
    main()
