"""Export the body's real mesh geometry for the browser visualiser.

Geometry is taken from the COMPILED MuJoCo model, not from the source STL
files, so what the browser draws is exactly what the physics uses: the same
vertices after mirroring and scaling, the same per-geom offsets, the same
material colours. A ball-and-stick approximation drawn from body positions
alone is not the fly, and using one invites reading the picture as the model.

Writes two files next to the page:

    geometry.bin    concatenated float32 vertices then uint32 indices
    geometry.json   per-geom: body index, local pose, buffer ranges, colour
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

import mujoco as mj
import numpy as np

from flyemu.body import Body

REPO = Path(__file__).resolve().parents[1]


def resolve_colour(m: mj.MjModel, g: int) -> list[float]:
    """The colour MuJoCo would draw this geom in.

    NeuroMechFly puts the cuticle colours in procedural TEXTURES and leaves
    most material rgba at [1,1,1,a], so reading mat_rgba alone yields a uniform
    grey fly. The drawn colour is the material rgba times the texture colour,
    so the texture is averaged and multiplied in. Flat procedural textures make
    that average exact; for a gradient it is the mean, which is what a
    single-colour-per-mesh renderer can represent.
    """
    matid = int(m.geom_matid[g])
    if matid < 0:
        return [float(x) for x in m.geom_rgba[g]]

    rgba = [float(x) for x in m.mat_rgba[matid]]
    texid = int(np.max(m.mat_texid[matid]))
    if texid < 0:
        return rgba

    adr = int(m.tex_adr[texid])
    h, w = int(m.tex_height[texid]), int(m.tex_width[texid])
    nc = int(m.tex_nchannel[texid])
    data = np.asarray(m.tex_data[adr:adr + h * w * nc]).reshape(-1, nc)[:, :3]
    tex = data.mean(axis=0) / 255.0
    return [rgba[0] * tex[0], rgba[1] * tex[1], rgba[2] * tex[2], rgba[3]]


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default="viz")
    args = ap.parse_args()
    out = REPO / args.out
    out.mkdir(parents=True, exist_ok=True)

    body = Body(with_camera=True)
    m = body.sim.mj_model

    verts: list[np.ndarray] = []
    faces: list[np.ndarray] = []
    geoms = []
    v_off = f_off = 0

    for g in range(m.ngeom):
        if m.geom_type[g] != mj.mjtGeom.mjGEOM_MESH:
            continue
        mid = int(m.geom_dataid[g])
        if mid < 0:
            continue
        va, vn = int(m.mesh_vertadr[mid]), int(m.mesh_vertnum[mid])
        fa, fn = int(m.mesh_faceadr[mid]), int(m.mesh_facenum[mid])
        v = np.asarray(m.mesh_vert[va:va + vn], dtype=np.float32).reshape(-1, 3)
        f = np.asarray(m.mesh_face[fa:fa + fn], dtype=np.int64).reshape(-1, 3)

        rgba = resolve_colour(m, g)

        geoms.append({
            "name": mj.mj_id2name(m, mj.mjtObj.mjOBJ_GEOM, g),
            "body": int(m.geom_bodyid[g]),
            "pos": [float(x) for x in m.geom_pos[g]],
            # MuJoCo stores quaternions as (w, x, y, z).
            "quat_wxyz": [float(x) for x in m.geom_quat[g]],
            "rgba": rgba,
            "vert_offset": v_off, "vert_count": vn,
            "face_offset": f_off, "face_count": fn,
        })
        verts.append(v)
        faces.append(f)
        v_off += vn
        f_off += fn

    if not geoms:
        print("no mesh geoms found")
        return 1

    V = np.concatenate(verts).astype(np.float32)
    F = np.concatenate(faces).astype(np.uint32)
    blob = V.tobytes() + F.tobytes()
    (out / "geometry.bin").write_bytes(blob)

    index = {
        "units": "mm",
        "n_geoms": len(geoms),
        "n_vertices": int(V.shape[0]),
        "n_triangles": int(F.shape[0]),
        "vertex_bytes": int(V.nbytes),
        "body_names": [mj.mj_id2name(m, mj.mjtObj.mjOBJ_BODY, i)
                       for i in range(m.nbody)],
        "geoms": geoms,
        "source": "flygym 2.1.0 NeuroMechFly, compiled MuJoCo model",
    }
    (out / "geometry.json").write_text(json.dumps(index))

    print(f"{len(geoms)} mesh geoms, {V.shape[0]:,} vertices, "
          f"{F.shape[0]:,} triangles")
    print(f"geometry.bin   {len(blob) / 1e6:.2f} MB")
    print(f"geometry.json  {(out / 'geometry.json').stat().st_size / 1e3:.1f} KB")
    bb = V.min(axis=0), V.max(axis=0)
    print(f"mesh-local bounds mm: {bb[0].round(2)} to {bb[1].round(2)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
