"""Triage line 11: the MetaWorm driver refuses a binary older than its sources (wbody2, 8 Nov 2026)."""
import os

import pytest

from wormemu.body import metaworm as mw


def _tree(tmp_path, t_bin, t_src):
    (tmp_path / "driver").mkdir()
    (tmp_path / "sim" / "fem").mkdir(parents=True)
    files = {"bin": tmp_path / "driver" / "run_body", "cpp": tmp_path / "driver" / "run_body.cpp",
             "h": tmp_path / "sim" / "fem" / "World.h"}
    for p in files.values():
        p.write_text("x")
    os.utime(files["bin"], (t_bin, t_bin))
    os.utime(files["cpp"], (t_src, t_src))
    os.utime(files["h"], (500_000, 500_000))  # a header older than either binary
    return files


def test_fresh_driver_accepted(tmp_path, monkeypatch):
    f = _tree(tmp_path, t_bin=2_000_000, t_src=1_000_000)
    monkeypatch.setattr(mw, "ROOT", tmp_path)
    monkeypatch.setattr(mw, "DRIVER", f["bin"])
    assert mw.ensure_driver() == f["bin"]


def test_stale_driver_refused(tmp_path, monkeypatch):
    f = _tree(tmp_path, t_bin=1_000_000, t_src=2_000_000)
    monkeypatch.setattr(mw, "ROOT", tmp_path)
    monkeypatch.setattr(mw, "DRIVER", f["bin"])
    assert mw.stale_sources(f["bin"]) == [f["cpp"]]
    with pytest.raises(RuntimeError, match="older than"):
        mw.ensure_driver()


def test_built_driver_is_current():
    if not mw.DRIVER.exists():
        pytest.skip("driver not built in this checkout")
    assert mw.stale_sources() == []
