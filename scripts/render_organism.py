"""Render the closed loop to video, so the behaviour can be watched.

    uv run python scripts/render_organism.py --duration-ms 500 \
        --set 'motor_unit:all|force_per_spike=10'

Every override is printed and recorded. A video is a communication artifact,
not evidence (docs/VALIDATION.md); the numbers come from the run records.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

import numpy as np

from flyemu.organism import Organism

REPO = Path(__file__).resolve().parents[1]


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--duration-ms", type=float, default=500.0)
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--set", action="append", default=[])
    ap.add_argument("--playback-speed", type=float, default=0.05)
    ap.add_argument("--out", default="runs/organism_video.mp4")
    args = ap.parse_args()

    overrides = {}
    for item in args.set:
        k, _, v = item.partition("=")
        overrides[k] = float(v)
    for k, v in overrides.items():
        print(f"override: {k} = {v}")

    org = Organism(policy="minimal", seed=args.seed, overrides=overrides)
    org.body.with_camera = True
    # Rebuild the body with a camera attached, then re-point the interfaces.
    from flyemu.body import Body
    from flyemu import neuromuscular, sensory
    org.body = Body(timestep=org.timestep_ms / 1000.0, with_camera=True)
    org.nm = neuromuscular.build(org.reg, org.conn, org.body.actuator_names)
    org.aff = sensory.build(org.reg, org.conn, org.body)

    renderer = org.body.sim.set_renderer(
        f"{org.body.fly.name}/trackcam", camera_res=(480, 640), playback_speed=args.playback_speed,
        output_fps=30,
    )
    print(f"network: {org.conn.n:,} neurons, {org.conn.n_edges:,} edges")
    print(f"rendering {args.duration_ms:g} ms ...")

    n_steps = int(round(args.duration_ms / org.timestep_ms))
    for step in range(n_steps):
        obs = org.body.observe()
        spiked = org.net.step(external_mv=org.aff.drive(obs))
        org.body.actuate(org.nm.step(spiked, org.timestep_ms))
        org.body.step()
        org.body.sim.render_as_needed()

    out = REPO / args.out
    out.parent.mkdir(parents=True, exist_ok=True)
    renderer.save_video(out)
    print(f"video: {out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
