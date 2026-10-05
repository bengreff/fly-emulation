"""Library scoring helpers that need no recordings: the multi-trial summary, the sham trajectory hash."""
from __future__ import annotations

import sys
from pathlib import Path
from types import SimpleNamespace

import numpy as np
import pytest

APP = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(APP / "tools"))
from score_library import train_hash, trials  # noqa: E402

CRIT = {"metric": "readout_delta_hz", "op": ">=", "value": 5}


def row(run, seed, hz, delta=None, error=False):
    r = {"run": run, "seed": seed, "readout_hz": hz, "readout_excluded_incomplete": ["MN9_R"]}
    if error:
        r["error"] = "no matched control"
    else:
        r.update(readout_delta_hz=delta, criterion=CRIT)
    return r


def test_trials_group_by_protocol_and_judge_the_mean():
    rows = [row("sugar-s1", 1, 6.0, 6.0), row("sugar-s0", 0, 1.0, 1.0), row("sugar-s2", 2, 5.0, 5.0),
            row("sham-s0", 0, 0.0, 0.0), row("lone-s3", 3, 2.0, 2.0), row("sugar", 12, 9.0, 9.0)]
    g = {x["protocol"]: x for x in trials(rows)}
    assert set(g) == {"sugar"}                          # one trial is not a group
    s = g["sugar"]
    assert s["seeds"] == [0, 1, 2]                       # sorted by seed; the unsuffixed run is not a trial
    assert s["readout_hz_mean"] == pytest.approx(4.0)
    assert s["readout_hz_sd"] == pytest.approx(2.6457513)
    assert s["criterion_on_mean"]["pass"] is False      # mean 4 < 5, though one trial passes
    assert "after the first library was viewed" in s["criterion_on_mean"]["rule"]
    assert s["excluded_incomplete"] == ["MN9_R"]


def test_trials_without_controls_report_rates_only():
    g = trials([row("assay-s0", 0, 7.0, error=True), row("assay-s1", 1, 6.0, error=True)])
    assert len(g) == 1 and g[0]["readout_hz_mean"] == pytest.approx(6.5)
    assert "readout_delta_hz" not in g[0] and "criterion_on_mean" not in g[0]


def test_train_hash_ignores_the_shams_own_cells():
    def run(steps, rows):
        return SimpleNamespace(steps=np.array(steps), rows=np.array(rows), m={"n_rows": 10})
    a = run([5, 7, 9, 20], [1, 2, 3, 4])         # sham kicks cell 1; the rest fire 2, 3; step 20 is outside
    b = run([5, 7, 9], [8, 2, 3])                # sham kicks cell 8; the rest the same
    c = run([5, 7, 10], [8, 2, 3])               # cell 3 fires one step later
    skip = np.array([1, 8])
    assert train_hash(a, 0, 15, skip) == train_hash(b, 0, 15, skip)
    assert train_hash(b, 0, 15, skip) != train_hash(c, 0, 15, skip)
    none = np.array([], np.int64)
    assert train_hash(a, 0, 15, none) != train_hash(b, 0, 15, none)
