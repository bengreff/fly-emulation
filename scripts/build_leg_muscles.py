"""Build data/params/leg_muscles.csv: one antagonist Hill-muscle pair per flybody
leg DOF (B4; Ben s9: antagonist pairs on flybody, FlyMimic parameters where the
joints correspond).

FlyMimic's 15 front-leg MTUs (flygym asset; data/params/flymimic_mtu.csv) are
compiled without meshes and their moment arms read at the model keyframe. Each
FlyMimic joint maps to a flybody DOF by joint-axis geometry and muscle function
(session 9 log):
    Coxa_pitch (lateral axis, promotor/remotor)  -> c_thorax-XX_coxa-yaw
    Coxa_roll  (coxa long axis)                  -> c_thorax-XX_coxa-roll
    Coxa_yaw   (fore-aft axis, adductor)         -> c_thorax-XX_coxa-pitch
    Trochanter_pitch (tr flexors/extensors)      -> XX_coxa-XX_trochanterfemur-pitch
    Trochanter_roll                              -> XX_coxa-XX_trochanterfemur-roll
    Tibia_pitch (ti flexor/extensor)             -> XX_trochanterfemur-XX_tibia-pitch
Per DOF and direction, the muscles whose arm has that sign are pooled:
F0 = sum F0_i, r = sum F0_i |arm_i| / F0, L0 = F0-weighted mean optimal length.
Direction in flybody coordinates: FTi and CTr use the calibrated flexor sign
(Ti flexor and Tr flexor act at -1 in joint_signs; FlyMimic flexor arms are
-/+ respectively); coxa and femur-roll directions are guessed (FlyMimic + ->
flybody +). Mid/hind legs and tibia-tarsus copy the front-leg values
(guessed); passive muscle force (fpmax) is 0 because the measured joint
springs (B3, eLife 2025) are the whole joint's passive torque.

    uv run python scripts/build_leg_muscles.py
"""
from __future__ import annotations

import re
from pathlib import Path

import mujoco as mj
import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[1]
XML = REPO / ".venv/lib/python3.12/site-packages/flygym/assets/model/musculoskeletal/best_combined_arm_damping_stiff_cvt3.xml"
OUT = REPO / "data" / "params" / "leg_muscles.csv"

MAP = {  # FlyMimic joint -> (flybody DOF template, flybody sign of FlyMimic +, basis)
    "Coxa_pitch": ("c_thorax-{L}_coxa-yaw", +1, "guessed"),
    "Coxa_roll": ("c_thorax-{L}_coxa-roll", +1, "guessed"),
    "Coxa_yaw": ("c_thorax-{L}_coxa-pitch", +1, "guessed"),
    "Trochanter_pitch": ("{L}_coxa-{L}_trochanterfemur-pitch", -1, "derived"),   # flexors +arm; Tr flexor = -1
    "Trochanter_roll": ("{L}_coxa-{L}_trochanterfemur-roll", +1, "guessed"),
    "Tibia_pitch": ("{L}_trochanterfemur-{L}_tibia-pitch", +1, "derived"),       # flexor -arm; Ti flexor = -1
}
DEFAULT_SHAPE = dict(lmin=0.5, lmax=1.6, vmax=10.0, fvmax=1.4, fpmax=0.0)


def flymimic_arms() -> pd.DataFrame:
    s = XML.read_text()
    s = re.sub(r"<mesh [^>]*/>", "", s)
    s = re.sub(r'<geom [^>]*mesh="[^"]*"[^>]*/>', "", s)
    m = mj.MjModel.from_xml_string(s)
    d = mj.MjData(m)
    if m.nkey:
        mj.mj_resetDataKeyframe(m, d, 0)
    mj.mj_forward(m, d)
    mom = np.zeros((m.nu, m.nv))
    mj.mju_sparse2dense(mom, d.actuator_moment, d.moment_rownnz, d.moment_rowadr, d.moment_colind)
    rows = []
    for a in range(m.nu):
        g = m.actuator_gainprm[a]
        lr = m.actuator_lengthrange[a]
        L0 = (lr[1] - lr[0]) / (g[1] - g[0])
        for j in range(m.njnt):
            jn = mj.mj_id2name(m, mj.mjtObj.mjOBJ_JOINT, j) or ""
            key = jn.removeprefix("joint_LF")
            arm = mom[a, m.jnt_dofadr[j]]
            if key in MAP and abs(arm) > 1e-6:
                rows.append(dict(muscle=mj.mj_id2name(m, mj.mjtObj.mjOBJ_ACTUATOR, a),
                                 fm_joint=key, arm_mm=arm, F0_uN=g[2], L0_mm=L0))
    return pd.DataFrame(rows)


def main() -> None:
    arms = flymimic_arms()
    pairs = []
    for key, (tmpl, sgn, basis) in MAP.items():
        a = arms[arms.fm_joint == key]
        for fm_dir in (+1, -1):
            g = a[np.sign(a.arm_mm) == fm_dir]
            F0 = g.F0_uN.sum()
            r = (g.F0_uN * g.arm_mm.abs()).sum() / F0
            L0 = (g.F0_uN * g.L0_mm).sum() / F0
            pairs.append(dict(dof=tmpl, direction=fm_dir * sgn, F0_uN=round(F0, 3), r_mm=round(r, 5),
                              L0_mm=round(L0, 4), n_flymimic=len(g), members=";".join(g.muscle),
                              dir_basis=basis))
    rows = []
    for side in "lr":
        for seg, lab in (("f", "derived"), ("m", "guessed"), ("h", "guessed")):
            L = f"{side}{seg}"
            for p in pairs:
                src = ("FlyMimic front leg pooled (derived)" if seg == "f"
                       else "copy of the front-leg pair (guessed; FlyMimic mid/hind unfitted)")
                rows.append(dict(joint=p["dof"].format(L=L), direction=p["direction"], F0_uN=p["F0_uN"],
                                 r_mm=p["r_mm"], L0_mm=p["L0_mm"], **DEFAULT_SHAPE,
                                 label=lab if seg == "f" else "guessed", direction_basis=p["dir_basis"],
                                 source=src, flymimic_members=p["members"]))
            for direction in (+1, -1):   # tibia-tarsus: no FlyMimic muscle
                rows.append(dict(joint=f"{L}_tibia-{L}_tarsus1-pitch", direction=direction, F0_uN=20.0,
                                 r_mm=0.01, L0_mm=0.1, **DEFAULT_SHAPE, label="guessed",
                                 direction_basis="guessed", source="no FlyMimic tarsal muscle; placeholder",
                                 flymimic_members=""))
    df = pd.DataFrame(rows)
    with open(OUT, "w") as f:
        f.write("# Antagonist Hill-muscle pairs per flybody leg DOF (B4). Built by scripts/build_leg_muscles.py "
                "from FlyMimic (arXiv 2509.06426) moment arms; F0 in uN, r and L0 in mm; MuJoCo muscle curve "
                "semantics (lmin, lmax, vmax in L0/s, fvmax); fpmax 0 (passive torque is B3). Session 9.\n")
        df.to_csv(f, index=False)
    front = df[df.joint.str.contains("lf_")]
    print(front[["joint", "direction", "F0_uN", "r_mm", "L0_mm", "direction_basis"]].to_string())
    print(len(df), "rows ->", OUT)


if __name__ == "__main__":
    main()
