"""Item 3 probe (wbody2, 8 Nov 2026): is there an in-range set of the intestine's fitted and guessed values whose Ca
waves ALL reach the anterior end, one wave per int9 cycle? Diagnostic only: nothing here is adopted (class D if a
set passes; a refit needs the gate and Ben's go).

Why: check_intestine.py scored only the first wave. Scored on every wave (8 Nov), the defaults fail: 1 of 11 waves
passes; int9 fires 12 times in 600 s, int2 10, int1 9 (measured). Inferred mechanism: every cell's IP3R recovers
from Ca inactivation with tau_h = 1 / (a2 (Q2 + c)), about 60 s at rest (derived: a2 0.034, Q2 0.39, c 0.1); int9's
higher IP3 lets it fire at partial recovery every 49 s, the anterior cells' lower IP3 needs more, so they skip.

Bar (written before running; the 8 Nov check bar): on the isolated intestine for 600 s, period of ring 9 in 45-52 s,
every wave after the first reaches ring 2 with >= 7 of 8 ordered ring steps and velocity 20-60 um/s, ring 2 has as
many transients as ring 9. Each value drawn uniformly (log-uniform for the rates) inside its registered range in
organs_intestine.SPECS. Screen at dt 5 ms (the original fit's grid; the defaults give 50.1 s there vs 49.3 s at
0.5 ms), confirm passing sets at 0.5 ms with check_intestine's own scoring.

Usage: python intestine_wave_probe.py [N=400] [seed=0]  -> runs/worm/wbody2/intestine_wave_probe.json
"""
from __future__ import annotations

import json
import sys
import time
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "scripts" / "worm" / "organs"))
from wormemu.mech import organs_intestine as I  # noqa: E402

FREE = ["int_lr_a2_per_uM_s", "int_ip3_rest_uM", "int_ip3_rest_pacemaker_uM", "int_ip3_tau_s", "int_plc_ca_uM_per_s",
        "int_plc_ca_k_uM", "int_gap_p_ip3_um_s", "int_gap_p_ca_um_s", "int_ring_length_um"]
LOG = {"int_lr_a2_per_uM_s", "int_ip3_tau_s", "int_gap_p_ip3_um_s"}
T_S, REC_S = 600.0, 0.1


def ranges():
    by = {s.id: s for s in I.SPECS}
    return {k: (float(by[k].lo), float(by[k].hi)) for k in FREE}


def draw(n, seed):
    rg, q0 = np.random.default_rng(seed), I.defaults()
    out = {k: np.full(n, float(q0[k])) for k in FREE}
    for k, (lo, hi) in ranges().items():
        u = rg.random(n)
        x = np.exp(np.log(lo) + u * (np.log(hi) - np.log(lo))) if k in LOG and lo > 0 else lo + u * (hi - lo)
        out[k][1:] = x[1:]                                     # set 0 = the defaults
    return out


def run_batch(P, dt_s):
    """The organs_intestine.Intestine equations, vectorised over parameter sets (rows). Returns ring means (t, n, 9)."""
    q, n = I.defaults(), len(next(iter(P.values())))
    g = {k: (P[k][:, None] if k in P else float(q[k])) for k in set(q) | set(P)}
    cells = I.Intestine(q)
    L, pace = cells.L, (I.RING == 9)[None, :]
    p_rest = np.where(pace, g["int_ip3_rest_pacemaker_uM"], g["int_ip3_rest_uM"]) * np.ones((n, 1))
    c = np.full((n, len(I.INT_CELLS)), float(q["int_ca_rest_uM"]))
    p = p_rest.copy()
    h = g["int_lr_d2_uM"] * (p + g["int_lr_d1_uM"]) / (p + g["int_lr_d3_uM"])
    h = h / (h + c)
    c0, c1 = g["int_lr_c0_uM"], g["int_lr_c1"]
    d1, d2, d3, d5 = g["int_lr_d1_uM"], g["int_lr_d2_uM"], g["int_lr_d3_uM"], g["int_lr_d5_uM"]
    k_ip3, k_ca = g["int_gap_p_ip3_um_s"] / g["int_ring_length_um"], g["int_gap_p_ca_um_s"] / g["int_ring_length_um"]
    a2, tau, kk, hn = g["int_lr_a2_per_uM_s"], g["int_ip3_tau_s"], g["int_plc_ca_k_uM"], g["int_plc_ca_hill"]
    base = I._hill(float(q["int_ca_rest_uM"]), kk, hn)
    M = np.stack([(I.RING == r) / (I.RING == r).sum() for r in range(1, 10)], 1)          # (20, 9) ring means
    every = int(round(REC_S / dt_s))
    rec = np.empty((int(T_S / REC_S), n, 9), np.float32)
    for s in range(int(round(T_S / dt_s))):
        cer = (c0 - c) / c1
        j_chan = c1 * g["int_lr_v1_per_s"] * (p / (p + d1) * c / (c + d5) * h) ** 3 * (c - cer)
        j_pump = g["int_lr_v3_uM_per_s"] * c * c / (g["int_lr_k3_uM"] ** 2 + c * c)
        j_leak = c1 * g["int_lr_v2_per_s"] * (c - cer)
        q2 = d2 * (p + d1) / (p + d3)
        plc = p_rest / tau + g["int_plc_ca_uM_per_s"] * (I._hill(c, kk, hn) - base)
        dc = -j_chan - j_pump - j_leak + k_ca * (c @ L.T)
        dh = a2 * q2 * (1.0 - h) - a2 * c * h
        dp = plc - p / tau + k_ip3 * (p @ L.T)
        c = np.maximum(c + dt_s * dc, 0.0)
        h = np.clip(h + dt_s * dh, 0.0, 1.0)
        p = np.maximum(p + dt_s * dp, 0.0)
        if (s + 1) % every == 0:
            rec[(s + 1) // every - 1] = c @ M
    return rec


def crossings(t, x, thr):
    k = np.flatnonzero((x[1:] >= thr) & (x[:-1] < thr)) + 1
    return t[k]


def score(t, R, ring_len):
    """check_intestine.py's scoring (8 Nov form) on one set's ring means R (t, 9)."""
    amp = float(R[:, 8].max() - R[:, 8].min())
    if not np.isfinite(amp) or amp < 0.05:
        return dict(ok=False, why="no int9 transient", period_s=float("nan"))
    thr = R[:, 8].min() + 0.5 * amp
    up9 = crossings(t, R[:, 8], thr)
    period = float(np.diff(up9[1:]).mean()) if len(up9) > 2 else float("nan")
    n_ring = [int(len(crossings(t, R[:, r], thr))) for r in range(9)]
    each = []
    for t0 in up9[1:]:
        w = []
        for r in range(9):
            u = crossings(t, R[:, r], thr)
            u = u[(u >= t0 - 5.0) & (u < t0 + 40.0)]
            w.append(float(u[0]) if len(u) else float("nan"))
        w = np.array(w)
        sk = int(np.sum(w[:-1] > w[1:]))
        vk = 7 * ring_len / (w[1] - w[8]) if np.isfinite(w[1]) and w[1] > w[8] else float("nan")
        each.append(bool(np.isfinite(w[1]) and sk >= 7 and 20 <= vk <= 60))
    ok = dict(period=45 <= period <= 52, every_wave=len(each) > 0 and all(each), one_to_one=n_ring[1] == n_ring[8])
    return dict(ok=all(ok.values()), period_s=period, waves_ok=int(sum(each)), n_waves=len(each),
                transients_per_ring=n_ring, parts=ok)


def main():
    kw = dict(a.split("=", 1) for a in sys.argv[1:])
    n, seed = int(kw.get("N", 400)), int(kw.get("seed", 0))
    P, t0 = draw(n, seed), time.time()
    R = run_batch(P, 0.005)
    t = (np.arange(R.shape[0]) + 1) * REC_S
    rows = []
    for i in range(n):
        s = score(t, R[:, i, :].astype(float), float(P["int_ring_length_um"][i]))
        rows.append(dict(values={k: float(P[k][i]) for k in FREE}, **s))
    screen_s = time.time() - t0
    passing = [r for r in rows if r["ok"]]
    confirmed = []
    for r in passing[:10]:                                     # confirm at 0.5 ms with the check's own run path
        q = I.defaults()
        q.update(r["values"])
        tt, C, _, _ = I.run_isolated(q, T_S, 0.5)
        Rr = np.stack([C[:, I.RING == k].mean(1) for k in range(1, 10)], 1)
        confirmed.append(dict(values=r["values"], **score(tt, Rr, r["values"]["int_ring_length_um"])))
    best = sorted(rows, key=lambda r: (-(r.get("waves_ok", 0) / max(r.get("n_waves", 1), 1)),
                                       abs((r["period_s"] if np.isfinite(r["period_s"]) else 1e9) - 48.5)))[:15]
    res = dict(bar=__doc__.split("Bar (written before running; the 8 Nov check bar): ")[1].split("\n\nUsage")[0],
               N=n, seed=seed, ranges=ranges(), dt_screen_ms=5.0, defaults=rows[0], n_pass_screen=len(passing),
               confirmed_0p5ms=confirmed, n_confirmed=sum(c["ok"] for c in confirmed),
               verdict=("D: an in-range set passes at 0.5 ms" if any(c["ok"] for c in confirmed)
                        else "no in-range set passes"), best=best, screen_wall_s=screen_s, wall_s=time.time() - t0,
               all_rows=rows)
    out = ROOT / f"runs/worm/wbody2/intestine_wave_probe{'_s' + str(seed) if seed else ''}.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(res, indent=1, default=float))
    print(json.dumps({k: v for k, v in res.items() if k not in ("all_rows", "best", "ranges", "bar")}, indent=1,
                     default=float))
    for r in best[:8]:
        print(r)


if __name__ == "__main__":
    main()
