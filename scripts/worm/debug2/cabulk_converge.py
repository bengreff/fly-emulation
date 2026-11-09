"""Probe and bars of "cabulk.mod stops a matured AIY" (docs/worm/night/2026-11-08_wbrain2.md, written before this ran;
wbrain2, 9 Nov 2026). weki's build (scripts/worm/fit/cabulk_crash_diag.py: one cell, `ca_bulk cadifpmp`, maturation's
multiplier s frozen) through FIT2's six sweeps, recording the soma's v, ica and cabulk's ca[0] and cab every 1 ms;
stops at the first sweep that raises. One process per cell; run from the repo root.

  python scripts/worm/debug2/cabulk_converge.py FEATURES.npz CLASS S OUT.npz
  python scripts/worm/debug2/cabulk_converge.py compare OLD.npz NEW.npz     # bar 2 on one pair
"""
import json
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[3]


def probe(cls, s, out):
    sys.path[:0] = [str(ROOT / "scripts/worm/triage"), str(ROOT / "scripts/worm"), str(ROOT / "src")]
    import ephys_score as E
    from wormemu.fit import maturation as MT
    S, fit2 = E.S, E.fit2
    br = S.build(cells=[fit2.CELL[cls]], extra={"ca_bulk": "cadifpmp"})
    br.mechs.append(MT.Frozen(1, np.array([0]), np.array([s])))
    seg = br.soma[0](0.5)
    amps = fit2.AMPS_PA[fit2.FIT2_SWEEPS]
    rec = {k: np.full((len(amps), fit2.T_END), np.nan) for k in ("V", "v", "ica", "cabmem", "cab")}
    ok, err = [], ""
    for i, a in enumerate(amps):
        br.reset()
        br.extra_pA[:] = 0.0
        try:
            for _ in range(fit2.T_SETTLE):
                br.step(None, 1.0)
            for k in range(fit2.T_END):
                br.extra_pA[:] = a if fit2.T_ON <= k < fit2.T_OFF else 0.0
                rec["V"][i, k] = br.step(None, 1.0).v_mV[0]
                rec["v"][i, k], rec["ica"][i, k] = seg.v, seg.ica
                rec["cabmem"][i, k], rec["cab"][i, k] = seg.cabulk.cabmem, seg.cabulk.cab
            ok.append(True)
        except RuntimeError as e:
            ok.append(False)
            err = str(e)[:120]
            break
    np.savez(out, amps=amps, ok=np.array(ok), **rec)
    summ = {"cell": cls, "s": s, "ok": ok, "err": err, "sweeps": []}
    for i in range(len(ok)):
        r = {x: rec[x][i] for x in rec}
        last = int(np.flatnonzero(np.isfinite(r["V"]))[-1]) if np.isfinite(r["V"]).any() else -1
        out_ms = int((r["ica"][: last + 1] > 0).sum())
        summ["sweeps"].append(dict(pA=float(amps[i]), ok=ok[i], last_ms=last, v_max=float(np.nanmax(r["v"])),
                                   ms_v_above_60=int((r["v"][: last + 1] > 60).sum()), ms_ica_outward=out_ms,
                                   ica_max=float(np.nanmax(r["ica"])), cabmem_min_uM=float(np.nanmin(r["cabmem"])),
                                   cab_max_uM=float(np.nanmax(r["cab"]))))
        if not ok[i]:
            w = slice(max(0, last - 9), last + 1)
            summ["sweeps"][-1]["tail"] = {x: [float(y) for y in r[x][w]] for x in ("v", "ica", "cabmem")}
    print(json.dumps(summ))
    Path(str(out).replace(".npz", ".json")).write_text(json.dumps(summ, indent=1))


def compare(a, b):
    A, B = np.load(a), np.load(b)
    n = int(min(A["ok"].size, B["ok"].size))
    res = {"sweeps": []}
    for i in range(n):
        f = np.isfinite(A["V"][i]) & np.isfinite(B["V"][i])
        out_old = bool((A["ica"][i][f] > 0).any())
        res["sweeps"].append(dict(pA=float(A["amps"][i]), old_ok=bool(A["ok"][i]), new_ok=bool(B["ok"][i]),
                                  max_abs_dV_mV=float(np.abs(A["V"][i][f] - B["V"][i][f]).max()),
                                  max_abs_dcab_uM=float(np.abs(A["cab"][i][f] - B["cab"][i][f]).max()),
                                  ica_outward_ms=int((A["ica"][i][f] > 0).sum()), ica_ever_outward=out_old))
    res["new_all_ok"] = bool(B["ok"].all() and B["ok"].size == 6)
    print(json.dumps(res))
    return res


if __name__ == "__main__":
    if sys.argv[1] == "compare":
        compare(sys.argv[2], sys.argv[3])
    else:
        feats, cls, s, out = sys.argv[1], sys.argv[2], float(sys.argv[3]), sys.argv[4]
        sys.argv = sys.argv[:2]                              # ephys_score reads its features path from argv[1]
        probe(cls, s, out)
