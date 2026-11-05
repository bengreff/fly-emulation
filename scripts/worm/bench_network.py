"""Whole-worm-scale cost benchmark (for the PLAN compute extrapolation; numbers are measured, the model is not).

Every cell in the Cook 2019 hermaphrodite chemical adjacency (neurons, muscles, end organs) gets the spike's
AIY model (4 compartments, full Nicoletti membrane); every nonzero chemical entry is one Jaxley
IonotropicSynapse; every nonzero symmetric gap-junction entry between those cells is a pair of ohmic
couplings. Times forward and forward+gradient (w.r.t. all synaptic and gap conductances) per biological
second, on whatever device JAX sees. Prints JSON lines.

usage: bench_network.py [T_ms=200] [dt_ms=0.1] [batch=1] [scale=1.0]
batch > 1 vmaps over that many perturbed copies of the conductances (the fitting use case: many parameter sets
or trials at once); timings are then per batch, and sims/s = batch / run_s * (T/1000) bio-s per wall-s.
"""
import json, math, os, sys, time
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "src"))
import numpy as np
import jax, jax.numpy as jnp
import jaxley as jx
from jaxley.synapses import IonotropicSynapse
from jaxley.connect import connectivity_matrix_connect
from bioemu.morph import nml_to_swc
from bioemu.jx_membrane import make_membrane
from bioemu.jx_gap import Gap, ExplicitGap, ImplicitGap, use_implicit_gaps
from wormemu import nicoletti as lib

T = float(sys.argv[1]) if len(sys.argv) > 1 else 200.0
DT = float(sys.argv[2]) if len(sys.argv) > 2 else 0.1
B = int(sys.argv[3]) if len(sys.argv) > 3 else 1
SCALE = float(sys.argv[4]) if len(sys.argv) > 4 else 1.0  # batch 1 only: multiply every synaptic and gap conductance
# default: the form the 4 Nov timings used
GAP = {"semi": Gap, "implicit": ImplicitGap}.get(os.environ.get("BENCH_GAP"), ExplicitGap)
HOME = os.path.expanduser("~")
COOK = f"{HOME}/worm-data/cook2019/SI 5 Connectome adjacency matrices, corrected July 2020.xlsx"
MORPH = f"{HOME}/worm-data/morphologies/CElegansNeuroML/CElegans/generatedNeuroML2/AIYL.cell.nml"


def adjacency(sheet):
    import openpyxl
    ws = openpyxl.load_workbook(COOK, read_only=True, data_only=True)[sheet]
    rows = [list(r) for r in ws.iter_rows(values_only=True)]
    cols = rows[2][3:]
    out = {}
    for r in rows[3:]:
        if r[2] is None:
            continue
        for c, x in zip(cols, r[3:]):
            if c is not None and isinstance(x, (int, float)) and x > 0:
                out[(r[2], c)] = x
    return out


chem = adjacency("hermaphrodite chemical")
gap = adjacency("hermaphrodite gap jn symmetric")
cells = sorted({a for a, b in chem} | {b for a, b in chem})
ix = {c: i for i, c in enumerate(cells)}
gpairs = sorted({(a, b) for a, b in gap if a in ix and b in ix and a != b})
N = len(cells)
C = np.zeros((N, N), bool)
for a, b in chem:
    if a != b:
        C[ix[a], ix[b]] = True
G = np.zeros((N, N), bool)
for a, b in gpairs:
    G[ix[a], ix[b]] = G[ix[b], ix[a]] = True
if os.environ.get("BENCH_NO_GAP"):  # diagnosis: chemical synapses only
    G[:] = False

swc = "/tmp/AIYL_bench.swc"
nml_to_swc(MORPH, swc)
cell = jx.read_swc(swc, ncomp=2)
cell.insert(make_membrane(lib)())
for c, g in {"leak": 2e-4, "egl19": 1e-4, "kqt1": 3e-4, "slo1egl19": 1e-3, "slo1iso": 1e-3, "nca": 9e-5}.items():
    cell.set(f"Mem_g_{c}", g)
cell.set("Mem_eL", -80.0)
net = jx.Network([cell for _ in range(N)])
t0 = time.time()
connectivity_matrix_connect(net.cell("all"), net.cell("all"), IonotropicSynapse(), C)
if G.any():
    connectivity_matrix_connect(net.cell("all"), net.cell("all"), GAP(), G)
    if GAP is ImplicitGap:
        use_implicit_gaps(net)
t_build = time.time() - t0
net.set("v", -60.0)
net.init_states(delta_t=DT)
for k in range(8):
    net.cell(k).branch(0).comp(0).record("v", verbose=False)
if os.environ.get("BENCH_RECORD_ALL"):  # diagnosis: every cell's first compartment
    for k in range(8, N):
        net.cell(k).branch(0).comp(0).record("v", verbose=False)
net.IonotropicSynapse.make_trainable("IonotropicSynapse_gS", verbose=False)
if G.any():
    getattr(net, GAP.__name__).make_trainable(f"{GAP.__name__}_g", verbose=False)
params = net.get_parameters()
stim = jx.step_current(10.0, T - 20.0, 0.01, DT, T)
ds = None
for k in range(8):
    ds = net.cell(k).branch(0).comp(0).data_stimulate(stim, ds)
nsteps = int(round(T / DT)) + 1
ck = [int(math.ceil(nsteps ** 0.5))] * 2
info = {"cells": N, "compartments": int(net.nodes.shape[0]), "chem_synapses": int(C.sum()), "gap_couplings": int(G.sum()),
        "gap_junction_pairs": len(gpairs) // 2, "gap_form": GAP.__name__,
        "implicit_gap_sites": int(len(net._implicit_gap["S"])) if GAP is ImplicitGap else None,
        "implicit_gap_slots": len(net._implicit_gap["slot_nodes"]) if GAP is ImplicitGap else None, "batch": B, "scale": SCALE, "T_ms": T, "dt_ms": DT, "device": str(jax.devices()[0]), "build_s": round(t_build, 1)}
print(json.dumps(info), flush=True)


def fwd(p):
    return jx.integrate(net, params=p, data_stimuli=ds, delta_t=DT)


def lossf(p):
    return jnp.mean(jx.integrate(net, params=p, data_stimuli=ds, delta_t=DT, checkpoint_lengths=ck) ** 2)


if B == 1 and SCALE != 1.0:
    params = [{k: v * SCALE for k, v in d.items()} for d in params]
if B > 1:
    scale = jnp.asarray(np.random.default_rng(0).uniform(0.5, 1.5, B))
    params = [{k: v[None] * scale.reshape((B,) + (1,) * v.ndim) for k, v in d.items()} for d in params]
    fwd, lossf = jax.vmap(fwd), (lambda p, f=lossf: jnp.sum(jax.vmap(f)(p)))
for mode, f in [("fwd", jax.jit(fwd)), ("grad", jax.jit(jax.grad(lossf)))]:
    t0 = time.time(); r = jax.block_until_ready(f(params)); tc = time.time() - t0
    t0 = time.time(); r = jax.block_until_ready(f(params)); tr = time.time() - t0
    ok = bool(np.all(np.isfinite(np.asarray(r)))) if mode == "fwd" else bool(all(np.all(np.isfinite(np.asarray(x))) for d in r for x in d.values()))
    if mode == "grad" and not ok:
        print(json.dumps({k: int((~np.isfinite(np.asarray(x))).sum()) for d in r for k, x in d.items()}), flush=True)
    if mode == "fwd":
        vr = np.asarray(r)
        print(json.dumps({"v_min": round(float(np.nanmin(vr)), 1), "v_max": round(float(np.nanmax(vr)), 1)}), flush=True)
        if os.environ.get("BENCH_RECORD_ALL") and B == 1:
            ext = np.nanmax(np.abs(vr), axis=1)
            worst = np.argsort(-ext)[:6]
            print(json.dumps({"n_cells_abs_v_over_150": int((ext > 150).sum()),
                              "worst": [[cells[k], round(float(ext[k]), 1), int(G[k].sum()), int(C[:, k].sum())] for k in worst],
                              "gap_degree_max": int(G.sum(1).max())}), flush=True)
    print(json.dumps({"mode": mode, "compile_plus_run_s": round(tc, 2), "run_s": round(tr, 3), "wall_s_per_bio_s": round(tr / (T / 1e3), 2), "bio_s_per_wall_s": round(B * (T / 1e3) / tr, 3),
                      "us_per_step": round(1e6 * tr / nsteps, 1), "finite": ok}), flush=True)
