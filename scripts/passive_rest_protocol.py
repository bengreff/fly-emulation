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
    uv run python scripts/passive_rest_protocol.py --fit --coxa-flybody   # within flybody coxa ranges (s12)
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import mujoco as mj
import numpy as np
import pandas as pd
from scipy.optimize import least_squares, minimize

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from flyemu import passive  # noqa: E402
from flyemu.legangles import paper_angles  # noqa: E402,F401
from flyemu.body import Body  # noqa: E402

REPO = Path(__file__).resolve().parents[1]
MEASURED = {"rf": (115, 40, 50, 115), "rm": (110, 90, 60, 120), "rh": (85, 130, 100, 135)}
# the fly is taken as mirror-symmetric: left legs get the same targets
MEASURED.update({"l" + k[1:]: v for k, v in list(MEASURED.items())})
WEIGHT_MG = 0.19
BODY_ANGLES = (-30, -15, 0, 15, 30)
G = 9810.0                                  # mm/s^2


class Leg:
    def __init__(self, body: Body, leg: str):
        self.m, self.d = body.sim.mj_model, body.sim.mj_data
        self.right = leg.startswith("r")
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
        # coupled springs (passive.CoupledSprings) on a subset of this leg's hinges
        self.Kc, self.ci = None, None
        for h in getattr(body, "passive_hooks", ()):
            if hasattr(h, "K") and leg in h.K:
                self.Kc = h.K[leg]
                self.ci = np.array([list(self.adr).index(a) for a in h.qadr[leg]])

    def energy(self, q, gvec):
        d = self.d
        d.qpos[self.adr] = q
        mj.mj_kinematics(self.m, d)
        e = 0.5 * np.sum(self.k * (q - self.ref) ** 2)
        if self.Kc is not None:
            dq = (q - self.ref)[self.ci]
            e += 0.5 * dq @ self.Kc @ dq
        e -= np.sum(self.m.body_mass[self.bodies][:, None] * d.xipos[self.bodies] * gvec)
        e -= WEIGHT_MG * 1e-3 * (d.xpos[self.b_tip] @ gvec)
        return e

    def equilibrium(self, body_angle_deg: float) -> np.ndarray:
        a = np.radians(body_angle_deg)
        gvec = G * np.array([0.0, np.sin(a), -np.cos(a)])      # roll about the long axis
        # energies are ~1e-3 (uN*mm); scale so the optimiser's tolerances bite
        r = minimize(lambda q: 1e4 * self.energy(q, gvec), self.q0.copy(), method="L-BFGS-B",
                     bounds=list(zip(self.lo, self.hi)),
                     options=dict(maxiter=2000, ftol=1e-14, gtol=1e-10))
        self.last_converged = bool(r.success)
        self.d.qpos[self.adr] = r.x
        mj.mj_kinematics(self.m, self.d)
        d = self.d
        return paper_angles(d.xpos[self.b_ctr], d.xpos[self.b_fti], d.xpos[self.b_tita],
                            right=self.right)

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
    ap.add_argument("--coxa-flybody", action="store_true",
                    help="s12: fit within flybody's leg-specific coxa ranges (passive.apply_coxa_ranges)")
    ap.add_argument("--source", type=int, default=2,
                    help="passive stiffness source (1 = name mapping, 2 = coupled projection)")
    a = ap.parse_args()
    body = Body(vision=False)
    if a.source == 2:
        passive.apply_coupled(body)
    else:
        passive.apply(body, a.source)
    if a.coxa_flybody:
        passive.apply_coxa_ranges(body)
    body.reset()
    mj.mj_forward(body.sim.mj_model, body.sim.mj_data)
    out, solved = {}, {}
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
            # multi-start: neutral, and (left legs) the mirror leg's solution;
            # an equilibrium on a joint limit has no gradient, so one start can stick
            starts = [ref0[idx]]
            mirror = "r" + L[1:]
            if L.startswith("l") and mirror in solved:
                starts.append(np.clip(solved[mirror], leg.lo[idx] + 1e-6, leg.hi[idx] - 1e-6))
            if a.coxa_flybody:                  # s12: also start from the s9 fit, clipped into range
                s9 = pd.read_csv(passive.REST_TABLE, comment="#").set_index(["leg", "joint"])
                x9 = np.array([s9.loc[(L, leg.names[i]), "spring_ref_rad"] for i in idx], dtype=float)
                starts.append(np.clip(x9, leg.lo[idx] + 1e-6, leg.hi[idx] - 1e-6))
            # s12: trf stalls at the neutral start under the flybody coxa ranges (every
            # trust-region step rejected; the neutral equilibrium sits on a coxa limit),
            # so dogbox is tried from every start too and the lower cost is kept
            fits = [least_squares(resid, x0, bounds=(leg.lo[idx], leg.hi[idx]),
                                  diff_step=0.02, max_nfev=60, method=meth)
                    for x0 in starts for meth in (("trf", "dogbox") if a.coxa_flybody else ("trf",))]
            r = min(fits, key=lambda f: f.cost)
            solved[L] = r.x
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
    dst = REPO / "runs" / ("s12_passive_rest_coxa_flybody" if a.coxa_flybody else "s9_passive_rest")
    dst.mkdir(parents=True, exist_ok=True)
    (dst / ("fit.json" if a.fit else "compare.json")).write_text(json.dumps(out, indent=1))


if __name__ == "__main__":
    main()
