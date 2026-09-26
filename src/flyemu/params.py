"""Per-cell-type parameter table: where individual blanks get filled.

`data/params/cell_types.csv` holds type-specific values, one row per
(type, parameter), each with its own basis label, source and justification:

    type,param,value,units,basis,source,justification

A type matches by exact `type` label, or by regex when `type` starts with
'^', or lists individual cells as `bodyId:<id>;<id>;...`. Every type without a row takes the shared default recorded in the
registry (itself labelled). So every slot in the model has a value, and each
value says where it came from. Filling a blank means adding a row.
"""
from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

from .registry import REQUIRED_FIELDS, Registry, Status

TABLE = Path(__file__).resolve().parents[2] / "data" / "params" / "cell_types.csv"
BASES = {"measured", "derived", "inferred", "guessed"}


def load(path: Path = TABLE) -> pd.DataFrame:
    if not path.exists():
        return pd.DataFrame(columns=["type", "param", "value", "units", "basis",
                                     "source", "justification"])
    t = pd.read_csv(path, comment="#")
    bad = t[~t.basis.isin(BASES)]
    if len(bad):
        raise ValueError(f"cell_types.csv rows with invalid basis: {bad.to_dict('records')}")
    missing = t[t.justification.isna() | (t.source.isna() & t.basis.isin(["measured", "derived"]))]
    if len(missing):
        raise ValueError(f"cell_types.csv rows missing source/justification: "
                         f"{missing[['type', 'param']].to_dict('records')}")
    return t


def per_neuron(reg: Registry, conn, param: str, default: float, *, units: str,
               table: pd.DataFrame | None = None) -> np.ndarray:
    """Per-neuron array: the shared default, overwritten by table rows."""
    table = load() if table is None else table
    arr = np.full(conn.n, float(default), dtype=np.float32)
    types = conn.neurons.type.fillna("").reset_index(drop=True)
    bids = conn.neurons.bodyId.reset_index(drop=True)
    rows = table[table.param == param]
    for r in rows.itertuples(index=False):
        if str(r.type).startswith("bodyId:"):
            # individual cells, e.g. motor units classed within a type
            want = {int(x) for x in str(r.type)[7:].split(";") if x}
            m = bids.isin(want).to_numpy()
        else:
            m = (types.str.match(r.type) if str(r.type).startswith("^")
                 else types.eq(r.type)).to_numpy()
        if not m.any():
            continue
        arr[m] = float(r.value)
        reg.provide(
            f"cell_type:{r.type}", param, float(r.value), units=units,
            model_use="type-specific value (data/params/cell_types.csv)",
            status=Status(r.basis), evidence=f"{r.source}: {r.justification}",
            subsystem="neuron_biophysics", instances=int(m.sum()),
            uncertainty=str(r.justification), method="per-type table",
        )
    return arr
