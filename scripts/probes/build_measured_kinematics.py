"""Session 12 B (F-FLIGHT-3, pre-registered test DECISIONS s12 19:08): turn the
measured steady-flight wing kinematics of Muijres et al. 2014 (Science 344:172,
Table S1 Fourier fits, D. hydei; data/derived/muijres2014_hover_kinematics.csv)
into model hinge angles per phase, for hover_blade_trace.py --table.

Conventions (inferred; DECISIONS s12 19:08, "Kinematics fixed before the run"):
stroke plane tilted 47.5 deg nose-up from the body axis; phi positive = posterior;
deviation positive toward the stroke-plane normal; alpha = 0 with the chord normal
to the stroke plane (leading edge up), positive = leading edge toward anterior.
Thorax frame: x head, y left, z up. Span and leading-edge vectors are built in the
thorax frame and fitted with flight.wing_pose_ik (bounded by the joint ranges).

    uv run python scripts/probes/build_measured_kinematics.py [--f-hz 218] [--out runs/s12/flight/muijres2014_hover.npz]
    uv run python scripts/probes/build_measured_kinematics.py --robot-level 12 --out runs/s12/flight/robot_level12.npz

--robot-level k takes instead the k-th beat (0-12) of Database S1's
robotForcesTorques.ForceModulations (F/mg 0.85-1.76, built by the authors from the
measured kinematic change per unit force, SM eq. S3) at its own frequency (the robot
time base: 182.4-220.0 Hz). The robot's steady beat is Table S1 with stroke and
rotation negated (checked, DECISIONS s12 20:31); that map is applied to every level.

--robot-roll k takes the k-th beat (0-12) of RollModulations (roll acceleration
-0.72 to 3.61 deg per beat^2; per-side angles, same map, steady frequency) for the
roll-torque test (DECISIONS s12 20:5x). --roll-part stroke|deviation|rotation keeps
only that angle's change from the steady beat (level 2), as the robot's
Mx_norm_<part> series; the other two angles stay at the steady beat.

--robot-pitch k takes the k-th beat (0-20) of PitchModulations (symmetric kinematics
built from the flies' measured change per unit pitch acceleration; same sign map,
steady frequency) for the held-out pitch-torque check (DECISIONS s12 22:08).
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "src"))
from flyemu import flight  # noqa: E402
from flyemu.body import Body  # noqa: E402

SRC = REPO / "data/derived/muijres2014_hover_kinematics.csv"     # copy of data/raw/flight_kinematics/hover_kinematics_muijres2014.csv
DB = REPO / "data/raw/flight_kinematics/muijres2014/FRUITFLY_LOOMINGRESPONSE_DATABASE.mat"


def robot_level(k: int, n: int = 100) -> tuple[np.ndarray, ...]:
    """(phase, stroke, deviation, rotation in this project's convention (deg), f_hz,
    F/mg target, robot mean vertical force / weight) for force-modulation level k."""
    import scipy.io as sio
    fm = sio.loadmat(DB, squeeze_me=True, struct_as_record=False)["robotForcesTorques"].ForceModulations
    t = np.asarray(fm.t_NOfreq, float)
    T = t[-1] + (t[1] - t[0])
    ti = np.asarray(fm.t_INCfreq, float)[:, k]
    f_hz = 1.0 / (np.nanmax(ti) + (ti[1] - ti[0]))
    ph = np.arange(n) / n
    ang = [np.interp(ph, t / T, np.asarray(getattr(fm, c), float)[:, k], period=1.0)
           for c in ("stroke", "deviation", "rotation")]
    fz = -float(np.nanmean(np.asarray(fm.Fz_norm_all, float)[:, k]))     # robot z points down
    return ph, -ang[0], ang[1], -ang[2], float(f_hz), float(np.asarray(fm.force_norm)[k]), fz


def robot_roll(k: int, part: str = "all", n: int = 100) -> tuple[np.ndarray, dict, float, dict]:
    """(phase, {side: (stroke, deviation, rotation)} in this project's convention (deg),
    f_hz, robot mean forces/torques {Fx..Mz: value}) for roll-modulation level k."""
    import scipy.io as sio
    rm = sio.loadmat(DB, squeeze_me=True, struct_as_record=False)["robotForcesTorques"].RollModulations
    t = np.asarray(rm.t, float)
    T = t[-1] + (t[1] - t[0])
    ph = np.arange(n) / n
    ang = {}
    for side, S in (("l", "L"), ("r", "R")):
        a3 = []
        for c in ("stroke", "deviation", "rotation"):
            col = np.asarray(getattr(rm, f"{c}_{S}"), float)
            x = col[:, k] if part in ("all", c) else col[:, 2]
            a3.append(np.interp(ph, t / T, x, period=1.0))
        ang[side] = (-a3[0], a3[1], -a3[2])
    ref = {c: float(np.nanmean(np.asarray(getattr(rm, f"{c}_norm_{part}"), float)[:, k]))
           for c in ("Fx", "Fy", "Fz", "Mx", "My", "Mz")}
    ref["roll_accel_norm"] = float(np.asarray(rm.roll_accel_norm)[k])
    return ph, ang, 1.0 / T, ref


def robot_pitch(k: int, n: int = 100) -> tuple[np.ndarray, tuple, float, dict]:
    """(phase, (stroke, deviation, rotation) in this project's convention (deg), f_hz,
    robot mean forces/torques {Fx..Mz: value}) for pitch-modulation level k."""
    import scipy.io as sio
    pm = sio.loadmat(DB, squeeze_me=True, struct_as_record=False)["robotForcesTorques"].PitchModulations
    t = np.asarray(pm.t, float)
    T = t[-1] + (t[1] - t[0])
    ph = np.arange(n) / n
    a3 = [np.interp(ph, t / T, np.asarray(getattr(pm, c), float)[:, k], period=1.0)
          for c in ("stroke", "deviation", "rotation")]
    ref = {c: float(np.nanmean(np.asarray(getattr(pm, f"{c}_norm_all"), float)[:, k]))
           for c in ("Fx", "Fy", "Fz", "Mx", "My", "Mz")}
    ref["pitch_accel_norm"] = float(np.asarray(pm.pitch_accel_norm)[k])
    return ph, (-a3[0], a3[1], -a3[2]), 1.0 / T, ref


open_wing_ranges = flight.open_wing_ranges


def wing_vectors(phi, dev, alpha, side: str, tilt_deg: float = flight.STROKE_PLANE_DEG):
    """Unit span and leading-edge vectors (thorax frame) for one wing pose (deg)."""
    return flight.stroke_frame_vectors(phi, dev, alpha, side, tilt_deg)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--f-hz", type=float, default=218.0, help="Fry et al. 2005 D. melanogaster free flight (measured)")
    ap.add_argument("--body-pitch", type=float, default=47.6, help="Muijres 2014 steady flight (measured)")
    ap.add_argument("--out", default=str(REPO / "runs/s12/flight/muijres2014_hover.npz"))
    ap.add_argument("--robot-level", type=int, default=None, help="Database S1 force-modulation beat 0-12")
    ap.add_argument("--robot-roll", type=int, default=None, help="Database S1 roll-modulation beat 0-12")
    ap.add_argument("--roll-part", default="all", choices=("all", "stroke", "deviation", "rotation"))
    ap.add_argument("--robot-pitch", type=int, default=None, help="Database S1 pitch-modulation beat 0-20")
    a = ap.parse_args()
    extra, sides = {}, None
    if a.robot_roll is not None:
        ph, sides, a.f_hz, ref = robot_roll(a.robot_roll, a.roll_part)
        extra = dict(robot_roll=a.robot_roll, roll_part=a.roll_part,
                     **{f"robot_{c}": v for c, v in ref.items()})
    elif a.robot_pitch is not None:
        ph, ang3, a.f_hz, ref = robot_pitch(a.robot_pitch)
        sides = {sd: ang3 for sd in ("l", "r")}
        extra = dict(robot_pitch=a.robot_pitch, **{f"robot_{c}": v for c, v in ref.items()})
    elif a.robot_level is not None:
        ph, phi, dev, rot, a.f_hz, fmg, fz = robot_level(a.robot_level)
        extra = dict(robot_level=a.robot_level, fly_force_over_weight=fmg, robot_vertical_over_weight=fz)
    else:
        import pandas as pd
        t = pd.read_csv(SRC, comment="#")
        ph, phi, dev, rot = (t[c].to_numpy(float) for c in ("phase", "stroke_deg", "deviation_deg", "rotation_deg"))
        if ph[-1] >= 1.0:
            ph, phi, dev, rot = ph[:-1], phi[:-1], dev[:-1], rot[:-1]
    body = Body(vision=False)
    open_wing_ranges(body)          # WING_RANGE_DEG holds a crossed-wing stroke (F-WING-3); fit unbounded
    res, errs = {}, {}
    if sides is None:
        sides = {sd: (phi, dev, rot) for sd in ("l", "r")}
    for side in ("l", "r"):
        qs, es, q0 = [], [], None
        sphi, sdev, srot = sides[side]
        for i in range(len(ph)):
            s, le = wing_vectors(sphi[i], sdev[i], srot[i], side)
            q, e = flight.wing_pose_ik(body, side, s, le, q_start=q0)
            qs.append(q); es.append(e); q0 = q
        res[side], errs[side] = np.array(qs), np.array(es)
    out = Path(a.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    np.savez(out, phase=ph, q_l=res["l"], q_r=res["r"], f_hz=a.f_hz, body_pitch_deg=a.body_pitch,
             err_l_deg=errs["l"], err_r_deg=errs["r"], **extra)
    summ = {"out": str(out), "n": int(len(ph)), "f_hz": a.f_hz, "body_pitch_deg": a.body_pitch, **extra,
            "max_pose_err_deg": {k: round(float(v.max()), 2) for k, v in errs.items()},
            "hinge_range_deg": {k: {fn: [round(float(np.degrees(v[:, i]).min()), 1), round(float(np.degrees(v[:, i]).max()), 1)]
                                    for i, fn in enumerate(("stroke", "deviation", "rotation"))} for k, v in res.items()}}
    print(json.dumps(summ, indent=1))


if __name__ == "__main__":
    main()
