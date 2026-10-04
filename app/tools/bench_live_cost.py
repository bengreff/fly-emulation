"""Measure what a live session costs on this machine: build time, wall time
per simulated second of the closed loop, and peak memory, for one profile.

    .venv/bin/python app/tools/bench_live_cost.py --profile m9 --steps 200

Reads the model only through its public API (Organism, sense, net.step,
motor_step). Bounded: one organism, a fixed number of steps.
"""
from __future__ import annotations

import argparse
import json
import resource
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))

from flyemu.organism import Organism  # noqa: E402


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--profile", default="m9")
    ap.add_argument("--steps", type=int, default=200)
    ap.add_argument("--warmup", type=int, default=20)
    ap.add_argument("--brain-only", action="store_true",
                    help="step the network with no sensory drive and no body")
    args = ap.parse_args()

    t0 = time.perf_counter()
    org = Organism(policy="minimal", seed=0, profile=args.profile, min_synapses=5,
                   overrides={"motor_unit:all|force_per_spike": 10.0})
    build_s = time.perf_counter() - t0

    def one(step: int) -> None:
        if args.brain_only:
            org.net.step(external_mv=None)
            return
        obs = org.body.observe()
        spiked = org.net.step(external_mv=org.sense(step, obs))
        org.motor_step(spiked)

    for s in range(args.warmup):
        one(s)
    t1 = time.perf_counter()
    for s in range(args.warmup, args.warmup + args.steps):
        one(s)
    run_s = time.perf_counter() - t1
    sim_ms = args.steps * org.timestep_ms
    rss_gb = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1e9   # bytes on macOS
    print(json.dumps({
        "profile": args.profile, "brain_only": args.brain_only,
        "neurons": int(org.conn.n), "edges": int(org.conn.n_edges),
        "timestep_ms": org.timestep_ms, "steps": args.steps,
        "build_s": round(build_s, 1),
        "wall_s_per_sim_s": round(run_s / (sim_ms / 1000.0), 1),
        "ms_per_step": round(1000 * run_s / args.steps, 2),
        "peak_rss_gb": round(rss_gb, 2),
        "spikes_total": int(org.net.spike_count),
    }))
    return 0


if __name__ == "__main__":
    sys.exit(main())
