"""Tethered-flight lift test (task 8: 'lift ~ weight at a nominal hover stroke').

The thorax is held fixed (root reset each step); the wingbeat generator (B10)
imposes hover kinematics; mean vertical aerodynamic force over whole wingbeats
(generalised fluid force on the root translation DOFs = sum over bodies) is
compared with the fly's weight. Checks MuJoCo warnings.

    uv run python scripts/probes/tethered_lift.py [--dt-ms 0.05] [--beats 10] [--rot-sign 1]
"""
import argparse
import json
import sys

import mujoco as mj
import numpy as np

sys.path.insert(0, "src")
from flyemu import flight  # noqa: E402
from flyemu.body import Body  # noqa: E402


def run(dt_ms=0.05, beats=10, rot_sign=1.0, amp=70.0, f=218.0, rot_amp=45.0, dev=8.0, kinematic=False, bw=1500.0,
        kutta=None):
    b = Body(vision=False, timestep=dt_ms / 1000.0, spawn_height=5.0)
    m, d = b.sim.mj_model, b.sim.mj_data
    flight.apply_wing_ranges(b)
    if kutta is not None:            # F-FLIGHT-2: membrane-only aero with this lift coefficient
        flight.apply_aero(b, kutta)
    kin = flight.WingKinematics(f_hz=f, stroke_amp_deg=amp, rot_sign=rot_sign, rot_amp_deg=rot_amp,
                                dev_amp_deg=dev)
    wb = flight.WingBeat(b, kin, bandwidth_hz=bw, ramp_ms=0.0)
    wb.power[:] = 1.0
    b.passive_hooks = [wb]
    mj.mj_forward(m, d)
    q0, n = d.qpos[:7].copy(), int(round(beats * 1000.0 / f / dt_ms))
    # start the wings on the generator's trajectory
    q, _ = kin.targets(0.0)
    d.qpos[wb.q_adr] = np.tile(q, 2)
    fz, fx, err = [], [], []
    for k in range(n):
        if kinematic:     # exact imposed kinematics (aerodynamics test only)
            tq, tqd = kin.targets(wb.t_s)
            d.qpos[wb.q_adr] = np.tile(tq, 2); d.qvel[wb.v_adr] = np.tile(tqd, 2)
        b.step()
        d.qpos[:7] = q0; d.qvel[:6] = 0.0
        fz.append(d.qfrc_fluid[2]); fx.append(d.qfrc_fluid[0])
        tq, _ = kin.targets(wb.t_s)
        err.append(np.degrees(np.abs(d.qpos[wb.q_adr[:3]] - tq)).max())
    warn = int(sum(w.number for w in d.warning))
    per = int(round(1000.0 / f / dt_ms))
    last = slice(n - per * (beats // 2), n)      # second half, whole beats
    weight = mj.mj_getTotalmass(m) * 9810.0     # uN
    return dict(kinematic=kinematic, bandwidth_hz=bw, dt_ms=dt_ms, f_hz=f, stroke_amp_deg=amp, rot_sign=rot_sign, rot_amp_deg=rot_amp,
                lift_uN=float(np.mean(fz[last])), thrust_x_uN=float(np.mean(fx[last])),
                weight_uN=weight, lift_over_weight=float(np.mean(fz[last]) / weight),
                track_err_deg_p95=float(np.percentile(err[per:], 95)), mujoco_warnings=warn)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--dt-ms", type=float, default=0.05)
    ap.add_argument("--beats", type=int, default=10)
    ap.add_argument("--rot-sign", type=float, default=1.0)
    ap.add_argument("--amp", type=float, default=70.0)
    ap.add_argument("--rot-amp", type=float, default=45.0)
    ap.add_argument("--kinematic", action="store_true")
    ap.add_argument("--bw", type=float, default=1500.0)
    ap.add_argument("--kutta", type=float, default=None, help="membrane-only aero with this Kutta coefficient")
    a = ap.parse_args()
    print(json.dumps(run(a.dt_ms, a.beats, a.rot_sign, a.amp, rot_amp=a.rot_amp, kinematic=a.kinematic, bw=a.bw, kutta=a.kutta)))
