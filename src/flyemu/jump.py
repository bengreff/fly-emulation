"""B15 (session 10): the jump muscle (tergotrochanteral muscle, TTM).

TTMn spikes drive a fast twitch of the TTM on each middle leg, applied as a
torque on the coxa-trochanter joint in the depression (extension) direction
given by the measured leg calibration (the same sign the legacy MN map uses for
TTMn). It bypasses the +-30 uN*mm actuator cap, which is sized for ordinary leg
muscles and cannot produce a jump. The TTM is biarticular (it also crosses the
thorax-coxa joint); a single-joint torque is an approximation (as in
neuromuscular.py).

    torque(t) = T_peak * sum over spikes of twitch(t - t_spike), capped at T_peak
    twitch: difference of exponentials, rise tau_r, decay tau_d, peak 1

Parameters (bounded unknowns, parameters.csv b15_*): T_peak, tau_r, tau_d.
Anchors (leads, not read here): jump myofibril tension 19.8 +- 10.5 mN/mm^2;
take-off within a few ms of GF activation (Card & Dickinson 2008; Zumstein et
al. 2004 JEB). Applied through a Body passive hook as an increment on
qfrc_applied (its previous share removed unless an earlier hook rewrote the
DOF this step), so it composes with the other hooks.
"""
from __future__ import annotations

import mujoco as mj
import numpy as np


class TTM:
    def __init__(self, body, conn, cal, t_peak: float, tau_r_ms: float, tau_d_ms: float, dt_ms: float):
        from .neuromuscular import resolve_sign
        m = body.sim.mj_model
        t = conn.neurons.type.fillna("").to_numpy().astype(str)
        inst = conn.neurons.instance.fillna("").to_numpy().astype(str)
        self.dofs, self.sign, self.cells = [], [], []
        for leg, suf in (("lm", "_L"), ("rm", "_R")):
            r = resolve_sign(cal, leg, "CTr", "depression")
            if r is None:
                continue
            j = mj.mj_name2id(m, mj.mjtObj.mjOBJ_JOINT, f"{body.fly.name}/{r[0].removesuffix('-motor')}")
            if j < 0:
                raise ValueError(f"TTM joint {r[0]} not in the body")
            self.dofs.append(m.jnt_dofadr[j]); self.sign.append(float(r[1]))
            self.cells.append(np.flatnonzero((t == "TTMn") & np.char.endswith(inst, suf)))
        self.dofs, self.sign = np.array(self.dofs), np.array(self.sign)
        self.t_peak = t_peak
        self.dr, self.dd = np.exp(-dt_ms / tau_r_ms), np.exp(-dt_ms / tau_d_ms)
        # normalise the difference of exponentials to a unit peak
        tp = tau_r_ms * tau_d_ms / (tau_d_ms - tau_r_ms) * np.log(tau_d_ms / tau_r_ms)
        self.norm = 1.0 / (np.exp(-tp / tau_d_ms) - np.exp(-tp / tau_r_ms))
        self.a = np.zeros(len(self.dofs)); self.b = np.zeros(len(self.dofs))
        self.last = np.zeros(len(self.dofs))
        self.written = None

    def spikes(self, spiked: np.ndarray) -> None:
        self.a *= self.dd; self.b *= self.dr
        if spiked.size:
            for k, c in enumerate(self.cells):
                n = np.isin(c, spiked).sum()
                self.a[k] += n; self.b[k] += n

    def torque(self) -> np.ndarray:
        return self.sign * np.minimum(self.t_peak * self.norm * (self.a - self.b), self.t_peak)

    def __call__(self, d) -> None:
        tq = self.torque()
        cur = d.qfrc_applied[self.dofs].copy()
        # if an earlier hook rewrote these DOFs this step, our old share is gone
        base = cur - self.last if (self.written is not None and np.array_equal(cur, self.written)) else cur
        d.qfrc_applied[self.dofs] = base + tq
        self.last, self.written = tq, d.qfrc_applied[self.dofs].copy()
