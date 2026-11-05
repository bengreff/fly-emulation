"""Pre-registered tests of the ported MetaWorm body (docs/worm/BODY_TESTS.md, 'Ported body: MetaWorm').

P0 dead body, P1 release, P2 published periodic gait (t0_fast key, zigzag reproduction), P2b default key turn2,
P3 prescribed sine wave at the Fang-Yen 2010 swim means with a0 calibrated to head kappa*L = 4.5.
Raw frames go to runs/worm/metaworm/ (not in git); readouts to data/worm/body_runs/metaworm_tests.json.
Single-threaded, ~15 s wall per 10 s run on the Mac.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))
from wormemu.body import metaworm as mw  # noqa: E402

REPO = Path(__file__).resolve().parents[2]
RUNS = REPO / "runs" / "worm" / "metaworm"
OUT = REPO / "data" / "worm" / "body_runs" / "metaworm_tests.json"
KEY_HZ = 30 / 20  # t0_fast and turn2 keys: 20 rows at the 30 Hz control rate
SWIM = {"f": 1.76, "lam": 1.54, "head_target_kL": 4.5}
BARS = {"speed_L_s": [0.29, 0.45], "wavelength_L": [1.29, 2.15], "freq_rel": 0.02}


def save(res):
    OUT.parent.mkdir(parents=True, exist_ok=True)
    json.dump(res, open(OUT, "w"), indent=1)


def main():
    RUNS.mkdir(parents=True, exist_ok=True)
    res = json.load(open(OUT)) if OUT.exists() and "--fresh" not in sys.argv else {}

    if "P0" not in res:
        r = mw.run(RUNS / "p0_dead", mode="dead", seconds=10)
        d = r["meta"]["max_disp_from_rest"]
        res["P0"] = {"max_disp_from_rest": d, "bar": 1e-9, "pass": bool(d < 1e-9), "wall_s": r["meta"]["wall_s"]}
        save(res)
        print("P0", res["P0"])

    if "P1" not in res:
        r = mw.run(RUNS / "p1_release", mode="key", key="worm_givenkey_t0_fast.csv", seconds=10, release_at=3.0)
        fr = mw.Frame(r["meta"], r["X"][0])
        rms = fr.shape_rms(r["X"])
        res["P1"] = {"peak_rms_L": float(rms.max()), "t_peak_s": float(r["t"][rms.argmax()]),
                     "end_rms_L": float(rms[-1]), "end_over_peak": float(rms[-1] / rms.max()), "bar": 0.10,
                     "pass": bool(rms[-1] / rms.max() < 0.10),
                     "rms_at_s": {str(s): float(rms[int(round(s * 30))]) for s in (3, 4, 5, 6, 8, 10)}}
        save(res)
        print("P1", res["P1"])

    for name, key in (("P2", "worm_givenkey_t0_fast.csv"), ("P2b", "worm_givenkey_turn2.csv")):
        if name in res:
            continue
        r = mw.run(RUNS / name.lower(), mode="key", key=key, seconds=10)
        fr = mw.Frame(r["meta"], r["X"][0])
        z = mw.zigzag(r, 2.0, KEY_HZ, fr)
        g = mw.gait(r, KEY_HZ, 2.0, fr)
        out = {"key": key, "zigzag": z, "gait": {k: v for k, v in g.items() if not isinstance(v, list)}}
        if name == "P2":
            out["pass_disp"] = bool(z["net_disp_L"] > 0.5)
            out["pass_freq"] = bool(abs(z["head_lat_f_hz"] - KEY_HZ) / KEY_HZ < 0.05)
            out["pass"] = out["pass_disp"] and out["pass_freq"]
        res[name] = out
        save(res)
        print(name, out)

    if "P3" not in res:
        def wave(a0, tag):
            r = mw.run(RUNS / f"p3_{tag}", mode="wave", seconds=10, f=SWIM["f"], lam=SWIM["lam"], amp=a0)
            return r, mw.gait(r, SWIM["f"], 2.0)
        lo, hi = 0.0, 1.0
        r, g = wave(hi, "a1")
        hist = [(hi, g["head_amp_kL"])]
        a0 = hi
        if g["head_amp_kL"] >= SWIM["head_target_kL"]:
            for i in range(14):
                a0 = 0.5 * (lo + hi)
                r, g = wave(a0, f"b{i}")
                hist.append((a0, g["head_amp_kL"]))
                print("  a0", a0, "head kL", g["head_amp_kL"], "speed", g["speed_L_s"])
                if abs(g["head_amp_kL"] - SWIM["head_target_kL"]) / SWIM["head_target_kL"] < 0.01:
                    break
                if g["head_amp_kL"] < SWIM["head_target_kL"]:
                    lo = a0
                else:
                    hi = a0
        r, g = wave(a0, "final")  # same a0 again under a fixed name for the viewer (deterministic)
        fr = mw.Frame(r["meta"], r["X"][0])
        U = g["speed_L_s"] * fr.length  # sim units / s
        out = {"a0": a0, "a0_label": "fitted (brain-side drive amplitude)", "calibration": hist,
               "gait": {k: v for k, v in g.items() if not isinstance(v, list)},
               "amp_profile_kL": g["amp_profile_kL"], "s": g["s"],
               "reynolds_si": float(abs(U) * fr.length / 1e-6),
               "pass_speed": bool(BARS["speed_L_s"][0] <= g["speed_L_s"] <= BARS["speed_L_s"][1]),
               "pass_wavelength": bool(BARS["wavelength_L"][0] <= g["wavelength_L"] <= BARS["wavelength_L"][1]),
               "pass_freq": bool(abs(g["f_body_hz"] - SWIM["f"]) / SWIM["f"] < BARS["freq_rel"]),
               "zigzag": mw.zigzag(r, 2.0, SWIM["f"], fr), "frames": str(RUNS / "p3_final")}
        res["P3"] = out
        save(res)
        print("P3", {k: v for k, v in out.items() if k not in ("amp_profile_kL", "s")})


if __name__ == "__main__":
    main()
