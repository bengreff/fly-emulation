"""B4 antagonist Hill-type muscles on the flybody leg DOFs (session 9).

Each leg DOF has two muscles (direction +1 and -1 in flybody joint
coordinates), parameters from data/params/leg_muscles.csv (FlyMimic-derived for
the front leg, copies elsewhere; see scripts/build_leg_muscles.py). A muscle
with direction s, moment arm r, optimal length L0 and peak force F0 has

    normalised length  L = 1 - s r (q - q_ref) / L0     (shortens as it moves q its way)
    normalised speed   V = -s r qdot / (L0 vmax)
    force              F = F0 a FL(L) FV(V)             (passive part: B3 springs)
    joint torque       tau = s r F

with MuJoCo's own muscle curves (FL piecewise quadratic on [lmin, lmax], FV
with fvmax), so FlyMimic's fitted parameters keep their meaning. Activation a
in [0, 1] comes from the motor units (B5): `activation_from_units`.

Why it matters: net-torque actuators cancel co-contraction to zero; a pair of
muscles stiffens the joint under co-contraction through FL and FV.
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pandas as pd

TABLE = Path(__file__).resolve().parents[2] / "data" / "params" / "leg_muscles.csv"


def gain_length(L: np.ndarray, lmin: np.ndarray, lmax: np.ndarray) -> np.ndarray:
    """MuJoCo mju_muscleGainLength, vectorised."""
    L = np.asarray(L, float)
    a = 0.5 * (lmin + 1.0)
    b = 0.5 * (1.0 + lmax)
    out = np.zeros_like(L)
    m1 = (L > lmin) & (L <= a)
    x = (L - lmin) / (a - lmin)
    out = np.where(m1, 0.5 * x * x, out)
    m2 = (L > a) & (L <= 1.0)
    x = (1.0 - L) / (1.0 - a)
    out = np.where(m2, 1.0 - 0.5 * x * x, out)
    m3 = (L > 1.0) & (L <= b)
    x = (L - 1.0) / (b - 1.0)
    out = np.where(m3, 1.0 - 0.5 * x * x, out)
    m4 = (L > b) & (L < lmax)
    x = (lmax - L) / (lmax - b)
    out = np.where(m4, 0.5 * x * x, out)
    return out


def gain_velocity(V: np.ndarray, fvmax: np.ndarray) -> np.ndarray:
    """MuJoCo's force-velocity factor (V < 0 shortening, in units of vmax)."""
    V = np.asarray(V, float)
    y = fvmax - 1.0
    out = np.where(V <= -1.0, 0.0, 0.0)
    out = np.where((V > -1.0) & (V <= 0.0), (V + 1.0) ** 2, out)
    out = np.where((V > 0.0) & (V <= y), fvmax - (y - V) ** 2 / np.where(y > 0, y, 1.0), out)
    out = np.where(V > y, fvmax, out)
    return out


@dataclass
class MusclePairs:
    joint: np.ndarray         # flybody joint name per muscle
    direction: np.ndarray     # +1 / -1
    F0: np.ndarray            # uN
    r: np.ndarray             # mm
    L0: np.ndarray            # mm
    lmin: np.ndarray
    lmax: np.ndarray
    vmax: np.ndarray
    fvmax: np.ndarray
    q_ref: np.ndarray         # rad, joint angle where L = 1 (neutral pose; guessed)

    @classmethod
    def load(cls, q_ref: dict[str, float] | None = None, table: Path = TABLE) -> "MusclePairs":
        t = pd.read_csv(table, comment="#")
        qr = np.array([(q_ref or {}).get(j, 0.0) for j in t.joint])
        return cls(t.joint.to_numpy(), t.direction.to_numpy(float), t.F0_uN.to_numpy(float),
                   t.r_mm.to_numpy(float), t.L0_mm.to_numpy(float), t.lmin.to_numpy(float),
                   t.lmax.to_numpy(float), t.vmax.to_numpy(float), t.fvmax.to_numpy(float), qr)

    def lengths(self, q: np.ndarray) -> np.ndarray:
        return 1.0 - self.direction * self.r * (q - self.q_ref) / self.L0

    def forces(self, a: np.ndarray, q: np.ndarray, qd: np.ndarray) -> np.ndarray:
        """Active force per muscle (uN, >= 0) given activation and its joint's q, qdot."""
        L = self.lengths(q)
        V = -self.direction * self.r * qd / (self.L0 * self.vmax)
        return self.F0 * np.clip(a, 0.0, 1.0) * gain_length(L, self.lmin, self.lmax) * gain_velocity(V, self.fvmax)

    def torques(self, a: np.ndarray, q: np.ndarray, qd: np.ndarray) -> np.ndarray:
        """Joint torque per muscle (uN*mm); sum per joint for the net."""
        return self.direction * self.r * self.forces(a, q, qd)


def activation_from_units(unit_state: np.ndarray, per_spike: np.ndarray,
                          fused: float = 5.0) -> np.ndarray:
    """B5 summation and saturation per motor unit: a unit's twitch state
    (spike-summed impulses decaying with its twitch tau) relative to its
    fused-tetanus level `fused` x per-spike impulse, clipped to [0, 1].
    `fused` is an unknown (parameters.csv b5_fused_ratio)."""
    return np.clip(unit_state / (np.maximum(per_spike, 1e-12) * fused), 0.0, 1.0)


# B5 motor-unit twitch kinetics by class (ms): rise and decay of a
# difference-of-exponentials twitch. Azevedo et al. 2020 eLife 9:e56754
# (read s9): a fast/intermediate spike reaches half-maximal probe displacement
# in ~8.5 ms (includes conduction and leg mechanics, so force is faster);
# a slow-unit rate increase "did not reach its peak within 500 ms", and
# hyperpolarising slow units took ~100 ms to take full effect. Values below
# are inferred to satisfy those (twitch half-max 5.2 ms; slow rate step at
# 85% of steady state at 500 ms); bounds in parameters.csv (b5_twitch_*).
TWITCH_MS = {"fast": (15.0, 40.0), "intermediate": (15.0, 40.0), "slow": (200.0, 100.0)}
FUSED_HZ = 100.0          # firing rate at which a unit's force saturates (guessed)
FACIL_DELTA = 0.0         # NMJ facilitation per spike: two spikes give only ~1.6x one (Azevedo 2020)
FACIL_TAU_MS = 50.0       # facilitation decay (guessed)


class MotorUnits:
    """B5 per-unit state: spike -> facilitated impulse -> rise filter ->
    decay; activation = state / (fused rate x decay tau), clipped to [0, 1].
    facil_delta = 0 is the neutral (no facilitation) setting."""

    def __init__(self, unit_class: np.ndarray, fused_hz: float = FUSED_HZ,
                 facil_delta: float = FACIL_DELTA, facil_tau_ms: float = FACIL_TAU_MS,
                 twitch_ms: dict | None = None):
        tw = twitch_ms or TWITCH_MS
        cls = np.array([c if c in tw else "intermediate" for c in unit_class])
        self.tau_r = np.array([tw[c][0] for c in cls])
        self.tau_d = np.array([tw[c][1] for c in cls])
        self.fused = fused_hz * self.tau_d / 1000.0     # decay-state level at fused tetanus
        self.facil_delta, self.facil_tau = facil_delta, facil_tau_ms
        n = len(cls)
        self.u = np.zeros(n)       # decaying spike state
        self.r = np.zeros(n)       # rise-filtered state
        self.f = np.ones(n)        # facilitation factor

    def step(self, hit: np.ndarray, dt_ms: float) -> None:
        self.f = 1.0 + (self.f - 1.0) * np.exp(-dt_ms / self.facil_tau)
        self.u *= np.exp(-dt_ms / self.tau_d)
        self.u[hit] += self.f[hit]
        self.f[hit] += self.facil_delta
        self.r += (self.u - self.r) * (1.0 - np.exp(-dt_ms / self.tau_r))

    def activation(self) -> np.ndarray:
        return np.clip(self.r / self.fused, 0.0, 1.0)


class HillLegDrive:
    """Motor units -> antagonist leg muscles -> joint torque (B4 + B5).

    Uses the Neuromuscular twitch state per mapped motor neuron (spike-summed,
    decaying with its unit's twitch tau). Each leg MN belongs to the muscle of
    its joint whose direction equals its calibrated drive sign. Muscle
    activation is the force-weighted mean of its units' saturating activations
    (recruitment + summation). Leg actuators with muscles receive the muscle
    torque; all other actuators keep the legacy torque."""

    def __init__(self, nm, body, fused: float = 5.0, pairs: MusclePairs | None = None,
                 unit_class: np.ndarray | None = None, units_kw: dict | None = None,
                 remap: dict[int, tuple[str, float]] | None = None):
        import mujoco as mj
        m = body.sim.mj_model
        prefix = f"{body.fly.name}/"
        short = [a.split("/")[-1].removesuffix("-motor") for a in body.actuator_names]
        jadr = {}
        for name in set(short):
            j = mj.mj_name2id(m, mj.mjtObj.mjOBJ_JOINT, prefix + name)
            if j >= 0:
                jadr[name] = (m.jnt_qposadr[j], m.jnt_dofadr[j])
        t = pd.read_csv(TABLE, comment="#")
        q_ref = {j: float(m.qpos0[jadr[j][0]]) for j in t.joint.unique()}
        self.p = pairs or MusclePairs.load(q_ref)
        self.fused = fused
        self.q_adr = np.array([jadr[j][0] for j in self.p.joint])
        self.v_adr = np.array([jadr[j][1] for j in self.p.joint])
        self.m_act = np.array([short.index(j) for j in self.p.joint])
        self.leg_actuators = np.unique(self.m_act)
        key = {(j, d): i for i, (j, d) in enumerate(zip(self.p.joint, self.p.direction))}
        mn_act = [short[i] for i in nm.actuator_index]
        self.mn_muscle = np.array([key.get((a, float(s)), -1) for a, s in zip(mn_act, nm.drive_sign)])
        # per-MN re-assignment by anatomical action (e.g. the sternal rotators)
        for k, (joint, direction) in (remap or {}).items():
            self.mn_muscle[k] = key.get((joint, float(direction)), -1)
        ok = self.mn_muscle >= 0
        self.ok = ok
        self.w = np.abs(np.asarray(nm.force_per_spike, float))
        self.W = np.bincount(self.mn_muscle[ok], weights=self.w[ok], minlength=len(self.p.F0))
        self.n_actuators = nm.n_actuators
        self.mn_rows = np.asarray(nm.mn_index)
        self.units = MotorUnits(unit_class if unit_class is not None
                                else np.full(len(self.mn_rows), "intermediate"), **(units_kw or {}))

    def step(self, spiked: np.ndarray, dt_ms: float) -> None:
        hit = np.isin(self.mn_rows, spiked) if spiked.size else np.zeros(len(self.mn_rows), bool)
        self.units.step(hit, dt_ms)

    def activation(self, nm=None) -> np.ndarray:
        a_unit = self.units.activation()
        num = np.bincount(self.mn_muscle[self.ok], weights=(self.w * a_unit)[self.ok],
                          minlength=len(self.p.F0))
        return np.divide(num, self.W, out=np.zeros_like(num), where=self.W > 0)

    def torque(self, nm, data, legacy: np.ndarray) -> np.ndarray:
        a = self.activation(nm)
        tq = self.p.torques(a, data.qpos[self.q_adr], data.qvel[self.v_adr])
        out = np.asarray(legacy, float).copy()
        out[self.leg_actuators] = 0.0
        out += np.bincount(self.m_act, weights=tq, minlength=self.n_actuators)
        return out.astype(np.float32)
