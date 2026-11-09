"""Synthetic-twin coverage of the excretory canal (weki, 8 Nov 2026; brief item 4; FIT_GENERAL.md section 5).

Pre-registered (8 Nov 21:25 CST, date; written before the first run of this script): 20 hidden values drawn inside the box
(rng 20261108 + k, unit positions uniform on [0.1, 0.9]), the protocol and noise of tests/test_worm_fit_eki.py, 100
members, the log-uniform prior, the data-misfit controller to t = 1, at most 40 iterations; for each inflation in
(1.0, 1.02, 1.05, 1.1):
  recovered  a draw whose 4 values are all within a factor 1.25 of the ensemble median;
  coverage   the fraction of the 80 (draw, value) pairs inside the ensemble's 2.5-97.5 % range.
Bar: recovered in at least 18 of 20 at inflation 1.0, else the canal's 4 numbers are reported as not identifiable from
this protocol. The fit's inflation is the smallest value whose coverage is at least 0.90 (0.95 nominal; finite ensembles
run overconfident), else the largest tried, flagged. Nothing here reads real data.

Result of that run (21:25, measured): recovered 11 / 20, coverage 0.975; dosm, e_vol and lp within 1.25 in 20 / 20
(median 95 % width a factor 1.03-1.04), canal_gain in 11 / 20 (width a factor 38). Not identifiable from protocol A: the
canal stops when the worm shrinks (organs_other.Osmo.step, the canal cannot pump water in), so a hypertonic step sees
the gain only near the switch point.

Protocol B, pre-registered 8 Nov 21:26 CST (date), before its first run: the same as A plus a hypotonic step (canal
form, medium 100 mOsm below the template for 2 h, then back, every 15 min), where the canal works hardest; the
equations give a swollen steady state 1 + RT 100 / ((1 + gain) E_vol) (derived), so the gain should be seen. Same bar.

Protocol B with correlation localisation, pre-registered 8 Nov 22:28 CST (date), before its first run (FIT_GENERAL
section 5: rho_corr does all the localising in the closed-loop worm, so the twin must pass with it on): protocol B,
`localise="corr"` (eki.corr_rho at its default k = 3, J = 100, cut |corr| > 0.30, derived), everything else as B. Same
bar (18 of 20 recovered at inflation 1.0; the inflation rule as above). Falsifier: fewer than 18 of 20, or coverage at
1.0 below 0.90 where B without it reached 0.925, means the cut drops pairs the data need and the fit cannot use it as is.

Usage: python scripts/worm/fit/twin_coverage.py OUT.json [A|B] [corr]
"""
from __future__ import annotations

import json
import sys
import time
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "tests"))
sys.path.insert(0, str(ROOT / "src"))
import test_worm_fit_eki as T  # noqa: E402
from wormemu.fit import eki as E  # noqa: E402
from wormemu.mech import organs_other as oo  # noqa: E402

SPEC = {s.id: s for s in oo.SPECS}
LO, HI = np.log([SPEC[k].lo for k in T.TWIN]), np.log([SPEC[k].hi for k in T.TWIN])
INFL = (1.0, 1.02, 1.05, 1.1)


def to_x(z):
    return np.exp(LO + (HI - LO) / (1 + np.exp(-z)))


def forward(x, protocol):
    g = T.osmo_forward(x)
    return g if protocol == "A" else np.hstack([g, T.osmo_forward(x, extra=-100.0, null=False)])


def one(k, infl, protocol, localise="fixed"):
    rng = np.random.default_rng(20261108 + k)
    u = rng.uniform(0.1, 0.9, 4)
    x_true = to_x(np.log(u / (1 - u)))
    y0 = forward(x_true, protocol)[0]
    y = y0 + rng.normal(0, T.NOISE_V, len(y0))
    u0 = rng.uniform(size=(100, 4))
    e = T.run(E.EKI(np.log(u0 / (1 - u0)), y, np.full(len(y), T.NOISE_V ** 2), seed=11 + k, inflation=infl,
                      localise=localise),
              lambda z: (forward(to_x(z), protocol), None), max_iter=40)
    xs = to_x(e.z)
    med = np.median(xs, 0)
    lo, hi = np.percentile(xs, [2.5, 97.5], axis=0)
    return dict(x_true=x_true.tolist(), median=med.tolist(), ratio=(med / x_true).tolist(),
                inside=((lo <= x_true) & (x_true <= hi)).tolist(), width=(hi / lo).tolist(),
                recovered=bool(np.all(np.abs(np.log(med / x_true)) < np.log(1.25))), done=e.done,
                iterations=len(e.dts), t_end=float(e.t))


def main():
    protocol = sys.argv[2] if len(sys.argv) > 2 else "A"
    localise = "corr" if sys.argv[3:4] == ["corr"] else "fixed"
    out = {"protocol": protocol, "localise": localise}
    for infl in INFL:
        t0 = time.time()
        rs = [one(k, infl, protocol, localise) for k in range(20)]
        out[str(infl)] = dict(runs=rs, recovered=sum(r["recovered"] for r in rs),
                              coverage=float(np.mean([v for r in rs for v in r["inside"]])),
                              coverage_by_value=dict(zip(T.TWIN, np.mean([r["inside"] for r in rs], 0).tolist())),
                              median_width=dict(zip(T.TWIN, np.median([r["width"] for r in rs], 0).tolist())),
                              all_done=all(r["done"] for r in rs), wall_s=time.time() - t0)
        o = out[str(infl)]
        print(infl, "recovered", o["recovered"], "/ 20; coverage", round(o["coverage"], 3), o["coverage_by_value"],
              "done", o["all_done"], flush=True)
    ok = [i for i in INFL if out[str(i)]["coverage"] >= 0.90]
    out["verdict"] = dict(identifiable=out["1.0"]["recovered"] >= 18, inflation=min(ok) if ok else max(INFL),
                          inflation_flagged=not ok)
    Path(sys.argv[1]).write_text(json.dumps(out, indent=1))
    print(json.dumps(out["verdict"]))


if __name__ == "__main__":
    main()
