"""Where does the membrane's gradient go non-finite? Evaluates d(update_states + current)/d(v, densities) on a
grid of voltage x pool Ca, float32 and float64, and prints the grid points that give NaN or inf.

usage: check_grad_nan.py [x64=0]
"""
import json, os, sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "src"))
import numpy as np
import jax, jax.numpy as jnp
if len(sys.argv) > 1 and sys.argv[1] == "1":
    jax.config.update("jax_enable_x64", True)
from bioemu.jx_membrane import make_membrane
from wormemu import nicoletti as lib

Mem = make_membrane(lib)
m = Mem()
P = {k: jnp.asarray(v) for k, v in m.channel_params.items()}
for c in lib.CHANNELS:
    P[f"Mem_g_{c}"] = jnp.asarray(1e-3)
P["Mem_sv"] = jnp.asarray(2e4)


def f(v, ca, P, dt):
    st0 = m.init_state({}, v, P, dt)
    st0["Mem_ca"] = ca
    new = m.update_states(st0, dt, v, P)
    return sum(jnp.sum(x) for x in new.values()) + m.compute_current(new, v, P)


g = jax.jit(jax.vmap(jax.grad(f, argnums=(0, 2)), in_axes=(0, 0, None, None)))
vs = np.arange(-200.0, 200.1, 1.0)
cas = np.array([1e-9, 5e-8, 1e-6, 1e-5, 1e-4, 1e-3])
V, C = np.meshgrid(vs, cas)
dv, dP = g(jnp.asarray(V.ravel()), jnp.asarray(C.ravel()), P, 0.1)
bad_v = ~np.isfinite(np.asarray(dv))
bad_p = {k: ~np.isfinite(np.asarray(x)) for k, x in dP.items()}
out = {"x64": bool(jax.config.jax_enable_x64), "n": int(V.size), "bad_dv": int(bad_v.sum()),
       "bad_dv_v": sorted(set(V.ravel()[bad_v].tolist()))[:40], "bad_dv_ca": sorted(set(C.ravel()[bad_v].tolist())),
       "bad_param": {k: [int(b.sum()), sorted(set(V.ravel()[b].tolist()))[:12]] for k, b in bad_p.items() if b.any()}}
print(json.dumps(out))
