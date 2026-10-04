"""flyemu-protocol/1: one JSON document describing an experiment (configuration,
build-time genotype, run-time stimuli, what to record). The recorder executes it
and embeds it, resolved, in the recording.

M1 implements the effectors the model's public API supports today:

  genotype  TNT            Network.silence(rows) before the run (irreversible output block)
  events    current        external_mv added to the target rows (mV, steady depolarisation)
            CsChrimson     approximated as `current` (+mV); not a light-gated conductance
            GtACR1         approximated as `current` (-mV); not shunting

Every approximation is written into the resolved protocol as `approximation`, so
the app can show it next to the result.
"""
from __future__ import annotations

import re

import numpy as np
import pandas as pd

APPROX = {
    "current": None,
    "CsChrimson": "current injection standing in for a light-gated cation conductance "
                  "(no reversal potential, no channel kinetics)",
    "GtACR1": "hyperpolarising current standing in for an anion conductance "
              "(no shunting, no reversal potential)",
    "TNT": None,
}
DEFAULT_MV = {"current": 10.0, "CsChrimson": 10.0, "GtACR1": -10.0}


def resolve_target(target: dict, neurons: pd.DataFrame) -> np.ndarray:
    """Rows of `neurons` (the model's row order) matching every given key."""
    keep = np.ones(len(neurons), dtype=bool)
    if "bodyId" in target:
        ids = np.atleast_1d(np.asarray(target["bodyId"], dtype=np.int64))
        keep &= np.isin(neurons["bodyId"].to_numpy().astype(np.int64), ids)
    for key in ("type", "class", "superclass", "somaSide", "instance"):
        if key not in target:
            continue
        col = neurons[key].astype(str).to_numpy()
        want = target[key]
        if isinstance(want, str) and want.startswith("re:"):
            rx = re.compile(want[3:])
            keep &= np.fromiter((bool(rx.fullmatch(c)) for c in col), bool, len(col))
        else:
            keep &= np.isin(col, np.atleast_1d(want).astype(str))
    if not any(k in target for k in ("bodyId", "type", "class", "superclass", "somaSide", "instance")):
        raise ValueError(f"target {target} names no selector")
    return np.flatnonzero(keep)


def resolve(protocol: dict, neurons: pd.DataFrame, timestep_ms: float) -> dict:
    """Resolve targets to rows and times to steps; return the protocol with a
    `resolved` block added. Raises if a target matches nothing."""
    out = {"genotype": [], "events": []}
    for g in protocol.get("genotype", []):
        if g["effector"] != "TNT":
            raise ValueError(f"genotype effector {g['effector']} not available in M1")
        rows = resolve_target(g["target"], neurons)
        if rows.size == 0:
            raise ValueError(f"genotype target {g['target']} matches no neuron")
        out["genotype"].append({**g, "rows": rows.tolist(), "n": int(rows.size)})
    for e in protocol.get("events", []):
        eff = e.get("effector", "current")
        if eff not in DEFAULT_MV:
            raise ValueError(f"event effector {eff} not available in M1")
        rows = resolve_target(e["target"], neurons)
        if rows.size == 0:
            raise ValueError(f"event target {e['target']} matches no neuron")
        on = int(round(e["t_ms"] / timestep_ms))
        off = on + int(round(e["dur_ms"] / timestep_ms))
        out["events"].append({**e, "effector": eff, "mv": float(e.get("mv", DEFAULT_MV[eff])),
                              "rows": rows.tolist(), "n": int(rows.size),
                              "on_step": on, "off_step": off,
                              "approximation": APPROX[eff]})
    w = protocol.get("record", {}).get("watch")
    out["watch"] = sorted(set(resolve_target(w, neurons).tolist())) if w else []
    return {**protocol, "resolved": out}


class Stimulator:
    """Per-step external drive from resolved events."""

    def __init__(self, resolved: dict, n: int):
        self.events = [(e["on_step"], e["off_step"], np.asarray(e["rows"], np.int64), e["mv"])
                       for e in resolved["events"]]
        self.n = n

    def drive(self, step: int) -> np.ndarray | None:
        active = [e for e in self.events if e[0] <= step < e[1]]
        if not active:
            return None
        v = np.zeros(self.n, dtype=np.float32)
        for _, _, rows, mv in active:
            v[rows] += mv
        return v
