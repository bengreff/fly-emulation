"""Line 3 (DEBUG_TRIAGE, class A; wbrain2, 8 Nov 2026): derive UNC-49's own deactivation tau (rec_gabacl_tau_off_ms).

Liu, Hollopeter and Jorgensen 2009 (PNAS 106:10823, Fig. 2B) measured the evoked NMJ GABA current's decay, 24.8 +-
2.7 ms (n = 12): a composite of the release time course and the receptor's closing. The model's evoked IPSC is the
same composite (receptor_unit_check item 3: a 2 ms presynaptic step, BAAIWorm's graded release state, decay
1/k = 8.6 ms after the step, then the receptor). Before this fix the receptor's own tau_off was set to the composite,
so the release tail added on top (29.2 ms). Here tau_off is solved (bisection) so that the composite equals 24.8 ms,
and the bounds so that it equals the bar's ends (22.1, 27.5 ms), every other value at the code templates
(at_ledger: also at the ledger values, reported).

Usage: PYTHONPATH=src .venv/bin/python scripts/worm/debug2/derive_gaba_tau_off.py [--ledger]
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
if "--ledger" in sys.argv:
    import at_ledger
    at_ledger.patch(["receptors"])
import receptor_unit_check as RU  # noqa: E402

TARGETS = {"template": 24.8, "lo": 22.1, "hi": 27.5}      # Liu et al. 2009, mean and the check's +-1 SD bar


def composite(tau_off):
    t, i = RU.run("gabacl", [(50, 52, 50.0)], 400, extra={"tau_off": tau_off})
    return RU.decay_tau(t, i, 50, 400)[0]


def solve(target, a=1.0, b=40.0, tol=0.01):
    fa = composite(a) - target
    for _ in range(40):
        m = 0.5 * (a + b)
        fm = composite(m) - target
        if (fm > 0) == (fa > 0):
            a, fa = m, fm
        else:
            b = m
        if b - a < tol:
            break
    return 0.5 * (a + b)


def main():
    out = {"release_tail_ms": 1.0 / 0.1166666666666666, "composite_at_24p8": round(composite(24.8), 2)}
    for k, v in TARGETS.items():
        tau = solve(v)
        out[k] = dict(target_ms=v, tau_off_ms=round(tau, 2), composite_ms=round(composite(tau), 2))
    print(json.dumps(out, indent=1))


if __name__ == "__main__":
    main()
