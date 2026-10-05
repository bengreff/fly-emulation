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


def set_leg_damping(body, c: float) -> int:
    """Leg hinge damping (not the inter-tarsal chain, B2): c (uN*mm*s/rad) is the
    damping of the DOFs whose flybody default is 1; the others (femur-tibia 0.4)
    keep their ratio to it, so c = 1 is the unchanged body. Returns the DOFs set."""
    m = body.sim.mj_model
    n = 0
    for j in range(m.njnt):
        name = mj.mj_id2name(m, mj.mjtObj.mjOBJ_JOINT, j) or ""
        if m.jnt_type[j] != mj.mjtJoint.mjJNT_HINGE or name.count("tarsus") >= 2:
            continue
        if not any(f"{leg}_" in name for leg in ("lf", "lm", "lh", "rf", "rm", "rh")):
            continue
        m.dof_damping[m.jnt_dofadr[j]] *= c
        n += 1
    return n


def register_damping_source(reg, body) -> None:
    """s12: leg damping from the measured stiffness (switch joint:leg|damping_source)."""
    if not int(reg.require("joint:leg", "damping_source", units="enum",
                           model_use="0 flybody default damping (x joint:leg|damping), 1 tau x each leg "
                                     "joint's measured stiffness (Kelvin-Voigt; F-DAMP-1)",
                           subsystem="body_mechanics", minimal=0,
                           minimal_note="flybody defaults (c/k ~1 s); 1 is the s12 option")):
        return
    tau = float(reg.require("joint:leg", "damping_tau_s", units="s",
                            model_use="relaxation time c/k of every leg joint",
                            subsystem="body_mechanics", minimal=0.05,
                            minimal_note="inferred: Wang et al. 2025 limbs reach the passive posture ~350 ms "
                                         "after MN silencing, explained by active-force decay (tau 100-150 ms), "
                                         "so c/k <= ~0.1 s; 0.05 s inside that bound (FlyMimic's choice)",
                            uncertainty="bounds 0.005-0.1 s (row b3_damping_tau_s)"))
    set_damping_from_stiffness(body, tau)


def set_damping_from_stiffness(body, tau_s: float) -> int:
    """Leg hinge damping c = tau x the joint's own measured stiffness (Kelvin-Voigt,
    one relaxation time for every leg joint; s12). Coupled legs use the diagonal of
    J^T K J (off-diagonal damping dropped; inferred). Applied as MuJoCo dof damping
    so the integrator treats it implicitly. Not the inter-tarsal chain (B2).
    Returns the DOFs set."""
    m = body.sim.mj_model
    kd = {}
    for h in getattr(body, "passive_hooks", ()):
        if isinstance(h, CoupledSprings):
            for leg, K in h.K.items():
                kd.update(zip(h.dofs[leg].tolist(), np.diag(K).tolist()))
    n = 0
    for j in range(m.njnt):
        name = mj.mj_id2name(m, mj.mjtObj.mjOBJ_JOINT, j) or ""
        if m.jnt_type[j] != mj.mjtJoint.mjJNT_HINGE or name.count("tarsus") >= 2:
            continue
        if not any(f"{leg}_" in name for leg in ("lf", "lm", "lh", "rf", "rm", "rh")):
            continue
        dof = int(m.jnt_dofadr[j])
        m.dof_damping[dof] = tau_s * kd.get(dof, float(m.jnt_stiffness[j]))
        n += 1
    return n


def register(reg, body) -> dict[str, float]:
    """Organism entry point: read the switch from the registry and apply."""
    from .registry import Status
    c = reg.require("joint:leg", "damping", units="uN*mm*s/rad",
                    model_use="viscous damping of every leg hinge DOF (not the tarsal chain)",
                    subsystem="body_mechanics", minimal=1.0,
                    minimal_note="1 = unchanged flybody/NMF defaults (1; femur-tibia 0.4 scales "
                                 "with it); c/k ~1 s against the measured springs; guessed",
                    uncertainty="unmeasured; FlyMimic (Ozdil et al.) uses c/k = 0.05 s; "
                                "row b3_d_leg in data/model/parameters.csv")
    if c != 1.0:
        set_leg_damping(body, float(c))
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
        register_damping_source(reg, body)
        return {}
    k = apply(body, int(src))
    register_damping_source(reg, body)
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


COXA_TABLE = Path(__file__).resolve().parents[2] / "data" / "params" / "coxa_ranges_flybody.csv"


def apply_coxa_ranges(body) -> list[str]:
    """B2 (s12): flybody's leg-specific thorax-coxa ranges (absolute, inferred:
    set to admit grooming IK) in place of the joints.py envelopes (+-45/25/30
    deg about q0, assumed, on mislabelled axes; F-COXA-1)."""
    t = pd.read_csv(COXA_TABLE, comment="#")
    m = body.sim.mj_model
    pre = f"{body.fly.name}/"
    done = []
    for r in t.itertuples():
        j = mj.mj_name2id(m, mj.mjtObj.mjOBJ_JOINT, pre + r.joint)
        if j < 0:
            raise KeyError(r.joint)
        m.jnt_range[j] = (r.lo_rad, r.hi_rad)
        m.jnt_limited[j] = 1
        done.append(r.joint)
    return done


def register_coxa(reg, body) -> list[str]:
    src = reg.require("joint:coxa", "range_source", units="enum",
                      model_use="0 joints.py envelopes (+-45/25/30 deg, assumed, mislabelled axes), "
                                "1 flybody leg-specific ranges (data/params/coxa_ranges_flybody.csv; inferred)",
                      subsystem="body_mechanics", minimal=0,
                      minimal_note="legacy m4 envelopes; flybody ranges are an option (s12)")
    return apply_coxa_ranges(body) if int(src) else []


CTR_TABLE = COXA_TABLE.with_name("ctr_ranges.csv")


def apply_ctr_ranges(body) -> list[str]:
    """B2 (s12, F-COXA-2): coxa-trochanter pitch ranges per leg in place of the
    joints.py envelope (-100..100 deg, assumed). Lower bound at the fold, where the
    femur lies flat on the coxa (physical limit, derived from the model geometry);
    upper bound at the measured walking extension (Haustein 2024, figure-read),
    or the model's straightest reach where it falls short (hind legs)."""
    t = pd.read_csv(CTR_TABLE, comment="#")
    m = body.sim.mj_model
    pre = f"{body.fly.name}/"
    for r in t.itertuples():
        j = mj.mj_name2id(m, mj.mjtObj.mjOBJ_JOINT, pre + r.joint)
        if j < 0:
            raise KeyError(r.joint)
        m.jnt_range[j] = (r.lo_rad, r.hi_rad)
        m.jnt_limited[j] = 1
    return t.joint.tolist()


def register_ctr(reg, body) -> list[str]:
    src = reg.require("joint:ctr", "range_source", units="enum",
                      model_use="0 joints.py envelope (-100..100 deg, assumed), 1 fold to measured walking "
                                "extension per leg (data/params/ctr_ranges.csv; derived + figure-read; F-COXA-2)",
                      subsystem="body_mechanics", minimal=0,
                      minimal_note="legacy envelope; the fold-bounded range is an option (s12)")
    return apply_ctr_ranges(body) if int(src) else []


def register_rest(reg, body) -> int:
    ref = reg.require("joint:leg", "spring_reference", units="enum",
                      model_use="0 flybody neutral pose, 1 fitted to the eLife weighted protocol (F-REST-1), "
                                "2 refitted within flybody's coxa ranges (F-COXA-2; use with joint:coxa|range_source 1), "
                                "3 refitted within the fold-bounded CTr ranges (F-COXA-2; use with joint:ctr|range_source 1)",
                      subsystem="body_mechanics", minimal=0,
                      minimal_note="legacy m4 body; fitted references are a template option")
    if int(ref) == 2:
        return set_rest_angles(body, REST_TABLE_COXA)
    if int(ref) == 3:
        return set_rest_angles(body, REST_TABLE_CTR)
    return set_rest_angles(body) if int(ref) else 0


# Wing hinge rotational stiffness (s12, joint:wing|stiffness_source 1): 91 +- 9 pN*m/deg
# = 5.21 +- 0.52 uN*mm/rad, FITTED by Bergou, Ristroph, Guckenheimer, Cohen & Wang 2010
# (PRL 104:148101, Fig. 2a, 3) as a damped torsional spring to the wing-pitch torque from
# measured free-flight D. melanogaster kinematics. Pitch only and in flight; the yaw
# (stroke) and roll (deviation) hinges take the same value (inferred transfer: no
# Drosophila measurement of either, nor of the folded-wing hinge).
WING_STIFFNESS_BERGOU = 91e-12 * 180.0 / np.pi * 1e9     # pN*m/deg -> uN*mm/rad


def set_wing_stiffness(body, k: float) -> list[str]:
    m = body.sim.mj_model
    done = []
    for j in range(m.njnt):
        name = mj.mj_id2name(m, mj.mjtObj.mjOBJ_JOINT, j) or ""
        if m.jnt_type[j] == mj.mjtJoint.mjJNT_HINGE and "_wing-" in name:
            m.jnt_stiffness[j] = k
            done.append(name.split("/")[-1])
    return done


def register_wings(reg, body) -> list[str]:
    ref = reg.require("joint:wing", "spring_reference", units="enum",
                      model_use="0 flybody spread pose (outside the yaw range), 1 folded neutral pose",
                      subsystem="body_mechanics", minimal=0,
                      minimal_note="legacy m4 body; folded reference is an option until adopted")
    src = reg.require("joint:wing", "stiffness_source", units="enum",
                      model_use="0 flybody 1 uN*mm/rad (unsourced), 1 Bergou et al. 2010 wing-pitch stiffness "
                                "5.21 uN*mm/rad (fitted, in flight) on all three hinge axes (yaw, roll inferred)",
                      subsystem="body_mechanics", minimal=0,
                      minimal_note="flybody value; one spike swings a folded wing 30-40 deg (s12, F-WING-4)")
    if int(src):
        set_wing_stiffness(body, WING_STIFFNESS_BERGOU)
    return fold_wings(body) if int(ref) else []


def register_noslip(reg, body) -> int:
    """B6: MuJoCo's noslip pass (a per-step projection that removes contact slip).
    flybody's arena runs 3 iterations, which do not converge at 0.1 ms on the
    m9d legs: resting motion then changes with the step by up to 4x (F-DAMP-2).
    MJWarp, the GPU path for many flies, has no noslip and sets it to 0."""
    n = reg.require("contact:floor", "noslip_iterations", units="count",
                    model_use="MuJoCo option noslip_iterations; 3 flybody arena, 0 off (as MJWarp)",
                    subsystem="body_mechanics", minimal=3,
                    minimal_note="flybody arena default; not converged at 0.1 ms on m9d (F-DAMP-2)")
    body.sim.mj_model.opt.noslip_iterations = int(n)
    return int(n)


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
REST_TABLE_COXA = REST_TABLE.with_name("passive_leg_rest_fit_coxa_flybody.csv")
REST_TABLE_CTR = REST_TABLE.with_name("passive_leg_rest_fit_ctr.csv")


def set_rest_angles(body, table: Path = REST_TABLE) -> int:
    """B3 rest angles: spring references fitted to the eLife weighted protocol
    (F-REST-1; inferred). Updates MuJoCo's spring reference and any coupled
    spring hook. Returns the number of joints set."""
    t = pd.read_csv(table, comment="#")
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
