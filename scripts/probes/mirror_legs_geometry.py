"""Left/right leg geometry at flybody's neutral pose and the coupled leg stiffness built from it
(passive.projected_matrices: K = J^T diag(K_eLife) J, J at the neutral pose). Follow-up to
mirror_audit.py, which found the derived leg damping (tau x diag K) differing left from right by
up to 10%. Reports, per leg pair: neutral hinge angles, world keypoints (CTr, FTi, TiTa, tip)
against the mirror image of the left leg, segment lengths, and the relative difference of K.

    uv run python scripts/probes/mirror_legs_geometry.py
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import mujoco as mj
import numpy as np

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "src"))
sys.path.insert(0, str(REPO / "scripts"))
M = np.diag([1.0, -1.0, 1.0])


def main() -> None:
    from passive_rest_protocol import Leg

    from flyemu import passive
    from flyemu.body import Body
    b = Body(vision=False)
    b.reset()
    m, d = b.sim.mj_model, b.sim.mj_data
    mj.mj_forward(m, d)
    th = mj.mj_name2id(m, mj.mjtObj.mjOBJ_BODY, b.fly.name + "/c_thorax")
    R0, p0 = d.xmat[th].reshape(3, 3), d.xpos[th].copy()

    def local(p):                       # thorax frame, so the check does not depend on placement
        return R0.T @ (p - p0)
    Ks, _, names, _ = passive.projected_matrices(b)
    out = {}
    for seg in "fmh":
        L, R = Leg(b, f"l{seg}"), Leg(b, f"r{seg}")
        kp = {}
        for k in ("b_ctr", "b_fti", "b_tita", "b_tip"):
            pl, pr = local(d.xpos[getattr(L, k)]), local(d.xpos[getattr(R, k)])
            kp[k] = dict(left_mm=np.round(pl, 4).tolist(), right_mirrored_mm=np.round(M @ pr, 4).tolist(),
                         diff_um=round(float(np.linalg.norm(pl - M @ pr) * 1e3), 1))
        seglen = {}
        for a, c in (("b_ctr", "b_fti"), ("b_fti", "b_tita"), ("b_tita", "b_tip")):
            ll = np.linalg.norm(d.xpos[getattr(L, a)] - d.xpos[getattr(L, c)])
            lr = np.linalg.norm(d.xpos[getattr(R, a)] - d.xpos[getattr(R, c)])
            seglen[f"{a[2:]}-{c[2:]}"] = [round(float(ll) * 1e3, 1), round(float(lr) * 1e3, 1)]
        KL, KR = Ks[f"l{seg}"], Ks[f"r{seg}"]
        out[f"{seg}"] = dict(
            neutral_q_deg=dict(zip([n.replace(f"l{seg}_", "*_").replace(f"-l{seg}", "-*") for n in L.names],
                                   zip(np.round(np.degrees(d.qpos[L.adr]), 2).tolist(),
                                       np.round(np.degrees(d.qpos[R.adr]), 2).tolist()))),
            keypoints=kp, segment_length_um_left_right=seglen,
            K_rel_diff=round(float(np.linalg.norm(KL - KR) / np.linalg.norm(KR)), 4),
            K_diag_left=np.round(np.diag(KL), 4).tolist(), K_diag_right=np.round(np.diag(KR), 4).tolist(),
            K_joints=names[f"r{seg}"])
    p = REPO / "runs" / "s12" / "stand3" / "mirror_legs_geometry.json"
    p.write_text(json.dumps(out, indent=1))
    for seg, r in out.items():
        print(seg, "K_rel_diff", r["K_rel_diff"], "keypoint diff um", {k: v["diff_um"] for k, v in r["keypoints"].items()},
              "seglen", r["segment_length_um_left_right"])
        print("   K diag L", r["K_diag_left"], "\n   K diag R", r["K_diag_right"])
        print("   neutral q differing:", {k: v for k, v in r["neutral_q_deg"].items() if abs(v[0] - v[1]) > 0.05})


if __name__ == "__main__":
    main()
