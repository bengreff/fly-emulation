"""Item 2, compartment convergence (wtriage, 8 Nov 2026): every built section's nseg against NEURON's d_lambda rule.

Bar (NEURON documentation, "Using the d_lambda rule", neuronsimulator.org, opened by the literature pass): nseg is
enough when every segment is no longer than 0.1 x the AC length constant at 100 Hz,
lambda_f = 1e5 * sqrt(diam / (4 pi f Ra cm)) um (diam um, Ra ohm cm, cm uF/cm2). Required nseg = the odd number
int((L / (0.1 lambda_f) + 0.9) / 2) * 2 + 1. The template worm, default toggles, as built (no run).
Reports sections short of the rule, the worst L / (nseg x 0.1 lambda_f), and which cells hold them.

Usage (backhouse): python compartments.py
Output: runs/worm/triage/compartments.json
"""
from __future__ import annotations

import json
import math
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "scripts" / "worm"))
import at_ledger  # noqa: E402

at_ledger.patch()
from wormemu import brain as B  # noqa: E402


def main():
    b = B.Brain(B.sample_worm(None))
    h = b.h
    rows, short = [], []
    for sec in h.allsec():
        L, ra, n = sec.L, sec.Ra, sec.nseg
        d = sum(seg.diam for seg in sec) / n
        cm = sum(seg.cm for seg in sec) / n
        lam = 1e5 * math.sqrt(d / (4 * math.pi * 100.0 * ra * cm))
        need = int((L / (0.1 * lam) + 0.9) / 2) * 2 + 1
        r = dict(sec=sec.name(), L=L, diam=d, Ra=ra, cm=cm, nseg=n, need=need, ratio=L / (n * 0.1 * lam))
        rows.append(r)
        if n < need:
            short.append(r)
    cells = Counter(r["sec"].split(".")[0].split("[")[0] for r in short)
    out = dict(n_sections=len(rows), n_short=len(short), frac_short=len(short) / max(len(rows), 1),
               worst=sorted(short, key=lambda r: -r["ratio"])[:15], cells_with_short=len(cells),
               top_cells=cells.most_common(20), nseg_total=sum(r["nseg"] for r in rows),
               need_total=sum(max(r["need"], r["nseg"]) for r in rows),
               ra_values=sorted({round(r["Ra"], 3) for r in rows})[:10],
               cm_values=sorted({round(r["cm"], 4) for r in rows})[:10])
    p = ROOT / "runs/worm/triage/compartments.json"
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(out, indent=1))
    print(json.dumps({k: v for k, v in out.items() if k != "worst"}, indent=1))
    for r in out["worst"][:8]:
        print(r)


if __name__ == "__main__":
    main()
