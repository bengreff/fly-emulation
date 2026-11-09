"""Probe (wbrain2, 8 Nov 2026): does the model's evoked NMJ ACh current repeat line 3's composite-as-component bug?

rec_lacr_tau_off_ms and rec_acr16_tau_off_ms (6.5 ms, inferred) come from the evoked NMJ EPSC decay, 5.6 ms
(electrical) to 7.4 ms (light) in Richmond and Jorgensen 1999, a composite of release and closing. This runs the same
2 ms presynaptic step as receptor_unit_check's IPSC (BAAIWorm's graded release state, then the receptor) for each
class alone and reports the composite decay. A probe only: nothing is changed here.

Usage: PYTHONPATH=src .venv/bin/python scripts/worm/debug2/probe_ach_epsc.py [--ledger]
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
if "--ledger" in sys.argv:
    import at_ledger
    at_ledger.patch(["receptors"])
import receptor_unit_check as RU  # noqa: E402

out = {}
for c in ("lacr", "acr16"):
    t, i = RU.run(c, [(50, 52, 50.0)], 400)
    out[c] = {"composite_tau_ms": round(RU.decay_tau(t, i, 50, 400)[0], 2)}
    t, i = RU.run(c, [(50, 52, 50.0)], 400, extra={"tau_off": 0.5})
    out[c]["composite_at_tau_off_0.5_ms"] = round(RU.decay_tau(t, i, 50, 400)[0], 2)
out["bar"] = "5.6-7.4 ms (Richmond and Jorgensen 1999, electrical and light)"
print(json.dumps(out, indent=1))
