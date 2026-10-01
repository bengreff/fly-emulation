"""Rung-1 repair 1 (session 11): fit the spike-triggered channels to recorded current steps.

Pre-registered in docs/DECISIONS.md 2026-09-30 21:17, plus the threshold deviation logged
at 21:20. Single unconnected rung-1 cells (src/flyemu/channels.py) stand for the slow
tibia-flexor MN class. Data: data/derived/azevedo2020_current_step_features.csv
(measured).

Model per recorded condition:
- tau_m is the cell's own; rest/reset are -52 mV and the threshold is -52 + theta.
- t_ref is 2.2 ms.
- Drive is the per-cell tonic d0 plus dI x Rin (mV, derived) during 0.5-1.0 s; each run lasts 1.0 s.
- The other channels sit at their priors with expression factor 1. Fitted values are
  class gbar at factor 1, labelled derived.

Parameters:
- shared: log10 gSK, gBK, gKv2, ca_per_spike, ca_tau, gh, and theta;
- per cell: d0.

Differential evolution over the whole population at once: each member x condition is one cell.
Hold-out cell 181127_F1_C1: shared values fixed, only d0 fitted to its spontaneous rate;
f-I RMS reported against the 30% criterion.

    uv run python scripts/fit_spike_channels.py [--gens 60] [--pop 12]
"""
import argparse
import json
import sys
import time

import numpy as np
import pandas as pd
from scipy.optimize import differential_evolution, minimize_scalar

sys.path.insert(0, "src")
from flyemu import channels, lif  # noqa: E402
from flyemu.connectome import Connectome  # noqa: E402

DT = 0.1
FIT = ["180111_F2_C1", "181021_F1_C1", "180621_F1_C1"]
HOLD = "181127_F1_C1"
FEAT = pd.read_csv("data/derived/azevedo2020_current_step_features.csv")
PRIOR = {c: p for c, (_, _, _, p) in channels.CHANNELS.items()}
# shared parameter bounds: parameters.csv (gbar 0-10x prior: log floor 1e-3x), Ca rows, theta 5-35 mV
SHARED = [("SK", -3, np.log10(5.0)), ("BK", -3, np.log10(10.0)), ("Kv2", -3, np.log10(5.0)),
          ("ca_per_spike", -1, 1), ("ca_tau", np.log10(20), np.log10(500)), ("h", -3, np.log10(2.0))]
THETA = (5.0, 35.0)
D0 = (0.0, 60.0)


def conn(n):
    nrn = pd.DataFrame({"bodyId": np.arange(n), "type": "x", "predictedNt": "acetylcholine",
                        "superclass": "x", "class": "x"})
    return Connectome(nrn, np.zeros(n + 1, np.int64), np.zeros(0, np.int32), np.zeros(0, np.float32),
                      np.zeros(n, np.float32), np.zeros(0, np.float32))


def simulate(rows: pd.DataFrame, sh: np.ndarray, theta: np.ndarray, d0: np.ndarray, channels_on=True):
    """rows: conditions (n); sh: (n, 6) shared params (linear units); theta, d0: (n,).
    Returns dict of per-condition features."""
    n = len(rows)
    f = lambda v: np.asarray(np.broadcast_to(v, (n,)), np.float32).copy()
    ich = None
    if channels_on:
        g = {c: f(PRIOR[c]) for c in channels.CHANNELS}
        g["SK"], g["BK"], g["Kv2"], g["h"] = f(sh[:, 0]), f(sh[:, 1]), f(sh[:, 2]), f(sh[:, 5])
        ich = channels.Intrinsic(g=g, ca_per_spike=f(sh[:, 3]), dt=DT, ca_tau=f(sh[:, 4]))
    p = lif.LIFParams(f(rows.tau_m_ms.to_numpy()), f(-52.0), f(-52.0 + theta), f(-52.0), f(2.2), 5.0,
                      np.ones(n, np.int64), 0.0, True, graded=np.zeros(n, bool), intrinsic=ich)
    net = lif.Network(conn(n), p, DT)
    step_mv = f((rows.dI_pA * rows.rin_MOhm / 1000.0).to_numpy())
    d0 = f(d0)
    cnt = {k: np.zeros(n) for k in ("spont", "on", "early", "late")}
    vpre, vmin, vss = np.zeros(n), np.full(n, np.inf), np.zeros(n)
    k_pre = k_ss = 0
    win = 50   # 5 ms running mean for the sag peak, as the data (50 samples at 50 kHz = 1 ms; here 5 steps)
    buf = []
    for s in range(int(1000 / DT)):
        t = s * DT
        ext = d0 + (step_mv if 500 <= t < 1000 else 0.0)
        sp = net.step(external_mv=ext)
        if sp.size:
            if 0 <= t < 500: cnt["spont"][sp] += 1
            if 550 <= t < 1000: cnt["on"][sp] += 1
            if 500 <= t < 600: cnt["early"][sp] += 1
            if 900 <= t < 1000: cnt["late"][sp] += 1
        v = net.v.astype(np.float64)
        if 200 <= t < 500: vpre += v; k_pre += 1
        if 500 <= t < 700:
            buf.append(v.copy())
            if len(buf) > 10: buf.pop(0)
            if len(buf) == 10: vmin = np.minimum(vmin, np.mean(buf, axis=0))
        if 900 <= t < 1000: vss += v; k_ss += 1
    vpre /= k_pre; vss /= k_ss
    steady = vss - vpre
    sag = np.where(steady < -1, (vmin - vpre - steady) / steady, np.nan)
    early, late = cnt["early"] / 0.1, cnt["late"] / 0.1
    return {"spont_hz": cnt["spont"] / 0.5, "on_hz": cnt["on"] / 0.45, "early_hz": early, "late_hz": late,
            "adapt": np.where(early > 0, late / np.maximum(early, 1e-9), np.nan), "sag": sag}


def loss_terms(rows, m):
    """Per-condition loss contributions, aggregated per cell then averaged over cells."""
    rec_adapt = rows.adapt_late_over_early.to_numpy()
    pos = rows.step_pA.to_numpy() > 0
    neg_big = rows.groupby("cell").step_pA.transform("min").to_numpy() == rows.step_pA.to_numpy()
    e = ((m["on_hz"] - rows.on_hz.to_numpy()) / 10) ** 2 + ((m["spont_hz"] - rows.spont_hz.to_numpy()) / 10) ** 2
    ad = np.nan_to_num(m["adapt"], nan=0.0)
    e = e + np.where(pos & np.isfinite(rec_adapt), ((ad - rec_adapt) / 0.1) ** 2, 0)
    sg = np.nan_to_num(m["sag"], nan=0.0)
    e = e + np.where(neg_big & np.isfinite(rows.sag_frac.to_numpy()), ((sg - rows.sag_frac.to_numpy()) / 0.05) ** 2, 0)
    return pd.Series(e).groupby(rows.cell.to_numpy()).mean()


def unpack(x, cells):
    sh = 10.0 ** np.asarray(x[:6])
    theta = x[6]
    d0 = dict(zip(cells, x[7:7 + len(cells)]))
    return sh, theta, d0


def vec_objective(X, rows, cells, channels_on=True):
    """X: (dim, S). Simulate all members x conditions at once."""
    S = X.shape[1]
    nr = len(rows)
    big = pd.concat([rows] * S, ignore_index=True)
    sh = np.repeat(10.0 ** X[:6].T, nr, axis=0)
    theta = np.repeat(X[6], nr)
    cidx = rows.cell.map({c: i for i, c in enumerate(cells)}).to_numpy()
    d0 = np.concatenate([X[7 + cidx, s] for s in range(S)])
    m = simulate(big, sh, theta, d0, channels_on)
    out = np.zeros(S)
    for s in range(S):
        sl = slice(s * nr, (s + 1) * nr)
        out[s] = loss_terms(rows, {k: v[sl] for k, v in m.items()}).mean()
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--gens", type=int, default=60)
    ap.add_argument("--pop", type=int, default=12)
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--out", default="runs/s11/rung1/spike_channel_fit.json")
    a = ap.parse_args()
    rows = FEAT[FEAT.cell.isin(FIT)].reset_index(drop=True)
    cells = FIT
    results = {}
    t0 = time.time()
    # (A) rung-1 fit: shared channels + theta + d0 per cell
    bounds = [(lo, hi) for _, lo, hi in SHARED] + [THETA] + [D0] * len(cells)
    r = differential_evolution(lambda X: vec_objective(np.atleast_2d(X.T).T if X.ndim == 1 else X, rows, cells),
                               bounds, vectorized=True, popsize=a.pop, maxiter=a.gens, seed=a.seed, tol=1e-4,
                               polish=False, updating="deferred")
    sh, theta, d0 = unpack(r.x, cells)
    results["fit"] = {"loss": float(r.fun), "nit": int(r.nit),
                      "shared": {k: float(v) for (k, _, _), v in zip(SHARED, sh)}, "theta_mV": float(theta),
                      "d0_mV": {c: float(v) for c, v in d0.items()}}
    # (B) baselines: channel priors with theta/d0 fitted; LIF only with theta/d0 fitted
    pri = np.log10([PRIOR["SK"], PRIOR["BK"], PRIOR["Kv2"], channels.KINETICS["Ca"][0], channels.KINETICS["Ca"][1], PRIOR["h"]])
    for name, on in (("priors", True), ("lif_only", False)):
        def obj(X, on=on):
            Y = np.vstack([np.repeat(pri[:, None], X.shape[1], axis=1), X])
            return vec_objective(Y, rows, cells, channels_on=on)
        rb = differential_evolution(obj, [THETA] + [D0] * len(cells), vectorized=True, popsize=a.pop,
                                    maxiter=a.gens, seed=a.seed, tol=1e-4, polish=False, updating="deferred")
        results[name] = {"loss": float(rb.fun), "theta_mV": float(rb.x[0]),
                         "d0_mV": dict(zip(cells, map(float, rb.x[1:])))}
    # per-condition table for the fit
    X = np.asarray(r.x)[:, None]
    big = rows.copy()
    cidx = rows.cell.map({c: i for i, c in enumerate(cells)}).to_numpy()
    m = simulate(rows, np.repeat(sh[None], len(rows), 0), np.full(len(rows), theta), X[7 + cidx, 0])
    for k in ("spont_hz", "on_hz", "adapt", "sag"):
        big["model_" + k] = m[k]
    big["model_sag"] = np.where(big.step_pA < 0, big.model_sag, np.nan)
    # (C) held-out cell: shared fixed, d0 fitted to its spontaneous rate only (fit and both baselines)
    hr = FEAT[FEAT.cell == HOLD].reset_index(drop=True)

    def holdout(shv, th, on):
        spont = hr.spont_hz.mean()
        def sp_err(d):
            mm = simulate(hr.iloc[:1], shv[None], np.array([th]), np.array([d]), on)
            return (mm["spont_hz"][0] - spont) ** 2
        d_h = minimize_scalar(sp_err, bounds=D0, method="bounded", options={"xatol": 0.05}).x
        mh = simulate(hr, np.repeat(shv[None], len(hr), 0), np.full(len(hr), th), np.full(len(hr), d_h), on)
        pos = hr.step_pA > 0
        rel = float(np.sqrt(np.mean(((mh["on_hz"][pos] - hr.on_hz[pos]) / hr.on_hz[pos]) ** 2)))
        tab = hr[["step_pA", "on_hz", "adapt_late_over_early", "sag_frac"]].copy()
        tab["model_on_hz"] = mh["on_hz"]; tab["model_adapt"] = mh["adapt"]
        tab["model_sag"] = np.where(hr.step_pA < 0, mh["sag"], np.nan)
        return {"cell": HOLD, "d0_mV": float(d_h), "on_rate_rel_rms_positive_steps": rel,
                "criterion_rel_rms": 0.30, "pass": rel <= 0.30, "table": tab.round(3).to_dict("records")}

    results["holdout"] = holdout(sh, theta, True)
    for name, on in (("priors", True), ("lif_only", False)):
        h = holdout(10.0 ** pri, results[name]["theta_mV"], on)
        results[name]["holdout_rel_rms"] = h["on_rate_rel_rms_positive_steps"]
    results["fit_table"] = big[["cell", "step_pA", "spont_hz", "model_spont_hz", "on_hz", "model_on_hz",
                                "adapt_late_over_early", "model_adapt", "sag_frac", "model_sag"]].round(3).to_dict("records")
    results["wall_s"] = round(time.time() - t0, 1)
    json.dump(results, open(a.out, "w"), indent=1)
    pd.set_option("display.width", 220)
    print(json.dumps({k: v for k, v in results.items() if k not in ("fit_table", "holdout")}, indent=1))
    print(pd.DataFrame(results["fit_table"]).round(2).to_string(index=False))
    print("holdout", {k: v for k, v in results["holdout"].items() if k != "table"})
    print(pd.DataFrame(results["holdout"]["table"]).round(2).to_string(index=False))


if __name__ == "__main__":
    main()
