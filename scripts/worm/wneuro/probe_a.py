"""wneuro item 1 (a), feasibility probe (written Sun 8 Nov 2026 22:51 CST, before any probe run): is NLP-40 at DVB
phasic per intestinal cycle for some peptide clearance inside its range?

Question. At the template (pep_degrade_tau_s 100 s, param_ranges D4, guessed, range 10-600 s) wbody2 measured NLP-40
at DVB's compartment rising tonically to 44.7 nM in 150 s, so AEX-2 (EC50 3.39 nM, Wang et al. 2013) is held near
saturation and cannot signal each cycle. Wang et al. 2013 (PMC3651789) record one DVB Ca spike per cycle (51 of 51)
and Wang and Sieburth 2013 (PLoS Genet e1003831) show that constitutively active PKA in these neurons gives ectopic
spikes, so a tonic Gs drive is not the wild-type state.

Bar (my construction from those two sources; the 0.5 threshold is guessed): the AEX-2 drive at DVB is phasic if in
every intestinal cycle after the first (int9L/R mean Ca peaks, the same detector as dmp_trace.py), both DVB's
area-weighted AEX-2 occupancy and its Gs satisfy (peak - trough) / peak >= 0.5, with peak = max in the 10 s after the
int9 peak and trough = min in the 5 s before it. Gs is the readout that reaches the channels; occupancy is reported to
show where the signal is lost. Values probed: pep_degrade_tau_s = 10, 30, 100 (template) s, inside 10-600 s, each one
dmp_trace.py run of 150 s with cells=dmp and the new neuromod defaults. A pass makes (a) class D for the clearance
(a passing value exists in range; not adopted). If none passes, (a) is A or B and the cause is written down.

Amendment (22:59 CST, still before any probe run): the template run (tau 100 s) shows the intestine releasing NLP-40
at basal Ca (Hill(0.09 uM; k 0.3 uM, n 2) = 8% of the maximum, tonic), so the clearance alone may not be enough.
Second stage, same bar: the intestine's guessed release-shape gaps (organs_intestine, wbody2's: nlp40_release_k_uM
0.1-1.0, nlp40_release_hill 1-4, nlp40_release_nM_per_s 1-100) at the corner that removes the tonic part while
keeping the peak (k 1.0, hill 4, release 100 nM/s), with tau 10 and 30 s. Probe only; nothing in wbody2's file changes.

Usage: python probe_a.py RUN.json [RUN.json ...]   (dmp_trace.py outputs) -> prints the per-cycle table and verdict
"""
from __future__ import annotations

import json
import sys

import numpy as np


def modulation(t, x, peaks_s):
    rows = []
    for a in peaks_s[1:]:
        pk = x[(t >= a) & (t < a + 10.0)]
        tr = x[(t >= a - 5.0) & (t < a)]
        if not len(pk) or not len(tr):
            continue
        p, q = float(pk.max()), float(tr.min())
        rows.append(dict(peak_s=a, peak=p, trough=q, mod=(p - q) / p if p > 0 else 0.0))
    return rows


def main():
    for f in sys.argv[1:]:
        r = json.load(open(f))
        tr = r["trace"]
        t = np.array(tr["t"])
        out = {}
        for k in ("DVB_occ", "DVB_gs"):
            rows = modulation(t, np.array(tr[k]), r["int9_peaks_s"])
            out[k] = dict(passed=bool(rows) and all(x["mod"] >= 0.5 for x in rows),
                          mod=[round(x["mod"], 3) for x in rows], peak=[round(x["peak"], 3) for x in rows],
                          trough=[round(x["trough"], 3) for x in rows])
        print(json.dumps(dict(run=f, params=r.get("params"), int9_peaks_s=r["int9_peaks_s"],
                              dvb_read_nM=r["summary"]["DVB_nlp40_read_nM"], **out,
                              phasic=out["DVB_occ"]["passed"] and out["DVB_gs"]["passed"]), indent=1))


if __name__ == "__main__":
    main()
