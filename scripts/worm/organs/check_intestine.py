"""Row 14 unit check: the isolated intestine (20 Li-Rinzel cells, IP3, INX-16), against Espelt et al. 2005.

Bar (night file, written before the run): period 45-52 s (consistency: a2 is fitted on the int9 cell); the wave
starts in int9 and ring peak times run posterior to anterior in >= 7 of 8 ring steps; velocity int9 -> int2 within
20-60 um/s; itr-1 null (IP3R flux 0) leaves no Ca transient above 10 % of the wild-type amplitude in 600 s.
Reported: rise / fall time (Espelt 8 +- 1 s, 23 +- 3 s), cleft pH minimum and its lag after the int9 Ca peak.

8 Nov 2026 (wbody2, item 3; class E, the check was wrong): the bar above was scored on the first wave only, so a
model whose later waves fail passed. Added, bar written before re-running: EVERY wave in the 600 s (each int9
transient after the first) must reach int2 with >= 7 of 8 ordered ring steps and 20-60 um/s, and ring 2 (anterior)
must have the same number of transients as ring 9 (1:1 propagation). Wild type is regular: defecation cycle CV 5.5 %
(Kwan et al. 2008, PMC2409367), and the wave is the cycle's trigger, so a skipped wave would be a skipped cycle.

    python scripts/worm/organs/check_intestine.py [out.json]
"""
import json
import sys

import numpy as np

from wormemu.mech import organs_intestine as I

T_S, DT_MS = 600.0, 0.5


def ring_mean(C):
    return np.stack([C[:, I.RING == r].mean(1) for r in range(1, 10)], 1)        # (steps, 9), ring 1..9


def crossings(t, x, thr):
    k = np.flatnonzero((x[1:] >= thr) & (x[:-1] < thr)) + 1
    return t[k]


def main(out=None):
    q = I.defaults()
    t, C, ph, po = I.run_isolated(q, T_S, DT_MS)
    R = ring_mean(C)
    rest = float(np.median(R[:, 0][t > 60]))
    amp = float(R[:, 8].max() - R[:, 8].min())
    thr = R[:, 8].min() + 0.5 * amp
    up9 = crossings(t, R[:, 8], thr)
    period = float(np.diff(up9[1:]).mean()) if len(up9) > 2 else float("nan")
    waves = []
    for t0 in up9[1:]:
        tr = []
        for r in range(9):
            u = crossings(t, R[:, r], thr)
            u = u[(u >= t0 - 5.0) & (u < t0 + 40.0)]
            tr.append(float(u[0]) if len(u) else float("nan"))
        waves.append(tr)
    waves = np.array(waves)
    w = waves[0] if len(waves) else np.full(9, np.nan)
    steps = int(np.sum(w[:-1] > w[1:]))                 # ring k-1 later than ring k, k = 9..2
    vel = (7 * q["int_ring_length_um"]) / (w[1] - w[8]) if np.isfinite(w[1]) else float("nan")
    each = []                                           # every wave, scored as the first one is
    for wk in waves:
        sk = int(np.sum(wk[:-1] > wk[1:]))
        vk = (7 * q["int_ring_length_um"]) / (wk[1] - wk[8]) if np.isfinite(wk[1]) and wk[1] > wk[8] else float("nan")
        each.append(dict(steps=sk, velocity_um_s=float(vk), reaches_int2=bool(np.isfinite(wk[1])),
                         ok=bool(np.isfinite(wk[1]) and sk >= 7 and 20 <= vk <= 60)))
    n_ring = [int(len(crossings(t, R[:, r], thr))) for r in range(9)]
    # rise and fall of int9 around its second transient
    x9 = R[:, 8]
    k0 = np.searchsorted(t, up9[1]) if len(up9) > 1 else 0
    seg = slice(max(k0 - int(20 / (t[1] - t[0])), 0), k0 + int(45 / (t[1] - t[0])))
    ts, xs = t[seg], x9[seg]
    lo, hi = xs.min(), xs.max()
    kp = int(np.argmax(xs))
    r10 = ts[:kp][xs[:kp] <= lo + 0.1 * (hi - lo)]
    r90 = ts[:kp][xs[:kp] <= lo + 0.9 * (hi - lo)]
    rise = float(r90[-1] - r10[-1]) if len(r10) and len(r90) else float("nan")
    f90 = ts[kp:][xs[kp:] <= lo + 0.9 * (hi - lo)]
    f10 = ts[kp:][xs[kp:] <= lo + 0.1 * (hi - lo)]
    fall = float(f10[0] - f90[0]) if len(f10) and len(f90) else float("nan")
    t_peak9 = float(ts[kp])
    win = (t >= t_peak9 - 5) & (t < t_peak9 + 15)
    ph_min = float(ph[win].min())
    ph_lag = float(t[win][np.argmin(ph[win])] - t_peak9)
    po_max = float(po[win].max())
    _, Cn, _, _ = I.run_isolated(q, T_S, DT_MS, ip3r=0.0)
    null_amp = float((Cn[t > 5] - Cn[t > 5].min(0)).max())
    res = dict(period_s=period, n_transients=int(len(up9)), rest_uM=rest, amp_uM=amp, wave_ring_times_s=w.tolist(),
               ring_steps_posterior_to_anterior=steps, velocity_um_s=float(vel), rise_s=rise, fall_s=fall,
               cleft_ph_min=ph_min, cleft_ph_lag_s=ph_lag, pbo5_open_max=po_max, null_max_transient_uM=null_amp,
               null_frac=null_amp / amp if amp > 0 else float("nan"),
               all_waves=waves.tolist(), each_wave=each, transients_per_ring=n_ring,
               waves_ok=int(sum(e["ok"] for e in each)), n_waves=len(each))
    ok = dict(period=45 <= period <= 52, order=steps >= 7 and np.nanargmin(w) == 8, velocity=20 <= vel <= 60,
              falsifier=res["null_frac"] < 0.1, every_wave=len(each) > 0 and all(e["ok"] for e in each),
              one_to_one=n_ring[1] == n_ring[8])
    res["pass"] = {k: bool(v) for k, v in ok.items()}
    res["PASS"] = bool(all(ok.values()))
    print(json.dumps({k: v for k, v in res.items() if k not in ("all_waves", "each_wave")}, indent=1))
    if out:
        with open(out, "w") as f:
            json.dump(res, f, indent=1)
    return res


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else None)
