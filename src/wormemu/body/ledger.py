"""Body rows of the worm ledger: the only place a body number may come from.

`data/worm/ledger/metaworm_parameters.csv` (built by scripts/worm/build_metaworm_ledger.py for the ported
MetaWorm body; the own-rod ledger is archived in archive/worm/rod_own/) has the fly's parameters.csv columns (docs/CONSTRUCTION.md, "The data
model") plus the worm's `precision_needed` columns. `value_used` is the number a run uses: `value_fixed` when
the value is measured and fixed, otherwise the prior centre (a guess, labelled as such). `sample(seed)` draws the
free rows from their priors inside [bio_min, bio_max] for population runs.
"""
from __future__ import annotations

import csv
import math
from dataclasses import dataclass, field
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[3]
LEDGER = ROOT / "data" / "worm" / "ledger" / "metaworm_parameters.csv"
MECHANISMS = ROOT / "data" / "worm" / "ledger" / "metaworm_mechanisms.json"

COLUMNS = ["param_id", "mechanism_id", "grain", "applies_to", "unit", "bio_min", "bio_max", "bound_basis",
           "bound_source", "prior_dist", "prior_a", "prior_b", "prior_basis", "prior_source", "value_fixed",
           "value_used", "si_factor", "label", "precision_needed", "precision_basis", "notes"]


def _f(x):
    try:
        return float(x) if x not in ("", None) else math.nan
    except ValueError:  # model rows hold a description, not a number
        return math.nan


@dataclass
class Row:
    param_id: str
    raw: dict

    @property
    def value(self) -> float:
        return _f(self.raw["value_used"])

    @property
    def si(self) -> float:
        """value_used converted to SI with the row's si_factor (the ledger keeps the source's units)."""
        return self.value * _f(self.raw.get("si_factor") or 1)

    @property
    def bounds(self):
        return _f(self.raw["bio_min"]), _f(self.raw["bio_max"])


@dataclass
class BodyLedger:
    rows: dict = field(default_factory=dict)

    @classmethod
    def load(cls, path: Path = LEDGER) -> "BodyLedger":
        with open(path, newline="") as fh:
            rows = {r["param_id"]: Row(r["param_id"], r) for r in csv.DictReader(fh)}
        return cls(rows)

    def si(self, pid: str) -> float:
        return self.rows[pid].si

    def override(self, **values_si) -> "BodyLedger":
        """A copy with some rows replaced by SI values (sensitivity runs, toggles). Bounds are not checked
        here; `check_bounds` reports any value outside [bio_min, bio_max]."""
        new = {k: Row(k, dict(v.raw)) for k, v in self.rows.items()}
        for k, v in values_si.items():
            r = new[k]
            r.raw["value_used"] = repr(v / _f(r.raw.get("si_factor") or 1))
        return BodyLedger(new)

    def check_bounds(self):
        bad = []
        for k, r in self.rows.items():
            lo, hi = r.bounds
            v = r.value
            if not math.isnan(v) and ((not math.isnan(lo) and v < lo) or (not math.isnan(hi) and v > hi)):
                bad.append((k, v, lo, hi))
        return bad

    def sample(self, seed: int) -> "BodyLedger":
        """Draw every non-fixed row from its prior, truncated to [bio_min, bio_max]."""
        rng = np.random.default_rng(seed)
        new = {k: Row(k, dict(v.raw)) for k, v in self.rows.items()}
        for k, r in new.items():
            if r.raw["value_fixed"] not in ("", None) or r.raw["prior_dist"] in ("", "fixed"):
                continue
            lo, hi = r.bounds
            a, b = _f(r.raw["prior_a"]), _f(r.raw["prior_b"])
            for _ in range(1000):
                if r.raw["prior_dist"] == "lognormal":
                    v = math.exp(rng.normal(math.log(a), b))
                elif r.raw["prior_dist"] == "uniform":
                    v = rng.uniform(a, b)
                else:
                    v = rng.normal(a, b)
                if (math.isnan(lo) or v >= lo) and (math.isnan(hi) or v <= hi):
                    break
            r.raw["value_used"] = repr(v)
        return BodyLedger(new)
