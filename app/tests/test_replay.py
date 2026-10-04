"""Replay of interventions: a recording's embedded protocol reproduces it exactly,
and the catalogue's verdicts are the scorer's."""
from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

APP = Path(__file__).resolve().parents[1]
REPO = APP.parent
sys.path.insert(0, str(APP / "server"))
sys.path.insert(0, str(APP / "tools"))
import replay  # noqa: E402
import serve  # noqa: E402

RUNS = REPO / "runs" / "app"
SMOKE = RUNS / "smoke"
LIB = RUNS / "lib"
# earlier recordings of the same protocols (re-recorded after the criteria were
# added to `expect`, which does not touch the simulation)
PRE = RUNS / "lib-precriterion"


def complete(d: Path) -> bool:
    try:
        return json.loads((d / "manifest.json").read_text()).get("status") == "complete"
    except OSError:
        return False


@pytest.mark.skipif(not (complete(SMOKE / "all-effectors") and complete(SMOKE / "control")), reason="smoke runs not recorded")
def test_compare_sees_identity_and_difference():
    same = replay.compare(SMOKE / "all-effectors", SMOKE / "all-effectors")
    assert same and all(v["identical"] for v in same.values())
    diff = replay.compare(SMOKE / "all-effectors", SMOKE / "control")
    assert not diff["spike_row"]["identical"] and diff["static/row_bodyid"]["identical"]


@pytest.mark.parametrize("name", sorted(p.name for p in PRE.glob("*") if complete(p)) if PRE.exists() else [])
def test_rerecording_is_identical(name):
    if not complete(LIB / name):
        pytest.skip("not re-recorded")
    res = replay.compare(PRE / name, LIB / name)
    bad = {k: v for k, v in res.items() if not v["identical"]}
    assert not bad, bad


@pytest.mark.skipif(not (LIB / "scores.json").exists(), reason="library not scored")
def test_catalogue_verdicts_are_the_scorers():
    doc = json.loads((LIB / "scores.json").read_text())
    want = {}
    for s in doc["scores"]:
        c = s.get("criterion")
        if c and c.get("pass") is not None:
            want["lib/" + s["run"]] = ("PASS" if c["pass"] else "FAIL") + (
                ", no spike changed" if s["first_divergence_step"] is None else " within noise" if c.get("within_sham") else "")
    got = {r["id"]: r.get("verdict") for r in serve.catalog(RUNS)["recordings"] if r["id"].startswith("lib/")}
    assert want and all(got.get(k) == v for k, v in want.items()), (want, got)
    assert all(v is None for k, v in got.items() if k not in want)
