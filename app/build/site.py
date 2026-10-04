"""Build a static copy of Fly Workbench that any file server can host.

    python app/build/site.py [--out runs/app-site] [--runs runs/app] [--only m9-s12-2000ms legacy/3000ms-m1 ...]

Copies the page (app/web), the data it needs (app/data: atlas and body) and the
chosen recordings into one directory, and writes catalog.json once instead of
on each request. Nothing is uploaded; publishing stays a separate, manual step.
Recordings that are still being written are skipped.
"""
from __future__ import annotations

import argparse
import json
import shutil
import sys
from pathlib import Path

APP = Path(__file__).resolve().parents[1]
REPO = APP.parent
sys.path.insert(0, str(APP / "server"))
from serve import catalog  # noqa: E402


def size(p: Path) -> int:
    return sum(f.stat().st_size for f in p.rglob("*") if f.is_file())


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--out", type=Path, default=REPO / "runs" / "app-site")
    ap.add_argument("--runs", type=Path, default=REPO / "runs" / "app")
    ap.add_argument("--only", nargs="*", help="recording ids to include (default: every complete one)")
    a = ap.parse_args()
    cat = catalog(a.runs)
    recs = [r for r in cat["recordings"] if r["status"] == "complete" and (not a.only or r["id"] in a.only)]
    if a.only and len(recs) != len(a.only):
        sys.exit(f"not found or incomplete: {sorted(set(a.only) - {r['id'] for r in recs})}")
    if a.out.exists():
        if not (a.out / "catalog.json").exists():
            sys.exit(f"{a.out} exists and is not a previous site build; refusing to overwrite")
        shutil.rmtree(a.out)
    shutil.copytree(APP / "web", a.out)
    shutil.copytree(APP / "data", a.out / "data")
    for r in recs:
        shutil.copytree(a.runs / r["id"], a.out / "runs" / r["id"])
    cat["recordings"] = recs
    cat["static"] = True
    (a.out / "catalog.json").write_text(json.dumps(cat))
    print(f"wrote {a.out}: {len(recs)} recordings, {len(cat['atlases'])} atlas, {len(cat['bodies'])} body; "
          f"{size(a.out) / 1e6:.1f} MB")


if __name__ == "__main__":
    main()
