"""The local server's API: request guards, protocol check, session commands
(no session is started here; that builds the model)."""
from __future__ import annotations

import json
import sys
import threading
import urllib.error
import urllib.request
from functools import partial
from http.server import ThreadingHTTPServer
from pathlib import Path

import pytest

APP = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(APP / "server"))
import serve  # noqa: E402
from sessions import ATLAS, Sessions  # noqa: E402

pytestmark = pytest.mark.skipif(not (ATLAS / "atlas.json").exists(), reason="atlas not built")


@pytest.fixture(scope="module")
def server(tmp_path_factory):
    runs = tmp_path_factory.mktemp("runs")
    serve.Handler.runs, serve.Handler.sessions = runs, Sessions(runs)
    srv = ThreadingHTTPServer(("127.0.0.1", 0), partial(serve.Handler, directory=str(APP / "web")))
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    yield f"http://127.0.0.1:{srv.server_address[1]}"
    srv.shutdown()


def call(url, body=None, headers=None):
    h = {"Content-Type": "application/json", **({"X-Workbench": "1"} if headers is None else headers)}
    req = urllib.request.Request(url, data=None if body is None else json.dumps(body).encode(), headers=h)
    try:
        with urllib.request.urlopen(req, timeout=60) as r:
            return r.status, json.loads(r.read())
    except urllib.error.HTTPError as e:
        return e.code, json.loads(e.read())


PROTO = {"format": "flyemu-protocol/1", "title": "t", "config": {"seed": 12}, "duration_ms": 100,
         "events": [{"effector": "kick", "target": {"type": "MN9"}, "t_ms": 10, "dur_ms": 20, "rate_hz": 50}]}


def test_posts_need_the_page_header_and_a_local_host(server):
    assert call(f"{server}/api/check", {"protocol": PROTO}, headers={})[0] == 403
    assert call(f"{server}/api/check", {"protocol": PROTO}, headers={"X-Workbench": "1", "Host": "evil.example"})[0] == 403


def test_check_resolves_on_the_atlas(server):
    code, r = call(f"{server}/api/check", {"protocol": PROTO})
    assert code == 200 and r["ok"] and r["items"][0]["n"] == 2 and r["items"][0]["kind"] == "event"
    code, r = call(f"{server}/api/check", {"protocol": {**PROTO, "events": [
        {"effector": "current", "target": {"type": "DNp01"}, "t_ms": 0, "dur_ms": 1}]}})
    assert not r["ok"] and "gf_dlm" in r["error"]
    code, r = call(f"{server}/api/check", {"protocol": {**PROTO, "config": {"seed": 40}}})
    assert not r["ok"] and "seed 40" in r["error"]
    code, r = call(f"{server}/api/check", {"protocol": {**PROTO, "duration_ms": 0}})
    assert not r["ok"] and "duration_ms" in r["error"]


def test_sessions_list_and_commands_to_unknown(server):
    code, r = call(f"{server}/api/sessions")
    assert code == 200 and r == {"sessions": [], "active": None}
    assert call(f"{server}/api/sessions/nope", {"cmd": "pause"})[0] == 409
    code, r = call(f"{server}/api/sessions/nope", {"cmd": "explode"})
    assert code == 409 and "cmd must be" in r["error"]


def test_start_refuses_what_check_refuses(server):
    code, r = call(f"{server}/api/sessions", {"protocol": {**PROTO, "config": {"seed": 40}}})
    assert code == 409 and "seed 40" in r["error"]
    assert not (serve.Handler.runs / "live").exists()
