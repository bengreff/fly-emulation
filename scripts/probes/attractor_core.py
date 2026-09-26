"""F-ORN-2 diagnostic: which cell types are necessary to sustain the attractor?

Runs the closed loop with Hallem ORN rates (seed with a known sustained state),
silences all senses at --ms, then at +100 ms removes the output of one type
group (regex) and reports non-tonic spikes per ms over the last 100 ms.

    uv run python scripts/probes/attractor_core.py --seed 2 --silence '^Lawf2$'
"""
import argparse
import json
import sys

import numpy as np

sys.path.insert(0, "src")
from flyemu.organism import Organism  # noqa: E402
from flyemu.profiles import WORKING_PROFILE  # noqa: E402


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--seed", type=int, default=2)
    ap.add_argument("--ms", type=float, default=1000.0)
    ap.add_argument("--silence", default="")
    a = ap.parse_args()
    ov = {"motor_unit:all|force_per_spike": 10.0, "orn:all|rate_calibration": 1.0}
    org = Organism(policy="minimal", profile=WORKING_PROFILE, min_synapses=5, overrides=ov, seed=a.seed)
    dt = org.timestep_ms
    tonic = np.broadcast_to(np.asarray(org.net.params.spont_mv), (org.conn.n,)) > 0
    t = org.conn.neurons.type.fillna("")
    kill = np.flatnonzero(t.str.match(a.silence).to_numpy()) if a.silence else np.array([], int)
    trace = []
    total = int((a.ms + 400) / dt)
    for s in range(total):
        tm = s * dt
        obs = org.body.observe()
        ext = org.sense(s, obs) if tm < a.ms else np.zeros(org.conn.n, np.float32)
        if kill.size and abs(tm - (a.ms + 100)) < dt / 2:
            org.net.silence(kill)
        sp = org.net.step(external_mv=ext)
        tq = org.nm.step(sp, dt)
        org.body.actuate(tq); org.body.set_adhesion(org.nm.grip); org.body.step()
        trace.append(int((~tonic[sp]).sum()))
    tr = np.array(trace)
    w = lambda a0, a1: round(float(tr[int(a0 / dt):int(a1 / dt)].sum() / (a1 - a0)), 2)  # noqa: E731
    print(json.dumps({"seed": a.seed, "silenced": a.silence, "n_killed": int(kill.size),
                      "sp_per_ms_before_silence": w(a.ms - 100, a.ms),
                      "after_senses_off_100ms": w(a.ms, a.ms + 100),
                      "last_100ms": w(a.ms + 300, a.ms + 400)}))


if __name__ == "__main__":
    main()
