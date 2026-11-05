"""Closed loop: the MetaWorm body (driver pipe mode) and a brain, exchanging through docs/worm/INTERFACE.md.

Body(out) starts third_party/metaworm/driver/run_body in pipe mode and speaks the interface: step(BrainToBody) ->
BodyToBrain. One exchange = one published physics step (1/240 s) by default. The brain's internal step is 0.5 ms,
so the brain advances to the 0.5 ms grid point nearest the body's time: steps of 4.0, 4.5, 4.0 ms, repeating, and
the two clocks never differ by more than 0.25 ms (derived). The body keeps the published dt; no published constant
changes.

Order within an exchange (lockstep, both sides hold their input over the interval): the body gets the command
from the end of the previous interval and the brain gets the observation from its start; the two run at the same
time in separate processes. The command therefore reaches the muscles one exchange (about 4 ms) after the brain
computes it; that lag is the loop's, not a filter (INTERFACE.md: the body adds no delay of its own).

Observation (INTERFACE.md body side): K = 49 midline samples; curvature from 24 material slices (slice centroids),
signed dorsal-concave positive, interpolated to the 49 samples, per mm with L = mm_per_body_length (1.0 mm,
measured); curvature rate by backward difference over the exchange; contact, nose force and tap 0 (no objects);
head / tail from the chemotaxis scene (scene.py, MB11), over the default plate of interface.HEAD_CHANNELS.

95 -> 96 muscles: segment j of MetaWorm's MDR / MVR / MDL / MVL string is Cook muscle j+1 of dBWMR / vBWMR / dBWML /
vBWML; MVL segment 24 copies vBWML23 (guessed; vBWML24 does not exist). Activation goes 1:1 into the published
muscle input (inferred).
"""
from __future__ import annotations

import json
import os
import struct
import subprocess
import time
from pathlib import Path

import numpy as np

from wormemu.interface import BWM_NAMES, HEAD_CHANNELS, TAIL_CHANNELS, BodyToBrain, BrainToBody
from wormemu.body import metaworm as mw
from wormemu.body.scene import ChemotaxisScene

K = 49
N_SLICES = 24
BRAIN_DT_MS = 0.5


def muscle_map(names: list[str]) -> np.ndarray:
    """Index into BWM_NAMES for each of the 96 MetaWorm activations (driver order: strings in `names`, 24 each)."""
    pre = {"MDR": "dBWMR", "MVR": "vBWMR", "MDL": "dBWML", "MVL": "vBWML"}
    idx = []
    for m in names:
        for j in range(mw.N_SEG):
            k = min(j + 1, 23) if m == "MVL" else j + 1
            idx.append(BWM_NAMES.index(f"{pre[m]}{k}"))
    return np.array(idx)


class Body:
    def __init__(self, out: str | Path, scene: ChemotaxisScene | None = None, frame_every: int = 8,
                 solver_exit: str = "published"):
        if not mw.DRIVER.exists():
            subprocess.run([str(mw.ROOT / "driver" / "build.sh")], check=True)
        self.out = str(Path(out).resolve())
        self.scene = scene or ChemotaxisScene()
        self.frame_every = frame_every
        c_r, c_w = os.pipe()  # commands: us -> driver
        s_r, s_w = os.pipe()  # state: driver -> us
        self._log = open(self.out + ".log", "w")
        self.proc = subprocess.Popen([str(mw.DRIVER), "--mode", "pipe", "--fd_in", str(c_r), "--fd_out", str(s_w),
                                      "--out", self.out, "--solver_exit", solver_exit], cwd=mw.ROOT, pass_fds=(c_r, s_w),
                                     stdout=self._log, stderr=subprocess.STDOUT)
        os.close(c_r)
        os.close(s_w)
        self._w = os.fdopen(c_w, "wb", buffering=0)
        self._r = os.fdopen(s_r, "rb", buffering=0)
        nv, self.n_act = struct.unpack("ii", self._read(8))
        self.dt_s = struct.unpack("d", self._read(8))[0]
        self.nv = nv
        self.X_rest = self._read_x()
        self.meta = json.load(open(self.out + ".json"))
        self.map = muscle_map(self.meta["muscles"])
        self.frame = mw.Frame(self.meta, self.X_rest, n_slices=N_SLICES)
        self.mm_per_unit = self.scene.mm_per_unit(self.X_rest)
        self.X = self.X_rest
        self.n_steps = 0
        self._kappa_prev = None
        self._pending = False
        self.obs = self.observe(dt_ms=None)

    def _read(self, n: int) -> bytes:
        buf = b""
        while len(buf) < n:
            chunk = self._r.read(n - len(buf))
            if not chunk:
                raise RuntimeError(f"body driver closed the pipe; see {self.out}.log")
            buf += chunk
        return buf

    def _read_x(self) -> np.ndarray:
        return np.frombuffer(self._read(8 * 3 * self.nv), np.float64).reshape(self.nv, 3).copy()

    @property
    def t_ms(self) -> float:
        return self.n_steps * self.dt_s * 1000.0

    def activations96(self, cmd) -> np.ndarray:
        if isinstance(cmd, BrainToBody):
            return np.asarray(cmd.muscle_activation, float)[self.map]
        a = np.asarray(cmd, float)
        if a.shape == (95,):
            return a[self.map]
        assert a.shape == (self.n_act,), a.shape
        return a

    def send(self, cmd, n_steps: int = 1, dump: bool | None = None):
        """Start n_steps physics steps with the command held; returns at once (the driver runs in parallel)."""
        assert not self._pending
        if dump is None:
            dump = (self.n_steps + n_steps) % self.frame_every == 0
        a = self.activations96(cmd)
        self._w.write(struct.pack("ii", n_steps, int(dump)) + a.astype(np.float64).tobytes())
        self._pending = n_steps

    def recv(self) -> BodyToBrain:
        n = self._pending
        self.X = self._read_x()
        self.n_steps += n
        self._pending = False
        self.obs = self.observe(dt_ms=n * self.dt_s * 1000.0)
        return self.obs

    def step(self, cmd, n_steps: int = 1) -> BodyToBrain:
        self.send(cmd, n_steps)
        return self.recv()

    def observe(self, dt_ms: float | None) -> BodyToBrain:
        s_int, kL = self.frame.curvature(self.X[None])
        s = np.linspace(0.0, 1.0, K)
        L_mm = self.scene.params["mm_per_body_length"]
        kappa = np.interp(s, s_int, kL[0]) / L_mm
        rate = np.zeros(K) if (dt_ms is None or self._kappa_prev is None) else (kappa - self._kappa_prev) / dt_ms
        self._kappa_prev = kappa
        h, t = self.scene.sample(self.X, self.X_rest)
        return BodyToBrain(t_ms=self.t_ms, s=s, curvature_per_mm=kappa, curvature_rate_per_mm_ms=rate,
                           contact_force_uN=np.zeros(K), nose_force_uN=0.0, muscle_strain=None,
                           head={**HEAD_CHANNELS, **h}, tail={**TAIL_CHANNELS, **t}, tap=0.0)

    def close(self) -> dict:
        if self._pending:
            self.recv()
        self._w.write(struct.pack("ii", 0, 0))
        self._w.close()
        self.proc.wait(timeout=60)
        self._r.close()
        self._log.close()
        return json.load(open(self.out + ".json"))


def brain_dt_schedule(n_steps: int, dt_body_ms: float) -> np.ndarray:
    """Brain step per exchange so the brain sits on the 0.5 ms grid point nearest the body's time."""
    t = np.round(np.arange(n_steps + 1) * dt_body_ms / BRAIN_DT_MS) * BRAIN_DT_MS
    return np.diff(t)


def run(brain, body: Body, seconds: float, record_every: int | None = None, log_every_s: float = 1.0) -> dict:
    """Closed loop for `seconds`. `brain` has reset() -> BrainToBody and step(obs, dt_ms) -> BrainToBody (brain.py
    or a stand-in). Records the cells' v_mV at the body's frames (every frame_every physics steps) into
    out.neural.f32 [n_frames, n_cells] (frame 0 = reset), and adds the run details to out.json."""
    n = int(round(seconds / body.dt_s))
    every = record_every or body.frame_every
    dts = brain_dt_schedule(n, body.dt_s * 1000.0)
    cmd = brain.reset()
    obs = body.obs
    names = list(getattr(brain, "cell_names", []))
    neural = open(body.out + ".neural.f32", "wb")
    if cmd.v_mV is not None:
        neural.write(np.asarray(cmd.v_mV, np.float32).tobytes())
    act_max = 0.0
    t0 = time.time()
    t_brain = 0.0
    next_log = log_every_s
    for i in range(n):
        body.send(cmd, 1, dump=(i + 1) % every == 0)
        cmd = brain.step(obs, dt_ms=float(dts[i]))
        t_brain += dts[i]
        obs = body.recv()
        act_max = max(act_max, float(np.max(cmd.muscle_activation)))
        if (i + 1) % every == 0 and cmd.v_mV is not None:
            neural.write(np.asarray(cmd.v_mV, np.float32).tobytes())
        if obs.t_ms / 1000.0 >= next_log:
            print(f"  t {obs.t_ms / 1000:.2f} s  wall {time.time() - t0:.1f} s  max act {act_max:.3f}  "
                  f"max |kappa| {np.abs(obs.curvature_per_mm).max():.2f} /mm", flush=True)
            next_log += log_every_s
    neural.close()
    wall = time.time() - t0
    meta = body.close()
    meta.update({"mode": "closed_loop", "brain": type(brain).__name__, "seconds": n * body.dt_s,
                 "frame_dt": body.dt_s * every, "loop_wall_s": wall, "exchange_ms": body.dt_s * 1000.0,
                 "brain_dt_ms_pattern": [float(x) for x in dts[:6]], "brain_t_end_ms": t_brain,
                 "cells": names, "max_activation": act_max, "scene": {"field": body.scene.field,
                 "target": body.scene.target, "channel": body.scene.channel, "params": body.scene.params}})
    json.dump(meta, open(body.out + ".json", "w"))
    return meta


class WaveStandIn:
    """Stand-in brain, open loop: the driver's `wave` mode (same formula), for checking the pipe against it."""

    def __init__(self, names: list[str], f=1.76, lam=1.54, amp=0.03, control_dt_s=1 / 30):
        self.names, self.f, self.lam, self.amp, self.cdt = names, f, lam, amp, control_dt_s
        self.t = 0.0

    def command(self, t: float) -> np.ndarray:
        a = np.zeros(4 * mw.N_SEG)
        ramp = min(1.0, t * self.f)
        for mi, m in enumerate(self.names):
            sgn = 1.0 if m.startswith("MD") else -1.0
            s = (np.arange(mw.N_SEG) + 0.5) / mw.N_SEG
            ph = 2 * np.pi * (self.f * t - s / self.lam)
            a[mi * mw.N_SEG:(mi + 1) * mw.N_SEG] = ramp * self.amp * 0.5 * (1 + sgn * np.sin(ph))
        return a


class ReflexStandIn:
    """Stand-in brain, closed loop (guessed, for testing the loop only, not a model of the worm): a head
    oscillator drives the first muscle pair, and every other muscle follows the curvature a fixed distance ahead
    of it (a proprioceptive chain in the spirit of Wen et al. 2012 Neuron 76:750). a_dorsal = amp * sigmoid(g *
    kappa(s - ds)), ventral the mirror. Returns BrainToBody so it exercises the 95-muscle path."""

    def __init__(self, f=0.5, amp=0.5, gain_mm=2.0, ds=0.08):
        from wormemu.interface import ENTERIC_MUSCLES, PHARYNX_MUSCLES, SEX_MUSCLES, muscle_index_along
        self.f, self.amp, self.g, self.ds = f, amp, gain_mm, ds
        self.s_m = np.array([(muscle_index_along(n) - 0.5) / 24 for n in BWM_NAMES])
        self.dorsal = np.array([n.startswith("d") for n in BWM_NAMES])
        self.extra = (len(PHARYNX_MUSCLES), len(ENTERIC_MUSCLES), len(SEX_MUSCLES))
        self.t = 0.0
        self.cell_names: list[str] = []

    def _out(self, act):
        p, e, x = self.extra
        return BrainToBody(t_ms=self.t, muscle_activation=act, pharynx_activation=np.zeros(p),
                           enteric_activation=np.zeros(e), sex_muscle_activation=np.zeros(x))

    def reset(self):
        self.t = 0.0
        return self._out(np.zeros(95))

    def step(self, obs: BodyToBrain, dt_ms: float):
        self.t += dt_ms
        k = np.interp(np.clip(self.s_m - self.ds, 0, 1), obs.s, obs.curvature_per_mm)
        drive = 1.0 / (1.0 + np.exp(-self.g * k))
        head = self.s_m < 1 / 24
        osc = 0.5 * (1 + np.sin(2 * np.pi * self.f * self.t / 1000.0))
        drive[head] = osc
        act = np.where(self.dorsal, drive, 1.0 - drive) * self.amp
        return self._out(act)
