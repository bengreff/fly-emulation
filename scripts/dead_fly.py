"""Run the dead-fly test and write runs/<label>/deadfly.json (+ traces.npz).

    uv run python scripts/dead_fly.py --label s9_deadfly_baseline [--ms 1000]
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

import numpy as np

from flyemu import deadfly

REPO = Path(__file__).resolve().parents[1]

if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--label", default="deadfly")
    ap.add_argument("--ms", type=float, default=1000.0)
    ap.add_argument("--template", action="store_true",
                    help="the construction-template body (model_data.TEMPLATE_SWITCHES body keys)")
    ap.add_argument("--set", action="append", default=[], metavar="KEY=V")
    a = ap.parse_args()
    body = None
    if a.template or a.set:
        from flyemu import model_data, passive
        from flyemu.body import Body
        from flyemu.registry import Registry
        reg = Registry("minimal")
        if a.template:
            reg.overrides.update(model_data.TEMPLATE_SWITCHES)
        reg.overrides.update({k: float(v) for k, v in (x.split("=") for x in a.set)})
        body = Body(vision=False)
        passive.register(reg, body)
        passive.register_coxa(reg, body)
        passive.register_ctr(reg, body)
        passive.register_rest(reg, body)
        passive.register_wings(reg, body)
        passive.register_noslip(reg, body)
        if int(reg.require("joint:wing", "range_by_function", units="enum", model_use="",
                           minimal=0)):
            from flyemu import flight
            flight.apply_wing_ranges(body)
    tr = deadfly.run(duration_ms=a.ms, body=body)
    s = deadfly.score(tr)
    out = REPO / "runs" / a.label
    out.mkdir(parents=True, exist_ok=True)
    (out / "deadfly.json").write_text(json.dumps(s, indent=1, default=str))
    np.savez_compressed(out / "traces.npz", t_ms=tr.t_ms, thorax_z=tr.thorax_z,
                        qpos=tr.qpos_hinge, qvel=tr.qvel_hinge, energy=tr.energy,
                        trunk_contact=tr.body_ground_contact, names=np.array(tr.hinge_names),
                        rng=tr.hinge_range)
    for k, v in s.items():
        print(f"{k:18s} {v['verdict']:8s} " + json.dumps({x: y for x, y in v.items()
                                                          if x not in ('verdict', 'criterion')}, default=str)[:400])
