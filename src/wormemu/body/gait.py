"""Gait readouts from a body run: bending frequency, body wavelength, curvature amplitude along the body, speed.

Method (BODY_TESTS.md): complex demodulation of the curvature kymograph kappa(s, t) at the bending frequency over a
whole number of periods; wavelength from the slope of the unwrapped phase along s = 0.1-0.9 L; amplitude = 2|c(s)|;
speed = net centroid displacement over the window / window length, signed by the mean nose direction.
"""
from __future__ import annotations

import numpy as np

from .drive import TravellingWave


def run(body, drive, t_end: float, record_every: int = 5):
    """Step the body under drive(t) to t_end. Returns a dict of time series sampled every `record_every` steps."""
    n = int(round(t_end / body.dt))
    ts, kap, cen, hd = [], [], [], []
    for i in range(n):
        body.step(drive(body.t))
        if (i + 1) % record_every == 0:
            ts.append(body.t)
            kap.append(body.curvature())
            cen.append(body.centroid())
            th0 = body.theta[0]
            hd.append((-np.cos(th0), -np.sin(th0)))
    return {"t": np.array(ts), "kappa": np.array(kap), "centroid": np.array(cen), "head_dir": np.array(hd),
            "s": body.s_joint / body.length}


def analyse(rec, f_drive: float, n_periods: int):
    """Readouts over the last n_periods whole periods of the drive."""
    t = rec["t"]
    T = n_periods / f_drive
    w = t > t[-1] - T - 1e-12
    tw, kw = t[w], rec["kappa"][w]
    # bending frequency: peak of |demodulated mid-body curvature| over a fine grid around the drive
    mid = kw[:, (rec["s"] > 0.3) & (rec["s"] < 0.7)]
    fgrid = np.linspace(0.5 * f_drive, 1.5 * f_drive, 401)
    kc = mid - mid.mean(0)
    pw = np.array([np.abs(np.exp(-2j * np.pi * fg * tw) @ kc).sum() for fg in fgrid])
    f_body = fgrid[pw.argmax()]
    c = (np.exp(-2j * np.pi * f_drive * tw) @ (kw - kw.mean(0))) / len(tw)
    amp = 2 * np.abs(c) * 1e-3  # 1/mm
    s = rec["s"]
    band = (s >= 0.1) & (s <= 0.9)
    ph = np.unwrap(np.angle(c[band]))
    slope = np.polyfit(s[band], ph, 1)[0]  # rad per body length
    lam = 2 * np.pi / abs(slope) if slope != 0 else np.inf
    head = amp[(s >= 0.1) & (s <= 0.2)].mean()
    tail = amp[(s >= 0.8) & (s <= 0.9)].mean()
    cen = rec["centroid"][w]
    disp = cen[-1] - cen[0]
    hdir = rec["head_dir"][w].mean(0)
    sign = np.sign(disp @ hdir) if np.linalg.norm(hdir) > 0 else 1.0
    speed = sign * np.linalg.norm(disp) / (tw[-1] - tw[0]) * 1e3  # mm/s, + = head first
    return {"f_body_hz": f_body, "wavelength_L": lam, "wave_dir": -np.sign(slope),
            "head_amp_per_mm": head, "tail_amp_per_mm": tail, "tail_head_ratio": tail / head,
            "speed_mm_s": speed, "amp_profile_per_mm": amp, "s": s}


GAITS = {  # drive inputs: Fang-Yen 2010 Table 1 means (measured)
    "crawl": {"medium": "agar", "f": 0.30, "lam": 0.65, "periods": 6, "window": 4, "head_target": 8.5},
    "swim": {"medium": "water", "f": 1.76, "lam": 1.54, "periods": 8, "window": 4, "head_target": 4.5},
}


def gait_run(make_body, gait: str, a0: float, record_every: int = 5):
    g = GAITS[gait]
    body = make_body(g["medium"])
    drv = TravellingWave(body, g["f"], g["lam"], a0)
    rec = run(body, drv, g["periods"] / g["f"], record_every)
    return analyse(rec, g["f"], g["window"]), rec, body


def calibrate_a0(make_body, gait: str, target=None, lo=0.0, hi=1.0, tol=0.01, max_iter=20):
    """Bisection on drive amplitude a0 so the head curvature amplitude matches the target (fitted, brain side).
    Returns (a0, readouts). a0 = hi with readouts below target means the body is too weak."""
    target = GAITS[gait]["head_target"] if target is None else target
    out_hi, _, _ = gait_run(make_body, gait, hi)
    if out_hi["head_amp_per_mm"] < target:
        return hi, out_hi
    for _ in range(max_iter):
        mid = 0.5 * (lo + hi)
        out, _, _ = gait_run(make_body, gait, mid)
        if abs(out["head_amp_per_mm"] - target) / target < tol:
            return mid, out
        if out["head_amp_per_mm"] < target:
            lo = mid
        else:
            hi = mid
    return mid, out
