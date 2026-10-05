"""Session 12 (aero:wing|added_mass): check the blade-element added-mass force in the
running model against an independent calculation from the stroke-frame angles.

Model side: hover_blade_trace's loop (imposed table kinematics, thorax held at the
measured body pitch), recording the left wing's added-mass force each step (hook
.parts[0, 3], world frame). Independent side: the same beat's stroke, deviation and
rotation angles (Database S1 robot level: the 100 samples the table was fitted to,
periodic cubic spline as in flight.TableKinematics), span and leading-edge vectors from
flight.stroke_frame_vectors on a fine phase grid, mid-chord points r s - (0.5 - x0) c
le per strip, their normal acceleration by periodic central differences, and
-rho pi c^2/4 dr a_n along the normal (Sane & Dickinson 2001 eq. 2 in strip form).
Strip radii, chords and x0 come from the hook; the motion does not.

    uv run python scripts/probes/added_mass_check.py --table runs/s12/flight/robot/level2.npz --level 2
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import matplotlib
import mujoco as mj
import numpy as np

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "src"))
sys.path.insert(0, str(Path(__file__).resolve().parent))
from build_measured_kinematics import open_wing_ranges, robot_level  # noqa: E402
from flyemu import flight  # noqa: E402
from flyemu.body import Body  # noqa: E402


def model_trace(table: str, dt_ms: float, beats: int):
    b = Body(vision=False, timestep=dt_ms / 1000.0, spawn_height=5.0)
    m, d = b.sim.mj_model, b.sim.mj_data
    open_wing_ranges(b)
    z = np.load(table)
    tabs = [flight.TableKinematics(z["phase"], z[k], float(z["f_hz"])) for k in ("q_l", "q_r")]
    pitch = float(z["body_pitch_deg"])
    wb = flight.WingBeat(b, tabs[0], ramp_ms=0.0)
    wb.power[:] = 1.0
    b.passive_hooks = [wb]
    be = flight.apply_blade_element(b, length_mm=2.99, area_mm2=2.831, planform="hydei", added_mass=True)
    mj.mj_forward(m, d)
    qp, qn = np.zeros(4), np.zeros(4)
    mj.mju_axisAngle2Quat(qp, np.array([0.0, -1.0, 0.0]), np.radians(pitch))
    mj.mju_mulQuat(qn, qp, d.qpos[3:7].copy()); d.qpos[3:7] = qn
    mj.mj_forward(m, d)
    q0 = d.qpos[:7].copy()
    f = float(z["f_hz"])
    per = int(round(1000.0 / f / dt_ms))
    rec = []
    for _ in range(per * beats):
        (tq, tqd), (rq, rqd) = (t.targets(wb.t_s) for t in tabs)
        d.qpos[wb.q_adr] = np.r_[tq, rq]; d.qvel[wb.v_adr] = np.r_[tqd, rqd]
        ph = wb.t_s * f % 1.0
        b.step()
        rec.append([ph, *be.parts[0, 3]])
        d.qpos[:7] = q0; d.qvel[:6] = 0.0
    jp = m.jnt_pos[mj.mj_name2id(m, mj.mjtObj.mjOBJ_JOINT, f"{b.fly.name}/c_thorax-l_wing-{flight.FN['rotation']}")]
    r = (be.pts[0] - jp) @ be.span[0]
    return np.array(rec[-per:]), be, r, pitch, f, float(m.opt.density)


def independent(level: int, be, r, f_hz: float, rho: float, n: int = 4000):
    from scipy.interpolate import CubicSpline
    p0, *ang, _, _, _ = robot_level(level, n=100)                 # the samples the model's table was fitted to
    A = np.vstack([np.array(ang).T, np.array(ang).T[:1]])
    sp = CubicSpline(np.append(p0, 1.0), A, bc_type="periodic", axis=0)   # as flight.TableKinematics
    ph = np.arange(n) / n
    phi, dev, rot = sp(ph).T
    c, dr, x0 = be.c[0], be.dr[0], be.x0[0]
    S, LE = zip(*(flight.stroke_frame_vectors(phi[i], dev[i], rot[i], "l") for i in range(n)))
    S, LE = np.array(S), np.array(LE)
    N = np.cross(S, LE)
    M = r[None, :, None] * S[:, None, :] - ((0.5 - x0) * c)[None, :, None] * LE[:, None, :]   # (n, strips, 3)
    dt = 1.0 / (f_hz * n)
    V = (np.roll(M, -1, 0) - np.roll(M, 1, 0)) / (2 * dt)
    vn = np.einsum("nsk,nk->ns", V, N)
    an = (np.roll(vn, -1, 0) - np.roll(vn, 1, 0)) / (2 * dt)
    F = -(rho * np.pi / 4 * c ** 2 * dr * an).sum(1)[:, None] * N                          # thorax frame
    return ph, F


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--table", default=str(REPO / "runs/s12/flight/robot/level2.npz"))
    ap.add_argument("--level", type=int, default=2)
    ap.add_argument("--dt-ms", type=float, default=0.05)
    ap.add_argument("--beats", type=int, default=4)
    ap.add_argument("--out", default=str(REPO / "runs/s12/flight/added_mass"))
    a = ap.parse_args()
    tr, be, r, pitch, f, rho = model_trace(a.table, a.dt_ms, a.beats)
    ph, Fth = independent(a.level, be, r, f, rho)
    th = np.radians(pitch)
    Rw = np.array([[np.cos(th), 0, -np.sin(th)], [0, 1, 0], [np.sin(th), 0, np.cos(th)]])   # thorax -> world (nose up about -y)
    Fw = Fth @ Rw.T
    o = np.argsort(tr[:, 0])
    mod = tr[o]
    ind = np.array([np.interp(mod[:, 0], ph, Fw[:, k], period=1.0) for k in range(3)]).T
    res = {"level": a.level, "f_hz": f, "body_pitch_deg": pitch, "dt_ms": a.dt_ms}
    for k, ax in enumerate("xyz"):
        res[f"F{ax}"] = {"corr": round(float(np.corrcoef(mod[:, 1 + k], ind[:, k])[0, 1]), 4),
                         "rms_model_over_independent": round(float(np.sqrt((mod[:, 1 + k] ** 2).mean() / (ind[:, k] ** 2).mean())), 4),
                         "mean_model_uN": round(float(mod[:, 1 + k].mean()), 4),
                         "mean_independent_uN": round(float(Fw[:, k].mean()), 4),
                         "peak_abs_model_uN": round(float(np.abs(mod[:, 1 + k]).max()), 3)}
    print(json.dumps(res, indent=1))
    out = Path(a.out); out.mkdir(parents=True, exist_ok=True)
    (out / f"added_mass_check_level{a.level}.json").write_text(json.dumps(res, indent=1))
    fig, axs = plt.subplots(3, 1, figsize=(8, 7), sharex=True)
    for k, ax in enumerate("xyz"):
        axs[k].plot(mod[:, 0], mod[:, 1 + k], "k", label="model hook (one-step backward difference)")
        axs[k].plot(ph, Fw[:, k], "r--", label="independent, stroke-frame angles")
        axs[k].set_ylabel(f"left wing F{ax} world (uN)")
    axs[0].legend(fontsize=8); axs[2].set_xlabel("wingbeat phase")
    fig.suptitle(f"Added-mass force, robot level {a.level}")
    fig.tight_layout(); fig.savefig(out / f"added_mass_check_level{a.level}.png", dpi=110)


if __name__ == "__main__":
    main()
