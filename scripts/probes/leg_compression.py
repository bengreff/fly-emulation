"""Whole-leg compression stiffness of the model's passive leg (B3 held-out check; B26 data-first).

Oeftger, Moussian & Lehmann 2026 (iScience 29:116404) pushed the left middle leg of decapitated living
flies against a force wire and report the strut stiffness from coxa to pretarsus: 13.1 +- 7.97 uN/mm
(wild type, n 11). This probe builds the body only, with the working profile's body switches set as the
organism sets them, holds the thorax fixed in the air, keeps every actuator at zero (passive leg, no
tone), and pushes the left middle leg's tarsus5 body toward the thorax-coxa joint in force steps.

Units are flybody's: g, mm, s, so force is uN and torque uN*mm. The strut runs from the lm_coxa body
origin (the thorax-coxa joint) to the lm_tarsus5 body origin (the pretarsus is not a separate body;
tarsus5 is the last segment, so this is short of the tip by tarsus5's length, inferred to be small).

    uv run python scripts/probes/leg_compression.py --out runs/s12/legk/m9r
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import mujoco as mj
import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))
from flyemu import passive, profiles, stubs  # noqa: E402
from flyemu.body import Body  # noqa: E402
from flyemu.profiles import WORKING_PROFILE  # noqa: E402
from flyemu.registry import Registry  # noqa: E402

STEPS_UN = [0.25, 0.5, 1.0, 2.0, 4.0, 8.0, 12.0]
ANGLES = {"coxa_trochanter": "lm_coxa-lm_trochanterfemur-pitch",
          "femur_tibia": "lm_trochanterfemur-lm_tibia-pitch",
          "tibia_tarsus": "lm_tibia-lm_tarsus1-pitch"}


def build(profile: str, overrides: dict) -> Body:
    reg = Registry("minimal")
    reg.overrides.update(overrides)
    if profile:
        profiles.apply(reg, profile)
    stubs.read(reg)
    body = Body(timestep=1e-4)
    passive.register(reg, body)
    passive.register_coxa(reg, body)
    passive.register_ctr(reg, body)
    passive.register_rest(reg, body)
    passive.register_wings(reg, body)
    passive.register_noslip(reg, body)
    return body


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--profile", default=WORKING_PROFILE)
    ap.add_argument("--set", action="append", default=[])
    ap.add_argument("--hold-s", type=float, default=0.4)
    ap.add_argument("--unload-s", type=float, default=1.0)
    ap.add_argument("--settle-s", type=float, default=1.5)
    ap.add_argument("--solo", action="store_true",
                    help="other legs collide with nothing (the experiment removed every leg but the left middle)")
    ap.add_argument("--lock-tarsi", action="store_true",
                    help="hold tibia-tarsus and the tarsal chain at their settled angles (the tarsus lies on "
                         "the wire in the experiment; bracket against the free tarsus)")
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    ov = {k: float(v) for k, v in (s.rsplit("=", 1) for s in a.set)}
    body = build(a.profile, ov)
    m, d = body.sim.mj_model, body.sim.mj_data
    pre = f"{body.fly.name}/"
    bid = {n: mj.mj_name2id(m, mj.mjtObj.mjOBJ_BODY, pre + n) for n in ("lm_coxa", "lm_tarsus5")}
    qadr = {k: m.jnt_qposadr[mj.mj_name2id(m, mj.mjtObj.mjOBJ_JOINT, pre + v)] for k, v in ANGLES.items()}
    free = [j for j in range(m.njnt) if m.jnt_type[j] == mj.mjtJoint.mjJNT_FREE][0]
    fq, fv = m.jnt_qposadr[free], m.jnt_dofadr[free]
    if a.solo:
        for g in range(m.ngeom):
            nm = mj.mj_id2name(m, mj.mjtObj.mjOBJ_BODY, m.geom_bodyid[g]) or ""
            if any(nm.startswith(pre + leg + "_") for leg in ("lf", "lh", "rf", "rm", "rh")):
                m.geom_contype[g] = 0
                m.geom_conaffinity[g] = 0
    d.qpos[fq + 2] += 5.0                       # 5 mm up: no floor contact
    mj.mj_forward(m, d)
    hold = d.qpos[fq:fq + 7].copy()
    d.ctrl[:] = 0.0
    n_hold = int(a.hold_s / m.opt.timestep)
    hooks = list(getattr(body, "passive_hooks", ()))
    lm_geom = np.array([(mj.mj_id2name(m, mj.mjtObj.mjOBJ_BODY, m.geom_bodyid[g]) or "").startswith(pre + "lm_")
                        for g in range(m.ngeom)])
    warn0 = int(sum(w.number for w in d.warning))

    def run(n: int, f_un: float) -> None:
        for _ in range(n):
            tip, cox = d.xpos[bid["lm_tarsus5"]], d.xpos[bid["lm_coxa"]]
            u = (cox - tip) / np.linalg.norm(cox - tip)
            d.xfrc_applied[:] = 0.0
            d.xfrc_applied[bid["lm_tarsus5"], :3] = f_un * u
            d.ctrl[:] = 0.0
            for hook in hooks:                  # coupled leg springs (B3 source 2) write qfrc_applied
                hook(d)
            mj.mj_step(m, d)
            d.qpos[fq:fq + 7] = hold            # thorax glued
            d.qvel[fv:fv + 6] = 0.0

    def sample(f_un: float) -> dict:
        mj.mj_forward(m, d)
        L = float(np.linalg.norm(d.xpos[bid["lm_tarsus5"]] - d.xpos[bid["lm_coxa"]]))
        return {"force_uN": f_un, "strut_mm": round(L, 5),
                **{k: round(float(np.degrees(d.qpos[q])), 3) for k, q in qadr.items()},
                "max_qvel": round(float(np.abs(d.qvel).max()), 4),
                "contacts_lm": int(sum(1 for c in d.contact[:d.ncon]
                                       if lm_geom[c.geom1] or lm_geom[c.geom2]))}

    run(int(a.settle_s / m.opt.timestep), 0.0)
    if a.lock_tarsi:
        for j in range(m.njnt):
            nm = mj.mj_id2name(m, mj.mjtObj.mjOBJ_JOINT, j) or ""
            if "lm_tarsus" in nm:
                m.jnt_stiffness[j] = 1e4
                m.qpos_spring[m.jnt_qposadr[j]] = d.qpos[m.jnt_qposadr[j]]
                m.dof_damping[m.jnt_dofadr[j]] = 10.0
        run(int(0.2 / m.opt.timestep), 0.0)
    rows = [sample(0.0)]
    for f in STEPS_UN:
        run(n_hold, f)
        rows.append(sample(f))
    run(int(a.unload_s / m.opt.timestep), 0.0)
    pairs = sorted({tuple(sorted((mj.mj_id2name(m, mj.mjtObj.mjOBJ_BODY, m.geom_bodyid[c.geom1]),
                                  mj.mj_id2name(m, mj.mjtObj.mjOBJ_BODY, m.geom_bodyid[c.geom2]))))
                    for c in d.contact[:d.ncon] if lm_geom[c.geom1] or lm_geom[c.geom2]})
    rows.append({**sample(0.0), "unloaded": True, "contact_pairs": [" / ".join(p_).replace(pre, "") for p_ in pairs]})
    L0 = rows[0]["strut_mm"]
    for r in rows:
        r["compression_mm"] = round(L0 - r["strut_mm"], 5)
        r["secant_uN_per_mm"] = (round(r["force_uN"] / r["compression_mm"], 3)
                                 if r["force_uN"] and r["compression_mm"] > 0 else None)
    ranges = {k: [round(float(np.degrees(x)), 1) for x in
                  m.jnt_range[mj.mj_name2id(m, mj.mjtObj.mjOBJ_JOINT, pre + v)]] for k, v in ANGLES.items()}
    out = {"profile": a.profile, "overrides": ov, "hold_s": a.hold_s, "unload_s": a.unload_s,
           "settle_s": a.settle_s, "lock_tarsi": a.lock_tarsi, "solo": a.solo,
           "passive_hooks": len(hooks), "strut_rest_mm": L0,
           "joint_range_deg": ranges, "mujoco_warnings": int(sum(w.number for w in d.warning)) - warn0,
           "nan": bool(np.isnan(d.qpos).any()), "rows": rows}
    Path(a.out).parent.mkdir(parents=True, exist_ok=True)
    with open(a.out + ".json", "w") as fh:
        json.dump(out, fh, indent=1)
    for r in rows:
        print(r)
    print({k: out[k] for k in ("strut_rest_mm", "joint_range_deg", "mujoco_warnings", "nan")})


if __name__ == "__main__":
    main()
