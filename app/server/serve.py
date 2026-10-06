"""Local server for Fly Workbench (stdlib only, binds 127.0.0.1).

    python app/server/serve.py [--port 8766] [--runs runs/app] [--open]

Routes:
    /               app/web (the page)
    /data/...       app/data (atlases, body geometry)
    /runs/...       recordings (flyemu-rec/1 directories under --runs)
    /catalog.json   built on each request from the manifests on disk
    /api/sessions   GET: live sessions; POST {"protocol": {...}}: start one (app/server/sessions.py)
    /api/sessions/<id>  POST {"cmd": "pause"|"resume"|"stop"|"stim", "event": {...}}
    /api/check      POST {"protocol": {...}}: resolve against the atlas, run the held-out guard

POSTs must carry the header X-Workbench: 1 and a Host of 127.0.0.1 or localhost
(a page from another site can send neither without the browser asking first).

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

sys.path.insert(0, str(Path(__file__).resolve().parent))
from sessions import Sessions, check  # noqa: E402

APP = Path(__file__).resolve().parents[1]
REPO = APP.parent

TYPES = {".js": "text/javascript; charset=utf-8", ".html": "text/html; charset=utf-8",
         ".json": "application/json; charset=utf-8", ".csv": "text/csv; charset=utf-8",
         ".css": "text/css; charset=utf-8", ".gz": "application/octet-stream",
         ".bin": "application/octet-stream", ".md": "text/plain; charset=utf-8"}


def catalog(runs: Path, prefix: str = "runs", data_prefix: str = "data") -> dict:
    """List recordings, libraries, atlases and bodies found on disk."""
    recs = []
    scores: dict[Path, dict] = {}       # app/tools/score_library.py output, per library folder
    docs: dict[Path, dict] = {}
    libs: dict[Path, dict] = {}         # what the Compare tab sets side by side, per scored folder

    def score_of(run_dir: Path):
        lib = run_dir.parent
        if lib not in scores:
            try:
                doc = json.loads((lib / "scores.json").read_text())
                docs[lib] = doc
                scores[lib] = {s["run"]: s for s in doc.get("scores", [])}
                for g in doc.get("trials", []):     # the same protocol at several seeds
                    for s in g["seeds"]:
                        if f"{g['protocol']}-s{s}" in scores[lib]:
                            scores[lib][f"{g['protocol']}-s{s}"] = {**scores[lib][f"{g['protocol']}-s{s}"], "trials": g}
            except (OSError, json.JSONDecodeError):
                scores[lib] = {}
        return scores[lib].get(run_dir.name)

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
        pr = m.get("protocol") or {}
        recs.append({
            "id": rel, "path": f"{prefix}/{rel}",
            "title": m.get("title") or f"{cfg.get('profile', '?')} seed {cfg.get('seed', '?')}, "
                                       f"{m.get('duration_ms', 0) / 1000:g} s, {cfg.get('body', '?')}",
            "created": m.get("created"), "duration_ms": m.get("duration_ms"),
            "status": m.get("status"), "config": cfg, "flags": flags,
            # what the page needs to pair a stimulated run with its control
            "n_events": len(pr.get("events", [])), "n_genotype": len(pr.get("genotype", [])),
            "control": bool(pr) and not pr.get("events") and not pr.get("genotype"),
            "commit": ((m.get("provenance") or {}).get("git") or {}).get("commit"),
            "expect_status": (pr.get("expect") or {}).get("status"),
            "role": pr.get("role"),
        })
        sc = score_of(man.parent)
        if man.parent.parent in docs:
            lib = man.parent.parent
            recs[-1]["library"] = lib.relative_to(runs).as_posix()
            L = libs.setdefault(lib, {"profiles": set(), "hosts": {}})
            L["profiles"].add(cfg.get("profile") or "?")
            L["hosts"][man.parent.name] = (m.get("provenance") or {}).get("host")
        if sc and sc.get("trials"):
            recs[-1]["trials"] = sc["trials"]
        cr = (sc or {}).get("criterion")
        if cr and cr.get("pass") is not None:
            # scored against a control recorded with the same configuration; a
            # result no larger than the sham's is labelled as noise
            recs[-1]["verdict"] = ("PASS" if cr["pass"] else "FAIL") + (
                ", no spike changed" if sc.get("first_divergence_step") is None
                else " within noise" if cr.get("within_sham") else "")
            if cr.get("sham_values") is not None:     # the scorer's noise floor, every sham
                recs[-1]["sham_values"] = cr["sham_values"]
                recs[-1]["shams_distinct"] = cr.get("n_shams_distinct")
    recs.sort(key=lambda r: (r["status"] != "complete", "legacy" in r["id"], r["id"]))
    libraries = []
    for lib, L in sorted(libs.items()):
        doc = docs[lib]
        if not doc.get("trials"):
            continue
        note = lib / "NOTE.txt"
        rel = lib.relative_to(runs).as_posix()
        libraries.append({
            "id": rel, "path": f"{prefix}/{rel}", "profiles": sorted(L["profiles"]),
            "commits": sorted(set((doc.get("commits") or {}).values()) - {None}), "hosts": L["hosts"],
            "note": note.read_text().strip() if note.exists() else None, "trials": doc["trials"]})
    atlases = []
    for a in sorted((APP / "data" / "atlas").glob("*/atlas.json")):
        info = json.loads(a.read_text())
        atlases.append({"scan": info["scan"], "version": info["version"], "n": info["n"],
                        "path": f"{data_prefix}/atlas/{a.parent.name}"})
    bodies = [{"id": b.parent.name, "path": f"{data_prefix}/body/{b.parent.name}"}
              for b in sorted((APP / "data" / "body").glob("*/geometry.json"))]
    return {"format": "flyemu-catalog/1", "recordings": recs, "libraries": libraries,
            "atlases": atlases, "bodies": bodies,
            # the model's construction tables for the Fidelity tab (app/build/fidelity.py)
            "model": f"{data_prefix}/model/fidelity.json" if (APP / "data" / "model" / "fidelity.json").exists() else None}


class Handler(SimpleHTTPRequestHandler):
    runs: Path = REPO / "runs" / "app"
    sessions: Sessions | None = None

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

    def _json(self, obj, code: int = 200) -> None:
        body = json.dumps(obj).encode()
        self.send_response(code)
        self.send_header("Content-Type", TYPES[".json"])
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        path = urlsplit(self.path).path
        if path == "/catalog.json":
            return self._json(catalog(self.runs))
        if path == "/api/sessions":
            return self._json({"sessions": self.sessions.status(), "active": self.sessions.active()})
        super().do_GET()

    def do_POST(self):
        host = (self.headers.get("Host") or "").rsplit(":", 1)[0]
        if self.headers.get("X-Workbench") != "1" or host not in ("127.0.0.1", "localhost"):
            return self._json({"ok": False, "error": "refused: local page requests only"}, 403)
        n = int(self.headers.get("Content-Length") or 0)
        if not 0 < n <= 1_000_000:
            return self._json({"ok": False, "error": "body missing or over 1 MB"}, 400)
        try:
            body = json.loads(self.rfile.read(n))
        except json.JSONDecodeError as exc:
            return self._json({"ok": False, "error": f"not JSON: {exc}"}, 400)
        path = urlsplit(self.path).path
        if path == "/api/check":
            return self._json(check(body.get("protocol") or {}))
        if path == "/api/sessions":
            r = self.sessions.start(body.get("protocol") or {})
            return self._json(r, 200 if r["ok"] else 409)
        if path.startswith("/api/sessions/"):
            r = self.sessions.command(path.rsplit("/", 1)[1], body)
            return self._json(r, 200 if r["ok"] else 409)
        return self._json({"ok": False, "error": "no such route"}, 404)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--port", type=int, default=8766)
    ap.add_argument("--open", action="store_true", help="open the page in the default browser")
    ap.add_argument("--runs", type=Path, default=REPO / "runs" / "app")
    a = ap.parse_args()
    Handler.runs = a.runs.resolve()
    Handler.sessions = Sessions(Handler.runs)
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
    finally:
        Handler.sessions.shutdown()      # a live session ends with the server


if __name__ == "__main__":
    main()
