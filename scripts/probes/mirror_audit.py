"""Left/right mirror audit of the built body (F-STAND-3: the dead fly rolls 0.9 deg in mid-air by
10 ms, before any contact, and then tips onto one side; m9w tips left, m9f tips right).

A body that is the mirror image of itself about the sagittal (x-z) plane, placed in a mirror pose
with no actuator input, cannot roll in free fall. For each left joint and its right partner this
compares stiffness, damping, armature, spring reference, range and the placed angle, after mapping
the right joint's angle sign through the axis convention: a hinge axis is a pseudovector, so the
mirror image of axis a is -M a with M = diag(1, -1, 1); if the right axis equals -M a_left the
angles carry the same sign, if it equals M a_left the opposite sign. It also compares body masses
and positions, and reports the passive generalised force and the trunk's roll acceleration at t=0.

    uv run python scripts/probes/mirror_audit.py [--set K=V ...] [--tag m9f]
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

import mujoco as mj
import numpy as np

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "src"))
M = np.diag([1.0, -1.0, 1.0])


def partner(name: str) -> str | None:
    """Right-side name for a left-side body/joint name, else None."""
    for pat, rep in ((r"(^|[_-])l([fmh])_", r"\1r\2_"), (r"(^|[_-])l_", r"\1r_"), (r"_left", "_right"),
                     (r"(^|[_-])l([fmh])$", r"\1r\2")):
        if re.search(pat, name):
            return re.sub(pat, rep, name)
    return None


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--set", action="append", default=[])
    ap.add_argument("--tag", default="m9f")
    ap.add_argument("--out", default=str(REPO / "runs" / "s12" / "stand3"))
    a = ap.parse_args()
    from flyemu.deadfly import place_standing
    from flyemu.organism import Organism
    from flyemu.profiles import WORKING_PROFILE
    ov = {"motor_unit:all|force_per_spike": 10.0}
    ov.update({k: float(v) for k, v in (s.split("=") for s in a.set)})
    org = Organism(policy="minimal", profile=WORKING_PROFILE, min_synapses=5, seed=12, overrides=ov)
    b = org.body
    m, d = b.sim.mj_model, b.sim.mj_data
    pre = f"{b.fly.name}/"
    place_standing(b)
    d.ctrl[:] = 0.0
    mj.mj_forward(m, d)
    jn = {(m.joint(j).name or "").removeprefix(pre): j for j in range(m.njnt)}
    rows = []
    for nl, jl in sorted(jn.items()):
        nr = partner(nl)
        if nr is None or nr not in jn or m.jnt_type[jl] != mj.mjtJoint.mjJNT_HINGE:
            continue
        jr = jn[nr]
        bl, br = m.jnt_bodyid[jl], m.jnt_bodyid[jr]
        al = d.xmat[bl].reshape(3, 3) @ m.jnt_axis[jl]
        ar = d.xmat[br].reshape(3, 3) @ m.jnt_axis[jr]
        same, opp = np.linalg.norm(ar - (-M @ al)), np.linalg.norm(ar - (M @ al))
        s = 1.0 if same < opp else -1.0
        axis_err = float(min(same, opp))
        dl, dr = m.jnt_dofadr[jl], m.jnt_dofadr[jr]
        ql, qr = m.jnt_qposadr[jl], m.jnt_qposadr[jr]
        rl = m.jnt_range[jl].copy()
        rr = np.sort(s * m.jnt_range[jr])
        rows.append(dict(
            left=nl, right=nr, sign=int(s), axis_err=round(axis_err, 4),
            stiff=[float(m.jnt_stiffness[jl]), float(m.jnt_stiffness[jr])],
            damp=[float(m.dof_damping[dl]), float(m.dof_damping[dr])],
            arm=[float(m.dof_armature[dl]), float(m.dof_armature[dr])],
            springref_deg=[round(float(np.degrees(m.qpos_spring[ql])), 2), round(float(np.degrees(s * m.qpos_spring[qr])), 2)],
            q_place_deg=[round(float(np.degrees(d.qpos[ql])), 2), round(float(np.degrees(s * d.qpos[qr])), 2)],
            range_deg=[np.round(np.degrees(rl), 1).tolist(), np.round(np.degrees(rr), 1).tolist()],
            qfrc_passive=[float(d.qfrc_passive[dl]), float(s * d.qfrc_passive[dr])],
        ))
    bad = []
    for r in rows:
        why = []
        for k in ("stiff", "damp", "arm"):
            x, y = r[k]
            if abs(x - y) > 1e-6 * max(abs(x), abs(y), 1e-12) + 1e-12:
                why.append(f"{k} {x:g} vs {y:g}")
        for k, tol in (("springref_deg", 0.05), ("q_place_deg", 0.05)):
            x, y = r[k]
            if abs(x - y) > tol:
                why.append(f"{k} {x} vs {y}")
        if np.abs(np.subtract(*r["range_deg"])).max() > 0.05:
            why.append(f"range {r['range_deg'][0]} vs {r['range_deg'][1]}")
        if r["axis_err"] > 1e-3:
            why.append(f"axis not mirrored ({r['axis_err']})")
        if why:
            bad.append(dict(joint=r["left"], issues=why))
    bn = {(m.body(i).name or "").removeprefix(pre): i for i in range(m.nbody)}
    body_bad = []
    for nl, il in sorted(bn.items()):
        nr = partner(nl)
        if nr is None or nr not in bn:
            continue
        ir = bn[nr]
        dm = float(m.body_mass[il] - m.body_mass[ir])
        di = np.abs(m.body_inertia[il] - m.body_inertia[ir]).max()
        dp = float(np.linalg.norm(m.body_pos[il] - M @ m.body_pos[ir]))
        if abs(dm) > 1e-6 * m.body_mass[il] or di > 1e-6 * m.body_inertia[il].max() or dp > 1e-4:
            body_bad.append(dict(body=nl, d_mass=dm, d_inertia=float(di), d_pos_mm=round(dp, 5)))
    unpaired = sorted(n for n in jn if partner(n) and partner(n) not in jn)
    # roll acceleration of the trunk from passive forces alone (free joint dofs 3:6 are angular)
    free = [j for j in range(m.njnt) if m.jnt_type[j] == mj.mjtJoint.mjJNT_FREE]
    fd = m.jnt_dofadr[free[0]] if free else 0
    res = dict(tag=a.tag, profile=WORKING_PROFILE, overrides=ov, n_pairs=len(rows), n_pairs_bad=len(bad),
               trunk_qacc_angular=np.round(d.qacc[fd + 3:fd + 6], 4).tolist(),
               trunk_y_mm=round(float(d.qpos[1]), 5), bad=bad, body_bad=body_bad, unpaired=unpaired, pairs=rows)
    out = Path(a.out); out.mkdir(parents=True, exist_ok=True)
    (out / f"mirror_audit_{a.tag}.json").write_text(json.dumps(res, indent=1))
    print(json.dumps({k: v for k, v in res.items() if k not in ("pairs",)}, indent=1))


if __name__ == "__main__":
    main()
