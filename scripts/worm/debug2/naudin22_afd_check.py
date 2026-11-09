"""Port check for nmodl/cells/naudin22_afd.mod (wbrain2, 9 Nov 2026; bars 2 and 3 of "Inbox item 5, AFD's
hyperpolarised branch" in docs/worm/night/2026-11-08_wbrain2.md, written before running).

CPU reference: Naudin et al. 2022's AFD model (S1 Table, the I_Ca,p + I_Kir + I_K,t + I_L model) with S2 Table's
multi-objective AFD column, in the paper's own units (time in ds, I in pA, g in nS, V in mV, C 0.066 pA ds/mV),
integrated by scipy (LSODA, rtol 1e-9), from their V0 -78 mV (Methods) and their fitted m0, h0. So the check also
tests the unit conversion the port makes (ds -> ms, C -> pF).

NEURON: one section, nseg 1, cm 1 uF/cm2, area 660 um2 (C 6.6 pF), the mod with densities g_nS / (1000 x 6.6) and the
module's GLOBALs; finitialize(-78), then the gates set to S2 Table's m0, h0. Sweeps: 1 s at 0 pA, 5 s step, 1 s
after, at dt 0.025 ms (bar 2) and 0.5 ms, secondorder 0 (bar 3).

  python scripts/worm/debug2/naudin22_afd_check.py [--out file.json]
"""
from __future__ import annotations

import argparse
import json
import math
from pathlib import Path

import numpy as np
from scipy.integrate import solve_ivp

from wormemu.mech import cell_models as M

# S2 Table, multi-objective, AFD, as printed (ds, pA, nS, mV)
P = dict(gCa=6.7, gKir=2.32, gK=28.01, gL=0.004, ECa=23.61, EK=-79.26, EL=-89.43, vmCa=-3.65, vmK=-2.54, vhK=-64.19,
         vKir=-86.19, kmCa=7.25, kmK=8.44, khK=-29.36, kKir=-9.01, tmCa=5.62, tmK=0.0001, thK=0.045, m0Ca=0.001,
         m0K=0.31, h0K=0.19, C=0.066)
AMPS = (-15.0, -5.0, 5.0, 15.0, 25.0, 35.0)
T_ON, T_OFF, T_END = 1000, 6000, 7000                     # ms


def b(v, vh, k):
    return 1.0 / (1.0 + np.exp((vh - v) / k))


def reference(amp):
    """V (mV) at 1 ms samples 0..T_END-1, Naudin's equations in ds."""
    p = P

    def rhs(t, y):
        v, mca, mk, hk = y
        i = amp if T_ON / 100.0 <= t < T_OFF / 100.0 else 0.0
        ion = (p["gCa"] * mca * (v - p["ECa"]) + p["gKir"] * b(v, p["vKir"], p["kKir"]) * (v - p["EK"])
               + p["gK"] * mk * hk * (v - p["EK"]) + p["gL"] * (v - p["EL"]))
        return [(-ion + i) / p["C"], (b(v, p["vmCa"], p["kmCa"]) - mca) / p["tmCa"],
                (b(v, p["vmK"], p["kmK"]) - mk) / p["tmK"], (b(v, p["vhK"], p["khK"]) - hk) / p["thK"]]

    t_ms = np.arange(T_END, dtype=float)
    y = [-78.0, p["m0Ca"], p["m0K"], p["h0K"]]
    out = []
    for a, z in ((0, T_ON), (T_ON, T_OFF), (T_OFF, T_END)):    # piecewise, so the solver never steps over an edge
        s = solve_ivp(rhs, (a / 100.0, z / 100.0), y, method="LSODA", rtol=1e-9, atol=1e-9,
                      t_eval=t_ms[(t_ms >= a) & (t_ms < z)] / 100.0)
        out.append(s.y[0])
        y = list(solve_ivp(rhs, (a / 100.0, z / 100.0), y, method="LSODA", rtol=1e-9, atol=1e-9).y[:, -1])
    return np.concatenate(out)


def neuron_sweep(h, amp, dt):
    s = h.Section(name="n22")
    s.nseg, s.cm = 1, 1.0
    s.L = s.diam = math.sqrt(660.0 / math.pi)               # pi d L = 660 um2 -> 6.6 pF at 1 uF/cm2
    s.insert(M.N22MOD)
    seg = s(0.5)
    for g, x in M.N22_G.items():
        setattr(getattr(seg, M.N22MOD), g, x * s.cm / (1000.0 * M.N22_C_PF))
    for k, (v, *_rest) in M.N22_KIN.items():
        setattr(h, f"{k}_{M.N22MOD}", float(v))
    st = h.IClamp(seg)
    st.delay, st.dur, st.amp = float(T_ON), float(T_OFF - T_ON), amp / 1000.0
    v = h.Vector()
    v.record(seg._ref_v, 1.0)
    h.dt, h.secondorder = dt, 0
    h.finitialize(-78.0)
    m = getattr(seg, M.N22MOD)
    m.mCa, m.mK, m.hK = P["m0Ca"], P["m0K"], P["h0K"]
    h.fcurrent()
    h.continuerun(T_END - 1.0)
    out = np.array(v)[:T_END]
    del st
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default="")
    a = ap.parse_args()
    from wormemu.brain import _neuron
    h = _neuron()
    rows = []
    for amp in AMPS:
        ref = reference(amp)
        ss_ref = float(ref[T_OFF - 1000:T_OFF].mean())
        for dt in (0.025, 0.5):
            v = neuron_sweep(h, amp, dt)
            n = min(len(v), len(ref))
            ss = float(v[T_OFF - 1000:T_OFF].mean())
            d = dict(pA=amp, dt=dt, max_abs_dV=float(np.abs(v[:n] - ref[:n]).max()), ss_ref=ss_ref, ss=ss,
                     d_ss=ss - ss_ref, early_ref=float(ref[T_ON:T_ON + 500].min() if amp < 0 else
                                                       ref[T_ON:T_ON + 500].max()))
            d["pass"] = bool(d["max_abs_dV"] <= 1.0 and abs(d["d_ss"]) <= 0.5) if dt == 0.025 else \
                bool(abs(d["d_ss"]) <= 1.0)
            rows.append(d)
            print(f"{amp:6.1f} pA dt {dt:5.3f}: max|dV| {d['max_abs_dV']:7.3f} mV  ss ref {ss_ref:7.2f}  "
                  f"neuron {ss:7.2f}  pass {d['pass']}", flush=True)
    res = dict(rows=rows, bar2_pass=all(r["pass"] for r in rows if r["dt"] == 0.025),
               bar3_pass=all(r["pass"] for r in rows if r["dt"] == 0.5))
    print(json.dumps({k: res[k] for k in ("bar2_pass", "bar3_pass")}))
    if a.out:
        Path(a.out).parent.mkdir(parents=True, exist_ok=True)
        Path(a.out).write_text(json.dumps(res, indent=1))


if __name__ == "__main__":
    main()
