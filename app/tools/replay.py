"""Replay a recording: run the protocol embedded in its manifest again and check
that the new recording is identical (every array it holds: spikes, kicks, body
pose, torques, voltages, eye frames).

    .venv/bin/python app/tools/replay.py runs/app/lib/sugar-grn-kick [--out runs/app/replay/sugar-grn-kick]
    .venv/bin/python app/tools/replay.py A B --compare-only     # compare two existing recordings

Exit status 0 when identical, 1 when not. A difference means the run is not
reproducible from its protocol (model code changed, or a random draw outside
the seeded generators). Cost: as for the original recording (about 3.5 minutes
and 2.4 GB for a 2 s run on the Mac).
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

import numpy as np

APP = Path(__file__).resolve().parents[1]
REPO = APP.parent
sys.path.insert(0, str(APP / "server"))
from recfmt import RecReader  # noqa: E402

SLOT = Path.home() / "director" / "harness" / "slot.py"


def arrays(path: Path) -> dict:
    """Every array the recording holds: static tables, then each chunk array
    joined over chunks (spikes, kicks, body pose, torques, voltages, eyes)."""
    r = RecReader(path)
    out = {f"static/{k}": v for k, v in r.static().items()}
    parts: dict[str, list] = {}
    for i in range(len(r)):
        for k, v in r.chunk(i).items():
            parts.setdefault(k, []).append(np.asarray(v).reshape(len(v), -1) if np.ndim(v) > 1 else np.asarray(v))
    for k, p in parts.items():
        out[k] = np.concatenate(p)
    return out


def compare(a: Path, b: Path) -> dict:
    x, y = arrays(a), arrays(b)
    res = {k: {"identical": False, "missing_in": str(b if k in x else a)} for k in set(x) ^ set(y)}
    for k in sorted(set(x) & set(y)):
        same = x[k].shape == y[k].shape and np.array_equal(x[k], y[k])
        res[k] = {"identical": bool(same), "n": [int(x[k].size), int(y[k].size)]}
        if not same and x[k].shape == y[k].shape and x[k].dtype.kind == "f":
            res[k]["max_abs_diff"] = float(np.abs(x[k] - y[k]).max())
    return res


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("source", type=Path)
    ap.add_argument("other", type=Path, nargs="?")
    ap.add_argument("--out", type=Path)
    ap.add_argument("--compare-only", action="store_true")
    a = ap.parse_args()
    if a.compare_only:
        if a.other is None:
            raise SystemExit("--compare-only needs two recordings")
        target = a.other
    else:
        m = json.loads((a.source / "manifest.json").read_text())
        pr = {k: v for k, v in m["protocol"].items() if k not in ("resolved", "heldout")}
        target = a.out or REPO / "runs" / "app" / "replay" / a.source.name
        if target.exists():
            raise SystemExit(f"{target} exists; choose another --out")
        target.parent.mkdir(parents=True, exist_ok=True)
        pfile = target.with_name(target.name + ".protocol.json")
        pfile.write_text(json.dumps(pr, indent=1) + "\n")
        cmd = [sys.executable, str(APP / "server" / "record.py"), "--protocol", str(pfile), "--out", str(target),
               "--chunk-ms", str(m.get("chunk_ms", 250.0))]
        for item in (m["protocol"].get("heldout") or {}).get("spent_here") or []:
            cmd += ["--spend-heldout", item]
        if SLOT.exists():
            cmd = ["python3", str(SLOT), "run", "--label", f"flyapp: replay {a.source.name}", "--"] + cmd
        print("replaying:", " ".join(cmd), flush=True)
        subprocess.run(cmd, cwd=REPO, check=True, timeout=40 * 60)
    res = compare(a.source, target)
    ok = all(v["identical"] for v in res.values())
    for k, v in sorted(res.items()):
        print(f"  {k:24} {'identical' if v['identical'] else 'DIFFERENT'}  {json.dumps({x: y for x, y in v.items() if x != 'identical'})}")
    print(f"{a.source} vs {target}: {'IDENTICAL' if ok else 'NOT IDENTICAL'} ({len(res)} arrays)")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
