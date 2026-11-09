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

Result (8 Nov 21:27, code f8e7699, measured; runs/worm/fit/maturation_f8e7699/): FALSIFIED, helps in 0 of 3.
  rmse18 default -> matured (mV): AIY 10.60 -> 23.92, AFD 49.89 -> 49.83, AWA 21.96 -> 21.96; mask on and off identical
  (brain.py _density: "on" keeps a published fit's channel set, and all three are published fits). Neutral |diff| 0.0.
  s* AIYL 0.627, AFDL 0.358 (converged, inside), AWAL 4.0 (at the bound); 105 bio-s, 123 s wall for the three.
  Why, per cell (inferred from the traces):
  - AIY: the target is Ca at -53 mV, but one multiplier scales the Ca channels too, so the cell meets that Ca at a
    different voltage: rest moved -51.3 -> -43.8 mV (data -53.5) and every step response grew. A Ca set point does not
    pin the voltage when the rule scales the Ca conductance itself.
  - AFD: the error is the hyperpolarising branch (steady -227 mV at -15 pA, data -91): a missing conductance near
    -90 mV, which no uniform multiplier supplies.
  - AWA: the default membrane is Liu 2018's (senses_chem inserts its own channels and zeroes BAAIWorm's), which no
    dens_* multiplier reaches, so the rule ran to its bound with no effect. Needs the Liu 2018 densities exposed as
    g_scale names (request in the night file).

Retry with the bulk Ca pool (pre-registered 8 Nov 23:33 CST, before any run that reads the bulk pool; Director 21:55
kept maturation open for this). Same cells, rule, protocol, forms, neutral check, primary and bar as above. Changes:
  sensor    the rule senses the bulk cytosolic pool (maturation ca_read "bulk": mech/capool's ca_bulk_uM, toggle
            ca_bulk = cadifpmp, wbrain2's port of NEURON's cadifpmp), not Eq. 28's microdomain.
  pool on   ca_bulk = cadifpmp in every arm (default, matured, neutral). One more arm, the default without the pool on
            the same checkout, checks that the pool is a readout: features equal (max |diff| reported, bar 0.0 mV).
            The 21:27 numbers are not the comparison: merges since f8e7699 changed other defaults.
  target    Ca of the bulk pool clamped at the class's measured rest. The pool's floor is its pump's 10 nM, below the
            [20, 150] nM range; a target there is reported as outside, not clipped (as before).
  guard     the run stops if the checkout has no ca_bulk toggle (single_cell_sanity drops unknown toggles silently).
  call      run with the argument --ca-read=bulk; output runs/worm/fit/maturation_bulk_<sha>/.
Prediction (inferred from wbrain2's floor table and the 21:27 traces, written before the run): AWA unchanged (its Liu
2018 membrane is out of reach of dens_*, and its bulk Ca is flat below -65 mV); AFD not helped (its error is a missing
conductance on the hyperpolarising branch); AIY may move. So the falsifier (fewer than 2 of 3) is likely met again;
the retry's value is whether a Ca set point on a sensor with range pins AIY's voltage. Either way maturation stays off.

Deviation (9 Nov 00:17 CST, written after the first bulk run crashed and before the rerun). Run 1 (1198812, Mac,
00:14, measured): default_mask_on with the pool on gave rmse18 AIY 10.60, AFD 49.89, AWA 21.96 mV (the 21:27 values);
the matured arm's sensing finished (s AIYL 0.627, AFDL 0.358, AWAL 4.0 at the bound; bulk targets 62.6, 10.7, 9.1 nM,
AFD and AWA below the [20, 150] nM range at the pump floor, as predicted); then its scoring sweeps stopped inside
cabulk.mod's KINETIC block ("scopmath library error: Convergence not achieved"). The pool writes neither cai nor ica,
so it cannot move a feature; the readout-check arm measures that (bar 0.0 mV). So, with --score-pool=off, the matured
arm senses and matures on a brain with the pool on (unchanged), then scores the same multipliers (a Frozen copy) on a
fresh build without the pool. The sensing brain stays in NEURON, unstimulated, as earlier arms' cells already do.
Everything else as pre-registered. The crash itself goes to wbrain2 (night file, Requests).

Result of the retry (9 Nov 00:16-00:23, 1198812, Mac, --score-pool=off, measured; runs/worm/fit/maturation_bulk_1198812/):
FALSIFIED again, helps in 0 of 3 (mask on and off identical). rmse18 default -> matured: AIY 10.60 -> 23.92, AFD
49.89 -> 49.83, AWA 21.96 -> 21.96 mV. Readout check (the default with and without the pool) max |diff| 0.0 mV, so the
deviation changes no feature; neutral 0.0 mV. s* AIYL 0.627, AFDL 0.358, AWAL 4.0 (bound): the same as the Eq. 28 run
to 3 digits. Why (derived): at a steady resting set point, the rule stops where the sensed Ca equals the Ca the cell had
when clamped at the measured rest; any sensor that is a steady monotone function of the soma Ca current then stops at
the same s, so moving the sensor from Eq. 28 to the bulk pool could not change the answer. The bulk pool's 65x range
matters for how fast the rule moves, not where it ends. Bulk targets 62.6, 10.7, 9.1 nM (AFD and AWA at the pump floor,
outside [20, 150] nM). Maturation stays off; it stops here until a worm source gives per-channel rates (21:27 note).

Usage (backhouse): python scripts/worm/fit/maturation_ephys.py OUT.json [FEATURES.npz] [--ca-read=bulk] [--score-pool=off]
"""
from __future__ import annotations

import json
import sys
import time
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[3]
CA_READ = "bulk" if "--ca-read=bulk" in sys.argv else "eq28"
SCORE_NOPOOL = "--score-pool=off" in sys.argv
sys.argv = [a for a in sys.argv if not a.startswith(("--ca-read", "--score-pool"))]
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
POOL = {"ca_bulk": "cadifpmp"} if CA_READ == "bulk" else {}
if POOL:
    from wormemu.mech import capool                    # the guard: this checkout must define the bulk pool
    assert "cadifpmp" in getattr(capool, "BULK", ()), "no ca_bulk toggle in this checkout"


def matured_build(mode, key):
    def build(**kw):
        br = ORIG(**kw)
        cls = [c for c in CLASSES if fit2.CELL[c] in br.cell_names]
        if mode == "neutral":
            br.mechs.append(MT.Frozen(len(br.cell_names), np.arange(len(br.cell_names)),
                                      np.ones(len(br.cell_names))))
            return br
        t0 = time.time()
        tg = {fit2.CELL[c]: MT.clamp_ca(br, fit2.CELL[c], V.SIGN[f"rest_{c}"].mean, ca_read=CA_READ) for c in cls}
        res = MT.mature(br, tg, max_s=300.0, ca_read=CA_READ)
        res["inside_range"] = [MT.P["mat_ca_tgt_lo_uM"] <= x <= MT.P["mat_ca_tgt_hi_uM"] for x in res["target_uM"]]
        res["wall_s"] = time.time() - t0
        LOG[key] = res
        print(key, json.dumps({k: v for k, v in res.items() if k != "trace"}), flush=True)
        if SCORE_NOPOOL and POOL:                     # the deviation above: score the multipliers without the pool
            fz, names = br.mechs[-1], list(br.cell_names)
            assert isinstance(fz, MT.Frozen)
            ex = {k: v for k, v in (kw.get("extra") or {}).items() if k not in POOL}
            br = ORIG(**{**kw, "extra": ex})
            assert list(br.cell_names) == names, "the scoring build has other cells"
            br.mechs.append(MT.Frozen(fz.n, fz.cells, fz.s.copy(), fz.channels))
            res["scored_without_pool"] = True
        return br
    return build


def run(mode, extra, key):
    S.build = ORIG if mode == "default" else matured_build(mode, key)
    try:
        t0 = time.time()
        r = E.score({**extra, **POOL}, CLASSES)
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
    if POOL:                                          # the pool is a readout: the default without it is identical
        pool = dict(POOL)
        POOL.clear()
        nop = run("default", {}, "default_nopool")
        POOL.update(pool)
        res["pool_readout_max_abs_diff_mV"] = max(
            float(np.max(np.abs(np.array(nop[c]["model"][n]) - np.array(res["default_mask_on"][c]["model"][n]))))
            for c in CLASSES for n in E.NAMES)
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
    res["ca_read"], res["toggles_added"] = CA_READ, POOL
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(res, indent=1, default=float))
    print("neutral max |diff|", res["neutral_max_abs_diff_mV"], "verdict", json.dumps(verdict), flush=True)


if __name__ == "__main__":
    main()
