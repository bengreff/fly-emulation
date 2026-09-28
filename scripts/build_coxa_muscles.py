"""Build data/params/coxa_muscles.csv: anatomical coxa muscles with moment-arm
VECTORS over flybody's three coxa hinges (B4, session 10; F-MUSCLE-2).

Why: flybody's three coxa hinges (yaw, roll, pitch) do not match anatomical
actions one-to-one (F-COXA-1), so one antagonist pair per hinge leaves hinge
directions without motor neurons once the MNs are mapped by action. A real
coxa muscle pulls on the coxa with one 3D torque; that torque has a component
on every hinge.

Derivation (front leg, label `derived`):
  1. FlyMimic (flygym asset, meshes stripped) gives, for each of its 7 coxa
     MTUs, the moment row d(length)/dq over its own three coxa hinges. A
     contracting muscle (tension T) produces generalised force -T dL/dq_j,
     and for hinges sharing one anchor that equals M . a_j, where M is the 3D
     torque per unit tension and a_j the world hinge axis. M is recovered by
     solving the 3x3 system (exact; the sum "arm x axis" is exact only for
     orthonormal axes, and FlyMimic's are not).
  2. Thorax frames are aligned by a rigid (Kabsch) fit of the six coxa origins
     of FlyMimic onto flybody's (both in their thorax frames); the rotation
     and the RMS residual are reported. A uniform scale is fitted only to
     report it; arms are not rescaled (as in build_leg_muscles.py).
  3. Pose: moment arms depend on the coxa's pose. FlyMimic's arms are read at
     the smallest coxa rotation from its fitted keyframe that points its coxa
     long axis (coxa -> trochanter origin) along flybody's neutral coxa long
     axis (aligned frame). The residual angle is reported; arms at the raw
     keyframe are written too (sensitivity column).
  4. Projection: flybody hinge k gets r_k = M' . b_k (M' = aligned M; b_k
     flybody's world hinge axis at its neutral pose). Then the muscle's
     normalised length is L = 1 - sum_k r_k (q_k - q_ref_k) / L0 and its
     torque on hinge k is r_k F: exactly the 3D torque M' F applied to the
     coxa (virtual work).
Other legs (label `guessed`; FlyMimic's middle/hind MTUs are not public):
  right front = left front mirrored in the sagittal plane (M is an axial
  vector: (Mx, My, Mz) -> (-Mx, My, -Mz)); middle/hind = the same-side front
  vector copied in the thorax frame. The alternative (copy in each coxa's own
  frame) is computed and reported as a check, not used.

Motor neurons join by male-cns type (anatomy, not joint sign):
  Tergopleural/Pleural promotor MN -> tergopleural promotor a, b; pleural promotor
  Pleural remotor/abductor MN      -> pleural remotor and abductor
  Sternal anterior/posterior rotator MN, Sternal adductor MN -> same-named muscle

    uv run python scripts/build_coxa_muscles.py
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

import mujoco as mj
import numpy as np
import pandas as pd
from scipy.optimize import minimize

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "src"))
sys.path.insert(0, str(REPO / "scripts"))

from build_leg_muscles import DEFAULT_SHAPE, XML  # noqa: E402

OUT = REPO / "data" / "params" / "coxa_muscles.csv"
LEGS = ["lf", "lm", "lh", "rf", "rm", "rh"]
FM_LEG = {"lf": "LF", "lm": "LM", "lh": "LH", "rf": "RF", "rm": "RM", "rh": "RH"}
AXES = ("yaw", "roll", "pitch")
MN_TYPE = {
    "LFC_tergopleural_promotor_a": "Tergopleural/Pleural promotor MN",
    "LFC_tergopleural_promotor_b": "Tergopleural/Pleural promotor MN",
    "LFC_pleural_promotor": "Tergopleural/Pleural promotor MN",
    "LFC_pleural_remotor_and_abductor": "Pleural remotor/abductor MN",
    "LFC_sternal_anterior_rotator": "Sternal anterior rotator MN",
    "LFC_sternal_posterior_rotator": "Sternal posterior rotator MN",
    "LFC_sternal_adductor": "Sternal adductor MN",
}
# Literature role (Cheong et al. eLife PMC13384506 and Azevedo 2024 Table A1,
# as recorded in F-COXA-1 / F-MUSCLE-2): the foot motion a muscle should give.
ROLE = {
    "LFC_tergopleural_promotor_a": "protraction",
    "LFC_tergopleural_promotor_b": "protraction",
    "LFC_pleural_promotor": "protraction",
    "LFC_pleural_remotor_and_abductor": "retraction",
    "LFC_sternal_anterior_rotator": "protraction",
    "LFC_sternal_posterior_rotator": "retraction",
    "LFC_sternal_adductor": "adduction",
}


def _rot_angle_deg(R: np.ndarray) -> float:
    return float(np.degrees(np.arccos(np.clip((np.trace(R) - 1) / 2, -1, 1))))


def _angle_deg(u, v) -> float:
    u, v = np.asarray(u, float), np.asarray(v, float)
    return float(np.degrees(np.arccos(np.clip(u @ v / np.linalg.norm(u) / np.linalg.norm(v), -1, 1))))


def kabsch(P: np.ndarray, Q: np.ndarray) -> tuple[np.ndarray, float, float, float]:
    """Rotation R (and scale s) minimising |s R (P - Pc) - (Q - Qc)|; returns R, s,
    RMS residual without scale and with scale (mm)."""
    Pc, Qc = P - P.mean(0), Q - Q.mean(0)
    U, S, Vt = np.linalg.svd(Pc.T @ Qc)
    dfix = np.sign(np.linalg.det(Vt.T @ U.T))
    D = np.diag([1, 1, dfix])
    R = Vt.T @ D @ U.T
    s = float((S * np.diag(D)).sum() / (Pc ** 2).sum())
    rms1 = float(np.sqrt(((Pc @ R.T - Qc) ** 2).sum(1).mean()))
    rms_s = float(np.sqrt(((s * Pc @ R.T - Qc) ** 2).sum(1).mean()))
    return R, s, rms1, rms_s


class FlyMimic:
    def __init__(self):
        s = XML.read_text()
        s = re.sub(r"<mesh [^>]*/>", "", s)
        s = re.sub(r'<geom [^>]*mesh="[^"]*"[^>]*/>', "", s)
        self.m = mj.MjModel.from_xml_string(s)
        self.d = mj.MjData(self.m)
        mj.mj_resetDataKeyframe(self.m, self.d, 0)
        self.qkey = self.d.qpos.copy()
        self.jid = {ax: mj.mj_name2id(self.m, mj.mjtObj.mjOBJ_JOINT, f"joint_LFCoxa_{ax}") for ax in AXES}
        self.qadr = {ax: self.m.jnt_qposadr[j] for ax, j in self.jid.items()}
        self.bid = lambda n: mj.mj_name2id(self.m, mj.mjtObj.mjOBJ_BODY, n)
        self.muscles = [mj.mj_id2name(self.m, mj.mjtObj.mjOBJ_ACTUATOR, a) for a in range(self.m.nu)]
        self.forward(self.qkey)

    def forward(self, q):
        self.d.qpos[:] = q
        mj.mj_forward(self.m, self.d)

    def thorax(self):
        b = self.bid("Thorax")
        return self.d.xpos[b].copy(), self.d.xmat[b].reshape(3, 3).copy()

    def coxa_origins(self) -> dict[str, np.ndarray]:
        p0, R0 = self.thorax()
        return {leg: R0.T @ (self.d.xpos[self.bid(f"{FM_LEG[leg]}Coxa")] - p0) for leg in LEGS}

    def long_axis(self) -> np.ndarray:
        p0, R0 = self.thorax()
        v = self.d.xpos[self.bid("LFTrochanter")] - self.d.xpos[self.bid("LFCoxa")]
        return R0.T @ v / np.linalg.norm(v)

    def torque_vectors(self) -> pd.DataFrame:
        """3D torque per unit tension (mm) in FlyMimic's thorax frame, per coxa muscle."""
        m, d = self.m, self.d
        mom = np.zeros((m.nu, m.nv))
        mj.mju_sparse2dense(mom, d.actuator_moment, d.moment_rownnz, d.moment_rowadr, d.moment_colind)
        _, R0 = self.thorax()
        A = np.array([R0.T @ d.xaxis[self.jid[ax]] for ax in AXES])       # rows: hinge axes
        dofs = [m.jnt_dofadr[self.jid[ax]] for ax in AXES]
        rows = []
        for a, name in enumerate(self.muscles):
            if name not in MN_TYPE:
                continue
            tau = -mom[a, dofs]                                              # contraction torque per T
            M = np.linalg.solve(A, tau)
            g = m.actuator_gainprm[a]
            lr = m.actuator_lengthrange[a]
            L0 = (lr[1] - lr[0]) / (g[1] - g[0])
            Lnorm = g[0] + (d.actuator_length[a] - lr[0]) / L0
            rows.append(dict(muscle=name, Mx=M[0], My=M[1], Mz=M[2], F0_uN=g[2], L0_mm=L0,
                             L_norm_at_pose=Lnorm, sum_arm_axis_err=float(np.linalg.norm(A.T @ tau - M))))
        return pd.DataFrame(rows), float(np.linalg.cond(A))


class FlyBodyGeom:
    def __init__(self):
        from flyemu.body import Body
        import warnings
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            self.body = Body(model="flybody", vision=False)
        m = self.body.sim.mj_model
        self.m, self.d = m, mj.MjData(m)
        self.d.qpos[:] = m.qpos0
        mj.mj_forward(m, self.d)
        self.pre = f"{self.body.fly.name}/"
        th = self._b("c_thorax")
        self.p0, self.R0 = self.d.xpos[th].copy(), self.d.xmat[th].reshape(3, 3).copy()

    def _b(self, n):
        return mj.mj_name2id(self.m, mj.mjtObj.mjOBJ_BODY, self.pre + n)

    def _j(self, n):
        return mj.mj_name2id(self.m, mj.mjtObj.mjOBJ_JOINT, self.pre + n)

    def local(self, v):
        return self.R0.T @ v

    def coxa_origins(self):
        return {leg: self.local(self.d.xpos[self._b(f"{leg}_coxa")] - self.p0) for leg in LEGS}

    def long_axis(self, leg):
        v = self.d.xpos[self._b(f"{leg}_trochanterfemur")] - self.d.xpos[self._b(f"{leg}_coxa")]
        return self.local(v / np.linalg.norm(v))

    def coxa_tip(self, leg):
        return self.local(self.d.xpos[self._b(f"{leg}_trochanterfemur")] - self.d.xpos[self._b(f"{leg}_coxa")])

    def hinge_axes(self, leg) -> dict[str, np.ndarray]:
        return {ax: self.local(self.d.xaxis[self._j(f"c_thorax-{leg}_coxa-{ax}")]) for ax in AXES}

    def ctr_axis(self, leg):
        return self.local(self.d.xaxis[self._j(f"{leg}_coxa-{leg}_trochanterfemur-pitch")])

    def foot_motion(self, leg, r: dict[str, float]) -> np.ndarray:
        """Thorax-frame tarsal-tip displacement (mm) for a coxa rotation dq = r / |r| (1 rad)."""
        tip = self._b(f"{leg}_tarsus5")
        jacp = np.zeros((3, self.m.nv))
        mj.mj_jacBody(self.m, self.d, jacp, None, tip)
        v = np.zeros(3)
        n = np.sqrt(sum(x * x for x in r.values()))
        for ax, x in r.items():
            v += jacp[:, self.m.jnt_dofadr[self._j(f"c_thorax-{leg}_coxa-{ax}")]] * x / n
        v = self.local(v)
        lat = np.sign(self.coxa_origins()[leg][1])
        return np.array([v[0], v[1] * lat, v[2]])        # fore, lateral (+ outward), up


def _role_ok(role: str, v) -> bool:
    """fore/lateral(+ outward)/up motion vs the literature role."""
    col, want = {"protraction": (0, 1), "retraction": (0, -1), "adduction": (1, -1)}[role]
    return bool(np.sign(v[col]) == want)


def mirror_axial(M):
    return np.array([-M[0], M[1], -M[2]])


def main() -> None:
    fm, fb = FlyMimic(), FlyBodyGeom()
    # 1. thorax alignment from the six coxa origins
    P = np.array([fm.coxa_origins()[leg] for leg in LEGS])
    Q = np.array([fb.coxa_origins()[leg] for leg in LEGS])
    R, s, rms, rms_s = kabsch(P, Q)
    print(f"thorax alignment: rotation {_rot_angle_deg(R):.1f} deg, RMS residual {1000 * rms:.0f} um "
          f"(with scale {s:.3f}: {1000 * rms_s:.0f} um)")
    # the alignment as axis-angle, to read it
    w = np.array([R[2, 1] - R[1, 2], R[0, 2] - R[2, 0], R[1, 0] - R[0, 1]])
    print("  rotation axis", np.round(w / np.linalg.norm(w), 3))

    # 2. pose match: smallest change from the keyframe that aligns the coxa long axes
    target = fb.long_axis("lf")
    key_err = _angle_deg(R @ fm.long_axis(), target)
    fm_ctr0 = None
    lo = np.array([fm.m.jnt_range[fm.jid[ax]][0] for ax in AXES])
    hi = np.array([fm.m.jnt_range[fm.jid[ax]][1] for ax in AXES])
    q0 = np.array([fm.qkey[fm.qadr[ax]] for ax in AXES])

    def pose(x):
        q = fm.qkey.copy()
        for ax, v in zip(AXES, x):
            q[fm.qadr[ax]] = v
        fm.forward(q)

    def cost(x):
        pose(x)
        c = 1.0 - (R @ fm.long_axis()) @ target
        return c + 1e-4 * np.sum((x - q0) ** 2)

    res = min((minimize(cost, q0 + dx, method="L-BFGS-B", bounds=list(zip(lo, hi)))
               for dx in ([0, 0, 0], [0.2, 0, 0], [-0.2, 0, 0], [0, 0.2, 0], [0, -0.2, 0])),
              key=lambda r: r.fun)
    pose(res.x)
    match_err = _angle_deg(R @ fm.long_axis(), target)
    print(f"coxa long axis vs flybody neutral: keyframe {key_err:.1f} deg; matched pose {match_err:.1f} deg "
          f"(coxa q {np.round(q0, 3)} -> {np.round(res.x, 3)} rad; bounds hit: "
          f"{bool(np.any(np.isclose(res.x, lo) | np.isclose(res.x, hi)))})")
    tv, cond = fm.torque_vectors()
    pose(q0)
    tv_key, _ = fm.torque_vectors()
    print(f"FlyMimic coxa hinge axes: condition number {cond:.2f}; "
          f"|sum arm*axis - exact M| up to {1000 * tv.sum_arm_axis_err.max():.1f} um")

    Mfront = {row.muscle: R @ np.array([row.Mx, row.My, row.Mz]) for row in tv.itertuples()}
    Mkey = {row.muscle: R @ np.array([row.Mx, row.My, row.Mz]) for row in tv_key.itertuples()}

    rows, checks = [], []
    for leg in LEGS:
        side, seg = leg[0], leg[1]
        ax = fb.hinge_axes(leg)
        tip = fb.coxa_tip(leg)
        for t in tv.itertuples():
            M = Mfront[t.muscle]
            Mk = Mkey[t.muscle]
            if side == "r":
                M, Mk = mirror_axial(M), mirror_axial(Mk)
            r = {a: float(M @ ax[a]) for a in AXES}
            rk = {a: float(Mk @ ax[a]) for a in AXES}
            lab = "derived" if leg == "lf" else "guessed"
            how = {"lf": "FlyMimic LF, aligned and projected (derived)",
                   "rf": "LF mirrored in the sagittal plane (guessed: symmetry)"}.get(
                leg, f"{side}f copied in the thorax frame (guessed; FlyMimic mid/hind MTUs not public)")
            name = t.muscle.removeprefix("LFC_")
            role = ROLE[t.muscle]
            lat = 1.0 if side == "l" else -1.0                                # + = away from the midline
            ct = np.cross(M / np.linalg.norm(M), tip) * np.array([1, lat, 1])    # coxa tip motion
            ft = fb.foot_motion(leg, r)
            checks.append(dict(leg=leg, muscle=name, role=role, tip_fore=ct[0], tip_lat=ct[1], tip_up=ct[2],
                               role_ok=_role_ok(role, ct), foot_fore=ft[0], foot_lat=ft[1],
                               foot_role_ok=_role_ok(role, ft)))
            for a in AXES:
                rows.append(dict(leg=leg, muscle=name, mn_type=MN_TYPE[t.muscle],
                                 joint=f"c_thorax-{leg}_coxa-{a}", r_mm=round(r[a], 6),
                                 r_keyframe_mm=round(rk[a], 6), F0_uN=round(t.F0_uN, 4),
                                 L0_mm=round(t.L0_mm, 5), **DEFAULT_SHAPE,
                                 L_norm_flymimic=round(t.L_norm_at_pose, 4), role=role,
                                 label=lab, method=how))
    df = pd.DataFrame(rows)
    ck = pd.DataFrame(checks)
    print("\nrole check: coxa-tip motion (mm per rad about the muscle's torque axis; lat + outward) and the foot "
          "motion at flybody's neutral pose (pose-dependent, information only):")
    print(ck.round(3).to_string(index=False))
    print(f"role consistent at the coxa tip: {int(ck.role_ok.sum())}/{len(ck)}; at the foot: "
          f"{int(ck.foot_role_ok.sum())}/{len(ck)}")

    # sign check against the joint-sign calibration: the foot action predicted from the
    # calibrated per-joint foot displacements must agree with the kinematic Jacobian
    cal = pd.read_csv(REPO / "data" / "derived" / "joint_signs_flybody.csv").set_index("actuator")
    agree = []
    for (leg, mus), g in df.groupby(["leg", "muscle"]):
        v = np.zeros(3)
        for rr in g.itertuples():
            c = cal.loc[rr.joint]
            v += rr.r_mm / np.radians(c.dq_deg) * c[["foot_fore_mm", "foot_lateral_mm", "foot_up_mm"]].to_numpy(float)
        f = ck[(ck.leg == leg) & (ck.muscle == mus)].iloc[0]
        agree.append(np.sign(v[0]) == np.sign(f.foot_fore))
    print(f"joint-sign calibration vs kinematic Jacobian (foot fore/back sign): {sum(agree)}/{len(agree)} agree")

    # alternative mid/hind transfer (copy in each coxa's own frame): sensitivity only
    def coxa_frame(leg):
        e1 = fb.long_axis(leg)
        c = fb.ctr_axis(leg)
        e2 = c - (c @ e1) * e1
        e2 /= np.linalg.norm(e2)
        return np.stack([e1, e2, np.cross(e1, e2)], 1)
    alt = []
    for leg in ("lm", "lh"):
        tip = fb.coxa_tip(leg)
        for mus, M in Mfront.items():
            M2 = coxa_frame(leg) @ coxa_frame("lf").T @ M
            alt.append(_role_ok(ROLE[mus], np.cross(M2 / np.linalg.norm(M2), tip)))
    print(f"mid/hind transfer: thorax-frame copy (used) role-consistent "
          f"{int(ck[ck.leg.isin(['lm', 'lh'])].role_ok.sum())}/14 (left); coxa-frame copy (not used) {sum(alt)}/14")

    header = (
        "# Anatomical coxa muscles with moment-arm vectors over flybody's three coxa hinges (B4, s10). "
        "Built by scripts/build_coxa_muscles.py from FlyMimic (arXiv 2509.06426; flygym asset) front-leg MTUs. "
        f"Thorax frames aligned by Kabsch on six coxa origins (rotation {_rot_angle_deg(R):.1f} deg, RMS residual "
        f"{1000 * rms:.0f} um); FlyMimic coxa posed to flybody's neutral coxa long axis (residual {match_err:.1f} deg; "
        f"keyframe {key_err:.1f} deg). r_mm = torque on the hinge per uN of tension (uN*mm/uN), signed: "
        "L = 1 - sum_j r_j (q_j - q_ref_j) / L0; torque_j = r_j F. r_keyframe_mm: arms at FlyMimic's raw keyframe "
        "(sensitivity). L_norm_flymimic: FlyMimic's normalised length at the matched pose (information; the model "
        "uses L = 1 at flybody neutral). F0 uN, L0 mm; shape as leg_muscles.csv. label: derived (lf) / guessed "
        "(rf mirror, mid/hind thorax-frame copies).\n")
    with open(OUT, "w") as f:
        f.write(header)
        df.to_csv(f, index=False)
    print(f"\n{len(df)} rows ({df.groupby(['leg', 'muscle']).ngroups} muscles) -> {OUT}")
    print(df[df.leg == "lf"][["muscle", "joint", "r_mm", "r_keyframe_mm"]].to_string(index=False))


if __name__ == "__main__":
    main()
