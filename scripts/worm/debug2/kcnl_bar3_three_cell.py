"""KCNL bar 3 on the three-cell build (AIY, AFD, AWA), the robustness run of "KCNL: the network's density or the
tuner's none" (docs/worm/night/2026-11-08_wbrain2.md; wbrain2, 9 Nov 2026). The three-cell build's median soma area
(267.2 um2) gives AIYL a pump scale within 2% of the full brain's, where the AIY+AFD build of kcnl_check.py does not
(pumps.Pump scales by the median over the built cells). Scores kcnl_density network, tuner, and tuner with
slo_ca_source tuner_gbar (the tuner's world). Run from the repo root.

  python scripts/worm/debug2/kcnl_bar3_three_cell.py FEATURES.npz OUT.json
"""
import json
import sys
from pathlib import Path

F, OUT = sys.argv[1], sys.argv[2]
sys.argv = [sys.argv[0], F]                              # ephys_score reads its features path from argv[1]
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "triage"))
import ephys_score as E  # noqa: E402

cls = ["AIY", "AFD", "AWA"]
net, tun = E.score({}, cls), E.score({"kcnl_density": "tuner"}, cls)
both = E.score({"kcnl_density": "tuner", "slo_ca_source": "tuner_gbar"}, cls)
r = {c: dict(network=net[c]["rmse_mV"], tuner=tun[c]["rmse_mV"], tuner_world=both[c]["rmse_mV"]) for c in cls}
r["aiy_baseline"] = dict(network=net["AIY"]["model"]["baseline"][0], tuner=tun["AIY"]["model"]["baseline"][0],
                         data=net["AIY"]["data"]["baseline"])
print(json.dumps(r))
Path(OUT).write_text(json.dumps(r, indent=1))
