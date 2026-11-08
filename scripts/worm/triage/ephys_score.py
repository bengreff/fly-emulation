"""Item 3 / row 5 (wtriage, 8 Nov 2026): our own single cells through the recorded current-clamp protocol, scored.

Pre-registered (before the first run): the cells AIYL, AFDL, AWAL as the default brain builds them (ledger values via
at_ledger.patch, single_cell_sanity.build: no synapses, no gaps, the default channel library and densities, AWA's
default membrane liu2018 and BAAIWorm's as the second form); FIT2's protocol and features unchanged (fit2.simulate:
2 s settle, step 1-6 s, 7 s sweeps; fit2.features: baseline, early peak, steady state, after-step, 2 ms smoothing)
on FIT2's training sweeps only (-15, -5, +5, +15, +25, +35 pA). Data: FIT2's own train_features.npz (computed from the
Naudin 2022 and Liu 2018 files by fit2.run; this script never opens a recording, and never RIM's). Score: RMSE over
the 24 features per class (FIT2's training loss, mV), plus each feature's model - data. Reference: FIT2's best
training loss per class where it exists (that fit changes densities through the map; the default does not).
RIM is sealed and is not scored.

Usage (backhouse): python ephys_score.py [FEATURES.npz]
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "scripts" / "worm"))
import at_ledger  # noqa: E402

at_ledger.patch()
import fit2  # noqa: E402
import single_cell_sanity as S  # noqa: E402

FEATS = Path(sys.argv[1]) if len(sys.argv) > 1 else Path.home() / "worm-night/wexcite/fit2/train_features.npz"
NAMES = ("baseline", "early_peak", "steady", "after")


def score(extra, classes):
    br = S.build(cells=[fit2.CELL[c] for c in classes], extra=extra)
    amps = fit2.AMPS_PA[fit2.FIT2_SWEEPS]
    V = fit2.simulate(br, amps)
    t = np.arange(1, fit2.T_END + 1, dtype=float)
    data = np.load(FEATS)
    out = {}
    for cls in classes:
        c = br.cell_names.index(fit2.CELL[cls])          # the brain's own cell order, not the class list's
        if not np.isfinite(V[c]).all():
            out[cls] = dict(finite=False)
            continue
        m, d = fit2.features(t, V[c], amps), data[cls]
        diff = m - d
        out[cls] = dict(rmse_mV=float(np.sqrt(np.mean(diff ** 2))), amps_pA=amps.tolist(),
                        model={n: m[:, j].round(2).tolist() for j, n in enumerate(NAMES)},
                        data={n: d[:, j].round(2).tolist() for j, n in enumerate(NAMES)},
                        v_max=float(V[c].max()), v_min=float(V[c].min()), cell=br.cell_names[c])
    return out


def main():
    res = {"default": score({}, ["AIY", "AFD", "AWA"]),
           "awa_baaiworm": score({"awa_membrane": "baaiworm"}, ["AWA"]),
           # diagnostic (cause, not a candidate): BAAIWorm's per-cell fits without the CeNGEN mask (brain.py:430-434)
           "mask_off": score({"expression_map": "off"}, ["AIY", "AFD", "AWA"])}
    for form, r in res.items():
        for cls, x in r.items():
            print(form, cls, "rmse %.2f mV" % x.get("rmse_mV", np.nan), "base", x.get("model", {}).get("baseline"),
                  "data", x.get("data", {}).get("baseline"), flush=True)
    p = ROOT / "runs/worm/triage/ephys_score.json"
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(res, indent=1))
    print(p)


if __name__ == "__main__":
    main()
