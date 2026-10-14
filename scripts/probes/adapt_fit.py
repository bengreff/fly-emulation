"""Fit a class's spike-frequency adaptation increment to a recorded adaptation ratio (s13 frontier stage 1).

One unconnected model cell per (adaptation increment, step drive) pair, with a cell type's own model constants
(tau_m, rest, threshold, reset, refractory period, rung-1 channels) taken from the profile build, or the generic
central cell (tau_m 20 ms, rest -52 mV, gap 7 mV, t_ref 2.2 ms). For each increment the step drive that gives the
recorded early rate is found by interpolation, and the late/early rate ratio at that drive is read off; the fitted
increment is the one whose ratio matches the recorded ratio (linear interpolation on the grid). No noise, no
synapses. Every fitted value is `inferred` (one class value from a recorded ratio; the model cell is a point neuron).

    uv run python scripts/probes/adapt_fit.py --profile m10f0 --cell-type MBON14 --early-hz 40 --ratio 0.5 \
        --early-ms 0,100 --late-ms 300,400 --step-ms 400
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve()
sys.path.insert(0, str(HERE.parents[2] / "src")); sys.path.insert(0, str(HERE.parent))
from flyemu import channels, lif, profiles  # noqa: E402
from flyemu.connectome import Connectome  # noqa: E402
from flyemu.registry import Policy, Registry  # noqa: E402
from central_fi import cell_constants  # noqa: E402

DT = 0.1


def sweep(profile: str, const: dict, body_id: int, cell_type: str, adapts: np.ndarray, drives: np.ndarray,
          tau_adapt: float, step_ms: float, early: tuple, late: tuple) -> tuple[np.ndarray, np.ndarray]:
    """(len(adapts), len(drives)) early and late rates in Hz."""
    reg = Registry(Policy.MINIMAL)
    profiles.apply(reg, profile)
    A, D = np.meshgrid(adapts, drives, indexing="ij")
    n = A.size
    nrn = pd.DataFrame({"bodyId": np.full(n, body_id), "type": cell_type, "predictedNt": "acetylcholine",
                        "superclass": "x", "class": "x"})
    conn = Connectome(nrn, np.zeros(n + 1, np.int64), np.zeros(0, np.int32), np.zeros(0, np.float32),
                      np.zeros(n, np.float32), np.zeros(0, np.float32))
    ich = channels.from_registry(reg, conn, timestep_ms=DT)
    f = lambda v: np.full(n, v, np.float32)
    p = lif.LIFParams(f(const["tau_m"]), f(const["v_rest"]), f(const["v_th"]), f(const["v_reset"]),
                      f(const["t_ref"]), 5.0, np.ones(n, np.int64), 0.0, True, graded=np.zeros(n, bool),
                      intrinsic=ich, spont_mv=f(const.get("spont", 0.0)),
                      adapt_mv=A.ravel().astype(np.float32), tau_adapt=f(tau_adapt))
    net = lif.Network(conn, p, DT)
    drive = D.ravel().astype(np.float32)
    t0 = 500.0
    # rate in a window = mean instantaneous rate (1/ISI) of the intervals ending in it, so short windows are
    # not quantised by whole spike counts; a window with no interval ending in it reads 0
    last = np.full(n, np.nan)
    es, ec, ls, lc = (np.zeros(n) for _ in range(4))
    for s in range(int((t0 + step_ms) / DT)):
        t = s * DT
        sp = net.step(external_mv=drive if t >= t0 else np.zeros(n, np.float32))
        if sp.size and t >= t0:
            r = t - t0
            isi = t - last[sp]
            ok = np.isfinite(isi)
            if early[0] <= r < early[1]:
                es[sp[ok]] += 1000.0 / isi[ok]; ec[sp[ok]] += 1
            if late[0] <= r < late[1]:
                ls[sp[ok]] += 1000.0 / isi[ok]; lc[sp[ok]] += 1
            last[sp] = t
    eh = np.where(ec > 0, es / np.maximum(ec, 1), 0.0).reshape(A.shape)
    lh = np.where(lc > 0, ls / np.maximum(lc, 1), 0.0).reshape(A.shape)
    return eh, lh


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--profile", default="m10f0")
    ap.add_argument("--cell-type", default="", help="take this type's model constants (first cell); else generic")
    ap.add_argument("--early-hz", type=float, required=True, help="recorded rate in the early window")
    ap.add_argument("--ratio", type=float, required=True, help="recorded late/early rate ratio")
    ap.add_argument("--early-ms", default="0,100")
    ap.add_argument("--late-ms", default="900,1000")
    ap.add_argument("--step-ms", type=float, default=1000.0)
    ap.add_argument("--tau-adapt", type=float, default=200.0)
    ap.add_argument("--adapts", default="0,0.05,0.1,0.2,0.3,0.5,0.75,1,1.5,2,3,4,6")
    ap.add_argument("--drives", default="")
    ap.add_argument("--out", default="")
    a = ap.parse_args()
    early = tuple(float(x) for x in a.early_ms.split(","))
    late = tuple(float(x) for x in a.late_ms.split(","))
    if a.cell_type:
        c, cells = cell_constants(a.profile, a.cell_type)
        const = {k: float(np.median(c[k])) for k in ("tau_m", "v_rest", "v_th", "v_reset", "t_ref", "spont")}
        body_id, ctype = int(cells.bodyId[0]), a.cell_type
    else:
        const = {"tau_m": 20.0, "v_rest": -52.0, "v_th": -45.0, "v_reset": -52.0, "t_ref": 2.2, "spont": 0.0}
        body_id, ctype = -1, "__central_probe__"
    adapts = np.array([float(x) for x in a.adapts.split(",")])
    drives = (np.array([float(x) for x in a.drives.split(",")]) if a.drives
              else np.concatenate([np.arange(6.0, 12.0, 0.25), np.arange(12.0, 40.0, 1.0), np.arange(40, 101, 5.0)]))
    eh, lh = sweep(a.profile, const, body_id, ctype, adapts, drives, a.tau_adapt, a.step_ms, early, late)
    ratios = []
    for i in range(len(adapts)):
        e = eh[i]
        if e.max() < a.early_hz or e.min() > a.early_hz:
            ratios.append(np.nan); continue
        j = int(np.argmax(e >= a.early_hz))                 # first drive reaching the early rate
        if j == 0:
            ratios.append(lh[i, 0] / max(e[0], 1e-9)); continue
        w = (a.early_hz - e[j - 1]) / max(e[j] - e[j - 1], 1e-9)
        lat = lh[i, j - 1] + w * (lh[i, j] - lh[i, j - 1])
        ratios.append(lat / a.early_hz)
    ratios = np.array(ratios)
    ok = np.isfinite(ratios)
    fit = None
    if ok.any():
        x, y = adapts[ok], ratios[ok]
        if a.ratio >= y.max():
            fit = float(x[np.argmax(y)])
        elif a.ratio <= y.min():
            fit = float(x[np.argmin(y)])
        else:
            k = int(np.argmax(y <= a.ratio))                 # ratios fall as the increment grows
            fit = float(x[k - 1] + (a.ratio - y[k - 1]) * (x[k] - x[k - 1]) / (y[k] - y[k - 1])) if k else float(x[0])
    res = {"profile": a.profile, "cell_type": a.cell_type or "generic", "constants": const,
           "target": {"early_hz": a.early_hz, "ratio": a.ratio, "early_ms": early, "late_ms": late,
                      "step_ms": a.step_ms, "tau_adapt": a.tau_adapt},
           "adapts_mv": adapts.tolist(), "ratio_at_target_early": [None if not np.isfinite(r) else round(float(r), 3)
                                                                   for r in ratios],
           "fit_adaptation_mv": None if fit is None else round(fit, 3)}
    print(json.dumps(res))
    if a.out:
        Path(a.out).parent.mkdir(parents=True, exist_ok=True)
        Path(a.out).write_text(json.dumps(res, indent=1))


if __name__ == "__main__":
    main()
