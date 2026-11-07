"""Row 24 unit and sanity checks in NEURON (bars in docs/worm/night/2026-11-06_wbrain.md, written before running).
One wsyn between two single-compartment cells, presynaptic voltage clamped to pulse trains, postsynaptic clamped
at -60 mV; the response is the synapse's peak current per pulse (the leak's offset excluded).

2. Held out (Liu et al. 2009): 0.2 Hz tau in 2.23-7.19 s; second/first in 0.25-0.45 at 10 and 20 Hz (L-AChR).
3. GABA sanity: UNC-49 plateau above 0.8 at 1 and 5 Hz; second/first above 1 at 20 Hz.
4. Code check: NEURON per-pulse amplitudes within 2% of mech.plasticity.numpy_reference (1 and 5 Hz).
5. Habituation sanity: touch-cell synapse, 10 x 20 ms steps at 10 s and 60 s intervals; 10th smaller at 10 s;
   above 90% of the first after 30 min of rest.

Usage: PYTHONPATH=src .venv/bin/python scripts/worm/stp_unit_check.py [out.json]
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
import stp_fit as F                                          # noqa: E402
from wormemu.brain import _neuron                            # noqa: E402
from wormemu.mech import plasticity as P                     # noqa: E402
from wormemu.mech import receptors as R                      # noqa: E402

h = _neuron()
T = F.T


def cell(name):
    s = h.Section(name=name)
    s.L = s.diam = 5.0
    s.insert("pas")
    return s


PRE, POST = cell("pre"), cell("post")
SYN = h.wsyn(POST(0.5))
h.setpointer(PRE(0.5)._ref_v, "vpre", SYN)
VC = h.SEClamp(POST(0.5))
VC.dur1, VC.amp1, VC.rs = 1e9, -60.0, 1e-3
PC = h.SEClamp(PRE(0.5))
PC.dur1, PC.rs = 1e9, 1e-3


def run(vpre, cls="lacr", hab=False, touch=False, stp="dittman_regehr"):
    """Synaptic current per step (nA) for a presynaptic voltage trace sampled at F.DT."""
    for k, v in R.site_params(T, cls, 2).items():
        setattr(SYN, k, v)
    for k, v in P.wsyn_params(T, "gaba" if cls == "gabacl" else "ach", stp, hab, touch).items():
        setattr(SYN, k, v)
    for k, v in F.REL.items():
        setattr(SYN, k, v)
    SYN.gmax = 0.001
    vec, out = h.Vector(vpre), h.Vector()
    vec.play(PC._ref_amp1, F.DT)
    out.record(SYN._ref_i, F.DT)
    h.dt, h.secondorder = F.DT, 0
    h.finitialize(-60.0)
    h.continuerun(len(vpre) * F.DT)
    i = np.array(out)[1:len(vpre) + 1]
    vec.play_remove()
    return i


def per_pulse(i, per):
    return np.abs(i[:len(i) // per * per]).reshape(-1, per).max(1)


def main():
    res = {}
    amp = {}
    for hz in (0.2, 1.0, 5.0, 10.0, 20.0):
        v, per = F.train(hz)
        amp[hz] = per_pulse(run(v), per)
    tau02, pl02 = F.fit_tau(amp[0.2], 0.2)
    r10, r20 = amp[10.0][1] / amp[10.0][0], amp[20.0][1] / amp[20.0][0]
    res["held_out"] = dict(tau_0p2Hz_s=tau02, plateau_0p2Hz=pl02, second_over_first_10Hz=r10,
                           second_over_first_20Hz=r20,
                           fit_1Hz=F.fit_tau(amp[1.0], 1.0), fit_5Hz=F.fit_tau(amp[5.0], 5.0),
                           first_10_rel={str(k): (a[:10] / a[0]).round(3).tolist() for k, a in amp.items()},
                           bar="tau 2.23-7.19 s; second/first 0.25-0.45 at 10 and 20 Hz",
                           passed=dict(tau=bool(2.23 <= tau02 <= 7.19), r10=bool(0.25 <= r10 <= 0.45),
                                       r20=bool(0.25 <= r20 <= 0.45)))
    g = {}
    for hz in (1.0, 5.0, 20.0):
        v, per = F.train(hz)
        a = per_pulse(run(v, "gabacl"), per)
        g[hz] = (a / a[0])
    res["gaba"] = dict(plateau_1Hz=float(g[1.0][-5:].mean()), plateau_5Hz=float(g[5.0][-5:].mean()),
                       second_over_first_20Hz=float(g[20.0][1]), bar="plateaus > 0.8; 20 Hz second/first > 1",
                       passed=bool(g[1.0][-5:].mean() > 0.8 and g[5.0][-5:].mean() > 0.8 and g[20.0][1] > 1))
    err = 0.0
    for hz in (1.0, 5.0):
        v, per = F.train(hz)
        a = amp[hz] / amp[hz][0]
        b = F.amplitudes(T, hz)
        b = b / b[0]
        err = max(err, float(np.max(np.abs(a - b) / b)))
    res["neuron_vs_numpy"] = dict(max_rel_err=err, bar="0.02", passed=bool(err < 0.02))
    hab = {}
    for isi in (10.0, 60.0):
        per = int(round(isi * 1000 / F.DT))
        n_rest = int(round(1800e3 / F.DT))
        v = np.full(10 * per + n_rest + per, -60.0)
        for k in list(range(10)) + [10 + n_rest // per]:
            v[k * per:k * per + int(20.0 / F.DT)] = 0.0
        i = run(v, hab=True, touch=True)
        a = per_pulse(i, per)
        a = a[a > 0.01 * a[0]] / a[0]
        hab[str(isi)] = dict(tenth=float(a[9]), after_30min=float(a[-1]))
    res["habituation"] = dict(**hab, bar="10th smaller at 10 s; > 0.9 after 30 min",
                              passed=bool(hab["10.0"]["tenth"] < hab["60.0"]["tenth"]
                                          and min(x["after_30min"] for x in hab.values()) > 0.9))
    off = run(F.train(1.0)[0], stp="off")
    res["off_q"] = float(SYN.q)
    print(json.dumps(res, indent=1, default=float))
    if len(sys.argv) > 1:
        open(sys.argv[1], "w").write(json.dumps(res, indent=1, default=float))
    return off


if __name__ == "__main__":
    main()
