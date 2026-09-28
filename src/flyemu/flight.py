"""Flight apparatus (task 8, session 10): B10 wingbeat generator, wing ranges by
function, B13 haltere beat and Coriolis proxy.

Wing DOFs by function (F-WING-1, measured on the model geometry at flybody's
spread pose): `wing-yaw` sweeps the wing fore-aft (stroke), `wing-roll` moves it
up-down (deviation), `wing-pitch` turns it about its span (rotation). joints.py
labels them pitch = stroke, yaw = deviation, roll = rotation (wrong for flybody).

B10 abstraction (declared): the asynchronous power muscles and the thoracic
resonance form a self-excited oscillator; it is represented by a wingbeat
generator that sets target stroke/deviation/rotation angles each step,

    stroke(t)    = s0 + A cos(2 pi f t)
    deviation(t) = d0 + D sin(4 pi f t)                      (figure-of-eight)
    rotation(t)  = r0 + R tanh(k sin(2 pi f t)) / tanh(k)     (flips at reversal)

tracked by a stiff PD torque on the wing hinges (a thorax that imposes wing
kinematics, not a controller of the fly's). A and f are set by the power-muscle
drive level P in [0, 1] (DLM/DVM MN activity): A = P A_max, f = f0; P = 0 is no
beat and the passive (folded) wing. Steering-muscle MNs (B11) will modulate
per-wing parameters (phenomenological map, not yet built). Validity: hover-like
kinematics; quasi-steady aerodynamics (body.py) only.
"""
from __future__ import annotations

from dataclasses import dataclass

import mujoco as mj
import numpy as np

SIDES = ("l", "r")
FN = {"stroke": "yaw", "deviation": "roll", "rotation": "pitch"}

# Wing envelopes by function (deg, flybody coordinates; folded pose = 0,
# flybody spread pose = yaw 86 / roll 40 / pitch -57). Assumed: sized to hold
# the folded pose, the spread pose and a 140 +- 10 deg hovering stroke
# (Fry, Sayaman & Dickinson 2005 JEB 208:2303) around it.
WING_RANGE_DEG = {"yaw": (-10.0, 175.0), "roll": (-30.0, 70.0), "pitch": (-130.0, 40.0)}


def apply_wing_ranges(body) -> list[str]:
    m = body.sim.mj_model
    done = []
    for j in range(m.njnt):
        n = m.joint(j).name
        for ax, (lo, hi) in WING_RANGE_DEG.items():
            if n.endswith(f"_wing-{ax}"):
                m.jnt_range[j] = np.radians([lo, hi])
                m.jnt_limited[j] = 1
                done.append(n)
    return done


@dataclass
class WingKinematics:
    f_hz: float = 218.0            # Fry et al. 2005 hover ~ 218 Hz (lead, not read)
    stroke_mean_deg: float = 86.0  # flybody spread-pose yaw (guessed as stroke centre)
    stroke_amp_deg: float = 70.0   # half of the ~140 deg peak-to-peak (Fry 2005, via joints.py)
    dev_mean_deg: float = 40.0
    dev_amp_deg: float = 8.0       # ~ 25 deg p-p deviation is the upper envelope (guessed smaller)
    rot_mean_deg: float = -57.0
    rot_amp_deg: float = 45.0      # mid-stroke angle of attack ~ 45 deg (guessed)
    rot_sharp: float = 3.0         # rotation flip sharpness (guessed)
    rot_sign: float = 1.0          # set by the lift calibration (derived)

    def targets(self, t_s: float, power: float = 1.0) -> tuple[np.ndarray, np.ndarray]:
        """(q, qdot) targets in rad for (stroke, deviation, rotation) of one wing."""
        w = 2 * np.pi * self.f_hz
        ph = w * t_s
        A = np.radians(self.stroke_amp_deg) * power
        D = np.radians(self.dev_amp_deg) * power
        R = np.radians(self.rot_amp_deg) * power * self.rot_sign
        k = self.rot_sharp
        s = np.sin(ph)
        q = np.array([np.radians(self.stroke_mean_deg) + A * np.cos(ph),
                      np.radians(self.dev_mean_deg) + D * np.sin(2 * ph),
                      np.radians(self.rot_mean_deg) + R * np.tanh(k * s) / np.tanh(k)])
        qd = np.array([-A * w * s, 2 * D * w * np.cos(2 * ph),
                       R * k * w * np.cos(ph) / np.cosh(k * s) ** 2 / np.tanh(k)])
        return q, qd


class WingBeat:
    """B10 hook: writes PD torques on the six wing hinges to impose the
    generator's kinematics (body.passive_hooks). power: per-wing drive in [0, 1]."""

    def __init__(self, body, kin: WingKinematics | None = None, bandwidth_hz: float = 1500.0,
                 zeta: float = 0.7):
        m = body.sim.mj_model
        self.kin = kin or WingKinematics()
        self.q_adr, self.v_adr = [], []
        for s in SIDES:
            for fn in ("stroke", "deviation", "rotation"):
                j = mj.mj_name2id(m, mj.mjtObj.mjOBJ_JOINT, f"{body.fly.name}/c_thorax-{s}_wing-{FN[fn]}")
                self.q_adr.append(m.jnt_qposadr[j]); self.v_adr.append(m.jnt_dofadr[j])
        self.q_adr, self.v_adr = np.array(self.q_adr), np.array(self.v_adr)
        d = mj.MjData(m)
        mj.mj_forward(m, d)
        M = np.zeros((m.nv, m.nv))
        mj.mj_fullM(m, M, d.qM)
        inertia = np.diag(M)[self.v_adr]
        wn = 2 * np.pi * bandwidth_hz
        self.kp, self.kd = inertia * wn ** 2, 2 * zeta * inertia * wn
        self.power = np.zeros(2)
        self.t_s = 0.0
        self.dt = m.opt.timestep
        self.torque = np.zeros(6)

    def __call__(self, d) -> None:
        if not self.power.any():
            self.torque[:] = 0.0
        else:
            q, qd = [], []
            for i in range(2):
                a, b = self.kin.targets(self.t_s, float(self.power[i]))
                if self.power[i] == 0:      # a silent wing stays passive
                    a, b = d.qpos[self.q_adr[3 * i:3 * i + 3]], np.zeros(3)
                q.append(a); qd.append(b)
            q, qd = np.concatenate(q), np.concatenate(qd)
            self.torque = self.kp * (q - d.qpos[self.q_adr]) + self.kd * (qd - d.qvel[self.v_adr])
            on = np.repeat(self.power > 0, 3)
            self.torque[~on] = 0.0
        d.qfrc_applied[self.v_adr] = self.torque
        self.t_s += self.dt
