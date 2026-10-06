"""Session 12 B: what torque does standing need, joint by joint?

Body only (m9w template body, no brain). The fly is placed standing in its
neutral pose; every leg hinge then gets a stiff instrument spring
(K_HOLD) to that pose, which is not part of the model: it measures the active
torque a real fly's muscles would have to supply to stand there. After the
transient, per joint: the hold torque (= required active torque), the
model's passive spring torque at that pose, and their ratio. Also reports the
model's height references (dorsal thorax surface, head centre, thorax origin)
so model heights can be compared with Pratt 2024 (ground to dorsal thorax
keypoint) and Wang 2025 (head height above the collapsed head).

    uv run python scripts/probes/stand_budget.py [--ms 300] [--drop MM] [--set KEY=V ...]
`--drop` lowers the placed body by MM first (legs re-solved by the hold).
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import mujoco as mj
import numpy as np

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "src"))
from flyemu import passive, profiles  # noqa: E402
from flyemu.body import Body  # noqa: E402
from flyemu.deadfly import place_standing  # noqa: E402
from flyemu.registry import Registry  # noqa: E402

LEGS = ("lf", "lm", "lh", "rf", "rm", "rh")
K_HOLD = 200.0      # uN*mm/rad, instrument
D_HOLD = 0.5        # uN*mm*s/rad, instrument


def group(n: str) -> str:
    return ("ThC" if n.startswith("c_thorax") else "CTr" if "_coxa-" in n and "pitch" in n
            else "Tr-roll" if "_coxa-" in n else "FTi" if "trochanterfemur-" in n
            else "TiTa" if "_tibia-" in n else "tarsal")


def heights(m, d, pre: str) -> dict:
    th = mj.mj_name2id(m, mj.mjtObj.mjOBJ_BODY, pre + "c_thorax")
    hd = mj.mj_name2id(m, mj.mjtObj.mjOBJ_BODY, pre + "c_head")
    top = -np.inf
    for g in range(m.ngeom):
        if m.geom_bodyid[g] == th and m.geom_type[g] == mj.mjtGeom.mjGEOM_MESH:
            mid = m.geom_dataid[g]
            v0, nv = m.mesh_vertadr[mid], m.mesh_vertnum[mid]
            v = m.mesh_vert[v0:v0 + nv] @ d.geom_xmat[g].reshape(3, 3).T + d.geom_xpos[g]
            top = max(top, float(v[:, 2].max()))
    return dict(thorax_origin=float(d.xpos[th, 2]), thorax_dorsal=top, head=float(d.xpos[hd, 2]))


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--ms", type=float, default=300.0)
    ap.add_argument("--drop", type=float, default=0.0)
    ap.add_argument("--set", action="append", default=[], metavar="KEY=V")
    ap.add_argument("--out", default=str(REPO / "runs" / "s12" / "standing"))
    a = ap.parse_args()
    reg = Registry("minimal")
    reg.overrides.update({k: float(v) for k, v in (x.split("=") for x in a.set)})
    profiles.apply(reg, profiles.WORKING_PROFILE)
    b = Body(vision=False)
    passive.register(reg, b)
    passive.register_coxa(reg, b)
    passive.register_rest(reg, b)
    passive.register_wings(reg, b)
    m, d = b.sim.mj_model, b.sim.mj_data
    pre = f"{b.fly.name}/"
    b.reset()
    place_standing(b)
    h_place = heights(m, d, pre)
    hj = [j for j in range(m.njnt) if m.jnt_type[j] == mj.mjtJoint.mjJNT_HINGE
          and any(f"{L}_" in (m.joint(j).name or "") for L in LEGS)]
    names = [(m.joint(j).name or "").removeprefix(pre) for j in hj]
    qa = np.array([m.jnt_qposadr[j] for j in hj]); va = np.array([m.jnt_dofadr[j] for j in hj])
    q_hold = d.qpos[qa].copy()
    k0, ref0 = m.jnt_stiffness[hj].copy(), m.qpos_spring[qa].copy()
    m.jnt_stiffness[hj] += K_HOLD
    m.qpos_spring[qa] = (k0 * ref0 + K_HOLD * q_hold) / (k0 + K_HOLD)   # same total spring: k0 to ref0 + K_HOLD to q_hold
    m.dof_damping[va] += D_HOLD
    if a.drop:
        d.qpos[2] -= a.drop
    b.set_adhesion(np.zeros(len(b.adhesion_names)))
    zero = np.zeros(b.n_actuators)
    n = int(round(a.ms / (m.opt.timestep * 1e3)))
    for _ in range(n):
        b.actuate(zero)
        b.step()
    q = d.qpos[qa]
    hold = K_HOLD * (q_hold - q)                              # instrument torque, uN*mm
    passive_diag = -k0 * (q - ref0)
    passive_cpl = np.zeros(len(hj))
    for h in b.passive_hooks:
        if isinstance(h, passive.CoupledSprings):
            for L, K in h.K.items():
                tq = -K @ (d.qpos[h.qadr[L]] - h.qref[L])
                for k, v in zip(h.dofs[L], tq):
                    passive_cpl[list(va).index(k)] = v
    pas = passive_diag + passive_cpl
    floor = {g for g in range(m.ngeom) if m.geom_bodyid[g] == 0}
    fz = 0.0
    f6 = np.zeros(6)
    for i in range(d.ncon):
        c = d.contact[i]
        if c.geom1 in floor or c.geom2 in floor:
            mj.mj_contactForce(m, d, i, f6); fz += f6[0]
    rows = {nm: dict(group=group(nm), hold_uNmm=round(float(h), 3), passive_uNmm=round(float(p), 3),
                     dev_deg=round(float(np.degrees(q[i] - q_hold[i])), 2))
            for i, (nm, h, p) in enumerate(zip(names, hold, pas))}
    by = {}
    for r in rows.values():
        g = by.setdefault(r["group"], dict(hold_abs_sum=0.0, passive_abs_sum=0.0, n=0))
        g["hold_abs_sum"] += abs(r["hold_uNmm"]); g["passive_abs_sum"] += abs(r["passive_uNmm"]); g["n"] += 1
    for g in by.values():
        g["hold_abs_mean"] = round(g.pop("hold_abs_sum") / g["n"], 3)
        g["passive_abs_mean"] = round(g.pop("passive_abs_sum") / g["n"], 3)
    res = dict(drop_mm=a.drop, heights_placed_mm={k: round(v, 3) for k, v in h_place.items()},
               heights_held_mm={k: round(v, 3) for k, v in heights(m, d, pre).items()},
               weight_uN=round(float(m.body_subtreemass[1] * 9.81e3), 2), floor_fz_uN=round(float(fz), 2),
               by_group=by, joints=rows, k_hold=K_HOLD)
    out = Path(a.out); out.mkdir(parents=True, exist_ok=True)
    (out / f"stand_budget_drop{a.drop:g}{'_' + '_'.join(x.split('|')[-1] for x in a.set) if a.set else ''}.json").write_text(json.dumps(res, indent=1))
    print(json.dumps({k: v for k, v in res.items() if k != "joints"}, indent=1))
    top = sorted(rows.items(), key=lambda kv: -abs(kv[1]["hold_uNmm"]))[:12]
    for nm, r in top:
        print(f"{nm:36s} {r['group']:7s} hold {r['hold_uNmm']:8.3f}  passive {r['passive_uNmm']:7.3f}  dev {r['dev_deg']:6.2f} deg")


if __name__ == "__main__":
    main()
