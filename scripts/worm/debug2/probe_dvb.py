"""DVB's action potential at the ledger, alone and embedded (wneuro's request, Director inbox 23:36, wbrain2, 8 Nov 2026).
--cell AVL (9 Nov) scores AVL against Jiang's AVL recordings (Fig 1c, n 17; bars in the night file's "Jiang 2022's
AVL model as a B toggle", written before running).

Check and bars: docs/worm/night/2026-11-08_wbrain2.md, "DVB cannot fire" (written before running). Jiang et al. 2022
Nat Commun 13:2783 (PMC9120479, Fig 1): 5 s current steps at 1 pA increments; rest -49.0 +- 3.6, threshold -23.4 +- 1.6,
peak 26.3 +- 2.6 mV, half-width 358.8 +- 59.5 ms (mean +- s.e.m., n = 5). Bars mean +- 2 SD, SD = s.e.m. x sqrt 5
(derived).

Contexts: alone (Brain(cells=["DVB"]), its own neurite), dmp (wbody2's DMP sub-brain, AVL, DVB and their 12 Cook
partners), whole (the whole brain). Diagnostics (never adopted): cut=gap zeroes every gap junction with a half on
DVB (both halves), cut=syn zeroes every chemical synapse onto DVB. Also records the gap and synaptic current into DVB
(nA, + = into the cell) over the last 1 s of each step.

  python scripts/worm/debug2/probe_dvb.py alone|dmp|whole [--cell DVB|AVL] [--amps 1,2,...] [--cut gap|syn|gap,syn]
      [--toggles '{}'] [--trace] [--out file.json]
"""
from __future__ import annotations

import argparse
import json
import time
from pathlib import Path

import numpy as np

DMP = ["AVL", "DVB", "PVR", "AVAL", "AVAR", "PHAL", "PHAR", "PDA", "DA09", "VA12", "LUAL", "LUAR", "PVCL", "PVCR"]
SEM5 = 5 ** 0.5
JIANG = dict(rest=(-49.0, 3.6), threshold=(-23.4, 1.6), peak=(26.3, 2.6), half_width_ms=(358.8, 59.5))
BARS = {k: (m - 2 * s * SEM5, m + 2 * s * SEM5) for k, (m, s) in JIANG.items()}
JIANG_AVL = dict(rest=(-45.7, 1.1), threshold=(-23.3, 0.8), peak=(9.8, 0.8), ahp=(-64.8, 1.2),
                 half_width_ms=(394.2, 40.0))                         # n = 17, mean +- s.e.m.
BARS_AVL = {k: (m - 2 * s * 17 ** 0.5, m + 2 * s * 17 ** 0.5) for k, (m, s) in JIANG_AVL.items()}
GAPS = ("gapjunction", "rectgap")


def i_nA(pp):
    """A point process's current (nA, + = out of the cell); BAAIWorm's inhibitory synapse does not expose i."""
    if hasattr(pp, "i"):
        return pp.i
    if hasattr(pp, "s"):
        return pp.weight * pp.conductance * pp.s * (pp.get_segment().v - pp.erev)
    return 0.0


def event(x, dv_frac=0.1, fall_mV=10.0):
    """The first all-or-none event in x (1 ms samples): a local maximum above 0 mV followed by a fall of fall_mV.
    Returns dict(peak, t_peak_ms, threshold, half_width_ms, ahp) or None."""
    n = len(x)
    for k in range(1, n - 1):
        if x[k] > 0.0 and x[k] >= x[k - 1] and x[k] > x[k + 1]:
            after = x[k + 1:]
            if not len(after) or after.min() > x[k] - fall_mV:
                continue
            dv = np.diff(x)[:k]                           # dv[j] = x[j+1] - x[j]
            ds = np.convolve(np.diff(x), np.ones(5) / 5, "same")[:k]   # 5 ms smoothing, only to find extrema
            j0 = int(np.argmin(x[:k]))                    # the rise to the first event starts at its lowest point
            js = k - 1
            while js > j0 and ds[js - 1] >= ds[js]:
                js -= 1                                   # back from the peak to the steepest upstroke
            im = js
            while im > j0 and ds[im - 1] <= ds[im]:
                im -= 1                                   # and on back to the inflection (onset charging excluded)
            smax = float(dv[im:js + 1].max())
            jt = next(j for j in range(im, js + 1) if dv[j] >= dv_frac * smax)
            thr = float(x[jt])
            lvl = 0.5 * (thr + x[k])
            a = k
            while a > 0 and x[a - 1] > lvl:
                a -= 1
            b = k
            while b < n - 1 and x[b + 1] > lvl:
                b += 1
            nxt = next((m for m in range(k + 1, n - 1) if x[m] > 0.0 and x[m] >= x[m - 1] and x[m] > x[m + 1]), n)
            return dict(peak=float(x[k]), t_peak_ms=k, threshold=thr, half_width_ms=float(b - a + 1),
                        ahp=float(x[k:nxt].min()))
    return None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("context", choices=("alone", "dmp", "whole"))
    ap.add_argument("--cell", default="DVB", choices=("DVB", "AVL"))
    ap.add_argument("--amps", default="")
    ap.add_argument("--on_ms", type=int, default=5000)
    ap.add_argument("--off_ms", type=int, default=1000)
    ap.add_argument("--cut", default="")
    ap.add_argument("--toggles", default="{}")
    ap.add_argument("--trace", action="store_true", help="store each step's V (1 ms) in the json")
    ap.add_argument("--out", default="")
    a = ap.parse_args()
    from wormemu import brain as B
    tg = json.loads(a.toggles)
    amps = [float(s) for s in a.amps.split(",")] if a.amps else \
        ([10.0, 20.0] if a.context == "whole" else [float(k) for k in range(1, 21)])
    pairs = []
    orig = B.Brain._gap

    def rec_gap(self, seg_a, seg_b, g_uS, kind, into=None, ratio=1.0):
        n0 = len(self.conn)
        orig(self, seg_a, seg_b, g_uS, kind, into=into, ratio=ratio)
        pairs.append((self.conn[n0], self.conn[n0 + 1], seg_a.sec, seg_b.sec))
    B.Brain._gap = rec_gap
    t0 = time.time()
    cells = {"alone": [a.cell], "dmp": DMP, "whole": None}[a.context]
    bars = BARS if a.cell == "DVB" else BARS_AVL
    b = B.Brain(toggles=tg, cells=cells)
    B.Brain._gap = orig
    dvb = b.idx[a.cell]                                    # the probed cell (DVB unless --cell)
    own = {s.name() for s in b.soma[dvb].wholetree()}
    gp = [(p, q) for p, q, sa, sb in pairs if sa.name() in own or sb.name() in own]
    g_in = [p if p.get_segment().sec.name() in own else q for p, q in gp]   # the half on DVB
    syn = [pp for pp in b.conn if pp.hname().split("[")[0] not in GAPS and pp.get_segment().sec.name() in own]
    load = dict(gap_halves_on_dvb=len(g_in), gap_g_sum_nS=float(sum(p.weight for p in g_in)) * 1e3,
                synapses_onto_dvb=len(syn), synapse_types=sorted({pp.hname().split("[")[0] for pp in syn}))
    for c in filter(None, a.cut.split(",")):
        if c == "gap":
            for p, q in gp:
                p.weight = q.weight = 0.0
        elif c == "syn":
            for pp in syn:
                for w in ("weight", "gmax"):
                    if hasattr(pp, w):
                        setattr(pp, w, 0.0)
        else:
            raise ValueError(c)
    b.reset()
    pre = [float(b.step().v_mV[dvb]) for _ in range(1000)]
    rows = []
    for amp in amps:
        x, ig, isy = [], [], []
        for k in range(a.on_ms + a.off_ms):
            b.extra_pA[dvb] = amp if k < a.on_ms else 0.0
            x.append(float(b.step().v_mV[dvb]))
            if a.on_ms - 1000 <= k < a.on_ms:
                ig.append(-sum(p.i for p in g_in))
                isy.append(-sum(i_nA(pp) for pp in syn))
        x = np.array(x)
        on = x[:a.on_ms]
        rows.append(dict(pA=amp, peak=float(on.max()), plateau=float(on[-1000:].mean()), after=float(x[-1]),
                         event=event(on), gap_in_nA=float(np.mean(ig)), syn_in_nA=float(np.mean(isy))))
        if a.trace:
            rows[-1]["v"] = np.round(x, 2).tolist()
    rest = float(np.mean(pre[-500:]))
    first = next((r for r in rows if r["event"]), None)
    score = dict(rest=rest, rheobase_pA=first["pA"] if first else None)
    if first:
        score.update({k: first["event"][k] for k in ("peak", "threshold", "half_width_ms", "ahp")})
    passes = {k: (score.get(k) is not None and lo <= score[k] <= hi) for k, (lo, hi) in bars.items()}
    passes["spike_by_20pA"] = bool(first and first["pA"] <= 20.0)
    res = dict(context=a.context, cell=a.cell, cut=a.cut, toggles=tg, cells=len(b.idx), wall_s=time.time() - t0,
               bars=bars,
               load=load, score=score, passes=passes, all_pass=all(passes.values()), steps=rows)
    print(json.dumps(dict(score=score, passes=passes, load=load, wall_s=res["wall_s"]), indent=1))
    for r in rows:
        e = r["event"] or {}
        print(f"{r['pA']:5.1f} pA  peak {r['peak']:7.1f}  plateau {r['plateau']:7.1f}  event "
              f"{e.get('peak', float('nan')):6.1f} thr {e.get('threshold', float('nan')):6.1f} "
              f"hw {e.get('half_width_ms', float('nan')):6.0f}  gap {r['gap_in_nA'] * 1e3:7.2f} pA  "
              f"syn {r['syn_in_nA'] * 1e3:7.2f} pA")
    if a.out:
        Path(a.out).parent.mkdir(parents=True, exist_ok=True)
        Path(a.out).write_text(json.dumps(res, indent=1))


if __name__ == "__main__":
    main()
