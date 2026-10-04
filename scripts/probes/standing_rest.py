"""Session 12 B: why does the fly sink at rest? Closed-loop standing probe.

Runs the working organism (all senses, no stimulus) placed standing and logs
every 10 ms: thorax height and tilt, trunk-floor contact, the floor's normal
force on each leg, every leg hinge's angle, which hinges sit on a range limit,
and leg MN rates by joint group. `--dead` silences motor output (no MN spike
reaches a muscle) for the same build: the eLife 2025 dead-fly reference.

    uv run python scripts/probes/standing_rest.py [--ms 1500] [--seed 12] [--set K=V] [--dead] [--tag NAME]
"""
from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

import mujoco as mj
import numpy as np

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "src"))
from flyemu.deadfly import place_standing  # noqa: E402
from flyemu.organism import Organism  # noqa: E402
from flyemu.profiles import WORKING_PROFILE  # noqa: E402

LEGS = ("lf", "lm", "lh", "rf", "rm", "rh")
BAND = 0.03


def shot(m, d, thorax: int) -> np.ndarray:
    r = mj.Renderer(m, 300, 400)
    imgs = []
    for az in (90.0, 180.0):
        c = mj.MjvCamera()
        c.type = mj.mjtCamera.mjCAMERA_FREE
        c.lookat[:] = d.xpos[thorax]
        c.distance, c.azimuth, c.elevation = 5.0, az, -5.0
        r.update_scene(d, camera=c)
        imgs.append(r.render().copy())
    r.close()
    return np.concatenate(imgs, axis=1)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--ms", type=float, default=1500.0)
    ap.add_argument("--seed", type=int, default=12)
    ap.add_argument("--set", action="append", default=[])
    ap.add_argument("--dead", action="store_true")
    ap.add_argument("--tag", default="")
    ap.add_argument("--out", default=str(REPO / "runs" / "s12" / "standing"))
    a = ap.parse_args()
    ov = {k: float(v) for k, v in (s.split("=") for s in a.set)}
    tag = a.tag or ("dead" if a.dead else "live")
    out = Path(a.out); out.mkdir(parents=True, exist_ok=True)
    org = Organism(policy="minimal", profile=WORKING_PROFILE, min_synapses=5, overrides=ov,
                   seed=a.seed, with_camera=True)
    b = org.body
    m, d = b.sim.mj_model, b.sim.mj_data
    pre = f"{b.fly.name}/"
    place_standing(b)
    z0 = float(d.qpos[2])
    thorax = mj.mj_name2id(m, mj.mjtObj.mjOBJ_BODY, pre + "c_thorax")
    trunk = {i for i in range(m.nbody) if any(k in (m.body(i).name or "") for k in ("thorax", "abdomen", "head"))}
    leg_of_body = {}
    for i in range(m.nbody):
        n = (m.body(i).name or "").removeprefix(pre)
        for L in LEGS:
            if n.startswith(L + "_"):
                leg_of_body[i] = L
    floor = {g for g in range(m.ngeom) if m.geom_bodyid[g] == 0}
    hj = [j for j in range(m.njnt) if m.jnt_type[j] == mj.mjtJoint.mjJNT_HINGE
          and any((m.joint(j).name or "").removeprefix(pre).count(L) for L in LEGS)
          and (m.joint(j).name or "").count("tarsus") < 2]
    hn = [(m.joint(j).name or "").removeprefix(pre) for j in hj]
    hadr = np.array([m.jnt_qposadr[j] for j in hj])
    rng = m.jnt_range[hj].copy()
    span = rng[:, 1] - rng[:, 0]
    # MN -> actuator short name, for rates by leg and joint group
    short = [s.split("/")[-1].removesuffix("-motor") for s in b.actuator_names]
    mn_idx = np.asarray(org.nm.mn_index)
    act_of_mn = np.asarray(org.nm.actuator_index)
    grp = {}
    for k, ai in enumerate(act_of_mn):
        if ai < 0 or ai >= len(short):
            continue
        s = short[ai]
        L = next((L for L in LEGS if f"{L}_" in s), None)
        if L is None:
            continue
        jg = ("ThC" if "c_thorax" in s else "CTr" if "_coxa-" in s else "FTi" if "trochanterfemur-" in s
              else "TiTa" if "_tibia-" in s else "other")
        grp.setdefault(f"{L}:{jg}", []).append(k)
    mn_cnt = np.zeros(len(mn_idx))
    steps = int(round(a.ms / org.timestep_ms))
    every = int(round(10 / org.timestep_ms))
    snaps = {0, int(100 / org.timestep_ms), int(300 / org.timestep_ms), int(700 / org.timestep_ms), steps - 1}
    rows, frames, onlim = [], [], np.zeros(len(hj))
    silent = np.array([], dtype=np.int64)
    t0 = time.time()
    for s in range(steps):
        obs = b.observe()
        ext = org.sense(s, obs)
        sp = org.net.step(external_mv=ext)
        hit = np.isin(mn_idx, sp)
        mn_cnt += hit
        org.motor_step(silent if a.dead else sp)
        q = d.qpos[hadr]
        lim = (q - rng[:, 0] < BAND * span) | (rng[:, 1] - q < BAND * span)
        onlim += lim
        if s % every == 0:
            fz = dict.fromkeys(LEGS, 0.0)
            tc = False
            f6 = np.zeros(6)
            for i in range(d.ncon):
                c = d.contact[i]
                g = c.geom2 if c.geom1 in floor else c.geom1 if c.geom2 in floor else None
                if g is None:
                    continue
                bi = m.geom_bodyid[g]
                mj.mj_contactForce(m, d, i, f6)
                if bi in trunk:
                    tc = True
                elif bi in leg_of_body:
                    fz[leg_of_body[bi]] += float(f6[0])
            xm = d.xmat[thorax].reshape(3, 3)
            rows.append(dict(t_ms=round(s * org.timestep_ms, 1), z_mm=round(float(d.xpos[thorax, 2]), 4),
                             pitch_deg=round(float(np.degrees(np.arcsin(-xm[2, 0]))), 1),
                             roll_deg=round(float(np.degrees(np.arctan2(xm[2, 1], xm[2, 2]))), 1),
                             trunk_floor=tc, leg_fz_uN={k: round(v, 2) for k, v in fz.items()},
                             n_at_limit=int(lim.sum())))
        if s in snaps:
            frames.append((s * org.timestep_ms, shot(m, d, thorax)))
    wall = time.time() - t0
    weight_uN = float(m.body_subtreemass[1] * 9.81e3) if m.opt.gravity[2] else 0.0
    q_end = np.degrees(d.qpos[hadr])
    res = dict(
        tag=tag, seed=a.seed, overrides=ov, profile=WORKING_PROFILE, dead=a.dead, wall_s=round(wall),
        z_place_mm=round(z0, 3), z_end_mm=rows[-1]["z_mm"], z_min_mm=min(r["z_mm"] for r in rows),
        trunk_floor_first_ms=next((r["t_ms"] for r in rows if r["trunk_floor"]), None),
        trunk_floor_frac=round(float(np.mean([r["trunk_floor"] for r in rows])), 2),
        weight_uN=round(weight_uN, 2), gravity=list(map(float, m.opt.gravity)),
        leg_fz_end_uN=rows[-1]["leg_fz_uN"],
        at_limit_frac={n: round(float(f), 2) for n, f in zip(hn, onlim / steps) if f / steps > 0.2},
        q_end_deg={n: round(float(v), 1) for n, v in zip(hn, q_end)},
        mn_hz_by_group={g: round(float(mn_cnt[ix].sum() / len(ix) / (a.ms / 1e3)), 1) for g, ix in sorted(grp.items())},
        mujoco_warnings=int(sum(w.number for w in d.warning)),
    )
    (out / f"standing_{tag}_s{a.seed}.json").write_text(json.dumps(dict(summary=res, trace=rows), indent=1))
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    fig, ax = plt.subplots(len(frames), 1, figsize=(8, 3.0 * len(frames)))
    for a_, (t, img) in zip(ax, frames):
        a_.imshow(img); a_.set_axis_off()
        r = min(rows, key=lambda r: abs(r["t_ms"] - t))
        a_.set_title(f"{tag} seed {a.seed}  t = {t:.0f} ms  thorax z = {r['z_mm']:.2f} mm  (left: side, right: front)",
                     fontsize=9)
    fig.tight_layout(); fig.savefig(out / f"standing_{tag}_s{a.seed}.png", dpi=80); plt.close(fig)
    print(json.dumps(res, indent=1))


if __name__ == "__main__":
    main()
