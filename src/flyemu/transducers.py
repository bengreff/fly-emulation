"""N15 (session 10): adaptation of sensory transducers, per sensory class.

Each sensory neuron's transduced drive d(t) (mV, from sensory.py, vision.py,
olfaction.py, extrasenses.py) passes through a subtractive first-order
adaptation stage before reaching the network:

    tau da/dt = d - a,      out = d - k a

so a sustained stimulus decays to (1 - k) of its onset value with time
constant tau, and steps are transmitted in full (phasic-tonic response). k = 0
is the neutral (m4) setting: out = d exactly. One (k, tau) per sensory circuit
class (data/model/classes.csv). Declared abstraction: one adaptation time
scale per class stands in for the multi-stage, stimulus-dependent adaptation of
real receptors (e.g. photoreceptor light adaptation, ORN two-stage adaptation,
Nagel & Wilson 2011; FeCO/campaniform rate adaptation). Validity: sub-second
to seconds stimulus changes; no gain control of the adaptation itself.
"""
from __future__ import annotations

import numpy as np

SENSORY_CLASSES = ("photoreceptor", "ocellar_photoreceptor", "sensory_olfactory",
                   "sensory_gustatory", "sensory_mechano", "sensory_proprioceptive",
                   "sensory_other")


class Adaptation:
    def __init__(self, idx: np.ndarray, k: np.ndarray, tau_ms: np.ndarray, dt_ms: float):
        self.idx, self.k = idx, k.astype(np.float32)
        self.alpha = (1.0 - np.exp(-dt_ms / tau_ms)).astype(np.float32)
        self.a = None

    def apply(self, drive: np.ndarray) -> np.ndarray:
        d = drive[self.idx]
        if self.a is None:                  # unadapted at t = 0
            self.a = np.zeros(d.shape, np.float32)
        self.a += self.alpha * (d - self.a)
        out = drive.copy()
        out[self.idx] = d - self.k * self.a
        return out


def build(reg, conn, dt_ms: float) -> Adaptation | None:
    from .lif import circuit_classes
    cls = circuit_classes(conn)
    idx, ks, taus = [], [], []
    for c in SENSORY_CLASSES:
        m = np.flatnonzero(cls == c)
        k = float(reg.require(f"transducer:{c}", "adapt_fraction", units="dimensionless",
                              model_use="N15: fraction of a sustained drive removed by adaptation",
                              subsystem="sensory_transduction", instances=int(m.size), minimal=0.0,
                              minimal_note="neutral 0: static transducer (m4)"))
        tau = float(reg.require(f"transducer:{c}", "adapt_tau_ms", units="ms",
                                model_use="N15: adaptation time constant",
                                subsystem="sensory_transduction", instances=int(m.size), minimal=500.0,
                                minimal_note="guessed; bounded in parameters.csv"))
        if k > 0 and m.size:
            idx.append(m); ks.append(np.full(m.size, k)); taus.append(np.full(m.size, tau))
    if not idx:
        return None
    return Adaptation(np.concatenate(idx), np.concatenate(ks), np.concatenate(taus), dt_ms)
