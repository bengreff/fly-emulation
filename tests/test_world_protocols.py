"""The scoreboard's world data (data/world, packed as the zip's world/) and the flyemu.score interpreter."""
import json
import sys
from pathlib import Path

import numpy as np
import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from flyemu import check, flyzip, score  # noqa: E402

W = ROOT / score.WORLD
READOUT_QUANTITIES = {"mean_rate_hz": {"rate_hz_mean"},
                      "gf_latency": {"gf_spike_fraction"}}   # plus <type>.<field> for each mn type


def test_scoreboard_lists_the_fixed_items_and_built_protocols():
    sb = check._scoreboard(ROOT)
    assert tuple(sb) == check.SCOREBOARD
    for item, v in sb.items():
        assert v["protocol"] or v["todo"], item


@pytest.mark.parametrize("name", sorted(p.stem for p in (W / "protocols").glob("*.json")))
def test_protocol_is_complete(name):
    proto, stim, shas = score.load(ROOT, name)
    assert proto["name"] == name and stim["name"] == proto["stimulus"]
    for k in ("item", "harness", "settings", "seeds", "duration_ms", "readout", "pass", "bar_source",
              "reference_script", "evidence_status"):
        assert proto[k] not in (None, "", []), k
    assert proto["item"] in check.SCOREBOARD
    assert proto["harness"]["build"] in ("assay", "organism")
    r = proto["readout"]
    names = set(READOUT_QUANTITIES[r["kind"]])
    if r["kind"] == "gf_latency":
        names |= {f"{t}.{f}" for t in r["mn_types"] for f in ("follow_fraction", "muscle_ms_median",
                                                              "central_ms_median", "control_fraction")}
    for c in proto["pass"]:
        for q in (c["quantity"] if isinstance(c["quantity"], list) else [c["quantity"]]):
            assert q in names, q


def test_schedule_poisson_and_train():
    types = np.array(["A", "B", "A", "C", "G"])
    stim = {"name": "t", "events": [
        {"kind": "poisson_kick", "types": ["A"], "rate_hz": 1e4, "t_on_ms": 0.0, "t_off_ms": 1.0, "kick_mv": "profile"},
        {"kind": "kick", "types": ["G"], "kick_mv": 100.0, "start_ms": 0.5, "period_ms": 1.0, "count": 2}]}
    s = score.Schedule(stim, types, 0.1, 30, kick_mv_profile=7.0)
    rng = np.random.default_rng(0)
    k0 = s.kick(0, rng)                       # rate x dt = 1: every A cell, scalar profile mV
    assert k0[0].tolist() == [0, 2] and k0[1] == 7.0
    k5 = s.kick(5, rng)                       # A still on and the G train: per-cell mV
    assert k5[0].tolist() == [0, 2, 4] and k5[1].tolist() == [7.0, 7.0, 100.0]
    assert s.kick(10, rng) is None            # A off at 1 ms, no train step
    k15 = s.kick(15, rng)
    assert k15[0].tolist() == [4] and k15[1] == 100.0
    with pytest.raises(flyzip.Refused):
        score.Schedule({"name": "t", "events": [stim["events"][0], stim["events"][0]]}, types, 0.1, 30, 7.0)


def test_judge():
    q = {"a": 6.0, "x.m": 1.0, "y.m": None}
    res = score.judge([{"quantity": "a", "op": ">", "value": 5.0},
                       {"quantity": ["x.m", "y.m"], "op": "present_all_in", "value": [0.9, 1.1]}], q)
    assert [r["ok"] for r in res] == [True, True]
    assert not score.judge([{"quantity": "y.m", "op": "in", "value": [0, 1]}], q)[0]["ok"]
    with pytest.raises(flyzip.Refused):
        score.judge([{"quantity": "missing", "op": ">", "value": 0}], q)


def test_world_files_are_json():
    for p in W.rglob("*.json"):
        json.loads(p.read_text())
