"""Measure what each leg actuator actually does to the foot.

The muscle-to-joint map has to state a SIGN. Anatomy says a muscle flexes a
joint or promotes a coxa; it cannot say which direction that is in this body
model's coordinate frame. That is a property of the model, so it is measured.

Readout: with gravity off and the body starting from its neutral pose, drive
ONE actuator with a fixed positive torque and record where the tarsal tip goes,
expressed in the THORAX frame so the body's own counter-rotation cancels:

    fore      + forward, towards the head      (promotion / protraction)
    lateral   + away from the midline          (abduction)
    up        + away from the ground           (levation)
    leg_len   distance coxa to tarsal tip      (- shortens: flexion)

A first version of this measured the angle between body origins, which is
meaningless for a serial limb: a child body's origin sits AT its joint, so
rotating the joint barely moves it. The joint moved 12 degrees and the readout
said 0.006 mm.

    uv run python scripts/calibrate_joint_signs.py
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

import mujoco as mj
import numpy as np
import pandas as pd

from flyemu.body import Body

REPO = Path(__file__).resolve().parents[1]
LEGS = ["lf", "lm", "lh", "rf", "rm", "rh"]


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--torque", type=float, default=3.0, help="uN*mm")
    ap.add_argument("--settle-ms", type=float, default=20.0)
    ap.add_argument("--drive-ms", type=float, default=60.0)
    ap.add_argument("--model", default="flybody",
                    choices=["flybody", "neuromechfly"])
    ap.add_argument("--out", default=None)
    args = ap.parse_args()

    args.out = args.out or f"data/derived/joint_signs_{args.model}.csv"
    body = Body(model=args.model, with_camera=False)
    m, d = body.sim.mj_model, body.sim.mj_data
    dt_ms = body.timestep * 1000.0
    n_settle, n_drive = int(args.settle_ms / dt_ms), int(args.drive_ms / dt_ms)
    m.opt.gravity[:] = 0.0    # measure the actuator, not the fall

    pre = f"{body.fly.name}/"
    bid = lambda n: mj.mj_name2id(m, mj.mjtObj.mjOBJ_BODY, pre + n)
    thorax = bid("c_thorax")
    tip = {leg: bid(f"{leg}_tarsus5") for leg in LEGS}
    # Measure the tarsal GEOM centre, not the body origin. A body's origin sits
    # at its own joint, so using it makes the most distal joint read as dead.
    def tip_geom(leg: str) -> int:
        """A geom on the distal tarsus, by name; body ids alone are not enough
        because a segment may carry several geoms or none."""
        want = f"{leg}_tarsus5"
        for g in range(m.ngeom):
            nm = mj.mj_id2name(m, mj.mjtObj.mjOBJ_GEOM, g) or ""
            if want in nm:
                return g
        raise KeyError(f"no geom found for {want}")

    gid = {leg: tip_geom(leg) for leg in LEGS}
    coxa = {leg: bid(f"{leg}_coxa") for leg in LEGS}

    def foot(leg: str) -> tuple[np.ndarray, float]:
        """Tarsal tip in the thorax frame, and the leg's base-to-tip length."""
        R = np.asarray(d.xmat[thorax]).reshape(3, 3)
        tip_x = np.asarray(d.geom_xpos[gid[leg]])
        local = R.T @ (tip_x - np.asarray(d.xpos[thorax]))
        length = float(np.linalg.norm(tip_x - np.asarray(d.xpos[coxa[leg]])))
        return local, length

    rows = []
    for a in range(body.n_actuators):
        name = body.actuator_names[a]
        short = name.removeprefix(pre).removesuffix("-motor")
        leg = next((L for L in LEGS if re.search(rf"(^|-){L}_", short)), None)
        jid = int(m.actuator_trnid[a, 0])
        qadr = int(m.jnt_qposadr[jid])

        body.reset()
        u = np.zeros(body.n_actuators)
        for _ in range(n_settle):
            body.actuate(u); body.step()
        q0 = float(d.qpos[qadr])
        p0, l0 = foot(leg) if leg else (None, None)

        u[a] = args.torque
        for _ in range(n_drive):
            body.actuate(u); body.step()
        q1 = float(d.qpos[qadr])
        p1, l1 = foot(leg) if leg else (None, None)

        row = {
            "actuator": short, "leg": leg,
            "dq_deg": round(np.degrees(q1 - q0), 3),
            "q_start_deg": round(np.degrees(q0), 2),
        }
        if leg:
            side = 1.0 if leg.startswith("l") else -1.0
            dp = p1 - p0
            row.update({
                "foot_fore_mm": round(float(dp[0]), 4),
                "foot_lateral_mm": round(float(dp[1] * side), 4),
                "foot_up_mm": round(float(dp[2]), 4),
                "leg_len_change_mm": round(l1 - l0, 4),
                "leg_len_start_mm": round(l0, 3),
            })
            mags = {"fore": dp[0], "lateral": dp[1] * side, "up": dp[2]}
            dom = max(mags, key=lambda k: abs(mags[k]))
            names = {
                ("fore", 1): "protraction (foot forward)",
                ("fore", -1): "retraction (foot backward)",
                ("lateral", 1): "abduction (foot outward)",
                ("lateral", -1): "adduction (foot inward)",
                ("up", 1): "levation (foot up)",
                ("up", -1): "depression (foot down)",
            }
            row["dominant_action"] = (
                names[(dom, 1 if mags[dom] > 0 else -1)]
                if abs(mags[dom]) > 1e-3 else "no foot movement"
            )
            row["length_action"] = (
                "flexion (leg shortens)" if (l1 - l0) < -1e-3
                else "extension (leg lengthens)" if (l1 - l0) > 1e-3
                else "no length change"
            )
        rows.append(row)

    df = pd.DataFrame(rows)
    out = REPO / args.out
    out.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(out, index=False)

    legs = df[df.leg.notna()]
    print(f"{len(df)} actuators driven singly at +{args.torque} uN*mm "
          f"for {args.drive_ms:g} ms, gravity off")
    print(f"uniform joint deflection: {legs.dq_deg.min():.3f} to "
          f"{legs.dq_deg.max():.3f} deg "
          f"(all joints share one stiffness, so one torque gives one angle)\n")
    cols = ["actuator", "foot_fore_mm", "foot_lateral_mm", "foot_up_mm",
            "leg_len_change_mm", "dominant_action", "length_action"]
    print(legs[legs.leg == "lf"][cols].to_string(index=False))
    print(f"\n{out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
