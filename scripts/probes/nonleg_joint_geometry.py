"""Session 12 B (non-leg torque per spike): the length of each non-leg moved part
on the flybody mesh (Vaxenburg et al. 2025; one female, confocal scan), the lever
used to turn a motor unit's twitch force into a torque at that joint, measured the
same way for the front-leg segments that carry the measured anchor.

For each actuated non-leg joint (and lf_coxa, lf_trochanterfemur, lf_tibia for
comparison with data/derived/leg_segment_geometry_flybody.csv) the child body's mesh
is projected on the line from the joint to the mesh centroid:
  child_len_mm  extent of the child mesh along that line beyond the joint (mm)
  com_mm        distance from the joint to the mesh centroid (mm)
  base_width_mm largest convex-hull width of the child mesh in a 12 um slab at 5%
                of its length from the joint (mm)
Label derived (computed from the mesh). The body is in its default pose.

    uv run python scripts/probes/nonleg_joint_geometry.py
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

import mujoco as mj
import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "src"))
sys.path.insert(0, str(REPO / "scripts" / "probes"))
from flyemu.body import Body  # noqa: E402
from leg_segment_geometry import section  # noqa: E402

LEG_REF = ("lf_coxa", "lf_trochanterfemur", "lf_tibia")
OUT = REPO / "data" / "derived" / "nonleg_joint_geometry_flybody.csv"
HEADER = ("# Non-leg moved-part geometry on the flybody mesh (Vaxenburg et al. 2025; one female, confocal scan) "
          "by scripts/probes/nonleg_joint_geometry.py (session 12 B). Label derived. child_len: extent of the "
          "child mesh beyond the joint along the joint-to-centroid line; com: joint to mesh centroid; "
          "base_width: widest hull width at 5% of child_len. mm. Front-leg rows for comparison.\n")


def world_points(m, d, body_id: int) -> np.ndarray:
    pts = []
    for g in range(m.ngeom):
        if m.geom_bodyid[g] != body_id or m.geom_type[g] != mj.mjtGeom.mjGEOM_MESH:
            continue
        mid = m.geom_dataid[g]
        v = m.mesh_vert[m.mesh_vertadr[mid]: m.mesh_vertadr[mid] + m.mesh_vertnum[mid]]
        pts.append(v @ d.geom_xmat[g].reshape(3, 3).T + d.geom_xpos[g])
    return np.concatenate(pts) if pts else np.zeros((0, 3))


def extent(p: np.ndarray, origin: np.ndarray, u: np.ndarray) -> dict:
    e1 = np.cross(u, [1.0, 0, 0] if abs(u[0]) < 0.9 else [0, 1.0, 0]); e1 /= np.linalg.norm(e1)
    e2 = np.cross(u, e1)
    s = (p - origin) @ u
    q = np.stack([(p - origin) @ e1, (p - origin) @ e2], axis=1)
    L = float(s.max())
    sel = np.abs(s - 0.05 * L) < 0.006
    return dict(child_len_mm=round(L, 4), com_mm=round(float(s.mean()), 4),
                base_width_mm=round(section(q[sel])[1], 4) if sel.sum() >= 3 else None)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=str(OUT))
    a = ap.parse_args()
    b = Body(vision=False)
    m, d = b.sim.mj_model, b.sim.mj_data
    mj.mj_forward(m, d)
    pre = b.fly.name + "/"
    children = []
    for i in range(m.nu):
        n = mj.mj_id2name(m, mj.mjtObj.mjOBJ_ACTUATOR, i) or ""
        if n.endswith("-motor") and not any(k in n for k in ("coxa", "femur", "tibia", "tarsus")):
            children.append(m.jnt_bodyid[m.actuator_trnid[i, 0]])
    children += [mj.mj_name2id(m, mj.mjtObj.mjOBJ_BODY, pre + c) for c in LEG_REF]
    rows = []
    for bid in dict.fromkeys(children):
        p = world_points(m, d, bid)
        if not len(p):
            continue
        origin = d.xpos[bid].copy()
        u = p.mean(0) - origin; u /= np.linalg.norm(u)
        r = dict(child=mj.mj_id2name(m, mj.mjtObj.mjOBJ_BODY, bid).removeprefix(pre),
                 parent=mj.mj_id2name(m, mj.mjtObj.mjOBJ_BODY, m.body_parentid[bid]).removeprefix(pre),
                 n_vertices=len(p))
        r.update(extent(p, origin, u))
        rows.append(r)
    df = pd.DataFrame(rows)
    out = Path(a.out)
    out.write_text(HEADER + df.to_csv(index=False))
    print(df.to_string(index=False))


if __name__ == "__main__":
    main()
