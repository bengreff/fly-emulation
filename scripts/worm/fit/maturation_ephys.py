"""Maturation on the recorded cells (weki, 8 Nov 2026; fit/maturation.py; brief item 2).

Pre-registered (8 Nov 21:12 CST, written before the first maturation run on a NEURON cell):
  cells     AIYL, AFDL, AWAL as wtriage's ephys_score builds them (single_cell_sanity.build: no synapses or gaps,
            ledger values, AWA's default membrane liu2018); RIM is sealed and never built or scored.
  rule      fit/maturation.py at its Spec templates: O'Leary 2014 integral control on the cell's Ca, one density
            multiplier s per cell on every regulated channel (leak and NCA static), s in [0.25, 4], at most 300 bio-s.
  target    form vrest: Ca of the built cell voltage-clamped at its class's measured rest (vitals.SIGN rest_AIY -53,
            rest_AFD -78, rest_AWA -75.3 mV). Inside [20, 150] nM or reported as outside.
  protocol  ephys_score.score unchanged (FIT2's training sweeps -15..+35 pA, its four features, FIT2's training
            features file); the maturation's Frozen multipliers ride through every sweep's reset.
  forms     default and matured, each with the expression mask on (default) and off (ephys_score's mask_off).
  neutral   s = 1 frozen on every cell must give features identical to the default (max |diff| = 0).
  primary   per class, RMSE over the 18 non-baseline features (early peak, steady, after x 6 sweeps); the 24-feature
            RMSE and the baselines reported. The baseline is not a clean test: the target came from a measured rest.
  bar       maturation helps if its 18-feature RMSE is lower than the default's by more than 0.5 mV in at least 2 of the
            3 classes with the mask on (0.5 mV guessed as a meaningful step). Falsifier: fewer than 2. Either way
            maturation stays off (neutral) until a battery run and Ben's go; this is a diagnostic, not an adoption.
  flags     s at a bound, not converged, target outside the range: each reported per cell.

Usage (backhouse): python scripts/worm/fit/maturation_ephys.py OUT.json [FEATURES.npz]
"""
from __future__ import annotations

import json
import sys
import time
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[3]
OUT = Path(sys.argv[1])
FEATS = sys.argv[2:3]
sys.argv = [sys.argv[0]] + FEATS                      # ephys_score reads its features path from argv
sys.path.insert(0, str(ROOT / "scripts" / "worm" / "triage"))
sys.path.insert(0, str(ROOT / "src"))
import ephys_score as E  # noqa: E402
from wormemu.fit import maturation as MT  # noqa: E402
from wormemu.fit import vitals as V  # noqa: E402

S, fit2 = E.S, E.fit2
CLASSES = ["AIY", "AFD", "AWA"]
ORIG = S.build
LOG = {}


def matured_build(mode, key):
    def build(**kw):
        br = ORIG(**kw)
        cls = [c for c in CLASSES if fit2.CELL[c] in br.cell_names]
        if mode == "neutral":
            br.mechs.append(MT.Frozen(len(br.cell_names), np.arange(len(br.cell_names)),
                                      np.ones(len(br.cell_names))))
            return br
        t0 = time.time()
        tg = {fit2.CELL[c]: MT.clamp_ca(br, fit2.CELL[c], V.SIGN[f"rest_{c}"].mean) for c in cls}
        res = MT.mature(br, tg, max_s=300.0)
        res["inside_range"] = [MT.P["mat_ca_tgt_lo_uM"] <= x <= MT.P["mat_ca_tgt_hi_uM"] for x in res["target_uM"]]
        res["wall_s"] = time.time() - t0
        LOG[key] = res
        print(key, json.dumps({k: v for k, v in res.items() if k != "trace"}), flush=True)
        return br
    return build


def run(mode, extra, key):
    S.build = ORIG if mode == "default" else matured_build(mode, key)
    try:
        t0 = time.time()
        r = E.score(extra, CLASSES)
    finally:
        S.build = ORIG
    for cls, x in r.items():
        if "model" in x:
            m = np.array([x["model"][n] for n in E.NAMES]).T
            d = np.array([x["data"][n] for n in E.NAMES]).T
            x["rmse18_mV"] = float(np.sqrt(np.mean((m[:, 1:] - d[:, 1:]) ** 2)))
    r["_wall_s"] = time.time() - t0
    return r


def main():
    res = {}
    for mask, extra in (("mask_on", {}), ("mask_off", {"expression_map": "off"})):
        for mode in ("default", "matured"):
            key = f"{mode}_{mask}"
            res[key] = run(mode, extra, key)
            print(key, {c: (round(res[key][c].get("rmse18_mV", np.nan), 2), round(res[key][c].get("rmse_mV", np.nan), 2))
                        for c in CLASSES}, flush=True)
    neu = run("neutral", {}, "neutral")
    res["neutral_max_abs_diff_mV"] = max(
        float(np.max(np.abs(np.array(neu[c]["model"][n]) - np.array(res["default_mask_on"][c]["model"][n]))))
        for c in CLASSES for n in E.NAMES)
    verdict = {}
    for mask in ("mask_on", "mask_off"):
        dd = {c: res[f"default_{mask}"][c].get("rmse18_mV", np.nan) - res[f"matured_{mask}"][c].get("rmse18_mV", np.nan)
              for c in CLASSES}
        verdict[mask] = {"improvement_mV": dd, "helps": int(sum(v > 0.5 for v in dd.values())) >= 2}
    res["verdict"] = verdict
    res["maturation"] = LOG
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(res, indent=1, default=float))
    print("neutral max |diff|", res["neutral_max_abs_diff_mV"], "verdict", json.dumps(verdict), flush=True)


if __name__ == "__main__":
    main()
