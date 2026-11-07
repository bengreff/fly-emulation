"""Ca pool units check (Director 22:08 check 2; bars in docs/worm/night/2026-11-06_wbrain.md, written before running):
AVAL in a 4-cell brain, soma clamped at -20 mV and 0 mV for 1 s, each ca_pool_units form; the Ca excess over caeq
against Nicoletti 2019 Eq. 28's steady state f I 1e6 tau_Ca / (2 F V_cell).

Usage: PYTHONPATH=src .venv/bin/python scripts/worm/capool_unit_check.py [out.json]
"""
from __future__ import annotations

import json
import sys

from wormemu.brain import Brain, sample_worm
from wormemu.mech import capool

CELLS = ["AVAL", "AVAR", "AWCL", "RIML"]
FARADAY = 96485.0


def clamp(form, v_hold, seconds=1.0):
    b = Brain(sample_worm(None), toggles={"ca_pool_units": form}, cells=CELLS)
    sec = b.soma[b.idx["AVAL"]]
    seg = sec(0.5)
    b.reset()
    c = b.h.SEClamp(seg)
    c.dur1, c.amp1, c.rs = 1e9, v_hold, 1e-3
    for _ in range(int(seconds * 1000)):
        b.step(None, 1.0)
    pool = seg.cainternm
    area = sum(s.area() for s in sec)
    vcell = pool.vcell * (capool.MA_CM2_TO_PA_UM2 * area if form != "off" else 1.0)   # the ledger's V_cell
    f, tca, caeq = b.h.f_cainternm, b.h.tca_cainternm, b.h.caeq_cainternm
    I = -seg.ica * (capool.MA_CM2_TO_PA_UM2 * area if form != "off" else 1.0)        # what Eq. 28 is fed
    want = f * I * 1e6 * tca / (2 * FARADAY * vcell)
    got = seg.cai - caeq
    c.dur1 = 0
    return dict(form=form, v_hold=v_hold, area_um2=area, ica_mA_cm2=seg.ica, I_whole_soma_pA=-seg.ica * 10 * area,
                cai_uM=seg.cai, excess_uM=got, closed_form_uM=want, rel_err=got / want - 1)


def main():
    res = {"runs": [clamp(f, v) for f in ("total_current", "off") for v in (-20.0, 0.0)]}
    res["passed"] = bool(all(abs(r["rel_err"]) < 0.01 for r in res["runs"]))
    print(json.dumps(res, indent=1))
    if len(sys.argv) > 1:
        open(sys.argv[1], "w").write(json.dumps(res, indent=1))


if __name__ == "__main__":
    main()
