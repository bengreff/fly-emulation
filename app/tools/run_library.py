"""Record the intervention library: every protocol in app/protocols, one after
another, each through the machine's slot limiter. Resumable: complete
recordings are skipped, and an interrupted one is moved aside, not deleted.

    .venv/bin/python app/tools/run_library.py [--only control sugar-grn-kick] [--out runs/app/lib]
        [--seeds 0 1 2] [--profile m9r] [--set 'motor_unit:all|force_per_spike=10'] [--parallel 8]

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
from concurrent.futures import ThreadPoolExecutor
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
    ap.add_argument("--seeds", type=int, nargs="*", help="record each protocol at these seeds "
                    "(output <name>-s<seed>) instead of its own")
    ap.add_argument("--profile", help="record every protocol under this model profile instead of its own")
    ap.add_argument("--set", action="append", default=[], metavar="'entity|property=value'",
                    help="an override added to every run (the recording labels it custom)")
    ap.add_argument("--timeout-min", type=float, default=40.0, help="per run")
    ap.add_argument("--parallel", type=int, default=1, help="runs at once (default 1). For a machine "
                    "without the slot limiter (backhouse): size it to free memory at 2.4 GB per run")
    a = ap.parse_args()
    names = sorted(p.stem for p in a.protocols.glob("*.json"))
    names.sort(key=lambda n: "control" not in n)      # controls first
    if a.only:
        names = [n for n in names if n in a.only]
    jobs = [(n, None) for n in names] if not a.seeds else [(n, s) for s in a.seeds for n in names]
    a.out.mkdir(parents=True, exist_ok=True)

    def record(job):
        proto_name, seed = job
        name = proto_name if seed is None else f"{proto_name}-s{seed}"
        out = a.out / name
        st = status(out)
        if st == "complete":
            print(f"{name}: complete, skipped", flush=True)
            return
        if out.exists():
            aside = out.with_name(f"{name}.incomplete-{dt.datetime.now():%Y%m%d-%H%M%S}")
            out.rename(aside)
            print(f"{name}: previous attempt ({st}) moved to {aside.name}", flush=True)
        cmd = [sys.executable, str(APP / "server" / "record.py"),
               "--protocol", str(a.protocols / f"{proto_name}.json"), "--out", str(out)]
        if seed is not None:
            cmd += ["--seed", str(seed)]
        if a.profile:
            cmd += ["--profile", a.profile]
        for item in a.set:
            cmd += ["--set", item]
        if SLOT.exists():
            cmd = ["python3", str(SLOT), "run", "--label", f"flyapp: library {name}", "--"] + cmd
        t0 = time.time()
        print(f"{name}: recording", flush=True)
        with (a.out / f"{name}.log").open("w") as f:
            try:
                r = subprocess.run(cmd, cwd=REPO, stdout=f, stderr=subprocess.STDOUT, timeout=a.timeout_min * 60)
                code = r.returncode
            except subprocess.TimeoutExpired:
                code = "timeout"
        print(f"{name}: exit {code}, {time.time() - t0:.0f} s, status {status(out)}", flush=True)

    if a.parallel > 1:
        with ThreadPoolExecutor(a.parallel) as ex:
            list(ex.map(record, jobs))
    else:
        for job in jobs:
            record(job)
    return 0


if __name__ == "__main__":
    sys.exit(main())
