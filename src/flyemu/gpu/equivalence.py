"""Equivalence harness: BatchedNetwork members vs separate lif.Network runs.

Used by tests/test_gpu_batched.py (toy network, CPU backend) and
scripts/gpu_bench.py equiv (whole CNS, GPU).
"""
from __future__ import annotations

import time

import numpy as np

from .. import lif


def build_brain(overrides: dict | None = None, profile: str | None = None,
                min_synapses: int | None = None, timestep_ms: float = 0.1):
    """Brain-only reference (no body): registry, connectome, params, kick mV."""
    from .. import connectome, profiles
    from ..registry import Policy, Registry
    reg = Registry(Policy.MINIMAL)
    reg.overrides.update(overrides or {})
    prof = profiles.apply(reg, profile or profiles.WORKING_PROFILE)
    conn = connectome.build(reg, min_synapses=min_synapses or profiles.WORKING_MIN_SYNAPSES)
    params = lif.default_params(reg, conn, timestep_ms=timestep_ms)
    return reg, conn, params, prof["kick_mv"]


def cpu_run(net: lif.Network, T: int, external_mv=None, kicks=None):
    """Reference: T steps of lif.Network.step. kicks = (idx, mask (T, k), mv)."""
    out, t0 = [], time.time()
    for s in range(T):
        kick = None
        if kicks is not None:
            idx, mask, mv = kicks
            kick = (np.asarray(idx)[mask[s]], mv)
        out.append(net.step(external_mv=external_mv, kick=kick).copy())
    return out, time.time() - t0


def unpack(raster: np.ndarray, n: int, member: int) -> list[np.ndarray]:
    """(T, ceil(n/8), B) packed -> per-step spike index arrays of one member."""
    r = np.unpackbits(raster[:, :, member], axis=1, count=n)
    return [np.flatnonzero(row) for row in r]


def compare(cpu: list[np.ndarray], gpu: list[np.ndarray], n: int, dt_ms: float) -> dict:
    """Exact raster match, first divergence, and per-neuron rate agreement."""
    T = len(cpu)
    first, n_bad = None, 0
    for s in range(T):
        a, b = np.sort(cpu[s]), np.sort(gpu[s])
        if a.size != b.size or not np.array_equal(a, b):
            n_bad += 1
            if first is None:
                first = (s, np.setdiff1d(a, b).tolist()[:10], np.setdiff1d(b, a).tolist()[:10])
    ca = np.bincount(np.concatenate(cpu) if cpu else [], minlength=n)
    cb = np.bincount(np.concatenate(gpu) if gpu else [], minlength=n)
    sec = T * dt_ms / 1000.0
    ra, rb = ca / sec, cb / sec
    act = (ca + cb) > 0
    corr = float(np.corrcoef(ra[act], rb[act])[0, 1]) if act.sum() > 2 else float("nan")
    return {
        "steps": T, "exact": first is None, "mismatch_steps": n_bad,
        "first_divergence_step": None if first is None else first[0],
        "first_divergence_cpu_only": None if first is None else first[1],
        "first_divergence_gpu_only": None if first is None else first[2],
        "spikes_cpu": int(ca.sum()), "spikes_gpu": int(cb.sum()),
        "active_cells": int(act.sum()), "rate_corr_active": corr,
        "max_abs_rate_diff_hz": float(np.abs(ra - rb).max()),
        "cells_rate_differs": int((ca != cb).sum()),
    }
