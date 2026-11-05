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

`ImplicitGap` (with `use_implicit_gaps`) is the coupling solved with the cable: the step solves
(M + dt G) v = rhs, where M is Jaxley's own backward-Euler matrix and G the gap-junction Laplacian, using Jaxley's
tree solver plus an exact Woodbury correction over the compartments that carry junctions. Checked against
NEURON's LinearMechanism in `scripts/worm/check_gap_neuron.py` (pre-registration: `docs/worm/GAPCHECK.md`).
"""
import inspect

import jax.numpy as jnp
import numpy as np
import jaxley
from jaxley.synapses import Synapse
from jaxley.utils.cell_utils import convert_point_process_to_distributed


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


class ImplicitGap(Synapse):
    """Holds the junction conductance only; its current is added implicitly by `use_implicit_gaps`."""

    def __init__(self, name=None):
        super().__init__(name)
        self.synapse_params = {f"{self._name}_g": 1e-4}  # uS
        self.synapse_states = {}

    def update_states(self, states, delta_t, pre_voltage, post_voltage, params):
        return {}

    def compute_current(self, states, pre_voltage, post_voltage, params):
        return 0.0 * post_voltage


_CTX = []  # (gap structure, params) of the step being traced; read by the patched tree solve


def use_implicit_gaps(net, name="ImplicitGap"):
    """Register the network's `name` edges as implicitly solved junctions. Call after every connect.

    Each junction is two directed edges (a->b and b->a), as with the other forms. Needs Jaxley 0.14.0, backward
    Euler and the default `jaxley.dhs` voltage solver; anything else raises rather than dropping the junctions.
    """
    assert jaxley.__version__ == "0.14.0", "patch written against jaxley 0.14.0 internals"
    _patch()
    e = net.edges[net.edges["type"] == name]
    pre, post = e["pre_index"].to_numpy(int), e["post_index"].to_numpy(int)
    # Edge indices are `nodes` labels, which index the solver's voltage vector; with branch points they skip numbers,
    # so look cells up by label, not by position.
    cell_of = net.nodes["global_cell_index"].astype(int).to_dict()
    S = np.unique(np.concatenate([pre, post]))
    pos = {c: i for i, c in enumerate(S)}
    slot, seen = np.zeros(len(S), int), {}
    for i, c in enumerate(S):  # slot j = the j-th junction compartment of its cell
        slot[i] = seen.get(cell_of[c], 0)
        seen[cell_of[c]] = slot[i] + 1
    net._implicit_gap = dict(
        name=name, post=post, S=S, slot=slot,
        slot_nodes=[S[slot == j] for j in range(slot.max() + 1)] if len(S) else [],
        same_cell=(np.array([cell_of[c] for c in S])[:, None] == np.array([cell_of[c] for c in S])[None, :]).astype(float),
        pre_s=np.array([pos[c] for c in pre], int), post_s=np.array([pos[c] for c in post], int))
    return net


def _patch():
    import jaxley.modules.base as base
    if getattr(base, "_bioemu_implicit_gap", False):
        return
    orig_step, orig_solve = base.Module.step, base.step_voltage_implicit_with_dhs_solve
    sig = inspect.signature(orig_step)

    def step(self, *args, **kwargs):
        gj = getattr(self, "_implicit_gap", None)
        if gj is None:
            return orig_step(self, *args, **kwargs)
        b = sig.bind(self, *args, **kwargs)
        b.apply_defaults()
        if b.arguments["solver"] != "bwd_euler" or not b.arguments["voltage_solver"].startswith("jaxley.dhs"):
            raise ValueError("implicit gap junctions need solver='bwd_euler' and a jaxley.dhs voltage solver")
        _CTX.append((gj, b.arguments["params"]))
        try:
            out = orig_step(self, *args, **kwargs)
        finally:
            missed = bool(_CTX)
            _CTX.clear()
        if missed:
            raise RuntimeError("implicit gap junctions were not applied in this step")
        return out

    def solve(voltages, voltage_terms, constant_terms, axial_conductances, *rest):
        if not _CTX:
            return orig_solve(voltages, voltage_terms, constant_terms, axial_conductances, *rest)
        gj, params = _CTX.pop()
        dt = rest[-1]
        g = params[f"{gj['name']}_g"]
        post = gj["post"]
        gn = convert_point_process_to_distributed(g, params["area"][post]) / params["capacitance"][post]
        vt = voltage_terms.at[post].add(gn)  # junction conductance onto its own compartment's diagonal
        zero = jnp.zeros_like(constant_terms)

        def tree(rhs, ct):  # M' x = rhs + dt ct, M' = Jaxley's matrix with the junction diagonals added
            return orig_solve(rhs, vt, ct, axial_conductances, *rest)

        x0 = tree(voltages, constant_terms)
        S, nS = gj["S"], len(gj["S"])
        if nS == 0:
            return x0
        # W[a, b] = (M'^-1 e_b)[S_a]; M' has no coupling between cells, so one solve per slot covers all cells.
        X = jnp.stack([tree(jnp.zeros_like(voltages).at[nodes].set(1.0), zero) for nodes in gj["slot_nodes"]])
        W = X[gj["slot"][None, :], S[:, None]] * gj["same_cell"]
        # Off-diagonal junction terms O[post, pre] = -gn. Solve (I + dt W O) y = x0[S], then correct x0.
        WO = jnp.zeros((nS, nS), W.dtype).at[:, gj["pre_s"]].add(-W[:, gj["post_s"]] * gn[None, :])
        y = jnp.linalg.solve(jnp.eye(nS, dtype=W.dtype) + dt * WO, x0[S])
        Oy = jnp.zeros(nS, y.dtype).at[gj["post_s"]].add(-gn * y[gj["pre_s"]])
        return x0 + tree(jnp.zeros_like(voltages).at[S].set(-dt * Oy), zero)

    base.Module.step = step
    base.step_voltage_implicit_with_dhs_solve = solve
    base._bioemu_implicit_gap = True

