"""Checks for Fly Workbench formats, joins and the page.

    .venv/bin/python -m pytest app/tests -q

Tests on generated data (the atlas, recordings under runs/app) skip when the
data has not been built; the format tests always run.
"""
from __future__ import annotations

import base64
import gzip
import json
import subprocess
import sys
from pathlib import Path

import numpy as np
import pytest

APP = Path(__file__).resolve().parents[1]
REPO = APP.parent
sys.path.insert(0, str(APP / "server"))
sys.path.insert(0, str(APP / "build"))
from recfmt import RecReader, RecWriter, spikes_to_csr, unpack  # noqa: E402

ATLAS = APP / "data" / "atlas" / "male-cns-v1.0"
RUNS = REPO / "runs" / "app"
MAIN = REPO.parents[2] if (REPO / ".git").is_file() else REPO     # the main checkout when run from a worktree


def native_runs():
    out = []
    for m in sorted(RUNS.glob("*/manifest.json")):
        man = json.loads(m.read_text())
        if man.get("format") == "flyemu-rec/1" and man.get("status") == "complete":
            out.append(m.parent)
    return out


def legacy_runs():
    return sorted(m.parent for m in (RUNS / "legacy").glob("*/manifest.json"))


@pytest.fixture(scope="module")
def atlas():
    if not (ATLAS / "atlas.json").exists():
        pytest.skip("atlas not built (python app/build/atlas.py)")
    info = json.loads((ATLAS / "atlas.json").read_text())
    arr = unpack(gzip.open(ATLAS / "neurons.bin.gz").read(), info["arrays"])
    return info, arr


# formats

def test_spikes_to_csr_keeps_exact_steps():
    rng = np.random.default_rng(0)
    step0, n_bins, spb = 5000, 250, 10
    steps = rng.integers(step0, step0 + n_bins * spb, 4000)
    rows = rng.integers(0, 300, steps.size).astype(np.uint32)
    c = spikes_to_csr(steps, rows, step0, n_bins, spb)
    assert c["spike_ptr"][-1] == steps.size and np.all(np.diff(c["spike_ptr"].astype(np.int64)) >= 0)
    b = np.repeat(np.arange(n_bins), np.diff(c["spike_ptr"].astype(np.int64)))
    got = sorted(zip((step0 + b * spb + c["spike_sub"]).tolist(), c["spike_row"].tolist()))
    assert got == sorted(zip(steps.tolist(), rows.tolist()))


def test_recording_round_trip(tmp_path):
    static = {"row_bodyid": np.array([10, 20, 30], np.int64), "tau_m": np.array([1.5, 2, 3], np.float32)}
    w = RecWriter(tmp_path / "r", {"timestep_ms": 0.1, "n_rows": 3,
                                   "streams": {"spikes": {"bin_ms": 1.0}}}, static)
    spikes = [(0, 0), (7, 2), (13, 1), (2499, 0)]
    for k in range(2):
        s0 = k * 2500
        sel = [(s + s0, r) for s, r in spikes]
        arr = spikes_to_csr(np.array([s for s, _ in sel]), np.array([r for _, r in sel], np.uint32), s0, 250, 10)
        arr["torque"] = np.full((50, 2), k, np.float32)
        w.add_chunk(k * 250.0, (k + 1) * 250.0, arr)
    w.finish("complete", summary={"spikes_total": 8})
    r = RecReader(tmp_path / "r")
    assert r.manifest["status"] == "complete" and len(r) == 2 and r.manifest["duration_ms"] == 500.0
    for k, v in static.items():
        np.testing.assert_array_equal(r.static()[k], v)
    t, rows = r.all_spikes()
    np.testing.assert_allclose(sorted(t), sorted([0.0, 0.7, 1.3, 249.9, 250.0, 250.7, 251.3, 499.9]), atol=1e-9)
    assert sorted(rows.tolist()) == [0, 0, 0, 0, 1, 1, 2, 2]
    assert r.chunk(1)["torque"].shape == (50, 2) and r.chunk(1)["torque"][0, 0] == 1


# atlas

def test_atlas_positions_and_policy(atlas):
    info, arr = atlas
    assert arr["pos"].shape == (info["n"], 3) and np.isfinite(arr["pos"]).all()
    assert int((arr["in_model"] > 0).sum()) == info["n_in_model_policy"]
    assert len(np.unique(arr["bodyid"])) == info["n"]
    counts = np.bincount(arr["pos_basis"], minlength=5)
    assert counts.sum() == info["n"]
    assert list(info["coverage"]["pos_basis_counts"].values()) == counts[:len(info["coverage"]["pos_basis_counts"])].tolist()


def test_atlas_counts_reconcile(atlas):
    """The header's numbers: cache = in model + scan only; in model = traced + untraced-but-typed."""
    info, arr = atlas
    c = info["counts"]
    assert c["cache"] == info["n"] == arr["bodyid"].size
    assert c["in_model"] == int((arr["in_model"] > 0).sum()) == info["n_in_model_policy"]
    assert c["in_model"] == c["in_model_traced"] + c["in_model_untraced_typed"]
    assert c["cache"] == c["in_model"] + c["scan_only"]
    assert sum(c["in_model_untraced_by_status"].values()) == c["in_model_untraced_typed"]
    assert sum(c["scan_only_by_status"].values()) == c["scan_only"]
    for run in native_runs():
        m = json.loads((run / "manifest.json").read_text())
        assert m["n_rows"] == c["in_model"], run.name


def test_atlas_edges_reciprocal(atlas):
    info, _ = atlas
    index = json.loads((ATLAS / "edges" / "index.json").read_text())
    S = info["shard"]
    shards = {}

    def shard(k):
        if k not in shards:
            shards[k] = unpack(gzip.open(ATLAS / "edges" / f"{k:03d}.bin.gz").read(), index[k])
        return shards[k]

    rng = np.random.default_rng(1)
    total = 0
    for i in rng.choice(info["n"], 40, replace=False):
        e = shard(i // S)
        j = i % S
        p = e["out_ptr"].astype(np.int64)
        for post, w in zip(e["out_idx"][p[j]:p[j + 1]], e["out_w"][p[j]:p[j + 1]]):
            assert w >= info["min_synapses"]
            f = shard(int(post) // S)
            q = f["in_ptr"].astype(np.int64)
            jj = int(post) % S
            ins = dict(zip(f["in_idx"][q[jj]:q[jj + 1]].tolist(), f["in_w"][q[jj]:q[jj + 1]].tolist()))
            assert ins.get(int(i)) == w
            total += 1
    assert total > 0


# recordings

@pytest.mark.parametrize("run", native_runs(), ids=lambda p: p.name)
def test_native_recording(run, atlas):
    info, arr = atlas
    r = RecReader(run)
    m, st = r.manifest, r.static()
    t, rows = r.all_spikes()
    assert t.size == m["summary"]["spikes_total"]
    assert np.all((t >= 0) & (t < m["duration_ms"])) and np.all(rows < m["n_rows"])
    # the model table keeps atlas order: its rows are the in-policy atlas neurons
    np.testing.assert_array_equal(st["row_bodyid"], arr["bodyid"][arr["in_model"] > 0])
    nact = len(m["names"]["actuators"])
    assert all(len(m["limits"][k]) == nact for k in ("lo", "hi", "limited"))
    for k in range(len(r)):
        c = r.chunk(k)
        assert c["torque"].shape[1] == nact and np.isfinite(c["xpos"]).all()


@pytest.mark.parametrize("run", legacy_runs(), ids=lambda p: p.name)
def test_legacy_recording(run, atlas):
    info, arr = atlas
    r = RecReader(run)
    m, st = r.manifest, r.static()
    assert "legacy" in m["flags"] and "matches" in m["join"]
    mn = arr["bodyid"][arr["superclass"] == info["vocab"]["superclass"].index("vnc_motor")]
    assert set(st["row_bodyid"].tolist()) <= set(mn.tolist()) and st["row_bodyid"].size == 708
    t, rows = r.all_spikes()
    assert t.size == m["summary"]["motor_spikes"]
    src = MAIN / m["provenance"]["source"]
    if src.exists():
        s = src.read_text()
        d = json.loads(s[s.index("{"): s.rindex("}") + 1])
        sp = np.frombuffer(base64.b64decode(d["motor_spikes"]), np.int32).reshape(-1, 2)
        np.testing.assert_array_equal(np.bincount(rows, minlength=708), np.bincount(sp[:, 1], minlength=708))
        np.testing.assert_array_equal(np.sort(np.round(t).astype(int)), np.sort(sp[:, 0]))


def test_catalog_lists_runs():
    from serve import catalog
    cat = catalog(RUNS)
    ids = {r["id"] for r in cat["recordings"]}
    assert {p.relative_to(RUNS).as_posix() for p in native_runs()} <= ids
    for r in cat["recordings"]:
        if r["id"].startswith("legacy/"):
            assert "legacy" in r["flags"] and "not validated" in r["flags"]


def test_catalog_lists_scored_libraries(tmp_path):
    # what the Compare tab sets side by side: a folder with a scores.json holding trials
    from serve import catalog
    for lib, prof, host in (("lib-a", "m9r", "backhouse"), ("lib-b", "m9", "mac.local"), ("lib-c", "m9", "mac.local")):
        for run in ("control-s0", "sugar-s0"):
            (tmp_path / lib / run).mkdir(parents=True)
            (tmp_path / lib / run / "manifest.json").write_text(json.dumps({
                "format": "flyemu-rec/1", "status": "complete", "config": {"profile": prof, "seed": 0},
                "provenance": {"host": host, "git": {"commit": "abc1234"}}}))
        trials = [{"protocol": "sugar", "seeds": [0]}] if lib != "lib-c" else []
        (tmp_path / lib / "scores.json").write_text(json.dumps({"scores": [], "trials": trials, "commits": {"sugar-s0": "abc1234"}}))
    (tmp_path / "lib-a" / "NOTE.txt").write_text("pre-fold\n")
    libs = {L["id"]: L for L in catalog(tmp_path)["libraries"]}
    assert set(libs) == {"lib-a", "lib-b"}            # lib-c has no trials
    a = libs["lib-a"]
    assert a["profiles"] == ["m9r"] and a["commits"] == ["abc1234"] and a["note"] == "pre-fold"
    assert a["hosts"] == {"control-s0": "backhouse", "sugar-s0": "backhouse"} and a["path"] == "runs/lib-a"
    assert libs["lib-b"]["note"] is None
    recs = {r["id"]: r for r in catalog(tmp_path)["recordings"]}
    assert recs["lib-a/sugar-s0"]["library"] == "lib-a"


# the eye view's column placement (app/build/columns.py)

COLUMNS = APP / "data" / "body" / "flybody" / "columns.json"


@pytest.mark.skipif(not COLUMNS.exists(), reason="columns.json not built")
def test_columns_consistent_and_checked():
    c = json.loads(COLUMNS.read_text())
    assert c["format"] == "flyemu-columns/1"
    cells, n_omm = c["cells"], 721
    n = len(cells["bodyId"])
    assert n and all(len(v) == n for v in cells.values())
    assert len(set(cells["bodyId"])) == n
    assert set(cells["eye"]) <= {0, 1} and 0 <= min(cells["column"]) and max(cells["column"]) < n_omm
    assert set(cells["type"]) <= set(range(len(c["types"]))) and min(cells["hops"]) >= 1
    per = {p["type"]: p for p in c["per_type"]}
    for t, p in per.items():
        assert p["n_placed"] <= p["n_scan"]
        assert p["eye_matches_soma_side"] is None or p["eye_matches_soma_side"] > 0.95, t
    # the independent check the placement must keep passing: neighbours by soma land
    # near each other far more often than with placements shuffled within the type
    for t in ("L1", "Mi1", "T4a"):
        assert per[t]["soma_neighbours_near"] > 3 * per[t]["soma_neighbours_near_shuffled"], t


# the page

@pytest.mark.skipif(not (ATLAS / "atlas.json").exists() or not native_runs(), reason="needs the atlas and a recording")
def test_page_renders(tmp_path):
    pytest.importorskip("playwright")
    run = native_runs()[0].name
    p = subprocess.run([sys.executable, str(APP / "tools" / "screenshot.py"), "--out", str(tmp_path),
                        "--shot", f"page:rec={run}&t=500&sel=800184"],
                       capture_output=True, text=True, timeout=300)
    assert p.returncode == 0, p.stdout + p.stderr
    assert (tmp_path / "page.png").exists()
