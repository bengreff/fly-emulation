"""Checks for the Fidelity tab (M4): the construction tables the app builds from the model
(app/build/fidelity.py) and the page's join of run values to them (app/web/js/fidelity.js).

    .venv/bin/python -m pytest app/tests/test_fidelity.py -q
"""
from __future__ import annotations

import json
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

APP = Path(__file__).resolve().parents[1]
REPO = APP.parent
sys.path.insert(0, str(APP / "build"))
import fidelity as fb  # noqa: E402
from flyemu import model_data, profiles  # noqa: E402


@pytest.fixture(scope="module")
def fid():
    return json.loads(json.dumps(fb.build()))


def test_tables_match_the_model(fid):
    md = model_data.load()
    st = model_data.construction_state(md)
    assert [m["id"] for m in fid["mechanisms"]] == list(md.mechanisms.id)
    assert len(fid["parameters"]) == len(md.parameters) == fid["state"]["n_unknowns"]
    assert fid["state"]["n_mechanisms"] == st["n_mechanisms"]
    assert sum(sum(c.values()) for c in fid["state"]["by_tier"].values()) == st["n_mechanisms"]
    assert [p["name"] for p in fid["profiles"]] == list(profiles.PROFILES)
    status = {p["name"]: p["status"] for p in fid["profiles"]}
    assert status[profiles.WORKING_PROFILE] == "adopted (working profile)" and status["m4"] == "regression reference"
    for p in fid["profiles"]:
        assert all(v[1] in model_data.LABELS for v in p["values"].values()), p["name"]
    assert {b["id"]: b["simulate"] for b in fid["bodies"]} == {"flybody": True, "neuromechfly": False}


def test_split_yaml_fields_are_rejoined(fid):
    """Unquoted commas in mechanisms.yaml flow mappings cut a field; the build rejoins the
    pieces in order and says which field it rejoined."""
    by = {m["id"]: m for m in fid["mechanisms"]}
    assert set(by["B1"]) == set(fb.MECH_FIELDS) | {"rejoined"}
    assert by["B1"]["name"].endswith("(mm, g, s)") and by["B1"]["rejoined"] == ["name"]
    assert all(set(m) == set(fb.MECH_FIELDS) | {"rejoined"} for m in fid["mechanisms"])
    assert not any(m["rejoined"] for m in fid["mechanisms"] if "," not in str(m["name"]) + str(m["notes"]))


@pytest.mark.skipif(not shutil.which("node"), reason="needs node")
def test_page_join_matches_model_owners(fid, tmp_path):
    """The page's owner join (keyPattern, ownerIndex) gives the same owning rows as
    flyemu.model_data.owners, and boundsCheck flags a value outside its range only."""
    md = model_data.load()
    keys = sorted({k.replace("*", "Mi1") for k in md.parameters.registry_key if k}
                  | {k.replace("*", "T4a") for k in md.structural.key_pattern}
                  | {"cell_type:all|v_rest", "nothing:here|at_all", "joint:leg|regex.(chars)"})
    want = {k: sorted([s, m] for s, _, m in model_data.owners(md, k)) for k in keys}
    for f in ("fidelity.js", "inspector.js"):
        shutil.copy(APP / "web" / "js" / f, tmp_path / f)
    (tmp_path / "package.json").write_text('{"type": "module"}')
    (tmp_path / "fid.json").write_text(json.dumps(fid))
    (tmp_path / "keys.json").write_text(json.dumps(keys))
    (tmp_path / "run.mjs").write_text("""
import { readFileSync } from "fs";
import { ownerIndex, boundsCheck, basisBySubsystem, profileDiff } from "./fidelity.js";
const fid = JSON.parse(readFileSync("fid.json")), keys = JSON.parse(readFileSync("keys.json"));
const own = ownerIndex(fid), src = { parameter: "parameters", "mechanism switch": "switch" };
const owners = Object.fromEntries(keys.map(k => [k, own(k).map(o => [src[o.kind] || "structural", o.mech]).sort()]));
const p = fid.parameters.find(r => r.registry_key === "cell_type:all|v_rest");
const [entity, property] = p.registry_key.split("|");
const inv = [{ entity, property, value: String(p.bio_min - 1), basis: "guessed", subsystem: "a" },
             { entity, property, value: String(p.bio_max), basis: "inferred", subsystem: "a" },
             { entity: "x:y", property: "z", value: "text", basis: "measured", subsystem: "b" }];
const w = fid.profiles.find(q => q.name === fid.working), r = fid.profiles.find(q => q.name === fid.regression);
console.log(JSON.stringify({ owners, bounds: boundsCheck(inv, own), counts: basisBySubsystem(inv),
  diff: profileDiff(w, r).length, same: profileDiff(w, w).length }));
""")
    out = subprocess.run(["node", "run.mjs"], cwd=tmp_path, capture_output=True, text=True, timeout=120)
    assert out.returncode == 0, out.stderr
    got = json.loads(out.stdout)
    assert got["owners"] == {k: [list(x) for x in v] for k, v in want.items()}
    assert got["owners"]["nothing:here|at_all"] == []
    assert got["bounds"]["ranged"] == 2 and len(got["bounds"]["outside"]) == 1
    assert got["counts"]["all"] == {"guessed": 1, "inferred": 1, "measured": 1}
    assert got["same"] == 0 and got["diff"] > 0
