"""Does a brief kick to the EPG ring leave persistent activity? (session 7, exploratory)

Default working model, closed loop. 300 ms settle, then Poisson-like kicks to
N EPG cells (one wedge-contiguous block by bodyId order is not guaranteed; the
first N EPGs of the table) for 50 ms, then all sensory input silenced for 400 ms.
Reports EPG / PEN / Delta7 active counts and rates in the last 200 ms.

    uv run python scripts/probes/cx_kick.py [--n 6] [--mv 3] [--set K=V ...]
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
    ap.add_argument("--n", type=int, default=6)
    ap.add_argument("--mv", type=float, default=3.0, help="kick per step while stimulated")
    ap.add_argument("--set", action="append", default=["motor_unit:all|force_per_spike=10"])
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--targets", default="EPG", help="comma-separated type prefixes to kick (all cells)")
    ap.add_argument("--kick-ms", type=float, default=50.0)
    a = ap.parse_args()
    ov = {k: float(v) for k, v in (s.split("=") for s in a.set)}
    org = Organism(policy="minimal", profile=WORKING_PROFILE, min_synapses=5, overrides=ov, seed=a.seed)
    t = org.conn.neurons.type.fillna("").to_numpy().astype(str)
    groups = {g: np.flatnonzero(np.char.startswith(t, g)) for g in ("EPG", "PEN_", "Delta7", "PEG", "ER")}
    epg = groups["EPG"]
    target = epg[: a.n] if a.targets == "EPG" else np.flatnonzero(
        np.any([np.char.startswith(t, g) for g in a.targets.split(",")], axis=0))
    dt = org.timestep_ms
    cnt = np.zeros(org.conn.n)
    for s in range(int((700 + a.kick_ms) / dt)):
        obs = org.body.observe()
        ms = s * dt
        ext = org.sense(s, obs) if ms < 300 + a.kick_ms else np.zeros(org.conn.n, np.float32)
        if 300 <= ms < 300 + a.kick_ms:
            ext = ext.copy(); ext[target] += a.mv
        sp = org.net.step(external_mv=ext)
        if ms >= 500 + a.kick_ms:
            cnt[sp] += 1
        org.body.actuate(org.nm.step(sp, dt)); org.body.set_adhesion(org.nm.grip); org.body.step()
    hz = cnt / 0.2
    out = {g: {"cells": len(ix), "active": int((hz[ix] > 0).sum()), "mean_hz": round(float(hz[ix].mean()), 1)}
           for g, ix in groups.items()}
    out.update(n_kicked=a.n, kick_mv=a.mv, overrides=ov, brain_hz_last200=round(float(hz.mean()), 3))
    print(json.dumps(out))


if __name__ == "__main__":
    main()
