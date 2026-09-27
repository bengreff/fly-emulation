"""Held-out reflex test against Azevedo 2020 cell 180111_F2_C1 (DECISIONS 6b).

Tethered thorax; left middle femur-tibia held by an external PD probe. Each
condition: go to the start angle, hold 500 ms (last 250 ms = pre), then step
or ramp to the end angle and hold 500 ms. Readout: mean rate of the model's
left-middle slow flexor MNs, windows as in scripts/azevedo_slow_mn.py
(step: transient 0-100 ms, hold 100-500 ms; ramp: transient = ramp duration
(>= 50 ms), hold from ramp end + 50 ms to 500 ms).

    uv run python scripts/probes/azevedo_reflex.py --conds step:-8,step:8,ramp:-8:40
Angles: displacement in deg, + = flexion (Azevedo convention); flexion
starts at theta0, extension starts at theta0 - 8 deg (the recorded offset).
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
    ap.add_argument("--conds", required=True)
    ap.add_argument("--theta0", type=float, default=90.0)
    ap.add_argument("--kp", type=float, default=3.0)
    ap.add_argument("--kd", type=float, default=0.004)
    ap.add_argument("--watch", default="^IN21A006$|^IN21A002$|^IN03A004$|^IN21A004$|^IN13A009$|^IN13A005$")
    ap.add_argument("--set", action="append", default=["motor_unit:all|force_per_spike=10"])
    a = ap.parse_args()
    ov = {k: float(v) for k, v in (s.split("=") for s in a.set)}
    org = Organism(policy="minimal", profile=WORKING_PROFILE, min_synapses=5, overrides=ov)
    dt = org.timestep_ms
    acts = [x.removeprefix(org.body.fly.name + "/").removesuffix("-motor") for x in org.body.actuator_names]
    name, flex_sign = resolve_sign(load_calibration("flybody"), "lm", "FTi", "flexion")
    j = acts.index(name)
    d = org.body.sim.mj_data
    n = org.conn.neurons
    mf = pd.read_csv("data/params/motor_forces.csv", comment="#")
    slow = np.flatnonzero(n.bodyId.isin(mf[(mf.leg == "ml") & (mf.unit_class == "slow")].bodyId).to_numpy())
    state = {"s": 0, "prev": None}
    aff = org.aff
    tab = pd.read_csv("data/params/proprio_assignment.csv", comment="#").set_index("type")
    atype = n.type.fillna("").to_numpy()[aff.rows]
    dirn = pd.Series(atype).map(tab.direction).fillna("").to_numpy()
    groups = {"claw_flex": aff.rows[(aff.leg == "lm") & (aff.subtype == "claw") & (dirn == "flexion")],
              "claw_ext": aff.rows[(aff.leg == "lm") & (aff.subtype == "claw") & (dirn == "extension")],
              "hook_ext": aff.rows[(aff.leg == "lm") & (aff.subtype == "hook_ext")],
              "hook_flex": aff.rows[(aff.leg == "lm") & (aff.subtype == "hook_flex")]}
    tt = n.type.fillna("")
    watch = {t: np.flatnonzero((tt == t).to_numpy() & (n.somaNeuromere == "T2").to_numpy() & (n.somaSide == "L").to_numpy())
             for t in sorted(set(tt[tt.str.match(a.watch)]))}
    watch = {k: v for k, v in watch.items() if len(v)}
    groups.update({f"IN:{k}": v for k, v in watch.items()})
    rec = {"isyn": [], "vwatch": [], **{k: [] for k in groups}}

    for s in range(3000):          # settle free for 300 ms
        obs = org.body.observe()
        sp = org.net.step(external_mv=org.sense(s, obs))
        org.motor_step(sp)
    state["s"] = 3000
    q_tether = d.qpos[:7].copy()

    def run(target_fn, ms):
        """Advance ms with the probe following target_fn(t_ms); return spike times of slow MNs, angles."""
        spikes, ang = [], []
        for i in range(int(ms / dt)):
            d.qpos[:7] = q_tether; d.qvel[:6] = 0.0
            obs = org.body.observe()
            th = org.aff.fti_angle_deg(obs["xpos"], "lm")
            w = 0.0 if state["prev"] is None else (th - state["prev"]) / (dt / 1000)
            state["prev"] = th
            sp = org.net.step(external_mv=org.sense(state["s"], obs))
            tq = org.nm.step(sp, dt).copy()
            tq[j] += flex_sign * (a.kp * (th - target_fn(i * dt)) + a.kd * w)
            org.body.actuate(tq); org.body.set_adhesion(org.nm.grip); org.body.step()
            state["s"] += 1
            spikes.append(np.isin(slow, sp).sum()); ang.append(th)
            rec["isyn"].append(float(org.net.i_syn[slow].mean()))
            rec["vwatch"].append({k: float((org.net.v[v] - org.net.v_rest[v]).mean()) for k, v in watch.items()})
            for k, g in groups.items():
                rec[k].append(np.isin(g, sp).sum() / max(len(g), 1))
        return np.array(spikes), np.array(ang)

    out = []
    for c in a.conds.split(","):
        parts = c.split(":")
        kind, disp = parts[0], float(parts[1])
        speed = float(parts[2]) if kind == "ramp" else np.inf
        start = a.theta0 if disp > 0 else a.theta0 - 8.0
        end = start - disp                      # + disp = flexion = smaller angle
        for v in rec.values():
            v.clear()
        sp0, an0 = run(lambda t: start, 500.0)
        dur = abs(disp) / speed * 1000.0 if kind == "ramp" else 0.0
        tgt = (lambda t: start + (end - start) * min(t / dur, 1.0)) if dur > 0 else (lambda t: end)
        sp1, an1 = run(tgt, 500.0)
        hz = lambda x, a0, a1: x[int(a0 / dt):int(a1 / dt)].sum() / len(slow) / ((a1 - a0) / 1000)  # noqa: E731
        pre = hz(sp0, 250, 500)
        tr1 = max(dur, 50.0) if kind == "ramp" else 100.0
        h0 = dur + 50.0 if kind == "ramp" else 100.0
        out.append({"cond": c, "start": round(start, 1), "end_target": round(end, 1),
                    "theta_pre": round(float(an0[-2500:].mean()), 1),
                    "theta_hold": round(float(an1[int(h0 / dt):].mean()), 1),
                    "pre_hz": round(pre, 1), "d_transient_hz": round(hz(sp1, 0, tr1) - pre, 1),
                    "d_hold_hz": round(hz(sp1, h0, 500) - pre, 1),
                    "isyn_mV_pre_hold": [round(float(np.mean(rec["isyn"][2500:5000])), 2),
                                         round(float(np.mean(rec["isyn"][5000 + int(h0 / dt):])), 2)],
                    "aff_hz_pre_hold": {k: [round(float(np.sum(rec[k][2500:5000])) / 0.25, 1),
                                            round(float(np.sum(rec[k][5000 + int(h0 / dt):])) / ((500 - h0) / 1000), 1)]
                                        for k in groups},
                    "n_aff": {k: int(len(g)) for k, g in groups.items()},
                    "watch_dV_pre_hold": {k: [round(float(np.mean([x[k] for x in rec["vwatch"][2500:5000]])), 2),
                                              round(float(np.mean([x[k] for x in rec["vwatch"][5000 + int(h0 / dt):]])), 2)]
                                          for k in watch}})
        print(json.dumps(out[-1]), flush=True)


if __name__ == "__main__":
    main()
