"""Serve the replay visualiser on localhost.

    uv run python scripts/serve_viz.py                 # newest recording
    uv run python scripts/serve_viz.py --list
    uv run python scripts/serve_viz.py --run runs/organism-record-3000ms-replay

Serves `viz/index.html` at the root and the chosen run's `replay_data.js`
alongside it, so the page needs no copy of the data and no build step. Binds to
localhost only.
"""
from __future__ import annotations

import argparse
import functools
import http.server
import socketserver
import sys
import threading
import webbrowser
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
VIZ = REPO / "viz"
RUNS = REPO / "runs"


def recordings() -> list[Path]:
    found = sorted(RUNS.glob("*/replay_data.js"), key=lambda p: p.stat().st_mtime)
    return [p.parent for p in found]


class Handler(http.server.SimpleHTTPRequestHandler):
    run_dir: Path

    def translate_path(self, path: str) -> str:
        clean = path.split("?", 1)[0].split("#", 1)[0].lstrip("/")
        if clean in ("", "index.html"):
            return str(VIZ / "index.html")
        if clean == "replay_data.js":
            return str(self.run_dir / "replay_data.js")
        # Anything else comes from viz/, and only from viz/.
        target = (VIZ / clean).resolve()
        if VIZ.resolve() not in target.parents:
            return str(VIZ / "index.html")
        return str(target)

    def end_headers(self) -> None:
        self.send_header("Cache-Control", "no-store")
        super().end_headers()

    def guess_type(self, path):  # noqa: D102 - stdlib override
        # SimpleHTTPRequestHandler omits the charset, which mangles any
        # non-ASCII text in the page.
        ctype = super().guess_type(path)
        if ctype in ("text/html", "text/javascript", "application/javascript"):
            return ctype + "; charset=utf-8"
        return ctype

    def log_message(self, fmt: str, *args) -> None:
        sys.stderr.write("  %s\n" % (fmt % args))


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--run", help="run directory holding replay_data.js")
    ap.add_argument("--port", type=int, default=8765)
    ap.add_argument("--list", action="store_true")
    ap.add_argument("--no-open", action="store_true")
    args = ap.parse_args()

    found = recordings()
    if args.list:
        if not found:
            print("no recordings; run scripts/record_organism.py first")
        for p in found:
            mb = (p / "replay_data.js").stat().st_size / 1e6
            print(f"  {p.relative_to(REPO)}  ({mb:.1f} MB)")
        return 0

    run_dir = Path(args.run) if args.run else (found[-1] if found else None)
    if run_dir is None:
        print("no recordings found. Run:\n"
              "  uv run python scripts/record_organism.py --duration-ms 3000 \\\n"
              "      --set 'motor_unit:all|force_per_spike=10'")
        return 1
    if not (run_dir / "replay_data.js").exists():
        print(f"{run_dir} has no replay_data.js")
        return 1

    handler = functools.partial(Handler, directory=str(VIZ))
    Handler.run_dir = run_dir.resolve()

    socketserver.TCPServer.allow_reuse_address = True
    with socketserver.TCPServer(("127.0.0.1", args.port), handler) as httpd:
        url = f"http://127.0.0.1:{args.port}/"
        print(f"serving {run_dir.name}")
        print(f"  {url}")
        print("ctrl-c to stop")
        if not args.no_open:
            threading.Timer(0.6, lambda: webbrowser.open(url)).start()
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\nstopped")
    return 0


if __name__ == "__main__":
    sys.exit(main())
