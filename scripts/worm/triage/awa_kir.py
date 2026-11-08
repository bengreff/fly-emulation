"""Row 17 AWA, cause check (wtriage, 8 Nov 2026). Never adopted; nothing written outside runs/worm/triage.

The ported Liu 2018 inward rectifier, I_Kir = -gKir (beta log[1 + exp(-(v - vK + I0)/beta)] + I0) (senses_checks.py
liu_currents, awa_liu2018.mod), is inward at every voltage: -gKir I0 = -4 pA above vK. A K+ current cannot be inward
above E_K. Liu et al. 2018 (bioRxiv 359935 methods, opened 8 Nov): the inward rectifier was 'tuned to match resting
potential around -75 mV'; the recorded rest is -75.3 +/- 4.7 mV (n = 27). This script runs the check's own protocol
(senses_checks.awa, scipy reference) with the Kir read three ways and reports rest, first spike, amplitude, and the
spike at double the current:
  as_ported      the printed form as ported
  smooth_min_mV  I = gKir * smooth-min(v - vK, I0) with I0 and beta in mV: -gKir (beta log[1 + exp(-(v - vK - I0)/beta)] - I0)
  smooth_min_pA  the same with I0 = 5 pA and beta = 5 pA as currents: -(beta log[1 + exp(-(gKir (v - vK) - I0)/beta)] - I0)
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[3]
sys.path[:0] = [str(ROOT / "scripts" / "worm"), str(ROOT / "src")]
sys.argv = ["x"]
import senses_checks as SC  # noqa: E402

FORMS = {
    "as_ported": lambda v, P: -P["gKir"] * (P["beta"] * np.log1p(np.exp(-(v - P["vK"] + P["I0"]) / P["beta"])) + P["I0"]),
    "smooth_min_mV": lambda v, P: -P["gKir"] * (P["beta"] * np.log1p(np.exp(-(v - P["vK"] - P["I0"]) / P["beta"])) - P["I0"]),
    "smooth_min_pA": lambda v, P: -(P["beta"] * np.log1p(np.exp(-(P["gKir"] * (v - P["vK"]) - P["I0"]) / P["beta"])) - P["I0"]),
}
ORIG = SC.liu_currents


def run(form):
    def cur(v, s, P=SC.LIU):
        c1, c2, k1, k2, k3, kr, ks = s
        iCa = P["gCa"] * (c1 + P["f"] * c2) * (v - P["vCa"])
        iK = (P["gK1"] * k1 + P["gK2"] * k2 + P["gK3"] * k3 + P["gKr"] * kr * SC._hinf(v, P["vKr1"], P["dvKr1"])
              + P["gKs"] * ks) * (v - P["vK"])
        return iCa + iK + FORMS[form](v, P) + P["gL"] * (v - P["vL"])
    SC.liu_currents = cur
    try:
        steps = list(range(1, 41))
        v0, out, _ = SC.awa_cpu(steps)
        first = next((I for I in steps if out[I]), None)
        r = dict(rest_mV=round(v0, 2), i_kir_at_m50_pA=round(float(FORMS[form](-50.0, SC.LIU)), 3),
                 i_kir_at_m75_pA=round(float(FORMS[form](-75.0, SC.LIU)), 3), first_step_pA=first)
        if first:
            r["first"] = out[first]
            r["double"] = out.get(2 * first) or SC.awa_cpu([2 * first])[1][2 * first]
            amps = [out[I]["amplitude_mV"] for I in steps if out[I]]
            r["amplitude_range_mV"] = [min(amps), max(amps)]
        return r
    finally:
        SC.liu_currents = ORIG


if __name__ == "__main__":
    res = {f: run(f) for f in FORMS}
    res["bars"] = "threshold -34 +/- 5 mV, amplitude 25.8 +/- 6 mV, all-or-none (double within 20%) (senses_checks.awa)"
    out = ROOT / "runs" / "worm" / "triage"
    out.mkdir(parents=True, exist_ok=True)
    (out / "awa_kir.json").write_text(json.dumps(res, indent=1, default=float))
    print(json.dumps(res, indent=1, default=float))
