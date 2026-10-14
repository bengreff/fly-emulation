"""Per-cycle MN modulation depth for the bypass assay (s13 S4; DECISIONS 13 Oct, S4 pre-registration).

The S3 result (F-BYPASS-4) and Pugliese's reference differ less in rhythm than in how deeply each MN pool is
modulated on every cycle. This readout measures that, the same way for both models:

- f0: the pool's spectral peak in 7-15 Hz (Pugliese 2025's reported range) over the scored window;
- the trace is folded at period 1/f0 into 12 phase bins; the "on" half-cycle is the 6 contiguous bins (circular)
  with the largest mean;
- per cycle k: m_k = (on - off) / (on + off), the summed activity in the on half against the off half of that cycle.
  For spiking runs a cycle with fewer than `--min-spikes` pool spikes scores m_k = 0 (one spike is not a burst;
  the floor of 3 is guessed: S2/S3 pools at 1.5-2 spikes per cycle score depth 1.0 with a floor of 2; floors 2
  and 5 are reported alongside);
- depth = median m_k over complete cycles; also reported: pool spikes per cycle and the fraction of cycles that
  reach the spike floor;
- drive_ratio = pool rate in the scored window / pool rate before drive onset. Calibration on S2 (13 Oct 23:40):
  the tonic tibia flexors fire regularly and in sync at 23 Hz before and during drive and score depth 0.4-1.0 at
  their own firing frequency, so depth alone is not drive-locked modulation. A pool counts only with
  drive_ratio >= 2 (guessed) or silence before drive.

Rate traces (Pugliese, arbitrary units) have no spike floor; their depth is the reference, not a target in Hz.

    uv run python scripts/probes/bypass_moddepth.py --ref runs/s13/bypass/pugliese_ref/fly_ref/mcns_DNg100R_I400_R.npz
    uv run python scripts/probes/bypass_moddepth.py runs/s13/bypass/s3/s2_A_25mv_traces.npz --t0 500 --t1 1300
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np

NB = 12


def f_peak(x: np.ndarray, dt_s: float, lo: float = 7.0, hi: float = 15.0) -> float:
    x = x - x.mean()
    n = 1 << int(np.ceil(np.log2(len(x) * 4)))  # zero-pad for a finer frequency grid
    p = np.abs(np.fft.rfft(x * np.hanning(len(x)), n)) ** 2
    f = np.fft.rfftfreq(n, dt_s)
    m = (f >= lo) & (f <= hi)
    return float(f[m][np.argmax(p[m])]) if p[m].max() > 0 else float("nan")


def depth(x: np.ndarray, dt_s: float, min_spikes: float | None) -> dict:
    """x: activity per bin (spike counts, or rate) over the scored window."""
    tot = float(x.sum())
    if tot <= 0:
        return dict(f0_hz=None, depth=0.0, per_cycle=None, cycles=0, frac_cycles_floor=0.0, profile=None)
    f0 = f_peak(x, dt_s)
    per = 1.0 / f0 / dt_s                               # period in bins
    ph = (np.arange(len(x)) % per) / per
    pb = np.minimum((ph * NB).astype(int), NB - 1)
    prof = np.bincount(pb, weights=x, minlength=NB) / np.maximum(np.bincount(pb, minlength=NB), 1)
    on0 = int(np.argmax([prof[(i + np.arange(NB // 2)) % NB].mean() for i in range(NB)]))
    on_bins = set(((on0 + np.arange(NB // 2)) % NB).tolist())
    is_on = np.array([b in on_bins for b in pb])
    cyc = (np.arange(len(x)) // per).astype(int)
    ms, n_cyc, n_floor, counts = [], 0, 0, []
    for k in range(int(len(x) // per)):            # complete cycles only
        sel = cyc == k
        on, off = float(x[sel & is_on].sum()), float(x[sel & ~is_on].sum())
        n_cyc += 1
        counts.append(on + off)
        if min_spikes is not None and on + off < min_spikes:
            ms.append(0.0)
            continue
        n_floor += 1
        ms.append((on - off) / (on + off) if on + off > 0 else 0.0)
    return dict(f0_hz=round(f0, 2), depth=round(float(np.median(ms)), 3) if ms else 0.0,
                per_cycle=round(float(np.mean(counts)), 2), cycles=n_cyc,
                frac_cycles_floor=round(n_floor / max(n_cyc, 1), 3),
                profile=[round(float(v), 4) for v in prof])


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("traces", nargs="*", help="bypass_s2_descending.py *_traces.npz (1 ms bins, pool spike counts)")
    ap.add_argument("--ref", action="append", default=[], help="Pugliese reference *_R.npz (R_mn rate traces)")
    ap.add_argument("--ref-dt-ms", type=float, default=1.0)
    ap.add_argument("--ref-t0", type=int, default=250, help="reference scored window start (their clip)")
    ap.add_argument("--ref-active", type=float, default=1.0, help="reference MN counts as active above this peak")
    ap.add_argument("--t0", type=int, default=500, help="spiking scored window start, ms (drive on + 200)")
    ap.add_argument("--t1", type=int, default=1300)
    ap.add_argument("--b0", type=int, default=0, help="pre-drive window start, ms")
    ap.add_argument("--b1", type=int, default=300, help="pre-drive window end, ms (drive onset)")
    ap.add_argument("--min-spikes", type=float, default=3.0)
    ap.add_argument("--min-total", type=int, default=10, help="pools with fewer spikes in the window are not scored")
    ap.add_argument("--out", default="")
    a = ap.parse_args()
    res = {}
    for r in a.ref:
        d = np.load(r)
        R = d["R_mn"][:, a.ref_t0:]
        act = np.flatnonzero(R.max(1) > a.ref_active)
        res[Path(r).stem] = {f"mn{int(d['mn'][i])}": depth(R[i].astype(float), a.ref_dt_ms / 1000, None) for i in act}
    for t in a.traces:
        d = np.load(t)
        pr, names = d["pool_rate"], [str(s) for s in d["pool_names"]]
        out = {}
        for j, nm in enumerate(names):
            x = pr[a.t0:a.t1, j].astype(float)
            if x.sum() >= a.min_total:
                out[nm] = depth(x, 1e-3, a.min_spikes)
                out[nm]["depth_floor2"] = depth(x, 1e-3, 2.0)["depth"]
                out[nm]["depth_floor5"] = depth(x, 1e-3, 5.0)["depth"]
                rb = pr[a.b0:a.b1, j].sum() / max(a.b1 - a.b0, 1)
                rd = x.sum() / max(a.t1 - a.t0, 1)
                out[nm]["drive_ratio"] = round(float(rd / rb), 2) if rb > 0 else None   # None: silent before drive
                out[nm]["counts"] = bool(rb == 0 or rd / rb >= 2.0)
        res[Path(t).stem] = out
    for k, v in res.items():
        print(k)
        for nm, s in sorted(v.items(), key=lambda kv: -kv[1]["depth"]):
            print(f"  {nm:40s} f0 {s['f0_hz']}  depth {s['depth']}  per_cycle {s['per_cycle']}  "
                  f"floor {s['frac_cycles_floor']}  d2/d5 {s.get('depth_floor2')}/{s.get('depth_floor5')}  drive_ratio {s.get('drive_ratio')}  counts {s.get('counts', '-')}")
    if a.out:
        Path(a.out).write_text(json.dumps(res, indent=1))


if __name__ == "__main__":
    main()
