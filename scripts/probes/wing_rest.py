"""Session 12 B: why do the wings hang? Wing hinge parameters and a passive drop.

Builds the template body with the m9 wing settings (folded spring reference,
envelopes by function), prints each wing hinge's spring reference, range,
stiffness, damping and the wing's mass, then runs the body with zero actuation
and logs the wing angles. Static check: gravity torque on each hinge at the
start pose vs the spring torque that would hold it.

    uv run python scripts/probes/wing_rest.py [--ms 1500] [--out runs/s12/wings]
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


def wing_joints(m):
    return [j for j in range(m.njnt) if "_wing-" in (m.joint(j).name or "")]


def shot(m, d, cam: str) -> np.ndarray:
    r = mj.Renderer(m, 360, 480)
    imgs = []
    for az in (90.0, 180.0):          # side view and front view, free camera on the thorax
        c = mj.MjvCamera()
        c.type = mj.mjtCamera.mjCAMERA_FREE
        c.lookat[:] = d.xpos[[i for i in range(m.nbody) if m.body(i).name.endswith("c_thorax")][0]]
        c.distance, c.azimuth, c.elevation = 4.5, az, -15.0
        r.update_scene(d, camera=c)
        imgs.append(r.render().copy())
    r.close()
    return np.concatenate(imgs, axis=1)


def sheet(frames, path: Path) -> None:
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    fig, ax = plt.subplots(len(frames), 1, figsize=(9.6, 3.6 * len(frames)))
    for a_, (t, img) in zip(np.atleast_1d(ax), frames):
        a_.imshow(img); a_.set_axis_off(); a_.set_title(f"t = {t:.0f} ms (left: side, right: front)")
    fig.tight_layout(); fig.savefig(path, dpi=80); plt.close(fig)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--ms", type=float, default=1500.0)
    ap.add_argument("--out", default=str(REPO / "runs" / "s12" / "wings"))
    a = ap.parse_args()
    out = Path(a.out); out.mkdir(parents=True, exist_ok=True)
    b = Body(vision=False, with_camera=True)
    passive.fold_wings(b)
    flight.apply_wing_ranges(b)
    m, d = b.sim.mj_model, b.sim.mj_data
    b.reset()
    place_standing(b)
    wj = wing_joints(m)
    info = {}
    for j in wj:
        n = m.joint(j).name.split("/")[-1]
        qa, va = m.jnt_qposadr[j], m.jnt_dofadr[j]
        info[n] = dict(q_start_deg=float(np.degrees(d.qpos[qa])), qpos0_deg=float(np.degrees(m.qpos0[qa])),
                       spring_ref_deg=float(np.degrees(m.qpos_spring[qa])),
                       range_deg=np.degrees(m.jnt_range[j]).round(1).tolist(),
                       stiffness=float(m.jnt_stiffness[j]), damping=float(m.dof_damping[va]),
                       armature=float(m.dof_armature[va]), frictionloss=float(m.dof_frictionloss[va]))
    wb = [i for i in range(m.nbody) if "_wing" in (m.body(i).name or "")]
    masses = {m.body(i).name.split("/")[-1]: float(m.body_mass[i]) for i in wb}
    # gravity (bias) torque on each wing dof at the start pose, zero velocity
    d.qvel[:] = 0
    mj.mj_forward(m, d)
    grav = {m.joint(j).name.split("/")[-1]: float(d.qfrc_bias[m.jnt_dofadr[j]]) for j in wj}
    cam = f"{b.fly.name}/trackcam"
    zero = np.zeros(b.n_actuators)
    dt = m.opt.timestep * 1e3
    rows, frames = [], []
    n_steps = int(round(a.ms / dt))
    snap = {0, n_steps // 4, n_steps // 2, n_steps}
    for k in range(n_steps + 1):
        if k % max(1, int(round(10 / dt))) == 0:
            rows.append([k * dt] + [float(np.degrees(d.qpos[m.jnt_qposadr[j]])) for j in wj])
        if k in snap:
            frames.append((k * dt, shot(m, d, cam)))
        if k == n_steps:
            break
        b.actuate(zero)
        b.step()
    names = [m.joint(j).name.split("/")[-1] for j in wj]
    sheet(frames, out / "wing_rest_sheet.png")
    np.savetxt(out / "wing_angles.csv", np.array(rows), delimiter=",",
               header="t_ms," + ",".join(names), comments="")
    res = dict(joints=info, wing_masses_g=masses, gravity_bias_torque_uNmm=grav,
               end_deg=dict(zip(names, rows[-1][1:])), timestep_ms=dt)
    (out / "wing_rest.json").write_text(json.dumps(res, indent=1))
    print(json.dumps(res, indent=1))


if __name__ == "__main__":
    main()
