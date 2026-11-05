"""Gap-junction check against NEURON (pre-registration and bars: docs/worm/GAPCHECK.md).

Cases: P, a passive pair; C, a chain of 8 three-compartment cells with the published Nicoletti 2024 AIY membrane.
NEURON couples the junctions with a LinearMechanism (fully implicit); Jaxley with ImplicitGap (bioemu.jx_gap),
and, as controls, ExplicitGap and the half-implicit Gap. Prints one JSON line per run and a summary of the bars;
saves the traces for the figure.

usage: check_gap_neuron.py <nicoletti moddir> <out.npz>
"""
import json, os, sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "src"))
import numpy as np
moddir, out = sys.argv[1], sys.argv[2]
from neuron import h
h.nrn_load_dll(os.path.join(moddir, "x86_64", "libnrnmech.so"))
h.load_file("stdrun.hoc")
import jax, jax.numpy as jnp
jax.config.update("jax_enable_x64", True)
import jaxley as jx
from jaxley.channels import Leak
from jaxley.connect import connect
from bioemu.jx_gap import Gap, ExplicitGap, ImplicitGap, use_implicit_gaps
from bioemu.jx_membrane import make_membrane
from wormemu import nicoletti as lib

PUB_NS = {"leak": 0.14, "slo1iso": 1, "kqt1": 0.2, "egl19": 0.1, "slo1egl19": 0.92, "nca": 0.06, "shl1": 0.5}
SURF, VOL, EL = 65.89e-8, 7.42e-12, -89.57  # published AIY: cm2, cm3, mV (as fit_aiy.PUB)
T = 100.0
CASES = {"P": dict(ncell=2, ncomp=1, L=10.0, cm=1.0, amp=0.001, v0=-70.0, pairs=[((0, 0), (1, 0))]),
         "C": dict(ncell=8, ncomp=3, L=30.0, cm=1.6, amp=0.015, v0=-65.0,
                   pairs=[((k, 2), (k + 1, 0)) for k in range(7)]),
         "S": dict(ncell=1, ncomp=1, L=10.0, cm=1.6, amp=0.015, v0=-65.0, pairs=[])}  # R0: one compartment


def nrn(case, g_nS, dt):
    c = CASES[case]
    secs = []
    for i in range(c["ncell"]):
        s = h.Section(name=f"{case}{i}")
        s.L, s.diam, s.nseg, s.cm, s.Ra = c["L"], 2.0, c["ncomp"], c["cm"], 100.0
        if case == "P":
            s.insert("pas")
            for seg in s:
                seg.pas.g, seg.pas.e = 1e-4, -70.0
        else:
            for m in PUB_NS:
                s.insert(m)
            h.ion_style("ca_ion", 1, 1, 0, 0, 0, sec=s)  # pin eca (see check_port.py, FINDINGS F-W0-1)
            for seg in s:
                for m, v in PUB_NS.items():
                    setattr(getattr(seg, m), "gbar", v * 1e-9 / SURF)
                seg.leak.e, seg.eca, seg.ek = EL, 60.0, -80.0
                if PATCHED:  # per-segment EGL-19 gates for the coupled BK channel (patch_nicoletti_mods.sh)
                    for X in ("megl19_egl19", "hegl19_egl19"):
                        h.setpointer(getattr(seg, f"_ref_{X}"), X, seg.slo1egl19)
        secs.append(s)
    x = lambda j: (j + 0.5) / c["ncomp"]
    keep = []
    for (ca, ja), (cb, jb) in c["pairs"]:
        if g_nS == 0:
            continue
        # LinearMechanism rows at segment nodes are current densities (mA/cm2), so each row's conductance is
        # g / (its segment's area), in S/cm2; absolute uS here gives area/100 of the intended coupling.
        sa, sb = secs[ca](x(ja)), secs[cb](x(jb))
        ga, gb = g_nS * 1e-9 / (sa.area() * 1e-8), g_nS * 1e-9 / (sb.area() * 1e-8)
        gm, cmat, y, b = h.Matrix(2, 2), h.Matrix(2, 2), h.Vector(2), h.Vector(2)
        gm.setval(0, 0, ga); gm.setval(0, 1, -ga); gm.setval(1, 0, -gb); gm.setval(1, 1, gb)
        sl = h.SectionList(); sl.append(sec=secs[ca]); sl.append(sec=secs[cb])
        xv = h.Vector([x(ja), x(jb)])
        keep.append((gm, cmat, y, b, sl, xv, h.LinearMechanism(cmat, gm, y, b, sl, xv)))
    stim = h.IClamp(secs[0](x(0)))
    stim.delay, stim.dur, stim.amp = 10.0, 50.0, c["amp"]
    recs = []
    for s in secs:
        for seg in s:
            r = h.Vector(); r.record(seg._ref_v); recs.append(r)
    if not PATCHED and case != "P":  # published GLOBALs carry the last run's gates into INITIAL (GAPCHECK.md)
        for X in ("megl19_egl19", "hegl19_egl19", "munc2_unc2", "hunc2_unc2"):
            setattr(h, X, 0.0)
    h.dt, h.steps_per_ms, h.tstop, h.v_init = dt, 1.0 / dt, T, c["v0"]
    h.secondorder = 0
    h.run()
    v = np.array([np.array(r) for r in recs])
    del keep, stim, recs
    for s in secs:
        h.delete_section(sec=s)
    return v


def _patched():
    s = h.Section(name="probe"); s.insert("egl19")
    r = hasattr(s(0.5).egl19, "megl19")  # RANGE in the patched mods, GLOBAL in the published ones
    h.delete_section(sec=s)
    return r


PATCHED = _patched()
print(json.dumps({"reference_mods": moddir, "per_segment_egl19_pointer": PATCHED}), flush=True)


def jxl(case, form, g_nS, dt, want_grad=False):
    c = CASES[case]
    cell = jx.Cell(jx.Branch(jx.Compartment(), ncomp=c["ncomp"]), parents=[-1])
    net = jx.Network([cell] * c["ncell"])
    if g_nS > 0:
        for (ca, ja), (cb, jb) in c["pairs"]:
            a, b = net.cell(ca).branch(0).comp(ja), net.cell(cb).branch(0).comp(jb)
            connect(a, b, form()); connect(b, a, form())
    net.set("radius", 1.0); net.set("length", c["L"] / c["ncomp"]); net.set("capacitance", c["cm"])  # per comp
    net.set("axial_resistivity", 100.0)
    if case == "P":
        net.insert(Leak()); net.set("Leak_gLeak", 1e-4); net.set("Leak_eLeak", -70.0)
    else:
        net.insert(make_membrane(lib)())
        for m, v in PUB_NS.items():
            net.set(f"Mem_g_{m}", v * 1e-9 / SURF)
        net.set("Mem_eL", EL); net.set("Mem_sv", SURF / VOL); net.set("Mem_eCa", 60.0)
    if g_nS > 0:
        net.set(f"{form.__name__}_g", g_nS * 1e-3)
        if form is ImplicitGap:
            use_implicit_gaps(net)
    net.set("v", c["v0"])
    net.init_states(delta_t=dt)
    for i in range(c["ncell"]):
        for j in range(c["ncomp"]):
            net.cell(i).branch(0).comp(j).record("v", verbose=False)
    ds = net.cell(0).branch(0).comp(0).data_stimulate(jx.step_current(10.0, 50.0, c["amp"], dt, T))
    v = np.asarray(jx.integrate(net, data_stimuli=ds, delta_t=dt))
    if not want_grad:
        return v
    getattr(net, form.__name__).make_trainable(f"{form.__name__}_g")
    p0 = net.get_parameters()
    last = (c["ncell"] - 1) * c["ncomp"] + 1  # middle compartment of the last cell

    def loss(g):
        p = [{k: jnp.full_like(val, g) for k, val in d.items()} for d in p0]
        vv = jx.integrate(net, params=p, data_stimuli=ds, delta_t=dt)
        return jnp.mean(vv[last] ** 2)
    g0 = g_nS * 1e-3
    gr = float(jax.grad(loss)(g0))
    eps = 1e-3 * g0
    fd = float((loss(g0 + eps) - loss(g0 - eps)) / (2 * eps))
    return v, gr, fd


def pair_exact(g_nS, t_ms):
    """Exact passive-pair voltages at t_ms (stimulus on from 10 ms), from the matrix exponential."""
    C, gL, g, I = 1e-6 * 2 * np.pi * 1e-8 * 10.0, 1e-4 * 2 * np.pi * 1e-8 * 10.0, g_nS * 1e-9, 1e-12
    A = np.array([[-(gL + g), g], [g, -(gL + g)]]) / C  # 1/s
    bvec = np.array([I / C, 0.0])
    w, V = np.linalg.eigh(A)
    tt = (t_ms - 10.0) * 1e-3
    E = V @ np.diag(np.expm1(w * tt) / w) @ V.T
    return -70.0 + 1e3 * (E @ bvec)


def err(a, b):
    n = min(a.shape[1], b.shape[1])
    d = np.abs(a[:, :n] - b[:, :n])
    return float(np.max(d)) if np.all(np.isfinite(d)) else float("inf")


res, traces = [], {}
FORMS = {"ImplicitGap": ImplicitGap, "ExplicitGap": ExplicitGap, "Gap": Gap}
for case, gs in (("S", (0.0,)), ("P", (0.1, 1.0, 10.0)), ("C", (0.0, 1.0, 20.0))):
    for g in gs:
        fine = nrn(case, g, 0.001)
        for dt in (0.1, 0.4):
            ref = nrn(case, g, dt)
            k = int(round(dt / 0.001))
            Cc = (CASES[case]["L"] / CASES[case]["ncomp"]) * 2 * np.pi * 1e-8 * CASES[case]["cm"] * 1e-6  # F
            row = dict(case=case, g_nS=g, dt_ms=dt, a_per_step=round(dt * 1e-3 * g * 1e-9 / Cc, 2),
                       nrn_vs_fine_mV=round(err(ref, fine[:, ::k]), 4),
                       nrn_peak_mV=round(float(ref.max()), 3))
            if case == "P":
                i60 = int(round(60.0 / 0.001))
                row["nrn_fine_vs_exact_at_60ms_mV"] = round(float(np.max(np.abs(fine[:, i60] - pair_exact(g, 60.0)))), 5)
            for name, form in FORMS.items():
                if g == 0 and name != "ImplicitGap":
                    continue
                v = jxl(case, form, g, dt)
                row[f"{name}_vs_nrn_mV"] = err(v, ref)
                row[f"{name}_vs_fine_mV"] = err(v, fine[:, ::k])
                if case == "C" and g == 20.0 and dt == 0.1:
                    traces[name] = v
            if case == "C" and g == 20.0 and dt == 0.1:
                traces["nrn"], traces["fine"] = ref, fine[:, ::k]
            if case == "S":
                traces[f"S_nrn_dt{dt}"] = ref
            print(json.dumps(row), flush=True)
            res.append(row)
_, gr, fd = jxl("C", ImplicitGap, 20.0, 0.1, want_grad=True)
b3 = bool(np.isfinite(gr) and abs(gr - fd) <= 1e-4 * abs(fd))
print(json.dumps({"B3_grad": gr, "B3_fd": fd, "rel": abs(gr - fd) / abs(fd) if fd else None, "pass": b3}), flush=True)
gap = [r for r in res if r["g_nS"] > 0]
b1 = all(r["ImplicitGap_vs_nrn_mV"] <= 0.01 for r in gap)
b2 = all(r["ImplicitGap_vs_nrn_mV"] <= 0.01 for r in res if r["case"] == "C" and r["g_nS"] == 0)
r0_jx = all(r["ImplicitGap_vs_nrn_mV"] <= 0.01 for r in res if r["case"] == "S")
strong = [max((r for r in gap if r["case"] == cs), key=lambda r: r["a_per_step"]) for cs in ("P", "C")]
f1_fails = all(not (r["ExplicitGap_vs_nrn_mV"] <= 0.01) for r in strong)
f2 = [round(r["Gap_vs_nrn_mV"], 3) for r in gap]
print(json.dumps({"R0_single_comp_vs_jaxley": r0_jx, "B1": b1, "B2": b2, "B3": b3, "F1_explicit_fails_strongest": f1_fails, "F2_Gap_errors_mV": f2,
                  "adopt_gate_numbers": b1 and b2 and b3 and f1_fails}), flush=True)
np.savez(out, **traces)
