"""The imaging noise per frame in Atanas et al. 2023's traces (weki, 8 Nov 2026; FIT_GENERAL.md section 7).

Why: the battery's two GCaMP signs (pc3_frac, gcamp_range) read the model through observation's additive imaging
noise, obs_noise_dff (0.03 dF/F, guessed, bounds 0 to 0.2, one of the 368 fit numbers). On the f8e7699 template the
model's signal under that noise is a median SD of 0.0018 dF/F (measured, 8 Nov 23:20), so both signs read the noise:
white noise of SD s has P95 - P5 = 3.29 s, which is 0.66 at the bound 0.2, inside the gcamp_range bar 0.567-0.983.
A fit that may move obs_noise_dff can pass that sign with no brain activity at all. The noise is a property of the
microscope and pipeline, so it should be fixed per experiment from the dataset itself, like the scene_* numbers.

Pre-registered (8 Nov 23:16 CST, before the script ran):
  data      the 60 open atanas2023_main animals (heldout.exclude runs before any file is opened; the 20 locked animals,
            pradhan2025, dag2023 and the scrambled-identity copy are never read), gcamp/traces_array_F_Fmean, finite
            columns, the same trace atanas_pc3.py scores. IDS (optional) restricts to a list of animal ids: the 60 ids
            atanas_pc3.py read, since the backhouse folder also holds 11 files outside the main 80.
  estimate  per neuron, from the frame-to-frame differences: D1 = var(x[t+1] - x[t]) / 2, D2 = var(x[t+2] - x[t]) / 2.
            For white noise of SD s on a signal whose autocovariance falls linearly over two frames (an exponential,
            as a first-order indicator gives), D1 = s^2 + a and D2 = s^2 + 2a, so s^2 = 2 D1 - D2 (the "linear"
            estimate). D1 alone is an upper bound (all frame-to-frame change counted as noise). Per animal the
            median over neurons of each; reported as P5, median, P95 over the 60 animals, in F / mean F units.
  use       the median animal's linear estimate becomes the measured (derived) value of obs_noise_dff for the Atanas
            experiment, proposed to the Director as a fixed per-experiment instrument number (not fitted); the
            upper bound is reported beside it. Nothing in the model is scored or changed by this script.
  falsifier if the linear estimate is negative or above D1 for most animals, the white-plus-smooth reading is wrong
            and the number is not proposed.

Usage: python scripts/worm/fit/atanas_noise.py H5_DIR OUT.json [IDS]
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import h5py
import numpy as np

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "src"))
from wormemu import heldout  # noqa: E402


def noise(x):
    """Per-neuron (D1, linear) noise SDs of a frames x neurons trace."""
    d1 = np.var(np.diff(x, axis=0), axis=0) / 2.0
    d2 = np.var(x[2:] - x[:-2], axis=0) / 2.0
    lin = 2.0 * d1 - d2
    return np.sqrt(d1), np.sqrt(np.clip(lin, 0.0, None)), float(np.mean(lin < 0))


def animal(path: Path) -> dict:
    with h5py.File(path, "r") as f:
        x = np.asarray(f["gcamp/traces_array_F_Fmean"], float)
    x = x[:, np.isfinite(x).all(axis=0)]
    up, lin, neg = noise(x)
    return {"id": path.name.replace("-data.h5", ""), "n_neurons": int(x.shape[1]),
            "upper": float(np.median(up)), "linear": float(np.median(lin)), "frac_negative": neg,
            "sd_total": float(np.median(x.std(axis=0)))}


def main(h5_dir, out, ids_file=None):
    ids = sorted(p.name.replace("-data.h5", "") for p in Path(h5_dir).glob("*-data.h5"))
    if ids_file:
        keep = set(Path(ids_file).read_text().split())
        ids = [i for i in ids if i in keep]
    open_ids = heldout.exclude("atanas2023", ids)
    rows = [animal(Path(h5_dir) / f"{i}-data.h5") for i in open_ids]
    summ = {}
    for k in ("upper", "linear", "sd_total", "frac_negative"):
        a = np.array([r[k] for r in rows])
        summ[k] = {"p5": float(np.percentile(a, 5)), "median": float(np.median(a)), "p95": float(np.percentile(a, 95))}
    summ["n_animals"] = len(rows)
    summ["linear_above_upper"] = int(sum(r["linear"] > r["upper"] for r in rows))
    Path(out).write_text(json.dumps({"summary": summ, "animals": rows}, indent=1))
    print(json.dumps(summ, indent=1))


if __name__ == "__main__":
    main(*sys.argv[1:4])
