"""Standing and resistance-reflex probe (DECISIONS session 6 pre-registration).

    uv run python scripts/probes/standing.py [--silence-motor] [--push] [--set K=V ...]

Reports thorax height over 0.5-1.5 s, body roll/pitch, afferent subtype
activity, leg motor-neuron rates; with --push, imposes an external flexion
torque on the left middle femur-tibia joint for 200 ms at t=0.9 s and reports
the signed torque of that joint's motor units (resistance = opposes the push).
"""
import argparse
import json
import sys

import numpy as np
import pandas as pd

sys.path.insert(0, "src")
from flyemu.organism import Organism  # noqa: E402
from flyemu.profiles import WORKING_PROFILE  # noqa: E402
from flyemu.neuromuscular import load_calibration, resolve_sign  # noqa: E402


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--ms", type=float, default=1500.0)
    ap.add_argument("--silence-motor", action="store_true")
    ap.add_argument("--push", action="store_true")
    ap.add_argument("--push-torque", type=float, default=20.0, help="uN*mm")
    ap.add_argument("--set", action="append", default=["motor_unit:all|force_per_spike=10"])
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--zero-joints", default="", help="diagnostic: regex of actuators whose torque is zeroed")
    a = ap.parse_args()
    ov = {k: float(v) for k, v in (s.split("=") for s in a.set)}
    org = Organism(policy="minimal", profile=WORKING_PROFILE, min_synapses=5, overrides=ov, seed=a.seed)
    dt = org.timestep_ms
    acts = [x.removeprefix(org.body.fly.name + "/").removesuffix("-motor") for x in org.body.actuator_names]
    cal = load_calibration("flybody")
    name, flex_sign = resolve_sign(cal, "lm", "FTi", "flexion")
    j_act = acts.index(name)
    import re
    zero = [i for i, x in enumerate(acts) if a.zero_joints and re.search(a.zero_joints, x)]
    unit_on_j = org.nm.actuator_index == j_act
    n = org.conn.neurons
    aff = org.aff
    st = aff.subtype if aff.subtype is not None else np.array([""] * len(aff.rows))
    mn = n.superclass.fillna("").to_numpy() == "vnc_motor"
    z, rp, cnt, fti = [], [], np.zeros(org.conn.n), []
    pre_tq, push_tq = [], []
    tt = n.type.fillna("")
    lm_mask = lambda k: np.flatnonzero((tt.str.startswith(k) & (n.somaNeuromere == "T2") & (n.somaSide == "L")).to_numpy())  # noqa: E731
    groups = {"lm_claw": aff.rows[(aff.leg == "lm") & (st == "claw")],
              "lm_hook_flex": aff.rows[(aff.leg == "lm") & (st == "hook_flex")],
              "lm_Ti_flexor": np.r_[lm_mask("Ti flexor"), lm_mask("Acc. ti flexor")],
              "lm_Ti_extensor": lm_mask("Ti extensor")}
    wcount = {k: np.zeros(2) for k in groups}
    t0, t1 = 900.0, 1100.0
    for s in range(int(a.ms / dt)):
        t = s * dt
        obs = org.body.observe()
        sp = org.net.step(external_mv=org.sense(s, obs))
        if t >= 500:
            cnt[sp] += 1
        tq = org.nm.step(sp, dt)
        if a.silence_motor:
            tq = np.zeros_like(tq)
        signed = float(np.sum(org.nm.unit[unit_on_j] * 1.0)) * flex_sign   # + = flexor torque
        for k, g in groups.items():
            if t0 - 200 <= t < t1:
                wcount[k][int(t >= t0)] += np.isin(g, sp).sum()
        if t0 <= t < t1:
            if a.push:
                tq = tq.copy(); tq[j_act] += flex_sign * a.push_torque
            push_tq.append(signed)
        elif t0 - 200 <= t < t0:
            pre_tq.append(signed)
        if zero:
            tq[zero] = 0.0
        org.body.actuate(tq); org.body.set_adhesion(org.nm.grip); org.body.step()
        if s % 50 == 0:
            z.append((t, float(obs["body_positions"][0, 2])))
            q = org.body.sim.mj_data.qpos[3:7]
            w, x, y, zq = q
            roll = np.degrees(np.arctan2(2 * (w * x + y * zq), 1 - 2 * (x * x + y * y)))
            pitch = np.degrees(np.arcsin(np.clip(2 * (w * y - zq * x), -1, 1)))
            rp.append((roll, pitch))
            if aff.fti_bodies is not None:
                fti.append((t, aff.fti_angle_deg(obs["xpos"], "lm")))
    z = pd.DataFrame(z, columns=["t", "z"])
    win = z[(z.t >= 500) & (z.t <= 1500)]
    rp = np.abs(np.array(rp)[len(rp) // 3:])
    hz = cnt / ((a.ms - 500) / 1000)
    rows = aff.rows
    act = {k: round(float(hz[rows[st == k]].mean()), 2) for k in np.unique(st) if k}
    act["campaniform"] = round(float(hz[rows[aff.channel == "load"]].mean()), 2)
    mtype = n.type.fillna("").to_numpy()
    out = {
        "z_min_0.5_1.5": round(float(win.z.min()), 3), "z_mean": round(float(win.z.mean()), 3),
        "stands_height": bool(win.z.min() >= 0.90),
        "max_abs_roll_pitch_deg": [round(float(x), 1) for x in rp.max(axis=0)],
        "afferent_hz": act,
        "mn_hz": {k: round(float(hz[mn & np.char.startswith(mtype.astype(str), k)].mean()), 2)
                  for k in ["Ti flexor", "Acc. ti flexor", "Ti extensor", "Tr flexor", "Tr extensor",
                            "Sternotrochanter", "Tergopleural"]},
        "fti_lm_deg_range": [round(min(f for _, f in fti), 1), round(max(f for _, f in fti), 1)] if fti else None,
        "silence_motor": a.silence_motor, "overrides": ov,
    }
    if True:
        f = pd.DataFrame(fti, columns=["t", "a"])
        out["push"] = {
            "fti_before_deg": round(float(f[(f.t >= t0 - 50) & (f.t < t0)].a.mean()), 1),
            "fti_during_min_deg": round(float(f[(f.t >= t0) & (f.t < t1)].a.min()), 1),
            "mn_flexor_torque_pre": round(float(np.mean(pre_tq)), 3),
            "mn_flexor_torque_push": round(float(np.mean(push_tq)), 3),
            "resists": bool(np.mean(push_tq) < np.mean(pre_tq) - 0.05), "pushed": a.push,
            "window_hz_pre_push": {k: [round(float(v[0] / max(len(groups[k]), 1) / 0.2), 1),
                                       round(float(v[1] / max(len(groups[k]), 1) / 0.2), 1)]
                                   for k, v in wcount.items()},
        }
    print(json.dumps(out))


if __name__ == "__main__":
    main()
