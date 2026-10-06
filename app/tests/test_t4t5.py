"""Checks for the T4/T5 direction test (app/tools/t4t5_ds.py): the protocols it records
and the verdicts it scores.

    .venv/bin/python -m pytest app/tests/test_t4t5.py -q
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

APP = Path(__file__).resolve().parents[1]
REPO = APP.parent
sys.path.insert(0, str(APP / "tools"))
import t4t5_ds as h  # noqa: E402
from eye_sweep import DIRS, OFF, ON  # noqa: E402


def test_protocols_target_the_declared_cells():
    ps = h.protocols("m9r", 0, {"x|y": 1.0}, None, ["medulla", "photoreceptor"])
    assert len(ps) == 17 and ps["control"]["events"] == []
    assert all(p["config"]["profile"] == "m9r" and p["config"]["seed"] == 0 and p["config"]["overrides"] == {"x|y": 1.0}
               and "extra_params" not in p["config"] and "variant" not in p for p in ps.values())
    ty = pd.read_parquet(REPO / "data" / "cache" / "male_cns_neurons.parquet",
                         columns=["bodyId", "type"]).set_index("bodyId")["type"]
    want = {"med-on": set(ON), "med-off": set(OFF)}
    for k, p in ps.items():
        if k == "control":
            continue
        ids = [i for e in p["events"] for i in e["target"]["bodyId"]]
        types = set(ty.reindex(ids).astype(str))
        if k[:-2] in want:
            assert types == want[k[:-2]], k
        else:
            assert all(t.startswith("R") for t in types), k
            assert {e["mv"] for e in p["events"]} == {3.0 if "-on" in k else -3.0}
        assert all(e["effector"] == "current" and e["t_ms"] >= 300 for e in p["events"])
    v = h.protocols("m9r", 0, {}, "app/protocols/eye/variant_graded_medulla.csv", ["medulla"])
    assert len(v) == 9 and all(p["config"]["extra_params"] and p["variant"] for p in v.values())


@pytest.mark.skipif(not (APP / "data" / "body" / "flybody" / "columns.json").exists(), reason="columns not built")
def test_fixed_stimuli_match_the_builder_and_the_graded_run():
    """The committed stimuli are what the builder makes from the current mosaic, and the medulla
    bars are the events of the graded-medulla run (eye_sweep.py), so that run is the reference."""
    built = h.build_stimuli()
    assert sorted(built) == sorted(f.stem for f in h.STIM.glob("*.json"))
    for k, p in built.items():
        assert json.loads((h.STIM / f"{k}.json").read_text()) == json.loads(json.dumps(p)), k
    for d in DIRS:
        for pol in ("on", "off"):
            ref = json.loads((APP / "protocols" / "eye" / f"graded-A-{pol}{d}-m9r-s0.json").read_text())
            assert built[f"med-{pol}{d}"]["events"] == ref["events"]


def _peaks(rule, n=18, seed=0):
    rng = np.random.default_rng(seed)
    out = {}
    for T in h.SUBTYPES:
        out[T] = {d: (rule(T, d) + rng.normal(0, 0.05, n)).tolist() for d in DIRS}
    return out


def test_score_verdicts():
    as_flies = h.score(_peaks(lambda T, d: 2.0 if d == h.PREF[T[-1]] else 1.0))
    assert as_flies["pass"] and as_flies["n_selective_as_in_flies"] == 8
    # a bias shared by every subtype (all prefer back-to-front and downward) cannot pass:
    # one of each pair a/b, c/d comes out opposite to flies
    shared = h.score(_peaks(lambda T, d: 2.0 if d in ("+x", "+y") else 1.0))
    v = {T: r["verdict"] for T, r in shared["subtypes"].items()}
    assert not shared["pass"] and v["T4a"] == "selective, opposite to flies" and v["T4b"] == "selective as in flies"
    flat = h.score(_peaks(lambda T, d: 1.5))
    assert {r["verdict"] for r in flat["subtypes"].values()} == {"not selective"}
    silent = h.score(_peaks(lambda T, d: 0.1))
    assert {r["verdict"] for r in silent["subtypes"].values()} == {"no response"}
