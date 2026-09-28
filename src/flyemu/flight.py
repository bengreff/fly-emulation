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
        # the mean pose also scales with the drive: drive 0 = folded wing (all 0)
        q = np.array([np.radians(self.stroke_mean_deg) * power + A * np.cos(ph),
                      np.radians(self.dev_mean_deg) * power + D * np.sin(2 * ph),
                      np.radians(self.rot_mean_deg) * power + R * np.tanh(k * s) / np.tanh(k)])
        qd = np.array([-A * w * s, 2 * D * w * np.cos(2 * ph),
                       R * k * w * np.cos(ph) / np.cosh(k * s) ** 2 / np.tanh(k)])
        return q, qd


class WingBeat:
    """B10 hook: writes PD torques on the six wing hinges to impose the
    generator's kinematics (body.passive_hooks). power: per-wing drive in [0, 1]."""

    def __init__(self, body, kin: WingKinematics | None = None, bandwidth_hz: float = 1500.0,
                 zeta: float = 0.7, ramp_ms: float = 20.0):
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
        self.power = np.zeros(2)        # commanded drive per wing
        self.level = np.zeros(2)        # applied drive: slews toward power over ramp_ms
        self.ramp = ramp_ms / 1000.0    # (unfolding and spin-up of the thoracic oscillator; guessed)
        self.t_s = 0.0
        self.dt = m.opt.timestep
        self.torque = np.zeros(6)

    def __call__(self, d) -> None:
        step = self.dt / self.ramp if self.ramp > 0 else 1.0
        self.level += np.clip(self.power - self.level, -step, step)
        if not self.level.any():
            self.torque[:] = 0.0
        else:
            q, qd = [], []
            for i in range(2):
                a, b = self.kin.targets(self.t_s, float(self.level[i]))
                q.append(a); qd.append(b)
            q, qd = np.concatenate(q), np.concatenate(qd)
            self.torque = self.kp * (q - d.qpos[self.q_adr]) + self.kd * (qd - d.qvel[self.v_adr])
            on = np.repeat(self.level > 0, 3)     # a silent wing stays passive
            self.torque[~on] = 0.0
        d.qfrc_applied[self.v_adr] = self.torque
        self.t_s += self.dt


class HaltereBeat:
    """B13 (partial): halteres beat in antiphase with the wings at the wingbeat
    frequency while the flight motor runs (hDVM-driven in the animal; here slaved
    to the generator's phase). PD-imposed like the wings. The Coriolis signal
    reaches the haltere campaniforms only through the existing |joint velocity|
    proxy (extrasenses.py), which becomes phase-locked to the beat (N16 partial)."""

    def __init__(self, body, wing: WingBeat, amp_deg: float = 60.0, bandwidth_hz: float = 3000.0):
        m = body.sim.mj_model
        self.wing, self.amp = wing, np.radians(amp_deg)
        self.q_adr, self.v_adr = [], []
        for s in SIDES:
            j = mj.mj_name2id(m, mj.mjtObj.mjOBJ_JOINT, f"{body.fly.name}/c_thorax-{s}_haltere-pitch")
            self.q_adr.append(m.jnt_qposadr[j]); self.v_adr.append(m.jnt_dofadr[j])
        self.q_adr, self.v_adr = np.array(self.q_adr), np.array(self.v_adr)
        d = mj.MjData(m)
        mj.mj_forward(m, d)
        M = np.zeros((m.nv, m.nv))
        mj.mj_fullM(m, M, d.qM)
        inertia = np.diag(M)[self.v_adr]
        wn = 2 * np.pi * bandwidth_hz
        self.kp, self.kd = inertia * wn ** 2, 2 * 0.7 * inertia * wn

    def __call__(self, d) -> None:
        p = float(self.wing.level.max())
        if p == 0:
            d.qfrc_applied[self.v_adr] = 0.0
            return
        w = 2 * np.pi * self.wing.kin.f_hz
        ph = w * self.wing.t_s + np.pi                      # antiphase to the wing stroke
        q, qd = self.amp * p * np.cos(ph), -self.amp * p * w * np.sin(ph)
        d.qfrc_applied[self.v_adr] = self.kp * (q - d.qpos[self.q_adr]) + self.kd * (qd - d.qvel[self.v_adr])


class FlightMotor:
    """B10 wiring: power-muscle MN activity (DLMn + DVMn, per side) -> drive level
    P = clip(rate / full_rate, 0, 1) with rate an exponential spike-rate estimate
    (tau_ms); P sets the wingbeat amplitude. While P > 0 on a side, that side's
    wing (and both halteres) are moved by the generator, and the legacy wing and
    haltere torques are removed (the steering-muscle map B11 is absent: steering
    MNs currently have no effect in flight)."""

    def __init__(self, reg, conn, body, timestep_ms: float, force_on: bool = False):
        if timestep_ms > 0.05 + 1e-9:
            raise ValueError("flight needs timestep <= 0.05 ms (B23; PD at 3 kHz bandwidth)")
        self.full_rate = float(reg.require(
            "flight:power", "full_rate_hz", units="Hz", model_use="power-MN rate for full stroke amplitude",
            subsystem="muscle_mechanics", minimal=10.0,
            minimal_note="guessed: asynchronous flight muscles need only low MN rates (~5-20 Hz) to stay active"))
        self.tau = float(reg.require(
            "flight:power", "rate_tau_ms", units="ms", model_use="power-MN rate estimate time constant",
            subsystem="muscle_mechanics", minimal=100.0,
            minimal_note="guessed: power-muscle Ca2+ level integrates MN spikes over ~100 ms"))
        t = conn.neurons.type.fillna("").to_numpy().astype(str)
        inst = conn.neurons.instance.fillna("").to_numpy().astype(str)
        pw = np.char.startswith(t, "DLMn") | np.char.startswith(t, "DVMn")
        side = np.array([1 if x.endswith("_R") else 0 if x.endswith("_L") else -1 for x in inst])
        self.cells = [np.flatnonzero(pw & (side == k)) for k in (0, 1)]
        self.rate = np.zeros(2)
        self.force_on = force_on
        self.dt = timestep_ms
        self.wing = WingBeat(body, bandwidth_hz=3000.0)
        self.haltere = HaltereBeat(body, self.wing)
        body.passive_hooks = list(getattr(body, "passive_hooks", ())) + [self.wing, self.haltere]
        short = [a.split("/")[-1] for a in body.actuator_names]
        self.wing_act = [np.array([i for i, a in enumerate(short) if f"c_thorax-{s}_wing-" in a]) for s in SIDES]
        self.haltere_act = np.array([i for i, a in enumerate(short) if "_haltere-" in a])

    def step(self, spiked: np.ndarray, torque: np.ndarray) -> np.ndarray:
        a = np.exp(-self.dt / self.tau)
        for k in (0, 1):
            n = np.isin(self.cells[k], spiked).sum() if spiked.size else 0
            self.rate[k] = self.rate[k] * a + n / max(len(self.cells[k]), 1) * (1000.0 / self.tau)
        p = np.ones(2) if self.force_on else np.clip(self.rate / self.full_rate, 0.0, 1.0)
        self.wing.power[:] = p
        torque = np.array(torque, dtype=np.float32, copy=True)
        p = np.maximum(p, self.wing.level)          # still beating while ramping down
        for k in (0, 1):
            if p[k] > 0:
                torque[self.wing_act[k]] = 0.0
        if p.max() > 0:
            torque[self.haltere_act] = 0.0
        return torque
