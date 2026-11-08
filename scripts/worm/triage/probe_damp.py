"""Probe, row 21 damping: mean internal-damping time constant during the 1.76 Hz wave (wtriage, 8 Nov 2026).

Pre-registered (8 Nov 13:40, before running):
  bar      the check's own (scripts/worm/body_layers_check.py item 3): mean tau during the 3 s wave on the agar film
           <= 5.3 ms (derived from Fang-Yen et al. 2010 PNAS 107:20323), and the run finite
  ids      the gaps the bar reads (traced: body/layers.world_flags, driver/run_body.cpp update_drag):
           body_damp_tau_ms, body_damp_w_ref_rad_s, body_damp_clip. body_damp_alpha (1.0, measured, Backholm 2013)
           is scan: fixed. Body layers at the default (frontiers2024), as in the check.
  design   64 Sobol points in the bio box, seed 0; one body run each (the driver, one thread)
  also     the body's slice-tangent rate w per point (the cause: the check's run has w 1.09 rad/s against the
           w_ref 10 rad/s the template was derived for)
Needs a driver built from the current run_body.cpp (backhouse: built 8 Nov 13:26 in the wtriage copy).
"""
from __future__ import annotations

import multiprocessing as mp
import sys
from pathlib import Path

import numpy as np

from probe_lib import Box, joint_bad, save

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "src"))
from wormemu.body import layers  # noqa: E402
from wormemu.body import metaworm as mw  # noqa: E402

OUT = ROOT / "runs" / "worm" / "triage" / "damp"
IDS = ["body_damp_tau_ms", "body_damp_w_ref_rad_s", "body_damp_clip"]
WAVE = dict(mode="wave", seconds=3.0, f=1.76, lam=1.54, amp=0.157, frame_every=8)


def one(a):
    k, x, ty = a
    w = {**mw.AGAR_FILM, "tet_youngs": ty, "damping": "backholm2013", "damp_tau_ms": float(x[0]),
         "damp_w_ref": float(x[1]), "damp_alpha": 1.0, "damp_clip": float(x[2])}
    try:
        r = mw.run(str(OUT / f"p{k:03d}"), world=w, **WAVE)
        m = r["meta"]["world"]
        return dict(tau=m["damp_tau_ms_mean"], w=m["damp_w_mean"], finite=bool(np.isfinite(r["X"]).all()))
    except Exception as e:
        return dict(tau=np.nan, w=np.nan, finite=False, error=str(e)[:200])


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    world, _ = layers.world_flags(None, str(OUT / "layers"), mw.AGAR_FILM)
    box = Box(IDS)
    X = box.design(64, which="bio", seed=0)
    with mp.get_context("fork").Pool(8, maxtasksperchild=1) as pool:
        rows = pool.map(one, [(k, x, world["tet_youngs"]) for k, x in enumerate(X)], chunksize=1)
    tau = np.array([r["tau"] for r in rows], float)
    jb = np.array([len(joint_bad(dict(zip(IDS, x)))) for x in X])
    ok = (tau <= 5.3) & np.array([r["finite"] for r in rows]) & (jb == 0)
    k = int(np.nanargmin(tau))
    nz = [i for i in np.where(ok)[0] if not box.at_edge(X[i])]
    res = dict(check="row 21 damping mean tau", bar="<= 5.3 ms", n=len(X), n_pass=int(ok.sum()),
               pass_fraction=float(ok.mean()), n_pass_no_edge=len(nz), joint_bad=int((jb > 0).sum()),
               best=dict(zip(IDS, X[k].tolist())), best_tau=float(tau[k]), best_w=rows[k]["w"],
               best_edges=box.at_edge(X[k]), w_range=[float(np.nanmin([r["w"] for r in rows])),
                                                     float(np.nanmax([r["w"] for r in rows]))],
               points=[dict(x=dict(zip(IDS, x.tolist())), passed=bool(o), edges=box.at_edge(x), **r)
                       for x, o, r in zip(X, ok, rows)], bounds=box.describe())
    print(save("probe_damp", res))
    print({k_: v for k_, v in res.items() if k_ not in ("points", "bounds")})


if __name__ == "__main__":
    main()
