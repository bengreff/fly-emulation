"""Item 5 probe (wbody2, 8 Nov 2026): is there an in-range set of the Du/Crodelle 2025 muscle values that passes the
paper's current-step check AND is nearly silent with no input, as a muscle without synaptic drive is? Diagnostic only:
the numpy reference (muscle_bwm.DuMuscle, the paper's integrator, dt 0.1 ms), nothing adopted (class D if a set
passes; a refit needs the gate and Ben's go).

Why comparable at the cell level: Gao & Zhen 2011 (PNAS 108:2557, PMC3038695) and Du et al. 2025 (same lab, dissected,
ventral cord kept) record spontaneous APs at 0 pA, and those are mostly synaptic: unc-13(lf) muscle fires at
0.04 +- 0.01 Hz, ACh receptor block removes about 88 % of APs (Gao & Zhen). The Du model was fitted only to 200 ms
steps of 15-30 pA; with zero input it fires on its own from about 1.5 s (19 spikes in 5 s, muscle_bwm's note).

Bar (written before running). Each value drawn inside its registered range in muscle_bwm.SPECS (log-uniform for
positive ranges spanning 2x or more, uniform otherwise; bwm_du_input_scale fixed, it is the protocol's seal factor);
set 0 = the defaults. Pass = all of
  (a) the check_bwm_du.py bar: AP count (0 mV up-crossings) within 1 of the recording at each of 30, 25, 20, 15 pA,
      mean V before the step within -31 +- 5 mV, peak above 20 mV at each amplitude;
  (b) zero input for 20 s from the code's initial state: at most 1 AP in the last 15 s (<= 0.067 Hz; unc-13(lf)
      0.04 +- 0.01 Hz, Gao & Zhen 2011);
  (c) zero input: mean V over the last 5 s within -36 to -20 mV (Du's own 8 wild-type cells, mean V of 0 pA traces,
      -25.5 to -29.1 mV, data/WT_exp_rest.npy; Gao & Zhen rest -25.0 +- 1.0 mV, n = 27; the check's -31 +- 5).
Screen (a) on all sets, run (b, c) on the sets that pass (a).

Usage: python bwm_rest_probe.py [N=2000] [seed=0] [data=PATH to the Du repo's data/spikes.npy]
-> runs/worm/wbody2/bwm_rest_probe[_sSEED].json
"""
from __future__ import annotations

import json
import sys
import time
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "src"))
from wormemu.mech import muscle_bwm as mb  # noqa: E402

AMPS = (30.0, 25.0, 20.0, 15.0)
FIXED = {"bwm_du_input_scale"}
DT = 0.1


def ranges():
    return {s.id: (float(s.lo), float(s.hi)) for s in mb.SPECS if s.id.startswith("bwm_du_") and s.id not in FIXED}


def draw(n, seed):
    rg = np.random.default_rng(seed)
    q0 = {s.id: float(s.template) for s in mb.SPECS}
    out = {}
    for k, (lo, hi) in ranges().items():
        u = rg.random(n)
        x = np.exp(np.log(lo) + u * np.log(hi / lo)) if lo > 0 and hi / lo >= 2 else lo + u * (hi - lo)
        x[0] = q0[k]
        out[k] = x
    return out


def step_screen(P, rec_counts):
    """(a) for every set: the paper's protocol, the 4 amplitudes side by side (n x 4 cells)."""
    n = len(next(iter(P.values())))
    Q = {k: np.repeat(v, len(AMPS)) for k, v in P.items()}
    m = mb.DuMuscle(n * len(AMPS), Q)
    amps = np.tile(np.asarray(AMPS) / m.q["bwm_du_input_scale"], n)
    nt = int(round(500.0 / DT))
    pre, peak, spk = np.zeros(n * 4), np.full(n * 4, -1e9), np.zeros(n * 4, int)
    npre, prev = 0, m.V.copy()
    for k in range(nt):
        t = k * DT
        V = m.step(np.where((t >= 57.8) & (t < 257.8), amps, 0.0), DT)
        if t < 57:
            pre += V
            npre += 1
        peak = np.maximum(peak, V)
        spk += (prev < 0) & (V >= 0)
        prev = V.copy()
    pre /= npre
    spk, pre, peak = spk.reshape(n, 4), pre.reshape(n, 4), peak.reshape(n, 4)
    ok = (np.abs(spk - np.asarray(rec_counts)) <= 1).all(1) & (np.abs(pre + 31) <= 5).all(1) & (peak > 20).all(1)
    return ok, spk, pre, peak


def zero_input(P, idx, secs=20.0):
    """(b, c) for the sets idx: APs in the last 15 s, mean V over the last 5 s, from the code's initial state."""
    Q = {k: v[idx] for k, v in P.items()}
    m = mb.DuMuscle(len(idx), Q)
    nt = int(round(secs * 1000 / DT))
    zero = np.zeros(len(idx))
    spk, vsum, nv, prev = np.zeros(len(idx), int), np.zeros(len(idx)), 0, m.V.copy()
    vmin, vmax = np.full(len(idx), 1e9), np.full(len(idx), -1e9)
    for k in range(nt):
        V = m.step(zero, DT)
        t = k * DT / 1000.0
        if t >= secs - 15.0:
            spk += (prev < 0) & (V >= 0)
            vmin, vmax = np.minimum(vmin, V), np.maximum(vmax, V)
        if t >= secs - 5.0:
            vsum += V
            nv += 1
        prev = V.copy()
    vmean = vsum / nv
    ok = (spk <= 1) & (vmean >= -36) & (vmean <= -20)
    return ok, spk, vmean, vmin, vmax


def main():
    kw = dict(a.split("=", 1) for a in sys.argv[1:])
    n, seed = int(kw.get("N", 2000)), int(kw.get("seed", 0))
    data = kw.get("data", "/tmp/worgans/C.elegans-Muscle/data/spikes.npy")
    rec = np.load(data)
    rec_counts = [mb.upcrossings(rec[:, i]) for i in range(len(AMPS))]
    P, t0 = draw(n, seed), time.time()
    ok_a, spk, pre, peak = step_screen(P, rec_counts)
    t_a = time.time() - t0
    idx = np.flatnonzero(ok_a)
    if 0 not in idx:
        idx = np.r_[0, idx]                          # always run the defaults through (b, c) for the record
    ok_bc, zs, zv, zmin, zmax = zero_input(P, idx)
    rows = []
    for j, i in enumerate(idx):
        rows.append(dict(set=int(i), values={k: float(P[k][i]) for k in P}, step_spikes=spk[i].tolist(),
                         pre_mV=pre[i].round(2).tolist(), peak_mV=peak[i].round(1).tolist(), pass_a=bool(ok_a[i]),
                         zero_spikes_last15s=int(zs[j]), zero_rate_hz=float(zs[j]) / 15.0,
                         zero_vmean_last5s=float(zv[j]), zero_vmin=float(zmin[j]), zero_vmax=float(zmax[j]),
                         pass_bc=bool(ok_bc[j]), ok=bool(ok_a[i] and ok_bc[j])))
    passing = [r for r in rows if r["ok"]]
    a_only = [r for r in rows if r["pass_a"]]
    res = dict(bar=__doc__.split("Bar (written before running). ")[1].split("\n\nUsage")[0], N=n, seed=seed,
               recording_counts=rec_counts, ranges=ranges(), n_pass_a=int(ok_a.sum()), n_pass_all=len(passing),
               verdict=("D: an in-range set passes the step check and is silent at rest" if passing
                        else "no in-range set passes (a) and (b, c)"),
               defaults=rows[0], zero_rate_hz_of_a_passers=dict(
                   min=min((r["zero_rate_hz"] for r in a_only), default=None),
                   median=float(np.median([r["zero_rate_hz"] for r in a_only])) if a_only else None),
               passing=passing[:20], closest=sorted(a_only, key=lambda r: (r["zero_spikes_last15s"],
                                                                          abs(r["zero_vmean_last5s"] + 27)))[:10],
               wall_a_s=t_a, wall_s=time.time() - t0)
    out = ROOT / f"runs/worm/wbody2/bwm_rest_probe{'_s' + str(seed) if seed else ''}.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(res, indent=1, default=float))
    print(json.dumps({k: v for k, v in res.items() if k not in ("bar", "ranges", "passing", "closest")}, indent=1,
                     default=float))


if __name__ == "__main__":
    main()
