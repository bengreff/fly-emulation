"""Bar 4 of "Inbox item 5, AFD's hyperpolarised branch" (docs/worm/night/2026-11-08_wbrain2.md; wbrain2, 9 Nov 2026):
embedded AFDL alone through wtriage's ephys_score.score (FIT2's training sweeps and 24 features), default and
afd_membrane naudin22. --diag adds a diagnostic of cause (not a bar, not adoption): Naudin's model with n22_C_pF at
our AFDL's 4.008 pF (267.2 um2 x 1.5 uF/cm2), which keeps the published whole-cell nS in our morphology.

  python scripts/worm/debug2/naudin22_afd_embed.py FEATURES.npz OUT.json [--diag]
"""
import dataclasses
import json
import sys
from pathlib import Path

FEATS, OUT, DIAG = sys.argv[1], sys.argv[2], "--diag" in sys.argv
sys.argv = [sys.argv[0], FEATS]                          # ephys_score reads its features path from argv[1]
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "triage"))
import ephys_score as E  # noqa: E402
from wormemu.mech import cell_models as M  # noqa: E402

res = {"default": E.score({}, ["AFD"])["AFD"], "naudin22": E.score({"afd_membrane": "naudin22"}, ["AFD"])["AFD"]}
if DIAG:
    i = [s.id for s in M.SPECS].index("n22_C_pF")
    M.SPECS[i] = dataclasses.replace(M.SPECS[i], template=4.008)
    res["naudin22_C4.008"] = E.score({"afd_membrane": "naudin22"}, ["AFD"])["AFD"]
for k, r in res.items():
    print(k, "rmse", round(r["rmse_mV"], 2), {n: r["model"][n] for n in ("steady", "after")})
res["bar4_pass"] = bool(abs(res["naudin22"]["model"]["steady"][0] - res["naudin22"]["data"]["steady"][0]) <= 3.0
                        and res["naudin22"]["rmse_mV"] <= 10.53)
Path(OUT).write_text(json.dumps(res, indent=1))
