"""wneuro item 6 helper (written Sun 8 Nov 2026 about 23:47 CST): each amine release cell's mean drive q, release factor R
and store over SECONDS of the template worm at the ledger values (all 302 neurons, default toggles), food_OD 0 or
1.02. A recording for probe_amine.py's fixed drive; no bar.

Usage: python release_drive.py [SECONDS] [food=F] -> runs/worm/wneuro/release_drive_food<F>.json
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[3]
for p in ("src", "scripts/worm"):
    sys.path.insert(0, str(ROOT / p))
import at_ledger  # noqa: E402

at_ledger.patch()
from wormemu import brain as B  # noqa: E402
from wormemu.interface import default_observation  # noqa: E402


def main():
    secs = float(sys.argv[1]) if len(sys.argv) > 1 and "=" not in sys.argv[1] else 20.0
    food = float(next((a.split("=")[1] for a in sys.argv[1:] if a.startswith("food=")), "1.02"))
    b = B.Brain(B.sample_worm(None))
    nm = next(m for m in b.mechs if type(m).__module__ == "wormemu.mech.neuromod")
    b.reset()
    rel = np.flatnonzero(nm.ma_rel.sum(1) > 0)
    q, R, S, n = np.zeros(len(rel)), np.zeros(len(rel)), np.zeros(len(rel)), 0
    for k in range(int(round(secs * 1000))):
        obs = default_observation(b.t)
        obs.head["food_OD"] = food
        b.step(obs, 1.0)
        q += nm.q_ma[rel]
        R += nm.release_factor()[rel]
        S += (nm.store[rel] * nm.ma_rel[rel]).sum(1)
        n += 1
    res = {nm.names[c]: dict(q_mean=q[i] / n, R_mean=R[i] / n, store_mean=S[i] / n) for i, c in enumerate(rel)}
    (ROOT / f"runs/worm/wneuro/release_drive_food{food:g}.json").write_text(json.dumps(res, indent=1))
    for k, v in res.items():
        print(k, {a: round(x, 4) for a, x in v.items()})


if __name__ == "__main__":
    main()
