"""Run the pre-registered body tests (docs/worm/BODY_TESTS.md) and write the results JSON + figures.

    PYTHONPATH=src python scripts/worm/body_tests.py [--quick]

Writes data/worm/body_runs/body_tests.json and figures under data/worm/body_runs/fig/.
"""
from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

import numpy as np

from wormemu.body import Body, BodyConfig, BodyLedger
from wormemu.body.gait import GAITS, analyse, calibrate_a0, gait_run, run
from wormemu.body.drive import TravellingWave

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "data/worm/body_runs"

BARS = {
    "crawl": {"speed": (0.08, 0.30), "wavelength": (0.46, 0.84)},
    "swim": {"speed": (0.29, 0.45), "wavelength": (1.29, 2.15)},
}


def body_factory(ledger=None, **cfg):
    def make(medium):
        return Body(ledger, BodyConfig(medium=medium, **cfg))
    return make


def dead_worm():
    res = {}
    for medium in ("agar", "water"):
        r = {}
        # D1 straight, silent
        b = Body(cfg=BodyConfig(medium=medium))
        c0 = b.centroid().copy()
        kmax = 0.0
        for _ in range(int(round(10.0 / b.dt))):
            b.step(np.zeros(95))
            kmax = max(kmax, np.abs(b.curvature()).max())
        r["D1_displacement_m"] = float(np.linalg.norm(b.centroid() - c0))
        r["D1_max_abs_kappa_per_m"] = float(kmax)
        r["D1_pass"] = r["D1_displacement_m"] < 1e-9 and kmax < 1e-9
        # D2 bent, silent
        for flip in (False, True):
            b = Body(cfg=BodyConfig(medium=medium))
            kap = 8e3 * np.sin(2 * np.pi * b.s_joint / (0.65 * b.length))
            th = np.pi + np.concatenate([[0.0], np.cumsum(kap * b.ds)])
            b.reset(theta=th)
            Kpos = b.K.copy()
            if flip:
                b.K = -b.K
            E = [0.5 * b.q @ Kpos @ b.q]
            c0 = b.centroid().copy()
            for _ in range(int(round(10.0 / b.dt))):
                b.step(np.zeros(95))
                E.append(0.5 * b.q @ Kpos @ b.q)
                if not np.isfinite(E[-1]) or E[-1] > 1e3 * E[0]:
                    break
            E = np.array(E)
            rises = np.diff(E) > 1e-12 * E[0]
            key = "D2_flipped_control" if flip else "D2"
            r[key] = {"E0_J": float(E[0]), "E_end_J": float(E[-1]), "E_end_frac": float(E[-1] / E[0]),
                      "n_rises": int(rises.sum()), "max_rise_frac": float(np.max(np.diff(E)) / E[0]),
                      "centroid_move_L": float(np.linalg.norm(b.centroid() - c0) / b.length) if np.isfinite(E[-1]) else None,
                      "t_end_s": float(b.t)}
            r[key]["pass"] = bool(r[key]["n_rises"] == 0 and r[key]["E_end_frac"] < 0.01
                                  and (r[key]["centroid_move_L"] or 1) < 0.05)
            if not flip:
                # energy half-life
                half = np.argmax(E < 0.5 * E[0])
                r[key]["E_half_time_s"] = float(half * b.dt)
        # D3 contracted dorsal muscles, input 0
        b = Body(cfg=BodyConfig(medium=medium))
        b.a[b.mus.dorsal] = 1.0
        E, kh, amax = [], [], []
        for _ in range(int(round(10.0 / b.dt))):
            b.step(np.zeros(95))
            E.append(b.elastic_energy())
            kh.append(b.curvature().mean())
        E = np.array(E)
        r["D3"] = {"E_peak_J": float(E.max()), "t_peak_s": float((E.argmax() + 1) * b.dt),
                   "mean_kappa_at_peak_per_mm": float(kh[E.argmax()] * 1e-3),
                   "E_end_frac_of_peak": float(E[-1] / E.max()),
                   "max_abs_kappa_end_per_mm": float(np.abs(b.curvature()).max() * 1e-3)}
        r["D3"]["bends_dorsal"] = bool(r["D3"]["mean_kappa_at_peak_per_mm"] > 0)
        r["D3"]["pass"] = bool(r["D3"]["bends_dorsal"] and r["D3"]["E_end_frac_of_peak"] < 0.01
                               and r["D3"]["max_abs_kappa_end_per_mm"] < 0.1)
        res[medium] = r
    return res


def strip(o):
    return {k: (float(v) if np.isscalar(v) else None) for k, v in o.items() if k not in ("amp_profile_per_mm", "s")}


def gait_tests(quick=False):
    res = {}
    make = body_factory()
    for gait in ("crawl", "swim"):
        g = GAITS[gait]
        t0 = time.time()
        a0, out = calibrate_a0(make, gait)
        r = {"a0_fitted": a0, "a0_label": "fitted (brain-side drive amplitude, head curvature)",
             "head_target_per_mm": g["head_target"], "calib_s": time.time() - t0}
        r["main"] = strip(out)
        r["main"]["amp_profile_per_mm"] = [float(x) for x in out["amp_profile_per_mm"]]
        bars = BARS[gait]
        r["G1_speed_pass"] = bool(bars["speed"][0] <= out["speed_mm_s"] <= bars["speed"][1])
        r["G2_wavelength_pass"] = bool(bars["wavelength"][0] <= out["wavelength_L"] <= bars["wavelength"][1])
        r["G3_frequency_pass"] = bool(abs(out["f_body_hz"] / g["f"] - 1) < 0.02)
        r["G4_tail_head_in_range"] = bool(0.15 <= out["tail_head_ratio"] <= 0.5)
        r["a0_le_1"] = bool(a0 < 1.0)
        # wrong control: isotropic drag, same a0
        def make_iso(medium):
            b = Body(cfg=BodyConfig(medium=medium))
            b.Ct = b.Cn = min(b.Ct, b.Cn)
            return b
        iso, _, _ = gait_run(make_iso, gait, a0)
        r["control_isotropic"] = strip(iso)
        r["control_fails_G1"] = bool(iso["speed_mm_s"] < bars["speed"][0])
        # numerics
        if not quick:
            dt0 = Body(cfg=BodyConfig(medium=g["medium"])).dt
            fine_dt, _, _ = gait_run(body_factory(dt=dt0 / 4), gait, a0, record_every=20)
            r["dt_s"] = dt0
            fine_n, _, _ = gait_run(body_factory(n_seg=96), gait, a0)
            r["numerics"] = {"dt_quarter": strip(fine_dt), "n96": strip(fine_n)}
            ch = []
            for alt in (fine_dt, fine_n):
                ch.append(abs(alt["speed_mm_s"] / out["speed_mm_s"] - 1))
                ch.append(abs(alt["wavelength_L"] / out["wavelength_L"] - 1))
            r["numerics"]["max_rel_change"] = float(max(ch))
            r["numerics_pass"] = bool(max(ch) < 0.02)
            # reported toggles, recalibrated a0
            r["toggles"] = {}
            alts = [("muscle.force_gradient", "bbc_head_to_tail")]
            if gait == "crawl":
                alts.append(("env.agar_drag", "rabets_K1p4"))
            for k, v in alts:
                mk = body_factory(toggles={k: v})
                a0t, ot = calibrate_a0(mk, gait)
                r["toggles"][f"{k}={v}"] = {"a0": a0t, **strip(ot)}
        res[gait] = r
        print(gait, json.dumps({k: v for k, v in r.items() if k != "main"}, default=float)[:600], flush=True)
    return res


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--quick", action="store_true")
    ap.add_argument("--only", choices=["dead", "gait"], default=None)
    a = ap.parse_args()
    OUT.mkdir(parents=True, exist_ok=True)
    path = OUT / "body_tests.json"
    res = json.loads(path.read_text()) if path.exists() else {}
    if a.only in (None, "dead"):
        t0 = time.time()
        res["dead_worm"] = dead_worm()
        res["dead_worm"]["wall_s"] = time.time() - t0
        print("dead", json.dumps(res["dead_worm"], default=float), flush=True)
        path.write_text(json.dumps(res, indent=1, default=float))
    if a.only in (None, "gait"):
        res["gait"] = gait_tests(a.quick)
        path.write_text(json.dumps(res, indent=1, default=float))
    print("wrote", path)


if __name__ == "__main__":
    sys.exit(main())
