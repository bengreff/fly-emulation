"""s23 N25 night input (DECISIONS 23 Oct, s23 N25 entry): mode 1 plus the clock's DN1 drive on the dFB OFF rate,
k_off (1 + light_arousal Lsat + night_arousal D(CT)), D peaking at CT 19 (Liang 2016 DN1 Ca2+ peak). The reduced
loop and checks of s21_n25_homeostat.py; k_r at its measured centre. Training data only (Garbe 2015 day and night
bouts, Abhilash & Shafer band, Liu 2016 anchors); Chowdhury 2023 stays unopened.

    .venv/bin/python scripts/probes/s23_n25_night.py unit             # U4 -> runs/s23/n25/unit.json
    .venv/bin/python scripts/probes/s23_n25_night.py fit --procs 3    # grid -> runs/s23/n25/fit.json
    .venv/bin/python scripts/probes/s23_n25_night.py predict          # candidate, 2048 flies -> predict.json
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import time
from itertools import product
from pathlib import Path

for _v in ("OMP_NUM_THREADS", "MKL_NUM_THREADS", "OPENBLAS_NUM_THREADS"):
    os.environ.setdefault(_v, "1")

import numpy as np  # noqa: E402

sys.path.insert(0, str(Path(__file__).resolve().parent))
import s21_n25_homeostat as h  # noqa: E402

OUT = Path("runs/s23/n25")
GRID = {"need_tau_rise_h": [2, 3, 4, 6, 8, 12, 18, 24, 36, 48],
        "need_gain": [0, 0.25, 0.5, 1, 2, 4, 8, 16, 32, 64, 100],
        "dfb_koff_per_min": [float(x) for x in np.round(np.geomspace(0.001, 0.9, 12), 5)[:7]],
        "light_arousal": [1, 2, 4, 8, 16, 20],
        "night_arousal": [0, 0.5, 1, 2, 4, 8, 16]}
# Garbe et al. 2015 (SB DAM, iso31 males, own figure read; F-S22-1, F-S22-2): mean +- 1 s.d.
GARBE = {"bouts_night": (2.8, 11.2), "bout_len_night": (43.0, 183.0),
         "bouts_day": (5.4, 12.0), "bout_len_day": (32.0, 82.0)}


def unit() -> dict:
    """U4: the vectorised loop against the Organs class with the night term on (U3's rule: daily sleep within
    3 combined SE), plus D(CT) at its peak and trough."""
    from flyemu.internal_state import night_drive
    p = h.base_params(need_tau_rise_h=8.0, need_gain=3.0, dfb_koff_per_min=0.01, light_arousal=2.0,
                      night_arousal=4.0)
    v = h.sim(p, flies=200, burn_days=3, days=2, seed=3)
    vt = h.day_table(h.dam_sleep(v["inact"], v["run0"]), 2)
    org = h.organs_loop(p, flies=60, burn_days=3, days=2)
    res = {"D_peak": float(night_drive(19.0, 19.0)), "D_trough": float(night_drive(7.0, 19.0)),
           "U4_vector": {k: [round(float(vt[d][k][0]), 1) for d in range(2)] for k in
                         ("total_min", "day_min", "night_min")},
           "U4_organs": org}
    se = float(np.hypot(vt[0]["total_sd"][0] / np.sqrt(200), org["total_sd"] / np.sqrt(60)))
    diff = float(np.mean([vt[d]["total_min"][0] for d in range(2)]) - np.mean(org["total_min"]))
    res["U4_diff_min"], res["U4_se_min"] = round(diff, 1), round(se, 1)
    res["U4_pass"] = bool(abs(diff) <= 3 * se and res["D_peak"] == 1.0 and res["D_trough"] < 1e-12)
    return res


def grid_sets() -> dict:
    combos = list(product(*GRID.values()))
    return {k: np.array([c[i] for c in combos], float) for i, k in enumerate(GRID)}


def _stage1(args):
    i, s = args
    b = h.baseline(s, seed=10 + i)
    pre = ((b["total"] >= h.BAND[0]) & (b["total"] <= h.BAND[1]) & (b["night"] > b["day"])
           & (b["ratio"] >= h.RATIO_MIN))
    idx = np.flatnonzero(pre)
    bo = h.rebout({k: v[idx] for k, v in s.items()}, seed=30 + i) if len(idx) else {}
    return i, b, idx, bo


def fit(procs: int) -> dict:
    sets = grid_sets()
    m = len(sets["need_gain"])
    t0 = time.time()
    jobs = list(h.chunks(sets, 400))
    if procs > 1:
        from multiprocessing import Pool
        with Pool(procs) as pool:
            parts = pool.map(_stage1, jobs, chunksize=1)
    else:
        parts = [_stage1(j) for j in jobs]
    rows = []
    n_t124 = 0
    for i, b, idx, bo in parts:
        n_t124 += len(idx)
        for j, k in enumerate(idx):
            row = {g: float(sets[g][i + k]) for g in GRID}
            row.update({q: round(float(b[q][k]), 3) for q in ("total", "day", "night", "ratio")})
            row.update({"dam_" + q: round(float(v[j]), 3) for q, v in bo.items()})
            row["t5"] = bool(all(lo <= row["dam_" + q] <= hi for q, (lo, hi) in GARBE.items()))
            rows.append(row)
    print(f"stage 1: {m} sets, {n_t124} pass T1, T2, T4; {sum(r['t5'] for r in rows)} pass T5; "
          f"{time.time() - t0:.0f} s", flush=True)
    t5 = [r for r in rows if r["t5"]]
    if t5:
        sub = {g: np.array([r[g] for r in t5], float) for g in GRID}
        d = h.deprivation(sub)
        for j, r in enumerate(t5):
            r.update({q: round(float(v[j]), 4) for q, v in d.items()})
            e0 = r["liu_e0"]
            r["liu_pass"] = bool(e0 > 0 and r["liu_e2"] >= 0.5 * e0 and abs(r["liu_e24"]) <= 0.1 * e0)
    print(f"stage 2: {len(t5)} sets, {time.time() - t0:.0f} s", flush=True)
    acc = [r for r in t5 if r["liu_pass"]]
    out = {"n_sets": m, "grid": GRID, "garbe": GARBE, "band": h.BAND, "k_r": h.base_params()["dfb_restart_per_min"],
           "n_t124": n_t124, "n_t1245": len(t5), "n_accepted": len(acc),
           "n_t124_by_night_arousal": {str(a): sum(r["night_arousal"] == a for r in rows) for a in GRID["night_arousal"]},
           "n_t1245_by_night_arousal": {str(a): sum(r["night_arousal"] == a for r in t5) for a in GRID["night_arousal"]},
           "wall_s": round(time.time() - t0), "accepted": h.select(acc), "t124_sets": rows}
    if rows:
        out["t124_bout_ranges"] = {q: [min(r["dam_" + q] for r in rows), max(r["dam_" + q] for r in rows)]
                                   for q in GARBE}
    return out


def predict() -> dict:
    """The fit's candidate at 2048 flies (seed 500, as the s22 amended candidate): day 1-3 rebounds per arm, the
    Liu anchors, and its baseline bouts at 512 flies. Written to DECISIONS before any Chowdhury read."""
    r = json.loads((OUT / "fit.json").read_text())
    c = r["accepted"]["candidate"]
    one = {g: np.array([c[g]], float) for g in GRID}
    d = h.deprivation(one, flies=2048, seed=500)
    bo = h.rebout(one, flies=512, seed=600)
    return {"candidate": {g: c[g] for g in GRID}, "n_accepted": r["n_accepted"],
            "fit_medians": r["accepted"]["median"], "fit_p2.5": r["accepted"]["p2.5"],
            "fit_p97.5": r["accepted"]["p97.5"],
            "pred_2048": {k: round(float(v[0]), 2) for k, v in d.items()},
            "bouts_512": {k: round(float(v[0]), 2) for k, v in bo.items()}}


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("mode", choices=["unit", "fit", "predict"])
    ap.add_argument("--procs", type=int, default=1)
    a = ap.parse_args()
    OUT.mkdir(parents=True, exist_ok=True)
    res = unit() if a.mode == "unit" else fit(a.procs) if a.mode == "fit" else predict()
    (OUT / f"{a.mode}.json").write_text(json.dumps(res, indent=1))
    print(json.dumps({k: v for k, v in res.items() if k != "t124_sets"}, indent=1)[:4000])
