"""fly_brain.zip: one file that holds the fly (docs/FLY_BRAIN_ZIP.md). Shared by the packer (pack.py) and
the entry point (run.py).

Standard library only, because run.py's launcher imports this module straight out of the zip
(`PYTHONPATH=fly_brain.zip/code python -m flyemu.run fly_brain.zip ...`) before anything is extracted.

A zip member has two names: its member path (the spec's layout: `connectome/edges.parquet`) and its runtime
path (where the simulator reads it: `data/cache/male_cns_edges.parquet`). Extraction writes every member to
its runtime path under a fresh root, so the code runs unchanged, with `Path(__file__).parents[2]` as that root.
manifest.json lists every member with its sha256, size, group and both paths; a zip member the manifest does
not list, or a hash that does not match, is refused.
"""
from __future__ import annotations

import hashlib
import json
import os
import sys
import zipfile
from pathlib import Path

SCHEMA = 1
MANIFEST = "manifest.json"
FIXED_DATE = (1980, 1, 1, 0, 0, 0)            # members carry no clock time, so the same inputs give the same zip
STORED_SUFFIXES = (".parquet", ".gz", ".npz", ".zip", ".png", ".jpg")   # already compressed


class Refused(Exception):
    """The zip, a member or a request failed a check; nothing was run."""


def sha256_file(path: str | os.PathLike, chunk: int = 1 << 20) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for b in iter(lambda: f.read(chunk), b""):
            h.update(b)
    return h.hexdigest()


def sha256_bytes(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def write_member(zf: zipfile.ZipFile, name: str, data: bytes) -> None:
    zi = zipfile.ZipInfo(name, date_time=FIXED_DATE)
    zi.external_attr = 0o644 << 16
    zi.compress_type = zipfile.ZIP_STORED if name.endswith(STORED_SUFFIXES) else zipfile.ZIP_DEFLATED
    zf.writestr(zi, data, compresslevel=6 if zi.compress_type == zipfile.ZIP_DEFLATED else None)


def read_manifest(zip_path: str | os.PathLike) -> dict:
    with zipfile.ZipFile(zip_path) as zf:
        try:
            man = json.loads(zf.read(MANIFEST))
        except KeyError:
            raise Refused(f"{zip_path}: no {MANIFEST}") from None
    if man.get("schema") != SCHEMA:
        raise Refused(f"{zip_path}: schema {man.get('schema')!r}, this reader knows {SCHEMA}")
    return man


def verify(zip_path: str | os.PathLike) -> dict:
    """Check every member against the manifest's sha256 and size; refuse on any mismatch, missing or extra member.
    Returns the manifest plus the zip's and the manifest's own sha256."""
    man = read_manifest(zip_path)
    listed = {m["path"]: m for m in man["members"]}
    bad = []
    with zipfile.ZipFile(zip_path) as zf:
        names = set(zf.namelist()) - {MANIFEST}
        for extra in sorted(names - set(listed)):
            bad.append(f"unlisted member {extra}")
        for missing in sorted(set(listed) - names):
            bad.append(f"missing member {missing}")
        for name in sorted(names & set(listed)):
            h = hashlib.sha256()
            n = 0
            with zf.open(name) as f:
                for b in iter(lambda: f.read(1 << 20), b""):
                    h.update(b)
                    n += len(b)
            m = listed[name]
            if h.hexdigest() != m["sha256"] or n != m["bytes"]:
                bad.append(f"hash/size mismatch {name}")
        man_bytes = zf.read(MANIFEST)
    if bad:
        raise Refused(f"{zip_path}: {len(bad)} member check(s) failed: " + "; ".join(bad[:10]))
    return {**man, "_zip_sha256": sha256_file(zip_path), "_manifest_sha256": sha256_bytes(man_bytes)}


def extract(zip_path: str | os.PathLike, root: str | os.PathLike, man: dict) -> Path:
    """Write every member to root/<runtime path>. The root must be new or empty."""
    root = Path(root)
    root.mkdir(parents=True, exist_ok=True)
    if any(root.iterdir()):
        raise Refused(f"extraction root {root} is not empty")
    with zipfile.ZipFile(zip_path) as zf:
        for m in man["members"]:
            dest = root / m["runtime"]
            if root.resolve() not in dest.resolve().parents:
                raise Refused(f"member {m['path']} escapes the root ({m['runtime']})")
            dest.parent.mkdir(parents=True, exist_ok=True)
            with zf.open(m["path"]) as src, open(dest, "wb") as out:
                for b in iter(lambda: src.read(1 << 20), b""):
                    out.write(b)
    return root


class ReadGuard:
    """Records every file the process opens (Python audit events) and refuses reads under denied roots.

    Native readers (pyarrow parquet, MuJoCo's mesh loader) do not raise audit events; run.py checks their
    paths separately (parquet paths come from the code's own constants, mesh paths from the compiled spec).
    """

    def __init__(self, allowed_roots, deny_roots, deny_inside_allowed=()):
        self.allowed = [os.path.realpath(r) for r in allowed_roots]
        self.deny = [os.path.realpath(r) for r in deny_roots]
        self.deny_inside = [os.path.realpath(r) for r in deny_inside_allowed]
        self.outside: set[str] = set()       # opened files under no allowed root (reported, not refused)
        self.denied: list[str] = []

    @staticmethod
    def _under(p: str, roots) -> bool:
        return any(p == r or p.startswith(r + os.sep) for r in roots)

    def check(self, p: str) -> None:
        if self._under(p, self.deny_inside) or (self._under(p, self.deny) and not self._under(p, self.allowed)):
            self.denied.append(p)
            raise PermissionError(f"fly_brain.zip read guard: {p} is outside the zip")
        if not self._under(p, self.allowed):
            self.outside.add(p)

    @staticmethod
    def _is_read(mode, flags) -> bool:
        if isinstance(mode, str):
            return not any(c in mode for c in "wax+")
        return not (isinstance(flags, int) and flags & (os.O_WRONLY | os.O_RDWR))

    def hook(self, event, args):
        if event == "open" and args and isinstance(args[0], (str, bytes, os.PathLike)):
            mode = args[1] if len(args) > 1 else None
            flags = args[2] if len(args) > 2 else None
            if not self._is_read(mode, flags):
                return                          # writes (the run's own outputs) are not reads of the fly
            p = os.fsdecode(args[0])
            self.check(os.path.realpath(p if os.path.isabs(p) else os.path.join(os.getcwd(), p)))

    def install(self) -> "ReadGuard":
        sys.addaudithook(self.hook)
        return self
