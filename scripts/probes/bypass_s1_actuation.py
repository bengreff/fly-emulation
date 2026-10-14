"""Motor-pathway bypass assay, stage S1: actuation with the CNS bypassed (s13, 13 Oct).

DIAGNOSTIC, forced drive: muscle activations are set by hand, not produced by the network. Nothing here is
behaviour or a fit.

The organism (profile body, Hill leg muscles, coxa muscles, passive springs, adhesion) is built as usual, but no
neuron is stepped. Every leg muscle gets a constant, bounded activation (0-1), and the body is placed standing
and run for --ms. Two patterns:
  coact:   every leg muscle at the same activation (antagonists included);
  support: only the muscles whose torque at the placed pose points the way the standing hold needs. The need is
           measured first with stand_budget.py's instrument springs (300 ms, then removed).
  need:    each muscle at the activation that supplies exactly that measured hold torque, times the level k.
Reports per run: thorax-origin height over time, floor force on the legs and on the trunk against body weight,
active torque by joint group, and NaN. Before the runs, a static audit lists, per muscle: F0, moment arm,
force-length gain at the placed pose, and motor neurons mapped (muscles with none are unreachable from the CNS),
plus the leg motor neurons that reach no muscle.

    uv run python scripts/probes/bypass_s1_actuation.py [--profile m10f0] [--ms 3000] [--levels 0,0.1,0.3,1]
"""
from __future__ import annotations

import argparse
import json
import re
import sys
import time
from pathlib import Path

import mujoco as mj
import numpy as np

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "src")); sys.path.insert(0, str(Path(__file__).resolve().parent))
from flyemu.deadfly import place_standing  # noqa: E402
from flyemu.muscles import gain_length  # noqa: E402
from flyemu.organism import Organism  # noqa: E402
from stand_budget import K_HOLD, D_HOLD, group, heights  # noqa: E402
from standing_rest import shot  # noqa: E402

LEGS = ("lf", "lm", "lh", "rf", "rm", "rh")
LEG_RE = re.compile(r"(?:^|[-/_])([lr][fmh])_")


def floor_forces(m, d, leg_body: np.ndarray, touched: dict | None = None) -> tuple[float, float]:
    """Normal floor force (uN) on the feet (tarsal segments) and on everything else; counts other bodies touching."""
    f6 = np.zeros(6)
    fl = fo = 0.0
    for i in range(d.ncon):
        c = d.contact[i]
        b1, b2 = m.geom_bodyid[c.geom1], m.geom_bodyid[c.geom2]
        if b1 != 0 and b2 != 0:
            continue
        other = b2 if b1 == 0 else b1
        mj.mj_contactForce(m, d, i, f6)
        if leg_body[other]:
            fl += f6[0]
        else:
            fo += f6[0]
            if touched is not None:
                nm = (m.body(other).name or "").split("/")[-1]
                touched[nm] = touched.get(nm, 0) + 1
    return fl, fo


def hold_need(org) -> dict[str, float]:
    """Instrument hold torque per leg hinge at the placed pose (stand_budget.py method), uN*mm."""
    b = org.body
    m, d = b.sim.mj_model, b.sim.mj_data
    pre = f"{b.fly.name}/"
    b.reset(); place_standing(b)
    hj = [j for j in range(m.njnt) if m.jnt_type[j] == mj.mjtJoint.mjJNT_HINGE
          and any(f"{L}_" in (m.joint(j).name or "") for L in LEGS)]
    qa = np.array([m.jnt_qposadr[j] for j in hj]); va = np.array([m.jnt_dofadr[j] for j in hj])
    q_hold = d.qpos[qa].copy()
    k0, ref0, dmp0 = m.jnt_stiffness[hj].copy(), m.qpos_spring[qa].copy(), m.dof_damping[va].copy()
    m.jnt_stiffness[hj] += K_HOLD
    m.qpos_spring[qa] = (k0 * ref0 + K_HOLD * q_hold) / (k0 + K_HOLD)
    m.dof_damping[va] += D_HOLD
    b.set_adhesion(np.zeros(len(b.adhesion_names)))
    zero = np.zeros(b.n_actuators)
    for _ in range(int(round(300.0 / (m.opt.timestep * 1e3)))):
        b.actuate(zero); b.step()
    need = K_HOLD * (q_hold - d.qpos[qa])
    m.jnt_stiffness[hj], m.qpos_spring[qa], m.dof_damping[va] = k0, ref0, dmp0
    return {(m.joint(j).name or "").removeprefix(pre): float(t) for j, t in zip(hj, need)}


def audit(org, pre: str) -> dict:
    h, b = org.hill, org.body
    m, d = b.sim.mj_model, b.sim.mj_data
    b.reset(); place_standing(b)
    p = h.p
    gl = gain_length(p.lengths(d.qpos[h.q_adr]), p.lmin, p.lmax)
    n_mn = np.bincount(h.mn_muscle[h.ok], minlength=len(p.F0))
    pairs = [dict(joint=j, direction=float(s), F0_uN=round(float(f), 1), r_mm=round(float(r), 4),
                  capacity_uNmm=round(float(f * r), 2), fl_gain_at_pose=round(float(g), 3), n_mn=int(k))
             for j, s, f, r, g, k in zip(p.joint, p.direction, p.F0, p.r, gl, n_mn)]
    coxa = []
    if h.coxa is not None:
        c = h.coxa
        cgl = gain_length(c.lengths(d.qpos[h.cq_adr]), c.lmin, c.lmax)
        gn = np.bincount(h.mn_group[h.mn_group >= 0], minlength=h.n_groups)
        for k in range(len(c.F0)):
            coxa.append(dict(leg=c.leg[k], muscle=c.name[k], mn_type=c.mn_type[k], F0_uN=round(float(c.F0[k]), 1),
                             r_norm_mm=round(float(np.linalg.norm(c.R[k])), 4), fl_gain_at_pose=round(float(cgl[k]), 3),
                             n_mn=int(gn[h.coxa_group[k]]) if h.coxa_group[k] >= 0 else 0))
    # leg MNs reaching no muscle (neither a pair muscle nor a coxa group)
    act = [b.actuator_names[i].split("/")[-1] for i in org.nm.actuator_index]
    legm = [LEG_RE.search(a) for a in act]
    is_leg = np.array([x is not None for x in legm]) & np.isin(np.arange(len(act)), np.flatnonzero(
        [any(k in a for k in ("coxa", "femur", "tibia", "tarsus", "trochanter")) for a in act]))
    reach = h.ok | ((h.mn_group >= 0) if h.coxa is not None else False)
    types = org.conn.neurons.type.fillna("").to_numpy()[org.nm.mn_index]
    lost = {}
    for k in np.flatnonzero(is_leg & ~reach):
        lost[types[k]] = lost.get(types[k], 0) + 1
    return dict(pairs=pairs, coxa=coxa,
                pairs_without_mn=[f"{r['joint']} {r['direction']:+g}" for r in pairs if r["n_mn"] == 0],
                coxa_without_mn=[f"{r['leg']} {r['muscle']}" for r in coxa if r["n_mn"] == 0],
                leg_mns_total=int(is_leg.sum()), leg_mns_reaching_no_muscle=int((is_leg & ~reach).sum()),
                leg_mn_types_reaching_no_muscle=dict(sorted(lost.items(), key=lambda kv: -kv[1])[:20]))


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--profile", default="m10f0")
    ap.add_argument("--seed", type=int, default=12)
    ap.add_argument("--ms", type=float, default=3000.0)
    ap.add_argument("--levels", default="0,0.05,0.1,0.2,0.3,0.5,1")
    ap.add_argument("--patterns", default="support,coact")
    ap.add_argument("--adhesion", type=float, default=1.0, help="tarsal adhesion state on every leg (0-1)")
    ap.add_argument("--frames-ms", default="0,250,1000,3000")
    ap.add_argument("--out", default=str(REPO / "runs" / "s13" / "bypass" / "s1"))
    a = ap.parse_args()
    out = Path(a.out); out.mkdir(parents=True, exist_ok=True)
    t0 = time.time()
    org = Organism(policy="minimal", profile=a.profile, min_synapses=5, seed=a.seed, with_camera=True)
    h, b = org.hill, org.body
    if h is None:
        raise SystemExit(f"profile {a.profile} has no Hill leg muscles (muscle:leg|model 0)")
    m, d = b.sim.mj_model, b.sim.mj_data
    pre = f"{b.fly.name}/"
    # feet are the tarsal segments; a coxa, femur or tibia on the floor means the fly is down, not standing
    leg_body = np.array(["tarsus" in (m.body(i).name or "") for i in range(m.nbody)])
    adh_ids = np.array([mj.mj_name2id(m, mj.mjtObj.mjOBJ_ACTUATOR, n if n.startswith(pre) else pre + n)
                        for n in b.adhesion_names], int)
    adh_ids = adh_ids[adh_ids >= 0]
    thorax = mj.mj_name2id(m, mj.mjtObj.mjOBJ_BODY, pre + "c_thorax")
    weight = float(m.body_subtreemass[1] * -m.opt.gravity[2])
    res = dict(profile=a.profile, seed=a.seed, ms=a.ms, adhesion=a.adhesion, diagnostic="forced drive (CNS bypassed)",
               units=dict(gravity=m.opt.gravity.tolist(), mass_g=float(m.body_subtreemass[1]), weight_uN=round(weight, 3),
                          timestep_ms=float(m.opt.timestep * 1e3)),
               build_s=round(time.time() - t0))
    res["audit"] = audit(org, pre)
    need = hold_need(org)
    res["hold_need_uNmm"] = {k: round(v, 3) for k, v in need.items()}
    p = h.p
    sup_pair = np.array([s * need.get(j, 0.0) > 0 for j, s in zip(p.joint, p.direction)], float)
    sup_coxa = None
    if h.coxa is not None:
        c = h.coxa
        nv = np.array([[need.get(j, 0.0) for j in row] for row in c.joint])
        sup_coxa = ((c.R * nv).sum(1) > 0).astype(float)
    # need: per muscle, the activation that supplies the measured static hold torque (FL gain is 1 at the pose).
    # Pairs act on one hinge each; the coxa muscles share the three coxa hinges, so per leg a non-negative least
    # squares picks their activations. Scaled by the level k (k = 1 is exactly the static need).
    need_pair = np.array([max(0.0, s * need.get(j, 0.0)) / (r * f) for j, s, r, f in zip(p.joint, p.direction, p.r, p.F0)])
    need_coxa, coxa_resid = None, {}
    if h.coxa is not None:
        from scipy.optimize import nnls
        need_coxa = np.zeros(len(c.F0))
        for L in sorted(set(c.leg)):
            ix = np.flatnonzero(np.asarray(c.leg) == L)
            tgt = np.array([need.get(j, 0.0) for j in c.joint[ix[0]]])
            x, rn = nnls((c.R[ix] * c.F0[ix, None]).T, tgt)
            need_coxa[ix] = x
            coxa_resid[L] = round(float(rn / max(np.linalg.norm(tgt), 1e-9)), 3)
    res["need_activation"] = dict(pair_max=round(float(need_pair.max()), 3), pair_mean_on=round(float(need_pair[need_pair > 0].mean()), 3),
                                  coxa_max=None if need_coxa is None else round(float(need_coxa.max()), 3),
                                  coxa_residual_frac=coxa_resid,
                                  by_pair={f"{j}{'+' if s > 0 else '-'}": round(float(v), 3) for j, s, v in zip(p.joint, p.direction, need_pair)})
    # bypass: constant activations replace the motor-unit pools; the network is never stepped
    adh_set = b.set_adhesion
    b.set_adhesion = lambda s: adh_set(np.full(np.shape(s), a.adhesion))
    frames_at = {int(round(float(x) / org.timestep_ms)) for x in a.frames_ms.split(",")}
    nospk = np.empty(0, np.int64)
    runs = []
    for pat in a.patterns.split(","):
        for lv in (float(x) for x in a.levels.split(",")):
            if pat == "need":
                ap_ = np.clip(need_pair * lv, 0.0, 1.0)
                ac_ = None if h.coxa is None else np.clip(need_coxa * lv, 0.0, 1.0)
            else:
                ap_ = (sup_pair if pat == "support" else np.ones(len(p.F0))) * lv
                ac_ = None if h.coxa is None else ((sup_coxa if pat == "support" else np.ones(len(h.coxa.F0))) * lv)
            h.activation = lambda nm=None, v=ap_: v
            h.coxa_activation = lambda v=ac_: v
            b.reset(); place_standing(b)
            z = [float(d.xpos[thorax, 2])]
            fl, fo, fa, nonleg_touch, touched = [], [], [], 0, {}
            imgs = []
            n = int(round(a.ms / org.timestep_ms))
            k10 = int(round(10.0 / org.timestep_ms))
            for s in range(n + 1):
                if s in frames_at:
                    imgs.append(shot(m, d, thorax))
                if s == n:
                    break
                org.motor_step(nospk)
                if (s + 1) % k10 == 0:
                    z.append(float(d.xpos[thorax, 2]))
                    a_, o_ = floor_forces(m, d, leg_body, touched if s >= n - 100 * k10 else None)
                    fl.append(a_); fo.append(o_); nonleg_touch += o_ > 0
                    fa.append(float(np.abs(d.actuator_force[adh_ids]).sum()) if adh_ids.size else 0.0)
            z = np.array(z); fl = np.array(fl); fo = np.array(fo); fa = np.array(fa)
            last1 = slice(-100, None)
            tq = p.torques(ap_, d.qpos[h.q_adr], d.qvel[h.v_adr])
            by = {}
            for j, t in zip(p.joint, tq):
                by[group(j)] = by.get(group(j), 0.0) + abs(float(t))
            if h.coxa is not None:
                ct = h.coxa.torques(ac_, d.qpos[h.cq_adr], d.qvel[h.cv_adr])
                by["coxa_muscles"] = float(np.abs(ct).sum())
            r = dict(pattern=pat, level=lv, z_place=round(float(z[0]), 3),
                     z_at_ms={str(t): round(float(z[int(t / 10)]), 3) for t in (100, 500, 1000, 2000, int(a.ms))
                              if int(t / 10) < len(z)},
                     z_min=round(float(z.min()), 3), z_final=round(float(z[-1]), 3),
                     sink_last2s_mm=round(float(z[min(len(z) - 1, 100)] - z[-1]), 3) if len(z) > 100 else None,
                     leg_floor_force_over_weight_last1s=round(float(fl[last1].mean() / weight), 3),
                     trunk_floor_force_over_weight_last1s=round(float(fo[last1].mean() / weight), 3),
                     trunk_touch_frac=round(nonleg_touch / max(len(fo), 1), 3),
                     # adhesion presses the feet down, so the foot normal force includes it; net support removes it
                     adhesion_force_over_weight_last1s=round(float(fa[last1].mean() / weight), 3),
                     foot_net_support_over_weight_last1s=round(float((fl[last1] - fa[last1]).mean() / weight), 3),
                     non_foot_touch_last1s={k: round(v / 100, 2) for k, v in sorted(touched.items(), key=lambda kv: -kv[1])[:8]},
                     active_torque_abs_uNmm=({k: round(v, 2) for k, v in by.items()}),
                     nan=bool(not np.isfinite(d.qpos).all()), heights_final_mm={k: round(v, 3) for k, v in heights(m, d, pre).items()})
            r["holds"] = bool(r["z_final"] >= 0.9 and (r["sink_last2s_mm"] or 0) < 0.05 and r["trunk_touch_frac"] == 0
                              and 0.8 <= r["leg_floor_force_over_weight_last1s"] <= 1.2 and not r["nan"])
            runs.append(r)
            print(json.dumps({k: r[k] for k in ("pattern", "level", "z_place", "z_min", "z_final", "sink_last2s_mm",
                                                "leg_floor_force_over_weight_last1s", "trunk_touch_frac", "holds")}), flush=True)
            if imgs:
                np.save(out / f"frames_{pat}_{lv:g}.npy", np.stack(imgs))
    res["runs"] = runs
    res["n_support_pairs"] = int(sup_pair.sum()); res["n_support_coxa"] = None if sup_coxa is None else int(sup_coxa.sum())
    res["wall_s"] = round(time.time() - t0)
    (out / f"s1_{a.profile}_adh{a.adhesion:g}.json").write_text(json.dumps(res, indent=1))
    au = res["audit"]
    print(json.dumps(dict(units=res["units"], pairs_without_mn=au["pairs_without_mn"], coxa_without_mn=au["coxa_without_mn"],
                          leg_mns_total=au["leg_mns_total"], leg_mns_reaching_no_muscle=au["leg_mns_reaching_no_muscle"],
                          lost_types=au["leg_mn_types_reaching_no_muscle"]), indent=1))


if __name__ == "__main__":
    main()
