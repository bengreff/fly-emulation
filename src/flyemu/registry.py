"""The parameter registry.

Every biological quantity the model reads passes through `Registry.require`.
Nothing is read from a bare literal buried in a function. The consequence is
that the model cannot use a value without declaring what the value is, what
equation needs it, what units it is in, and where it came from - and the list of
requirements is a byproduct of running the model rather than a document
maintained beside it.

Three fill policies, run and reported together (docs/PLAN.md step 6):

    STRICT        unresolved quantities raise. The model does not start, and the
                  list it refuses on is the result.
    MINIMAL       unresolved quantities take one declared default per subsystem.
                  Runs; expected to produce nothing recognisable.
    CONVENTIONAL  unresolved quantities take what published precedents assume.

A default is never silently a measurement. `status` records which it is, and
`Registry.inventory()` renders the whole set with instance counts.
"""
from __future__ import annotations

import json
from collections import OrderedDict
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any

import pandas as pd


class Status(str, Enum):
    """Where a value came from. Ordered from strongest to weakest evidence."""

    MEASURED = "measured"          # directly measured in this preparation
    DERIVED = "derived"            # computed from a measurement, with assumptions
    FITTED = "fitted"              # optimised against observations
    ASSUMED = "assumed"            # a declared guess or a precedent's convention
    UNRESOLVED = "unresolved"      # required, no value available
    CONFLICTING = "conflicting"    # sources disagree
    INAPPLICABLE = "inapplicable"  # required by M but meaningless for this entity


class Policy(str, Enum):
    STRICT = "strict"
    MINIMAL = "minimal"
    CONVENTIONAL = "conventional"


class Unresolved(Exception):
    """Raised under STRICT when the model reaches for a quantity it lacks."""

    def __init__(self, req: "Requirement") -> None:
        super().__init__(
            f"unresolved requirement: {req.entity}.{req.property} "
            f"[{req.units}] needed by {req.model_use}"
        )
        self.requirement = req


@dataclass
class Requirement:
    """One row of the inventory. Schema from docs/PLAN.md."""

    entity: str                 # 'cell_type:Ti flexor MN', 'muscle:Ti flexor'
    property: str               # 'tau_m', 'sign', 'g_syn'
    units: str                  # 'ms', 'dimensionless', 'mN*mm'
    model_use: str              # the equation or interface that needs it
    status: Status
    value: Any = None
    evidence: str | None = None
    conditions: dict[str, Any] = field(default_factory=dict)
    uncertainty: str | None = None
    transfer: str | None = None
    instances: int = 1          # how many model elements this value fills
    shared_with: tuple[str, ...] = ()   # rows sharing one inference
    subsystem: str = "unassigned"

    @property
    def key(self) -> str:
        return f"{self.entity}|{self.property}"

    def to_row(self) -> dict[str, Any]:
        return {
            "subsystem": self.subsystem,
            "entity": self.entity,
            "property": self.property,
            "units": self.units,
            "model_use": self.model_use,
            "status": self.status.value,
            "value": _scalar_repr(self.value),
            "instances": self.instances,
            "evidence": self.evidence,
            "uncertainty": self.uncertainty,
            "transfer": self.transfer,
            "conditions": json.dumps(self.conditions) if self.conditions else None,
            "shared_with": ";".join(self.shared_with) or None,
        }


def _scalar_repr(v: Any) -> Any:
    """Keep the inventory readable: summarise arrays rather than inlining them."""
    if v is None or isinstance(v, (int, float, str, bool)):
        return v
    try:
        import numpy as np

        if isinstance(v, np.ndarray):
            if v.size == 0:
                return "[]"
            return f"array(shape={v.shape}, mean={float(v.mean()):.4g})"
        if isinstance(v, np.generic):
            return v.item()
    except Exception:
        pass
    if isinstance(v, (list, tuple, dict)):
        return f"{type(v).__name__}(n={len(v)})"
    return repr(v)[:80]


class Registry:
    """Collects requirements as the model asks for them."""

    def __init__(
        self, policy: Policy | str = Policy.MINIMAL, *, enumerate_all: bool = True
    ) -> None:
        self.policy = Policy(policy)
        # Under STRICT, keep going so the caller gets the complete list of
        # unresolved requirements rather than only the first one. Construction
        # proceeds on placeholders; integration is refused by the caller.
        self.enumerate_all = enumerate_all
        # Explicit command-line overrides of assumed scalars, keyed
        # "entity|property". Recorded as assumed with the override noted, so a
        # swept value can never read back as a measurement.
        self.overrides: dict[str, float] = {}
        self._reqs: OrderedDict[str, Requirement] = OrderedDict()
        self._refusals: list[Requirement] = []

    # --- declaring values ----------------------------------------------------

    def provide(
        self,
        entity: str,
        property: str,
        value: Any,
        *,
        units: str,
        model_use: str,
        status: Status,
        evidence: str | None = None,
        subsystem: str = "unassigned",
        instances: int = 1,
        conditions: dict[str, Any] | None = None,
        uncertainty: str | None = None,
        transfer: str | None = None,
        shared_with: tuple[str, ...] = (),
    ) -> Any:
        """Record a quantity that has a value, and return it."""
        if status in (Status.UNRESOLVED, Status.INAPPLICABLE) and value is not None:
            raise ValueError(f"{status.value} requirement cannot carry a value")
        req = Requirement(
            entity=entity, property=property, units=units, model_use=model_use,
            status=status, value=value, evidence=evidence, subsystem=subsystem,
            instances=instances, conditions=conditions or {},
            uncertainty=uncertainty, transfer=transfer, shared_with=shared_with,
        )
        self._reqs[req.key] = req
        return value

    def require(
        self,
        entity: str,
        property: str,
        *,
        units: str,
        model_use: str,
        subsystem: str = "unassigned",
        instances: int = 1,
        minimal: Any = None,
        conventional: Any = None,
        minimal_note: str | None = None,
        conventional_note: str | None = None,
        uncertainty: str | None = None,
        shared_with: tuple[str, ...] = (),
    ) -> Any:
        """Ask for a quantity with no measured value available.

        Under STRICT this raises. Under MINIMAL or CONVENTIONAL it returns the
        corresponding declared default, recorded as `assumed` - never as a
        measurement.
        """
        key = f"{entity}|{property}"
        if key in self.overrides:
            req = Requirement(
                entity=entity, property=property, units=units,
                model_use=model_use, status=Status.ASSUMED,
                value=self.overrides[key],
                evidence="explicit override supplied for this run",
                subsystem=subsystem, instances=instances,
                uncertainty=uncertainty, shared_with=shared_with,
            )
            self._reqs[req.key] = req
            return self.overrides[key]

        if self.policy is Policy.STRICT:
            req = Requirement(
                entity=entity, property=property, units=units,
                model_use=model_use, status=Status.UNRESOLVED,
                subsystem=subsystem, instances=instances,
                uncertainty=uncertainty, shared_with=shared_with,
            )
            self._reqs[req.key] = req
            self._refusals.append(req)
            if not self.enumerate_all:
                raise Unresolved(req)
            # A placeholder so construction can finish and enumerate the rest.
            # It is never a value the model is allowed to integrate with.
            placeholder = minimal if minimal is not None else conventional
            if placeholder is None:
                raise Unresolved(req)
            return placeholder

        if self.policy is Policy.CONVENTIONAL and conventional is not None:
            value, note = conventional, conventional_note or "published precedent"
        elif minimal is not None:
            value, note = minimal, minimal_note or "declared subsystem default"
        elif conventional is not None:
            value, note = conventional, conventional_note or "published precedent"
        else:
            req = Requirement(
                entity=entity, property=property, units=units,
                model_use=model_use, status=Status.UNRESOLVED,
                subsystem=subsystem, instances=instances,
                uncertainty=uncertainty, shared_with=shared_with,
            )
            self._reqs[req.key] = req
            self._refusals.append(req)
            raise Unresolved(req)

        req = Requirement(
            entity=entity, property=property, units=units, model_use=model_use,
            status=Status.ASSUMED, value=value, evidence=note,
            subsystem=subsystem, instances=instances, uncertainty=uncertainty,
            shared_with=shared_with,
        )
        self._reqs[req.key] = req
        return value

    # --- reading the inventory back ------------------------------------------

    def inventory(self) -> pd.DataFrame:
        return pd.DataFrame([r.to_row() for r in self._reqs.values()])

    @property
    def refusals(self) -> list[Requirement]:
        return list(self._refusals)

    def counts(self) -> pd.DataFrame:
        """Rows and filled model elements by subsystem and status."""
        inv = self.inventory()
        if inv.empty:
            return inv
        return (
            inv.groupby(["subsystem", "status"])
            .agg(rows=("property", "size"), instances=("instances", "sum"))
            .reset_index()
            .sort_values(["subsystem", "rows"], ascending=[True, False])
        )

    def summary(self) -> dict[str, Any]:
        inv = self.inventory()
        if inv.empty:
            return {"rows": 0}
        by_status = inv.groupby("status").agg(
            rows=("property", "size"), instances=("instances", "sum")
        )
        return {
            "policy": self.policy.value,
            "rows": int(len(inv)),
            "model_elements": int(inv.instances.sum()),
            "by_status": by_status.to_dict("index"),
            "refusals": len(self._refusals),
        }

    def write(self, path: str | Path) -> Path:
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        self.inventory().to_csv(path, index=False)
        return path
