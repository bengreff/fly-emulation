"""Live sessions and protocol checks for the local server (serve.py).

A session is one record.py process started with --live: it records into
<runs>/live/<id>/ like any run and reads commands from <runs>/live/<id>.commands.jsonl
(app/server/live.py). It goes through the director's slot harness when present,
so it waits for RAM like any heavy job. One session at a time; the server stops
it when the server stops.

/api/check resolves a protocol against the atlas (the same rows and order as the
model's table; instance names are not in the atlas, so `instance` targets resolve
to nothing here) and runs the held-out guard, without building the model.
"""
from __future__ import annotations

import datetime as dt
import gzip
import json
import os
import re
import signal
import subprocess
import sys
import threading
import time
from pathlib import Path

import numpy as np
import pandas as pd

import heldout
import protocol as proto
from recfmt import unpack

APP = Path(__file__).resolve().parents[1]
REPO = APP.parent
SLOT = Path.home() / "director" / "harness" / "slot.py"
ATLAS = APP / "data" / "atlas" / "male-cns-v1.0"
COMMANDS = ("pause", "resume", "stop", "stim")
CHUNK_MS = 50.0          # small chunks so the page sees a live run grow (about every 5 s of wall time)

_table: pd.DataFrame | None = None


def atlas_table() -> pd.DataFrame:
    """The model's neuron table as far as the atlas knows it (rows in model order)."""
    global _table
    if _table is None:
        info = json.loads((ATLAS / "atlas.json").read_text())
        arr = unpack(gzip.open(ATLAS / "neurons.bin.gz").read(), info["arrays"])
        keep = arr["in_model"] > 0
        voc = info["vocab"]
        col = lambda k: np.asarray(voc[k], dtype=object)[arr[k][keep]]   # noqa: E731
        _table = pd.DataFrame({"bodyId": arr["bodyid"][keep], "type": col("type"), "class": col("class"),
                               "superclass": col("superclass"), "somaSide": col("side"), "instance": ""})
    return _table


def check(pr: dict) -> dict:
    """Resolve without building the model: what each event reaches, and the guard."""
    neurons = atlas_table()
    try:
        r = proto.resolve(pr, neurons, 0.1)
    except (ValueError, KeyError, TypeError) as exc:
        return {"ok": False, "error": str(exc)}
    g = heldout.check(r, neurons)
    res = r["resolved"]
    items = [{"kind": "genotype", "label": x["label"], "n": x["n"], "approximation": x.get("approximation")}
             for x in res["genotype"]] + \
            [{"kind": "event", "label": x["label"], "n": x["n"], "t_ms": x.get("t_ms"), "dur_ms": x.get("dur_ms"),
              "approximation": x.get("approximation")} for x in res["events"]]
    problems = [f"touches held-out {h['id']} ({h['what']})" for h in g["items"]]
    if not g["seed_spent"]:
        problems.append(f"seed {g['seed']} may be a fresh held-out seed; use a spent seed "
                        f"(0-13, 17-19) or record it from the command line with --spend-heldout seed")
    return {"ok": not problems, "error": "; ".join(problems) or None, "items": items,
            "watch": len(res["watch"]), "preparation": res["preparation"],
            "note": "resolved against the atlas (time step 0.1 ms); the recorder resolves again on the model's table"}


class Sessions:
    def __init__(self, runs: Path):
        self.dir = Path(runs) / "live"
        self.procs: dict[str, subprocess.Popen] = {}
        self.lock = threading.Lock()

    def _paths(self, sid: str) -> dict[str, Path]:
        return {"out": self.dir / sid, "protocol": self.dir / f"{sid}.protocol.json",
                "commands": self.dir / f"{sid}.commands.jsonl", "log": self.dir / f"{sid}.log"}

    def active(self) -> str | None:
        return next((s for s, p in self.procs.items() if p.poll() is None), None)

    def start(self, pr: dict) -> dict:
        c = check(pr)
        if not c["ok"]:
            return {"ok": False, "error": c["error"]}
        with self.lock:
            if self.active():
                return {"ok": False, "error": f"session {self.active()} is still running; stop it first"}
            slug = re.sub(r"[^a-z0-9]+", "-", (pr.get("title") or "session").lower()).strip("-")[:40]
            sid = f"{dt.datetime.now():%Y%m%d-%H%M%S}-{slug or 'session'}"
            p = self._paths(sid)
            self.dir.mkdir(parents=True, exist_ok=True)
            p["protocol"].write_text(json.dumps(pr, indent=1) + "\n")
            p["commands"].write_text("")
            cmd = [sys.executable, str(APP / "server" / "record.py"), "--protocol", str(p["protocol"]),
                   "--out", str(p["out"]), "--live", str(p["commands"]), "--chunk-ms", str(CHUNK_MS)]
            if SLOT.exists():
                cmd = ["python3", str(SLOT), "run", "--label", f"flyapp: live {sid}", "--"] + cmd
            with p["log"].open("w") as log:
                self.procs[sid] = subprocess.Popen(cmd, cwd=REPO, stdout=log, stderr=subprocess.STDOUT,
                                                   stdin=subprocess.DEVNULL, start_new_session=True)
        return {"ok": True, "id": sid, "path": f"runs/live/{sid}", "check": c}

    def command(self, sid: str, c: dict) -> dict:
        if c.get("cmd") not in COMMANDS:
            return {"ok": False, "error": f"cmd must be one of {COMMANDS}"}
        proc = self.procs.get(sid)
        if proc is None or proc.poll() is not None:
            return {"ok": False, "error": f"session {sid} is not running"}
        line = {"cmd": c["cmd"], "sent": dt.datetime.now().astimezone().isoformat(timespec="seconds")}
        if c["cmd"] == "stim":
            line["event"] = c.get("event") or {}
        with self.lock, self._paths(sid)["commands"].open("a") as f:
            f.write(json.dumps(line) + "\n")
        return {"ok": True}

    def status(self) -> list[dict]:
        out = []
        for sid, proc in sorted(self.procs.items()):
            p = self._paths(sid)
            m = {}
            try:
                m = json.loads((p["out"] / "manifest.json").read_text())
            except (OSError, json.JSONDecodeError):
                pass
            try:
                tail = p["log"].read_text(errors="replace").splitlines()[-6:]
            except OSError:
                tail = []
            out.append({"id": sid, "path": f"runs/live/{sid}", "alive": proc.poll() is None,
                        "returncode": proc.poll(), "status": m.get("status"),
                        "t_ms": m.get("duration_ms", 0), "live": m.get("live"), "log": tail})
        return out

    def shutdown(self, wait_s: float = 20.0) -> None:
        """Stop running sessions: a stop command (the recording ends complete), then
        the process group if it does not exit in time."""
        for sid, proc in self.procs.items():
            if proc.poll() is None:
                self.command(sid, {"cmd": "stop"})
        t0 = time.time()
        for proc in self.procs.values():
            try:
                proc.wait(timeout=max(0.1, wait_s - (time.time() - t0)))
            except subprocess.TimeoutExpired:
                try:
                    os.killpg(proc.pid, signal.SIGTERM)
                except ProcessLookupError:
                    pass
