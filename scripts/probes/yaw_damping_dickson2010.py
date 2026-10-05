"""Session 12 (F-FLIGHT-3, held-out; pre-registered DECISIONS s12 22:40): the
blade-element wing against the measured yaw damping and yaw actuation of a
dynamically scaled D. melanogaster wing pair (Dickson, Polidoro, Tanner & Dickinson
2010 J Exp Biol 213:3047; open, data/raw/flight_kinematics/dickson2010/).

Robot (measured): melanogaster planform, R 0.23 m, mean chord c 0.065 m, wing
rotation axes 0.11 m apart, Re about 100, horizontal stroke plane, yaw axis vertical
midway between the wing joints. Baseline kinematics (their eqs 1-3): stroke
phi = phi0 asin(k_phi cos 2 pi f t) / asin(k_phi), phi0 70 deg, k_phi 0.01; deviation
0; rotation alpha = alpha0 tanh(k_a sin 2 pi f t) / tanh(k_a), alpha0 45 deg (chord
from the stroke-plane normal), k_a 1.5. Stroke-averaged yaw torque tau* = tau /
(rho c^5 f^2) against omega* = omega / f is linear with slope C*_omega = -6.4e2
(under 5% spread over trials). Actuation slopes (their Table 3, tau* per unit
parameter): differential angle of attack pa 3.1e3, deviation pd 1.3e3, stroke-plane
rotation pr 1.3e3, velocity pv 3.4e3 (eqs 4, 5, 6-8, 9-10).

Model: the same angles in this project's stroke frame (flight.stroke_frame_vectors:
phi positive posterior; alpha positive = leading edge anterior, so alpha > 0 while
the wing moves anterior and the plate lifts), fitted to hinge angles
(flight.wing_pose_ik, open ranges as for the robot tables); pr as a rigid rotation of
each wing's pose about the thorax's lateral axis (+pr left, -pr right). Thorax
pitched 47.5 deg nose-up so the stroke plane is horizontal, then turned at constant
omega about the vertical through the hinge midpoint; torque about that axis from the
wing forces only. Chords rescaled so c/R equals the robot's (0.065/0.23) with the
scan's length and ellipse shape; tau* uses the model's own c.

The robot's sign conventions for the deformation parameters relative to this frame
are not established, so actuation is scored on magnitude.

    uv run python scripts/probes/yaw_damping_dickson2010.py --out runs/s12/flight/dickson2010
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
from flyemu import flight  # noqa: E402
from flyemu.body import Body  # noqa: E402

PHI0, K_PHI, A0, K_A = 70.0, 0.01, 45.0, 1.5             # Dickson 2010 baseline (measured protocol)
ROBOT = {"R_m": 0.23, "c_m": 0.065, "hinge_sep_m": 0.11, "C_omega": -6.4e2,
         "slope": {"pa": 3.1e3, "pd": 1.3e3, "pr": 1.3e3, "pv": 3.4e3}}
LEVELS = {"omega": [-0.73, -0.365, 0.0, 0.365, 0.73],   # robot's -7..7 deg/s at 0.167 Hz
          "pa": [-0.17, -0.087, 0.087, 0.17], "pd": [-0.17, -0.087, 0.087, 0.17],
          "pr": [-0.17, -0.087, 0.087, 0.17], "pv": [-0.066, -0.033, 0.033, 0.066]}   # their Figs 7-8


def baseline(ph):
    phi = PHI0 * np.arcsin(K_PHI * np.cos(2 * np.pi * ph)) / np.arcsin(K_PHI)
    return phi, np.zeros_like(ph), A0 * np.tanh(K_A * np.sin(2 * np.pi * ph)) / np.tanh(K_A)


def angles(ph, mode: str, p: float, side: str):
    """Stroke, deviation, rotation (deg) of one wing under one deformation mode."""
    s = 1.0 if side == "l" else -1.0
    phi, dev, al = baseline(ph)
    if mode == "pa":                                  # eq 4
        al = al + s * np.degrees(p)
    elif mode == "pd":                                # eq 5
        dev = dev - s * np.degrees(p) * np.cos(2 * np.pi * ph)
    elif mode == "pv":                                # eqs 9-10: stroke position only, time warped
        q = s * p
        phi = baseline(np.where(ph < 0.5 * (1 - q), ph / (1 - q), (ph + q) / (1 + q)))[0]
    return phi, dev, al


def table(body, mode: str, p: float, n: int = 100) -> dict:
    ph = np.arange(n) / n
    out = {"phase": ph}
    for side in ("l", "r"):
        phi, dev, al = angles(ph, mode, p, side)
        ang = p if side == "l" else -p                 # pr (rad): left +, right -
        Ry = np.array([[np.cos(ang), 0, np.sin(ang)], [0, 1, 0], [-np.sin(ang), 0, np.cos(ang)]])
        qs, es, q0 = [], [], None
        for i in range(n):
            sp, le = flight.stroke_frame_vectors(phi[i], dev[i], al[i], side)
            if mode == "pr":                          # rigid stroke-plane tilt about the lateral axis
                sp, le = Ry @ sp, Ry @ le
            q, e = flight.wing_pose_ik(body, side, sp, le, q_start=q0)
            qs.append(q); es.append(e); q0 = q
        out[f"q_{side}"], out[f"err_{side}"] = np.array(qs), np.array(es)
    return out


def run(tab: dict, f_hz: float, omega_star: float, area: float, added_mass: bool,
        dt_ms: float, beats: int, avg_beats: int) -> dict:
    b = Body(vision=False, timestep=dt_ms / 1000.0, spawn_height=5.0)
    m, d = b.sim.mj_model, b.sim.mj_data
    flight.open_wing_ranges(b)
    tabs = [flight.TableKinematics(tab["phase"], tab[k], f_hz) for k in ("q_l", "q_r")]
    wb = flight.WingBeat(b, tabs[0], ramp_ms=0.0)
    wb.power[:] = 1.0
    b.passive_hooks = [wb]
    be = flight.apply_blade_element(b, area_mm2=area, added_mass=added_mass)
    mj.mj_forward(m, d)
    qp, qn = np.zeros(4), np.zeros(4)
    mj.mju_axisAngle2Quat(qp, np.array([0.0, -1.0, 0.0]), np.radians(flight.STROKE_PLANE_DEG))
    mj.mju_mulQuat(qn, qp, d.qpos[3:7].copy()); d.qpos[3:7] = qn
    mj.mj_forward(m, d)
    th_id = be.thorax
    n_world = d.xmat[th_id].reshape(3, 3) @ be.n_stroke
    O = 0.5 * (d.xpos[be.bid[0]] + d.xpos[be.bid[1]])
    hinge_half = 0.5 * np.linalg.norm(d.xpos[be.bid[0]] - d.xpos[be.bid[1]])
    p0, quat0 = d.qpos[:3].copy(), d.qpos[3:7].copy()
    om = omega_star * f_hz
    per = int(round(1000.0 / f_hz / dt_ms))
    rec = []
    qz, qq, Rm = np.zeros(4), np.zeros(4), np.zeros(9)
    for i in range(per * beats):
        th = om * i * dt_ms / 1000.0
        mj.mju_axisAngle2Quat(qz, np.array([0.0, 0.0, 1.0]), th)
        mj.mju_mulQuat(qq, qz, quat0)
        c, s = np.cos(th), np.sin(th)
        p = O + np.array([[c, -s, 0], [s, c, 0], [0, 0, 1]]) @ (p0 - O)
        d.qpos[:3], d.qpos[3:7] = p, qq
        mj.mju_quat2Mat(Rm, qq)
        d.qvel[:3] = om * np.cross([0.0, 0.0, 1.0], p - O)
        d.qvel[3:6] = Rm.reshape(3, 3).T @ np.array([0.0, 0.0, om])
        (tq, tqd), (rq, rqd) = (t.targets(wb.t_s) for t in tabs)
        d.qpos[wb.q_adr] = np.r_[tq, rq]; d.qvel[wb.v_adr] = np.r_[tqd, rqd]
        b.step()
        F = sum(d.xfrc_applied[bb, :3] for bb in be.bid)
        M = sum(d.xfrc_applied[bb, 3:] + np.cross(d.xipos[bb] - O, d.xfrc_applied[bb, :3]) for bb in be.bid)
        rec.append(np.r_[F, M])
    r = np.array(rec[-per * avg_beats:])
    rho = float(m.opt.density)
    cbar = float((be.c[0] * be.dr[0]).sum()) / tip_radius(be)
    scale = rho * cbar ** 5 * f_hz ** 2
    mean = r.mean(0)
    return {"omega_star": omega_star, "tau_star": float(mean[5] / scale), "Fz_over_scale": float(mean[2] / scale),
            "Fz_uN": float(mean[2]), "Mz_uN_mm": float(mean[5]), "cbar_mm": cbar, "R_mm": tip_radius(be),
            "hinge_offset_over_R": float(hinge_half / tip_radius(be)), "stroke_normal_world": n_world.round(4).tolist(),
            "per_beat_tau_star": [float(x) for x in np.array(rec[-per * avg_beats:])[:, 5].reshape(avg_beats, per).mean(1) / scale],
            "steps_per_beat": per}


def tip_radius(be) -> float:
    """Hinge (wing body origin) to the outer edge of the last strip along the span (model mm)."""
    r = be.pts[0] @ be.span[0]
    return float(r[-1] + be.dr[0] / 2)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=str(REPO / "runs/s12/flight/dickson2010"))
    ap.add_argument("--f-hz", type=float, default=200.0, help="any; tau* and omega* are scaled by f")
    ap.add_argument("--dt-ms", type=float, default=0.05)
    ap.add_argument("--beats", type=int, default=6)
    ap.add_argument("--avg-beats", type=int, default=3)
    ap.add_argument("--no-added-mass", action="store_true")
    ap.add_argument("--modes", default="omega,pa,pd,pr,pv")
    ap.add_argument("--geometry-only", action="store_true")
    a = ap.parse_args()
    out = Path(a.out); out.mkdir(parents=True, exist_ok=True)
    b0 = Body(vision=False)
    flight.open_wing_ranges(b0)
    be0 = flight.BladeElementWing(b0)
    R = tip_radius(be0)
    area = R * R * ROBOT["c_m"] / ROBOT["R_m"]
    geo = {"R_mm": R, "area_scan_mm2": float((be0.c[0] * be0.dr[0]).sum()), "area_robot_ratio_mm2": area,
           "cbar_over_R_scan": float((be0.c[0] * be0.dr[0]).sum()) / R ** 2, "cbar_over_R_robot": ROBOT["c_m"] / ROBOT["R_m"],
           "x0_pitch_axis_chord_fraction": be0.x0[0], "robot_hinge_offset_over_R": ROBOT["hinge_sep_m"] / 2 / ROBOT["R_m"]}
    print(json.dumps(geo))
    if a.geometry_only:
        return
    res = {"geometry": geo, "added_mass": not a.no_added_mass, "f_hz": a.f_hz, "dt_ms": a.dt_ms,
           "beats": a.beats, "avg_beats": a.avg_beats, "robot": ROBOT, "runs": {}}
    for mode in a.modes.split(","):
        rows = []
        for v in LEVELS[mode] if mode == "omega" else [0.0] + LEVELS[mode]:
            if mode == "omega":
                tab = table(b0, "base", 0.0)
                row = run(tab, a.f_hz, v, area, not a.no_added_mass, a.dt_ms, a.beats, a.avg_beats)
            else:
                tab = table(b0, mode, v)
                row = run(tab, a.f_hz, 0.0, area, not a.no_added_mass, a.dt_ms, a.beats, a.avg_beats)
            row["param"] = v
            row["max_pose_err_deg"] = float(max(tab["err_l"].max(), tab["err_r"].max()))
            rows.append(row)
            print(mode, v, round(row["tau_star"], 2), "Fz*", round(row["Fz_over_scale"], 1), "err", round(row["max_pose_err_deg"], 2), flush=True)
        x = np.array([r_["omega_star" if mode == "omega" else "param"] for r_ in rows])
        y = np.array([r_["tau_star"] for r_ in rows])
        A = np.column_stack([x, np.ones_like(x)])
        (k, c0), *_ = np.linalg.lstsq(A, y, rcond=None)
        r2 = 1 - ((y - A @ [k, c0]) ** 2).sum() / max(((y - y.mean()) ** 2).sum(), 1e-30)
        ref = ROBOT["C_omega"] if mode == "omega" else ROBOT["slope"][mode]
        res["runs"][mode] = {"rows": rows, "slope": float(k), "intercept": float(c0), "r2": float(r2),
                             "robot_slope": ref, "ratio": float(k / ref), "abs_ratio": float(abs(k / ref))}
        print(mode, "slope", round(k, 1), "robot", ref, "ratio", round(k / ref, 3), "r2", round(r2, 4), flush=True)
    tag = "_noam" if a.no_added_mass else ""
    (out / f"dickson2010{tag}.json").write_text(json.dumps(res, indent=1))
    modes = list(res["runs"])
    fig, axs = plt.subplots(1, len(modes), figsize=(3.4 * len(modes), 3.4))
    for ax, mode in zip(np.atleast_1d(axs), modes):
        rr = res["runs"][mode]
        x = np.array([r_["omega_star" if mode == "omega" else "param"] for r_ in rr["rows"]])
        y = np.array([r_["tau_star"] for r_ in rr["rows"]])
        xs = np.linspace(x.min(), x.max(), 3)
        ax.plot(x, y, "C3s", label=f"model, slope {rr['slope']:.0f}")
        ax.plot(xs, rr["robot_slope"] * xs + rr["intercept"], "k-", label=f"robot slope {rr['robot_slope']:.0f}")
        if mode != "omega":
            ax.plot(xs, -rr["robot_slope"] * xs + rr["intercept"], "k:", alpha=0.5, label="robot slope, other sign")
        ax.set_xlabel("omega* = omega/f" if mode == "omega" else mode)
        ax.set_title(f"{mode}: |ratio| {rr['abs_ratio']:.2f}", fontsize=9)
        ax.legend(fontsize=6)
    np.atleast_1d(axs)[0].set_ylabel("stroke-averaged yaw torque / (rho c^5 f^2)")
    fig.suptitle(f"Blade-element wing vs Dickson et al. 2010 robot (melanogaster wing, Re 100), added mass {'on' if res['added_mass'] else 'off'}", fontsize=9)
    fig.tight_layout(); fig.savefig(out / f"dickson2010{tag}.png", dpi=110)


if __name__ == "__main__":
    main()
