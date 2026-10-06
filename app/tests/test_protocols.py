"""Checks for stimulus protocols, the effectors, the held-out guard and the
recorded intervention library.

    .venv/bin/python -m pytest app/tests/test_protocols.py -q

Library checks skip until app/tools/run_library.py has recorded the runs.
"""
from __future__ import annotations

import gzip
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

APP = Path(__file__).resolve().parents[1]
REPO = APP.parent
sys.path.insert(0, str(APP / "server"))
import heldout  # noqa: E402
import protocol as proto  # noqa: E402
from recfmt import RecReader, unpack  # noqa: E402

ATLAS = APP / "data" / "atlas" / "male-cns-v1.0"
LIB = REPO / "runs" / "app" / "lib"
SMOKE = REPO / "runs" / "app" / "smoke"
ASSAY = REPO / "runs" / "app" / "assay"     # app/protocols/assay recorded at seeds 0-2

NEURONS = pd.DataFrame({
    "bodyId": [11, 12, 13, 14, 15, 16],
    "type": ["MDN", "MDN", "DNa02", "DNa02", "LB3b", "DNp01"],
    "class": ["descending"] * 4 + ["sensory", "descending"],
    "superclass": ["descending_neuron"] * 4 + ["sensory_neuron", "descending_neuron"],
    "somaSide": ["L", "R", "L", "R", "L", "R"],
    "instance": ["MDN_L", "MDN_R", "DNa02_L", "DNa02_R", "LB3b_L", "DNp01_R"],
})


def doc(**kw):
    d = {"config": {"seed": 12}, "duration_ms": 100, "genotype": [], "events": []}
    d.update(kw)
    return d


# resolving

def test_resolve_targets_and_steps():
    r = proto.resolve(doc(events=[
        {"effector": "CsChrimson", "target": {"type": "MDN"}, "t_ms": 50, "dur_ms": 20},
        {"effector": "current", "target": {"type": "DNa02", "somaSide": "L"}, "t_ms": 10, "dur_ms": 5, "mv": 15},
        {"effector": "kick", "target": {"type": "re:LB3.*"}, "t_ms": 0, "dur_ms": 100, "rate_hz": 50},
    ], genotype=[{"effector": "TNT", "target": {"bodyId": [16]}}]), NEURONS, 0.1)["resolved"]
    e0, e1, e2 = r["events"]
    assert e0["rows"] == [0, 1] and (e0["on_step"], e0["off_step"]) == (500, 700) and e0["mv"] == 10.0
    assert "current injection" in e0["approximation"]
    assert e1["rows"] == [2] and e1["mv"] == 15 and e1["approximation"] is None
    assert e2["rows"] == [4] and e2["rate_hz"] == 50
    assert r["genotype"][0]["rows"] == [5] and r["genotype"][0]["n"] == 1


@pytest.mark.parametrize("bad", [
    doc(duration_ms=20_000),
    doc(events=[{"effector": "current", "target": {"type": "nope"}, "t_ms": 0, "dur_ms": 1}]),
    doc(events=[{"effector": "current", "target": {"type": "MDN"}, "t_ms": 0, "dur_ms": 1, "mv": 60}]),
    doc(events=[{"effector": "kick", "target": {"type": "MDN"}, "t_ms": 0, "dur_ms": 1, "rate_hz": 5000}]),
    doc(events=[{"effector": "TNT", "target": {"type": "MDN"}, "t_ms": 0, "dur_ms": 1}]),
    doc(events=[{"effector": "world", "set": {"temperature_c": 30}, "t_ms": 0, "dur_ms": 1}]),
    doc(events=[{"effector": "current", "target": {}, "t_ms": 0, "dur_ms": 1}]),
    doc(genotype=[{"effector": "CsChrimson", "target": {"type": "MDN"}}]),
])
def test_resolve_refuses(bad):
    with pytest.raises(ValueError):
        proto.resolve(bad, NEURONS, 0.1)


def test_is_control():
    assert proto.is_control(doc()) and proto.is_control(None)
    assert not proto.is_control(doc(genotype=[{"effector": "TNT", "target": {"type": "MDN"}}]))


# effectors

def test_drive_pulses_and_tonic():
    r = proto.resolve(doc(events=[
        {"effector": "CsChrimson", "target": {"type": "MDN"}, "t_ms": 10, "dur_ms": 50, "pulse_hz": 50, "pulse_ms": 5}],
        genotype=[{"effector": "Kir2.1", "target": {"type": "LB3b"}, "mv": -8}]), NEURONS, 0.1)["resolved"]
    assert r["events"][0]["pulse_steps"] == (200, 50)
    s = proto.Stimulator(r, len(NEURONS), 12, None)
    before = s.drive(0)
    assert before[4] == -8 and before[0] == 0                  # Kir2.1 from step 0, stimulus off
    assert s.drive(100)[0] == 10 and s.drive(149)[0] == 10     # first pulse: steps 100 to 149
    assert s.drive(150)[0] == 0 and s.drive(300)[0] == 10      # gap, then the second pulse
    assert s.drive(600)[0] == 0 and s.drive(600)[4] == -8      # after the event


def test_drive_none_without_effectors():
    r = proto.resolve(doc(events=[{"effector": "current", "target": {"type": "MDN"}, "t_ms": 5, "dur_ms": 1}]),
                      NEURONS, 0.1)["resolved"]
    s = proto.Stimulator(r, len(NEURONS), 12, None)
    assert s.drive(0) is None and s.drive(50)[0] == 10 and s.drive(60) is None


def test_kicks_seeded_windowed_and_at_rate():
    r = proto.resolve(doc(duration_ms=1000, events=[
        {"effector": "kick", "target": {"type": "MDN"}, "t_ms": 100, "dur_ms": 800, "rate_hz": 100}]), NEURONS, 0.1)["resolved"]
    runs = []
    for _ in range(2):
        s = proto.Stimulator(r, len(NEURONS), 12, 68.75)
        got = [(k, s.kick(k, 0.1)) for k in range(10_000)]
        runs.append([(k, x[0].tolist()) for k, x in got if x is not None])
    assert runs[0] == runs[1]                                   # same seed, same kicks
    steps = [k for k, _ in runs[0]]
    rows = {r_ for _, rs in runs[0] for r_ in rs}
    assert min(steps) >= 1000 and max(steps) < 9000 and rows == {0, 1}
    n = sum(len(rs) for _, rs in runs[0])
    assert 120 < n < 200                                        # 2 cells x 100 Hz x 0.8 s = 160 expected
    with pytest.raises(ValueError):
        proto.Stimulator(r, len(NEURONS), 12, None)             # kicks need the profile's kick size


def test_assay_kick_stream_is_the_assay_scripts():
    """kick_rng "assay" reproduces scripts/assay_pathways.py run_trial's draws:
    default_rng(seed + 10000), one uniform per stimulated cell per step from step 0."""
    r = proto.resolve(doc(config={"seed": 2, "kick_rng": "assay", "preparation": "brain_only"}, duration_ms=100,
                          events=[{"effector": "kick", "target": {"type": ["MDN", "LB3b"]}, "t_ms": 0,
                                   "dur_ms": 100, "rate_hz": 100}]), NEURONS, 0.1)["resolved"]
    assert (r["preparation"], r["kick_rng"]) == ("brain_only", "assay")
    s = proto.Stimulator(r, len(NEURONS), 2, 68.75)
    idx, rng = np.array([0, 1, 4]), np.random.default_rng(2 + 10_000)
    for step in range(1000):
        want = idx[rng.random(len(idx)) < 100 * 0.1 / 1000.0]
        got = s.kick(step, 0.1)
        assert (got[0].tolist() if got else []) == want.tolist()


def test_brain_only_refuses_world_events():
    with pytest.raises(ValueError, match="brain_only"):
        proto.resolve(doc(config={"seed": 1, "preparation": "brain_only"}, events=[
            {"effector": "world", "set": {"light_lux": 10}, "t_ms": 0, "dur_ms": 1}]), NEURONS, 0.1)
    with pytest.raises(ValueError, match="preparation"):
        proto.resolve(doc(config={"seed": 1, "preparation": "slice"}), NEURONS, 0.1)


# held-out guard

def test_guard_flags_giant_fibre_and_fresh_seeds(tmp_path):
    pr = proto.resolve(doc(events=[{"effector": "current", "target": {"type": "DNp01"}, "t_ms": 0, "dur_ms": 1}]),
                       NEURONS, 0.1)
    g = heldout.check(pr, NEURONS)
    assert {h["id"] for h in g["items"]} == {"gf_dlm", "gf_latency"} and g["seed_spent"]
    log = tmp_path / "spent.jsonl"
    with pytest.raises(SystemExit, match="gf_dlm"):
        heldout.enforce(g, [], log, "t")
    heldout.enforce(g, ["gf_dlm", "gf_latency"], log, "t")
    assert json.loads(log.read_text())["spent"] == ["gf_dlm", "gf_latency"]
    fresh = heldout.check({**pr, "config": {"seed": 40}}, NEURONS)
    assert not fresh["seed_spent"]
    with pytest.raises(SystemExit, match="seed 40"):
        heldout.enforce(fresh, ["gf_dlm", "gf_latency"], log, "t")
    clean = heldout.check(proto.resolve(doc(), NEURONS, 0.1), NEURONS)
    assert clean["items"] == []
    heldout.enforce(clean, [], log, "t")


# the protocol files

def atlas_neurons():
    info = json.loads((ATLAS / "atlas.json").read_text())
    arr = unpack(gzip.open(ATLAS / "neurons.bin.gz").read(), info["arrays"])
    keep = arr["in_model"] > 0
    voc = info["vocab"]
    col = lambda k: np.asarray(voc[k], dtype=object)[arr[k][keep]]
    # a stand-in for the model's table: same rows and order (test_workbench checks the order)
    return pd.DataFrame({"bodyId": arr["bodyid"][keep], "type": col("type"), "class": col("class"),
                         "superclass": col("superclass"), "somaSide": col("side"), "instance": ""})


PROTOCOLS = sorted((APP / "protocols").glob("*.json")) + sorted((APP / "protocols" / "assay").glob("*.json")) + sorted(
    (APP / "protocols" / "eye").glob("*.json")) + sorted((APP / "protocols" / "t4t5").glob("*.json")) + sorted(
    (APP / "tests" / "protocols").glob("*.json"))


@pytest.mark.skipif(not (ATLAS / "atlas.json").exists(), reason="atlas not built")
@pytest.mark.parametrize("path", PROTOCOLS, ids=lambda p: p.stem)
def test_protocol_files_resolve(path):
    p = json.loads(path.read_text())
    assert p["format"] == "flyemu-protocol/1" and p.get("title")
    r = proto.resolve(p, atlas_neurons(), 0.1)
    g = heldout.check(r, atlas_neurons())
    assert g["items"] == [] and g["seed_spent"], "library protocols must not spend held-out data"
    if path.parent == APP / "protocols":
        assert p.get("expect", {}).get("text"), "library protocols state what a real fly does"


@pytest.mark.skipif(not (ATLAS / "atlas.json").exists(), reason="atlas not built")
def test_variant_rows_load_label_and_match(monkeypatch):
    """The graded-medulla variant's rows pass the model's own table checks, are labelled
    measured with a source, and make exactly the intended types graded."""
    sys.path.insert(0, str(REPO / "src"))
    from flyemu import params
    path = APP / "protocols" / "eye" / "variant_graded_medulla.csv"
    monkeypatch.delenv("FLYEMU_EXTRA_PARAMS", raising=False)
    n_live = len(params.load())
    monkeypatch.setenv("FLYEMU_EXTRA_PARAMS", str(path))
    rows = pd.read_csv(path, comment="#")
    assert len(params.load()) == n_live + len(rows)
    assert (rows.basis == "measured").all() and rows.source.notna().all()
    types = atlas_neurons()["type"].astype(str)
    hit = np.zeros(len(types), bool)
    for rx in rows.type:
        m = types.str.match(rx).to_numpy()
        assert m.any(), rx
        hit |= m
    assert set(types[hit]) == {"Mi1", "Tm3", "Tm1", "Tm2", "Mi4", "Mi9", "C3"} | {
        f"T{k}{s}" for k in "45" for s in "abcd"}
    for p in sorted((APP / "protocols" / "eye").glob("graded-*.json")):
        d = json.loads(p.read_text())
        assert d["config"]["extra_params"] == "app/protocols/eye/variant_graded_medulla.csv"
        assert d["variant"]["name"] and d["expect"]["status"] == "prediction"


def test_record_labels_variants():
    import record
    assert record.profile_status("m9r", {}) == "adopted (working profile)"
    assert record.profile_status("m9r", {}, True) == (
        "adopted profile with extra per-type rows: custom, not validated")
    assert record.profile_status("m9r", {"a|b": 1}, True) == (
        "adopted profile with overrides and extra per-type rows: custom, not validated")
    assert record.profile_status("m4", {}) == "regression reference"
    assert record.profile_status("m4", {"a|b": 1}) == (
        "m4 (regression reference) with overrides: custom, not validated")
    assert record.profile_status("m9", {}) == "custom, not validated"


# recordings: an intervention changes nothing before it starts

def recordings(base):
    out = []
    for m in sorted(base.glob("*/manifest.json")):
        man = json.loads(m.read_text())
        if man.get("status") == "complete" and man.get("protocol"):
            out.append(m.parent)
    return out


def pairs():
    out = []
    for base in (LIB, SMOKE, ASSAY):
        runs = recordings(base) if base.exists() else []
        ctrl = [r for r in runs if proto.is_control(json.loads((r / "manifest.json").read_text())["protocol"])]
        for r in runs:
            if r in ctrl:
                continue
            m = json.loads((r / "manifest.json").read_text())
            match = [c for c in ctrl if json.loads((c / "manifest.json").read_text())["config"] == m["config"]]
            if match:
                out.append((r, match[0]))
    return out


@pytest.mark.parametrize("run,ctrl", pairs(), ids=lambda p: p.name)
def test_identical_before_first_event(run, ctrl):
    a, b = RecReader(run), RecReader(ctrl)
    res = a.manifest["protocol"]["resolved"]
    assert not res["genotype"], "genotype runs differ from step 0; compare them as a whole"
    first = min(e["on_step"] for e in res["events"])
    ts = a.manifest["timestep_ms"]
    ta, ra = a.all_spikes()
    tb, rb = b.all_spikes()
    sa = np.round(ta / ts).astype(np.int64)
    sb = np.round(tb / ts).astype(np.int64)
    pre_a = sorted(zip(sa[sa < first].tolist(), ra[sa < first].tolist()))
    pre_b = sorted(zip(sb[sb < first].tolist(), rb[sb < first].tolist()))
    assert pre_a == pre_b and (len(pre_a) > 0 or first == 0)
    # the stimulus was delivered: an effector acting on cells changes the spikes;
    # a world change is recorded as applied at its onset (whether the fly senses
    # it is the result, not a property of the recorder)
    direct = [e for e in res["events"] if e["effector"] != "world"]
    if direct:
        post_a = set(zip(sa[sa >= first].tolist(), ra[sa >= first].tolist()))
        post_b = set(zip(sb[sb >= first].tolist(), rb[sb >= first].tolist()))
        assert post_a != post_b
    worlds = [e for e in res["events"] if e["effector"] == "world"]
    applied = res.get("world_applied") or []
    assert len(applied) == len(worlds) and all(w and w["step"] == e["on_step"] for w, e in zip(applied, worlds))


@pytest.mark.parametrize("run", [r for base in (LIB, SMOKE, ASSAY) if base.exists() for r in recordings(base)], ids=lambda p: p.name)
def test_kicks_recorded_inside_their_events(run):
    r = RecReader(run)
    ev = [e for e in r.manifest["protocol"]["resolved"]["events"] if e["effector"] == "kick"]
    steps, rows = [], []
    for k in range(len(r)):
        c = r.chunk(k)
        if "kick_step" in c:
            steps.append(c["kick_step"]); rows.append(c["kick_row"])
    n = int(sum(s.size for s in steps))
    assert n == r.manifest["summary"].get("kicks_total", 0)
    if not ev:
        assert n == 0
        return
    s, w = np.concatenate(steps).astype(np.int64), np.concatenate(rows).astype(np.int64)
    inside = np.zeros(s.size, bool)
    for e in ev:
        inside |= (s >= e["on_step"]) & (s < e["off_step"]) & np.isin(w, e["rows"])
    assert inside.all() and n > 0
