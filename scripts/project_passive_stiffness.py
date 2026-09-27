"""Project the eLife 2025 joint stiffness onto flybody's leg joints (F-COXA-1).

The paper reports a stiffness K_a for each of its four leg angles a (theta,
phi, psi, gamma; passive torque = K_a x deviation of angle a). With J the
Jacobian of those angles with respect to flybody's hinge angles at the neutral
pose, the passive energy 0.5 da^T K da = 0.5 dq^T (J^T K J) dq, so the joint
stiffness matrix is J^T K J. MuJoCo takes one stiffness per joint, so the
diagonal is used; the off-diagonal share is reported.

Compares with the name mapping in passive.py (retpro->coxa yaw, prosup->coxa
roll, levdep->CTr pitch, extflex->FTi pitch) and writes
data/derived/passive_leg_stiffness_projected.csv (derived; right legs).

    uv run python scripts/project_passive_stiffness.py
"""
from __future__ import annotations

import sys
from pathlib import Path

import mujoco as mj
import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "src"))
sys.path.insert(0, str(REPO / "scripts"))

from flyemu import passive  # noqa: E402
from flyemu.body import Body  # noqa: E402
from passive_rest_protocol import Leg, paper_angles  # noqa: E402

ORDER = ("levdep", "retpro", "extflex", "prosup")   # theta, phi, psi, gamma
LEGS = {"rf": "pro", "rm": "meso", "rh": "meta"}


def main() -> None:
    body = Body(vision=False)
    body.reset()
    m, d = body.sim.mj_model, body.sim.mj_data
    mj.mj_forward(m, d)
    tab = pd.read_csv(passive.TABLE, comment="#")
    named = passive.measured_stiffness()
    rows = []
    for L, cls in LEGS.items():
        leg = Leg(body, L)
        keep = [i for i, n in enumerate(leg.names) if "tarsus2" not in n and "tarsus3" not in n
                and "tarsus4" not in n and "tarsus5" not in n]
        K = np.array([float(tab[(tab.leg == cls) & (tab.dof == a)].stiffness_uNmm_per_rad.iloc[0])
                      for a in ORDER])
        q0 = d.qpos[leg.adr].copy()

        def angles(q):
            d.qpos[leg.adr] = q
            mj.mj_kinematics(m, d)
            return np.radians(paper_angles(d.xpos[leg.b_ctr], d.xpos[leg.b_fti], d.xpos[leg.b_tita]))
        a0 = angles(q0)
        h = 1e-4
        J = np.zeros((4, len(keep)))
        for c, i in enumerate(keep):
            q = q0.copy()
            q[i] += h
            da = angles(q) - a0
            da[3] = (da[3] + np.pi) % (2 * np.pi) - np.pi
            J[:, c] = da / h
        d.qpos[leg.adr] = q0
        Kj = J.T @ np.diag(K) @ J
        off = np.abs(Kj - np.diag(np.diag(Kj))).sum(axis=1) / np.diag(Kj)
        for c, i in enumerate(keep):
            n = leg.names[i]
            rows.append(dict(leg=L, joint=n, k_projected=round(float(Kj[c, c]), 4),
                             k_name_mapped=named.get(n), offdiag_over_diag=round(float(off[c]), 2)))
    df = pd.DataFrame(rows)
    out = REPO / "data" / "derived" / "passive_leg_stiffness_projected.csv"
    df.to_csv(out, index=False)
    print(df.to_string())


if __name__ == "__main__":
    main()
