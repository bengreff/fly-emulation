"""One point of the line-vi probe (wtriage, 8 Nov 2026): can HSN's 5-HT reach the vulval muscles' SER-7 EC50?

The row 15 brain (check_egglaying.CELLS: HSNL/R, VC01-06; every module at the ledger values, default toggles), both
HSNs held depolarised by a step of current from 2 s to the end (a test input, so HSN's silence, line 5, is taken out
of the question), dt 5 ms. Recorded every 50 ms: the vulval 5-HT the egg module reads (organs_egglaying
concentrations(), nM), its SER-1/SER-7 occupancy (mech_out egg_5ht_occ), HSN's mean voltage and amine drive q, and
HSN's store. Nothing scored here: probe_5ht.py scores.

Usage: python hsn_5ht_point.py OUT.json [INJECT_PA] [SECONDS]
"""
from __future__ import annotations

import json
import sys
import time
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "scripts" / "worm"))
sys.path.insert(0, str(ROOT / "scripts" / "worm" / "organs"))
import at_ledger  # noqa: E402

at_ledger.patch()
import check_egglaying as CE  # noqa: E402
from wormemu import brain as B  # noqa: E402
from wormemu.mech import neuromod as nmod  # noqa: E402

ON_MS = 2000.0


def main():
    out_p = Path(sys.argv[1])
    inj = float(sys.argv[2]) if len(sys.argv) > 2 else 40.0
    secs = float(sys.argv[3]) if len(sys.argv) > 3 else 62.0
    b = B.Brain(B.sample_worm(None), toggles={}, cells=CE.CELLS)
    b.reset()
    eg = next(x for x in b.mechs if type(x).__module__.endswith("organs_egglaying"))
    nm = next(x for x in b.mechs if isinstance(x, nmod.Mech))
    hsn = [b.idx["HSNL"], b.idx["HSNR"]]
    n = int(round(secs * 1000 / CE.DT))
    t, c5, occ, v, q, st = [], [], [], [], [], []
    t0 = time.time()
    for k in range(n):
        tm = k * CE.DT
        b.extra_pA[:] = 0.0
        if tm >= ON_MS:
            b.extra_pA[hsn] = inj
        o = b.step(None, CE.DT)
        if k % 10 == 0:
            t.append(tm / 1000.0)
            c5.append(float(eg.concentrations()[0]))
            occ.append(float(b.mech_out["egg_5ht_occ"]))
            v.append(float(np.mean(o.v_mV[hsn])))
            q.append(float(np.mean(nm.q_ma[hsn])))
            s = nm.store[hsn]
            st.append(float(np.mean(s if s.ndim == 1 else s[:, 0])))
    res = dict(inject_pA=inj, seconds=secs, wall_s=time.time() - t0, t=t, c5_nM=c5, occ=occ, hsn_v=v, q=q, store=st,
               ec50_nM=eg.ec5.tolist(), comp_volume_um3=float(nm.ma.V[int(nm.ma_comp[hsn[0]])]),
               p_used={k_: float(v_) for k_, v_ in nm.p.items() if k_.startswith("ma_")})
    out_p.parent.mkdir(parents=True, exist_ok=True)
    out_p.write_text(json.dumps(res, default=float))
    on = np.array(t) >= ON_MS / 1000 + 1.0
    print(json.dumps(dict(inject_pA=inj, wall_s=res["wall_s"], c5_max=max(c5), occ_max=max(occ),
                          hsn_v_on=float(np.mean(np.array(v)[on])), q_on=float(np.mean(np.array(q)[on])),
                          store_end=st[-1])), flush=True)


if __name__ == "__main__":
    main()
