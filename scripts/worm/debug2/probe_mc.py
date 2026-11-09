"""MC (pharyngeal pacemaker motor neuron) at the ledger values: what it is built from and whether it has any
regenerative event (inbox item 1, wbrain2, 8 Nov 2026).

Sub-brain of the named cells (default MCL, MCR, and AS01 which carries the same BAAIWorm set), no synapses beyond
those among them, default observation. Prints each cell's soma densities as built, then current steps of 1 s
(0 to 100 pA) with 0.5 s rest between, and for each step the plateau V, the peak and the number of upward crossings
of -20 mV (a spike count). --brain runs the whole brain (--sub a sub-brain) for --secs at rest and reports the
--cells' V distribution and upward -20 mV crossings instead.

  python scripts/worm/debug2/probe_mc.py [--cells MCL,MCR,AS01] [--toggles '{"k": "v"}'] [--out file.json]
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np

AMPS = (0.0, 2.0, 5.0, 10.0, 20.0, 40.0, 80.0, 100.0)


def built(b, name):
    from wormemu.brain import CHANNELS, GB
    seg = b.soma[b.idx[name]](0.5)
    d = {ch: float(getattr(getattr(seg, ch), GB.get(ch, f"gb{ch}"))) for ch in CHANNELS[:-1]}
    d.update(gpas=float(seg.pas.g), epas=float(seg.pas.e), cm=float(b.soma[b.idx[name]].cm),
             area_um2=float(sum(s.area() for s in b.soma[b.idx[name]])))
    return d


def steps(b, names, amps=AMPS, on_ms=1000, off_ms=500):
    b.reset()
    for _ in range(1000):                                  # 1 s to settle
        b.step()
    out = {n: [] for n in names}
    for a in amps:
        tr = {n: [] for n in names}
        for k in range(on_ms + off_ms):
            for n in names:
                b.extra_pA[b.idx[n]] = a if k < on_ms else 0.0
            v = b.step().v_mV
            for n in names:
                tr[n].append(float(v[b.idx[n]]))
        for n in names:
            x = np.array(tr[n][:on_ms])
            up = int(np.sum((x[1:] >= -20.0) & (x[:-1] < -20.0)))
            out[n].append(dict(pA=a, start=tr[n][0], plateau=float(x[-200:].mean()), peak=float(x.max()),
                               spikes=up, after=tr[n][-1]))
    return out


def events(x, thr=-30.0, gap_ms=50):
    """Times (ms) of upward crossings of thr at least gap_ms apart: MC's depolarising events."""
    t = np.flatnonzero((x[1:] >= thr) & (x[:-1] < thr)) + 1
    out = []
    for k in t:
        if not out or k - out[-1] >= gap_ms:
            out.append(int(k))
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--cells", default="MCL,MCR,AS01")
    ap.add_argument("--toggles", default="{}")
    ap.add_argument("--brain", action="store_true")
    ap.add_argument("--sub", default="", help="comma list: a sub-brain of these cells at rest, report --cells' V")
    ap.add_argument("--secs", type=float, default=3.0)
    ap.add_argument("--food", type=float, default=0.0, help="food_OD at the head (0 = the open-loop observation)")
    ap.add_argument("--out", default="")
    a = ap.parse_args()
    from wormemu.brain import Brain
    names = a.cells.split(",")
    tg = json.loads(a.toggles)
    res = dict(toggles=tg)
    if a.brain or a.sub:
        b = Brain(toggles=tg, cells=a.sub.split(",") if a.sub else None)
        from wormemu.interface import default_observation
        b.reset()
        V, CA, pumps = [], [], 0
        for _ in range(int(a.secs * 1000)):
            obs = default_observation(b.t)
            obs.head["food_OD"] = a.food
            o = b.step(obs, 1.0)
            pumps += int(getattr(o, "pumps", 0) or 0)
            V.append(o.v_mV[[b.idx[n] for n in names]])
            CA.append([b.soma[b.idx[n]](0.5).cai for n in names])
        V, CA = np.array(V), np.array(CA)
        res["cai_uM"] = {n: dict(median=float(np.median(CA[:, i])) * 1e3, max=float(CA[:, i].max()) * 1e3)
                         for i, n in enumerate(names)}
        res.update(food_OD=a.food, pumps=pumps, events_ms={n: events(V[:, i]) for i, n in enumerate(names)})
        res["brain"] = {n: dict(median=float(np.median(V[:, i])), max=float(V[:, i].max()), min=float(V[:, i].min()),
                                crossings=int(np.sum((V[1:, i] >= -20.0) & (V[:-1, i] < -20.0))))
                        for i, n in enumerate(names)}
        res["built"] = {n: built(b, n) for n in names}
    else:
        b = Brain(toggles=tg, cells=names)
        res["built"] = {n: built(b, n) for n in names}
        res["steps"] = steps(b, names)
    print(json.dumps(res, indent=1))
    if a.out:
        Path(a.out).parent.mkdir(parents=True, exist_ok=True)
        Path(a.out).write_text(json.dumps(res, indent=1))


if __name__ == "__main__":
    main()
