"""Item 3 (wbody2, 8 Nov 2026): where does the defecation motor program stop? Diagnostic only, nothing tuned.

Brain only at the ledger values, default toggles (as vital_signs.py). Every 10 ms: int9 and int1 Ca (the cells, not
the max over cells), the intestine's NLP-40 release, neuromod's nlp-40 concentration in AVL's and DVB's compartments,
AVL's and DVB's Gs and V, the enteric muscles' V, Ca and activation, expulsions; plus the cleft pH and PBO-5/6 open
fraction. Usage: python dmp_trace.py [SECONDS] [cells=dmp] [toggle=value ...]
  cells=dmp  build only AVL, DVB and their chemical/gap partners in Cook (faster); default the whole brain
-> runs/worm/wbody2/dmp_trace[_tag].json
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
sys.path.insert(0, str(ROOT / "scripts" / "worm" / "triage"))
import at_ledger  # noqa: E402

at_ledger.patch()
from vital_signs import peaks  # noqa: E402
from wormemu import brain as B  # noqa: E402
from wormemu.interface import ENTERIC_MUSCLES  # noqa: E402
from wormemu.mech import neuromod as nmod  # noqa: E402
from wormemu.mech import organs_intestine as I  # noqa: E402

DMP = ["AVL", "DVB", "PVR", "AVAL", "AVAR", "PHAL", "PHAR", "PDA", "DA09", "VA12", "LUAL", "LUAR", "PVCL", "PVCR"]


def main():
    secs = float(sys.argv[1]) if len(sys.argv) > 1 else 120.0
    tog = dict(a.split("=", 1) for a in sys.argv[2:])
    tag = "_".join(f"{k}-{v}" for k, v in tog.items())
    cells = DMP if tog.pop("cells", None) == "dmp" else None
    b = B.Brain(B.sample_worm(None), toggles=tog, cells=cells)
    gut = next(m for m in b.mechs if isinstance(m, I.Mech))
    nm = next((m for m in b.mechs if isinstance(m, nmod.Mech)), None)
    i9 = [I.INT_CELLS.index(n) for n in ("int9L", "int9R")]
    i1 = [I.INT_CELLS.index(n) for n in ("int1DL", "int1DR", "int1VL", "int1VR")]
    who = [n for n in ("AVL", "DVB") if n in b.idx]
    row = nmod.PRECURSORS.index("nlp-40") if nm is not None and "nlp-40" in nmod.PRECURSORS else None
    b.reset()
    rec = {k: [] for k in ("t", "int9", "int1", "nlp40_local_nM", "cleft_pH", "pbo5_open", "exp_total")}
    for n in who:
        rec[f"{n}_v"], rec[f"{n}_gs"], rec[f"{n}_nlp40_nM"] = [], [], []
    for n in ENTERIC_MUSCLES:
        rec[f"{n}_v"], rec[f"{n}_ca_mM"], rec[f"{n}_act"] = [], [], []
    vmax = {n: -1e9 for n in who + list(ENTERIC_MUSCLES)}
    exps, t0 = 0, time.time()
    for k in range(int(secs * 1000)):
        o = b.step(None, 1.0)
        exps += int(o.expulsions)
        mo = b.mech_out
        for n in who:
            vmax[n] = max(vmax[n], float(o.v_mV[b.idx[n]]))
        ev = mo.get("enteric_v_mV")
        if ev is not None:
            for x, n in enumerate(ENTERIC_MUSCLES):
                vmax[n] = max(vmax[n], float(ev[x]))
        if k % 10:
            continue
        c = mo.get("intestine_ca_uM")
        rec["t"].append(k / 1000.0)
        rec["int9"].append(float(np.mean(c[i9])))
        rec["int1"].append(float(np.mean(c[i1])))
        rec["nlp40_local_nM"].append(float(mo.get("nlp40_nM", np.nan)))
        rec["cleft_pH"].append(float(mo.get("cleft_pH", np.nan)))
        rec["pbo5_open"].append(float(mo.get("pbo5_open", np.nan)))
        rec["exp_total"].append(exps)
        cpool = nm.pep.nM() if (nm is not None and row is not None and nm.on.get(nmod.P)) else None
        for n in who:
            j = b.idx[n]
            rec[f"{n}_v"].append(float(o.v_mV[j]))
            rec[f"{n}_gs"].append(float(nm.G[j, 2]) if nm is not None else np.nan)
            rec[f"{n}_nlp40_nM"].append(float(cpool[row, nm.pep_comp[j]]) if cpool is not None else np.nan)
        ca, act = mo.get("enteric_ca_mM"), mo.get("enteric_activation")
        for x, n in enumerate(ENTERIC_MUSCLES):
            rec[f"{n}_v"].append(float(ev[x]) if ev is not None else np.nan)
            rec[f"{n}_ca_mM"].append(float(ca[x]) if ca is not None else np.nan)
            rec[f"{n}_act"].append(float(act[x]) if act is not None else np.nan)
    t = np.array(rec["t"])
    summ = {k: dict(min=float(np.nanmin(v)), median=float(np.nanmedian(v)), max=float(np.nanmax(v)))
            for k, v in rec.items() if k != "t" and np.isfinite(np.asarray(v, float)).any()}
    res = dict(bio_s=secs, wall_s=time.time() - t0, cells=len(b.idx), toggles=tog, expulsions=exps,
               int9_peaks_s=peaks(t, np.array(rec["int9"]), 0.3, 10.0),
               int1_peaks_s=peaks(t, np.array(rec["int1"]), 0.3, 10.0),
               v_max_per_ms=vmax, summary=summ, trace={k: v[::10] for k, v in rec.items()})
    out = ROOT / f"runs/worm/wbody2/dmp_trace{'_' + tag if tag else ''}.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(res, indent=1, default=float))
    print(json.dumps({k: v for k, v in res.items() if k != "trace"}, indent=1, default=float))


if __name__ == "__main__":
    main()
