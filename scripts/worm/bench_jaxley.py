"""Jaxley throughput benchmark on a C. elegans morphology (OpenWorm NeuroML, Virtual Worm geometry).

Measures simulations per second for one cell, 1 s of biological time, dt 0.025 ms, at several batch
sizes (vmap over parameter sets), forward only and forward+gradient. Prints a JSON line per case.
"""
import json, os, sys, time
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "src"))
import jax, jax.numpy as jnp
import jaxley as jx
from jaxley.channels import HH
from bioemu.morph import nml_to_swc

jax.config.update("jax_enable_x64", False)
cellname = sys.argv[1] if len(sys.argv) > 1 else "RMDL"
ncomp = int(sys.argv[2]) if len(sys.argv) > 2 else 2
T = float(sys.argv[3]) if len(sys.argv) > 3 else 1000.0
morph = os.path.expanduser(f"~/worm-spike/morph/{cellname}.cell.nml")
swc = morph.replace(".cell.nml", ".swc")
npts, L = nml_to_swc(morph, swc)
cell = jx.read_swc(swc, ncomp=ncomp)
cell.insert(HH())
cell.set("HH_gNa", 0.0)  # passive-ish K + leak load; kinetics cost is what we time
ntot = cell.nodes.shape[0]
cell.branch(0).comp(0).record("v", verbose=False)
cell.make_trainable("HH_gK", verbose=False)
cell.make_trainable("HH_gLeak", verbose=False)
dt = 0.025
stim = jx.step_current(100.0, 500.0, 0.005, dt, T)
ds = cell.branch(0).comp(0).data_stimulate(stim)
params = cell.get_parameters()

nsteps = int(T / dt) + 1
ck = [int(nsteps ** 0.5) + 1] * 2  # sqrt checkpointing keeps backward memory O(sqrt(steps))

def sim(p, ckpt=None):
    return jx.integrate(cell, params=p, data_stimuli=ds, delta_t=dt, checkpoint_lengths=ckpt)

def lossf(p):
    return jnp.mean(sim(p, ck) ** 2)

out = {"cell": cellname, "swc_points": npts, "neurite_um": round(L, 1), "branches": len(cell.branch_edges) if hasattr(cell, "branch_edges") else None,
       "compartments": int(ntot), "T_ms": T, "dt_ms": dt, "device": str(jax.devices()[0])}
print(json.dumps(out), flush=True)
for B in [int(b) for b in os.environ.get('BATCHES', '1,64,512,2048').split(',')]:
    pb = jax.tree_util.tree_map(lambda x: jnp.repeat(x[None], B, 0) * (1 + 0.01 * jnp.arange(B).reshape((B,) + (1,) * x.ndim) / B), params)
    for mode in ["fwd", "grad"]:
        f = jax.jit(jax.vmap(sim)) if mode == "fwd" else jax.jit(jax.vmap(jax.grad(lossf)))
        t0 = time.time(); r = f(pb); jax.block_until_ready(r); tc = time.time() - t0
        t0 = time.time(); r = f(pb); jax.block_until_ready(r); tr = time.time() - t0
        print(json.dumps({"batch": B, "mode": mode, "compile_plus_run_s": round(tc, 2), "run_s": round(tr, 3),
                          "sims_per_s": round(B / tr, 1), "comp_steps_per_s": round(B * ntot * T / dt / tr, 0)}), flush=True)
        if tr > 60: break
