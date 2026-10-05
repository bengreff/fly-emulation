"""Session 12 B (CTr range conflict, F-COXA-2): the model's coxa-femur flexion
angle as a function of its CTr hinge angle, per leg, so measured 3D joint angles
(keypoint-based, e.g. Anipose: the angle at the coxa-femur keypoint between the
coxa and femur segments, 180 deg = straight) can be mapped onto the hinge and
compared with flybody's CTr range (-8.6..114.6 deg front/mid, -40..86 hind).

Keypoints are the joint anchors: ThC (c_thorax-coxa), CTr (coxa-trochanterfemur)
and FTi (trochanterfemur-tibia); flexion = angle at CTr between CTr->ThC and
CTr->FTi. Only the CTr pitch hinge moves; the other leg joints stay at 0, so the
angle depends on the hinge alone up to the CTr roll (0 here).

    uv run python scripts/probes/ctr_flexion_map.py [--out runs/s12/body]
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import mujoco as mj
import numpy as np

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "src"))
from flyemu.body import Body  # noqa: E402

LEGS = ("lf", "lm", "lh", "rf", "rm", "rh")


def flexion_curve(b: Body, leg: str, q_deg: np.ndarray) -> tuple[np.ndarray, list[float]]:
    m = b.sim.mj_model
    d = mj.MjData(m)
    name = lambda s: mj.mj_name2id(m, mj.mjtObj.mjOBJ_JOINT, f"{b.fly.name}/{s}")  # noqa: E731
    thc, ctr = name(f"c_thorax-{leg}_coxa-pitch"), name(f"{leg}_coxa-{leg}_trochanterfemur-pitch")
    fti = name(f"{leg}_trochanterfemur-{leg}_tibia-pitch")
    rng = np.degrees(m.jnt_range[ctr]).round(1).tolist()
    out = []
    for q in np.radians(q_deg):
        d.qpos[:] = m.qpos0
        d.qpos[m.jnt_qposadr[ctr]] = q
        mj.mj_kinematics(m, d)
        u, v = d.xanchor[thc] - d.xanchor[ctr], d.xanchor[fti] - d.xanchor[ctr]
        out.append(np.degrees(np.arccos(np.clip(u @ v / np.linalg.norm(u) / np.linalg.norm(v), -1, 1))))
    return np.array(out), rng


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=str(REPO / "runs" / "s12" / "body"))
    a = ap.parse_args()
    b = Body(vision=False)
    q = np.arange(-100.0, 120.1, 2.0)
    res = {"hinge_deg": q.tolist(), "legs": {}}
    for leg in LEGS:
        f, rng = flexion_curve(b, leg, q)
        res["legs"][leg] = {"flexion_deg": f.round(2).tolist(), "model_range_deg": rng,
                            "flexion_at_hinge_0": round(float(f[np.argmin(abs(q))]), 1),
                            "d_flexion_d_hinge": round(float(np.polyfit(q[40:70], f[40:70], 1)[0]), 3)}
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    (out / "ctr_flexion_map.json").write_text(json.dumps(res))
    print(json.dumps({k: {kk: vv for kk, vv in v.items() if kk != "flexion_deg"} for k, v in res["legs"].items()}, indent=1))


if __name__ == "__main__":
    main()
