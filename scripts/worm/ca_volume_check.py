"""Row 6 check (bars in docs/worm/night/2026-11-06_wneuron.md, written before running): mech/ca_volume.
(a) each fitted cell's whole-cell volume in the BAAIWorm morphology against Nicoletti's NeuroMorpho volume;
(b) Nicoletti 2019 Eq. 28's steady state per cell with the pool sized by the form's volume (soma clamped at 0 mV).

Usage: PYTHONPATH=src .venv/bin/python scripts/worm/ca_volume_check.py [out.json]
Each form runs in its own subprocess (one NEURON per process).
"""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
CELLS = ["AIYL", "RIML", "AVAL", "AVAR", "VA05", "VB06", "VD05", "AWCL"]
# Nicoletti et al. 2024 PLoS ONE 19:e0298105 (NeuroMorpho whole-cell volumes, um3, in their fitted cells' scripts);
# AWC: Nicoletti et al. 2019 PLoS ONE 14:e0218738 (the ledger's capool_vcell). Check data only, not used by the model.
NICOLETTI_UM3 = {"AIYL": 7.42, "RIML": 10.94, "AVAL": 129.6, "AVAR": 129.08, "VA05": 48.07, "VB06": 58.54,
                 "VD05": 51.3, "AWCL": 31.16}
FARADAY = 96485.0
CHILD = """
import json, sys
from wormemu.brain import Brain, sample_worm
from wormemu.mech import ca_volume, capool
form, cells = sys.argv[1], json.loads(sys.argv[2])
b = Brain(sample_worm(None), toggles={"ca_pool_volume": form}, cells=cells)
b.reset()
clamps = []
for c in cells:
    cl = b.h.SEClamp(b.soma[b.idx[c]](0.5))
    cl.dur1, cl.amp1, cl.rs = 1e9, 0.0, 1e-3
    clamps.append(cl)
for _ in range(1000):
    b.step(None, 1.0)
f, tca, caeq = b.h.f_cainternm, b.h.tca_cainternm, b.h.caeq_cainternm
out = {}
for c in cells:
    i = b.idx[c]
    seg = b.soma[i](0.5)
    area = sum(s.area() for s in b.soma[i])
    whole, soma = ca_volume.volumes(b, i)
    out[c] = dict(whole_um3=whole, soma_um3=soma, soma_area_um2=area, cai_uM=seg.cai, excess_uM=seg.cai - caeq,
                  I_pA=-seg.ica * capool.MA_CM2_TO_PA_UM2 * area,
                  v_eff_um3=seg.cainternm.vcell * capool.MA_CM2_TO_PA_UM2 * area, f=f, tca=tca, caeq=caeq)
print(json.dumps(out))
"""


def run(form):
    r = subprocess.run([sys.executable, "-c", CHILD, form, json.dumps(CELLS)], capture_output=True, text=True,
                       cwd=ROOT, env={**__import__("os").environ, "PYTHONPATH": str(ROOT / "src")}, timeout=1800)
    assert r.returncode == 0, r.stderr[-3000:]
    return json.loads(r.stdout.strip().splitlines()[-1])


def main():
    res = {"forms": {f: run(f) for f in ("whole_cell", "soma", "fixed")}}
    w = res["forms"]["whole_cell"]
    res["a"] = {c: dict(baaiworm_um3=w[c]["whole_um3"], nicoletti_um3=NICOLETTI_UM3[c],
                        ratio=w[c]["whole_um3"] / NICOLETTI_UM3[c], soma_um3=w[c]["soma_um3"]) for c in CELLS}
    res["a_passed"] = bool(all(0.5 <= x["ratio"] <= 2.0 for x in res["a"].values()))
    b = {}
    for form, want_v in (("whole_cell", "whole_um3"), ("soma", "soma_um3")):
        for c, x in res["forms"][form].items():
            closed = x["f"] * x["I_pA"] * 1e6 * x["tca"] / (2 * FARADAY * x[want_v])
            b[f"{form}:{c}"] = dict(v_eff_um3=x["v_eff_um3"], v_want_um3=x[want_v], I_pA=x["I_pA"],
                                    excess_uM=x["excess_uM"], closed_form_uM=closed,
                                    rel_err=x["excess_uM"] / closed - 1)
    res["b"] = b
    res["b_passed"] = bool(all(abs(x["rel_err"]) < 0.01 for x in b.values()))
    res["fixed_excess_uM"] = {c: x["excess_uM"] for c, x in res["forms"]["fixed"].items()}
    print(json.dumps({k: res[k] for k in ("a", "a_passed", "b_passed", "fixed_excess_uM")}, indent=1))
    print(json.dumps({k: (round(v["rel_err"], 5), round(v["excess_uM"], 4)) for k, v in b.items()}))
    out = Path(sys.argv[1]) if len(sys.argv) > 1 else ROOT / "runs/worm/night_wneuron/ca_volume_check.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(res, indent=1))


if __name__ == "__main__":
    main()
