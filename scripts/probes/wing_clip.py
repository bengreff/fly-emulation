"""Session 12: do the folded wings clip through the body? (Ben, 5 Oct 2026)

Two separate questions:
  visual   - at the rest pose, how many wing render vertices (vein mesh + membrane)
             lie inside the thorax / abdomen render meshes, and how deep;
  physical - which wing-body geom pairs can generate contacts at all (bitmasks plus
             MuJoCo's parent-child filter), and what the contacts are at the rest pose.
Also renders side / top / rear views of the rest pose.

    uv run --with trimesh --with rtree python scripts/probes/wing_clip.py [--on-abdomen] [--out runs/s12/wingclip]
    uv run python scripts/probes/wing_clip.py --organism m9f --seed 12   # closed-loop sheet, gate overrides
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
from flyemu import flight, passive  # noqa: E402
from flyemu.body import Body  # noqa: E402
from flyemu.deadfly import place_standing  # noqa: E402


def short(s):
    return (s or "").split("/")[-1]


def geom_world_mesh(m, d, g):
    import trimesh
    mid = m.geom_dataid[g]
    v0, nv = m.mesh_vertadr[mid], m.mesh_vertnum[mid]
    f0, nf = m.mesh_faceadr[mid], m.mesh_facenum[mid]
    v = m.mesh_vert[v0:v0 + nv] @ d.geom_xmat[g].reshape(3, 3).T + d.geom_xpos[g]
    return trimesh.Trimesh(v, m.mesh_face[f0:f0 + nf], process=False)


def body_geoms(m, pred):
    return [g for g in range(m.ngeom) if m.geom_type[g] == mj.mjtGeom.mjGEOM_MESH and pred(short(m.body(m.geom_bodyid[g]).name), short(m.geom(g).name))]


def visual_overlap(m, d):
    """Wing render vertices inside each body render mesh (trimesh ray parity)."""
    import trimesh  # noqa: F401
    targets = {"thorax": body_geoms(m, lambda b, g: b == "c_thorax"),
               "abdomen": body_geoms(m, lambda b, g: b.startswith("c_abdomen"))}
    out = {}
    for side in ("l", "r"):
        for part in ("brown", "membrane"):
            g = [x for x in range(m.ngeom) if short(m.geom(x).name) == f"{side}_wing_{part}"][0]
            wm = geom_world_mesh(m, d, g)
            pts = wm.vertices
            hj = [j for j in range(m.njnt) if short(m.joint(j).name) == f"c_thorax-{side}_wing-yaw"][0]
            r_hinge = np.linalg.norm(pts - d.xanchor[hj], axis=1)
            for tname, gs in targets.items():
                inside = np.zeros(len(pts), bool)
                depth = np.zeros(len(pts))
                for tg in gs:
                    tm = geom_world_mesh(m, d, tg)
                    if not tm.is_watertight:
                        tm.fill_holes()
                    c = np.concatenate([tm.contains(pts[i:i + 500]) for i in range(0, len(pts), 500)])  # bounded memory
                    if c.any():
                        _, dist, _ = tm.nearest.on_surface(pts[c])
                        depth[c] = np.maximum(depth[c], dist)
                    inside |= c
                out[f"{side}_wing_{part} in {tname}"] = dict(
                    n_inside=int(inside.sum()), n_vertices=int(len(pts)),
                    frac=float(inside.mean()), max_depth_um=float(depth.max() * 1e3),
                    max_dist_from_hinge_mm=float(r_hinge[inside].max()) if inside.any() else 0.0)
    return out


def collision_pairs(m):
    """Which wing-body geom pairs can collide: bitmask test and parent-child filter."""
    rows = []
    filt_parent = not (m.opt.disableflags & mj.mjtDisableBit.mjDSBL_FILTERPARENT)
    wing = [g for g in range(m.ngeom) if short(m.geom(g).name).endswith("_wing_membrane")]
    body = [g for g in range(m.ngeom) if m.geom_contype[g] or m.geom_conaffinity[g]]
    for w in wing:
        for g in body:
            bw, bg = m.geom_bodyid[w], m.geom_bodyid[g]
            if bw == bg or short(m.body(bg).name).endswith("_wing"):
                continue
            nm = short(m.body(bg).name)
            if not (nm.startswith("c_") or "haltere" in nm):
                continue
            mask = bool((m.geom_contype[w] & m.geom_conaffinity[g]) or (m.geom_contype[g] & m.geom_conaffinity[w]))
            # MuJoCo filters parent-child pairs by weld-body; the wing's parent is the thorax
            pw, pg = m.body_parentid[m.body_weldid[bw]], m.body_parentid[m.body_weldid[bg]]
            parent = filt_parent and (m.body_weldid[bg] == pw or m.body_weldid[bw] == pg) and m.body_weldid[bg] != 0
            rows.append(dict(wing=short(m.geom(w).name), other=short(m.geom(g).name),
                             bitmask=mask, parent_filtered=bool(parent), can_contact=bool(mask and not parent)))
    return rows


def contacts(m, d):
    mj.mj_collision(m, d)
    out = []
    for i in range(d.ncon):
        c = d.contact[i]
        a, b = short(m.geom(c.geom1).name), short(m.geom(c.geom2).name)
        if "wing" in a or "wing" in b:
            out.append(dict(g1=a, g2=b, dist_um=float(c.dist * 1e3)))
    return out


def views(m, d, path: Path, title: str):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    th = [i for i in range(m.nbody) if short(m.body(i).name) == "c_thorax"][0]
    ab = [i for i in range(m.nbody) if short(m.body(i).name) == "c_abdomen3"][0]
    look = 0.5 * (d.xpos[th] + d.xpos[ab])
    r = mj.Renderer(m, 480, 640)
    spec = [("left side", 90.0, 0.0), ("right side", 270.0, 0.0), ("top", 90.0, -89.9),
            ("rear, above", 0.0, -30.0), ("front, above", 180.0, -30.0), ("rear, low", 0.0, -5.0)]
    fig, ax = plt.subplots(2, 3, figsize=(15, 8))
    for a_, (lab, az, el) in zip(ax.ravel(), spec):
        c = mj.MjvCamera()
        c.type = mj.mjtCamera.mjCAMERA_FREE
        c.lookat[:] = look
        c.distance, c.azimuth, c.elevation = 3.2, az, el
        r.update_scene(d, camera=c)
        a_.imshow(r.render()); a_.set_axis_off(); a_.set_title(lab)
    r.close()
    fig.suptitle(title); fig.tight_layout(); fig.savefig(path, dpi=70); plt.close(fig)


def settle(b, ms: float) -> dict:
    """Zero actuation with the m9v wing hinge stiffness; wing angles and wing contacts after ms."""
    m, d = b.sim.mj_model, b.sim.mj_data
    passive.set_wing_stiffness(b, passive.WING_STIFFNESS_BERGOU)
    m.opt.noslip_iterations = 0
    wj = [j for j in range(m.njnt) if "_wing-" in m.joint(j).name]
    q0 = np.array([d.qpos[m.jnt_qposadr[j]] for j in wj])
    zero = np.zeros(b.n_actuators)
    for _ in range(int(round(ms / (m.opt.timestep * 1e3)))):
        b.actuate(zero)
        b.step()
    mj.mj_forward(m, d)
    q1 = np.array([d.qpos[m.jnt_qposadr[j]] for j in wj])
    cs = contacts(m, d)
    return dict(ms=ms, wing_drift_deg=dict(zip([short(m.joint(j).name) for j in wj], np.degrees(q1 - q0).round(2).tolist())),
                wing_contacts=cs, min_wing_contact_dist_um=min([c["dist_um"] for c in cs] or [None]) if cs else None,
                visual=visual_overlap(m, d))


def build(ranges, on_abdomen: bool = False):
    b = Body(vision=False, with_camera=True)
    passive.fold_wings(b)
    if on_abdomen:
        passive.rest_wings_on_abdomen(b)
    flight.apply_wing_ranges(b, ranges)
    b.reset()
    place_standing(b)
    mj.mj_forward(b.sim.mj_model, b.sim.mj_data)
    return b


GATE_SET = {"motor_unit:all|force_per_spike": 10, "motor_map:wing|roles": 1, "sense:mechano|assign_by_nerve": 2,
            "muscle:leg|midhind_source": 1, "jump:ttm|peak_torque": 90, "joint:leg|damping_source": 1,
            "jump:ttm|exclude_from_hill": 1, "contact:floor|noslip_iterations": 0, "motor_map:neck|mirror_sides": 1}


def organism_sheet(profile: str, seed: int, ms: float, out: Path) -> dict:
    """Closed loop at rest (no stimulus), gate overrides; views and wing contacts at 0, ms/2, ms."""
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from flyemu.organism import Organism
    org = Organism(policy="minimal", profile=profile, min_synapses=5, overrides=dict(GATE_SET), seed=seed, with_camera=True)
    m, d = org.body.sim.mj_model, org.body.sim.mj_data
    wj = [j for j in range(m.njnt) if "_wing-" in m.joint(j).name]
    steps = int(ms / org.timestep_ms)
    snap = {0: None, steps // 4: None, steps // 2: None, steps: None}
    th = [i for i in range(m.nbody) if short(m.body(i).name) == "c_thorax"][0]
    aj = [j for j in range(m.njnt) if short(m.joint(j).name).startswith("c_abdomen") or "abdomen" in short(m.joint(j).name)]
    rec = {}
    for s in range(steps + 1):
        if s in snap:
            mj.mj_forward(m, d)
            tag = f"{s * org.timestep_ms:.0f} ms"
            views(m, d, out / f"_tmp_{s}.png", tag)
            snap[s] = plt.imread(out / f"_tmp_{s}.png")
            (out / f"_tmp_{s}.png").unlink()
            xm = d.xmat[th].reshape(3, 3)
            ov_ = visual_overlap(m, d)
            rec[tag] = dict(wing_deg={short(m.joint(j).name): round(float(np.degrees(d.qpos[m.jnt_qposadr[j]])), 2) for j in wj},
                            wing_contacts=contacts(m, d),
                            visual_inside={k: (v["n_inside"], round(v["max_depth_um"], 1)) for k, v in ov_.items() if v["n_inside"]},
                            thorax_z_mm=round(float(d.xpos[th, 2]), 3),
                            thorax_pitch_deg=round(float(np.degrees(np.arcsin(-xm[2, 0]))), 1),
                            thorax_roll_deg=round(float(np.degrees(np.arctan2(xm[2, 1], xm[2, 2]))), 1),
                            abdomen_deg={short(m.joint(j).name): round(float(np.degrees(d.qpos[m.jnt_qposadr[j]])), 1) for j in aj})
        if s == steps:
            break
        obs = org.body.observe()
        sp = org.net.step(external_mv=org.sense(s, obs))
        org.motor_step(sp)
    fig, ax = plt.subplots(len(snap), 1, figsize=(15, 8 * len(snap)))
    for a_, (s, img) in zip(ax, snap.items()):
        a_.imshow(img); a_.set_axis_off()
    fig.suptitle(f"closed loop at rest, {profile}, seed {seed}")
    fig.tight_layout(); fig.savefig(out / f"organism_{profile}_s{seed}.png", dpi=60); plt.close(fig)
    return rec


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=str(REPO / "runs" / "s12" / "wingclip"))
    ap.add_argument("--on-abdomen", action="store_true", help="joint:wing|folded_pose 1")
    ap.add_argument("--settle-ms", type=float, default=300.0)
    ap.add_argument("--organism", default="", help="profile: closed-loop sheet instead of the plain body")
    ap.add_argument("--seed", type=int, default=12)
    ap.add_argument("--ms", type=float, default=600.0)
    a = ap.parse_args()
    if a.organism:
        out = Path(a.out); out.mkdir(parents=True, exist_ok=True)
        rec = organism_sheet(a.organism, a.seed, a.ms, out)
        (out / f"organism_{a.organism}_s{a.seed}.json").write_text(json.dumps(rec, indent=1))
        print(json.dumps(rec, indent=1))
        return
    tag = "on_abdomen" if a.on_abdomen else "flybody"
    out = Path(a.out); out.mkdir(parents=True, exist_ok=True)
    b = build(None, a.on_abdomen)
    m, d = b.sim.mj_model, b.sim.mj_data
    wj = {short(m.joint(j).name): float(np.degrees(d.qpos[m.jnt_qposadr[j]])) for j in range(m.njnt) if "_wing-" in m.joint(j).name}
    res = dict(wing_joint_deg=wj, visual=visual_overlap(m, d), pairs=collision_pairs(m), contacts=contacts(m, d))
    views(m, d, out / f"rest_{tag}.png", f"folded rest pose, t = 0 ({tag})")
    res["settle"] = settle(b, a.settle_ms)
    views(m, d, out / f"rest_{tag}_settled.png", f"after {a.settle_ms:.0f} ms passive, Bergou hinge stiffness ({tag})")
    (out / f"wing_clip_{tag}.json").write_text(json.dumps(res, indent=1))
    print(json.dumps(dict(wing_joint_deg=wj, visual=res["visual"], contacts=res["contacts"], settle=res["settle"]), indent=1))


if __name__ == "__main__":
    main()
