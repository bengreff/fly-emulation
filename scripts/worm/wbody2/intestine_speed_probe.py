"""Row 3 wave, diagnostic (wbody2, 9 Nov 2026): what INX-16 coupling does the diffusive form need for the intact worm's
wave? Nothing here is adopted; values outside the registered ranges never are (they would need a source).

Why: check_intestine.py's velocity bar is now the behaving worm's 200-480 um/s (Peters et al. 2007: 340 +- 140 um/s,
n 10), not the dissected intestine's 20-60 um/s (Espelt et al. 2005: 33 +- 3 um/s). The model's junctions exchange
IP3 and Ca at P / L per s (int_gap_p_ip3_um_s 2.0, range 0.1-10; int_gap_p_ca_um_s 0.5, range 0-5; L 80 um; all
guessed; no INX-16 permeability is published, lit_int_wave.md).

Written 9 Nov 03:53 CST, before running. Grid: P_ip3 in {2, 10, 30, 100, 300, 1000, 3000} um/s x P_ca in {0.5, 5, 50,
500} um/s, every other value at its default; the isolated intestine for 600 s, vectorised at dt 1 ms (stable: the
largest exchange rate 37.5 /s), scored with check_intestine's rules (intestine_wave_probe.score, band intact).
Expectation stated first: inside the registered ranges (P_ip3 <= 10, P_ca <= 5) no set reaches 200 um/s, and the form
needs couplings well outside them. Reported per set: period, median velocity over the waves, waves reaching ring 2 in
order, waves passing, transients per ring. The lowest-coupling sets that pass on the screen are re-run at 0.5 ms with
check_intestine's own path (run_isolated) and scored the same way (at most 4).

Result (03:56, screen at 1 ms): 0 of 28 pass. Inside the ranges the median velocity is 15-33 um/s. Median
velocities of 100-560 um/s, with all waves but at most one in order, come only with P_ca >= 50 um/s (100x its
default, 10x its range top) or P_ip3 >= 100 um/s (50x, 10x); the period there is 64.7-67.6 s (bar 45-52 s).

mode=joint, written 9 Nov 03:58 CST before running: can the period come back with the coupling that gives the speed?
Every screen set with a median velocity in 120-600 um/s ((10, 50), (30, 50), (100, 5), (100, 50),
(300, 0.5), (300, 5) um/s) x 200 draws each of the other 7 free values (intestine_wave_probe.FREE less the two
permeabilities, uniform or log-uniform inside their registered ranges, seed 1); dt 5 ms (largest exchange rate 3.75 /s);
check_intestine's full scoring, band intact. Pass counts per coupling set reported; passing sets (at most 4) re-run at
0.5 ms. Expectation stated first: none pass, because the in-range a2 and IP3 values cannot shorten a coupled gut's
period by 15-20 s. Diagnostic only, never adopted.

Usage: python intestine_speed_probe.py [mode=grid|joint] -> runs/worm/wbody2/intestine_speed_probe[_joint].json
"""
from __future__ import annotations

import json
import sys
import time
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
import intestine_wave_probe as W  # noqa: E402

I = W.I
P_IP3 = (2.0, 10.0, 30.0, 100.0, 300.0, 1000.0, 3000.0)
P_CA = (0.5, 5.0, 50.0, 500.0)


JOINT = ((10.0, 50.0), (30.0, 50.0), (100.0, 5.0), (100.0, 50.0), (300.0, 0.5), (300.0, 5.0))


def joint(per=200, seed=1):
    t0 = time.time()
    free = [k for k in W.FREE if k not in ("int_gap_p_ip3_um_s", "int_gap_p_ca_um_s")]
    D = W.draw(per * len(JOINT), seed)
    P = {k: D[k] for k in free}
    P["int_gap_p_ip3_um_s"] = np.repeat([a for a, _ in JOINT], per).astype(float)
    P["int_gap_p_ca_um_s"] = np.repeat([b for _, b in JOINT], per).astype(float)
    R = W.run_batch(P, 0.005)
    t = (np.arange(R.shape[0]) + 1) * W.REC_S
    rows = []
    for i in range(len(P["int_gap_p_ca_um_s"])):
        s = W.score(t, R[:, i, :].astype(float), float(P["int_ring_length_um"][i]))
        rows.append(dict(values={k: float(P[k][i]) for k in P}, **s))
    passing = [r for r in rows if r["ok"]]
    confirmed = []
    for r in passing[:4]:
        q = I.defaults()
        q.update(r["values"])
        tt, C, _, _ = I.run_isolated(q, W.T_S, 0.5)
        Rr = np.stack([C[:, I.RING == k].mean(1) for k in range(1, 10)], 1)
        confirmed.append(dict(values=r["values"], **W.score(tt, Rr, r["values"]["int_ring_length_um"])))
    per_set = []
    for a, b in JOINT:
        rs = [r for r in rows if r["values"]["int_gap_p_ip3_um_s"] == a and r["values"]["int_gap_p_ca_um_s"] == b]
        pr = np.array([r["period_s"] for r in rs], float)
        per_set.append(dict(p_ip3_um_s=a, p_ca_um_s=b, n=len(rs), n_pass=sum(r["ok"] for r in rs),
                            n_period_ok=sum(bool(r["parts"]["period"]) for r in rs if "parts" in r),
                            n_every_wave_ok=sum(bool(r["parts"]["every_wave"]) for r in rs if "parts" in r),
                            period_min_s=float(np.nanmin(pr)) if np.isfinite(pr).any() else float("nan"),
                            period_median_s=float(np.nanmedian(pr)) if np.isfinite(pr).any() else float("nan")))
    best = sorted([r for r in rows if np.isfinite(r["period_s"])], key=lambda r: abs(r["period_s"] - 48.5))[:15]
    res = dict(bar=__doc__.split("mode=joint, written 9 Nov 03:58 CST before running: ")[1].split("\n\nUsage")[0],
               band_um_s=list(W.BANDS["intact"]), dt_screen_ms=5.0, per_set=per_set, n_pass_screen=len(passing),
               confirmed_0p5ms=confirmed, best=best, wall_s=time.time() - t0, all_rows=rows)
    (W.ROOT / "runs/worm/wbody2/intestine_speed_probe_joint.json").write_text(json.dumps(res, indent=1, default=float))
    for x in per_set:
        print(x)
    for r in best[:6]:
        print(r)
    print(json.dumps({k: res[k] for k in ("n_pass_screen", "confirmed_0p5ms", "wall_s")}, default=float))


def main():
    if dict(a.split("=", 1) for a in sys.argv[1:]).get("mode", "grid") == "joint":
        return joint()
    t0 = time.time()
    grid = [(a, b) for a in P_IP3 for b in P_CA]
    P = {"int_gap_p_ip3_um_s": np.array([a for a, _ in grid]), "int_gap_p_ca_um_s": np.array([b for _, b in grid])}
    R = W.run_batch(P, 0.001)
    t = (np.arange(R.shape[0]) + 1) * W.REC_S
    L = float(I.defaults()["int_ring_length_um"])
    rows = []
    for i, (a, b) in enumerate(grid):
        s = W.score(t, R[:, i, :].astype(float), L)
        rows.append(dict(p_ip3_um_s=a, p_ca_um_s=b, in_range=bool(a <= 10.0 and b <= 5.0), **s))
    screen_s = time.time() - t0
    passing = sorted([r for r in rows if r["ok"]], key=lambda r: (r["p_ip3_um_s"] + r["p_ca_um_s"]))
    confirmed = []
    for r in passing[:4]:
        q = I.defaults()
        q.update(int_gap_p_ip3_um_s=r["p_ip3_um_s"], int_gap_p_ca_um_s=r["p_ca_um_s"])
        tt, C, _, _ = I.run_isolated(q, W.T_S, 0.5)
        Rr = np.stack([C[:, I.RING == k].mean(1) for k in range(1, 10)], 1)
        confirmed.append(dict(p_ip3_um_s=r["p_ip3_um_s"], p_ca_um_s=r["p_ca_um_s"], **W.score(tt, Rr, L)))
    res = dict(bar=__doc__.split("Written 9 Nov 03:53 CST, before running. ")[1].split("\n\nResult")[0],
               band_um_s=list(W.BANDS["intact"]), dt_screen_ms=1.0, rows=rows, n_pass_screen=len(passing),
               n_pass_in_range=sum(r["ok"] for r in rows if r["in_range"]), confirmed_0p5ms=confirmed,
               screen_wall_s=screen_s, wall_s=time.time() - t0)
    out = W.ROOT / "runs/worm/wbody2/intestine_speed_probe.json"
    out.write_text(json.dumps(res, indent=1, default=float))
    for r in rows:
        print(r["p_ip3_um_s"], r["p_ca_um_s"], r["ok"], round(r["period_s"], 2) if np.isfinite(r["period_s"]) else None,
              r.get("velocity_median_um_s"), r.get("waves_in_order"), r.get("n_waves"), r.get("transients_per_ring"))
    print(json.dumps({k: v for k, v in res.items() if k not in ("rows", "bar")}, indent=1, default=float))


if __name__ == "__main__":
    main()
