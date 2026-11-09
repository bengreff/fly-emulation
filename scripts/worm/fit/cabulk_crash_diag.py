"""Which matured cell stops cabulk.mod's solver (weki, 9 Nov 2026; for wbrain2). One cell alone, as ephys_score builds
it, with the bulk pool on (ca_bulk cadifpmp) and maturation's multiplier s frozen on its regulated channels, through
FIT2's six training sweeps; stops at the first sweep that raises.

Measured 9 Nov 00:24-00:27 on 1198812 (Mac): AIY s 0.627 stops at +35 pA ("scopmath library error: Convergence not
achieved", cabulk.mod BREAKPOINT); its +25 pA sweep peaks at +55 mV. AFD s 0.358 and AWA s 4.0 run all six. The default
(s 1) runs with the pool on in maturation_ephys.py's default arm.

Usage: python scripts/worm/fit/cabulk_crash_diag.py FEATURES.npz CLASS S     (one process per cell)
"""
import sys, json, numpy as np
from pathlib import Path
ROOT = Path(__file__).resolve().parents[3]
sys.path[:0] = [str(ROOT / "scripts/worm/triage"), str(ROOT / "scripts/worm"), str(ROOT / "src")]
cls, s = sys.argv[2], float(sys.argv[3])
sys.argv = sys.argv[:2]                               # ephys_score reads its features path from argv
import ephys_score as E
from wormemu.fit import maturation as MT
S, fit2 = E.S, E.fit2
br = S.build(cells=[fit2.CELL[cls]], extra={"ca_bulk": "cadifpmp"})
br.mechs.append(MT.Frozen(1, np.array([0]), np.array([s])))
amps = fit2.AMPS_PA[fit2.FIT2_SWEEPS]
out = {"cell": cls, "s": s, "sweeps": []}
for a in amps:
    try:
        V = fit2.simulate(br, np.array([a]))
        out["sweeps"].append({"pA": float(a), "ok": True, "v_max": float(np.nanmax(V)), "v_min": float(np.nanmin(V))})
    except RuntimeError as e:
        out["sweeps"].append({"pA": float(a), "ok": False, "err": str(e)[:80]})
        break
print(json.dumps(out))
