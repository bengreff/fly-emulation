"""List the cells whose input gain the adopted per-cell rules set (ledger fill; session 11).

m7 applies the within-type size principle to motor neurons only
(cell_type:motor|within_type_size_exponent 1.49; src/flyemu/percell.py). This writes
one row per motor neuron the rule acts on (typed, >= 2 complete cells in its type,
itself complete) with its factor -> data/derived/percell_motor_factors.csv, which
data/ontology/fly_information.yaml cites as a rule fill for per-cell excitability.

    uv run python scripts/percell_fill_table.py
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "src"))
from flyemu import profiles  # noqa: E402
from flyemu.percell import incomplete, within_type_ratio  # noqa: E402

n = pd.read_parquet(REPO / "data" / "cache" / "male_cns_neurons.parquet")
n = n[(n.status == "Traced") | n.type.notna()].reset_index(drop=True)
alpha = profiles.PROFILES["m7"]["values"]["cell_type:motor|within_type_size_exponent"][0]
types = n.type
bad = incomplete(n["post"].to_numpy(np.float64), types)
r = within_type_ratio(n["size"].to_numpy(np.float64), types, exclude=bad)
motor = n.superclass.isin(["vnc_motor", "cb_motor"]).to_numpy()
f = r ** alpha
acted = motor & ~bad & (r != 1.0)
out = n.loc[acted, ["bodyId", "type", "superclass"]].assign(factor=f[acted], alpha=alpha)
out.to_csv(REPO / "data" / "derived" / "percell_motor_factors.csv", index=False)
print(f"{len(n):,} cells; motor {motor.sum():,}; rule acts on {acted.sum():,} "
      f"(factor 5-95%: {np.percentile(f[acted], 5):.2f}-{np.percentile(f[acted], 95):.2f})")
