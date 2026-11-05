"""Fast worm body: a planar, inextensible Kirchhoff rod in resistive-force media (Boyle-Berri-Cohen lineage).

Coordinates q = [x0, y0, theta_0 .. theta_{N-1}]: head position and the angle of each of N equal segments.
Overdamped (Re << 1, BODY.md s2): no inertia, so drag balances the internal forces at every instant:

    A(q) dq/dt = -dU/dq + Q_active,   U = sum_k (EI_k / 2ds) phi_k^2,  phi_k = theta_k - theta_{k-1}

A(q) = J^T R J (resistive-force drag of each segment, tangential C_t, normal C_n per unit length) plus the
internal bending viscosity. Each step solves the linearly implicit system

    (A(q_n)/dt + K) q_{n+1} = A(q_n) q_n/dt + D^T M_active

which is the exact minimiser of U(q) + |q - q_n|^2_A / (2 dt) - M.q, so with the brain silent the elastic energy
can only fall (the dead-worm test), whatever dt.

Sign convention: +normal n = (-sin, cos) is DORSAL. Positive curvature = dorsal side concave = dorsal muscles
shortened. Validity: planar dorsoventral bending only (no roll, twist, left-right bending or 3D burrowing);
no self-contact; linear (Newtonian-style) substrate drag; no inertia (fine below Re ~ 0.5).
"""
from __future__ import annotations

import json
from dataclasses import dataclass, field

import numpy as np

from .ledger import MECHANISMS, BodyLedger
from .muscles import N_MUSCLES, MuscleLayout

# Mechanism switches (docs/worm/INTERFACE.md, data/worm/ledger/body_mechanisms.json). The first option of each
# is the neutral/default setting.
TOGGLES = {
    "env.agar_drag": ("wallace_K40", "rabets_K1p4"),
    "muscle.input": ("activation", "calcium_hill"),
    "muscle.force_gradient": ("radius_scaled", "bbc_head_to_tail"),
    "muscle.force_length": ("off", "gaussian"),
    "body.internal_damping": ("kelvin_voigt", "off"),
}


def default_toggles():
    return {k: v[0] for k, v in TOGGLES.items()}


@dataclass
class BodyConfig:
    medium: str = "agar"  # "agar" | "water" | "viscous" (Newtonian with viscosity_pa_s)
    viscosity_pa_s: float | None = None
    n_seg: int | None = None  # None = ledger numerics row
    dt: float | None = None
    toggles: dict = field(default_factory=default_toggles)


def _numerics():
    with open(MECHANISMS) as fh:
        return json.load(fh)["numerics"]


class Body:
    def __init__(self, ledger: BodyLedger | None = None, cfg: BodyConfig | None = None):
        self.L = ledger or BodyLedger.load()
        self.cfg = cfg or BodyConfig()
        num = _numerics()
        for k, v in default_toggles().items():
            self.cfg.toggles.setdefault(k, v)
        for k, v in self.cfg.toggles.items():
            if v not in TOGGLES[k]:
                raise ValueError(f"toggle {k}={v} not in {TOGGLES[k]}")
        self.N = int(self.cfg.n_seg or num["n_seg"])
        # water/buffer relaxes in ~0.2 ms, so fluids take a shorter step (ledger numerics, BODY_TESTS.md)
        self.dt = float(self.cfg.dt or (num["dt_s"] if self.cfg.medium == "agar" else num["dt_fluid_s"]))
        L = self.L
        N = self.N
        self.length = L.si("wb1_length")
        self.ds = self.length / N
        ds = self.ds
        # arclength of nodes (N+1), segment midpoints (N), interior joints (N-1); 0 = head tip
        self.s_node = np.arange(N + 1) * ds
        self.s_mid = (np.arange(N) + 0.5) * ds
        self.s_joint = self.s_node[1:-1]
        # radius profile, Boyle-Berri-Cohen 2012 eq. 2 in continuous form: R(s) = R sin(acos(u)),
        # u = (s - L/2) / (L/2 + e*ds_bbc), e = wb1_radius_end_offset in units of BBC segments (48 per body)
        rmax = L.si("wb1_radius_max")
        e = L.si("wb1_radius_end_offset") * self.length / 48.0
        self.radius = lambda s: rmax * np.sin(np.arccos(np.clip((s - self.length / 2) / (self.length / 2 + e), -1, 1)))
        self.r_joint = self.radius(self.s_joint)
        self.r_mid = self.radius(self.s_mid)
        self.r_node = self.radius(self.s_node)
        self.rmax = rmax
        # bending stiffness EI(s) = b (r/rmax)^p (Backholm 2013 EI ~ D^4.02), joint springs k = EI/ds
        b = L.si("wb1_bending_stiffness")
        p = L.si("wb1_EI_radius_exponent")
        self.EI = b * (self.r_joint / rmax) ** p
        kphi = self.EI / ds
        bv = L.si("wb2_bending_viscosity") if self.cfg.toggles["body.internal_damping"] == "kelvin_voigt" else 0.0
        cphi = bv * (self.r_joint / rmax) ** p / ds
        # difference operator D: phi = D theta  (N-1, N)
        D = np.zeros((N - 1, N))
        D[np.arange(N - 1), np.arange(N - 1)] = -1.0
        D[np.arange(N - 1), np.arange(1, N)] = 1.0
        self.D = D
        nq = N + 2
        self.K = np.zeros((nq, nq))
        self.K[2:, 2:] = D.T @ (kphi[:, None] * D)
        self.B = np.zeros((nq, nq))
        self.B[2:, 2:] = D.T @ (cphi[:, None] * D)
        # drag coefficients per unit length (Pa s)
        self.Ct, self.Cn = self._drag()
        # lower-triangular map from segment angular velocities to midpoint velocities
        Lm = np.tril(np.ones((N, N)), -1) + 0.5 * np.eye(N)
        self.Lm = Lm * ds
        # muscles
        self.mus = MuscleLayout(self.s_joint / self.length, L.si("wb4_muscle_s_start"),
                                L.si("wb4_muscle_s_end"), L.si("wb4_edge_taper"))
        self.tau_act = L.si("wb5_tau_activation")
        M0 = L.si("wb6_max_moment")
        if self.cfg.toggles["muscle.force_gradient"] == "radius_scaled":
            self.Mmax = M0 * (self.r_joint / rmax) ** L.si("wb6_moment_radius_exponent")
        else:  # BBC 2012: force capacity falls linearly head to tail by the ratio wb6_bbc_head_tail_ratio
            ratio = L.si("wb6_bbc_head_tail_ratio")
            sf = self.s_joint / self.length
            g = 1.0 - (1.0 - 1.0 / ratio) * sf
            self.Mmax = M0 * g / g.mean() * (self.r_joint / rmax) ** L.si("wb6_moment_radius_exponent")
        self.fl_width = L.si("wb6_force_length_width")
        self.r_muscle = L.si("wb7_muscle_radius_fraction")
        self.ca_K = L.si("wb5_ca_half_activation")
        self.ca_n = L.si("wb5_ca_hill_n")
        self.reset()

    # ------------------------------------------------------------------ media
    def _drag(self):
        L = self.L
        med = self.cfg.medium
        if med == "agar":
            Ct = L.si("wb3_agar_Ct")
            if self.cfg.toggles["env.agar_drag"] == "wallace_K40":
                Cn = L.si("wb3_agar_Cn")
            else:  # Rabets 2014 direct force measurement: anisotropy 1.4, tangential kept
                Cn = Ct * L.si("wb3_agar_K_rabets")
            return Ct, Cn
        mu = L.si("wb3_water_viscosity") if med == "water" else float(self.cfg.viscosity_pa_s)
        # Lighthill slender-body RFT (as Boyle-Berri-Cohen 2012 eq. 1): q = 0.09 lambda
        q = L.si("wb3_lighthill_q_fraction") * L.si("wb3_swim_wavelength_ref")
        a = L.si("wb1_radius_max")
        lg = np.log(2 * q / a)
        return 2 * np.pi * mu / lg, 4 * np.pi * mu / (lg + 0.5)

    # ------------------------------------------------------------------ state
    def reset(self, theta=None, head=(0.0, 0.0), heading=0.0):
        """Straight body: head at `head`, tail along -x, nose pointing +x (forward = +x), unless theta (segment
        angles, radians, head to tail) is given."""
        N = self.N
        th = np.full(N, np.pi + heading) if theta is None else np.asarray(theta, float).copy()
        self.q = np.concatenate([np.asarray(head, float), th])
        self.a = np.zeros(N_MUSCLES)  # muscle activation state (force fraction), 0..1
        self.t = 0.0

    @property
    def theta(self):
        return self.q[2:]

    def nodes(self, q=None):
        q = self.q if q is None else q
        th = q[2:]
        steps = self.ds * np.stack([np.cos(th), np.sin(th)], 1)
        return np.vstack([q[:2], q[:2] + np.cumsum(steps, 0)])

    def curvature(self, q=None):
        q = self.q if q is None else q
        return np.diff(q[2:]) / self.ds  # (N-1,) 1/m at the joints

    def elastic_energy(self, q=None):
        q = self.q if q is None else q
        return 0.5 * q @ self.K @ q

    def centroid(self, q=None):
        x = self.nodes(q)
        mid = 0.5 * (x[1:] + x[:-1])
        return mid.mean(0)

    # ------------------------------------------------------------------ dynamics
    def drag_matrix(self, q):
        N, ds = self.N, self.ds
        th = q[2:]
        c, s = np.cos(th), np.sin(th)
        Ct, Cn = self.Ct, self.Cn
        Rxx = Ct * c * c + Cn * s * s
        Rxy = (Ct - Cn) * c * s
        Ryy = Ct * s * s + Cn * c * c
        Jx = np.zeros((N, N + 2))
        Jy = np.zeros((N, N + 2))
        Jx[:, 0] = 1.0
        Jy[:, 1] = 1.0
        Jx[:, 2:] = self.Lm * (-s)[None, :]
        Jy[:, 2:] = self.Lm * c[None, :]
        RJx = Rxx[:, None] * Jx + Rxy[:, None] * Jy
        RJy = Rxy[:, None] * Jx + Ryy[:, None] * Jy
        A = ds * (Jx.T @ RJx + Jy.T @ RJy)
        # rotational drag of each segment about its own midpoint
        A[np.arange(2, N + 2), np.arange(2, N + 2)] += Cn * ds ** 3 / 12.0
        return A

    def activation_from_input(self, u):
        u = np.asarray(u, float)
        if self.cfg.toggles["muscle.input"] == "calcium_hill":  # u is muscle [Ca] in M
            un = np.power(np.maximum(u, 0), self.ca_n)
            return un / (un + self.ca_K ** self.ca_n)
        return np.clip(u, 0.0, 1.0)

    def muscle_strain(self, q=None):
        """Fibre strain of each muscle (dimensionless, + = lengthened): -sign * kappa * r_m over its span."""
        kap = self.curvature(q)
        eps_joint_dorsal = -kap * self.r_muscle * self.r_joint
        return self.mus.sign * self.mus.per_muscle_mean(eps_joint_dorsal)

    def active_moment(self, q=None):
        f = self.a.copy()
        if self.cfg.toggles["muscle.force_length"] == "gaussian":
            f = f * np.exp(-(self.muscle_strain(q) / self.fl_width) ** 2)
        return self.Mmax * self.mus.net_drive(f)

    def step(self, u, dt=None):
        """Advance by dt (default self.dt) with muscle input u (95,) held constant (zero-order hold)."""
        dt = self.dt if dt is None else dt
        target = self.activation_from_input(u)
        # first-order excitation-contraction, exact for constant input over the step
        self.a = target + (self.a - target) * np.exp(-dt / self.tau_act)
        Ma = self.active_moment()
        A = self.drag_matrix(self.q) + self.B
        # incremental form of (A/dt + K) q_new = A q/dt + D^T Ma (same solution; a straight silent body gives
        # rhs exactly 0, so no rounding drift: BODY_TESTS.md D1)
        rhs = -self.K @ self.q
        rhs[2:] += self.D.T @ Ma
        self.q = self.q + np.linalg.solve(A / dt + self.K, rhs)
        self.t += dt
        return self.q

    def advance(self, u, duration):
        """Hold input u for `duration` seconds (the brain-body exchange interval), in whole body steps."""
        n = max(1, int(round(duration / self.dt)))
        for _ in range(n):
            self.step(u)
        return self.q

    def observe(self):
        """Body -> brain channels (docs/worm/INTERFACE.md)."""
        x = self.nodes()
        th = self.theta
        return {
            "t": self.t,
            "muscle_stretch": self.muscle_strain(),  # (95,) fibre strain
            "muscle_force_fraction": self.a.copy(),  # (95,)
            "curvature_per_mm": self.curvature() * 1e-3,  # (N-1,) at s_joint
            "s_joint_frac": self.s_joint / self.length,
            "head_xy_mm": x[0] * 1e3,
            "head_dir": np.array([-np.cos(th[0]), -np.sin(th[0])]),  # unit vector the nose points along
            "centroid_mm": self.centroid() * 1e3,
            "nodes_mm": x * 1e3,
        }
