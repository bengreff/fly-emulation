"""The whole-brain GCaMP vital sign's measured range (weki, 8 Nov 2026; VITAL_SIGNS.md, sign pc3_frac).

Pre-registered (8 Nov 20:35 CST, before any model run was scored on it):
  data      Atanas et al. 2023 (Cell; Zenodo 8185377), the atanas2023_main processed_h5 files, the 60 animals the
            held-out lock leaves open (heldout.exclude("atanas2023", ...) runs before any file is opened; the 20
            locked animals, pradhan2025 and dag2023 are never read). The scrambled-identity copy is not read.
  trace     gcamp/traces_array_F_Fmean (F / mean F per neuron), z-scored per neuron inside each window.
  statistic the fraction of the variance in the top 3 principal components (wormemu.fit.vitals.pc_frac), per animal:
              whole     over the whole recording (DEBUG_TRIAGE challenge iii as written)
              windowed  over non-overlapping windows of the model run's scored length (W s, default 195 s: a 200 s
                        run less the 5 s settle), the median over an animal's windows. The model is scored on this
                        one, since the fraction depends on the window length (fewer frames, fewer slow modes).
  neurons   each animal's ROI count is kept; the model is scored on random subsets of the median open ROI count.
  bar       the 5th to 95th percentile over the 60 open animals of the windowed statistic (vitals.SIGN["pc3_frac"]).
  range     added 8 Nov 20:57 CST, before any model run was scored on it: per neuron P95 - P5 of F / mean F in each
            window (vitals.gcamp_range), the median over neurons, then over windows; the bar its 5th to 95th
            percentile over animals. The model's dF/F0 is against F0 at rest, Atanas's against the mean F: the same
            range when the mean sits near rest (inferred).

Usage: python scripts/worm/fit/atanas_pc3.py H5_DIR OUT.json [WINDOW_S]
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
from wormemu.fit.vitals import PC_K, gcamp_range, pc_frac  # noqa: E402


def animal(path: Path, window_s: float) -> dict:
    with h5py.File(path, "r") as f:
        x = np.asarray(f["gcamp/traces_array_F_Fmean"], float)
        ts = np.asarray(f["timing/timestamp_confocal"], float)
    ok = np.isfinite(x).all(axis=0)
    x = x[:, ok]
    dt = float(np.median(np.diff(ts)))
    w = int(round(window_s / dt))
    starts = range(0, x.shape[0] - w + 1, w)
    wins = [pc_frac(x[a:a + w])[0] for a in starts]
    rng = [gcamp_range(x[a:a + w]) for a in starts]
    return {"id": path.name.replace("-data.h5", ""), "n_neurons": int(ok.sum()), "n_frames": int(x.shape[0]),
            "dt_s": dt, "frames_per_window": w, "whole": pc_frac(x)[0], "windows": wins,
            "windowed": float(np.median(wins)) if wins else None,
            "gcamp_range": float(np.median(rng)) if rng else None}


def main(h5_dir, out, window_s=195.0):
    ids = sorted(p.name.replace("-data.h5", "") for p in Path(h5_dir).glob("*-data.h5"))
    open_ids = heldout.exclude("atanas2023", ids)
    rows = [animal(Path(h5_dir) / f"{i}-data.h5", window_s) for i in open_ids]
    win = np.array([r["windowed"] for r in rows if r["windowed"] is not None])
    whole = np.array([r["whole"] for r in rows])
    nn = np.array([r["n_neurons"] for r in rows])
    gr = np.array([r["gcamp_range"] for r in rows if r["gcamp_range"] is not None])
    pct = lambda a: {f"p{q}": float(np.percentile(a, q)) for q in (5, 25, 50, 75, 95)} | {
        "mean": float(a.mean()), "sd": float(a.std(ddof=1)), "n": int(len(a))}
    res = {"source": "Atanas et al. 2023 Cell, Zenodo 8185377, processed_h5 (atanas2023_main)",
           "trace": "gcamp/traces_array_F_Fmean", "k": PC_K, "window_s": window_s, "n_files": len(ids),
           "n_open": len(open_ids), "n_locked_skipped": len(ids) - len(open_ids),
           "windowed": pct(win), "whole": pct(whole), "gcamp_range": pct(gr), "n_neurons": pct(nn.astype(float)),
           "dt_s_median": float(np.median([r["dt_s"] for r in rows])), "animals": rows}
    Path(out).write_text(json.dumps(res, indent=1))
    print(json.dumps({k: v for k, v in res.items() if k != "animals"}, indent=1))


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2], float(sys.argv[3]) if len(sys.argv) > 3 else 195.0)
