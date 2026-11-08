"""Row 21 damping, causal chain (wtriage, 8 Nov 2026). Never adopted; writes runs/worm/triage/damp_chain.json.

The damping bar (mean tau <= 5.3 ms during the 1.76 Hz wave) fails at 16.7 ms because tau = tau_ref * (w_ref / w),
and the body's measured slice-tangent rate w is ~1.1 rad/s, not the ~9 rad/s w_ref was derived from. Question: is w
low because the layered body is too stiff (row 21's other failure, 7.8x)? Runs the same 3 s wave on the agar film:
  a  layers default + damping default (the check's run)
  b  layers 'published' (uniform 2e5 Pa, upstream) + damping default
and reports w, tau and the body's tangent-angle amplitude for each. Mac smoke, ~10 s wall per run.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "src"))
from wormemu.body import layers  # noqa: E402
from wormemu.body import metaworm as mw  # noqa: E402

OUT = ROOT / "runs" / "worm" / "triage"
OUT.mkdir(parents=True, exist_ok=True)
WAVE = dict(mode="wave", seconds=3.0, f=1.76, lam=1.54, amp=0.157, frame_every=8)
DAMP = {"damping": "backholm2013", "damp_tau_ms": 2.0, "damp_w_ref": 10.0, "damp_alpha": 1.0, "damp_clip": 10.0}


def tangent_amp(X):
    """Body-axis tangent angle amplitude (rad): X frames (T, nv, 3) -> centreline by z-slices is not available here,
    so use the per-frame principal-axis angle of vertex chunks along the body (20 chunks)."""
    X = np.asarray(X)
    T = X.shape[0]
    z = X[0, :, 2] if X.ndim == 3 else None
    order = np.argsort(X[0, :, 0] if np.ptp(X[0, :, 0]) > np.ptp(X[0, :, 1]) else X[0, :, 1])
    chunks = np.array_split(order, 20)
    ang = np.zeros((T, 19))
    for t in range(T):
        c = np.array([X[t, ch, :2].mean(0) for ch in chunks])
        d = np.diff(c, axis=0)
        ang[t] = np.unwrap(np.arctan2(d[:, 1], d[:, 0]))
    ang -= ang.mean(0)
    return float(np.sqrt(2) * ang[T // 3:].std())


def main():
    res = {}
    world, _ = layers.world_flags(None, str(OUT / "dc_layers"), mw.AGAR_FILM)
    for key, extra in (("a_layers_default", {**DAMP, "tet_youngs": world["tet_youngs"]}),
                       ("b_published_uniform", dict(DAMP))):
        r = mw.run(str(OUT / f"dc_{key}"), world={**mw.AGAR_FILM, **extra}, **WAVE)
        wm = r["meta"]["world"]
        res[key] = dict(w_mean=wm["damp_w_mean"], tau_ms_mean=wm["damp_tau_ms_mean"], theta_amp_rad=tangent_amp(r["X"]))
        print(key, res[key], flush=True)
    res["note"] = ("a 1.76 Hz wave with tangent amplitude theta has RMS tangent rate theta * 2 pi f / sqrt(2) = "
                   "7.8 theta rad/s (derived)")
    (OUT / "damp_chain.json").write_text(json.dumps(res, indent=1))


if __name__ == "__main__":
    main()
