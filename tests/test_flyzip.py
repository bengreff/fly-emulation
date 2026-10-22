"""fly_brain.zip plumbing (s22 fly2): the manifest's hashes are checked, tampered or unlisted members are refused,
extraction refuses escapes and non-empty roots, and run.py refuses --set keys no mechanism owns."""
import json
import sys
import zipfile
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "src"))

from flyemu import flyzip  # noqa: E402


def _zip(path, members, extra=None, runtime=None):
    man = {"schema": flyzip.SCHEMA, "members": [
        {"path": n, "runtime": (runtime or {}).get(n, n), "sha256": flyzip.sha256_bytes(b), "bytes": len(b)}
        for n, b in members.items()]}
    with zipfile.ZipFile(path, "w") as zf:
        flyzip.write_member(zf, flyzip.MANIFEST, json.dumps(man).encode())
        for n, b in {**members, **(extra or {})}.items():
            flyzip.write_member(zf, n, b)
    return path


def test_verify_and_extract_round_trip(tmp_path):
    z = _zip(tmp_path / "a.zip", {"connectome/x.parquet": b"abc", "code/flyemu/y.py": b"print(1)\n"},
             runtime={"connectome/x.parquet": "data/cache/x.parquet", "code/flyemu/y.py": "src/flyemu/y.py"})
    man = flyzip.verify(z)
    root = flyzip.extract(z, tmp_path / "root", man)
    assert (root / "data/cache/x.parquet").read_bytes() == b"abc"
    assert (root / "src/flyemu/y.py").read_bytes() == b"print(1)\n"
    with pytest.raises(flyzip.Refused, match="not empty"):
        flyzip.extract(z, root, man)


def test_tampered_unlisted_and_escaping_members_are_refused(tmp_path):
    z = _zip(tmp_path / "b.zip", {"a.txt": b"one"})
    man = flyzip.read_manifest(z)
    man["members"][0]["sha256"] = flyzip.sha256_bytes(b"two")
    with zipfile.ZipFile(tmp_path / "c.zip", "w") as zf:
        flyzip.write_member(zf, flyzip.MANIFEST, json.dumps(man).encode())
        flyzip.write_member(zf, "a.txt", b"one")
    with pytest.raises(flyzip.Refused, match="mismatch"):
        flyzip.verify(tmp_path / "c.zip")
    with pytest.raises(flyzip.Refused, match="unlisted"):
        flyzip.verify(_zip(tmp_path / "d.zip", {"a.txt": b"one"}, extra={"b.txt": b"x"}))
    z = _zip(tmp_path / "e.zip", {"a.txt": b"one"}, runtime={"a.txt": "../outside.txt"})
    with pytest.raises(flyzip.Refused, match="escapes"):
        flyzip.extract(z, tmp_path / "root", flyzip.verify(z))


def test_same_inputs_give_the_same_zip(tmp_path):
    m = {"a.txt": b"one", "b.npz": b"two"}
    assert flyzip.sha256_file(_zip(tmp_path / "1.zip", m)) == flyzip.sha256_file(_zip(tmp_path / "2.zip", m))


def test_read_guard_refuses_denied_reads_only(tmp_path):
    g = flyzip.ReadGuard([tmp_path / "ok"], [tmp_path], [tmp_path / "ok" / "no"])
    g.check(str(tmp_path / "ok" / "f"))
    for p in (tmp_path / "other", tmp_path / "ok" / "no" / "f"):
        with pytest.raises(PermissionError):
            g.check(str(p))
    assert g._is_read("rb", None) and not g._is_read("wb", None)


def test_set_keys_without_a_mechanism_are_refused():
    from flyemu import run
    with pytest.raises(flyzip.Refused, match="no mechanism"):
        run._check_sets({"made_up|nonsense_key": 1.0})
