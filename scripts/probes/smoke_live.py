"""'Does it live' smoke metric (s13, Director brief 8 Oct): how much the body moves on its own,
and the resting-rate distribution, with the frontier-profile smoke checks (no runaway, no NaN).

Closed loop, all senses on, the default resting world. Reports:
- movement: summed hinge-joint speed (rad/s, i.e. joint path length per second) per body part,
  thorax path length and net displacement, the fraction of 100 ms bins in which any joint moves
  faster than --move-thresh rad/s; over [--skip-ms, end] and over the first 10 s of that window;
- rates: per-neuron rates over [--skip-ms, end]; whole-brain mean, fraction active (> 0 Hz and
  > 1 Hz), percentiles, per circuit class and superclass; per-1-s spike totals (stationarity);
- runaway (> 20000 spikes in a step aborts), NaN in body or brain state, MuJoCo warnings.
--dead removes every motor neuron spike before the muscles (passive floor for the movement metric).

    uv run python scripts/probes/smoke_live.py --profile m9c --ms 10000 --seed 12 --out x.json
"""
import argparse
import json
import sys
import time

import numpy as np

sys.path.insert(0, "src")
from flyemu.organism import Organism  # noqa: E402

PARTS = (("leg", ("coxa", "femur", "tibia", "tarsus", "trochanter")), ("wing", ("wing",)),
         ("head", ("head",)), ("abdomen", ("abdomen",)), ("antenna", ("antenna", "arista", "funiculus")),
         ("proboscis", ("rostrum", "haustellum", "labrum")), ("haltere", ("haltere",)))


def part_of(name: str) -> str:
    for p, keys in PARTS:
        if any(k in name for k in keys):
            return p
    return "other"


def summarize(a, ov, build_s, wall, runaway, org, d, n, steps, skip, dt, speed_bins, xyz, cnt, sec_tot,
              part, cls, sup, rates_out=""):
    out = {"profile": a.profile, "seed": a.seed, "ms": steps * dt, "skip_ms": a.skip_ms, "dead": a.dead,
           "overrides": ov, "build_s": round(build_s), "wall_s": round(wall), "runaway_at_ms": runaway}
    nan = bool(not np.isfinite(d.qpos).all() or not np.isfinite(org.net.v).all())
    out["nan_state"] = nan
    out["mujoco_warnings"] = int(sum(w.number for w in d.warning))
    if runaway is None and speed_bins:
        sb = np.array(speed_bins)                         # (bins, joints) rad/s
        first10 = sb[:100]
        def mv(x):
            return {"total_rad_per_s": round(float(x.sum(1).mean()), 4),
                    "by_part_rad_per_s": {p: round(float(x[:, part == p].sum(1).mean()), 4)
                                          for p in sorted(set(part))},
                    "frac_bins_moving": round(float((x.max(1) > a.move_thresh).mean()), 3),
                    "p95_bin_total": round(float(np.percentile(x.sum(1), 95)), 4)}
        out["movement_all"] = mv(sb)
        out["movement_first10s"] = mv(first10)
        X = np.array(xyz)
        out["thorax_path_mm"] = round(float(np.linalg.norm(np.diff(X, axis=0), axis=1).sum()), 4)
        out["thorax_net_mm"] = round(float(np.linalg.norm(X[-1] - X[0])), 4)
        out["thorax_z_mm"] = {"min": round(float(X[:, 2].min()), 3), "final": round(float(X[-1, 2]), 3)}
        dur = (steps - skip) * dt / 1000.0
        hz = cnt / dur
        act = hz[hz > 0]
        out["rates"] = {
            "whole_brain_hz": round(float(hz.mean()), 4),
            "frac_active": round(float((hz > 0).mean()), 4),
            "frac_above_1hz": round(float((hz > 1).mean()), 4),
            "median_active_hz": round(float(np.median(act)), 3) if act.size else 0.0,
            "pct_hz": {str(q): round(float(np.percentile(hz, q)), 3) for q in (50, 75, 90, 95, 99, 99.9)},
            "max_hz": round(float(hz.max()), 1),
            "per_second_spikes": list(sec_tot),
        }
        out["hz_by_class"] = {c: [round(float(hz[cls == c].mean()), 4), round(float((hz[cls == c] > 0).mean()), 3)]
                              for c in np.unique(cls)}
        out["hz_by_superclass"] = {c: [round(float(hz[sup == c].mean()), 4), round(float((hz[sup == c] > 0).mean()), 3)]
                                   for c in np.unique(sup)}
        if rates_out:
            np.savez_compressed(rates_out, hz=hz.astype(np.float32), body_id=n.bodyId.to_numpy())
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--profile", default="m9c")
    ap.add_argument("--ms", type=float, default=10000.0)
    ap.add_argument("--skip-ms", type=float, default=500.0, help="opening transient left out of every metric")
    ap.add_argument("--seed", type=int, default=12)
    ap.add_argument("--set", action="append", default=[])
    ap.add_argument("--dead", action="store_true", help="no motor neuron spike reaches the muscles")
    ap.add_argument("--move-thresh", type=float, default=0.5, help="rad/s; a bin 'moves' above this")
    ap.add_argument("--out", default="")
    ap.add_argument("--rates-out", default="", help="per-neuron rates (npz) for offline scoring")
    a = ap.parse_args()
    ov = {k: float(v) for k, v in (s.split("=", 1) for s in a.set)}
    t_build = time.time()
    org = Organism(policy="minimal", profile=a.profile, min_synapses=5, overrides=ov, seed=a.seed)
    import mujoco as mj
    m = org.body.sim.mj_model
    d = org.body.sim.mj_data
    hinge = [j for j in range(m.njnt) if m.jnt_type[j] == mj.mjtJoint.mjJNT_HINGE]
    names = [mj.mj_id2name(m, mj.mjtObj.mjOBJ_JOINT, j) or f"j{j}" for j in hinge]
    dof = np.array([m.jnt_dofadr[j] for j in hinge])
    part = np.array([part_of(nm) for nm in names])
    n = org.conn.neurons
    mn = n.superclass.fillna("").isin(["vnc_motor", "cb_motor"]).to_numpy()
    from flyemu.lif import circuit_classes
    cls = circuit_classes(org.conn)
    sup = n.superclass.fillna("none").to_numpy().astype(str)
    dt = org.timestep_ms
    steps, skip = int(a.ms / dt), int(a.skip_ms / dt)
    per_ms = int(round(1.0 / dt))
    ck = skip + int(10000 / dt)
    cnt = np.zeros(org.conn.n)
    sec_tot, sec_cur = [], 0
    speed_bins, cur_bin, xyz = [], np.zeros(len(hinge)), []
    runaway = None
    t0 = time.time()
    build_s = t0 - t_build
    for s in range(steps):
        obs = org.body.observe()
        ext = org.sense(s, obs)
        sp = org.net.step(external_mv=ext)
        if sp.size > 20000:
            runaway = s * dt
            break
        if s >= skip:
            cnt[sp] += 1
            sec_cur += sp.size
            if (s - skip + 1) % (1000 * per_ms) == 0:
                sec_tot.append(int(sec_cur)); sec_cur = 0
        org.motor_step(sp[~mn[sp]] if a.dead else sp)
        if s >= skip:
            cur_bin += np.abs(d.qvel[dof]) * dt / 1000.0       # rad moved this step
            if (s - skip + 1) % (100 * per_ms) == 0:
                speed_bins.append(cur_bin / 0.1); cur_bin = np.zeros(len(hinge))   # rad/s per bin
            if (s - skip) % (10 * per_ms) == 0:
                xyz.append(np.asarray(obs["body_positions"][0, :3], float).copy())
        if a.out and s + 1 == ck and ck < steps:            # early 'does it live' read (first 10 s after skip)
            o = summarize(a, ov, build_s, time.time() - t0, None, org, d, n, s + 1, skip, dt, speed_bins, xyz,
                          cnt.copy(), sec_tot, part, cls, sup)
            with open(a.out.replace(".json", "") + ".10s.json", "w") as f:
                json.dump(o, f)
    wall = time.time() - t0
    out = summarize(a, ov, build_s, wall, runaway, org, d, n, steps, skip, dt, speed_bins, xyz, cnt, sec_tot,
                    part, cls, sup, a.rates_out)
    print(json.dumps(out))
    if a.out:
        with open(a.out, "w") as f:
            json.dump(out, f)


if __name__ == "__main__":
    main()
