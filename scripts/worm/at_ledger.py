"""Run a worm unit-check script with the ledger's values in place of the code templates (wfinal, 7 Nov 2026).

The unit checks (receptor_unit_check.py, stp_unit_check.py, neuromod_unit_check.py, chnoise_unit_check.py, ...)
read each Spec's code template, while the brain runs the ledger value (mech.params_for). After the catalog merge
(7b49648) 42 Specs differ, so the checks as written score values the model no longer runs. This swaps each Spec's
template for its ledger value (data/worm/model/parameters.csv, value_template) before the script runs; the script
itself is unchanged.

Usage: PYTHONPATH=src .venv/bin/python scripts/worm/at_ledger.py scripts/worm/receptor_unit_check.py [args ...]
"""
from __future__ import annotations

import csv
import dataclasses
import importlib
import runpy
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from wormemu import mech  # noqa: E402


def patch(registry=None) -> list[str]:
    """Replace each registry module's Specs, in place, by ones whose template is the ledger value. Returns the
    changes as 'id old -> new'."""
    led = {r["param_id"]: r for r in csv.DictReader(open(ROOT / "data/worm/model/parameters.csv"))}
    moved = []
    for name in registry or mech.REGISTRY:
        m = importlib.import_module(f"wormemu.mech.{name}")
        specs = getattr(m, "SPECS", None)
        for i, s in enumerate(specs or []):
            r = led.get(s.id)
            try:
                v = float(r["value_template"]) if r else None
            except ValueError:
                v = None
            if v is not None and abs(v - float(s.template)) > 1e-12 * max(1.0, abs(v)):
                specs[i] = dataclasses.replace(s, template=v)
                moved.append(f"{s.id} {s.template:g} -> {v:g}")
    return moved


if __name__ == "__main__":
    moved = patch()
    print(f"at_ledger: {len(moved)} Spec templates set to their ledger values", flush=True)
    script = sys.argv[1]
    sys.argv = sys.argv[1:]
    runpy.run_path(script, run_name="__main__")
