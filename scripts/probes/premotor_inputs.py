"""Diagnostic: steady-state synaptic input to chosen VNC cells, by presynaptic type.

Tethered fly, left middle FTi clamped at --theta for 800 ms (rates from the
last 500 ms). For each target cell, the mean steady input from presynaptic
cell j is  w_ij * rate_j * tau_s  (mV, current-based m2), summed by type.

    uv run python scripts/probes/premotor_inputs.py --targets '^IN03A004$|^IN21A004$|^IN21A006$'
"""
import argparse
import sys

import numpy as np
import pandas as pd

sys.path.insert(0, "src")
from flyemu.organism import Organism  # noqa: E402
from flyemu.profiles import WORKING_PROFILE  # noqa: E402
from flyemu.neuromuscular import load_calibration, resolve_sign  # noqa: E402


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--targets", default="^IN03A004$|^IN21A004$|^IN21A006$")
    ap.add_argument("--theta", type=float, default=82.0)
    ap.add_argument("--set", action="append", default=["motor_unit:all|force_per_spike=10"])
    a = ap.parse_args()
    ov = {k: float(v) for k, v in (s.split("=") for s in a.set)}
    org = Organism(policy="minimal", profile=WORKING_PROFILE, min_synapses=5, overrides=ov)
    dt, d, n = org.timestep_ms, org.body.sim.mj_data, org.conn.neurons
    acts = [x.removeprefix(org.body.fly.name + "/").removesuffix("-motor") for x in org.body.actuator_names]
    name, fs = resolve_sign(load_calibration("flybody"), "lm", "FTi", "flexion")
    j = acts.index(name)
    for s in range(3000):
        obs = org.body.observe(); sp = org.net.step(external_mv=org.sense(s, obs))
        org.body.actuate(org.nm.step(sp, dt)); org.body.set_adhesion(org.nm.grip); org.body.step()
    q = d.qpos[:7].copy(); cnt = np.zeros(org.conn.n); prev = None
    for i in range(8000):
        d.qpos[:7] = q; d.qvel[:6] = 0
        obs = org.body.observe(); th = org.aff.fti_angle_deg(obs["xpos"], "lm")
        w = 0 if prev is None else (th - prev) / (dt / 1000); prev = th
        sp = org.net.step(external_mv=org.sense(3000 + i, obs))
        tq = org.nm.step(sp, dt).copy(); tq[j] += fs * (3.0 * (th - a.theta) + 0.004 * w)
        org.body.actuate(tq); org.body.set_adhesion(org.nm.grip); org.body.step()
        if i >= 3000:
            cnt[sp] += 1
    hz = cnt / 0.5
    t = n.type.fillna("untyped").to_numpy()
    tgt = np.flatnonzero(pd.Series(t).str.match(a.targets).to_numpy()
                        & (n.somaNeuromere == "T2").to_numpy() & (n.somaSide == "L").to_numpy())
    ip, ix = org.conn.indptr, org.conn.indices
    pre = np.repeat(np.arange(org.conn.n), np.diff(ip))
    tau_s = np.broadcast_to(np.asarray(org.net.params.tau_s, float), (org.conn.n,))
    for c in tgt:
        m = ix == c
        contrib = org.net.w[m] * hz[pre[m]] * tau_s[c] / 1000.0
        df = pd.DataFrame({"type": t[pre[m]], "nt": n.predictedNt.fillna("?").to_numpy()[pre[m]],
                           "syn": org.conn.weight_syn[m], "pre_hz": hz[pre[m]], "mV": contrib})
        g = df.groupby(["type", "nt"]).agg(syn=("syn", "sum"), hz=("pre_hz", "mean"), mV=("mV", "sum"))
        print(f"== {t[c]} (row {c}) rate {hz[c]:.1f} Hz, V-Vrest now {org.net.v[c]-org.net.v_rest[c]:.2f} mV,"
              f" net steady input {df.mV.sum():.2f} mV; excit {df.mV[df.mV>0].sum():.2f}, inhib {df.mV[df.mV<0].sum():.2f}")
        print(g[g.mV.abs() > 0.05].sort_values("mV").to_string())
    vnc = (n.superclass.fillna("") == "vnc_intrinsic").to_numpy() & (n.somaNeuromere == "T2").to_numpy()
    print(f"\nT2 vnc_intrinsic cells: {vnc.sum()}, fraction active (>0.5 Hz): {(hz[vnc] > 0.5).mean():.2f}, "
          f"median rate of active {np.median(hz[vnc][hz[vnc] > 0.5]) if (hz[vnc] > 0.5).any() else 0:.1f} Hz")


if __name__ == "__main__":
    main()
