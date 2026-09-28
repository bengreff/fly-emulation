"""B23 numerical convergence (s10): the same passive fall (dead fly, m4 body) and
the same tethered wingbeat at successively halved timesteps. Reports the largest
difference against the finest run.

    uv run python scripts/probes/convergence.py [--ms 300]
"""
import argparse
import json
import sys

import numpy as np

sys.path.insert(0, "src")
sys.path.insert(0, "scripts/probes")
from flyemu import deadfly  # noqa: E402
from flyemu.body import Body  # noqa: E402

if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--ms", type=float, default=300.0)
    a = ap.parse_args()
    out = {"deadfly": {}, "flight": {}}
    tr = {}
    for dt in (0.1, 0.05, 0.025):
        t = deadfly.run(duration_ms=a.ms, sample_ms=1.0, body=Body(vision=False, timestep=dt / 1000))
        tr[dt] = t
        out["deadfly"][dt] = dict(warnings=t.info["mujoco_warnings"], z_end=float(t.thorax_z[-1]))
    ref = tr[0.025]
    for dt in (0.1, 0.05):
        n = min(len(ref.thorax_z), len(tr[dt].thorax_z))
        out["deadfly"][dt]["max_dz_mm_vs_0.025"] = float(np.abs(tr[dt].thorax_z[:n] - ref.thorax_z[:n]).max())
        out["deadfly"][dt]["max_dq_deg_end_vs_0.025"] = float(np.degrees(np.abs(tr[dt].qpos_hinge[-1] - ref.qpos_hinge[-1]).max()))
    from tethered_lift import run
    for dt in (0.05, 0.025):
        out["flight"][dt] = run(dt_ms=dt, beats=6, kinematic=True, rot_amp=55.0)["lift_over_weight"]
    print(json.dumps(out, indent=1, default=str))
