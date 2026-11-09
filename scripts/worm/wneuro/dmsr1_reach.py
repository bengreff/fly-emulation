"""wneuro Open 5, part 2 (written Mon 9 Nov 2026 00:35 CST, before running): how far the DMSR-1 isoform toggle reaches
in the live template worm. Diagnostic, no adoption (class C; no source says which isoform any cell makes).

Method. The template worm at the ledger values (at_ledger.patch), all 302 neurons, default toggles except
dmsr1_isoform = ISO, food_OD 0, SECONDS of 1 ms steps. Every 100 ms: Gi (G[:, 1]) and V of every neuron and FLP-25 in
each compartment (nM). Run once per isoform (NEURON is one simulator per process); `compare` reads both.
Reported: per cell, mean Gi and mean V over the second half, under each setting; FLP-25 per compartment against
DMSR-1B's EC50 (0.6 pM) and A's (1.6 uM). Rule written before running: a cell "moves" if its mean Gi changes by more
than 0.1 or its mean V by more than 1 mV (both thresholds guessed).

Usage: python dmsr1_reach.py ISO [SECONDS] -> runs/worm/wneuro/dmsr1_reach_<ISO>.json; python dmsr1_reach.py compare
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
OUT = ROOT / "runs/worm/wneuro"


def run(iso, secs):
    import at_ledger
    at_ledger.patch()
    from wormemu import brain as B
    from wormemu.interface import default_observation
    from wormemu.mech import neuromod as N
    b = B.Brain(B.sample_worm(None), toggles={"dmsr1_isoform": iso})
    nm = next(m for m in b.mechs if type(m).__module__ == "wormemu.mech.neuromod")
    f25 = N.PRECURSORS.index("flp-25")
    b.reset()
    t0, GI, V, F = time.time(), [], [], []
    for k in range(int(round(secs * 1000))):
        obs = default_observation(b.t)
        obs.head["food_OD"] = 0.0
        o = b.step(obs, 1.0)
        if k % 100 == 99:
            GI.append(nm.G[:, 1].copy())
            V.append(np.asarray(o.v_mV)[:nm.n].copy())
            F.append(nm.pep.nM()[f25].copy())
    h = len(GI) // 2
    GI, V, F = np.array(GI), np.array(V), np.array(F)
    res = dict(iso=iso, bio_s=secs, names=list(nm.names[:nm.n]), neuron=[bool(x) for x in nm.neuron],
               gi_mean=GI[h:].mean(0).tolist(), v_mean=V[h:].mean(0).tolist(), flp25_mean_nM=F[h:].mean(0).tolist(),
               flp25_max_nM=F.max(0).tolist(), wall_s=time.time() - t0)
    (OUT / f"dmsr1_reach_{iso}.json").write_text(json.dumps(res, indent=1, default=float))
    print(iso, "wall", round(res["wall_s"]), "s; FLP-25 nM per compartment", np.round(F[h:].mean(0), 6))


def compare():
    a, b = (json.loads((OUT / f"dmsr1_reach_{i}.json").read_text()) for i in ("most_potent", "dmsr-1a"))
    dg = np.array(b["gi_mean"]) - np.array(a["gi_mean"])
    dv = np.array(b["v_mean"]) - np.array(a["v_mean"])
    names = a["names"]
    moved = [dict(cell=names[c], gi=[a["gi_mean"][c], b["gi_mean"][c]], v=[a["v_mean"][c], b["v_mean"][c]])
             for c in range(len(names)) if a["neuron"][c] and (abs(dg[c]) > 0.1 or abs(dv[c]) > 1.0)]
    res = dict(flp25_mean_nM=dict(most_potent=a["flp25_mean_nM"], dmsr_1a=b["flp25_mean_nM"]),
               ec50_nM=dict(B=6.022e-4, A=1596.0), n_moved=len(moved), moved=moved,
               max_abs_dgi=float(np.abs(dg).max()), max_abs_dv_mV=float(np.abs(dv).max()),
               top_dgi=[(names[c], float(dg[c])) for c in np.argsort(-np.abs(dg))[:10]],
               top_dv=[(names[c], float(dv[c])) for c in np.argsort(-np.abs(dv))[:10]])
    (OUT / "dmsr1_reach.json").write_text(json.dumps(res, indent=1, default=float))
    print(json.dumps({k: v for k, v in res.items() if k != "moved"}, indent=1, default=float))
    print("moved:", [(m["cell"], np.round(m["gi"], 3).tolist(), np.round(m["v"], 2).tolist()) for m in moved])


if __name__ == "__main__":
    if sys.argv[1] == "compare":
        compare()
    else:
        run(sys.argv[1], float(sys.argv[2]) if len(sys.argv) > 2 else 10.0)
