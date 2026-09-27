"""Held-out comparison with Agrawal 2020 13Balpha static tuning (F-VNC-2).

Tethered fly; left front femur-tibia clamped by the PD probe at a staircase
of anatomical angles (30..170 deg, 400 ms each, last 250 ms scored). Reports,
for T1-left cells of a hemilineage prefix, the per-cell Vm slope (mV/deg) and
Vm range. No parameter is changed.

    uv run python scripts/probes/vnc_angle_tuning.py --prefix IN13B
"""
import argparse
import json
import sys

import numpy as np

sys.path.insert(0, "src")
from flyemu.organism import Organism  # noqa: E402
from flyemu.profiles import WORKING_PROFILE  # noqa: E402
from flyemu.neuromuscular import load_calibration, resolve_sign  # noqa: E402

ANG = [30, 50, 70, 90, 110, 130, 150, 170]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--prefix", default="IN13B")
    ap.add_argument("--leg", default="lf", help="lf (T1, as recorded) or lm/lh")
    ap.add_argument("--set", action="append", default=["motor_unit:all|force_per_spike=10"])
    a = ap.parse_args()
    ov = {k: float(v) for k, v in (s.split("=") for s in a.set)}
    org = Organism(policy="minimal", profile=WORKING_PROFILE, min_synapses=5, overrides=ov)
    dt, d, n = org.timestep_ms, org.body.sim.mj_data, org.conn.neurons
    acts = [x.removeprefix(org.body.fly.name + "/").removesuffix("-motor") for x in org.body.actuator_names]
    name, fs = resolve_sign(load_calibration("flybody"), a.leg, "FTi", "flexion")
    j = acts.index(name)
    cells = np.flatnonzero((n.type.fillna("").str.startswith(a.prefix) & (n.somaNeuromere == {"f": "T1", "m": "T2", "h": "T3"}[a.leg[1]])
                            & (n.somaSide == a.leg[0].upper())).to_numpy())
    for s in range(3000):
        obs = org.body.observe(); sp = org.net.step(external_mv=org.sense(s, obs))
        org.motor_step(sp)
    q = d.qpos[:7].copy(); prev = None; s = 3000
    vm, th_ach = [], []
    for target in ANG:
        acc, ths = [], []
        for i in range(4000):
            d.qpos[:7] = q; d.qvel[:6] = 0
            obs = org.body.observe(); th = org.aff.fti_angle_deg(obs["xpos"], a.leg)
            w = 0 if prev is None else (th - prev) / (dt / 1000); prev = th
            sp = org.net.step(external_mv=org.sense(s, obs)); s += 1
            tq = org.nm.step(sp, dt).copy(); tq[j] += fs * (3.0 * (th - target) + 0.004 * w)
            org.body.actuate(tq); org.body.set_adhesion(org.nm.grip); org.body.step()
            if i >= 1500 and i % 10 == 0:
                acc.append(org.net.v[cells].copy()); ths.append(th)
        vm.append(np.mean(acc, axis=0)); th_ach.append(np.mean(ths))
    vm = np.array(vm)
    slopes = np.array([np.polyfit(th_ach, vm[:, c], 1)[0] for c in range(len(cells))])
    print(json.dumps({"prefix": a.prefix, "leg": a.leg, "cells": int(len(cells)), "theta": [round(x, 1) for x in th_ach],
                      "slope_mV_per_deg_p10_p50_p90": [round(float(x), 4) for x in np.percentile(slopes, [10, 50, 90])],
                      "frac_slope_above_0.012": round(float((slopes > 0.012).mean()), 2),
                      "vm_range_mean_over_cells": [round(float(vm.min(axis=0).mean()), 1), round(float(vm.max(axis=0).mean()), 1)],
                      "overrides": ov}))


if __name__ == "__main__":
    main()
