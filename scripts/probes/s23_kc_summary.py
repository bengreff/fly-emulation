"""s23 MB descriptive run (DECISIONS 23 Oct 23:42): KCs at Turner's measured 0.1 Hz via class:KC|noise. Picks
sigma*_KC from the seed-12 grid by the registered rule and reports the descriptive numbers: KC rate stats, class
means, the 11 Huang types, Spearman rho of model rate with total input synapses, and the SD of log10 rate across the
types (model against data). Huang 2024 is spent: consistency only, nothing scored or adopted.

    python3 scripts/probes/s23_kc_summary.py   # reads runs/s23/kc/*.json -> runs/s23/kc/summary.json
"""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np
from scipy.stats import spearmanr

KC = Path("runs/s23/kc")
TURNER = 0.1
# s22 table (docs/research/s22_mb_type_spread.md): total input synapses per cell (male-cns v1.0) and Huang 2024
# medians (spent)
TYPES = {"MBON11": (23441, 34.8), "PPL101": (19568, 20.4), "PPL106": (8560, 14.0), "MBON12": (6983, 20.9),
         "PPL103": (15788, 11.7), "MBON13": (6471, 15.6), "MBON14": (6296, 15.2), "PPL105": (8636, 8.5),
         "MBON17": (2010, 13.1), "MBON18": (8512, 9.8), "PPL104": (3586, 7.7)}


def describe(d: dict) -> dict:
    m = np.array([d["type_hz"][t] for t in TYPES])
    inp = np.array([v[0] for v in TYPES.values()])
    data = np.array([v[1] for v in TYPES.values()])
    rho, p = spearmanr(m, inp)
    pos = m > 0
    return {"kc_noise": d["kc_noise"], "seed": d["seed"], "kc_hz": d["class_hz"]["KC"],
            "kc_active": d["class_active"]["KC"], "kc_hz_sd": d.get("kc_hz_sd"),
            "kc_hz_q50_q90_q99": d.get("kc_hz_quantiles"), "class_hz": d["class_hz"],
            "whole_brain_hz": d["whole_brain_hz"], "type_hz": {t: round(float(x), 2) for t, x in zip(TYPES, m)},
            "rho_rate_vs_input": round(float(rho), 3), "rho_p": round(float(p), 4),
            "log10_sd_model": round(float(np.std(np.log10(m[pos]))), 3) if pos.all() else None,
            "log10_sd_data": round(float(np.std(np.log10(data))), 3),
            "range_model": [round(float(m.min()), 1), round(float(m.max()), 1)]}


def main() -> None:
    grid = {}
    for f in sorted(KC.glob("kc*_s12.json")):
        d = json.loads(f.read_text())
        grid[d["kc_noise"]] = describe(d)
    out = {"grid_s12": grid}
    ok = {s: r for s, r in grid.items() if r["kc_hz"] > 0}
    inband = {s: r for s, r in ok.items() if 0.05 <= r["kc_hz"] <= 0.2}
    if inband:
        out["sigma_star"] = min(inband, key=lambda s: abs(np.log10(inband[s]["kc_hz"] / TURNER)))
    elif ok:
        ss = sorted(grid)
        lo = [s for s in ss if grid[s]["kc_hz"] < 0.05]
        hi = [s for s in ss if grid[s]["kc_hz"] > 0.2]
        if lo and hi and grid[lo[-1]]["kc_hz"] > 0:
            a, b = lo[-1], hi[0]
            ya, yb = np.log10(grid[a]["kc_hz"]), np.log10(grid[b]["kc_hz"])
            out["sigma_interp"] = round(float(a + (np.log10(TURNER) - ya) * (b - a) / (yb - ya)), 3)
    for f in sorted(KC.glob("kc*_s13.json")):
        d = json.loads(f.read_text())
        out.setdefault("confirm_s13", {})[d["kc_noise"]] = describe(d)
    ref = Path("runs/s23/fc/mb_m10f7_s12.json")
    if ref.exists():
        out["m10f7_no_kc_s12"] = describe({**json.loads(ref.read_text()), "kc_noise": 0.0})
    KC.mkdir(parents=True, exist_ok=True)
    (KC / "summary.json").write_text(json.dumps(out, indent=1))
    print(json.dumps({k: v for k, v in out.items() if k != "grid_s12"}, indent=1)[:3000])
    for s, r in sorted(grid.items()):
        print(s, r["kc_hz"], r["kc_active"], r["rho_rate_vs_input"], r["log10_sd_model"], r["range_model"])


if __name__ == "__main__":
    main()
