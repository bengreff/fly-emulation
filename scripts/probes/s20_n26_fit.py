"""s20 N26: fit ct_light, k and l50 to read sources, then write the held-out ZT21 prediction
(DECISIONS 22 Oct 04:44, 04:49, 05:04; values in docs/research/s20_n26_figreads.md and the s19 reads).

- ct_light: the model's DD PRC zero crossing for Kistenpfennig 2012's pulse (60 min, 1000 lux) = CT 18.5.
- k: the model's LD-assay delay for Lamba 2014's pulse (5 min, 1500 lux) at ZT15 = -3.1 h.
- l50: the model's 10 min IRC half-max at CT20 = Vinayak 2013's 600 nW/cm2 blue = 0.37 lux (inferred at 470 nm).
LD assay: 12:12 LD at `--ld-lux` for 10 days, the pulse in the last night at ZT, then DD; shift = pulsed minus
unpulsed CT after 4 DD days (+ advance).

    .venv/bin/python scripts/probes/s20_n26_fit.py --out runs/s20/n26/fit.json
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))
from flyemu.internal_state import Organs, default_params  # noqa: E402
from s19_n26_prc import DT, _wrap_h, irc_half_lsat, shift_h, zero_crossing_ct  # noqa: E402


def ld_assay_shift(p: dict, zt: float, dur_s: float, lux: float, ld_lux: float = 1000.0, days: int = 10,
                   free_days: float = 4.0) -> float:
    def run(pulse: bool) -> float:
        org = Organs(p=p, z=complex(1.0, 0.0))
        for _ in range(days):
            for _ in range(12):
                org.step(3600.0, light_lux=ld_lux)
            for _ in range(12):
                org.step(3600.0, light_lux=0.0)
        for _ in range(12):
            org.step(3600.0, light_lux=ld_lux)
        pre = (zt - 12.0) * 3600.0
        t = 0.0
        while t < pre:
            org.step(min(600.0, pre - t), light_lux=0.0); t += 600.0
        n_on = max(1, int(round(dur_s / DT)))
        for _ in range(n_on):
            org.step(DT, light_lux=lux if pulse else 0.0)
        t, t_end = 0.0, free_days * 86400.0
        while t < t_end:
            org.step(min(3600.0, t_end - t), light_lux=0.0); t += 3600.0
        return org.ct_h
    return _wrap_h(run(True) - run(False))


def fit(p: dict, zc_target: float, zc_pulse, k_zt: float, k_delay: float, k_pulse, irc_lux: float,
        irc_ct: float, irc_dur_s: float, ld_lux: float, rounds: int = 3, iters: int = 4) -> dict:
    p = dict(p)
    p["ct_light_h"] = (zc_target + 12.0) % 24.0
    hist = []
    for r in range(rounds):
        for _ in range(iters):
            lo, hi = 1e-3, 500.0
            for _ in range(36):
                k = np.sqrt(lo * hi); p["k_light_per_h"] = k
                (lo, hi) = (k, hi) if ld_assay_shift(p, k_zt, *k_pulse, ld_lux=ld_lux) > k_delay else (lo, k)
            p["k_light_per_h"] = float(np.sqrt(lo * hi))
            zc = zero_crossing_ct(p, *zc_pulse)
            if zc is None:
                break
            p["ct_light_h"] = float((p["ct_light_h"] + _wrap_h(zc_target - zc)) % 24.0)
        x = irc_half_lsat(p, irc_ct, irc_dur_s)
        p["l50_lux"] = float(irc_lux * (1 - x) / x)
        hist.append({"round": r, "k": p["k_light_per_h"], "ct_light": p["ct_light_h"], "l50": p["l50_lux"],
                     "zc": zc, "half_lsat": x})
    return p, hist


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--ld-lux", type=float, default=1000.0)
    ap.add_argument("--out", type=Path, required=True)
    a = ap.parse_args()
    p0 = default_params()
    irc_lux = 0.6 * 0.62    # Vinayak 10 min half-max 600 nW/cm2 blue; 1 uW/cm2 ~ 0.62 lux at 470 nm (inferred)
    p, hist = fit(p0, 18.5, (3600.0, 1000.0), 15.0, -3.1, (300.0, 1500.0), irc_lux, 20.0, 600.0, a.ld_lux)
    keys = ("k_light_per_h", "l50_lux", "ct_light_h", "mu_per_h", "period_h")
    x120 = irc_half_lsat(p, 20.0, 7200.0)
    org = Organs(p=p, z=complex(1.0, 0.0))
    for _ in range(20):
        for _ in range(12):
            org.step(3600.0, light_lux=a.ld_lux)
        for _ in range(12):
            org.step(3600.0, light_lux=0.0)
    res = {"params": {k: p[k] for k in keys}, "guess": {k: p0[k] for k in keys}, "history": hist,
           "fit_checks": {
               "zero_crossing_ct_60min_1000lux": zero_crossing_ct(p, 3600.0, 1000.0),
               "ld_zt15_shift_5min_1500lux": ld_assay_shift(p, 15.0, 300.0, 1500.0, ld_lux=a.ld_lux),
               "irc_half_lux_ct20_10min": irc_half_lsat(p, 20.0, 600.0) / (1 - irc_half_lsat(p, 20.0, 600.0))
               * p["l50_lux"]},
           "consistency": {
               "kistenpfennig_ct15_delay_60min_1000lux_h": {"model": shift_h(p, 15.0, 3600.0, 1000.0),
                                                            "measured": -4.05, "sem": 0.18},
               "kistenpfennig_max_advance_ct_measured": 21.0,
               "model_max_advance_ct_60min_1000lux": max(np.arange(16.0, 24.0, 0.5),
                                                          key=lambda c: shift_h(p, c % 24, 3600.0, 1000.0)),
               "vinayak_irc_half_lux_ct20_120min": {"model": x120 / (1 - x120) * p["l50_lux"],
                                                    "measured_inferred_lux": 0.004 * 0.62},
               "ct_at_lights_on_ld12": float(org.ct_h)},
           "prediction_heldout": {"lamba_zt21_shift_5min_1500lux_h":
                                  ld_assay_shift(p, 21.0, 300.0, 1500.0, ld_lux=a.ld_lux)}}
    a.out.parent.mkdir(parents=True, exist_ok=True)
    a.out.write_text(json.dumps(res, indent=1, default=float))
    print(json.dumps(res, indent=1, default=float))


if __name__ == "__main__":
    main()
