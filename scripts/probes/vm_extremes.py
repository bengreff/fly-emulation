"""Which cells leave the physiological voltage range under a profile and --set overrides (diagnostic, s12).

Open loop, eye at a static mean-luminance drive (as motion_grating.py's static segment), then reports the
types with the most cells outside [--lo, --hi] mV and their extreme values.

    uv run python scripts/probes/vm_extremes.py --profile m9c --set cell_type:ol_graded|release_at_rest=0.5
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))
from flyemu import connectome, electrical, lif, profiles, vision  # noqa: E402
from flyemu.registry import Policy, Registry  # noqa: E402

DT = 0.1


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--profile", default=profiles.WORKING_PROFILE)
    ap.add_argument("--set", action="append", default=[])
    ap.add_argument("--ms", type=float, default=300.0)
    ap.add_argument("--lo", type=float, default=-100.0)
    ap.add_argument("--hi", type=float, default=20.0)
    ap.add_argument("--out", default="")
    a = ap.parse_args()
    reg = Registry(Policy.MINIMAL)
    for s in a.set:
        k, v = s.split("=")
        reg.overrides[k] = float(v)
    profiles.apply(reg, a.profile)
    conn = connectome.build(reg, min_synapses=profiles.WORKING_MIN_SYNAPSES)
    params = lif.default_params(reg, conn, timestep_ms=DT)
    el = electrical.build(reg, conn)
    vis = vision.build(reg, conn, timestep_ms=DT, sample_hz=100.0)
    net = lif.Network(conn, params, DT, rng=np.random.default_rng(1))
    net.elec = el if len(el[0]) else None
    drive = np.zeros(conn.n, np.float32)
    drive[vis.rows] = vis.baseline_mv + vis.gain_mv * 0.5
    t = conn.neurons.type.fillna("untyped").to_numpy()
    graded = np.asarray(params.graded, bool)
    vmin = np.full(conn.n, np.inf)
    vmax = np.full(conn.n, -np.inf)
    first_out = {}
    for s in range(int(a.ms / DT)):
        net.step(external_mv=drive)
        vmin = np.minimum(vmin, net.v)
        vmax = np.maximum(vmax, net.v)
        if s % 100 == 0:
            bad = np.flatnonzero((net.v < a.lo) | (net.v > a.hi))
            for ty in set(t[bad]) - set(first_out):
                first_out[ty] = round(s * DT, 1)
    bad = (vmin < a.lo) | (vmax > a.hi)
    df = pd.DataFrame({"type": t, "vmin": vmin, "vmax": vmax, "vend": net.v, "graded": graded, "bad": bad})
    g = (df[df.bad].groupby("type")
         .agg(n_bad=("bad", "size"), graded=("graded", "mean"), vmin=("vmin", "min"), vmax=("vmax", "max"),
              vend_med=("vend", "median"))
         .sort_values("n_bad", ascending=False))
    g["n_type"] = df.groupby("type").size().reindex(g.index)
    g["first_ms"] = [first_out.get(x) for x in g.index]
    print(f"cells outside [{a.lo}, {a.hi}] mV: {int(bad.sum())} of {conn.n}; types {len(g)}")
    print(g.head(40).round(1).to_string())
    if a.out:
        Path(a.out).write_text(json.dumps({"set": a.set, "n_bad": int(bad.sum()),
                                           "types": g.head(200).round(2).reset_index().to_dict("records")}))


if __name__ == "__main__":
    main()
