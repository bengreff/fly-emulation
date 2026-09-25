"""Replay a recording in MuJoCo's own viewer. No simulation, just playback.

    uv run python scripts/replay_mujoco.py runs/organism-record-3000ms-replay

Keys:
    space       play / pause
    . / ,       speed up / slow down (0.001x to 2x)
    [ / ]       step one frame back / forward while paused
    r           restart
    0           reset speed to 0.1x
    left drag   orbit, right drag pan, scroll zoom   (MuJoCo viewer defaults)

Poses come from the recorded `qpos` and are pushed through `mj_forward`, so
what is drawn is the recorded state, not a re-integration of it. Nothing here
can diverge from the run.
"""
from __future__ import annotations

import argparse
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

import mujoco as mj
import mujoco.viewer
import numpy as np

from flyemu.body import Body

SPEEDS = [0.001, 0.002, 0.005, 0.01, 0.02, 0.05, 0.1, 0.2, 0.5, 1.0, 2.0]


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("recording", help="run directory or path to recording.npz")
    ap.add_argument("--speed", type=float, default=0.1,
                    help="initial playback speed, 1.0 = real time")
    args = ap.parse_args()

    path = Path(args.recording)
    if path.is_dir():
        path = path / "recording.npz"
    data = np.load(path, allow_pickle=False)
    qpos = data["qpos"]
    timestep_ms = float(data["timestep_ms"])
    n_frames = qpos.shape[0]
    print(f"{path.name}: {n_frames:,} frames, {timestep_ms} ms each, "
          f"{n_frames * timestep_ms / 1000:.2f} s of fly")

    body = Body(timestep=timestep_ms / 1000.0, with_camera=True)
    m, d = body.sim.mj_model, body.sim.mj_data
    if qpos.shape[1] != m.nq:
        raise SystemExit(
            f"recording has nq={qpos.shape[1]} but this body has nq={m.nq}; "
            "the body model changed since the recording was made"
        )

    speed_i = min(
        range(len(SPEEDS)), key=lambda i: abs(SPEEDS[i] - args.speed)
    )
    state = {"frame": 0, "playing": True, "speed_i": speed_i}

    def key_callback(keycode: int) -> None:
        k = chr(keycode) if 32 <= keycode < 127 else ""
        if k == " ":
            state["playing"] = not state["playing"]
        elif k == ".":
            state["speed_i"] = min(len(SPEEDS) - 1, state["speed_i"] + 1)
        elif k == ",":
            state["speed_i"] = max(0, state["speed_i"] - 1)
        elif k == "0":
            state["speed_i"] = SPEEDS.index(0.1)
        elif k == "R":
            state["frame"] = 0
        elif k == "]":
            state["frame"] = min(n_frames - 1, state["frame"] + 1)
            state["playing"] = False
        elif k == "[":
            state["frame"] = max(0, state["frame"] - 1)
            state["playing"] = False
        print(f"  t={state['frame'] * timestep_ms:8.1f} ms  "
              f"speed={SPEEDS[state['speed_i']]}x  "
              f"{'playing' if state['playing'] else 'paused'}", flush=True)

    def show(frame: int) -> None:
        d.qpos[:] = qpos[frame]
        d.qvel[:] = 0.0
        mj.mj_forward(m, d)

    print("space play/pause   . faster   , slower   [ ] step   r restart")
    with mujoco.viewer.launch_passive(
        m, d, key_callback=key_callback, show_left_ui=False, show_right_ui=False
    ) as viewer:
        show(0)
        last = time.perf_counter()
        carry = 0.0
        while viewer.is_running():
            now = time.perf_counter()
            elapsed, last = now - last, now
            if state["playing"]:
                carry += elapsed * SPEEDS[state["speed_i"]] * 1000.0
                advance = int(carry / timestep_ms)
                if advance:
                    carry -= advance * timestep_ms
                    state["frame"] = (state["frame"] + advance) % n_frames
            show(state["frame"])
            viewer.sync()
            time.sleep(max(0.0, 1 / 60 - (time.perf_counter() - now)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
