"""ImplicitGap on branched cells (reported check, docs/worm/GAPCHECK.md): three Virtual Worm AIYL cells, 2
compartments per branch, junctions on both branches and two sites in every cell, so node labels skip the branch
points. Implicit and explicit coupling at the same small step (explicit is stable there) must converge to the
same solution, their difference falling in proportion to dt; an indexing error would show as a difference that
does not shrink. Also reports ImplicitGap's own step error at dt 0.1 ms against dt 0.001 ms.

usage: check_gap_branched.py
"""
import json, os, sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "src"))
import numpy as np
import jax
jax.config.update("jax_enable_x64", True)
import jaxley as jx
from jaxley.connect import connect
from bioemu.jx_gap import ExplicitGap, ImplicitGap, use_implicit_gaps
from bioemu.jx_membrane import make_membrane
from bioemu.morph import nml_to_swc
from wormemu import nicoletti as lib

MORPH = os.path.expanduser("~/worm-data/morphologies/CElegansNeuroML/CElegans/generatedNeuroML2/AIYL.cell.nml")
SITES = [((0, 0, 0), (1, 0, 0)), ((1, 1, 1), (2, 0, 0)), ((0, 1, 1), (2, 1, 0))]  # (cell, branch, comp); AIYL has 2 branches
T, G_NS = 100.0, 5.0


def run(form, dt, solve="dense"):
    nml_to_swc(MORPH, "/tmp/AIYL_gb.swc")
    cell = jx.read_swc("/tmp/AIYL_gb.swc", ncomp=2)
    cell.insert(make_membrane(lib)())
    for c, g in {"leak": 2e-4, "egl19": 1e-4, "kqt1": 3e-4, "slo1egl19": 1e-3, "slo1iso": 1e-3, "nca": 9e-5}.items():
        cell.set(f"Mem_g_{c}", g)
    cell.set("Mem_eL", -80.0)
    net = jx.Network([cell, cell, cell])
    for (a, b) in SITES:
        pa, pb = net.cell(a[0]).branch(a[1]).comp(a[2]), net.cell(b[0]).branch(b[1]).comp(b[2])
        connect(pa, pb, form()); connect(pb, pa, form())
    net.set(f"{form.__name__}_g", G_NS * 1e-3)
    if form is ImplicitGap:
        use_implicit_gaps(net, solve=solve)
    net.set("v", -60.0)
    net.init_states(delta_t=dt)
    for k in range(3):
        for (b, cp) in ((0, 0), (0, 1), (1, 0), (1, 1)):
            net.cell(k).branch(b).comp(cp).record("v", verbose=False)
    ds = net.cell(0).branch(0).comp(0).data_stimulate(jx.step_current(10.0, 60.0, 0.02, dt, T))
    return np.asarray(jx.integrate(net, data_stimuli=ds, delta_t=dt)), net


vi, net = run(ImplicitGap, 0.1)
out = {"nodes": int(net.nodes.shape[0]), "max_label": int(net.nodes.index.max()), "junction_sites": int(len(net._implicit_gap["S"])),
       "slots": len(net._implicit_gap["slot_nodes"]), "v_range_mV": [float(vi.min()), float(vi.max())]}
# Implicit and explicit coupling differ by O(dt) at the same step, so their difference must shrink in proportion
# to dt; a wrong node or cell lookup would leave a difference that does not go to zero.
for dt in (0.004, 0.002, 0.001):
    a, _ = run(ImplicitGap, dt)
    b, _ = run(ExplicitGap, dt)
    out[f"implicit_vs_explicit_dt{dt}_mV"] = float(np.abs(a - b).max())
    if dt == 0.001:
        k = 100
        n = min(vi.shape[1], a[:, ::k].shape[1])
        out["implicit_dt0.1_vs_implicit_dt0.001_mV"] = float(np.abs(vi[:, :n] - a[:, ::k][:, :n]).max())
vg, _ = run(ImplicitGap, 0.1, "gmres")  # gapcheck4 B4: the iterative junction solve against the dense one
out["gmres_vs_dense_dt0.1_mV"] = float(np.abs(vg - vi).max())
print(json.dumps(out), flush=True)
