"""Record the intervention library: every protocol in app/protocols, one after
another, each through the machine's slot limiter. Resumable: complete
recordings are skipped, and an interrupted one is moved aside, not deleted.

    .venv/bin/python app/tools/run_library.py [--only control sugar-grn-kick] [--out runs/app/lib]

Cost (m9 on the Mac, measured): about 115 s of wall time per simulated second
plus 15 s to build, 2.4 GB of memory per run; the 2 s library runs take about
4 minutes each.
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import subprocess
import sys
import time
from pathlib import Path

APP = Path(__file__).resolve().parents[1]
REPO = APP.parent
SLOT = Path.home() / "director" / "harness" / "slot.py"


def status(d: Path) -> str | None:
    try:
        return json.loads((d / "manifest.json").read_text()).get("status")
    except (OSError, json.JSONDecodeError):
        return None if not d.exists() else "unreadable"


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--protocols", type=Path, default=APP / "protocols")
    ap.add_argument("--out", type=Path, default=REPO / "runs" / "app" / "lib")
    ap.add_argument("--only", nargs="*")
    ap.add_argument("--timeout-min", type=float, default=40.0, help="per run")
    a = ap.parse_args()
    names = sorted(p.stem for p in a.protocols.glob("*.json"))
    names.sort(key=lambda n: n != "control")          # the control first
    if a.only:
        names = [n for n in names if n in a.only]
    for name in names:
        out = a.out / name
        st = status(out)
        if st == "complete":
            print(f"{name}: complete, skipped", flush=True)
            continue
        if out.exists():
            aside = out.with_name(f"{name}.incomplete-{dt.datetime.now():%Y%m%d-%H%M%S}")
            out.rename(aside)
            print(f"{name}: previous attempt ({st}) moved to {aside.name}", flush=True)
        cmd = [sys.executable, str(APP / "server" / "record.py"),
               "--protocol", str(a.protocols / f"{name}.json"), "--out", str(out)]
        if SLOT.exists():
            cmd = ["python3", str(SLOT), "run", "--label", f"flyapp: library {name}", "--"] + cmd
        t0 = time.time()
        print(f"{name}: recording", flush=True)
        log = a.out / f"{name}.log"
        a.out.mkdir(parents=True, exist_ok=True)
        with log.open("w") as f:
            r = subprocess.run(cmd, cwd=REPO, stdout=f, stderr=subprocess.STDOUT, timeout=a.timeout_min * 60)
        print(f"{name}: exit {r.returncode}, {time.time() - t0:.0f} s, status {status(out)}", flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
