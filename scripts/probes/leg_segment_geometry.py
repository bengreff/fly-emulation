"""Session 12 B (mid/hind leg muscles): leg segment geometry from the flybody meshes.

For each leg segment (coxa, trochanter-femur, tibia, tarsus 1) of each leg:
  length      distance from the segment's joint to its child's joint (mm)
  area_mid    mean convex-hull cross-section of the mesh over the middle third of the
              segment, perpendicular to its long axis (mm^2)
  width_dist  largest mesh width in the distal fifth (mm), the lever the next joint's
              tendons work on
  width_prox  same in the proximal fifth (mm)
The mesh is flybody's (Vaxenburg et al. 2025, from a confocal scan of one female);
these are measured on that mesh, not on a population.

    uv run python scripts/probes/leg_segment_geometry.py [--out runs/s12/muscles]
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

import mujoco as mj
import numpy as np
import pandas as pd
from scipy.spatial import ConvexHull

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "src"))
from flyemu.body import Body  # noqa: E402

SEGMENTS = (("coxa", "trochanterfemur"), ("trochanterfemur", "tibia"), ("tibia", "tarsus1"),
            ("tarsus1", "tarsus2"))


def mesh_points_in_body(m, body_id: int) -> np.ndarray:
    """All mesh vertices of a body's geoms, in the body frame."""
    pts = []
    for g in range(m.ngeom):
        if m.geom_bodyid[g] != body_id or m.geom_type[g] != mj.mjtGeom.mjGEOM_MESH:
            continue
        mid = m.geom_dataid[g]
        v = m.mesh_vert[m.mesh_vertadr[mid]: m.mesh_vertadr[mid] + m.mesh_vertnum[mid]]
        R = np.zeros(9)
        mj.mju_quat2Mat(R, m.geom_quat[g])
        pts.append(v @ R.reshape(3, 3).T + m.geom_pos[g])
    return np.concatenate(pts) if pts else np.zeros((0, 3))


def section(p2: np.ndarray) -> tuple[float, float]:
    if len(p2) < 3:
        return 0.0, 0.0
    hull = ConvexHull(p2)
    c = p2[hull.vertices]
    width = float(np.max(np.linalg.norm(c[:, None] - c[None], axis=-1)))
    return float(hull.volume), width          # 2-D hull: volume is the area


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=str(REPO / "runs" / "s12" / "muscles"))
    a = ap.parse_args()
    b = Body(vision=False)
    m = b.sim.mj_model
    pre = b.fly.name + "/"
    bid = lambda n: mj.mj_name2id(m, mj.mjtObj.mjOBJ_BODY, pre + n)  # noqa: E731
    rows = []
    for leg in ("lf", "lm", "lh", "rf", "rm", "rh"):
        for seg, child in SEGMENTS:
            i, j = bid(f"{leg}_{seg}"), bid(f"{leg}_{child}")
            axis = m.body_pos[j].copy()                      # child joint in this body's frame
            L = float(np.linalg.norm(axis))
            u = axis / L
            e1 = np.cross(u, [1.0, 0, 0] if abs(u[0]) < 0.9 else [0, 1.0, 0])
            e1 /= np.linalg.norm(e1)
            e2 = np.cross(u, e1)
            p = mesh_points_in_body(m, i)
            s = p @ u                                        # position along the axis, 0 = joint
            q = np.stack([p @ e1, p @ e2], axis=1)
            areas, widths = [], []
            for f in np.linspace(1 / 3, 2 / 3, 7):
                sel = np.abs(s - f * L) < L / 30
                ar, w = section(q[sel])
                areas.append(ar)
                widths.append(w)
            dist = section(q[(s > 0.8 * L) & (s < L)])[1]
            prox = section(q[(s > 0) & (s < 0.2 * L)])[1]
            rows.append(dict(leg=leg, segment=seg, length_mm=round(L, 4),
                             area_mid_mm2=round(float(np.mean(areas)), 5),
                             width_mid_mm=round(float(np.mean(widths)), 4),
                             width_dist_mm=round(dist, 4), width_prox_mm=round(prox, 4),
                             n_vertices=int(len(p))))
    df = pd.DataFrame(rows)
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    df.to_csv(out / "leg_segment_geometry.csv", index=False)
    print(df.to_string(index=False))
    # mid/hind relative to front, mean of left and right
    df["pos"] = df.leg.str[1]
    g = df.groupby(["pos", "segment"])[["length_mm", "area_mid_mm2", "width_dist_mm", "width_prox_mm"]].mean()
    rel = g / g.xs("f", level="pos")
    print("\nrelative to the front leg (L/R mean):")
    print(rel.round(3).to_string())


if __name__ == "__main__":
    main()
