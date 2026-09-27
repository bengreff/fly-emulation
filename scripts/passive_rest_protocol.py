"""Replicate the eLife 2025 weighted-leg protocol in the model (B3 rest angles).

Wang et al. 2025 (PMC12324252): tethered fly, motor neurons silenced, a
0.19 mg wire (~20x rear-leg mass) glued to the distal tarsus, body rotated
through five angles from -30 to +30 deg; leg equilibria measured with the
paper's four angles (methods Eqs. 5-11):
  theta  levation-depression: femur projection in the transverse (x'z') plane vs z'
  phi    protraction-retraction: femur projection in the coronal (x'y') plane vs y' (0 = anterior)
  psi    extension-flexion: angle between femur and tibia vectors (0 = straight)
  gamma  pronation-supination: azimuth of the tibia about the femur (Eq. 11)
Figure 3C medians (right legs; digitised by eye, +-10 deg; loaded equilibria):
  pro 115/40/50/115, meso 110/90/60/120, meta 85/130/100/135 (theta/phi/psi/gamma).

The model's static equilibrium is found directly (thorax fixed, dead fly):
minimise spring + gravitational potential of the leg + the weight's potential
over the leg's hinge angles within their ranges. The rotation axis of the
body is not stated in the text; roll about the long axis is assumed.

    uv run python scripts/passive_rest_protocol.py            # compare current springs
    uv run python scripts/passive_rest_protocol.py --fit      # fit spring references
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import mujoco as mj
import numpy as np
from scipy.optimize import least_squares, minimize

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from flyemu import passive  # noqa: E402
from flyemu.body import Body  # noqa: E402

REPO = Path(__file__).resolve().parents[1]
MEASURED = {"rf": (115, 40, 50, 115), "rm": (110, 90, 60, 120), "rh": (85, 130, 100, 135)}
WEIGHT_MG = 0.19
BODY_ANGLES = (-30, -15, 0, 15, 30)
G = 9810.0                                  # mm/s^2


def paper_angles(pF_ctr, pF_fti, pT_titA, right: bool = True) -> np.ndarray:
    """theta, phi, psi, gamma (deg) in the thorax frame (x fwd, y left, z up)."""
    xp = np.array([0.0, -1.0, 0.0]) if right else np.array([0.0, 1.0, 0.0])  # toward the leg's side
    yp = np.array([1.0, 0.0, 0.0])
    zp = np.array([0.0, 0.0, 1.0])
    rF = pF_fti - pF_ctr
    rF /= np.linalg.norm(rF)
    rT = pT_titA - pF_fti
    rT /= np.linalg.norm(rT)
    xz = rF - (rF @ yp) * yp
    theta = np.degrees(np.arccos(np.clip(xz @ zp / np.linalg.norm(xz), -1, 1)))
    xy = rF - (rF @ zp) * zp
    phi = np.degrees(np.arccos(np.clip(xy @ yp / np.linalg.norm(xy), -1, 1)))
    psi = np.degrees(np.arccos(np.clip(rF @ rT, -1, 1)))
    z2 = rF
    y2 = np.cross(z2, zp)
    y2 /= np.linalg.norm(y2)
    x2 = np.cross(y2, z2)
    gamma = np.degrees(np.arctan2(rT @ y2, rT @ x2)) % 360
    return np.array([theta, phi, psi, gamma])


class Leg:
    def __init__(self, body: Body, leg: str):
        self.m, self.d = body.sim.mj_model, body.sim.mj_data
        m = self.m
        pre = body.fly.name + "/"
        self.j = [j for j in range(m.njnt) if m.jnt_type[j] == mj.mjtJoint.mjJNT_HINGE
                  and f"{leg}_" in (mj.mj_id2name(m, mj.mjtObj.mjOBJ_JOINT, j) or "")]
        self.names = [mj.mj_id2name(m, mj.mjtObj.mjOBJ_JOINT, j).split("/")[-1] for j in self.j]
        self.adr = np.array([m.jnt_qposadr[j] for j in self.j])
        self.k = m.jnt_stiffness[self.j].copy()
        self.lo, self.hi = m.jnt_range[self.j, 0].copy(), m.jnt_range[self.j, 1].copy()
        bid = lambda n: mj.mj_name2id(m, mj.mjtObj.mjOBJ_BODY, pre + n)  # noqa: E731
        self.b_ctr, self.b_fti = bid(f"{leg}_trochanterfemur"), bid(f"{leg}_tibia")
        self.b_tita, self.b_tip = bid(f"{leg}_tarsus1"), bid(f"{leg}_tarsus5")
        self.bodies = [i for i in range(m.nbody)
                       if (mj.mj_id2name(m, mj.mjtObj.mjOBJ_BODY, i) or "").startswith(pre + leg + "_")]
        self.q0 = self.d.qpos[self.adr].copy()
        self.ref = m.qpos_spring[self.adr].copy()

    def energy(self, q, gvec):
        d = self.d
        d.qpos[self.adr] = q
        mj.mj_kinematics(self.m, d)
        e = 0.5 * np.sum(self.k * (q - self.ref) ** 2)
        e -= np.sum(self.m.body_mass[self.bodies][:, None] * d.xipos[self.bodies] * gvec)
        e -= WEIGHT_MG * 1e-3 * (d.xpos[self.b_tip] @ gvec)
        return e

    def equilibrium(self, body_angle_deg: float) -> np.ndarray:
        a = np.radians(body_angle_deg)
        gvec = G * np.array([0.0, np.sin(a), -np.cos(a)])      # roll about the long axis
        r = minimize(self.energy, self.q0.copy(), args=(gvec,), method="L-BFGS-B",
                     bounds=list(zip(self.lo, self.hi)), options=dict(maxiter=500))
        self.d.qpos[self.adr] = r.x
        mj.mj_kinematics(self.m, self.d)
        d = self.d
        return paper_angles(d.xpos[self.b_ctr], d.xpos[self.b_fti], d.xpos[self.b_tita])

    def median_angles(self) -> np.ndarray:
        return np.median([self.equilibrium(a) for a in BODY_ANGLES], axis=0)


# gamma is not fitted: its convention (Eq. 11 axes and sign) is not verified,
# and every leg is off by a similar 50-75 deg, which suggests an offset.
# The coxa axes are functionally coupled and leg-dependent (joint_signs
# calibration; F-COXA-1), so all three coxa joints are free, with a small
# penalty (REG deg of angle error per deg of reference change) toward neutral.
FIT_DOFS = ("c_thorax-{L}_coxa-yaw", "c_thorax-{L}_coxa-roll", "c_thorax-{L}_coxa-pitch",
            "{L}_coxa-{L}_trochanterfemur-pitch", "{L}_trochanterfemur-{L}_tibia-pitch")
REG = 0.1
FIT_ANGLES = [0, 1, 2]                      # theta, phi, psi


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--fit", action="store_true")
    ap.add_argument("--source", type=int, default=1, help="passive stiffness source (1 = measured)")
    a = ap.parse_args()
    body = Body(vision=False)
    passive.apply(body, a.source)
    body.reset()
    mj.mj_forward(body.sim.mj_model, body.sim.mj_data)
    out = {}
    for L, meas in MEASURED.items():
        leg = Leg(body, L)
        before = leg.median_angles()
        row = dict(measured=meas, model_neutral_springs=before.round(1).tolist(),
                   err_deg=(before - meas).round(1).tolist())
        if a.fit:
            idx = [leg.names.index(t.format(L=L)) for t in FIT_DOFS]
            ref0 = leg.ref.copy()

            def resid(x):
                leg.ref = ref0.copy()
                leg.ref[idx] = x
                return np.concatenate([(leg.median_angles() - np.array(meas))[FIT_ANGLES],
                                       REG * np.degrees(x - ref0[idx])])
            r = least_squares(resid, ref0[idx], bounds=(leg.lo[idx], leg.hi[idx]),
                              diff_step=0.02, max_nfev=60)
            leg.ref = ref0.copy()
            leg.ref[idx] = r.x
            after = leg.median_angles()
            row.update(fit_dofs=[leg.names[i] for i in idx],
                       spring_ref_rad=r.x.round(4).tolist(),
                       spring_ref_change_deg=np.degrees(r.x - ref0[idx]).round(1).tolist(),
                       model_fitted=after.round(1).tolist(),
                       err_fitted_deg=(after - meas).round(1).tolist(),
                       at_range_limit=[bool(abs(v - leg.lo[i]) < 1e-3 or abs(v - leg.hi[i]) < 1e-3)
                                       for v, i in zip(r.x, idx)])
        out[L] = row
        print(L, json.dumps(row))
    dst = REPO / "runs" / "s9_passive_rest"
    dst.mkdir(parents=True, exist_ok=True)
    (dst / ("fit.json" if a.fit else "compare.json")).write_text(json.dumps(out, indent=1))


if __name__ == "__main__":
    main()
