"""Exploratory (not pre-registered): stimulate a descending command type in
closed loop and look for stepping. A reproduction attempt of command-neuron
activation experiments (DNg100: Bidaye et al. 2020; Pugliese et al. 2025).

Kicks every cell of --type at --hz (Poisson, Shiu kick) during 300-1300 ms.
Reports per-leg tarsal-tip fore-aft oscillation (dominant frequency 3-25 Hz and
its power share), the thorax displacement, and the leg MN rates.

    uv run python scripts/probes/command_walk.py --type DNg100 --hz 100
"""
import argparse
import json
import sys

import mujoco
import numpy as np

sys.path.insert(0, "src")
from flyemu.organism import Organism  # noqa: E402

LEGS = ["lf", "lm", "lh", "rf", "rm", "rh"]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--type", default="DNg100")
    ap.add_argument("--hz", type=float, default=100.0)
    ap.add_argument("--set", action="append", default=["motor_unit:all|force_per_spike=10"])
    a = ap.parse_args()
    ov = {k: float(v) for k, v in (s.split("=") for s in a.set)}
    org = Organism(policy="minimal", profile="m2", min_synapses=5, overrides=ov)
    dt = org.timestep_ms
    n = org.conn.neurons
    stim = np.flatnonzero(n.type.fillna("").eq(a.type).to_numpy())
    m, d = org.body.sim.mj_model, org.body.sim.mj_data
    pre = org.body.fly.name + "/"
    tips = [mujoco.mj_name2id(m, mujoco.mjtObj.mjOBJ_BODY, pre + f"{l}_tarsus5") for l in LEGS]
    th = mujoco.mj_name2id(m, mujoco.mjtObj.mjOBJ_BODY, pre + "c_thorax")
    rng = np.random.default_rng(1)
    X, P = [], []
    mn = (n.superclass.fillna("") == "vnc_motor").to_numpy()
    cnt = np.zeros(org.conn.n)
    for s in range(int(1400 / dt)):
        t = s * dt
        obs = org.body.observe()
        kick = None
        if a.hz > 0 and 300 <= t < 1300:
            kick = (stim[rng.random(stim.size) < a.hz * dt / 1000], org.kick_mv)
        sp = org.net.step(external_mv=org.sense(s, obs), kick=kick)
        if 300 <= t < 1300:
            cnt[sp] += 1
        org.body.actuate(org.nm.step(sp, dt)); org.body.set_adhesion(org.nm.grip); org.body.step()
        if s % 10 == 0:                      # 1 kHz sampling
            R = d.xmat[th].reshape(3, 3)
            rel = (d.xpos[tips] - d.xpos[th]) @ R   # body frame
            X.append(rel[:, 0]); P.append(d.xpos[th].copy())
    X = np.array(X)[300:1300]; P = np.array(P)
    out = {}
    for i, l in enumerate(LEGS):
        x = X[:, i] - X[:, i].mean()
        f = np.fft.rfftfreq(len(x), 1e-3); pw = np.abs(np.fft.rfft(x)) ** 2
        band = (f >= 3) & (f <= 25)
        k = np.argmax(pw * band)
        out[l] = {"f_hz": round(float(f[k]), 1), "band_share": round(float(pw[band].sum() / pw[1:].sum()), 2),
                  "amp_mm": round(float(x.std() * 2), 3)}
    hz = cnt / 1.0
    print(json.dumps({"type": a.type, "n_stim": int(stim.size), "hz": a.hz,
                      "stim_rate_obs": round(float(hz[stim].mean()), 1),
                      "thorax_dx_mm": round(float(P[1300, 0] - P[300, 0]), 3),
                      "thorax_dy_mm": round(float(P[1300, 1] - P[300, 1]), 3),
                      "leg_mn_hz": round(float(hz[mn].mean()), 2), "legs": out}))


if __name__ == "__main__":
    main()
