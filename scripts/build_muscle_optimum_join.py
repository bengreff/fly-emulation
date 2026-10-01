"""Join FlyMimic muscle optimal lengths to flybody joint angles by anatomy (s11).

leg_muscles.csv (session 9) took FlyMimic's moment arms and optimal lengths
but placed every muscle's optimum (normalised length 1) at the flybody zero
pose. FlyMimic (NeuroMechFly skeleton) and flybody use different joint zeros
and ranges, so that put the strong tibia extensor at a force-length gain of
0.1-0.3 in the working posture (DECISIONS s11, 19:26).

Here the optimum is carried across as an anatomical angle:
  1. in FlyMimic at its keyframe, each muscle's joint angle at L = 1 is
     q_key + (1 - L_key) L0 / arm (that joint alone, linear in the arm);
  2. that pose's interior angle between segments is measured from body
     positions (femur-tibia: femur axis vs tibia axis; coxa-trochanter:
     coxa axis vs femur axis);
  3. pooled per (flybody DOF, direction) as the F0-weighted mean;
  4. in flybody, per leg, the joint angle giving that interior angle (others
     at the zero pose) is found by scanning the joint range.
Only the two DOFs whose FlyMimic mapping is derived (coxa-trochanter pitch,
femur-tibia pitch) are joined; the rest keep the zero pose (guessed). The
front leg is derived; mid and hind legs copy the front-leg optimum as an
interior angle (guessed: FlyMimic has no mid/hind muscles).

    uv run python scripts/build_muscle_optimum_join.py
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

import mujoco as mj
import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "src"))
sys.path.insert(0, str(REPO / "scripts"))
from build_leg_muscles import MAP, XML  # noqa: E402

OUT = REPO / "data" / "derived" / "leg_muscle_optimum_join.csv"
FM_CHAIN = {"Tibia_pitch": ("LFTrochanter", "LFTibia", "LFTarsus1"),
            "Trochanter_pitch": ("LFCoxa", "LFTrochanter", "LFTibia")}
FB_CHAIN = {"Tibia_pitch": ("{L}_trochanterfemur", "{L}_tibia", "{L}_tarsus1"),
            "Trochanter_pitch": ("{L}_coxa", "{L}_trochanterfemur", "{L}_tibia")}


def interior(m, d, names) -> float:
    """Angle (rad) between segment a->b and segment b->c; 0 = straight."""
    p = [d.xpos[mj.mj_name2id(m, mj.mjtObj.mjOBJ_BODY, n)] for n in names]
    u, v = p[1] - p[0], p[2] - p[1]
    return float(np.arccos(np.clip(u @ v / np.linalg.norm(u) / np.linalg.norm(v), -1, 1)))


def flymimic_optima() -> pd.DataFrame:
    s = XML.read_text()
    s = re.sub(r"<mesh [^>]*/>", "", s)
    s = re.sub(r'<geom [^>]*mesh="[^"]*"[^>]*/>', "", s)
    m = mj.MjModel.from_xml_string(s)
    d = mj.MjData(m)
    mj.mj_resetDataKeyframe(m, d, 0)
    mj.mj_forward(m, d)
    key = d.qpos.copy()
    mom = np.zeros((m.nu, m.nv))
    mj.mju_sparse2dense(mom, d.actuator_moment, d.moment_rownnz, d.moment_rowadr, d.moment_colind)
    rows = []
    for a in range(m.nu):
        g, lr = m.actuator_gainprm[a], m.actuator_lengthrange[a]
        L0 = (lr[1] - lr[0]) / (g[1] - g[0])
        Lkey = g[0] + (d.actuator_length[a] - lr[0]) / L0
        for fm in FM_CHAIN:
            j = mj.mj_name2id(m, mj.mjtObj.mjOBJ_JOINT, f"joint_LF{fm}")
            arm = mom[a, m.jnt_dofadr[j]]
            if abs(arm) <= 1e-6:
                continue
            q_opt = key[m.jnt_qposadr[j]] + (1.0 - Lkey) * L0 / arm
            th_key = interior(m, d, FM_CHAIN[fm])
            d.qpos[:] = key
            d.qpos[m.jnt_qposadr[j]] = q_opt
            mj.mj_kinematics(m, d)
            th_opt = interior(m, d, FM_CHAIN[fm])
            d.qpos[:] = key
            mj.mj_kinematics(m, d)
            rows.append(dict(muscle=mj.mj_id2name(m, mj.mjtObj.mjOBJ_ACTUATOR, a), fm_joint=fm,
                             arm_mm=arm, F0_uN=g[2], L_key=Lkey, q_key=key[m.jnt_qposadr[j]],
                             q_opt_fm=q_opt, theta_key=th_key, theta_opt=th_opt))
    return pd.DataFrame(rows)


def main() -> None:
    from flyemu.body import Body
    fm = flymimic_optima()
    b = Body(vision=False)
    m, d = b.sim.mj_model, b.sim.mj_data
    pre = b.fly.name + "/"
    out = []
    for fmj, chain in FB_CHAIN.items():
        tmpl, sgn, _ = MAP[fmj]
        for fm_dir in (+1, -1):
            g = fm[(fm.fm_joint == fmj) & (np.sign(fm.arm_mm) == fm_dir)]
            th = float((g.F0_uN * g.theta_opt).sum() / g.F0_uN.sum())
            for side in "lr":
                for seg in "fmh":
                    L = f"{side}{seg}"
                    j = mj.mj_name2id(m, mj.mjtObj.mjOBJ_JOINT, pre + tmpl.format(L=L))
                    qa = m.jnt_qposadr[j]
                    lo, hi = m.jnt_range[j]
                    qs = np.linspace(lo, hi, 701)
                    ths = []
                    for q in qs:
                        d.qpos[:] = m.qpos0
                        d.qpos[qa] = q
                        mj.mj_kinematics(m, d)
                        ths.append(interior(m, d, [pre + c.format(L=L) for c in chain]))
                    ths = np.array(ths)
                    # the unsigned angle folds at its extrema: match only on the
                    # monotonic branch of theta(q) that contains the zero pose
                    k0 = int(np.argmin(np.abs(qs - m.qpos0[qa])))
                    dth = np.sign(np.diff(ths))
                    lo_k = k0
                    while lo_k > 0 and dth[lo_k - 1] == dth[min(k0, len(dth) - 1)]:
                        lo_k -= 1
                    hi_k = k0
                    while hi_k < len(dth) and dth[hi_k] == dth[min(k0, len(dth) - 1)]:
                        hi_k += 1
                    k = lo_k + int(np.argmin(np.abs(ths[lo_k:hi_k + 1] - th)))
                    d.qpos[:] = m.qpos0
                    mj.mj_kinematics(m, d)
                    out.append(dict(joint=tmpl.format(L=L), direction=fm_dir * sgn,
                                    theta_opt_deg=round(np.degrees(th), 1),
                                    theta_zero_pose_deg=round(np.degrees(interior(m, d, [pre + c.format(L=L) for c in chain])), 1),
                                    q_opt_rad=round(float(qs[k]), 3),
                                    branch_deg=f"{np.degrees(ths[lo_k]):.0f}-{np.degrees(ths[hi_k]):.0f}",
                                    match_err_deg=round(float(np.degrees(abs(ths[k] - th))), 1),
                                    n_flymimic=len(g), label="derived" if seg == "f" else "guessed",
                                    basis="FlyMimic keyframe optimum as an interior angle (front leg)" if seg == "f"
                                    else "front-leg interior angle copied (FlyMimic has no mid/hind muscles)"))
    df = pd.DataFrame(out)
    OUT.parent.mkdir(parents=True, exist_ok=True)
    with open(OUT, "w") as f:
        f.write("# Muscle optimum (normalised length 1) per flybody DOF and direction, joined from FlyMimic by "
                "interior segment angle. Built by scripts/build_muscle_optimum_join.py (session 11). q_opt_rad "
                "in flybody joint coordinates; DOFs not listed keep the zero pose.\n")
        df.to_csv(f, index=False)
    print(fm[["muscle", "fm_joint", "L_key", "q_key", "q_opt_fm", "theta_key", "theta_opt"]].round(3).to_string())
    print(df[df.joint.str.contains("lf_|lm_")].to_string())


if __name__ == "__main__":
    main()
