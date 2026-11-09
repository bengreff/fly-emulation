"""pumps.py rest reference at zero input (wbody2, 9 Nov 2026; follow-up of item 8's glia_v0_probe).

pumps.py loads each cell's [Na]i with g_Na (V - V0)^+, V0 the cell's mean over the first pump_v0_ms (1 s). The
glia probe (23:27) found the network drifting 3 mV (median) off its 0-1 s mean, which holds the start-up from V_INIT
-65 mV, so the rectified term may load Na+ at zero input. Brain: check_glia's 44 cells (default toggles, dt 5 ms),
no input, 22 s. Recorded: every cell's V, [Na]i and injected pump current.

Measures, per cell, over 2-22 s: the false load g_Na (V - V0)^+ with V0 = the module's (0-1 s mean) and, derived
from the same V trace, with V0 = the 1-2 s mean (what a settled window would give; not run through the module);
each as a fraction of check_pumps' drive load, g_Na x 20 mV (the row-27 check's 20 mV step).
Verdict rule (written before running): A in my module if the median cell's false load under the 0-1 s reference
is >= 10 % of the drive load and the 1-2 s reference brings it under 10 %; none if it is already under 10 %;
B (the network's drift) if both are >= 10 %. The 10 % tolerance is guessed. Reported, not barred: [Na]i rise and
injected pump current at 22 s.

Usage: PYTHONPATH=src .venv/bin/python scripts/worm/wbody2/pump_v0_probe.py OUT.json
"""
import importlib.util
import json
import sys
import time
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "src"))
_sp = importlib.util.spec_from_file_location("check_glia", ROOT / "scripts/worm/organs/check_glia.py")
cg = importlib.util.module_from_spec(_sp)
_sp.loader.exec_module(cg)

from wormemu.brain import Brain  # noqa: E402
from wormemu.mech import pumps as pu  # noqa: E402

T_END = 22000.0


def main():
    out = Path(sys.argv[1])
    b = Brain(cells=cg.CELLS)
    b.reset()
    m = next(x for x in b.mechs if isinstance(x, pu.Mech))
    w0, t, V, NA, I = time.time(), [], [], [], []
    while b.t < T_END:
        o = b.step(None, cg.DT)
        t.append(b.t)
        V.append(np.asarray(o.v_mV, float).copy())
        NA.append(b.mech_out["na_i_mM"].copy())
        I.append(np.asarray(b.mech_out["pump_current_pA"], float).copy())
    t, V, NA, I = map(np.array, (t, V, NA, I))
    gna = m.pump.gna
    v_first = m.v0
    v_settled = V[(t > 1000.0) & (t <= 2000.0)].mean(axis=0)
    w = t > 2000.0
    drive = gna * 20.0
    f_first = (gna * np.maximum(V[w] - v_first, 0.0)).mean(axis=0) / drive
    f_settled = (gna * np.maximum(V[w] - v_settled, 0.0)).mean(axis=0) / drive
    a, s = float(np.median(f_first)), float(np.median(f_settled))
    verdict = "none" if a < 0.1 else ("A" if s < 0.1 else "B")
    names = b.cell_names
    res = {"median_false_load_first": a, "median_false_load_settled": s, "verdict": verdict,
           "p90_false_load_first": float(np.percentile(f_first, 90)),
           "p90_false_load_settled": float(np.percentile(f_settled, 90)),
           "median_abs_v0_shift_mV": float(np.median(np.abs(v_settled - v_first))),
           "na_rise_22s_mM": {"median": float(np.median(NA[-1] - NA[0])), "max": float((NA[-1] - NA[0]).max())},
           "pump_I_22s_pA": {"median": float(np.median(I[-1])), "min": float(I[-1].min()), "max": float(I[-1].max())},
           "per_cell": {n: {"first": float(f_first[i]), "settled": float(f_settled[i]),
                            "na_rise_mM": float(NA[-1, i] - NA[0, i]), "I_22s_pA": float(I[-1, i]),
                            "v0_first": float(v_first[i]), "v0_settled": float(v_settled[i])}
                        for i, n in enumerate(names)},
           "wall_s": time.time() - w0}
    out.write_text(json.dumps(res, indent=1))
    print(json.dumps({k: v for k, v in res.items() if k != "per_cell"}, indent=1))


if __name__ == "__main__":
    main()
