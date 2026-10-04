"""Live session: commands a running recorder takes from a file.

The server appends one JSON object per line to the commands file; the recorder
reads new lines between steps (every `poll_ms` of simulated time, and every
quarter second of wall time while paused):

    {"cmd": "pause"}  {"cmd": "resume"}  {"cmd": "stop"}
    {"cmd": "stim", "event": {"effector": "kick", "target": {"type": "MN9"},
                              "dur_ms": 200, "rate_hz": 100}}

A stim starts at the step the recorder reads it; its t_ms is set to that time.
It is resolved and checked as a protocol event would be, refused if it touches
a held-out item (a live session cannot spend held-out data), and appended to the
recording's protocol, so the finished recording replays from its protocol alone.
Pausing stops the simulation clock, not the model: a paused run continues with
the same state, so pauses leave no trace in the recording. A stop ends the run
at the current step; the recording is complete, with the shorter duration.
"""
from __future__ import annotations

import datetime as dt
import json
import time
from pathlib import Path

import heldout
import protocol as proto

MAX_PAUSE_S = 30 * 60.0        # total paused wall time before the session stops itself


def now() -> str:
    return dt.datetime.now().astimezone().isoformat(timespec="seconds")


class Commands:
    """New lines of the commands file, read incrementally."""

    def __init__(self, path: Path):
        self.path = Path(path)
        self.pos = 0

    def read(self) -> list[dict]:
        try:
            with self.path.open("rb") as f:
                f.seek(self.pos)
                data = f.read()
        except FileNotFoundError:
            return []
        end = data.rfind(b"\n") + 1          # a line still being written waits for the next read
        self.pos += end
        out = []
        for line in data[:end].splitlines():
            try:
                c = json.loads(line)
            except json.JSONDecodeError:
                c = {"cmd": "invalid", "raw": line.decode(errors="replace")[:200]}
            out.append(c if isinstance(c, dict) else {"cmd": "invalid"})
        return out


class Session:
    """State of a live run: applies commands to the protocol and the Stimulator,
    keeps a log in the manifest (`live`)."""

    def __init__(self, path: Path, writer, pr: dict, stim, neurons, ts: float):
        self.cmds = Commands(path)
        self.w, self.pr, self.stim, self.neurons, self.ts = writer, pr, stim, neurons, ts
        self.paused = False
        self.stopped = None           # reason, once stopped
        self.paused_s = 0.0
        self.state = {"commands": str(path), "state": "running", "log": [], "paused_s": 0.0,
                      "max_pause_s": MAX_PAUSE_S}
        writer.note(live=self.state)

    def _log(self, step: int, c: dict, result: str, ok: bool) -> None:
        self.state["log"].append({"time": now(), "t_ms": round(step * self.ts, 3), "cmd": c.get("cmd"),
                                  "ok": ok, "result": result,
                                  **({"event": c["event"]} if "event" in c else {})})

    def poll(self, step: int) -> bool:
        """Apply new commands at `step` (before it is simulated). Blocks while
        paused. Returns False when the run should end here."""
        changed = self._apply(step, self.cmds.read())
        while self.paused and self.stopped is None:
            if changed:
                self._note()
                changed = False
            time.sleep(0.25)
            self.paused_s += 0.25
            if self.paused_s >= MAX_PAUSE_S:
                self.stopped = f"paused for {MAX_PAUSE_S / 60:g} min in total"
                self._log(step, {"cmd": "stop"}, self.stopped, True)
                changed = True
                break
            changed |= self._apply(step, self.cmds.read())
        if changed:
            self._note()
        return self.stopped is None

    def _note(self) -> None:
        self.state["state"] = "stopped" if self.stopped else "paused" if self.paused else "running"
        self.state["paused_s"] = round(self.paused_s, 1)
        self.w.note(live=self.state)

    def _apply(self, step: int, cmds: list[dict]) -> bool:
        for c in cmds:
            kind = c.get("cmd")
            if kind == "pause":
                self.paused = True
                self._log(step, c, "paused", True)
            elif kind == "resume":
                self.paused = False
                self._log(step, c, "resumed", True)
            elif kind == "stop":
                self.stopped = "stopped by the user"
                self._log(step, c, self.stopped, True)
                break
            elif kind == "stim":
                self._stim(step, c)
            else:
                self._log(step, c, f"unknown command {kind!r}", False)
        return bool(cmds)

    def _stim(self, step: int, c: dict) -> None:
        e = dict(c.get("event") or {})
        e["t_ms"] = round(step * self.ts, 6)
        e["live"] = True
        try:
            r = proto.resolve_event(e, self.neurons, self.ts, self.pr["resolved"]["preparation"])
            guard = heldout.check({"resolved": {"genotype": [], "events": [r]},
                                   "config": self.pr["config"]}, self.neurons)
            if guard["items"]:
                raise ValueError("touches held-out " + ", ".join(h["id"] for h in guard["items"])
                                 + "; a live session cannot spend held-out data")
            self.stim.add(r)
        except (ValueError, KeyError, TypeError) as exc:
            self._log(step, c, f"refused: {exc}", False)
            return
        self.pr.setdefault("events", []).append(e)
        self.pr["resolved"]["events"].append(r)
        self._log(step, c, f"applied at {e['t_ms']:g} ms to {r['n']} cells: {r['label']}", True)
