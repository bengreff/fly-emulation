"""Maturation: activity-dependent channel-density tuning before a cell or worm is scored (weki, 8 Nov 2026;
FIT_GENERAL.md, the step between building a member and scoring it). Acts only through the Brain API: a mech-shaped
object appended to `Brain.mechs` returns `g_scale` multipliers on the built densities (brain._apply_g_scale), so no
brain file changes and `Brain.reset()` restores the built cell. Neutral by default: nothing here runs unless called.

Rule ported: O'Leary, Williams, Franci & Marder 2014 Neuron 82:809 (PMC4109293, opened 8 Nov 2026), eq. 3, and the
authors' own code (github.com/marderlab/oleary_et_al_2014 @ 757ffef, int_controller.h and figure3.m, opened):
    tau_m m_i' = r_i (Ca_tgt - Ca),    tau_g g_i' = m_i - g_i,    g_i >= 0 (m_i held while g_i would cross the bound)
Sign: the paper prints the error as [Ca] - Ca_tgt (eq. 3 and Experimental Procedures); the code integrates
Tu1 * (Ca - target) with Tu1 = -tu1, i.e. Ca_tgt - Ca, the only sign that grows conductances out of the nascent state
the paper's Fig. 3 starts from. The code's sign is used (inferred: the print is a sign slip). The code's
tau_m = 10 tau_g is kept; its absolute times are compressed (tau_g = 100 ms for an STG cell), as here.
Leak static: "the leak conductance ... is static but varies between cells" (the paper); here pas and NCA stay built.
Bounds: the code sets g = 0 and restores m whenever g would go negative, which also freezes m if the error then
reverses; here only an update that pushes further past a bound is held (conditional integration), the same wherever
the code's bound never binds ("this condition was not required for the models presented").

Rates: eq. 4, g_i / g_j ~ tau_j / tau_i, says the rates set the steady-state density ratios. The worm has no
measured rates, so the built densities (the CeNGEN expression map times BAAIWorm's fits) are taken as those ratios,
which sets r_i proportional to each channel's built density. With r_i = k g_i_built and every g_i, m_i starting at
the same fraction of built, every regulated channel stays at s x its built density with one s per cell (exactly,
since the m_i are the same integral times r_i and the g_i the same linear filter). So the rule runs as
    tau_m mu' = k (Ca_tgt - Ca),       tau_g s' = mu - s,       s in [s_lo, s_hi] (mu held at a bound)
with no per-channel knob. k and the taus set only the path: the fixed point is Ca = Ca_tgt (derived). k is set per
cell to 1 / |Ca_tgt - Ca_start| so the first error is +-1 (numerical).

Targets (per class, cited, bounded): form "vrest" = the Ca the built cell holds when voltage-clamped at its class's
measured resting potential (vitals.SIGN rest_<class>; derived from a measured value through the cell's own Ca(V)).
Bounded by the generic resting-Ca range of observation.py's obs_ca_rest_nM (20-150 nM, guessed there); a target
outside is reported, not clipped.

Measured precondition (8 Nov, single cells AIYL / AFDL / AWAL as single_cell_sanity builds them): Ca is 50.00 to
50.15 nM from -78 to -35 mV, i.e. within 0.3% of the Ca pool's floor. The sensor's error at rest is that small, so
the fixed point is set by sub-nanomolar differences (see the night file and FIT_GENERAL.md).
"""
from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np

from wormemu.brain_layers import Spec
from wormemu.mech import CHANNEL_NAMES

M = "maturation"
STATIC = ("nca",)                                  # NCA is a voltage-independent leak: static, like pas (O'Leary)
REGULATED = tuple(c for c in CHANNEL_NAMES if c not in STATIC)
OL = "O'Leary, Williams, Franci & Marder 2014 Neuron 82:809 and their code (marderlab/oleary_et_al_2014)"


def _s(sid, units, t, lo, hi, src, label, **kw):
    return Spec(sid, M, units, t, lo, hi, src, label, grain="class", applies_to="matured cells", **kw)


SPECS = [
    _s("mat_tau_g_s", "s", 2.0, 0.5, 20.0, f"{OL}: channel expression low-pass; compressed time (the code uses 100 ms "
       "for an STG cell); the fixed point does not depend on it (derived)", "guessed", role="rule"),
    _s("mat_tau_m_ratio", "1", 10.0, 2.0, 50.0, f"{OL}: figure3.m sets tau_m = 10 tau_g", "measured",
       notes="a published model setting, not a biological measurement", role="rule"),
    _s("mat_settle_s", "s", 2.0, 0.5, 10.0, "initial transient dropped before the integrator starts (FIT2's settle)",
       "guessed", role="rule"),
    _s("mat_s_lo", "1", 0.25, 0.0, 1.0, "lowest density multiplier (slow_signalling homeo_d_lo)", "guessed",
       role="rule"),
    _s("mat_s_hi", "1", 4.0, 1.0, 10.0, "highest density multiplier (slow_signalling homeo_d_hi: channel levels vary "
       "several-fold between types, CeNGEN)", "guessed", role="rule"),
    _s("mat_ca_tgt_lo_uM", "uM", 0.02, 0.0, 0.05, "lowest allowed resting-Ca target (observation.py obs_ca_rest_nM "
       "range)", "guessed", role="rule"),
    _s("mat_ca_tgt_hi_uM", "uM", 0.15, 0.05, 1.0, "highest allowed resting-Ca target (obs_ca_rest_nM range)",
       "guessed", role="rule"),
    _s("mat_conv_window_s", "s", 10.0, 2.0, 60.0, "convergence window", "guessed", role="rule"),
    _s("mat_conv_err", "1", 0.02, 0.001, 0.1, "converged: |mean (Ca - Ca_tgt)| / |Ca_tgt - Ca_start| over the window "
       "below this", "guessed", role="rule"),
    _s("mat_conv_ds", "1", 0.005, 0.0005, 0.05, "converged: s moved less than this (relative) over the window",
       "guessed", role="rule"),
]
P = {s.id: s.template for s in SPECS}


def relax(x, target, tau_ms, dt):
    return target + (x - target) * np.exp(-dt / tau_ms)


def g_scale(n, cells, s, channels=REGULATED):
    """{dens_<c>: per-cell multiplier}: s on the matured cells, 1 elsewhere (the brain ignores channels a cell lacks)"""
    f = np.ones(n)
    f[cells] = s
    return {f"dens_{c}": f.copy() for c in channels}


class Maturation:
    """The rule as a mech: append to brain.mechs, step the brain, read .s. reset() restarts from `start`."""

    def __init__(self, brain, targets: dict, ca_start: dict | None = None, params: dict | None = None,
                 start: float = 1.0, channels=REGULATED):
        self.p = {**P, **(params or {})}
        self.n = len(brain.cell_names)
        self.names = list(targets)
        self.cells = np.array([brain.cell_names.index(c) for c in self.names])
        self.tgt = np.array([float(targets[c]) for c in self.names])
        c0 = np.array([float((ca_start or {}).get(c, np.nan)) for c in self.names])
        self.k = np.where(np.isfinite(c0) & (c0 != self.tgt), 1.0 / np.abs(self.tgt - c0), 1.0 / self.tgt)
        self.start, self.channels = float(start), channels
        self.reset()

    def reset(self):
        self.t = 0.0
        self.s = np.full(len(self.cells), self.start)
        self.mu = self.s.copy()
        self.hist = []                                   # (t_ms, s, ca) every 10 ms after the settle

    def step(self, ctx, dt_ms):
        p = self.p
        self.t += dt_ms
        if self.t > 1000.0 * p["mat_settle_s"]:
            ca = np.asarray(ctx.ca, float)[self.cells]
            dmu = self.k * (self.tgt - ca) * dt_ms / (1000.0 * p["mat_tau_m_ratio"] * p["mat_tau_g_s"])
            tau = 1000.0 * p["mat_tau_g_s"]
            s = relax(self.s, self.mu + dmu, tau, dt_ms)
            hold = ((s > p["mat_s_hi"]) & (dmu > 0)) | ((s < p["mat_s_lo"]) & (dmu < 0))
            self.mu = np.where(hold, self.mu, self.mu + dmu)   # anti-windup (see Bounds in the module docstring)
            self.s = np.clip(relax(self.s, self.mu, tau, dt_ms), p["mat_s_lo"], p["mat_s_hi"])
            if int(round(self.t)) % 10 == 0:
                self.hist.append((self.t, self.s.copy(), ca.copy()))
        return {"g_scale": g_scale(self.n, self.cells, self.s, self.channels)}

    def converged(self):
        p = self.p
        w = [h for h in self.hist if h[0] >= self.t - 1000.0 * p["mat_conv_window_s"]]
        if not w or self.t - w[0][0] < 1000.0 * p["mat_conv_window_s"] - 20.0:
            return np.zeros(len(self.cells), bool)
        s = np.array([h[1] for h in w])
        ca = np.array([h[2] for h in w])
        err = np.abs(ca.mean(axis=0) - self.tgt) * self.k
        ds = (s.max(axis=0) - s.min(axis=0)) / np.maximum(s.mean(axis=0), 1e-9)
        at_bound = (s[-1] <= p["mat_s_lo"]) | (s[-1] >= p["mat_s_hi"])
        return ((err < p["mat_conv_err"]) | at_bound) & (ds < p["mat_conv_ds"])


@dataclass
class Frozen:
    """Fixed multipliers from a finished maturation: survives Brain.reset() (it keeps s)."""
    n: int
    cells: np.ndarray
    s: np.ndarray
    channels: tuple = REGULATED
    g: dict = field(init=False)

    def __post_init__(self):
        self.g = g_scale(self.n, self.cells, self.s, self.channels)

    def reset(self):
        pass

    def step(self, ctx, dt_ms):
        return {"g_scale": self.g}


def clamp_ca(brain, cell: str, v_mV: float, seconds: float = 3.0, avg_s: float = 1.0) -> float:
    """Mean Ca (uM) of `cell` over the last avg_s of a somatic voltage clamp at v_mV from reset (NEURON SEClamp)."""
    i = brain.cell_names.index(cell)
    cl = brain.h.SEClamp(brain.soma[i](0.5))
    cl.dur1, cl.amp1, cl.rs = 1e9, float(v_mV), 0.01
    brain.reset()
    n, na, acc = int(1000 * seconds), int(1000 * avg_s), []
    for k in range(n):
        o = brain.step(None, 1.0)
        if k >= n - na:
            acc.append(float(o.ca_uM[i]))
    del cl
    brain.reset()
    return float(np.mean(acc))


def mature(brain, targets: dict, max_s: float = 300.0, start: float = 1.0, params: dict | None = None,
           check_s: float = 1.0) -> dict:
    """Run the rule on `brain` (from reset, 0 pA) until every matured cell converges or max_s; returns the result and
    leaves a Frozen copy of the multipliers attached (brain.mechs[-1])."""
    pp = {**P, **(params or {})}
    brain.reset()
    i = [brain.cell_names.index(c) for c in targets]
    for _ in range(int(1000 * pp["mat_settle_s"])):  # the built cell's Ca after the settle sets the gain k
        o = brain.step(None, 1.0)
    m = Maturation(brain, targets, ca_start={c: float(o.ca_uM[j]) for c, j in zip(targets, i)}, params=params,
                   start=start)
    brain.mechs.append(m)
    try:
        brain.reset()
        k = 0
        while k < 1000 * max_s:
            brain.step(None, 1.0)
            k += 1
            if k % int(1000 * check_s) == 0 and m.converged().all():
                break
    finally:
        brain.mechs.remove(m)
    conv = m.converged()
    fz = Frozen(m.n, m.cells, m.s.copy(), m.channels)
    brain.mechs.append(fz)
    brain.reset()
    last = m.hist[-1] if m.hist else (m.t, m.s, np.full(len(m.cells), np.nan))
    return {"bio_s": m.t / 1000.0, "cells": m.names, "target_uM": m.tgt.tolist(), "s": m.s.tolist(),
            "ca_end_uM": np.asarray(last[2]).tolist(), "converged": conv.tolist(),
            "at_bound": ((m.s <= m.p["mat_s_lo"]) | (m.s >= m.p["mat_s_hi"])).tolist(),
            "trace": [(h[0] / 1000.0, h[1].tolist(), h[2].tolist()) for h in m.hist[::100]]}
