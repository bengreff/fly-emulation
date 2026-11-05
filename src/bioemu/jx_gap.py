"""Ohmic gap-junction coupling for Jaxley networks.

A junction between cells a and b is two one-way couplings, a->b and b->a, each adding g (v_post - v_pre) to the
post compartment's membrane current (nA, with g in uS).

Two forms, neither adopted (FINDINGS F-W0-5). Jaxley 0.14 makes synaptic currents semi-implicit by evaluating
each current at (pre, post) and at (pre + 1e-3 mV, post + 1e-3 mV) and using the difference as the slope in the
post voltage (`jaxley/modules/network.py`, `_synapse_currents`). For g (post - pre) the two nudges cancel, so
`ExplicitGap` is integrated fully explicitly: accurate while a = dt x g / C is well below 1, and it blows up
above a = 1 (measured on a coupled pair, `scripts/worm/check_gap.py`). `Gap` carries the presynaptic voltage as a
state set at the start of each step, so the post term is implicit and the pre term explicit: it is stable at any
a, but it slows the cells' common relaxation by a factor of about 1 + a (derived; matches the pair check to
0.06 mV), so it is quietly wrong for a near or above 1. Neither replaces a coupling solved implicitly on both
sides. Use either only where every cell's summed a is well below 1, and check that.
"""
from jaxley.synapses import Synapse


class Gap(Synapse):
    """One-way ohmic coupling; post implicit, pre from the step start. Slows common relaxation by ~(1 + a)."""

    def __init__(self, name=None):
        super().__init__(name)
        self.synapse_params = {f"{self._name}_g": 1e-4}  # uS
        self.synapse_states = {f"{self._name}_vpre": -60.0}  # mV; overwritten before first use

    def update_states(self, states, delta_t, pre_voltage, post_voltage, params):
        return {f"{self._name}_vpre": pre_voltage}

    def compute_current(self, states, pre_voltage, post_voltage, params):
        return params[f"{self._name}_g"] * (post_voltage - states[f"{self._name}_vpre"])


class ExplicitGap(Synapse):
    """The naive form: zero slope under Jaxley's linearisation, so fully explicit. Unstable above a = 1."""

    def __init__(self, name=None):
        super().__init__(name)
        self.synapse_params = {f"{self._name}_g": 1e-4}  # uS
        self.synapse_states = {}

    def update_states(self, states, delta_t, pre_voltage, post_voltage, params):
        return {}

    def compute_current(self, states, pre_voltage, post_voltage, params):
        return params[f"{self._name}_g"] * (post_voltage - pre_voltage)
