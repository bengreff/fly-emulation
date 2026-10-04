"""Local server for Fly Workbench (stdlib only, binds 127.0.0.1).

    python app/server/serve.py [--port 8766] [--runs runs/app] [--open]

Routes:
    /               app/web (the page)
    /data/...       app/data (atlases, body geometry)
    /runs/...       recordings (flyemu-rec/1 directories under --runs)
    /catalog.json   built on each request from the manifests on disk

Files are sent as stored: .gz blobs go out as application/octet-stream with no
Content-Encoding, and the page decompresses them itself. Nothing is cached, so a
run that is still recording can be refreshed.
"""
from __future__ import annotations

import argparse
import json
import mimetypes
import sys
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import unquote, urlsplit

APP = Path(__file__).resolve().parents[1]
REPO = APP.parent

TYPES = {".js": "text/javascript; charset=utf-8", ".html": "text/html; charset=utf-8",
         ".json": "application/json; charset=utf-8", ".csv": "text/csv; charset=utf-8",
         ".css": "text/css; charset=utf-8", ".gz": "application/octet-stream",
         ".bin": "application/octet-stream", ".md": "text/plain; charset=utf-8"}


def catalog(runs: Path, prefix: str = "runs", data_prefix: str = "data") -> dict:
    """List recordings, atlases and bodies found on disk."""
    recs = []
    for man in sorted(runs.glob("**/manifest.json")):
        try:
            m = json.loads(man.read_text())
        except (OSError, json.JSONDecodeError):
            continue
        if m.get("format") != "flyemu-rec/1":
            continue
        rel = man.parent.relative_to(runs).as_posix()
        cfg = m.get("config", {})
        flags = list(m.get("flags", []))
        if m.get("status") != "complete":
            flags.append(m.get("status", "incomplete"))
        if "not validated" in (m.get("profile_status") or ""):
            flags.append("not validated")
        recs.append({
            "id": rel, "path": f"{prefix}/{rel}",
            "title": m.get("title") or f"{cfg.get('profile', '?')} seed {cfg.get('seed', '?')}, "
                                       f"{m.get('duration_ms', 0) / 1000:g} s, {cfg.get('body', '?')}",
            "created": m.get("created"), "duration_ms": m.get("duration_ms"),
            "status": m.get("status"), "config": cfg, "flags": flags,
        })
    recs.sort(key=lambda r: (r["status"] != "complete", "legacy" in r["id"], r["id"]))
    atlases = []
    for a in sorted((APP / "data" / "atlas").glob("*/atlas.json")):
        info = json.loads(a.read_text())
        atlases.append({"scan": info["scan"], "version": info["version"], "n": info["n"],
                        "path": f"{data_prefix}/atlas/{a.parent.name}"})
    bodies = [{"id": b.parent.name, "path": f"{data_prefix}/body/{b.parent.name}"}
              for b in sorted((APP / "data" / "body").glob("*/geometry.json"))]
    return {"format": "flyemu-catalog/1", "recordings": recs, "atlases": atlases, "bodies": bodies}


class Handler(SimpleHTTPRequestHandler):
    runs: Path = REPO / "runs" / "app"

    def log_message(self, fmt, *args):
        if args and str(args[1]) not in ("200", "304"):
            sys.stderr.write("%s %s\n" % (self.address_string(), fmt % args))

    def end_headers(self):
        self.send_header("Cache-Control", "no-store")
        super().end_headers()

    def guess_type(self, path):
        return TYPES.get(Path(path).suffix, mimetypes.guess_type(path)[0] or "application/octet-stream")

    def translate_path(self, path):
        p = unquote(urlsplit(path).path)
        parts = [x for x in p.split("/") if x and x not in (".", "..")]
        if parts[:1] == ["data"]:
            root, rest = APP / "data", parts[1:]
        elif parts[:1] == ["runs"]:
            root, rest = self.runs, parts[1:]
        else:
            root, rest = APP / "web", parts
        return str(root.joinpath(*rest)) if rest else str(root)

    def do_GET(self):
        if urlsplit(self.path).path == "/catalog.json":
            body = json.dumps(catalog(self.runs)).encode()
            self.send_response(200)
            self.send_header("Content-Type", TYPES[".json"])
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
            return
        super().do_GET()


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--port", type=int, default=8766)
    ap.add_argument("--open", action="store_true", help="open the page in the default browser")
    ap.add_argument("--runs", type=Path, default=REPO / "runs" / "app")
    a = ap.parse_args()
    Handler.runs = a.runs.resolve()
    srv = ThreadingHTTPServer(("127.0.0.1", a.port), partial(Handler, directory=str(APP / "web")))
    url = f"http://127.0.0.1:{a.port}/"
    print(f"Fly Workbench at {url}  (recordings from {Handler.runs}; Ctrl-C stops it)", flush=True)
    if a.open:
        import webbrowser
        webbrowser.open(url)
    try:
        srv.serve_forever()
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    main()
