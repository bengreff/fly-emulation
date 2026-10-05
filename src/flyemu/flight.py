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
from pathlib import Path

import mujoco as mj
import numpy as np

SIDES = ("l", "r")
FN = {"stroke": "yaw", "deviation": "roll", "rotation": "pitch"}

# Wing envelopes by function (deg, flybody coordinates; folded pose = 0,
# flybody spread pose = yaw 86 / roll 40 / pitch -57). Assumed: sized to hold
# the folded pose, the spread pose and a 140 +- 10 deg hovering stroke
# (Fry, Sayaman & Dickinson 2005 JEB 208:2303) around it.
WING_RANGE_DEG = {"yaw": (-10.0, 175.0), "roll": (-30.0, 70.0), "pitch": (-130.0, 40.0)}


# Wing envelopes from the measured hover beat (joint:wing|range_by_function = 2; F-WING-3):
# the hinge angles StrokeFrameKinematics needs for Muijres et al. 2014 steady flight
# (yaw -120.7..36.9, roll -61.9..4.2, pitch -60.3..120.6 deg; derived by wing_pose_ik
# from measured kinematics), joined with the folded pose (0, 0, 0), widened by a 20 deg
# margin on each side (guessed: Fry 2005's +-10 deg amplitude spread plus steering).
WING_RANGE_MEASURED_DEG = {"yaw": (-140.7, 56.9), "roll": (-81.9, 24.2), "pitch": (-80.3, 140.6)}


def apply_wing_ranges(body, ranges: dict | None = None) -> list[str]:
    m = body.sim.mj_model
    done = []
    for j in range(m.njnt):
        n = m.joint(j).name
        for ax, (lo, hi) in (ranges or WING_RANGE_DEG).items():
            if n.endswith(f"_wing-{ax}"):
                m.jnt_range[j] = np.radians([lo, hi])
                m.jnt_limited[j] = 1
                done.append(n)
    return done


def open_wing_ranges(body, deg: float = 180.0) -> None:
    """Wing hinge ranges +-deg (fitting measured poses: WING_RANGE_DEG holds a stroke
    that crosses the wings over the dorsum, F-WING-3)."""
    m = body.sim.mj_model
    for j in range(m.njnt):
        if any(m.joint(j).name.endswith(f"_wing-{a}") for a in FN.values()):
            m.jnt_range[j] = np.radians([-deg, deg])


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

    def targets(self, t_s: float, power: float = 1.0, mod: np.ndarray | None = None
                ) -> tuple[np.ndarray, np.ndarray]:
        """(q, qdot) targets in rad for (stroke, deviation, rotation) of one wing.
        mod (B11 steering, per wing): (d amplitude deg, d stroke mean deg,
        d deviation mean deg, d rotation mean deg), added to the generator."""
        w = 2 * np.pi * self.f_hz
        ph = w * t_s
        m = np.zeros(4) if mod is None else np.asarray(mod, float)
        A = np.radians(max(self.stroke_amp_deg + m[0], 0.0)) * power
        D = np.radians(self.dev_amp_deg) * power
        R = np.radians(self.rot_amp_deg) * power * self.rot_sign
        k = self.rot_sharp
        s = np.sin(ph)
        # the mean pose also scales with the drive: drive 0 = folded wing (all 0)
        q = np.array([np.radians(self.stroke_mean_deg + m[1]) * power + A * np.cos(ph),
                      np.radians(self.dev_mean_deg + m[2]) * power + D * np.sin(2 * ph),
                      np.radians(self.rot_mean_deg + m[3]) * power + R * np.tanh(k * s) / np.tanh(k)])
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
        self.mod = np.zeros((2, 4))     # B11 steering modifiers per wing
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
                a, b = self.kin.targets(self.t_s, float(self.level[i]), self.mod[i])
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
        # B11 steering map: male-cns steering MN groups -> per-wing kinematic change
        # (deg per Hz of group mean rate), data/params/steering_map.csv
        import pandas as pd
        from pathlib import Path
        tab = pd.read_csv(Path(__file__).resolve().parents[2] / "data" / "params" / "steering_map.csv",
                          comment="#")
        self.steer_cells, self.steer_coef = [], []
        for r in tab.itertuples():
            gain = float(reg.require(f"flight:steer_{r.group}", "gain", units="deg/Hz",
                                     model_use=f"B11: {r.group} MN rate -> {r.target}",
                                     subsystem="muscle_mechanics", minimal=float(r.coef),
                                     minimal_note=f"guessed ({r.basis}): {r.evidence}"))
            sel = np.isin(t, r.types.split(";"))
            col = ["amp", "mean", "dev", "rot"].index(r.target)
            for k in (0, 1):
                self.steer_cells.append((k, col, np.flatnonzero(sel & (side == k))))
                self.steer_coef.append(gain)
        self.steer_rate = np.zeros(len(self.steer_cells))
        self.dt = timestep_ms
        kin = None
        if int(reg.require(
                "flight:wings", "kinematics", units="enum",
                model_use="0 s10 joint-space generator (crosses the wings over the dorsum, F-WING-3; legacy "
                          "fixture), 1 measured steady-flight beat in stroke-frame angles (Muijres 2014) mapped "
                          "to the hinges (StrokeFrameKinematics)",
                subsystem="muscle_mechanics", minimal=0, minimal_note="s10-s12 behaviour")):
            kin = StrokeFrameKinematics(body)
        self.wing = WingBeat(body, kin, bandwidth_hz=3000.0)
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
        mod = np.zeros((2, 4))
        for j, ((k, col, cells), c) in enumerate(zip(self.steer_cells, self.steer_coef)):
            n = np.isin(cells, spiked).sum() if (spiked.size and cells.size) else 0
            self.steer_rate[j] = self.steer_rate[j] * a + n / max(cells.size, 1) * (1000.0 / self.tau)
            mod[k, col] += c * self.steer_rate[j]
        self.wing.mod[:] = mod
        torque = np.array(torque, dtype=np.float32, copy=True)
        p = np.maximum(p, self.wing.level)          # still beating while ramping down
        for k in (0, 1):
            if p[k] > 0:
                torque[self.wing_act[k]] = 0.0
        if p.max() > 0:
            torque[self.haltere_act] = 0.0
        return torque


def apply_aero(body, kutta: float) -> list[str]:
    """B12 (F-FLIGHT-2): fluid forces on the wing membrane only (flybody's vein mesh
    overlaps it and doubled the lifting area) with a Kutta lift coefficient
    `kutta` (inferred: ~3.1 makes hover kinematics lift ~ body weight)."""
    m = body.sim.mj_model
    done = []
    for g in list(getattr(body, "fluid_geoms", [])):
        gi = mj.mj_name2id(m, mj.mjtObj.mjOBJ_GEOM, g)
        if g.endswith("_wing_brown"):
            m.geom_fluid[gi][0] = 0.0
        elif g.endswith("_wing_membrane"):
            m.geom_fluid[gi][4] = kutta           # [enable, blunt, slender, angular, kutta, magnus]
            done.append(g)
    return done


def robofly_coefficients(alpha_deg: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """Translational lift and drag coefficients of the dynamically scaled
    Drosophila wing (Dickinson, Lehmann & Sane 1999 Science 284:1954; measured,
    Re ~136, alpha 0-90 deg)."""
    a = np.radians(alpha_deg)
    return (0.225 + 1.58 * np.sin(2.13 * a - np.radians(7.20)),
            1.92 - 1.55 * np.cos(2.04 * a - np.radians(9.82)))


# Stroke plane tilted this far nose-up from the body's long axis (deg): Muijres et
# al. 2014 Science 344:172, Table S1 / SM (D. hydei steady flight, measured, n = 1603
# wingbeats; their mean body pitch 47.6 +- 0.2). Measured in a related species; the
# thorax frame x axis is taken as the body axis (assumed).
STROKE_PLANE_DEG = 47.5


def stroke_normal(tilt_deg: float = STROKE_PLANE_DEG) -> np.ndarray:
    """Stroke-plane normal (dorsal side) in the thorax frame (x head, y left, z up)."""
    b = np.radians(tilt_deg)
    return np.array([np.sin(b), 0.0, np.cos(b)])


def stroke_frame_vectors(phi, dev, alpha, side: str, tilt_deg: float = STROKE_PLANE_DEG):
    """Unit span (hinge to tip) and leading-edge vectors in the thorax frame for one
    wing pose given as stroke-frame angles (deg), in the convention of Muijres et al.
    2014 (inferred from their SM; DECISIONS s12 19:08): phi stroke, positive
    posterior; dev deviation, positive toward the stroke-plane normal; alpha rotation
    about the span, 0 with the chord normal to the stroke plane (leading edge up),
    positive = leading edge toward anterior."""
    b = np.radians(tilt_deg)
    n = stroke_normal(tilt_deg)
    f = np.array([np.cos(b), 0.0, -np.sin(b)])         # anterior, in the stroke plane
    lat = np.array([0.0, 1.0 if side == "l" else -1.0, 0.0])
    p, g, a = np.radians([phi, dev, alpha])
    span = np.cos(g) * (np.cos(p) * lat - np.sin(p) * f) + np.sin(g) * n
    t = np.sin(p) * lat + np.cos(p) * f                # stroke tangent toward anterior
    t -= (t @ span) * span
    t /= np.linalg.norm(t)
    up = n - (n @ span) * span
    up /= np.linalg.norm(up)
    return span, np.cos(a) * up + np.sin(a) * t


def stroke_frame_spin(om_rel: np.ndarray, sp: np.ndarray, n: np.ndarray) -> float:
    """Wing spin about its span relative to the stroke frame (span, stroke-plane normal
    n): om_rel . sp minus the frame's own spin about sp, which is
    -(n.sp)(sp_dot . (sp x e))/|v| with v = n - (n.sp)sp, e = v/|v|, sp_dot =
    om_rel x sp (derived). A cone swept about n gives 0; for poses built by
    stroke_frame_vectors it equals +-dalpha/dt (+ left wing, - right)."""
    v = n - (n @ sp) * sp
    nv = np.linalg.norm(v)
    e = v / nv
    return float(om_rel @ sp + (n @ sp) * (np.cross(om_rel, sp) @ np.cross(sp, e)) / nv)


# Hinge to the farthest membrane vertex of the scanned wing (derived from the flybody
# mesh; the hinge anchor sits on the thorax surface; runs/s12/diag/wing_root_geometry.py)
WING_LENGTH_SCAN_MM = 2.65
# Female D. melanogaster wing length R, Canton-S, n = 27 (measured; Lehmann & Dickinson
# 1997 J Exp Biol 200:1133, Table 1; same cohort weighed 1.05 mg, 1998)
WING_LENGTH_FEMALE_MM = 2.47


class BladeElementWing:
    """B12 option (aero:wing|model = 1; F-FLIGHT-3): quasi-steady blade-element
    forces on each wing membrane, written to xfrc_applied (body.passive_hooks).

    Per spanwise strip of the membrane ellipse (chord c(r), width dr), with w the
    strip's velocity relative to the air (spanwise part removed) taken on the
    pitch axis, and alpha in [0, 90] deg the angle between w and the chord plane:
      translational: drag 1/2 rho |w|^2 CD(alpha) c dr against w; lift 1/2 rho |w|^2
        CL(alpha) c dr normal to w on the side the plate pushes (robofly CL, CD,
        measured; the plate is treated as symmetric, so alpha is folded);
      rotational: C_rot rho |w| dalpha/dt c^2 dr normal to the plate, dalpha/dt the
        wing's rotation about its span relative to the stroke frame (span, stroke-plane
        normal; STROKE_PLANE_DEG), i.e. the measured rotation-angle rate: the conical
        stroke spins the wing about its span without changing alpha, so that spin is
        removed. (s12 first used the pitch joint rate as a proxy, rot_rate="pitch_joint";
        wrong here because the model's hinge axes are not the stroke frame, F-WING-3),
        C_rot =
        pi (0.75 - x0) (Sane & Dickinson 2002 JEB 205:1087, theory matched by their
        robofly), x0 the pitch axis' chord position, derived from the model at
        mid-span (0.20).
    MuJoCo's own drag, lift and angular drag on the membrane are switched off (they
    would count the same force twice); its added-mass terms stay. Not modelled:
    acceleration added mass, wake capture, pitching moment (forces act on the pitch
    axis), wing flexion. Validity: hovering-like strokes at Re ~ 100-200."""

    def __init__(self, body, n_strips: int = 20, rot_rate: str = "stroke_frame",
                 stroke_plane_deg: float = STROKE_PLANE_DEG, length_mm: float | None = None):
        m, d = body.sim.mj_model, body.sim.mj_data
        # aero:wing|size_source 1: strips scaled isometrically about the hinge to a
        # measured wing length; mesh, inertia and MuJoCo added mass keep the scan's size
        self.length_scale = 1.0 if length_mm is None else length_mm / WING_LENGTH_SCAN_MM
        self.m = m
        assert rot_rate in ("stroke_frame", "pitch_joint")
        self.rot_rate = rot_rate
        self.thorax = mj.mj_name2id(m, mj.mjtObj.mjOBJ_BODY, f"{body.fly.name}/c_thorax")
        self.n_stroke = stroke_normal(stroke_plane_deg)    # thorax frame
        mj.mj_forward(m, d)
        self.bid, self.pts, self.span, self.normal, self.c, self.dr, self.x0 = [], [], [], [], [], [], []
        self.pitch_dof, self.pitch_s = [], []
        for s in SIDES:
            g = mj.mj_name2id(m, mj.mjtObj.mjOBJ_GEOM, f"{body.fly.name}/{s}_wing_membrane")
            b = int(m.geom_bodyid[g])
            Rb, xb = d.xmat[b].reshape(3, 3), d.xpos[b]
            Rg, sz = d.geom_xmat[g].reshape(3, 3), m.geom_size[g]
            o = np.argsort(sz)
            normal, chord, span = (Rb.T @ Rg[:, o[k]] for k in range(3))
            a, half = sz[o[1]], sz[o[2]]
            ctr = Rb.T @ (d.geom_xpos[g] - xb)
            if ctr @ span < 0:
                span = -span                          # root to tip
            j = mj.mj_name2id(m, mj.mjtObj.mjOBJ_JOINT, f"{body.fly.name}/c_thorax-{s}_wing-{FN['rotation']}")
            jp, ax = m.jnt_pos[j], m.jnt_axis[j]
            self.pitch_dof.append(int(m.jnt_dofadr[j])); self.pitch_s.append(float(ax @ span))
            y = -half + (np.arange(n_strips) + 0.5) * 2 * half / n_strips
            t = (y + (ctr - jp) @ span) / (ax @ span)
            pts = jp + t[:, None] * ax                 # strip points on the pitch axis
            c = 2 * a * np.sqrt(1 - (y / half) ** 2)
            dr = 2 * half / n_strips
            c *= np.pi * a * half / (c.sum() * dr)     # planform area exactly pi a b
            k = self.length_scale
            pts, c, dr = jp + k * (pts - jp), k * c, k * dr
            off = abs((jp + (ctr - jp) @ span / (ax @ span) * ax - ctr) @ chord)
            self.bid.append(b); self.pts.append(pts); self.span.append(span); self.normal.append(normal)
            self.c.append(c); self.dr.append(dr); self.x0.append(float((a - off) / (2 * a)))
        self.c_rot = [np.pi * (0.75 - x) for x in self.x0]
        self.force = np.zeros((2, 3))                  # last total force per wing (world, uN)
        self.parts = np.zeros((2, 3, 3))               # per wing: lift, drag, rotational (world, uN)
        self.alpha = np.zeros((2, n_strips))           # last folded angle of attack per strip (deg)
        self._v = np.zeros(6)

    def __call__(self, d) -> None:
        m = self.m
        mj.mj_kinematics(m, d)
        mj.mj_comPos(m, d)
        mj.mj_comVel(m, d)
        mj.mj_objectVelocity(m, d, mj.mjtObj.mjOBJ_XBODY, self.thorax, self._v, 0)
        om_th = self._v[:3].copy()
        n_st = d.xmat[self.thorax].reshape(3, 3) @ self.n_stroke
        for k, b in enumerate(self.bid):
            R, x = d.xmat[b].reshape(3, 3), d.xpos[b]
            mj.mj_objectVelocity(m, d, mj.mjtObj.mjOBJ_XBODY, b, self._v, 0)   # at xpos, not the COM
            om, v0 = self._v[:3], self._v[3:]
            P = x + self.pts[k] @ R.T
            sp, n = R @ self.span[k], R @ self.normal[k]
            W = v0 + np.cross(om, P - x) - m.opt.wind
            W -= np.outer(W @ sp, sp)
            U = np.linalg.norm(W, axis=1)
            if U.max() < 1e-6:
                d.xfrc_applied[b] = 0.0
                self.force[k] = 0.0
                continue
            u = W / np.maximum(U, 1e-12)[:, None]
            un = u @ n
            sgn = np.where(un >= 0, 1.0, -1.0)
            alpha = np.degrees(np.arcsin(np.clip(np.abs(un), 0.0, 1.0)))
            CL, CD = robofly_coefficients(alpha)
            q = 0.5 * self.rho(m) * U ** 2 * self.c[k] * self.dr[k]
            en = -sgn[:, None] * n                     # side the plate pushes
            eL = en - (en * u).sum(1)[:, None] * u
            eL /= np.maximum(np.linalg.norm(eL, axis=1), 1e-12)[:, None]
            if self.rot_rate == "pitch_joint":
                om_s = d.qvel[self.pitch_dof[k]] * self.pitch_s[k]
            else:
                om_s = stroke_frame_spin(om - om_th, sp, n_st)
            dalpha = sgn * om_s * np.where(u @ np.cross(sp, n) >= 0, 1.0, -1.0)
            frot = self.c_rot[k] * self.rho(m) * U * dalpha * self.c[k] ** 2 * self.dr[k]
            parts = (q * CL)[:, None] * eL, -(q * CD)[:, None] * u, frot[:, None] * en
            F = parts[0] + parts[1] + parts[2]
            Ft = F.sum(0)
            self.parts[k] = [x.sum(0) for x in parts]
            self.alpha[k] = alpha
            d.xfrc_applied[b, :3] = Ft
            d.xfrc_applied[b, 3:] = np.cross(P - d.xipos[b], F).sum(0)
            self.force[k] = Ft

    @staticmethod
    def rho(m) -> float:
        return float(m.opt.density)


def apply_blade_element(body, n_strips: int = 20, **kw) -> BladeElementWing:
    """Membrane-only aero (apply_aero) with MuJoCo's drag/lift/angular drag off on
    the membrane, and the blade-element hook appended to body.passive_hooks."""
    m = body.sim.mj_model
    for g in apply_aero(body, 0.0):
        gi = mj.mj_name2id(m, mj.mjtObj.mjOBJ_GEOM, g)
        m.geom_fluid[gi][1:6] = 0.0                    # interaction stays on: added mass
    hook = BladeElementWing(body, n_strips, **kw)
    body.passive_hooks = list(getattr(body, "passive_hooks", ())) + [hook]
    return hook


def wing_axes(body, side: str) -> tuple[int, int, int, float]:
    """(geom id, span column, chord column, leading-edge sign) of a wing membrane
    ellipsoid. The leading edge is the chord side that holds the pitch (rotation)
    axis, as in a real wing (derived from the model geometry)."""
    m = body.sim.mj_model
    d = mj.MjData(m)
    mj.mj_kinematics(m, d)
    g = mj.mj_name2id(m, mj.mjtObj.mjOBJ_GEOM, f"{body.fly.name}/{side}_wing_membrane")
    o = np.argsort(m.geom_size[g])
    j = mj.mj_name2id(m, mj.mjtObj.mjOBJ_JOINT, f"{body.fly.name}/c_thorax-{side}_wing-{FN['rotation']}")
    Rg = d.geom_xmat[g].reshape(3, 3)
    r, ax = d.xanchor[j] - d.geom_xpos[g], d.xaxis[j]
    r = r - (r @ Rg[:, o[2]]) / (ax @ Rg[:, o[2]]) * ax          # axis point at mid-span
    return g, int(o[2]), int(o[1]), float(np.sign(r @ Rg[:, o[1]]))


def wing_span_sign(body, side: str) -> float:
    """+1 if the membrane's span column points from the hinge toward the tip, else
    -1 (the ellipsoid axis sign is arbitrary; rigid, so one pose decides it)."""
    m = body.sim.mj_model
    d = mj.MjData(m)
    mj.mj_kinematics(m, d)
    g, i_s, _, _ = wing_axes(body, side)
    j = mj.mj_name2id(m, mj.mjtObj.mjOBJ_JOINT, f"{body.fly.name}/c_thorax-{side}_wing-{FN['stroke']}")
    return float(np.sign(d.geom_xmat[g].reshape(3, 3)[:, i_s] @ (d.geom_xpos[g] - d.xanchor[j])))


def wing_pose_ik(body, side: str, span_t: np.ndarray, lead_t: np.ndarray,
                 q_start: np.ndarray | None = None) -> tuple[np.ndarray, float]:
    """Hinge angles (stroke, deviation, rotation) in rad that point the membrane's
    span (hinge to tip) along span_t and its leading edge along lead_t (both unit-ish, thorax
    frame), by bounded least squares on the wing pose (independent of joint order;
    bounds = the joint ranges). Returns (q, worst axis error in deg)."""
    from scipy.optimize import least_squares
    m = body.sim.mj_model
    d = mj.MjData(m)
    th = mj.mj_name2id(m, mj.mjtObj.mjOBJ_BODY, f"{body.fly.name}/c_thorax")
    g, i_s, i_c, le = wing_axes(body, side)
    out = wing_span_sign(body, side)
    jid = [mj.mj_name2id(m, mj.mjtObj.mjOBJ_JOINT, f"{body.fly.name}/c_thorax-{side}_wing-{FN[fn]}")
           for fn in ("stroke", "deviation", "rotation")]
    adr = [m.jnt_qposadr[j] for j in jid]
    lo = np.array([m.jnt_range[j][0] if m.jnt_limited[j] else -np.inf for j in jid])
    hi = np.array([m.jnt_range[j][1] if m.jnt_limited[j] else np.inf for j in jid])
    span_t, lead_t = span_t / np.linalg.norm(span_t), lead_t / np.linalg.norm(lead_t)

    def axes(q):
        d.qpos[adr] = q
        mj.mj_kinematics(m, d)
        Rt, Rg = d.xmat[th].reshape(3, 3), d.geom_xmat[g].reshape(3, 3)
        return out * (Rt.T @ Rg[:, i_s]), le * (Rt.T @ Rg[:, i_c])

    starts = [q_start] if q_start is not None else []
    starts += [np.radians([a, b_, c]) for a in (10, 90, 160) for b_ in (0, 40) for c in (-100, -30, 20)]
    best = None
    for q0 in starts:
        q0 = np.clip(q0, lo + 1e-6, hi - 1e-6)
        r = least_squares(lambda q: np.concatenate([axes(q)[0] - span_t, axes(q)[1] - lead_t]), q0,
                          bounds=(lo, hi))
        if best is None or r.cost < best.cost - 1e-12:
            best = r
        if best.cost < 1e-12:
            break
    s_, c_ = axes(best.x)
    err = max(np.degrees(np.arccos(np.clip(s_ @ span_t, -1, 1))), np.degrees(np.arccos(np.clip(c_ @ lead_t, -1, 1))))
    return best.x, float(err)


MEASURED_HOVER_CSV = Path(__file__).resolve().parents[2] / "data" / "derived" / "muijres2014_hover_kinematics.csv"


class StrokeFrameKinematics:
    """F-WING-3 fix (flight:wings|kinematics = 1): a measured wingbeat given in
    stroke-frame angles (stroke phi, deviation gamma, rotation alpha; Muijres et al.
    2014 Table S1, D. hydei steady flight, measured; convention of stroke_frame_vectors)
    mapped to hinge angles by wing_pose_ik at each table phase, with ranges opened for
    the fit and restored after. Left and right hinges are mirror images, so one table
    serves both wings (checked: < 0.002 deg apart). WingKinematics' targets() interface.

    B11 steering mods (d amplitude, d stroke mean, d deviation, d rotation; deg) act on
    the stroke-frame angles: the amplitude change scales phi about its mean, the others
    shift. They reach the hinges through the pose Jacobian dq/d(phi, gamma, alpha) at
    each phase (linear in the mods; derived by finite differences of wing_pose_ik).
    power scales the hinge angles toward the folded pose (0), as in WingKinematics."""

    def __init__(self, body, csv: Path | str = MEASURED_HOVER_CSV, f_hz: float = 218.0,
                 tilt_deg: float = STROKE_PLANE_DEG, side: str = "l", eps_deg: float = 0.5):
        import pandas as pd
        from scipy.interpolate import CubicSpline
        t = pd.read_csv(csv, comment="#")
        ph = t["phase"].to_numpy(float)
        ang = t[["stroke_deg", "deviation_deg", "rotation_deg"]].to_numpy(float)
        if ph[-1] >= 1.0:
            ph, ang = ph[:-1], ang[:-1]
        m = body.sim.mj_model
        keep = (m.jnt_range.copy(), m.jnt_limited.copy())
        open_wing_ranges(body)
        try:
            q, J, qa = [], [], None
            for a in ang:
                qa, err = wing_pose_ik(body, side, *stroke_frame_vectors(*a, side, tilt_deg), q_start=qa)
                if err > 0.5:
                    raise ValueError(f"measured pose not reachable: {err:.2f} deg")
                cols = []
                for i in range(3):
                    da = a.copy()
                    da[i] += eps_deg
                    qb, _ = wing_pose_ik(body, side, *stroke_frame_vectors(*da, side, tilt_deg), q_start=qa)
                    cols.append((qb - qa) / np.radians(eps_deg))
                q.append(qa)
                J.append(np.array(cols).T)
        finally:
            m.jnt_range[:], m.jnt_limited[:] = keep
        q = np.unwrap(np.array(q), axis=0)
        x = np.append(ph, 1.0)
        per = lambda v: CubicSpline(x, np.concatenate([v, v[:1]]), bc_type="periodic", axis=0)  # noqa: E731
        self.f_hz = f_hz
        self.q, self.J = per(q), per(np.array(J))
        self.ang = per(np.radians(ang))
        self.phi_mean = float(np.radians(ang[:, 0]).mean())
        self.phi_amp = float(np.radians(np.ptp(ang[:, 0])) / 2)

    def targets(self, t_s: float, power: float = 1.0, mod: np.ndarray | None = None
                ) -> tuple[np.ndarray, np.ndarray]:
        ph = (t_s * self.f_hz) % 1.0
        q, qd = self.q(ph), self.q(ph, 1) * self.f_hz
        if mod is not None and np.any(mod):
            dA, dm, dg, da = np.radians(np.asarray(mod, float))
            dA = max(dA, -self.phi_amp)
            phi, dphi = self.ang(ph)[0], self.ang(ph, 1)[0] * self.f_hz
            k = dA / self.phi_amp
            delta = np.array([k * (phi - self.phi_mean) + dm, dg, da])
            ddelta = np.array([k * dphi, 0.0, 0.0])
            J, Jd = self.J(ph), self.J(ph, 1) * self.f_hz
            q, qd = q + J @ delta, qd + Jd @ delta + J @ ddelta
        return q * power, qd * power


class TableKinematics:
    """Wing kinematics from a measured table over one beat (joint angles per phase,
    periodic cubic spline), with WingKinematics' targets() interface. Built by
    fitting the hinge angles to a measured wing pose (wing_pose_ik)."""

    def __init__(self, phase: np.ndarray, q: np.ndarray, f_hz: float):
        from scipy.interpolate import CubicSpline
        q = np.unwrap(np.asarray(q, float), axis=0)
        ph = np.asarray(phase, float)
        if ph[-1] < 1.0:
            ph, q = np.append(ph, 1.0), np.vstack([q, q[:1]])
        q[-1] = q[0]
        self.f_hz = f_hz
        self.spline = CubicSpline(ph, q, bc_type="periodic", axis=0)

    def targets(self, t_s: float, power: float = 1.0, mod: np.ndarray | None = None
                ) -> tuple[np.ndarray, np.ndarray]:
        ph = (t_s * self.f_hz) % 1.0
        return self.spline(ph) * power, self.spline(ph, 1) * self.f_hz * power
