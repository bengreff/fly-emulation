"""wneuro item 5 (written Sun 8 Nov 2026 23:16 CST, before running): is homeostasis's Ca set point the cell's own
steady state, or the start-up transient?

slow_signalling's O'Leary rule (row 19) integrates err = (c0 - Ca) / c0 per neuron, with c0 the mean of the cell's
own Ca over the first slow_set_s (2 s) of the run; the docstring's intent is "each neuron type keeps the state
development gave it" (inferred). If the network is still relaxing from its reset state during those 2 s, c0 is the
transient, the error has one sign in most cells for the rest of the run, and every density drifts one way: the code
would not do what its spec says (class A). If c0 matches each cell's later mean, the only asymmetry is the published
rule's own (err <= 1 because Ca >= 0, O'Leary et al. 2014), and there is nothing to fix in the code.

Method: the template worm at the ledger values (all cells, default toggles, homeostasis oleary), SECONDS of 1 ms
steps; each neuron's c0 (read from the module) against its mean Ca over 10 s to the end; the Ca trajectory over the
first 2 s (means over 0-0.5 s and 1.5-2 s). Homeostasis's taus are hours, so it barely moves in this run.
Bar (thresholds guessed): class A if more than half the neurons have |mean Ca(10 s-end) - c0| / c0 > 0.1 AND more
than 80% of those share one sign. Otherwise no code fix (the set point is the cell's steady state to within 10% in
most cells, or the departures go both ways).

Usage: python homeo_setpoint.py [SECONDS=20] -> runs/worm/wneuro/homeo_setpoint.json
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


def main():
    secs = float(sys.argv[1]) if len(sys.argv) > 1 else 20.0
    t0 = time.time()
    b = B.Brain(B.sample_worm(None))
    hm = next(m for m in b.mechs if type(m).__module__ == "wormemu.mech.slow_signalling")
    b.reset()
    neu = ~np.asarray(b.is_muscle, bool)
    n = int(round(secs * 1000))
    early, mid, late, nl = 0.0, 0.0, 0.0, 0
    for k in range(n):
        o = b.step(None, 1.0)
        ca = np.asarray(o.ca_uM, float)
        if k < 500:
            early = early + ca / 500.0
        elif 1500 <= k < 2000:
            mid = mid + ca / 500.0
        elif k >= 10000:
            late, nl = late + ca, nl + 1
    late = late / max(nl, 1)
    c0 = np.asarray(hm.c0, float)
    rel = (late - c0) / c0
    big = neu & (np.abs(rel) > 0.1)
    up, down = int((big & (rel > 0)).sum()), int((big & (rel < 0)).sum())
    nn = int(neu.sum())
    frac_big = big.sum() / nn
    one_sign = max(up, down) / max(big.sum(), 1)
    names = list(b.cell_names)
    order = np.argsort(-np.abs(np.where(neu, rel, 0.0)))[:15]
    res = dict(bio_s=secs, wall_s=time.time() - t0, n_neurons=nn, set_s=float(hm.p["slow_set_s"]),
               frac_departing_10pct=float(frac_big), n_up=up, n_down=down, one_sign_share=float(one_sign),
               class_A=bool(frac_big > 0.5 and one_sign > 0.8),
               rel_median=float(np.median(rel[neu])), rel_q10_q90=[float(np.quantile(rel[neu], q)) for q in (0.1, 0.9)],
               early_vs_mid_median=float(np.median(((mid - early) / np.maximum(early, 1e-9))[neu])),
               c0_median_uM=float(np.median(c0[neu])), late_median_uM=float(np.median(late[neu])),
               worst=[dict(cell=names[i], c0=float(c0[i]), late=float(late[i]), early=float(early[i]),
                           mid=float(mid[i])) for i in order],
               err_late_mean=float(np.mean(((c0 - late) / c0)[neu])))
    (ROOT / "runs/worm/wneuro/homeo_setpoint.json").write_text(json.dumps(res, indent=1))
    print(json.dumps({k: v for k, v in res.items() if k != "worst"}, indent=1))
    print(json.dumps(res["worst"][:8]))


if __name__ == "__main__":
    main()
