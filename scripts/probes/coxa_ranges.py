"""Session 12 B: coxa ranges. Which envelope is the body using, and do the
fitted rest angles fit inside flybody's own leg-specific ranges?

Builds the m9w template body (no brain), then for every thorax-coxa hinge
prints: spawn angle q0, the range applied now (joints.py envelope about q0),
flybody's native range and spring reference (flygym joints.yaml, fitted to
grooming IK by Vaxenburg et al. 2025; inferred), the fitted rest angle
(F-REST-1, inferred), and the foot's displacement for +10 deg of the hinge in
the thorax frame (x forward, y left, z up) to read each axis's action.

    uv run python scripts/probes/coxa_ranges.py [--out runs/s12/coxa]
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import mujoco as mj
import numpy as np
import yaml

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "src"))
from flyemu import passive, profiles  # noqa: E402
from flyemu.body import Body  # noqa: E402
from flyemu.registry import Registry  # noqa: E402

NATIVE = REPO / ".venv/lib/python3.12/site-packages/flygym/assets/model/flybody/joints.yaml"


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=str(REPO / "runs" / "s12" / "coxa"))
    a = ap.parse_args()
    out = Path(a.out); out.mkdir(parents=True, exist_ok=True)
    reg = Registry("minimal")
    profiles.apply(reg, profiles.WORKING_PROFILE)
    b = Body(vision=False)
    passive.register(reg, b)
    passive.register_rest(reg, b)
    m, d = b.sim.mj_model, b.sim.mj_data
    b.reset()
    mj.mj_forward(m, d)
    nat = yaml.safe_load(NATIVE.read_text())["ranges"]
    pre = f"{b.fly.name}/"
    thorax = mj.mj_name2id(m, mj.mjtObj.mjOBJ_BODY, pre + "c_thorax")
    R = d.xmat[thorax].reshape(3, 3)
    rows = {}
    for j in range(m.njnt):
        n = (m.joint(j).name or "").removeprefix(pre)
        if "c_thorax-" not in n or "_coxa-" not in n:
            continue
        leg = n.split("-")[1].split("_")[0]
        qa = m.jnt_qposadr[j]
        foot = mj.mj_name2id(m, mj.mjtObj.mjOBJ_BODY, pre + f"{leg}_tarsus5")
        dd = mj.MjData(m); dd.qpos[:] = d.qpos; mj.mj_forward(m, dd)
        p0 = R.T @ dd.xpos[foot]
        dd.qpos[qa] += np.radians(10.0); mj.mj_forward(m, dd)
        dp = R.T @ dd.xpos[foot] - p0
        nr = nat.get(n, {})
        lo_n, hi_n = (float(x) for x in nr.get("range", ("nan", "nan")))
        ref = float(m.qpos_spring[qa])
        lo_c, hi_c = (float(x) for x in m.jnt_range[j])
        rows[n] = dict(
            q0_deg=round(float(np.degrees(d.qpos[qa])), 1),
            range_now_deg=[round(np.degrees(lo_c), 1), round(np.degrees(hi_c), 1)],
            range_native_deg=[round(np.degrees(lo_n), 1), round(np.degrees(hi_n), 1)],
            native_springref_deg=(round(np.degrees(float(nr["springref"])), 1) if "springref" in nr else None),
            fitted_rest_deg=round(float(np.degrees(ref)), 1),
            rest_inside_now=bool(lo_c - 1e-6 <= ref <= hi_c + 1e-6),
            rest_inside_native=bool(lo_n - 1e-6 <= ref <= hi_n + 1e-6),
            q0_inside_native=bool(lo_n - 1e-6 <= d.qpos[qa] <= hi_n + 1e-6),
            foot_dxyz_um_per_10deg=[round(float(v) * 1e3) for v in dp],
        )
    print(f"{'joint':28s} {'q0':>6s} {'now':>14s} {'native':>14s} {'natref':>7s} {'rest':>7s} in_now in_nat  foot dxyz um/+10deg")
    for n, r in rows.items():
        print(f"{n:28s} {r['q0_deg']:6.1f} {str(r['range_now_deg']):>14s} {str(r['range_native_deg']):>14s} "
              f"{str(r['native_springref_deg']):>7s} {r['fitted_rest_deg']:7.1f} {str(r['rest_inside_now']):6s} "
              f"{str(r['rest_inside_native']):6s} {r['foot_dxyz_um_per_10deg']}")
    (out / "coxa_ranges.json").write_text(json.dumps(rows, indent=1))


if __name__ == "__main__":
    main()
