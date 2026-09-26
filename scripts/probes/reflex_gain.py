"""Resistance-reflex gain, protocol after Azevedo et al. 2020 (tethered fly, tibia
moved by a probe, tibia MNs recorded).

The thorax is kinematically tethered at its settled pose; the left middle
femur-tibia joint is held by an external PD position clamp (the "probe") at a
staircase of anatomical angles. Reports each tibia MN class's rate per angle
(first 50 ms after each step excluded) and the slope in Hz/deg.

    uv run python scripts/probes/reflex_gain.py [--set K=V ...]
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

ANGLES = [120, 100, 80, 60, 40, 60, 80, 100, 120]
HOLD_MS = 250.0


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--set", action="append", default=["motor_unit:all|force_per_spike=10"])
    ap.add_argument("--kp", type=float, default=1.0, help="uN*mm per deg")
    ap.add_argument("--kd", type=float, default=0.002, help="uN*mm per deg/s")
    a = ap.parse_args()
    ov = {k: float(v) for k, v in (s.split("=") for s in a.set)}
    org = Organism(policy="minimal", profile=WORKING_PROFILE, min_synapses=5, overrides=ov)
    dt = org.timestep_ms
    acts = [x.removeprefix(org.body.fly.name + "/").removesuffix("-motor") for x in org.body.actuator_names]
    name, flex_sign = resolve_sign(load_calibration("flybody"), "lm", "FTi", "flexion")
    j = acts.index(name)
    d = org.body.sim.mj_data
    n = org.conn.neurons
    t = n.type.fillna("")
    mf = pd.read_csv("data/params/motor_forces.csv", comment="#")
    lm = (n.somaNeuromere == "T2") & (n.somaSide == "L")
    rows = {c: np.flatnonzero(n.bodyId.isin(mf[(mf.leg == "ml") & (mf.unit_class == c)].bodyId).to_numpy())
            for c in ["slow", "intermediate", "fast"]}
    rows["extensor"] = np.flatnonzero((t.str.startswith("Ti extensor") & lm).to_numpy())
    # settle 300 ms free, then tether the thorax where it is
    for s in range(3000):
        obs = org.body.observe()
        sp = org.net.step(external_mv=org.sense(s, obs))
        org.body.actuate(org.nm.step(sp, dt)); org.body.set_adhesion(org.nm.grip); org.body.step()
    q_tether = d.qpos[:7].copy()
    out, s0 = [], 3000
    theta_prev = None
    for k, target in enumerate(ANGLES):
        cnt = {c: 0 for c in rows}
        th_log = []
        for i in range(int(HOLD_MS / dt)):
            s = s0 + k * int(HOLD_MS / dt) + i
            d.qpos[:7] = q_tether; d.qvel[:6] = 0.0
            obs = org.body.observe()
            th = org.aff.fti_angle_deg(obs["xpos"], "lm")
            w = 0.0 if theta_prev is None else (th - theta_prev) / (dt / 1000)
            theta_prev = th
            sp = org.net.step(external_mv=org.sense(s, obs))
            tq = org.nm.step(sp, dt).copy()
            # probe: + flex_sign torque flexes (lowers theta)
            tq[j] += flex_sign * (a.kp * (th - target) + a.kd * w)
            org.body.actuate(tq); org.body.set_adhesion(org.nm.grip); org.body.step()
            if i * dt >= 50:
                for c, r in rows.items():
                    cnt[c] += np.isin(r, sp).sum()
                th_log.append(th)
        dur = (HOLD_MS - 50) / 1000
        out.append({"target": target, "theta": round(float(np.mean(th_log)), 1),
                    **{c: round(cnt[c] / max(len(rows[c]), 1) / dur, 1) for c in rows}})
    df = pd.DataFrame(out)
    slope = {c: round(float(np.polyfit(df.theta, df[c], 1)[0]), 3) for c in rows}
    print(df.to_string(index=False))
    print(json.dumps({"hz_per_deg": slope, "n_cells": {c: len(r) for c, r in rows.items()},
                      "overrides": ov}))


if __name__ == "__main__":
    main()
