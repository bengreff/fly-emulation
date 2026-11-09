"""Reported effects of the specific-capacitance fill (docs/worm/night/2026-11-08_wbrain2.md, "The specific capacitance
from Goodman 1998", written before this ran; wbrain2, 9 Nov 2026): FIT2 training RMSE of AIY, AFD and AWA on the
three-cell build, and AVAL's input resistance at -10 pA alone. Run once before and once after the ledger fill.

  python scripts/worm/debug2/cm_effects.py FEATURES.npz OUT.json
"""
import json
import sys
from pathlib import Path

F, OUT = sys.argv[1], sys.argv[2]
sys.argv = [sys.argv[0], F]                              # ephys_score reads its features path from argv[1]
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "triage"))
import ephys_score as E  # noqa: E402

cls = ["AIY", "AFD", "AWA"]
s = E.score({}, cls)
r = {c: dict(rmse_mV=s[c]["rmse_mV"], baseline_model=s[c]["model"]["baseline"][0],
             baseline_data=s[c]["data"]["baseline"]) for c in cls}
b = E.S.build(cells=["AVAL"])
cm = sorted({round(float(x.cm), 9) for x in b.cells[0].all})
b.reset()
b.extra_pA[:] = 0.0
for _ in range(2000):
    v0 = float(b.step(None, 1.0).v_mV[0])
b.extra_pA[:] = -10.0
for _ in range(2000):
    v1 = float(b.step(None, 1.0).v_mV[0])
r["AVAL"] = dict(cm=cm, v_rest_mV=v0, v_step_mV=v1, rin_GOhm=(v0 - v1) / 10.0)
print(json.dumps(r))
Path(OUT).write_text(json.dumps(r, indent=1))
