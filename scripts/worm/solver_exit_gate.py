"""Gate for body.solver_exit = latest (pre-registered in docs/worm/BODY_TESTS.md, 17:48 CST 5 Nov): S1 no
regression and S2 readouts within 10% on P0-P3 (same drives, P3 a0 not recalibrated), S3 the dead zone at wave
amplitudes 0.001 and 0.01, plus a report-only response curve. S4 (A1f, A2f) is `agar_tests.py A1f|A2f latest`.
Run from the repo root. Writes runs/worm/metaworm/se_* (not in git), data/worm/body_runs/solver_exit_gate.json
and solver_exit_gate.png."""
import json
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))
from wormemu.body import metaworm as mw  # noqa: E402

REPO = Path(__file__).resolve().parents[2]
RUNS = REPO / "runs" / "worm" / "metaworm"
OUT = REPO / "data" / "worm" / "body_runs"
PUB = json.load(open(OUT / "metaworm_tests.json"))
KEY_HZ, SWIM, BARS = 1.5, {"f": 1.76, "lam": 1.54}, {"speed_L_s": [0.29, 0.45], "wavelength_L": [1.29, 2.15]}
GAIT = ("f_body_hz", "wavelength_L", "head_amp_kL", "speed_L_s")
LAT = dict(solver_exit="latest")

res = {"P0": {}, "P1": {}, "P2": {}, "P3": {}, "S3": {}}
r = mw.run(RUNS / "se_p0", mode="dead", seconds=10, **LAT)
res["P0"] = {"max_disp_from_rest": r["meta"]["max_disp_from_rest"], "pass": bool(r["meta"]["max_disp_from_rest"] < 1e-9)}

r = mw.run(RUNS / "se_p1", mode="key", key="worm_givenkey_t0_fast.csv", seconds=10, release_at=3.0, **LAT)
rms = mw.Frame(r["meta"], r["X"][0]).shape_rms(r["X"])
res["P1"] = {"end_over_peak": float(rms[-1] / rms.max()), "pass": bool(rms[-1] / rms.max() < 0.10)}

r = mw.run(RUNS / "se_p2", mode="key", key="worm_givenkey_t0_fast.csv", seconds=10, **LAT)
fr = mw.Frame(r["meta"], r["X"][0])
z, g = mw.zigzag(r, 2.0, KEY_HZ, fr), mw.gait(r, KEY_HZ, 2.0, fr)
res["P2"] = {**{k: g[k] for k in GAIT}, "net_disp_L": z["net_disp_L"], "head_lat_f_hz": z["head_lat_f_hz"],
             "pass_disp": bool(z["net_disp_L"] > 0.5), "pass_freq": bool(abs(z["head_lat_f_hz"] - KEY_HZ) / KEY_HZ < 0.05)}
res["P2"]["pass"] = res["P2"]["pass_disp"] and res["P2"]["pass_freq"]

r = mw.run(RUNS / "se_p3", mode="wave", seconds=10, f=SWIM["f"], lam=SWIM["lam"], amp=PUB["P3"]["a0"], **LAT)
g = mw.gait(r, SWIM["f"], 2.0)
res["P3"] = {**{k: g[k] for k in GAIT},
             "pass_speed": bool(BARS["speed_L_s"][0] <= g["speed_L_s"] <= BARS["speed_L_s"][1]),
             "pass_wavelength": bool(BARS["wavelength_L"][0] <= g["wavelength_L"] <= BARS["wavelength_L"][1]),
             "pass_freq": bool(abs(g["f_body_hz"] - SWIM["f"]) / SWIM["f"] < 0.02)}

# S1: no published pass turns to fail
s1 = {}
for t in ("P0", "P1", "P2", "P3"):
    for k, v in res[t].items():
        if k.startswith("pass") and k in PUB[t]:
            s1[f"{t}.{k}"] = {"published": PUB[t][k], "latest": v, "ok": bool(v or not PUB[t][k])}
# S2: readouts within 10%
s2 = {"P1.end_over_peak": (PUB["P1"]["end_over_peak"], res["P1"]["end_over_peak"])}
for t in ("P2", "P3"):
    for k in GAIT:
        s2[f"{t}.{k}"] = (PUB[t]["gait"][k], res[t][k])
s2 = {k: {"published": a, "latest": b, "rel": (b - a) / a, "ok": bool(abs(b - a) / abs(a) <= 0.10)} for k, (a, b) in s2.items()}

# S3: dead zone, both exits; 0.001 and 0.01 are the bar, the rest report-only
amps = [0.001, 0.003, 0.01, 0.03, 0.06, 0.1, 0.157]
curve = {"published": [], "latest": []}
for ex in curve:
    for a in amps:
        r = mw.run(RUNS / f"se_dz_{ex}_{a}", mode="wave", seconds=1.5, f=SWIM["f"], lam=SWIM["lam"], amp=a, solver_exit=ex)
        curve[ex].append(r["meta"]["max_disp_from_rest"] / mw.Frame(r["meta"], r["X"][0]).length)
lat = dict(zip(amps, curve["latest"]))
pub = dict(zip(amps, curve["published"]))
ratio = lat[0.01] / lat[0.001] if lat[0.001] > 0 else float("inf")
res["S3"] = {"amps": amps, "max_disp_L": curve, "ratio_0.01_over_0.001": ratio,
             "pass": bool(lat[0.001] > 0 and lat[0.01] > 0 and 5 <= ratio <= 20 and pub[0.001] == 0 and pub[0.01] == 0)}
res["S1"] = {"checks": s1, "pass": all(v["ok"] for v in s1.values())}
res["S2"] = {"checks": s2, "pass": all(v["ok"] for v in s2.values())}
json.dump(res, open(OUT / "solver_exit_gate.json", "w"), indent=1)
print("S1", res["S1"]["pass"], {k: (v["published"], v["latest"]) for k, v in s1.items()})
print("S2", res["S2"]["pass"], {k: round(v["rel"], 4) for k, v in s2.items()})
print("S3", res["S3"]["pass"], "ratio", round(ratio, 2), "latest", [f"{x:.3g}" for x in curve["latest"]],
      "published", [f"{x:.3g}" for x in curve["published"]])

import matplotlib  # noqa: E402
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
fig, ax = plt.subplots(1, 2, figsize=(11, 4.2))
floor = 1e-5
for ex, c in (("published", "tab:gray"), ("latest", "tab:orange")):
    y = np.array(curve[ex])
    ax[0].plot(amps, np.where(y > 0, y, floor), "o-", color=c, label=f"solver_exit = {ex}")
ax[0].axhline(floor, color="k", lw=0.5, ls=":")
ax[0].text(amps[0], floor * 1.3, "0 exactly (drawn at 1e-5)", fontsize=8)
ax[0].set(xscale="log", yscale="log", xlabel="prescribed wave amplitude (fraction of max force)",
          ylabel="largest displacement from rest in 1.5 s (L)", title="S3: dead zone (swim wave, 1.5 s)")
ax[0].legend(fontsize=8)
names = list(s2)
ax[1].barh(range(len(names)), [100 * s2[k]["rel"] for k in names],
           color=["tab:green" if s2[k]["ok"] else "tab:red" for k in names])
ax[1].axvspan(-10, 10, color="tab:green", alpha=0.08)
ax[1].set_yticks(range(len(names)), names, fontsize=8)
ax[1].set(xlabel="latest vs published (%)", title="S2: readouts (bar: within 10%)")
fig.tight_layout()
fig.savefig(OUT / "solver_exit_gate.png", dpi=110)
print("figure", OUT / "solver_exit_gate.png")
