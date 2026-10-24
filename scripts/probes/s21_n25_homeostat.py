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
        k_on, k_off = dfb_rates(q, need, lsat, (t % DAY) / 60.0)    # entrained LD: CT = ZT (s23 night term)
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


def bouts(sl: np.ndarray, days: int) -> dict:
    """DAM-style bouts from sleep[T, M, F]: each bout belongs to the 12 h period it starts in and counts its full
    length (bouts still running at the end of the record are cut there). Per set: mean bouts per period, and the
    mean bout length (pooled over bouts) for day and night."""
    T, m, f = sl.shape
    x = np.concatenate([np.zeros((1, m, f), bool), sl, np.zeros((1, m, f), bool)]).reshape(T + 2, m * f).T
    dx = np.diff(x.astype(np.int8), axis=1)
    sc, st = np.nonzero(dx == 1)
    _, en = np.nonzero(dx == -1)
    length, cell = en - st, sc // f
    keep = st < days * DAY
    night = (st % DAY) >= 720
    out = {}
    for name, sel in (("day", keep & ~night), ("night", keep & night)):
        n = np.bincount(cell[sel], minlength=m)
        tot = np.bincount(cell[sel], weights=length[sel], minlength=m)
        out[f"bouts_{name}"] = n / (f * days)
        out[f"bout_len_{name}"] = tot / np.maximum(n, 1)
    return out


def rebout(sets: dict, flies: int = 128, seed: int = 30) -> dict:
    """Baseline bout structure (bouts() above) for given sets, 2 scored days after 6 burn-in days."""
    r = sim(base_params(), sets, flies=flies, burn_days=6, days=2, seed=seed)
    return bouts(dam_sleep(r["inact"], r["run0"]), 2)


GARBE_NIGHT_BOUT_MAX = 335.0  # min, longest per-fly mean night bout, Garbe 2015 Fig. 2 (SB DAM; own figure read)


def bout_check() -> dict:
    """Baseline bouts for every stage-2 set (seed 30 + chunk), then the s22 sensitivity: the primary accepted sets
    whose mean night bout lies inside Garbe 2015's per-fly range, and their day-1 predictions. Not a registered
    check: the locked prediction is the plain primary candidate."""
    path = OUT / "fit_bouts.json"
    if path.exists():
        r = json.loads(path.read_text())
    else:
        r = json.loads((OUT / "fit.json").read_text())
        rows = r["sets"]
        sets = {k: np.array([s[k] for s in rows], float) for k in GRID}
        res = {}
        for i, ch in chunks(sets, 200):
            for k, v in rebout(ch, seed=30 + i).items():
                res.setdefault(k, []).append(v)
        for k, v in res.items():
            for s, x in zip(rows, np.concatenate(v)):
                s["dam_" + k] = round(float(x), 3)
        path.write_text(json.dumps(r, indent=1))
    acc = [s for s in r["sets"] if s["liu_pass"] and s["band"]]
    keys = ("dam_bouts_night", "dam_bout_len_night", "dam_bouts_day", "dam_bout_len_day")
    out = {"primary_bout_ranges": {k: [min(s[k] for s in acc), max(s[k] for s in acc)] for k in keys}}
    for cap in (GARBE_NIGHT_BOUT_MAX, 250.0):
        sel = select([s for s in acc if s["dam_bout_len_night"] <= cap])
        if sel["n_accepted"]:
            c = sel.pop("candidate")
            sel["candidate"] = {k: c[k] for k in (*GRID, "total", "day", "night", *keys, *(f"{a}_d1" for a in ARMS))}
        out[f"night_bout_le_{cap:g}"] = sel
    c = out[f"night_bout_le_{GARBE_NIGHT_BOUT_MAX:g}"]["candidate"]
    d = deprivation({k: np.array([c[k]], float) for k in GRID}, flies=2048, seed=500)
    out["amended_candidate_2048"] = {k: round(float(v[0]), 2) for k, v in d.items()}
    return out


KR_FAST = 0.094               # min^-1, upper end of the measured k_r range, 1/(mean - 2 SEM) (Pimentel 2016)
GARBE_LIKE = (2.8, 183.0)     # bouts per night >= mean - 1 s.d., mean night bout <= mean + 1 s.d. (Garbe 2015 SB)


def kr_check(kr: float = KR_FAST) -> dict:
    """s22 diagnostic (DECISIONS 23 Oct 03:45), training data only: the mode 1 grid with k_r at the fast end of its
    measured range. Stage 1 in the primary band, then bouts, then stage 2 and T3 on the T5 survivors."""
    sets = grid_sets()
    sets["dfb_restart_per_min"] = np.full(len(sets["need_gain"]), kr)
    t0 = time.time()
    b = baseline(sets)
    pre = (b["total"] >= BAND[0]) & (b["total"] <= BAND[1]) & (b["night"] > b["day"]) & (b["ratio"] >= RATIO_MIN)
    idx = np.flatnonzero(pre)
    print(f"stage 1: {len(idx)} sets pass T1 (primary band), T2, T4; {time.time() - t0:.0f} s", flush=True)
    out = {"k_r": kr, "n_t124": int(len(idx)),
           "stage1_night_bout_range": [float(b["bout_night"].min()), float(b["bout_night"].max())], "sets": []}
    if not len(idx):
        return out
    sub = {k: v[idx] for k, v in sets.items()}
    bo = {}
    for i, ch in chunks(sub, 200):
        for k, v in rebout(ch, seed=30 + i).items():
            bo.setdefault(k, []).append(v)
    bo = {k: np.concatenate(v) for k, v in bo.items()}
    t5 = np.flatnonzero(bo["bout_len_night"] <= GARBE_NIGHT_BOUT_MAX)
    out["n_t1245"] = int(len(t5))
    out["t124_bouts_night_range"] = [float(bo["bouts_night"].min()), float(bo["bouts_night"].max())]
    out["t124_bout_len_night_range"] = [float(bo["bout_len_night"].min()), float(bo["bout_len_night"].max())]
    print(f"bouts: {len(t5)} sets pass T5; {time.time() - t0:.0f} s", flush=True)
    d = deprivation({k: v[t5] for k, v in sub.items()}) if len(t5) else {}
    for j, i in enumerate(t5):
        row = {k: float(sub[k][i]) for k in GRID}
        row.update({k: round(float(b[k][idx[i]]), 3) for k in ("total", "day", "night", "ratio")})
        row.update({"dam_" + k: round(float(v[i]), 3) for k, v in bo.items()})
        row.update({k: round(float(v[j]), 4) for k, v in d.items()})
        e0 = row["liu_e0"]
        row["liu_pass"] = bool(e0 > 0 and row["liu_e2"] >= 0.5 * e0 and abs(row["liu_e24"]) <= 0.1 * e0)
        row["garbe_like"] = bool(row["dam_bouts_night"] >= GARBE_LIKE[0] and row["dam_bout_len_night"] <= GARBE_LIKE[1])
        out["sets"].append(row)
    acc = [r for r in out["sets"] if r["liu_pass"]]
    like = [r for r in acc if r["garbe_like"]]
    out["n_accepted_t1_5"] = len(acc)
    out["n_garbe_like"] = len(like)
    out["garbe_like_gamma"] = sorted({r["need_gain"] for r in like})
    out["accepted"] = select(acc)
    out["garbe_like_sel"] = select(like)
    print(f"stage 2: {len(acc)} accepted, {len(like)} Garbe-like; {time.time() - t0:.0f} s", flush=True)
    return out


def bout_figure(path: Path = Path("docs/media/s22_n25_bouts.png")) -> dict:
    """Accepted sets at k_r 0.0387 (fit_bouts.json, primary) and 0.094 (kr_check.json): bouts per 12 h and mean bout
    length, day against night, coloured by the 24 h day-1 rebound; Garbe 2015 SB mean +- 1 s.d. as a box."""
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    import matplotlib.ticker
    a = [s for s in json.loads((OUT / "fit_bouts.json").read_text())["sets"] if s["liu_pass"] and s["band"]]
    b = [s for s in json.loads((OUT / "kr_check.json").read_text())["sets"] if s["liu_pass"]]
    garbe = {"bouts": ((8.7, 3.3), (7.0, 4.2)), "bout_len": ((57.0, 25.0), (113.0, 70.0))}
    fig, ax = plt.subplots(1, 2, figsize=(11, 4.6))
    for j, (key, lab) in enumerate((("bouts", "bouts per 12 h"), ("bout_len", "mean bout (min)"))):
        (dm, ds), (nm, ns) = garbe[key]
        ax[j].add_patch(plt.Rectangle((dm - ds, nm - ns), 2 * ds, 2 * ns, fc="0.85", ec="k", lw=0.8,
                                      label="Garbe 2015 SB, mean +- 1 s.d."))
        for rows, mk, name in ((a, "o", "k_r 0.0387 (measured mean)"), (b, "^", "k_r 0.094 (measured upper end)")):
            sc = ax[j].scatter([r[f"dam_{key}_day"] for r in rows], [r[f"dam_{key}_night"] for r in rows],
                               c=[r["24h_d1"] for r in rows], marker=mk, s=22, cmap="viridis", vmin=0, vmax=260,
                               edgecolors="k", linewidths=0.3, label=name)
        ax[j].set_xlabel(f"day: {lab}")
        ax[j].set_ylabel(f"night: {lab}")
    ax[1].set_xscale("log")
    ax[1].set_yscale("log")
    for axis, ticks in ((ax[1].xaxis, (20, 30, 50, 100, 200)), (ax[1].yaxis, (50, 100, 200, 400, 700))):
        axis.set_major_locator(matplotlib.ticker.FixedLocator(ticks))
        axis.set_major_formatter(matplotlib.ticker.FixedFormatter([str(t) for t in ticks]))
        axis.set_minor_formatter(matplotlib.ticker.NullFormatter())
    ax[0].legend(fontsize=7, loc="upper right")
    fig.colorbar(sc, ax=ax, label="24 h arm day-1 rebound (min)")
    fig.suptitle("N25 mode 1 accepted sets: night bout structure only matches with over-fragmented days", fontsize=10)
    path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(path, dpi=110)
    return {"figure": str(path), "n_mean": len(a), "n_fast": len(b)}


def figure(path: Path = Path("docs/media/s22_n25_homeostat.png")) -> dict:
    """The primary candidate: 30-min sleep profile and need (control vs 24 h arm), and day-1 rebound vs length
    with the accepted-set spread. Re-simulated with 512 flies per arm (seed 40)."""
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    r = json.loads((OUT / "fit.json").read_text())
    pr = r["primary"]
    c = pr["candidate"]
    p = base_params(**{k: c[k] for k in GRID})
    runs = {a: sim(p, flies=512, burn_days=6, days=5, sd=sd, seed=40 + j)
            for j, (a, sd) in enumerate([("ctrl", None), ("24h", ARMS["24h"])])}
    fig, ax = plt.subplots(3, 1, figsize=(9, 9))
    h = np.arange(5 * DAY) / 60.0
    for a, col in (("ctrl", "k"), ("24h", "tab:red")):
        sl = dam_sleep(runs[a]["inact"], runs[a]["run0"])[:5 * DAY, 0].mean(1)
        ax[0].plot(h.reshape(-1, 30).mean(1), sl.reshape(-1, 30).mean(1) * 30, col, lw=1, label=a)
        ax[1].plot(h, runs[a]["need"][:5 * DAY, 0], col, lw=1, label=a)
    for a_ in ax[:2]:
        for d in range(5):
            a_.axvspan(d * 24 + 12, d * 24 + 24, color="0.9", zorder=0)
        a_.set_xlim(0, 120)
    ax[0].axvspan(24, 48, ymax=0.05, color="tab:red", alpha=0.5)
    ax[0].set_ylabel("sleep (min per 30 min)")
    ax[0].set_title("N25 mode 1 primary candidate: " + ", ".join(f"{k} {c[k]}" for k in GRID), fontsize=9)
    ax[0].legend(fontsize=8)
    ax[1].set_ylabel("ER5 need n (mean over flies)")
    ax[1].set_xlabel("h from ZT 0 of baseline day B (grey: dark; red bar: 24 h deprivation)")
    L = [6, 12, 24]
    ax[2].errorbar(L, [pr["median"][a] for a in ARMS],
                   yerr=[[pr["median"][a] - pr["p2.5"][a] for a in ARMS],
                         [pr["p97.5"][a] - pr["median"][a] for a in ARMS]], fmt="o", color="0.5",
                   capsize=4, label=f"accepted sets, median and 2.5-97.5 % (n {pr['n_accepted']})")
    ax[2].plot(L, [c[f"{a}_d1"] for a in ARMS], "s-", color="tab:blue", label="candidate")
    ax[2].axhline(0, color="k", lw=0.5)
    ax[2].set_xlabel("deprivation length (h), ending ZT 0")
    ax[2].set_ylabel("day-1 rebound (min)")
    ax[2].legend(fontsize=8)
    fig.tight_layout()
    path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(path, dpi=110)
    return {"figure": str(path)}


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
    elif sys.argv[1] == "figure":
        print(figure())
    elif sys.argv[1] == "krcheck":
        r = kr_check()
        (OUT / "kr_check.json").write_text(json.dumps(r, indent=1))
        for k, v in r.items():
            if k != "sets":
                print(k, json.dumps(v))
    elif sys.argv[1] == "boutfig":
        print(bout_figure())
    elif sys.argv[1] == "bouts":
        r = bout_check()
        (OUT / "bout_check.json").write_text(json.dumps(r, indent=1))
        for k, v in r.items():
            print(k, json.dumps(v))
    print(f"wall {time.time() - t0:.0f} s")
