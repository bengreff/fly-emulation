"""FIT2's puzzle (weki, 8 Nov 2026; brief item 5): why the true expression map trains worse than its 4 shuffles
(13.72 vs 8.42-10.78 mV). Read-only on FIT2: its code (scripts/worm/fit2.py, src/wormemu/excite_map.py) and its stored
best points (~/worm-night/wexcite/fit2/<model>/best.json) are used unchanged. Not a fit: single evaluations at fixed
points, no optimisation, nothing adopted. Training sweeps only (FIT2's train_features.npz); RIM is never opened.

Pre-registered (8 Nov 21:38 CST, date; before the first run):
  reproduce  each of the 5 stored best points re-evaluated with fit2.evaluate; |recomputed - stored| < 0.05 mV, else the
             brain changed since FIT2 (7 Nov) and that is reported first.
  H_leak     the true map's slope b is pinned at 0 by the leak term: the recorded classes have the lowest TWK sums
             (AIY 3.0 TPM, lowest of 128 classes; AFD 83.4, 13th; AWA 192.1, 27th; median 713.9), so any b > 0 cuts
             their leak. At the true best point, b raised to 0.25, 0.5, 1.0 in three forms: as registered (b on channels
             and leak), channels only (leak exponent 0), leak only (channel exponent 0). Supported if b = 0.5 raises the
             registered loss by at least 2 mV and the channels-only loss by less than half of that rise.
  H_level    the shuffles' advantage is their use of b > 0 (their fits chose b 1.50, 1.03, 1.41, 0.00): each shuffle's
             best point with b set to 0. Supported if, in at least 2 of the 3 shuffles with b > 0, the loss at b = 0 is
             at or above the true map's 13.72 mV.
  Each loss is FIT2's (mean absolute feature error over the training classes, mV), per class reported. Thresholds
  (2 mV, half, 2 of 3) guessed.

Usage (backhouse): python scripts/worm/fit/fit2_puzzle.py OUT_DIR [FIT2_DIR]   (one process per model, in turn: a
NEURON process builds one brain; then OUT_DIR/puzzle.json with the verdict)
"""
from __future__ import annotations

import json
import subprocess
import sys
import time
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[3]
OUT = Path(sys.argv[1])
FIT2_DIR = Path(sys.argv[2] if len(sys.argv) > 2 else Path.home() / "worm-night" / "wexcite" / "fit2")
ONE = sys.argv[3] if len(sys.argv) > 3 else None          # internal: the model this process evaluates
sys.path.insert(0, str(ROOT / "scripts" / "worm"))
sys.path.insert(0, str(ROOT / "src"))
import fit2 as F  # noqa: E402
from wormemu import excite_map as X  # noqa: E402

CLASSES = ["AIY", "AFD", "AWA"]
FORM = {"form": "registered"}
_CELL = X.Map.cell


def cell(self, name, P):
    """the registered map, or the slope applied to channels only / the leak only (diagnostic forms)"""
    if FORM["form"] == "registered":
        return _CELL(self, name, P)
    flat = {**P, "b": 0.0}
    ch, lk = (P, flat) if FORM["form"] == "channels_only" else (flat, P)
    out = _CELL(self, name, ch)
    leak = _CELL(self, name, lk)
    for part in ("soma", "neurite"):
        out[f"gpas_{part}"] = leak[f"gpas_{part}"]
    return out


X.Map.cell = cell


def ev(P, feats):
    m = F._W["map"]
    loss, per = F.evaluate((m.to_unit(P), feats))
    return dict(loss=loss, per=dict(zip(CLASSES, per)))


def one(model):
    d = np.load(FIT2_DIR / "train_features.npz")
    feats = {c: d[c] for c in CLASSES}
    t0 = time.time()
    best = json.loads((FIT2_DIR / model / "best.json").read_text())
    P = best["params"]
    F._init(model, CLASSES)
    r = {"stored": best["train_loss_mV"], "b": P["b"]}
    FORM["form"] = "registered"
    r["reproduced"] = ev(P, feats)
    if model == "true":
        for form in ("registered", "channels_only", "leak_only"):
            FORM["form"] = form
            r[form] = {str(b): ev({**P, "b": b}, feats) for b in (0.25, 0.5, 1.0)}
    elif P["b"] > 0:
        FORM["form"] = "registered"
        r["b0"] = ev({**P, "b": 0.0}, feats)
        FORM["form"] = "channels_only"
        r["channels_only"] = ev(P, feats)
    FORM["form"] = "registered"
    r["wall_s"] = time.time() - t0
    (OUT / f"{model}.json").write_text(json.dumps(r, indent=1, default=float))
    print(model, json.dumps(r, default=float), flush=True)


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    res = {"fit2_dir": str(FIT2_DIR), "started": time.ctime()}
    for model in F.MODELS:
        subprocess.run([sys.executable, __file__, str(OUT), str(FIT2_DIR), model], check=True)
        res[model] = json.loads((OUT / f"{model}.json").read_text())
    t = res["true"]
    rise = t["registered"]["0.5"]["loss"] - t["reproduced"]["loss"]
    rise_ch = t["channels_only"]["0.5"]["loss"] - t["reproduced"]["loss"]
    shuf = [m for m in F.MODELS[1:] if "b0" in res[m]]
    res["verdict"] = dict(
        reproduced=all(abs(res[m]["reproduced"]["loss"] - res[m]["stored"]) < 0.05 for m in F.MODELS),
        H_leak=dict(rise_registered=rise, rise_channels_only=rise_ch, supported=bool(rise >= 2.0 and rise_ch < rise / 2)),
        H_level=dict(b0={m: res[m]["b0"]["loss"] for m in shuf},
                     supported=bool(sum(res[m]["b0"]["loss"] >= t["stored"] for m in shuf) >= 2)))
    (OUT / "puzzle.json").write_text(json.dumps(res, indent=1, default=float))
    print("verdict", json.dumps(res["verdict"], default=float), flush=True)


if __name__ == "__main__":
    one(ONE) if ONE else main()
