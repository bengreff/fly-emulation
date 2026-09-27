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
                      model_use="0 flybody defaults (1 uN*mm/rad), 1 measured (eLife 2025)",
                      subsystem="body_mechanics", minimal=0,
                      minimal_note="legacy m4 body; measured values are an option until adopted")
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


def register_wings(reg, body) -> list[str]:
    ref = reg.require("joint:wing", "spring_reference", units="enum",
                      model_use="0 flybody spread pose (outside the yaw range), 1 folded neutral pose",
                      subsystem="body_mechanics", minimal=0,
                      minimal_note="legacy m4 body; folded reference is an option until adopted")
    return fold_wings(body) if int(ref) else []
