"""Port check for nmodl/cells/jiang22_avl.mod against the CPU reference jiang22_ref.py (wbrain2, 9 Nov 2026; bars 2
and 3 of "Jiang 2022's AVL model as a B toggle" in docs/worm/night/2026-11-08_wbrain2.md, written before running).

One NEURON section, nseg 1, cm 1 uF/cm2, area 500 um2 (C 5 pF, Jiang's), no pas; the mod's densities at g_nS / (1000 x
5) S/cm2; EGL-36 weights as in the code (0.31, the reference's); Jiang's start state; their sweep (fresh start, step
from 1 s to the last 1 s). At dt 0.025 ms (bar 2: transcription) and at the brain's 0.5 ms, secondorder 0 (bar 3).

  python scripts/worm/debug2/jiang22_port_check.py [--out file.json]
"""
from __future__ import annotations

import argparse
import json
import math
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
from jiang22_ref import SETS, sweep  # noqa: E402
from probe_dvb import event  # noqa: E402

G = ("g_UNC2", "g_EGL19", "g_CCA1", "g_SHL1", "g_EGL36", "g_EXP2", "g_NCA", "g_L")
CASES = (("wt", 6.0), ("wt", 10.0), ("dvb", 6.0))
SECS = 7.0


def neuron_sweep(h, p, amp, dt):
    s = h.Section(name="j22")
    s.nseg, s.cm = 1, 1.0
    s.L = s.diam = math.sqrt(500.0 / math.pi)                 # pi d L = 500 um2 -> 5 pF at 1 uF/cm2
    s.insert("j22avl")
    for g in G:
        setattr(s(0.5).j22avl, g, p[g] * s.cm / (1000.0 * p["C"]))
    for k, x in p.items():
        if k not in G and k != "C":
            setattr(h, f"{k}_j22avl", float(x))
    h.w36_f_j22avl = 0.31                                      # the code's weight, as the reference
    st = h.IClamp(s(0.5))
    st.delay, st.dur, st.amp = 1000.0, SECS * 1000.0 - 2000.0, amp / 1000.0
    v = h.Vector()
    v.record(s(0.5)._ref_v, 1.0)
    h.dt, h.secondorder = dt, 0
    h.finitialize(-60.0)
    h.continuerun(SECS * 1000.0 - 1.0)
    out = np.array(v)[:int(SECS * 1000)]
    del st
    return out


def metrics(v):
    e = event(v[1000:int(SECS * 1000) - 1000])
    return e and {k: e[k] for k in ("peak", "threshold", "half_width_ms", "ahp", "t_peak_ms")}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default="")
    a = ap.parse_args()
    from wormemu.brain import _neuron
    h = _neuron()
    rows = []
    for name, amp in CASES:
        p = SETS[name]
        _, y = sweep(p, amp, SECS)
        ref = y[0][:int(SECS * 1000)]
        er = metrics(ref)
        for dt in (0.025, 0.5):
            v = neuron_sweep(h, p, amp, dt)
            n = min(len(v), len(ref))
            e = metrics(v)
            d = dict(set=name, pA=amp, dt=dt, max_abs_dV=float(np.abs(v[:n] - ref[:n]).max()), ref=er, neuron=e)
            if er and e:
                d["d_peak"] = e["peak"] - er["peak"]
                d["d_threshold"] = e["threshold"] - er["threshold"]
                d["hw_ratio"] = e["half_width_ms"] / er["half_width_ms"]
            if dt == 0.025:
                d["pass"] = bool(d["max_abs_dV"] <= 1.0 and er and e and abs(d["d_peak"]) <= 0.5
                                 and abs(d["d_threshold"]) <= 0.5 and abs(d["hw_ratio"] - 1) <= 0.02)
            else:
                d["pass"] = bool(er and e and abs(d["d_peak"]) <= 2.0 and abs(d["d_threshold"]) <= 2.0
                                 and abs(d["hw_ratio"] - 1) <= 0.10)
            rows.append(d)
            print(f"{name:4s} {amp:4.1f} pA dt {dt:5.3f}: max|dV| {d['max_abs_dV']:7.3f} mV  "
                  f"ref {er and round(er['peak'], 2)}/{er and round(er['threshold'], 2)}/{er and er['half_width_ms']}  "
                  f"neuron {e and round(e['peak'], 2)}/{e and round(e['threshold'], 2)}/{e and e['half_width_ms']}  "
                  f"pass {d['pass']}", flush=True)
    res = dict(rows=rows, bar2_pass=all(r["pass"] for r in rows if r["dt"] == 0.025),
               bar3_pass=all(r["pass"] for r in rows if r["dt"] == 0.5))
    print(json.dumps({k: res[k] for k in ("bar2_pass", "bar3_pass")}))
    if a.out:
        Path(a.out).parent.mkdir(parents=True, exist_ok=True)
        Path(a.out).write_text(json.dumps(res, indent=1))


if __name__ == "__main__":
    main()
