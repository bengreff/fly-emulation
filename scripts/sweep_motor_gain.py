"""Tier-A sweep: how much torque per motor spike does this body need to move?

The measured quantity for a real fly is force per spike in one motor pool
(slow <0.1 uN, intermediate ~1 uN, fast ~10 uN; Azevedo 2020). What the model
needs is joint TORQUE per spike, which differs from it by an assumed moment arm
and by the body model's passive joint stiffness. This sweep measures the torque
per spike at which the body starts to move, so the two can be compared.

    uv run python scripts/sweep_motor_gain.py --duration-ms 200
"""
from __future__ import annotations

import argparse
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

import numpy as np
import pandas as pd

from flyemu.organism import Organism

REPO = Path(__file__).resolve().parents[1]
FORCE_KEY = "motor_unit:all|force_per_spike"
NOISE_KEY = "cell_type:all|background_noise"
EFFICACY_KEY = "connection_class:all|efficacy_per_synapse"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--duration-ms", type=float, default=200.0)
    ap.add_argument("--force", type=float, nargs="+",
                    default=[0.0, 0.01, 0.1, 0.3, 1.0, 3.0, 10.0, 30.0])
    ap.add_argument("--noise", type=float, default=2.5)
    ap.add_argument("--efficacy", type=float, default=0.1)
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--out", default="runs/sweep_motor_gain.csv")
    args = ap.parse_args()

    rows = []
    for f in args.force:
        t0 = time.time()
        org = Organism(policy="minimal", seed=args.seed, overrides={
            FORCE_KEY: f, NOISE_KEY: args.noise, EFFICACY_KEY: args.efficacy,
        })
        trace = org.run(args.duration_ms)
        hz = org.spike_counts / (org.duration_ms / 1000.0)
        mn = org.conn.neurons.superclass.to_numpy() == "vnc_motor"
        # Leg joint excursion: how much the legs actually swung.
        jcols = [i for i, a in enumerate(org.body.actuator_names)
                 if any(f"_{seg}" in a for seg in ["coxa", "trochanterfemur",
                                                    "tibia", "tarsus1"])]
        disp = float(np.hypot(
            trace.thorax_x.iloc[-1] - trace.thorax_x.iloc[0],
            trace.thorax_y.iloc[-1] - trace.thorax_y.iloc[0]))
        row = {
            "force_per_spike_uNmm": f,
            "motor_hz": float(hz[mn].mean()),
            "motor_max_hz": float(hz[mn].max()),
            "torque_absmean_uNmm": float(trace.torque_absmean.mean()),
            "torque_absmax_uNmm": float(trace.torque_absmean.max()),
            "displacement_mm": disp,
            "thorax_z_mm": float(trace.thorax_z.iloc[-1]),
            "thorax_z_std": float(trace.thorax_z.std()),
            "contact_mean": float(trace.contact_total.mean()),
            "wall_s": round(time.time() - t0, 1),
        }
        rows.append(row)
        print(f"f={f:<6} motor={row['motor_hz']:6.2f} Hz  "
              f"torque={row['torque_absmean_uNmm']:9.4f} uNmm  "
              f"disp={disp:6.3f} mm  z={row['thorax_z_mm']:.3f}  "
              f"zstd={row['thorax_z_std']:.4f}  {row['wall_s']}s", flush=True)

    df = pd.DataFrame(rows)
    out = REPO / args.out
    out.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(out, index=False)
    print(f"\n{out}")
    print(df.to_string(index=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
