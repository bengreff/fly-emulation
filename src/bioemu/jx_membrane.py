"""One fused Jaxley mechanism per neuron: every channel of a kinetics library in one Channel, with a
per-compartment density for each. Absent genes get density 0 (a CeNGEN mask), so all neurons of an
organism share one compiled kernel. Organism-agnostic: the library module supplies the kinetics.

Library interface (see wormemu.nicoletti): CHANNELS, STATES, all_rates(v, ca), coupled_rates(v, st, e, u),
currents(v, st, g, e_leak, e_ca), ca_pool_step(ca, i_ca, sv, dt), CA_EQ_M.
"""
import jax.numpy as jnp
from jaxley.channels import Channel


def make_membrane(lib, name="Mem"):
    class Membrane(Channel):
        def __init__(self, name=name):
            self.current_is_in_mA_per_cm2 = True
            super().__init__(name)
            p = self._name
            self.channel_params = {f"{p}_g_{c}": 0.0 for c in lib.CHANNELS}
            self.channel_params[f"{p}_eL"] = -70.0
            self.channel_params[f"{p}_sv"] = 8.88e4  # surface/volume (1/cm) for the Ca pool
            self.channel_params[f"{p}_eCa"] = lib.E_CA  # Ca reversal (mV)
            self.channel_states = {f"{p}_{s}": 0.0 for s in lib.STATES}
            self.channel_states[f"{p}_ca"] = lib.CA_EQ_M
            self.current_name = f"i_{p}"

        def _st(self, states):
            p = self._name
            return {s: states[f"{p}_{s}"] for s in lib.STATES}

        def _g(self, params):
            p = self._name
            return {c: params[f"{p}_g_{c}"] for c in lib.CHANNELS}

        def update_states(self, states, dt, v, params):
            p = self._name
            st = self._st(states)
            r, e, u = lib.all_rates(v, st["ca"])
            r.update(lib.coupled_rates(v, st, e, u, params[f"{p}_eCa"]))
            new = {}
            for s, (inf, tau) in r.items():
                new[f"{p}_{s}"] = inf + (st[s] - inf) * jnp.exp(-dt / tau)
            _, i_ca = lib.currents(v, st, self._g(params), params[f"{p}_eL"], params[f"{p}_eCa"])
            new[f"{p}_ca"] = lib.ca_pool_step(st["ca"], i_ca, params[f"{p}_sv"], dt)
            return new

        def compute_current(self, states, v, params):
            p = self._name
            i, _ = lib.currents(v, self._st(states), self._g(params), params[f"{p}_eL"], params[f"{p}_eCa"])
            return sum(i.values())

        def init_state(self, states, v, params, delta_t):
            p = self._name
            ca = jnp.asarray(lib.CA_EQ_M) * jnp.ones_like(v)
            r, e, u = lib.all_rates(v, ca)
            st = {s: r[s][0] for s in r}
            st.update({"egl19_m": e[0], "unc2_m": u[0], "ca": ca})
            st.update({s: val[0] for s, val in lib.coupled_rates(v, st, e, u, params[f"{p}_eCa"]).items()})
            return {f"{p}_{s}": st[s] for s in lib.STATES}

    return Membrane
