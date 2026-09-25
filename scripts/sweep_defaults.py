"""Tier-A sensitivity sweep over the guesses that carry the most model elements.

Two scalars in the C1 default set are propagated to almost everything:

    connection_class:all|efficacy_per_synapse   25,862,574 edges
    cell_type:all|background_noise                 176,422 neurons

Neither has a measurement behind it. This sweep asks what the closed loop does
across them: whether the animal is silent, plausibly active, or saturated, and
how sharp the boundary is. The result is written back as the `uncertainty`
column for those two requirement rows.

    uv run python scripts/sweep_defaults.py --duration-ms 50
"""
from __future__ import annotations

import argparse
import itertools
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

import numpy as np
import pandas as pd

from flyemu.organism import Organism

REPO = Path(__file__).resolve().parents[1]
EFFICACY_KEY = "connection_class:all|efficacy_per_synapse"
NOISE_KEY = "cell_type:all|background_noise"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--duration-ms", type=float, default=50.0)
    ap.add_argument("--efficacy", type=float, nargs="+",
                    default=[0.025, 0.05, 0.1, 0.2, 0.4, 0.8])
    ap.add_argument("--noise", type=float, nargs="+",
                    default=[1.0, 1.5, 2.0, 2.5])
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--spike-cap", type=int, default=120_000)
    ap.add_argument("--out", default="runs/sweep_defaults.csv")
    args = ap.parse_args()

    rows = []
    for eff, noise in itertools.product(args.efficacy, args.noise):
        t0 = time.time()
        org = Organism(
            policy="minimal", seed=args.seed,
            overrides={EFFICACY_KEY: eff, NOISE_KEY: noise},
        )
        status, trace = "ok", None
        try:
            trace = org.run(args.duration_ms, spike_cap_per_step=args.spike_cap)
        except RuntimeError as exc:
            status = "runaway"
            print(f"  eff={eff} noise={noise}: {exc}")

        if trace is not None:
            hz = org.spike_counts / (org.duration_ms / 1000.0)
            n = org.conn.neurons
            mn = n.superclass.to_numpy() == "vnc_motor"
            sens = n.superclass.to_numpy() == "vnc_sensory"
            disp = float(np.hypot(
                trace.thorax_x.iloc[-1] - trace.thorax_x.iloc[0],
                trace.thorax_y.iloc[-1] - trace.thorax_y.iloc[0]))
            row = {
                "efficacy_mv": eff, "noise_mv": noise, "status": status,
                "mean_hz": float(hz.mean()),
                "frac_active": float((hz > 0).mean()),
                "motor_hz": float(hz[mn].mean()),
                "motor_max_hz": float(hz[mn].max()),
                "sensory_hz": float(hz[sens].mean()),
                "torque_absmean": float(trace.torque_absmean.mean()),
                "displacement_mm": disp,
                "final_z_mm": float(trace.thorax_z.iloc[-1]),
                "wall_s": round(time.time() - t0, 1),
            }
        else:
            row = {"efficacy_mv": eff, "noise_mv": noise, "status": status,
                   "wall_s": round(time.time() - t0, 1)}
        rows.append(row)
        print(f"eff={eff:<6} noise={noise:<5} {status:<8} "
              f"mean={row.get('mean_hz', float('nan')):7.2f} Hz  "
              f"motor={row.get('motor_hz', float('nan')):7.2f} Hz  "
              f"disp={row.get('displacement_mm', float('nan')):6.3f} mm  "
              f"{row['wall_s']}s", flush=True)

    df = pd.DataFrame(rows)
    out = REPO / args.out
    out.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(out, index=False)
    print(f"\n{out}")
    print(df.to_string(index=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
