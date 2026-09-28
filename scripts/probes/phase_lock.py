"""N17 probe (s10): do steering MNs phase-lock to the wingbeat in tethered flight?

Thorax held fixed; wingbeat generator forced on (B10); haltere/wing campaniforms
driven by the beating body (N16 proxies); haltere CS -> b1 MN electrical coupling
set by --k (N12). Reports spike counts and the vector strength of b1 MN and haltere
afferent spikes relative to the generator's stroke phase.

    uv run python scripts/probes/phase_lock.py --k 10 --ms 200
"""
import argparse
import json
import sys

import numpy as np

sys.path.insert(0, "src")
from flyemu.organism import Organism  # noqa: E402


def vs(phases):
    return float(np.abs(np.exp(1j * np.asarray(phases)).mean())) if len(phases) else float("nan")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--k", type=float, default=10.0)
    ap.add_argument("--ms", type=float, default=200.0)
    ap.add_argument("--gain", type=float, default=8.0, help="sense:mechano_extra|gain")
    a = ap.parse_args()
    ov = {"flight:wings|generator": 2.0, "joint:wing|range_by_function": 1.0,
          "electrical:SNpp25->b1 MN|spike_coupling": a.k, "electrical:SNpp34->b1 MN|spike_coupling": a.k,
          "sense:mechano_extra|gain": a.gain}
    org = Organism(policy="minimal", profile="m4", min_synapses=5, timestep_ms=0.05, overrides=ov)
    d = org.body.sim.mj_data
    t = org.conn.neurons.type.fillna("").to_numpy()
    b1 = np.flatnonzero(t == "b1 MN")
    hal = org.extra.channels["haltere_cs"].rows
    q0 = d.qpos[:7].copy()
    f = org.flight.wing.kin.f_hz
    ph_b1, ph_h, n_h = [], [], 0
    for s in range(int(a.ms / org.timestep_ms)):
        obs = org.body.observe()
        sp = org.net.step(external_mv=org.sense(s, obs))
        org.motor_step(sp)
        d.qpos[:7] = q0; d.qvel[:6] = 0.0
        ph = 2 * np.pi * f * org.flight.wing.t_s
        if s * org.timestep_ms < 50:
            continue
        if sp.size:
            k = np.isin(sp, b1).sum()
            ph_b1 += [ph] * int(k)
            kh = np.isin(sp, hal).sum()
            n_h += int(kh)
            ph_h += [ph] * int(kh)
    dur = (a.ms - 50) / 1000
    print(json.dumps(dict(k_mv=a.k, b1_hz=len(ph_b1) / dur / max(len(b1), 1), b1_vector_strength=vs(ph_b1),
                          haltere_cs_hz=n_h / dur / max(len(hal), 1), haltere_vector_strength=vs(ph_h),
                          wingbeats=round(dur * f), mujoco_warnings=int(sum(w.number for w in d.warning)))))
