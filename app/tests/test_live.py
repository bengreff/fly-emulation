"""Live sessions: the command file reader and the session's effect on the protocol
and the Stimulator (no model is built; app/server/live.py)."""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pytest

APP = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(APP / "server"))
sys.path.insert(0, str(APP / "tests"))
import live  # noqa: E402
import protocol as proto  # noqa: E402
from test_protocols import NEURONS, doc  # noqa: E402


class Writer:
    def __init__(self):
        self.notes = []

    def note(self, **f):
        self.notes.append(json.loads(json.dumps(f)))


def session(tmp_path, **kw):
    pr = proto.resolve(doc(duration_ms=1000, **kw), NEURONS, 0.1)
    stim = proto.Stimulator(pr["resolved"], len(NEURONS), 12, 68.75)
    cmd = tmp_path / "c.jsonl"
    cmd.write_text("")
    return live.Session(cmd, Writer(), pr, stim, NEURONS, 0.1), pr, stim, cmd


def send(path, *cmds, partial=""):
    with path.open("a") as f:
        for c in cmds:
            f.write(json.dumps(c) + "\n")
        f.write(partial)


def test_commands_read_whole_lines_once(tmp_path):
    p = tmp_path / "c.jsonl"
    c = live.Commands(p)
    assert c.read() == []                                    # no file yet
    send(p, {"cmd": "pause"}, partial='{"cmd": "res')
    assert c.read() == [{"cmd": "pause"}]
    send(p, partial='ume"}\nnot json\n')
    assert c.read() == [{"cmd": "resume"}, {"cmd": "invalid", "raw": "not json"}]
    assert c.read() == []


def test_stim_applies_now_and_enters_the_protocol(tmp_path):
    s, pr, stim, cmd = session(tmp_path)
    send(cmd, {"cmd": "stim", "event": {"effector": "current", "target": {"type": "MDN"}, "dur_ms": 5, "mv": 7,
                                        "t_ms": 999}})
    assert s.poll(250)
    e, r = pr["events"][-1], pr["resolved"]["events"][-1]
    assert e["t_ms"] == 25.0 and e["live"] and (r["on_step"], r["off_step"]) == (250, 300)
    assert stim.drive(249) is None and stim.drive(250)[[0, 1]].tolist() == [7, 7] and stim.drive(300) is None
    # the final protocol, resolved afresh (as a replay does), gives the same drive
    again = proto.Stimulator(proto.resolve({k: v for k, v in pr.items() if k != "resolved"}, NEURONS, 0.1)["resolved"],
                             len(NEURONS), 12, 68.75)
    assert all(np.array_equal(again.drive(k) if again.drive(k) is not None else [], stim.drive(k) if stim.drive(k)
                              is not None else []) for k in range(0, 400, 7))
    assert s.state["log"][-1]["ok"] and "applied at 25 ms to 2 cells" in s.state["log"][-1]["result"]


def test_live_kicks_replay_identically(tmp_path):
    s, pr, stim, cmd = session(tmp_path, events=[
        {"effector": "kick", "target": {"type": "LB3b"}, "t_ms": 0, "dur_ms": 100, "rate_hz": 300}])
    got = []
    for k in range(1000):
        if k == 400:
            send(cmd, {"cmd": "stim", "event": {"effector": "kick", "target": {"type": "MDN"}, "dur_ms": 30,
                                                "rate_hz": 500}})
        if k % 100 == 0:
            s.poll(k)
        x = stim.kick(k, 0.1)
        got.append(x[0].tolist() if x else [])
    again = proto.Stimulator(proto.resolve({k: v for k, v in pr.items() if k != "resolved"}, NEURONS, 0.1)["resolved"],
                             len(NEURONS), 12, 68.75)
    rep = [(lambda x: x[0].tolist() if x else [])(again.kick(k, 0.1)) for k in range(1000)]
    assert rep == got and any(got[400:700])


def test_refusals_are_logged_not_applied(tmp_path):
    s, pr, stim, cmd = session(tmp_path)
    send(cmd, {"cmd": "stim", "event": {"effector": "current", "target": {"type": "DNp01"}, "dur_ms": 5}},
         {"cmd": "stim", "event": {"effector": "current", "target": {"type": "nothing"}, "dur_ms": 5}},
         {"cmd": "stim", "event": {"effector": "TNT", "target": {"type": "MDN"}, "dur_ms": 5}},
         {"cmd": "fly"})
    assert s.poll(0)
    assert pr["events"] == [] and pr["resolved"]["events"] == [] and stim.drive(0) is None
    log = s.state["log"]
    assert [x["ok"] for x in log] == [False] * 4
    assert "held-out gf_dlm" in log[0]["result"] and "matches no neuron" in log[1]["result"]


def test_pause_resume_stop(tmp_path, monkeypatch):
    s, pr, stim, cmd = session(tmp_path)
    slept = []
    monkeypatch.setattr(live.time, "sleep", lambda dt: (slept.append(dt), len(slept) == 3 and send(cmd, {"cmd": "resume"})))
    send(cmd, {"cmd": "pause"})
    assert s.poll(10) and len(slept) == 3 and not s.paused and s.state["state"] == "running"
    send(cmd, {"cmd": "stop"}, {"cmd": "stim", "event": {"effector": "current", "target": {"type": "MDN"}, "dur_ms": 5}})
    assert not s.poll(20) and s.stopped == "stopped by the user"
    assert pr["events"] == []                                # nothing after a stop is applied


def test_pause_limit_stops_the_session(tmp_path, monkeypatch):
    s, *_ , cmd = session(tmp_path)
    monkeypatch.setattr(live, "MAX_PAUSE_S", 1.0)
    monkeypatch.setattr(live.time, "sleep", lambda dt: None)
    send(cmd, {"cmd": "pause"})
    assert not s.poll(0) and "paused for" in s.stopped and s.state["state"] == "stopped"


def test_brain_only_session_refuses_world(tmp_path):
    s, pr, stim, cmd = session(tmp_path, config={"seed": 12, "preparation": "brain_only"})
    send(cmd, {"cmd": "stim", "event": {"effector": "world", "set": {"light_lux": 5}, "dur_ms": 5}})
    s.poll(0)
    assert not s.state["log"][-1]["ok"] and "brain_only" in s.state["log"][-1]["result"]


@pytest.mark.parametrize("bad", [{"dur_ms": 0}, {"dur_ms": -3}, {}])
def test_event_needs_a_duration(bad):
    with pytest.raises(ValueError, match="dur_ms"):
        proto.resolve_event({"effector": "current", "target": {"type": "MDN"}, "t_ms": 0, **bad}, NEURONS, 0.1)
