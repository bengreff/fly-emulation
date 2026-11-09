"""wneuro item 4, line 13 (written Sun 8 Nov 2026 23:12 CST, before running): does line 13's D proof stand under the
corrected GABA bar? Never adopted.

The triage's probe (scripts/worm/triage/probes.py gaba, wtriage) scored 256 Sobol points over the 8 guessed stp_gaba
gaps against "plateaus > 0.8 at 1 and 5 Hz, 20 Hz second/first > 1" and found 24 passes (9%). The bar is corrected
(class E, stp_unit_check.gaba_score, Liu et al. 2009 PMC2705609): plateaus 0.8-1 at 1 and 5 Hz (no facilitation
reported there) and second/first > 1 at 10 and 20 Hz. This re-runs the same design (same ids, bio box, 256 points,
Sobol seed 0) with the corrected score. The triage counted passes without the joint-constraint filter; both counts
are reported, and the verdict uses the filtered one (a point that breaks a hard joint constraint is not a fly). The D
proof stands if at least one filtered point passes the corrected bar; if none does, line 13 is not D and is reported
as such.

Usage: python probe_gaba.py [--workers=W] -> runs/worm/wneuro/probe_gaba.json
"""
from __future__ import annotations

import json
import sys
import time
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[3]
for p in ("src", "scripts/worm", "scripts/worm/triage"):
    sys.path.insert(0, str(ROOT / p))
from probe_lib import Box, joint_bad  # noqa: E402
from probes import GABA_IDS, _pool  # noqa: E402


def point(x):
    import at_ledger
    at_ledger.patch()
    sys.argv = ["stp"]
    import stp_unit_check as S
    S.T.update(dict(zip(GABA_IDS, map(float, x))))
    g = {}
    for hz in (1.0, 5.0, 10.0, 20.0):
        v, per = S.F.train(hz)
        a = S.per_pulse(S.run(v, "gabacl"), per)
        g[hz] = a / a[0]
    return S.gaba_score(g)


def main():
    workers = int(next((a.split("=")[1] for a in sys.argv[1:] if a.startswith("--workers=")), 1))
    t0 = time.time()
    box = Box(GABA_IDS)
    X = box.design(256, which="bio", seed=0)
    rows = _pool(point, X, workers)
    jb = np.array([len(joint_bad(dict(zip(GABA_IDS, x)))) for x in X])
    new_raw = np.array([r["passed"] for r in rows])
    old_raw = np.array([r["old_bar_passed"] for r in rows])
    new, old = new_raw & (jb == 0), old_raw & (jb == 0)
    best = [dict(x=dict(zip(GABA_IDS, map(float, X[k]))), edges=box.at_edge(X[k], which="bio"), **rows[k])
            for k in np.flatnonzero(new)]
    res = dict(n=len(X), n_pass_old_bar_raw=int(old_raw.sum()), n_pass_new_bar_raw=int(new_raw.sum()),
               n_pass_old_bar=int(old.sum()), n_pass_new_bar=int(new.sum()), n_joint_bad=int((jb > 0).sum()),
               d_proof_stands=bool(new.any()), wall_s=time.time() - t0, passes=best,
               old_only=[dict(p1=rows[k]["plateau_1Hz"], p5=rows[k]["plateau_5Hz"], r10=rows[k]["second_over_first_10Hz"],
                              r20=rows[k]["second_over_first_20Hz"]) for k in np.flatnonzero(old & ~new)])
    (ROOT / "runs/worm/wneuro/probe_gaba.json").write_text(json.dumps(res, indent=1, default=float))
    print(json.dumps({k: v for k, v in res.items() if k not in ("passes", "old_only")}, indent=1))
    print("first passes", json.dumps(best[:3], default=float))


if __name__ == "__main__":
    main()
