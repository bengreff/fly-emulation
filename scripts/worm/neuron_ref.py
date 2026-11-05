"""CPU reference path: run the Nicoletti et al. 2024 .mod files in NEURON for a single-compartment
neuron with given densities, under the published current-clamp protocol. Writes an .npz.

usage: neuron_ref.py <moddir> <out.npz> <json densities in nS, plus eL (mV), cm (uF/cm2), surf (cm2), vol (cm3)>
Protocol (AIY_simulation_iclamp.py): steps -15..+35 pA x 11, delay 1000 ms, dur 5000 ms, 11000 ms, dt 0.4 ms,
v_init -65 (what h.run() actually uses in the published scripts), eca 60, ek -80.
"""
import json, math, os, sys
import numpy as np

moddir, out, cfg = sys.argv[1], os.path.abspath(sys.argv[2]), json.loads(sys.argv[3])
os.chdir(moddir)
from neuron import h  # noqa: E402  (nrnivmodl output in moddir/x86_64 is auto-loaded from cwd)

h.load_file("stdrun.hoc")
surf, vol = cfg["surf"], cfg["vol"]
L = math.sqrt(surf / math.pi) * 1e4
soma = h.Section(name="soma")
soma.L = soma.diam = L
soma.cm = cfg["cm"]
soma.Ra = 100
g = cfg["g_nS"]
for mech in g:
    soma.insert(mech)
if "kcnl" in g:
    soma.insert("caintra1")
    for seg in soma:
        seg.caintra1.surf = surf
        seg.caintra1.vol = vol
# NEURON quirk: if any mechanism READs cai (slo1iso does), finitialize recomputes eca from the Nernst equation
# and overrides the eca=60 set below. The published scripts hit this. "eca_mode": "fixed" (default) pins eca so
# the port check compares like with like; "published" leaves NEURON's default, as the authors' runs did.
if cfg.get("eca_mode", "fixed") == "fixed" and hasattr(soma(0.5), "eca"):
    h.ion_style("ca_ion", 1, 1, 0, 0, 0, sec=soma)
for seg in soma:
    for mech, val in g.items():
        setattr(getattr(seg, mech), "gbar", val * 1e-9 / surf)
    seg.leak.e = cfg["eL"]
    for ion, e in (("eca", 60), ("ek", -80)):
        if hasattr(seg, ion):
            setattr(seg, ion, e)
stim = h.IClamp(soma(0.5))
stim.delay, stim.dur = 1000, 5000
v_vec, t_vec = h.Vector(), h.Vector()
v_vec.record(soma(0.5)._ref_v)
t_vec.record(h._ref_t)
dt = cfg.get("dt", 0.4)
V = []
for amp in np.linspace(-0.015, 0.035, 11):
    stim.amp = amp
    h.steps_per_ms = 1.0 / dt  # stdrun would otherwise reset dt to 0.025
    h.dt = dt
    h.tstop = cfg.get("tstop", 11000)
    h.v_init = cfg.get("v_init", -65.0)  # run() re-initialises at v_init (the published scripts' finitialize(-60) is overridden)
    h.run()
    V.append(np.array(v_vec))
np.savez(out, t=np.array(t_vec), v=np.array(V), cfg=json.dumps(cfg))
print("saved", out, np.array(V).shape, "rest %.2f mV" % V[3][int(900 / dt)],
      "eca after run %s, celsius %.2f" % (getattr(soma(0.5), "eca", None), h.celsius))
