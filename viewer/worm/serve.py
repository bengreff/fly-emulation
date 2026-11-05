"""Serve the worm viewer on 127.0.0.1 and run new body drives on request.

    uv run python viewer/worm/serve.py            # then open http://127.0.0.1:8781/viewer/worm/
    (first time: third_party/metaworm/driver/build.sh; scripts/worm/metaworm_tests.py;
     scripts/worm/build_viewer_data.py)

Serves the repo root read-only (localhost only). POST /api/run {mode: wave|key, f, lam, amp, key, seconds} runs the
ported MetaWorm body once (about 1.5 s wall per simulated second, one at a time) and adds it to the run list.
"""
from __future__ import annotations

import hashlib
import json
import sys
import threading
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "src"))
sys.path.insert(0, str(REPO / "scripts" / "worm"))
from wormemu.body import metaworm as mw  # noqa: E402
import build_viewer_data as bvd  # noqa: E402

PORT = int(sys.argv[1]) if len(sys.argv) > 1 else 8781
LOCK = threading.Lock()
KEYS = sorted(p.name for p in (mw.ROOT / "data").glob("worm_givenkey*.csv"))


class Handler(SimpleHTTPRequestHandler):
    def end_headers(self):
        self.send_header("Cache-Control", "no-store")
        super().end_headers()

    def log_message(self, fmt, *args):
        pass

    def _json(self, code: int, obj):
        body = json.dumps(obj).encode()
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        if self.path == "/api/keys":
            return self._json(200, {"keys": KEYS})
        return super().do_GET()

    def do_POST(self):
        if self.path != "/api/run":
            return self._json(404, {"error": "unknown endpoint"})
        try:
            req = json.loads(self.rfile.read(int(self.headers.get("Content-Length", 0))) or b"{}")
            mode = req.get("mode", "wave")
            if mode not in ("wave", "key", "dead"):
                raise ValueError("mode must be wave, key or dead")
            seconds = min(max(float(req.get("seconds", 10)), 1.0), 10.0)
            f = min(max(float(req.get("f", 1.76)), 0.1), 5.0)
            lam = min(max(float(req.get("lam", 1.54)), 0.3), 5.0)
            amp = min(max(float(req.get("amp", 0.157)), 0.0), 1.0)
            key = req.get("key") if mode == "key" else None
            if key is not None and key not in KEYS:
                raise ValueError(f"key must be one of {KEYS}")
        except (ValueError, TypeError) as e:
            return self._json(400, {"error": str(e)})
        tag = hashlib.sha1(json.dumps([mode, seconds, f, lam, amp, key]).encode()).hexdigest()[:8]
        rid = f"user_{tag}"
        if not LOCK.acquire(blocking=False):
            return self._json(409, {"error": "another run is in progress"})
        try:
            mw.run(bvd.SRC / rid, mode=mode, seconds=seconds, key=key, f=f, lam=lam, amp=amp)
            if mode == "wave":
                title = f"Wave f {f:g} Hz, lambda {lam:g} L, amp {amp:g}"
            elif mode == "key":
                title = f"Key {key}"
            else:
                title = "Dead worm"
            entry = bvd.add_runs([rid], {rid: (title, "run from the viewer (prescribed drive, no brain)")})[0]
            entry["tests"] = {}
            return self._json(200, entry)
        except Exception as e:  # report driver failures to the page
            return self._json(500, {"error": repr(e)})
        finally:
            LOCK.release()


if __name__ == "__main__":
    srv = ThreadingHTTPServer(("127.0.0.1", PORT), partial(Handler, directory=str(REPO)))
    print(f"worm viewer: http://127.0.0.1:{PORT}/viewer/worm/", flush=True)
    srv.serve_forever()
