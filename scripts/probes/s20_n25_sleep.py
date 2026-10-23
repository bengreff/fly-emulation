"""s20 N25 sleep homeostat probe: the reduced loop of DECISIONS 23 Oct 00:27 (CPU, Organs as in the model).

Activity is 0 while the dFB switch is on and 1 while it is off; mechanical deprivation forces activity 1.
The clock runs at period 24 h with no light input, so ct = ZT + phase offset (0 unless variant V3).
Sleep is scored like DAM data: inactivity runs of >= 5 min count whole. One step is 1 min.

    .venv/bin/python scripts/probes/s20_n25_sleep.py checks          # C1, C2 -> runs/s20/n25/checks.json
    .venv/bin/python scripts/probes/s20_n25_sleep.py sd              # deprivation runs -> runs/s20/n25/sd.json
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np

from flyemu.internal_state import Organs, default_params

OUT = Path("runs/s20/n25")
DAY = 1440                                  # minutes


def abhilash_discrete(t_i=8.76, t_d=9.51, mu=0.35, ml=0.15, amp=0.10, tau=24.0, days=30, s0=0.2):
    """Abhilash & Shafer 2024 Methods, as read (round 2): 1-min steps; returns per-minute sleep (bool)."""
    i, d = np.exp(-1 / (t_i * 60)), np.exp(-1 / (t_d * 60))
    s, sleep, out = s0, False, np.zeros(days * DAY, bool)
    for t in range(days * DAY):
        c = amp * np.cos(2 * np.pi * t / (tau * 60))
        if not sleep and s >= mu + c:
            sleep = True
        elif sleep and s <= ml + c:
            sleep = False
        s = s * d if sleep else 1 - i * (1 - s)
        out[t] = sleep
    return out


def params(mode: int, **over) -> dict:
    p = default_params(sleep_sourced=bool(mode))
    p["period_h"] = 24.0
    p.update(over)
    return p


def run(p: dict, days: float, sd: tuple[float, float] | None = None, ct_offset_h: float = 0.0,
        burn_days: int = 10) -> dict:
    """Burn-in days, then `days` days from ZT0; sd = (start ZT hours after the burn-in, length h)."""
    o = Organs(p=dict(p), z=np.exp(1j * 2 * np.pi * ct_offset_h / 24.0))
    n = int(round((burn_days + days) * DAY))
    inact, sw, P = np.zeros(n, bool), np.zeros(n, bool), np.zeros(n)
    sd0 = None if sd is None else int(round(burn_days * DAY + sd[0] * 60))
    sd1 = None if sd is None else sd0 + int(round(sd[1] * 60))
    for t in range(n):
        act = 0.0 if o.switch else 1.0
        if sd0 is not None and sd0 <= t < sd1:
            act = 1.0
        o.step(60.0, activity=act)
        inact[t], sw[t], P[t] = act < p["a_rest"], o.switch, o.pressure
    k = burn_days * DAY
    return {"sleep": dam_sleep(inact)[k:], "switch": sw[k:], "pressure": P[k:]}


def dam_sleep(inact: np.ndarray, crit: int = 5) -> np.ndarray:
    """Inactivity runs of >= crit minutes count whole (DAM convention)."""
    out = np.zeros_like(inact)
    t, n = 0, len(inact)
    while t < n:
        if inact[t]:
            u = t
            while u < n and inact[u]:
                u += 1
            if u - t >= crit:
                out[t:u] = True
            t = u
        else:
            t += 1
    return out


def day_stats(sl: np.ndarray, day: int) -> dict:
    d = sl[day * DAY:(day + 1) * DAY]
    return {"total_min": int(d.sum()), "day_min": int(d[:720].sum()), "night_min": int(d[720:].sum()),
            "pct": round(100 * d.mean(), 2), "hourly_min": [int(x) for x in d.reshape(24, 60).sum(1)],
            "bouts": int(np.sum(np.diff(d.astype(int)) == 1) + int(d[0]))}


def checks() -> dict:
    res = {}
    # C1: the discrete rule as published, last 4 of 30 days, tau 23.5 / 24 / 24.5 (V2 reported)
    for tau in (23.5, 24.0, 24.5):
        sl = abhilash_discrete(tau=tau)
        res[f"C1_discrete_tau{tau}"] = round(100 * sl[-4 * DAY:].mean(), 2)
    # our continuous form (Organs, 5-min onset lag) and V1 (no lag), last of 10 + 1 days
    for name, mode, over, off in (("mode1", 1, {}, 0.0), ("mode1_V1_nolag", 1, {"t_sleep_s": 1e-6}, 0.0),
                                  ("mode1_V3_phi12", 1, {}, 12.0), ("mode0", 0, {}, 0.0)):
        r = run(params(mode, **over), days=2, ct_offset_h=off)
        res[name] = {"day0": day_stats(r["sleep"], 0), "day1": day_stats(r["sleep"], 1)}
    m1 = res["mode1"]["day1"]["pct"]
    res["C1_pass"] = bool(abs(res["C1_discrete_tau24.0"] - 74.36) <= 1.0 and abs(m1 - res["C1_discrete_tau24.0"]) <= 2.0)
    for m in ("mode1", "mode0"):
        d = res[m]["day1"]
        res[f"C2_{m}"] = {"total_in_618_1100": bool(618 <= d["total_min"] <= 1100),
                          "night_gt_day": bool(d["night_min"] > d["day_min"])}
    return res


if __name__ == "__main__":
    OUT.mkdir(parents=True, exist_ok=True)
    if sys.argv[1] == "checks":
        r = checks()
        (OUT / "checks.json").write_text(json.dumps(r, indent=1))
        for k, v in r.items():
            print(k, v if not isinstance(v, dict) or "day1" not in v else
                  {d: {x: v[d][x] for x in ("total_min", "day_min", "night_min", "pct", "bouts")} for d in v})
    elif sys.argv[1] == "sd":
        # deprivation ending at ZT0 of the recovery day (6 h: ZT18-24; 12 h: ZT12-24; 24 h: ZT0-24), the usual
        # night-ending design; the hourly time course covers any recovery window / baseline the source uses
        out = {}
        for name, mode, off in (("mode1", 1, 0.0), ("mode1_V3_phi12", 1, 12.0), ("mode0", 0, 0.0)):
            p = params(mode)
            base = run(p, days=3, ct_offset_h=off)
            for dur in (6.0, 12.0, 24.0):
                r = run(p, days=3, sd=(24.0 - dur, dur), ct_offset_h=off)      # SD on day 0, recovery day 1
                b1, r1 = day_stats(base["sleep"], 1), day_stats(r["sleep"], 1)
                lost = int(base["sleep"][int((24 - dur) * 60):DAY].sum())
                gain = [x - y for x, y in zip(r1["hourly_min"], b1["hourly_min"])]
                out[f"{name}_sd{int(dur)}"] = {"lost_min": lost, "base_day1": b1, "rec_day1": r1,
                                               "gain_hourly_min": gain, "gain_6h": sum(gain[:6]),
                                               "gain_24h": sum(gain), "pct_recovered_24h": round(100 * sum(gain) / lost, 1)}
                print(name, dur, "lost", lost, "gain 6h", sum(gain[:6]), "24h", sum(gain),
                      f"({out[f'{name}_sd{int(dur)}']['pct_recovered_24h']} %)")
        (OUT / "sd.json").write_text(json.dumps(out, indent=1))
