"""Dump the registry inventory of the working organism (profile m4, edges >= 5).

The construction data model (data/model/) must cover every key the model reads:
tests/test_model_data.py checks data/model/registry_inventory_m4.csv against
parameters.csv and mechanisms.yaml. Re-run after adding any registry key:

    uv run python scripts/model_keys.py
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from flyemu import profiles
from flyemu.organism import Organism

REPO = Path(__file__).resolve().parents[1]

if __name__ == "__main__":
    org = Organism(policy="minimal", profile=profiles.WORKING_PROFILE,
                   min_synapses=profiles.WORKING_MIN_SYNAPSES)
    inv = org.reg.inventory()
    cols = ["subsystem", "entity", "property", "units", "basis", "value", "instances"]
    out = REPO / "data" / "model" / "registry_inventory_m4.csv"
    inv[cols].to_csv(out, index=False)
    print(f"{len(inv)} keys -> {out}")
