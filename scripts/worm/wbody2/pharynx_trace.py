"""Item 2 (wbody2, 8 Nov 2026): where does the pump chain stop? Diagnostic only, nothing tuned or adopted.

Brain only, as vital_signs.py (the template worm at the ledger values, default toggles, step(None), dt 1 ms; the
entire-worm loop gave the same 0 pumps). Records every 1 ms: the pharyngeal neurons' V, the marginal cells' V, pm4's
V, core Ca and activation, the pump count; lists the pharynx wiring organs_pharynx placed (MC -> marginal -> pm4).
Usage: python pharynx_trace.py [SECONDS] [toggle=value ...] [inject=MCL,MCR:40] [cells=pharynx] [food=OD]
  inject   a current step (pA) into the listed cells from 0.5 s (a diagnostic drive, never a model input);
           CELLS:PA:HZ:MS gives MS-ms pulses at HZ instead
  cells    pharynx = build only the pharyngeal neurons (and NSM, RIP) for speed; default the whole brain
  food     food_OD at the head (item 4, 8 Nov; default 0 = the open-loop observation). The entire-worm loop's mean
           on the lawn was 1.02 (measured, DEBUG_TRIAGE)
-> runs/worm/wbody2/pharynx_trace[_tag].npz/.json
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
import at_ledger  # noqa: E402

at_ledger.patch()
from wormemu import brain as B  # noqa: E402
from wormemu.interface import PHARYNX_MUSCLES, default_observation  # noqa: E402
from wormemu.mech import organs_pharynx as P  # noqa: E402

PN = ["MCL", "MCR", "M1", "M2L", "M2R", "M3L", "M3R", "M4", "M5", "I1L", "I1R", "I2L", "I2R", "I3", "I4", "I5", "I6",
      "MI", "NSML", "NSMR", "RIPL", "RIPR"]


def main():
    secs = float(sys.argv[1]) if len(sys.argv) > 1 else 5.0
    tog = dict(a.split("=", 1) for a in sys.argv[2:])
    tag = "_".join(f"{k}-{v}" for k, v in tog.items()).replace(",", "+").replace(":", "@")
    inj = tog.pop("inject", None)
    food = float(tog.pop("food", 0.0))
    cells = PN if tog.pop("cells", None) == "pharynx" else None
    out = ROOT / "runs/worm/wbody2"
    out.mkdir(parents=True, exist_ok=True)
    b = B.Brain(B.sample_worm(None), toggles=tog, cells=cells)
    inj_idx, inj_pA, pulse = [], 0.0, None
    if inj:
        names, amp, *rest = inj.split(":")             # optional :HZ:MS = pulses of MS ms at HZ instead of a step
        inj_idx, inj_pA = [b.idx[n] for n in names.split(",")], float(amp)
        pulse = (float(rest[0]), float(rest[1])) if rest else None
    ph = next(m for m in b.mechs if isinstance(m, P.Mech))
    st, nm = b.st, b.st.names
    mine = set(ph.names)
    wiring = {"chem_in": [], "gap": []}
    for i, j, n in st.chem:
        if nm[j] in mine and nm[i] in b.idx:
            wiring["chem_in"].append([nm[i], nm[j], int(n), bool((nm[i] in P.M3) or b._inhibitory(nm[i], nm[j]))])
    for i, j, n in st.gap:
        if nm[i] in mine or nm[j] in mine:
            wiring["gap"].append([nm[i], nm[j], int(n)])
    pn = [n for n in PN if n in b.idx]
    h = b.h
    rec = {n: h.Vector().record(b.soma[b.idx[n]](0.5)._ref_v) for n in pn}
    for n in ph.names:
        rec["sec_" + n] = h.Vector().record(ph.sec[n](0.5)._ref_v)
    b.reset()
    nsteps = int(round(secs * 1000))
    a4, pumps, ma, cai = [], 0, [], []
    nsm_i = [b.idx[n] for n in ("NSML", "NSMR") if n in b.idx]
    t0 = time.time()
    for k in range(nsteps):
        b.extra_pA[:] = 0.0
        if inj_idx and k >= 500 and (pulse is None or (k - 500) % (1000.0 / pulse[0]) < pulse[1]):
            b.extra_pA[inj_idx] = inj_pA
        obs = default_observation(b.t)
        obs.head["food_OD"] = food
        o = b.step(obs, 1.0)
        pumps += int(o.pumps)
        a4.append(float(ph.act[P.METACORPUS].mean()) if ph.form == "sherman2024" else np.nan)
        if k % 10 == 0:
            ma.append(ph.serotonin_nM() if hasattr(ph, "serotonin_nM") else np.nan)
            cai.append(o.ca_uM[nsm_i].tolist() if (o.ca_uM is not None and nsm_i) else [np.nan])
    wall = time.time() - t0
    arr = {k: np.array(v) for k, v in rec.items()}
    n_rec = len(next(iter(arr.values())))
    res = dict(cells=len(b.idx), inject=inj, bio_s=secs, wall_s=wall, toggles=tog, pumps=pumps, n_syn=ph.n_syn, n_gap=ph.n_gap, form=ph.form,
               a4_max=float(np.nanmax(a4)), n_rec=n_rec, wiring=wiring,
               v_summary={k: dict(min=float(v.min()), median=float(np.median(v)), max=float(v.max()),
                                  frac_above_m20=float((v > -20).mean())) for k, v in arr.items()})
    cai = np.array(cai, float)
    res["food_OD"] = food
    res["nsm_ca_uM"] = dict(median=float(np.nanmedian(cai)), max=float(np.nanmax(cai)))
    res["pharynx_5ht_nM_trace_1s"] = [float(x) for x in ma[::100]]
    res["pharynx_5ht_nM"] = dict(max=float(np.nanmax(ma)), last=float(ma[-1]), source=(ph._ser or ["none"])[0])
    (out / f"pharynx_trace{'_' + tag if tag else ''}.json").write_text(json.dumps(res, indent=1))
    np.savez_compressed(out / f"pharynx_trace{'_' + tag if tag else ''}.npz", a4=np.array(a4), **arr)
    print(json.dumps({k: v for k, v in res.items() if k not in ("wiring", "v_summary")}), flush=True)


if __name__ == "__main__":
    main()
