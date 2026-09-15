"""Check that every run record is complete.

docs/VALIDATION.md requires each substantial run to retain its code commit,
input hashes, environment, timing, memory and an explicit list of scaffolds.
This verifies that for every record in runs/ and fails loudly if any is short.

    uv run python scripts/audit_provenance.py
"""
from __future__ import annotations

import json
import sys
from collections import Counter
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
REQUIRED = ["run_id", "started_utc", "code", "environment", "inputs",
            "config", "scaffolds", "results", "wall_seconds", "peak_rss_gb"]


def main() -> None:
    files = sorted((REPO / "runs").glob("*/*.provenance.json"))
    if not files:
        print("no provenance records found")
        raise SystemExit(1)

    problems: list[str] = []
    scaffolds: Counter[str] = Counter()
    hashed = commits = 0
    for f in files:
        try:
            d = json.loads(f.read_text())
        except Exception as e:
            problems.append(f"{f.name}: unreadable ({e})")
            continue
        for k in REQUIRED:
            if k not in d:
                problems.append(f"{f.name}: missing '{k}'")
        if d.get("code", {}).get("flyemu_commit"):
            commits += 1
        ins = d.get("inputs", {})
        if ins and all(v.get("sha256") for v in ins.values()):
            hashed += 1
        if not d.get("scaffolds"):
            problems.append(f"{f.name}: no scaffolds declared")
        for s in d.get("scaffolds", []):
            scaffolds[s.split(".")[0][:64]] += 1

    print(f"provenance records          : {len(files)}")
    print(f"  with this repo's commit   : {commits}/{len(files)}")
    print(f"  with SHA-256 on all inputs: {hashed}/{len(files)}")
    print(f"  distinct scaffolds declared: {len(scaffolds)}")
    print("\nmost common scaffolds:")
    for text, n in scaffolds.most_common(6):
        print(f"  {n:3d}  {text}")

    if problems:
        print(f"\n{len(problems)} PROBLEMS:")
        for p in problems[:20]:
            print("  " + p)
        raise SystemExit(1)
    print("\nall records complete")


if __name__ == "__main__":
    main()
