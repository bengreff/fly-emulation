"""Which mapped motor neurons still read the shared motor_unit:all|force_per_spike under a
profile (s12, Director 5 Oct: a profile name must mean one model). Static: builds the
organism, no stepping. A sentinel value marks every neuron that takes the shared value.

    PYTHONPATH=src uv run python scripts/probes/shared_fps_census.py --profile m9r
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd

from flyemu.organism import Organism

SENTINEL = 7.7777


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--profile", default="m9r")
    ap.add_argument("--out", default="runs/s12/fpsfold/census_m9r.json")
    a = ap.parse_args()
    org = Organism(policy="minimal", seed=12, profile=a.profile,
                   overrides={"motor_unit:all|force_per_spike": SENTINEL})
    nm = org.nm
    names = org.body.actuator_names if hasattr(org.body, "actuator_names") else None
    shared = np.isclose(nm.force_per_spike, SENTINEL)
    bid = org.conn.neurons.bodyId.to_numpy()[nm.mn_index]
    typ = org.conn.neurons.type.to_numpy()[nm.mn_index]
    act = nm.actuator_index
    df = pd.DataFrame({"bodyId": bid, "type": typ, "actuator": act, "shared": shared})
    if names is not None:
        df["actuator"] = [str(names[i]).split("/")[-1] for i in act]
    by_act = df[df.shared].groupby("actuator").bodyId.nunique().sort_values(ascending=False)
    out = {
        "profile": a.profile,
        "mapped_rows": int(len(df)),
        "mapped_neurons": int(df.bodyId.nunique()),
        "shared_rows": int(shared.sum()),
        "shared_neurons": int(df[df.shared].bodyId.nunique()),
        "shared_by_actuator": {k: int(v) for k, v in by_act.items()},
        "shared_types": sorted(set(map(str, df[df.shared].type))),
    }
    Path(a.out).parent.mkdir(parents=True, exist_ok=True)
    Path(a.out).write_text(json.dumps(out, indent=1))
    print(json.dumps({k: v for k, v in out.items() if k != "shared_types"}, indent=1))
    print("types:", out["shared_types"][:40])


if __name__ == "__main__":
    main()
