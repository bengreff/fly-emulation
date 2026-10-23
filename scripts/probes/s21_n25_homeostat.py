"""s21 N25 homeostat mode 1 (state:sleep|homeostat = 1), the reduced loop on the CPU (DECISIONS 23 Oct, s21).

The loop of the s20 probe, with the mode-1 state: activity is 0 while at least half the dFB cells are ON (the
switch) and 1 otherwise; deprivation forces activity 1. LD 12:12 at REAR_LUX (lights on ZT 0-12). One step is
1 min with the exact two-state transition over 60 s (Organs.step(60) takes three 20 s sub-steps; check U3
compares the two). Sleep is scored like DAM: inactivity runs of >= 5 min count whole.

Vectorised over parameter sets (axis 0) and flies (axis 1); the Organs class is the model, this is its fast copy.

    .venv/bin/python scripts/probes/s21_n25_homeostat.py unit     # U1-U3 -> runs/s21/n25/unit.json
    .venv/bin/python scripts/probes/s21_n25_homeostat.py fit      # training grid -> runs/s21/n25/fit.json
    .venv/bin/python scripts/probes/s21_n25_homeostat.py predict  # registered arms + Liu anchors -> predict.json
"""
from __future__ import annotations

import json
import sys
import time
from itertools import product
from pathlib import Path

import numpy as np

from flyemu.internal_state import (DFB_SLEEP_FRACTION, N_DFB, REAR_LUX, Organs, default_params, dfb_rates,
                                   dfb_transition)

OUT = Path("runs/s21/n25")
DAY = 1440
FIT = ("need_tau_rise_h", "need_gain", "dfb_koff_per_min", "light_arousal")


def base_params(**over) -> dict:
    p = default_params(homeostat=True)
    p["period_h"] = 24.0
    p.update(over)
    return p


def sim(p: dict, sets: dict | None = None, flies: int = 64, burn_days: int = 4, days: int = 2,
        sd: tuple[int, int] | None = None, seed: int = 0, margin: int = 60, lux: float = REAR_LUX) -> dict:
    """Simulate. `sets` maps a field to an array (one value per parameter set); other fields come from p.
    sd = (start minute counted from the first scored minute, length in minutes); may start in the burn-in
    (negative start). Returns inactivity (T, M, F) and the mean need per set (T, M) over the scored days."""
    sets = sets or {}
    m = len(next(iter(sets.values()))) if sets else 1
    q = {k: (np.asarray(sets[k], float)[:, None] if k in sets else float(v)) for k, v in p.items()
         if isinstance(v, (int, float))}
    rng = np.random.default_rng(seed)
    need = np.full((m, flies), 0.2)
    on = np.zeros((m, flies, N_DFB), bool)
    inact_s = np.zeros((m, flies))
    switch = np.zeros((m, flies), bool)
    n0 = burn_days * DAY
    n = n0 + days * DAY + margin
    rec_i = np.zeros((n - n0, m, flies), bool)
    rec_n = np.zeros((n - n0, m))
    run0 = None
    sd0 = None if sd is None else n0 + sd[0]
    sd1 = None if sd is None else sd0 + sd[1]
    lsat_on = lux / (lux + p["l50_lux"])
    for t in range(n):
        lsat = lsat_on if (t % DAY) < 720 else 0.0
        act = np.where(switch, 0.0, 1.0)
        if sd0 is not None and sd0 <= t < sd1:
            act = np.ones_like(act)
        inactive = act < p["a_rest"]
        if t == n0:
            run0 = (inact_s / 60.0).round().astype(int)          # inactive minutes carried into the window
        inact_s = np.where(inactive, inact_s + 60.0, 0.0)
        asleep = inact_s >= p["t_sleep_s"]
        tau = np.where(asleep, q["need_tau_decay_h"], q["need_tau_rise_h"]) * 3600.0
        target = np.where(asleep, 0.0, 1.0)
        need = target + (need - target) * np.exp(-60.0 / tau)
        k_on, k_off = dfb_rates(q, need, lsat)
        stay, turn = dfb_transition(k_on, k_off * np.ones_like(need), 60.0)
        u = rng.random(on.shape)
        on = np.where(on, u < stay[..., None], u < turn[..., None])
        switch = on.mean(-1) >= DFB_SLEEP_FRACTION
        if t >= n0:
            rec_i[t - n0] = inactive
            rec_n[t - n0] = need.mean(1)
    return {"inact": rec_i, "need": rec_n, "run0": run0, "days": days}


def dam_sleep(inact: np.ndarray, run0: np.ndarray, crit: int = 5) -> np.ndarray:
    """(T, ...) inactivity -> sleep: runs of >= crit minutes count whole; run0 = inactive minutes before t = 0."""
    T = inact.shape[0]
    fwd = np.zeros(inact.shape, np.int32)
    c = run0.astype(np.int32)
    for t in range(T):
        c = np.where(inact[t], c + 1, 0)
        fwd[t] = c
    out = np.zeros(inact.shape, bool)
    run = np.zeros(inact.shape[1:], np.int32)
    for t in range(T - 1, -1, -1):           # carry each run's total length backwards from its last minute
        last = ~inact[t + 1] if t + 1 < T else np.ones(inact.shape[1:], bool)
        run = np.where(inact[t], np.where(last, fwd[t], run), 0)
        out[t] = inact[t] & (run >= crit)
    return out


def day_table(sl: np.ndarray, days: int) -> dict:
    """Per set (axis 1 of sl[T, M, F]): mean over flies of day/night/total sleep and bouts per scored day."""
    res = []
    for d in range(days):
        x = sl[d * DAY:(d + 1) * DAY]
        light, dark = x[:720].sum(0), x[720:].sum(0)                       # (M, F) minutes
        starts = np.diff(np.concatenate([np.zeros((1,) + x.shape[1:], bool), x]).astype(np.int8), axis=0) == 1
        b_l, b_d = starts[:720].sum(0), starts[720:].sum(0)
        res.append({"day_min": light.mean(1), "night_min": dark.mean(1), "total_min": (light + dark).mean(1),
                    "total_sd": (light + dark).std(1), "bouts_day": b_l.mean(1), "bouts_night": b_d.mean(1),
                    "bout_len_day": light.sum(1) / np.maximum(b_l.sum(1), 1),
                    "bout_len_night": dark.sum(1) / np.maximum(b_d.sum(1), 1),
                    "per_fly_total": light + dark})
    return res


# --- U1-U3 implementation checks ------------------------------------------------

def unit() -> dict:
    res = {}
    # U1: with the need held at 0 and no arousal, the OFF dwell of the Organs units is exponential at k0
    p = base_params(need_gain=0.0, dfb_koff_per_min=1e-12, need_tau_rise_h=1e9, need_tau_decay_h=1e9)  # rate = k_r
    o = Organs(dict(p), n_dfb=4000, seed=1, pressure=0.0)
    first = np.full(4000, np.nan)
    t = 0.0
    while np.isnan(first).any() and t < 3600 * 20:
        o.step(20.0, activity=1.0)
        t += 20.0
        first[np.isnan(first) & o.dfb_on] = t / 60.0
    mean_dwell = float(np.nanmean(first))
    res["U1_mean_off_dwell_min"] = round(mean_dwell, 2)
    res["U1_expected_min"] = round(1 / p["dfb_restart_per_min"], 2)
    se = (1 / p["dfb_restart_per_min"]) / np.sqrt(4000)
    res["U1_pass"] = bool(abs(mean_dwell - 1 / p["dfb_restart_per_min"]) <= 3 * se + 1 / 3)   # +1/3 min: 20 s grid
    # U2: constant rates, stationary ON fraction = k_on / (k_on + k_off)
    p = base_params(need_gain=2.0, dfb_koff_per_min=0.05, need_tau_rise_h=1e9, need_tau_decay_h=1e9)
    o = Organs(dict(p), n_dfb=4000, seed=2, pressure=0.3)
    for _ in range(int(6 * 3600 / 20)):
        o.step(20.0, activity=1.0)
    fr = []
    for _ in range(int(6 * 3600 / 20)):
        o.step(20.0, activity=1.0)
        fr.append(o.dfb_on.mean())
    k_on, k_off = dfb_rates(p, 0.3, 0.0)
    res["U2_on_fraction"] = round(float(np.mean(fr)), 4)
    res["U2_expected"] = round(float(k_on / (k_on + k_off)), 4)
    res["U2_pass"] = bool(abs(res["U2_on_fraction"] - res["U2_expected"]) <= 0.01)
    # U3: the vectorised loop against the Organs class, same parameters, 2 scored days, mean daily sleep
    p = base_params(need_tau_rise_h=8.0, need_gain=3.0, dfb_koff_per_min=0.03, light_arousal=2.0)
    v = sim(p, flies=200, burn_days=3, days=2, seed=3)
    vs = dam_sleep(v["inact"], v["run0"])
    vt = day_table(vs, 2)
    org = organs_loop(p, flies=60, burn_days=3, days=2)
    res["U3_vector"] = {k: [round(float(vt[d][k][0]), 1) for d in range(2)] for k in
                        ("total_min", "day_min", "night_min", "bout_len_night")}
    res["U3_organs"] = org
    se = float(np.hypot(vt[0]["total_sd"][0] / np.sqrt(200), org["total_sd"] / np.sqrt(60)))
    diff = float(np.mean([vt[d]["total_min"][0] for d in range(2)]) - np.mean(org["total_min"]))
    res["U3_diff_min"], res["U3_se_min"] = round(diff, 1), round(se, 1)
    res["U3_pass"] = bool(abs(diff) <= 3 * se)
    return res


def organs_loop(p: dict, flies: int, burn_days: int, days: int) -> dict:
    """The model class itself in the s20 loop (20 s sub-steps), one fly at a time."""
    tot, day, night = [], [], []
    for f in range(flies):
        o = Organs(dict(p), seed=100 + f)
        n0, n = burn_days * DAY, (burn_days + days) * DAY + 60
        inact = np.zeros(n - n0, bool)
        run0 = 0
        for t in range(n):
            act = 0.0 if o.switch else 1.0
            if t == n0:
                run0 = int(round(o.inactive_s / 60.0))
            o.step(60.0, activity=act, light_lux=REAR_LUX if (t % DAY) < 720 else 0.0)
            if t >= n0:
                inact[t - n0] = act < p["a_rest"]
        sl = dam_sleep(inact[:, None, None], np.array([[run0]]))[:, 0, 0]
        for d in range(days):
            x = sl[d * DAY:(d + 1) * DAY]
            tot.append(int(x.sum()))
            day.append(int(x[:720].sum()))
            night.append(int(x[720:].sum()))
    return {"total_min": float(np.mean(tot)), "day_min": float(np.mean(day)), "night_min": float(np.mean(night)),
            "total_sd": float(np.std(tot))}


# --- training fit and held-out predictions (registration DECISIONS 23 Oct, s21 fit) ---------------

GRID = {"need_tau_rise_h": [1, 1.5, 2, 3, 4, 6, 8, 12, 18, 24, 36, 48],
        "need_gain": [0, 0.25, 0.5, 1, 2, 4, 8, 16, 32, 64, 100],
        "dfb_koff_per_min": [float(x) for x in np.round(np.geomspace(0.001, 0.9, 12), 5)],
        "light_arousal": [0, 0.25, 0.5, 1, 2, 4, 8, 16, 20]}
BAND = (1008.0, 1100.0)      # Abhilash & Shafer 2024 70-80 % of 24 h, inside the registered 618-1100
WIDE = (618.0, 1100.0)       # registered training range (variant)
RATIO_MIN = 2.0              # Liu 2016 firing ZT13-15 / ZT0-2 about 3x; need ratio >= firing ratio if affine
ARMS = {"6h": (DAY + 1080, 360), "12h": (DAY + 720, 720), "24h": (DAY, DAY)}   # all end at ZT 0 of day R1


def grid_sets() -> dict:
    combos = list(product(*GRID.values()))
    return {k: np.array([c[i] for c in combos], float) for i, k in enumerate(GRID)}


def chunks(sets: dict, size: int):
    m = len(next(iter(sets.values())))
    for i in range(0, m, size):
        yield i, {k: v[i:i + size] for k, v in sets.items()}


def baseline(sets: dict, flies: int = 64, burn: int = 6, seed: int = 10) -> dict:
    """Stage 1: 2 scored days, no deprivation. Totals, day/night, bouts and the ZT13-15 / ZT0-2 need ratio."""
    p = base_params()
    out = {k: [] for k in ("total", "day", "night", "bout_night", "bout_day", "ratio")}
    for i, s in chunks(sets, 400):
        r = sim(p, s, flies=flies, burn_days=burn, days=2, seed=seed + i)
        t = day_table(dam_sleep(r["inact"], r["run0"]), 2)
        out["total"].append(np.mean([d["total_min"] for d in t], 0))
        out["day"].append(np.mean([d["day_min"] for d in t], 0))
        out["night"].append(np.mean([d["night_min"] for d in t], 0))
        out["bout_night"].append(np.mean([d["bout_len_night"] for d in t], 0))
        out["bout_day"].append(np.mean([d["bout_len_day"] for d in t], 0))
        n = r["need"]
        hi = np.mean([n[d * DAY + 780:d * DAY + 900].mean(0) for d in range(2)], 0)
        lo = np.mean([n[d * DAY:d * DAY + 120].mean(0) for d in range(2)], 0)
        out["ratio"].append(hi / np.maximum(lo, 1e-9))
    return {k: np.concatenate(v) for k, v in out.items()}


def deprivation(sets: dict, flies: int = 128, burn: int = 6, seed: int = 20) -> dict:
    """Stage 2: days B, S, R1-R3 scored. Control and the three 20 s-arm counterparts (activity forced to 1).
    Rebound on day k = (focal Rk - focal B) - (control Rk - control B), 24 h windows from ZT 0."""
    p = base_params()
    res = {f"{a}_d{k}": [] for a in ARMS for k in (1, 2, 3)}
    res.update({f"{a}_d1_sem": [] for a in ARMS})
    res.update({"liu_e0": [], "liu_e2": [], "liu_e24": [], "ctrl_total": []})
    for i, s in chunks(sets, 200):
        per, needs = {}, {}
        for j, (arm, sd) in enumerate([("ctrl", None)] + list(ARMS.items())):
            r = sim(p, s, flies=flies, burn_days=burn, days=5, sd=sd, seed=seed + 7 * i + j)
            sl = dam_sleep(r["inact"], r["run0"])
            per[arm] = np.stack([sl[d * DAY:(d + 1) * DAY].sum(0) for d in range(5)])      # (5, M, F)
            needs[arm] = r["need"]
        c = per["ctrl"]
        res["ctrl_total"].append(c[0].mean(1))
        for a in ARMS:
            f = per[a]
            for k in (1, 2, 3):
                res[f"{a}_d{k}"].append((f[k + 1] - f[0]).mean(1) - (c[k + 1] - c[0]).mean(1))
            res[f"{a}_d1_sem"].append(np.sqrt((f[2] - f[0]).var(1) / flies + (c[2] - c[0]).var(1) / flies))
        ex = needs["24h"] - needs["ctrl"]
        res["liu_e0"].append(ex[2 * DAY - 1])
        res["liu_e2"].append(ex[2 * DAY + 120])
        res["liu_e24"].append(ex[3 * DAY])
    return {k: np.concatenate(v) for k, v in res.items()}


def fit() -> dict:
    sets = grid_sets()
    m = len(sets["need_gain"])
    t0 = time.time()
    b = baseline(sets)
    print(f"stage 1: {m} sets, {time.time() - t0:.0f} s", flush=True)
    pre = (b["total"] >= WIDE[0]) & (b["total"] <= WIDE[1]) & (b["night"] > b["day"]) & (b["ratio"] >= RATIO_MIN)
    idx = np.flatnonzero(pre)
    sub = {k: v[idx] for k, v in sets.items()}
    d = deprivation(sub) if len(idx) else {}
    print(f"stage 2: {len(idx)} sets, {time.time() - t0:.0f} s", flush=True)
    out = {"n_sets": m, "n_stage2": int(len(idx)), "grid": GRID, "band": BAND, "wide": WIDE,
           "ratio_min": RATIO_MIN, "sets": []}
    for j, i in enumerate(idx):
        row = {k: float(sets[k][i]) for k in GRID}
        row.update({k: round(float(b[k][i]), 3) for k in b})
        row.update({k: round(float(v[j]), 4) for k, v in d.items()})
        e0 = row["liu_e0"]
        row["liu_pass"] = bool(e0 > 0 and row["liu_e2"] >= 0.5 * e0 and abs(row["liu_e24"]) <= 0.1 * e0)
        row["band"] = bool(BAND[0] <= row["total"] <= BAND[1])
        out["sets"].append(row)
    out["stage1_summary"] = {"total_min_range": [float(b["total"].min()), float(b["total"].max())],
                             "n_wide": int(((b["total"] >= WIDE[0]) & (b["total"] <= WIDE[1])).sum()),
                             "n_band": int(((b["total"] >= BAND[0]) & (b["total"] <= BAND[1])).sum()),
                             "n_night_gt_day": int((b["night"] > b["day"]).sum()),
                             "n_ratio": int((b["ratio"] >= RATIO_MIN).sum())}
    for name, key in (("primary", "band"), ("wide", None)):
        acc = [r for r in out["sets"] if r["liu_pass"] and (key is None or r[key])]
        out[name] = select(acc)
    return out


def select(acc: list) -> dict:
    """Registered rule: candidate = the accepted set whose day-1 predictions (6, 12, 24 h) lie closest
    (Euclidean, min) to the per-arm medians over the accepted set; the spread is reported alongside."""
    if not acc:
        return {"n_accepted": 0}
    pred = np.array([[r[f"{a}_d1"] for a in ARMS] for r in acc])
    med = np.median(pred, 0)
    j = int(np.argmin(((pred - med) ** 2).sum(1)))
    return {"n_accepted": len(acc), "median": dict(zip(ARMS, med.round(1).tolist())),
            "p2.5": dict(zip(ARMS, np.percentile(pred, 2.5, 0).round(1).tolist())),
            "p97.5": dict(zip(ARMS, np.percentile(pred, 97.5, 0).round(1).tolist())),
            "candidate": acc[j]}


if __name__ == "__main__":
    OUT.mkdir(parents=True, exist_ok=True)
    t0 = time.time()
    if sys.argv[1] == "unit":
        r = unit()
        (OUT / "unit.json").write_text(json.dumps(r, indent=1))
        for k, v in r.items():
            print(k, v)
    elif sys.argv[1] == "fit":
        r = fit()
        (OUT / "fit.json").write_text(json.dumps(r, indent=1))
        for k in ("n_sets", "n_stage2", "stage1_summary", "primary", "wide"):
            print(k, json.dumps(r[k]) if k not in ("primary", "wide") else
                  json.dumps({kk: v for kk, v in r[k].items() if kk != "candidate"}))
        for k in ("primary", "wide"):
            print(k, "candidate", json.dumps(r[k].get("candidate")))
    print(f"wall {time.time() - t0:.0f} s")
