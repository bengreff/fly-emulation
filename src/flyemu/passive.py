"""B3 passive joint mechanics: measured leg stiffness (eLife 2025).

data/params/passive_leg_stiffness.csv holds the per-leg, per-DOF medians of
Wang et al. 2025 (PMC12324252, Table 1), converted to uN*mm/rad after the unit
reconciliation (FINDINGS s9, F-PASSIVE-1). Leg DOFs the paper did not measure
(ThC pitch, trochanter-femur roll, tibia-tarsus) take the median of that leg's
four measured DOFs (inferred). The tarsal chain (B2) and damping are unchanged.

Rest angles: the paper gives equilibrium angles only in its Figure 3C, so the
spring reference stays at flybody's neutral pose (guessed) until they are read.

Registry switch `joint:leg|passive_stiffness_source`: 0 = flybody group
defaults (1 uN*mm/rad; legacy m4), 1 = measured.
"""
from __future__ import annotations

from pathlib import Path

import mujoco as mj
import numpy as np
import pandas as pd

TABLE = Path(__file__).resolve().parents[2] / "data" / "params" / "passive_leg_stiffness.csv"
LEGS = {"f": "pro", "m": "meso", "h": "meta"}
UNMEASURED = ("thorax-coxa-pitch", "coxa-trochanterfemur-roll", "tibia-tarsus1-pitch")


def _joint_name(side: str, seg: str, template: str) -> str:
    leg = f"{side}{seg}"
    a, b, ax = {
        "thorax-coxa-yaw": ("c_thorax", "coxa", "yaw"),
        "thorax-coxa-roll": ("c_thorax", "coxa", "roll"),
        "thorax-coxa-pitch": ("c_thorax", "coxa", "pitch"),
        "coxa-trochanterfemur-pitch": ("coxa", "trochanterfemur", "pitch"),
        "coxa-trochanterfemur-roll": ("coxa", "trochanterfemur", "roll"),
        "trochanterfemur-tibia-pitch": ("trochanterfemur", "tibia", "pitch"),
        "tibia-tarsus1-pitch": ("tibia", "tarsus1", "pitch"),
    }[template]
    pa = a if a == "c_thorax" else f"{leg}_{a}"
    return f"{pa}-{leg}_{b}-{ax}"


def measured_stiffness() -> dict[str, float]:
    """flybody joint name -> stiffness (uN*mm/rad) for every leg hinge above the tarsi."""
    t = pd.read_csv(TABLE, comment="#")
    out = {}
    for side in ("l", "r"):
        for seg, leg in LEGS.items():
            rows = t[t.leg == leg]
            for r in rows.itertuples():
                out[_joint_name(side, seg, r.flybody_joint)] = float(r.stiffness_uNmm_per_rad)
            med = float(rows.stiffness_uNmm_per_rad.median())
            for u in UNMEASURED:
                out[_joint_name(side, seg, u)] = med
    return out


def apply(body, source: int = 1, scale: float = 1.0) -> dict[str, float]:
    """Set leg joint stiffness on a compiled Body. Returns what was set."""
    if source == 0:
        return {}
    m = body.sim.mj_model
    prefix = f"{body.fly.name}/"
    k = measured_stiffness()
    for name, v in k.items():
        j = mj.mj_name2id(m, mj.mjtObj.mjOBJ_JOINT, prefix + name)
        if j < 0:
            raise KeyError(name)
        m.jnt_stiffness[j] = v * scale
    return k


def register(reg, body) -> dict[str, float]:
    """Organism entry point: read the switch from the registry and apply."""
    from .registry import Status
    src = reg.require("joint:leg", "passive_stiffness_source", units="enum",
                      model_use="0 flybody defaults (1 uN*mm/rad), 1 measured by name mapping, 2 measured projected and coupled (J^T K J)",
                      subsystem="body_mechanics", minimal=0,
                      minimal_note="legacy m4 body; measured values are an option until adopted")
    if int(src) == 2:
        apply_coupled(body)
        reg.provide("joint:leg", "passive_stiffness", "J^T K J (passive.apply_coupled)", units="uN*mm/rad",
                    model_use="coupled torsional springs per leg", status=Status.DERIVED,
                    evidence="eLife 2025 Table 1 medians projected through the Jacobian of the paper's leg "
                             "angles at the neutral pose (F-PASSIVE-2); tibia-tarsus = leg median (inferred)",
                    subsystem="body_mechanics", instances=6)
        return {}
    k = apply(body, int(src))
    if k:
        reg.provide("joint:leg", "passive_stiffness", str(TABLE.name), units="uN*mm/rad",
                    model_use="torsional spring per leg DOF", status=Status.MEASURED,
                    evidence="Wang et al. 2025 eLife PMC12324252 Table 1 (medians, right legs); "
                             "unit mN*m/deg reconciled (F-PASSIVE-1); unmeasured DOFs = leg median (inferred)",
                    uncertainty="IQR ~2-fold across flies; DOF mapping inferred from axis geometry",
                    subsystem="body_mechanics", instances=len(k))
    return k


def fold_wings(body) -> list[str]:
    """B14: reference the wing springs to the folded (neutral) pose. flybody's
    wing spring reference is a spread pose whose yaw (86 deg) lies outside the
    wing-yaw range (+-15 deg), so a passive wing is pinned on its stop (s9)."""
    m = body.sim.mj_model
    done = []
    for j in range(m.njnt):
        name = mj.mj_id2name(m, mj.mjtObj.mjOBJ_JOINT, j) or ""
        if m.jnt_type[j] == mj.mjtJoint.mjJNT_HINGE and "_wing-" in name:
            a = m.jnt_qposadr[j]
            m.qpos_spring[a] = m.qpos0[a]
            done.append(name.split("/")[-1])
    return done


def springs_outside_range(body) -> list[str]:
    """Hinges whose spring reference lies outside their joint range."""
    m = body.sim.mj_model
    out = []
    for j in range(m.njnt):
        if m.jnt_type[j] != mj.mjtJoint.mjJNT_HINGE or not m.jnt_limited[j]:
            continue
        q = m.qpos_spring[m.jnt_qposadr[j]]
        lo, hi = m.jnt_range[j]
        if not lo <= q <= hi:
            out.append((mj.mj_id2name(m, mj.mjtObj.mjOBJ_JOINT, j) or "").split("/")[-1])
    return out


def register_rest(reg, body) -> int:
    ref = reg.require("joint:leg", "spring_reference", units="enum",
                      model_use="0 flybody neutral pose, 1 fitted to the eLife weighted protocol (F-REST-1)",
                      subsystem="body_mechanics", minimal=0,
                      minimal_note="legacy m4 body; fitted references are a template option")
    return set_rest_angles(body) if int(ref) else 0


def register_wings(reg, body) -> list[str]:
    ref = reg.require("joint:wing", "spring_reference", units="enum",
                      model_use="0 flybody spread pose (outside the yaw range), 1 folded neutral pose",
                      subsystem="body_mechanics", minimal=0,
                      minimal_note="legacy m4 body; folded reference is an option until adopted")
    return fold_wings(body) if int(ref) else []


class CoupledSprings:
    """B3 as a coupled spring per leg (F-PASSIVE-2): torque = -K (q - q_ref),
    K = J^T diag(K_eLife) J, J = d(paper angles)/d(hinge angles) at the
    neutral pose. Replaces MuJoCo's diagonal stiffness on the projected leg
    hinges (set to 0); tibia-tarsus keeps a diagonal spring at the leg median
    (unmeasured). Applied through qfrc_applied by a Body passive hook."""

    def __init__(self, body, K: dict[str, np.ndarray], dofs: dict[str, np.ndarray],
                 qadr: dict[str, np.ndarray], qref: dict[str, np.ndarray]):
        self.K, self.dofs, self.qadr, self.qref = K, dofs, qadr, qref

    def __call__(self, d) -> None:
        for leg, K in self.K.items():
            dq = d.qpos[self.qadr[leg]] - self.qref[leg]
            d.qfrc_applied[self.dofs[leg]] = -K @ dq

    def energy(self, d) -> float:
        e = 0.0
        for leg, K in self.K.items():
            dq = d.qpos[self.qadr[leg]] - self.qref[leg]
            e += 0.5 * float(dq @ K @ dq)
        return e


def projected_matrices(body) -> tuple[dict, dict, dict, list]:
    """Per leg: joint names, J^T K J, and the paper-angle Jacobian (neutral pose)."""
    import sys
    sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "scripts"))
    from passive_rest_protocol import Leg, paper_angles
    m, d = body.sim.mj_model, body.sim.mj_data
    body.reset()
    mj.mj_forward(m, d)
    t = pd.read_csv(TABLE, comment="#")
    order = ("levdep", "retpro", "extflex", "prosup")
    out, jac, names_all = {}, {}, {}
    for side in "lr":
        for seg, cls in LEGS.items():
            L = f"{side}{seg}"
            leg = Leg(body, L)
            keep = [i for i, n in enumerate(leg.names)
                    if not any(f"tarsus{k}" in n for k in (2, 3, 4, 5)) and "tarsus1" not in n]
            Kp = np.array([float(t[(t.leg == cls) & (t.dof == a)].stiffness_uNmm_per_rad.iloc[0])
                           for a in order])
            q0 = d.qpos[leg.adr].copy()

            def ang(q):
                d.qpos[leg.adr] = q
                mj.mj_kinematics(m, d)
                return np.radians(paper_angles(d.xpos[leg.b_ctr], d.xpos[leg.b_fti],
                                               d.xpos[leg.b_tita]))
            a0, h = ang(q0), 1e-4
            J = np.zeros((4, len(keep)))
            for c, i in enumerate(keep):
                q = q0.copy()
                q[i] += h
                da = ang(q) - a0
                da[3] = (da[3] + np.pi) % (2 * np.pi) - np.pi
                J[:, c] = da / h
            d.qpos[leg.adr] = q0
            Kj = J.T @ np.diag(Kp) @ J
            # the four paper angles constrain only a rank-4 subspace of the
            # leg's hinges; the null directions (e.g. coxa roll vs femur roll
            # redundancy) get the leg's median measured stiffness (guessed)
            _, sv, vt = np.linalg.svd(J)
            null = vt[np.sum(sv > 1e-6 * sv.max()):]
            out[L] = Kj + float(np.median(Kp)) * null.T @ null
            jac[L] = J
            names_all[L] = [leg.names[i] for i in keep]
    mj.mj_forward(m, d)
    return out, jac, names_all, order


def apply_coupled(body, scale: float = 1.0) -> CoupledSprings:
    """Switch value 2: coupled projected leg springs (x scale, for tests)."""
    apply(body, 1)                                     # tibia-tarsus etc. at measured/median
    m = body.sim.mj_model
    Ks, _, names, _ = projected_matrices(body)
    pre = f"{body.fly.name}/"
    K, dofs, qadr, qref = {}, {}, {}, {}
    for L, nm in names.items():
        js = [mj.mj_name2id(m, mj.mjtObj.mjOBJ_JOINT, pre + n) for n in nm]
        m.jnt_stiffness[js] = 0.0
        K[L] = Ks[L] * scale
        dofs[L] = np.array([m.jnt_dofadr[j] for j in js])
        qadr[L] = np.array([m.jnt_qposadr[j] for j in js])
        qref[L] = m.qpos_spring[qadr[L]].copy()
    springs = CoupledSprings(body, K, dofs, qadr, qref)
    body.passive_hooks = list(getattr(body, "passive_hooks", [])) + [springs]
    return springs


REST_TABLE = Path(__file__).resolve().parents[2] / "data" / "params" / "passive_leg_rest_fit.csv"


def set_rest_angles(body) -> int:
    """B3 rest angles: spring references fitted to the eLife weighted protocol
    (F-REST-1; inferred). Updates MuJoCo's spring reference and any coupled
    spring hook. Returns the number of joints set."""
    t = pd.read_csv(REST_TABLE, comment="#")
    m = body.sim.mj_model
    pre = f"{body.fly.name}/"
    ref = {}
    for r in t.itertuples():
        j = mj.mj_name2id(m, mj.mjtObj.mjOBJ_JOINT, pre + r.joint)
        if j < 0:
            raise KeyError(r.joint)
        a = m.jnt_qposadr[j]
        m.qpos_spring[a] = r.spring_ref_rad
        ref[a] = r.spring_ref_rad
    for h in getattr(body, "passive_hooks", ()):
        if isinstance(h, CoupledSprings):
            for L in h.qref:
                h.qref[L] = np.array([ref.get(a, h.qref[L][k]) for k, a in enumerate(h.qadr[L])])
    return len(ref)
