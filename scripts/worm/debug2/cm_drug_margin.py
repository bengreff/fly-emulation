"""Is the specific-capacitance fill the whole cause of test_drugs_act_through_their_targets' levamisole margin?
(docs/worm/night/2026-11-08_wbrain2.md, "The specific capacitance from Goodman 1998"; wbrain2, 9 Nov 2026). Runs the
test's DRUG snippet, base and levamisole, at pas_cm_uF_cm2 1.5 (the value before the fill) and at the ledger's value.
Run from the repo root: python scripts/worm/debug2/cm_drug_margin.py OUT.json
"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "tests"))
import test_worm_datamodel as T  # noqa: E402

fast = lambda d, frac=1.0: {f"drug_{d}_uptake_tau_s": 30.0, f"drug_{d}_cuticle_frac": frac}  # noqa: E731
out = {}
for cm in (1.5, None):
    extra = {} if cm is None else {"pas_cm_uF_cm2": cm}
    base = T._run(T.DRUG.format(th=extra or None, dr=[]))
    lev = T._run(T.DRUG.format(th={**fast("levamisole"), **extra}, dr=[("levamisole", 1000.0, 0.0)]))
    out[str(cm)] = dict(base_v=base["v"], lev_v=lev["v"], dv=lev["v"] - base["v"],
                        lev_nS=lev["drugs"]["drug_levamisole_max_nS"], base_act=base["act"], lev_act=lev["act"])
    print(cm, out[str(cm)], flush=True)
Path(sys.argv[1]).write_text(json.dumps(out, indent=1))
