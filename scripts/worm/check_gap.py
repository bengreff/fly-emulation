"""Check gap-junction coupling (bioemu.jx_gap) against a converged reference.

Two passive single-compartment cells (radius 1 um, length 10 um, 1 uF/cm2, leak 1e-4 S/cm2 at -70 mV, so
0.628 pF and a 10 ms time constant), coupled both ways with conductance g. Cell 0 gets 1 pA from 10 to 60 ms;
100 ms in total. For each form (Gap: post implicit; ExplicitGap: Jaxley's default linearisation, fully
explicit), each g and each dt, prints the max |v - v_ref| over both cells, where v_ref is the same form at
dt 0.001 ms. a = dt g / C is the coupling stiffness per step: the explicit form should fail above a = 1 (the difference mode decays by 1 - 2a per step).

usage: check_gap.py
"""
import json, os, sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "src"))
import numpy as np
import jax
jax.config.update("jax_enable_x64", True)
import jaxley as jx
from jaxley.channels import Leak
from jaxley.connect import connect
from bioemu.jx_gap import Gap, ExplicitGap

T = 100.0
C_F = 1e-6 * 2 * np.pi * 1e-4 * 10e-4  # F: 1 uF/cm2 x area in cm2


def pair(form, g_uS, dt):
    cell = jx.Cell(jx.Branch(jx.Compartment(), ncomp=1), parents=[-1])
    net = jx.Network([cell, cell])
    a, b = net.cell(0).branch(0).comp(0), net.cell(1).branch(0).comp(0)
    connect(a, b, form())
    connect(b, a, form())
    net.set("radius", 1.0); net.set("length", 10.0); net.set("capacitance", 1.0)
    net.insert(Leak())
    net.set("Leak_gLeak", 1e-4); net.set("Leak_eLeak", -70.0)
    net.set(f"{form.__name__}_g", g_uS)
    net.set("v", -70.0)
    net.init_states(delta_t=dt)
    a.record("v", verbose=False); b.record("v", verbose=False)
    ds = a.data_stimulate(jx.step_current(10.0, 50.0, 0.001, dt, T))
    v = np.asarray(jx.integrate(net, data_stimuli=ds, delta_t=dt))
    t = np.arange(v.shape[1]) * dt
    return t, v


def on_grid(t, v, tq):
    return np.stack([np.interp(tq, t, x) for x in v])


tq = np.arange(0.0, T, 0.4)
for form in (Gap, ExplicitGap):
    for g in (1e-6, 1e-5, 1e-4, 1e-3, 1e-2):  # uS: 1 pS to 10 nS (a up to 6 per step)
        tr, vr = pair(form, g, 0.001)
        ref = on_grid(tr, vr, tq)
        for dt in (0.1, 0.4):
            t, v = pair(form, g, dt)
            x = on_grid(t, v, tq)
            err = float(np.nanmax(np.abs(x - ref))) if np.all(np.isfinite(x)) else float("nan")
            print(json.dumps({"form": form.__name__, "g_pS": round(g * 1e6, 3), "dt_ms": dt,
                              "a_per_step": round(dt * 1e-3 * g * 1e-6 / C_F, 2),
                              "max_abs_err_mV": round(err, 4), "v_range_mV": [round(float(np.nanmin(v)), 2), round(float(np.nanmax(v)), 2)],
                              "ref_peak_mV": [round(float(ref[0].max()), 3), round(float(ref[1].max()), 3)]}), flush=True)
