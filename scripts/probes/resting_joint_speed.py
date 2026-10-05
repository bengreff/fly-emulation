"""Session 12 B (F-DAMP-1 follow-up): is the resting leg motion that raised bristle
rates on m9d physical or numerical jitter? Records leg joint speeds at rest.

--mode body: no neural drive (motor path stepped with no spikes), so only passive
mechanics, contact and gravity act. --substeps k halves (k=2) the physics step and
repeats the body step with the same applied forces; numerical chatter changes with
the step, settled physical motion does not.
--mode loop: the gate's closed loop (closed_loop_check.py), recording the same speeds.

Reports RMS leg joint speed (deg/s) after 200 ms, and the fraction of speed power
above 1 kHz (chatter shows as power near the step's Nyquist band). Also the head
contact that drives the head-touch channel (extrasenses): fraction of samples with
any head-region contact, mean total normal force, and the contact partners. Foot
creep: horizontal drift of each tarsal tip (tarsus5 body) from 200 ms to the end,
mm, and whether it was on the floor throughout.

    uv run python scripts/probes/resting_joint_speed.py --profile m9d --mode body [--substeps 2]
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
from flyemu.organism import Organism  # noqa: E402


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--profile", required=True)
    ap.add_argument("--mode", choices=("body", "loop"), default="body")
    ap.add_argument("--ms", type=float, default=1000.0)
    ap.add_argument("--seed", type=int, default=13)
    ap.add_argument("--substeps", type=int, default=1)
    ap.add_argument("--set", action="append", default=["motor_unit:all|force_per_spike=10"])
    ap.add_argument("--noslip", type=int, default=-1, help="override MuJoCo noslip_iterations (flybody arena: 3)")
    ap.add_argument("--out", default="")
    a = ap.parse_args()
    ov = {k: float(v) for k, v in (s.split("=") for s in a.set)}
    org = Organism(policy="minimal", profile=a.profile, min_synapses=5, overrides=ov, seed=a.seed)
    m, d = org.body.sim.mj_model, org.body.sim.mj_data
    m.opt.timestep /= a.substeps
    if a.noslip >= 0:
        m.opt.noslip_iterations = a.noslip
    names = [mj.mj_id2name(m, mj.mjtObj.mjOBJ_JOINT, j) or "" for j in range(m.njnt)]
    leg = [j for j, nm in enumerate(names) if m.jnt_type[j] == mj.mjtJoint.mjJNT_HINGE
           and any(s in nm for s in ("coxa", "femur", "tibia", "tarsus"))]
    dof = np.array([m.jnt_dofadr[j] for j in leg])
    grp = {g: [i for i, j in enumerate(leg) if g in names[j]] for g in ("coxa", "femur", "tibia", "tarsus")}
    none = np.zeros(0, dtype=np.int64)
    steps = int(a.ms / org.timestep_ms)
    from flyemu.extrasenses import HEAD_BODIES
    hb = {mj.mj_name2id(m, mj.mjtObj.mjOBJ_BODY, f"{org.body.fly.name}/{h}") for h in HEAD_BODIES}
    hb.discard(-1)
    LEGS = ("lf", "lm", "lh", "rf", "rm", "rh")
    tip = [mj.mj_name2id(m, mj.mjtObj.mjOBJ_BODY, f"{org.body.fly.name}/{L}_tarsus5") for L in LEGS]
    tip0, tip_down = None, np.ones(len(LEGS), bool)
    c6 = np.zeros(6)
    v, nsp, hf, partners = [], 0, [], {}
    for s in range(steps):
        if a.mode == "loop":
            obs = org.body.observe()
            sp = org.net.step(external_mv=org.sense(s, obs))
        else:
            sp = none
        org.motor_step(sp)
        for _ in range(a.substeps - 1):
            org.body.step()
        if s * org.timestep_ms >= 200:
            v.append(np.degrees(d.qvel[dof]))
            if tip0 is None:
                tip0 = d.xpos[tip, :2].copy()
            down = np.zeros(len(LEGS), bool)
            for i in range(d.ncon):
                for g in (d.contact[i].geom1, d.contact[i].geom2):
                    b = int(m.geom_bodyid[g])
                    if b in tip:
                        down[tip.index(b)] = True
            tip_down &= down
            nsp += sp.size
            f = 0.0
            for i in range(d.ncon):
                b1, b2 = int(m.geom_bodyid[d.contact[i].geom1]), int(m.geom_bodyid[d.contact[i].geom2])
                for b, o in ((b1, b2), (b2, b1)):
                    if b in hb:
                        mj.mj_contactForce(m, d, i, c6)
                        f += abs(c6[0])
                        k = (mj.mj_id2name(m, mj.mjtObj.mjOBJ_BODY, b) or "").split("/")[-1] + "-" + \
                            ((mj.mj_id2name(m, mj.mjtObj.mjOBJ_BODY, o) or "world").split("/")[-1])
                        partners[k] = partners.get(k, 0) + 1
            hf.append(f)
    v = np.array(v)
    dt = org.timestep_ms / 1000.0
    P = np.abs(np.fft.rfft(v - v.mean(0), axis=0)) ** 2
    fr = np.fft.rfftfreq(len(v), dt)
    out = {"profile": a.profile, "mode": a.mode, "substeps": a.substeps, "noslip_iterations": int(m.opt.noslip_iterations), "physics_dt_ms": m.opt.timestep * 1000,
           "sample_dt_ms": org.timestep_ms, "seed": a.seed,
           "rms_deg_s": {g: round(float(np.sqrt((v[:, i] ** 2).mean())), 2) for g, i in grp.items()},
           "rms_all_deg_s": round(float(np.sqrt((v ** 2).mean())), 2),
           "max_abs_deg_s": round(float(np.abs(v).max()), 1),
           "power_frac_above_1khz": round(float(P[fr > 1000].sum() / P.sum()), 4),
           "spikes_after_200ms": int(nsp),
           "mujoco_warnings": int(sum(w.number for w in d.warning)),
           "head_contact_frac": round(float((np.array(hf) > 0).mean()), 4),
           "head_force_mean": round(float(np.mean(hf)), 4),
           "head_contact_partners": {k: round(n / len(hf), 4) for k, n in sorted(partners.items(), key=lambda x: -x[1])[:8]},
           "foot_creep_mm": {L: round(float(np.linalg.norm(d.xpos[t, :2] - tip0[k])), 4) for k, (L, t) in enumerate(zip(LEGS, tip))},
           "foot_down_throughout": {L: bool(x) for L, x in zip(LEGS, tip_down)},
           "thorax_z_mm": round(float(org.body.observe()["body_positions"][0, 2]), 3), "overrides": ov}
    print(json.dumps(out))
    if a.out:
        Path(a.out).parent.mkdir(parents=True, exist_ok=True)
        Path(a.out).write_text(json.dumps(out, indent=1))


if __name__ == "__main__":
    main()
