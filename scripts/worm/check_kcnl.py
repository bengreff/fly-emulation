"""Q3 check (W1_RIM_AFD.md, run kcnl1): the per-segment KCNL Ca pointer, NEURON vs Jaxley.

Cells: S (one compartment, RIM geometry), M (300 um x 0.3 um cable, 3 compartments, current into the first),
M0 (M without KCNL). Membrane: published RIM densities plus KCNL, SLO-1(EGL-19), SLO-2(UNC-2) at 1e-3 S/cm2.

usage: check_kcnl.py nrn <moddir> <out.npz>     NEURON on the given mods (published or patched)
       check_kcnl.py jx <out.npz> [--ca-lag]    Jaxley, float64 (--ca-lag: NEURON's Ca-pool step order, kcnl2)
       check_kcnl.py score <rundir> <fig.png>   bars K0-K2 from rundir/{pub,pat,jx}.npz
"""
import json, math, os, sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "src"))
import numpy as np

RIM = dict(surf=103.34e-8, vol=10.94e-12, cm=1.5, eL=-50.0)
G = dict(zip(["shl1", "egl2", "irk", "cca1", "unc2", "egl19", "leak"],
             [0.0009048750067326097, 0.0001411644285181245, 0.0003272854640954744, 0.0008451919806776876,
              9.676795045480941e-05, 0.00032005818627638106, 9.676795045480941e-05]))  # RIM_simulation.py, S/cm2
G.update(kcnl=1e-3, slo1egl19=1e-3, slo2unc2=1e-3)  # guessed test densities
CELLS = {"S": dict(L=None, diam=None, ncomp=1, kcnl=True), "M": dict(L=300.0, diam=0.3, ncomp=3, kcnl=True),
         "M0": dict(L=300.0, diam=0.3, ncomp=3, kcnl=False)}
AMPS = np.linspace(-0.015, 0.035, 11)  # nA
T = 8000.0
DTS = tuple(float(x) for x in os.environ.get("KCNL_DTS", "0.4,0.1").split(","))  # development: e.g. 0.01 for a fine reference
if os.environ.get("KCNL_CELLS"):
    CELLS = {k: CELLS[k] for k in os.environ["KCNL_CELLS"].split(",")}


def geom(c):
    if c["L"] is None:  # cylinder with L = diam and the RIM surface, as the Nicoletti scripts
        L = math.sqrt(RIM["surf"] / math.pi) * 1e4
        return L, L, RIM["surf"] / RIM["vol"]
    return c["L"], c["diam"], 2.0 / (c["diam"] / 2 * 1e-4)


def gset(c):
    return {k: v for k, v in G.items() if c["kcnl"] or k != "kcnl"}


def run_nrn(moddir, out):
    os.chdir(moddir)
    from neuron import h
    h.load_file("stdrun.hoc")
    probe = h.Section(name="probe"); probe.insert("caintra1")
    patched = hasattr(probe(0.5).caintra1, "calcium")  # RANGE in the patched mods, GLOBAL in the published ones
    h.delete_section(sec=probe)
    res = {}
    for name, c in CELLS.items():
        L, diam, _ = geom(c)
        s = h.Section(name=name)
        s.L, s.diam, s.nseg, s.cm, s.Ra = L, diam, c["ncomp"], RIM["cm"], 100.0
        g = gset(c)
        for m in g:
            s.insert(m)
        s.insert("caintra1")
        h.ion_style("ca_ion", 1, 1, 0, 0, 0, sec=s)  # pin eca (F-W0-1)
        for seg in s:
            for m, v in g.items():
                setattr(getattr(seg, m), "gbar", v)
            seg.leak.e, seg.eca, seg.ek = RIM["eL"], 60.0, -80.0
            if c["L"] is None:
                seg.caintra1.surf, seg.caintra1.vol = RIM["surf"], RIM["vol"]
            else:
                seg.caintra1.surf = seg.area() * 1e-8
                seg.caintra1.vol = math.pi * (diam / 2) ** 2 * (L / c["ncomp"]) * 1e-12
            if patched:
                for X in ("megl19_egl19", "hegl19_egl19"):
                    h.setpointer(getattr(seg, f"_ref_{X}"), X, seg.slo1egl19)
                for X in ("munc2_unc2", "hunc2_unc2"):
                    h.setpointer(getattr(seg, f"_ref_{X}"), X, seg.slo2unc2)
                if c["kcnl"]:
                    h.setpointer(seg._ref_calcium_caintra1, "calcium_caintra1", seg.kcnl)
        stim = h.IClamp(s((0.5) / c["ncomp"]))
        stim.delay, stim.dur = 1000.0, 5000.0
        recs = []
        for seg in s:
            r = h.Vector(); r.record(seg._ref_v); recs.append(r)
        for dt in DTS:
            V = []
            for amp in AMPS:
                if not patched:  # published GLOBALs keep the last run's values (F-W0-10); reset them
                    for X in ("megl19_egl19", "hegl19_egl19", "munc2_unc2", "hunc2_unc2"):
                        setattr(h, X, 0.0)
                    h.calcium_caintra1 = 0.05e-6
                elif os.environ.get("KCNL_RESET_RANGE"):  # kcnl1 carried the last run's calcium into step 1 (K0)
                    for seg in s:
                        seg.caintra1.calcium = 0.05e-6
                stim.amp = amp
                h.dt, h.steps_per_ms, h.tstop, h.v_init = dt, 1.0 / dt, T, -65.0
                h.secondorder = 0
                h.run()
                V.append(np.array([np.array(r) for r in recs]))
            res[f"{name}_dt{dt}"] = np.array(V)  # (sweep, comp, t)
            print(name, dt, "patched" if patched else "published", res[f"{name}_dt{dt}"].shape, flush=True)
        del stim, recs
        h.delete_section(sec=s)
    np.savez(out, patched=patched, **res)


def run_jx(out, ca_lag=False):
    import jax
    jax.config.update("jax_enable_x64", True)
    import jaxley as jx
    from bioemu.jx_membrane import make_membrane
    from wormemu import nicoletti as lib
    res = {}
    for name, c in CELLS.items():
        L, diam, sv = geom(c)
        g = gset(c)
        cell = jx.Cell(jx.Branch(jx.Compartment(), ncomp=c["ncomp"]), parents=[-1])
        cell.set("length", L / c["ncomp"]); cell.set("radius", diam / 2)
        cell.set("capacitance", RIM["cm"]); cell.set("axial_resistivity", 100.0)
        cell.insert(make_membrane(lib, channels=[ch for ch in lib.ALL_CHANNELS if ch in g], ca_lag=ca_lag)())
        for m, v in g.items():
            cell.set(f"Mem_g_{m}", v)
        cell.set("Mem_eL", RIM["eL"]); cell.set("Mem_sv", sv); cell.set("Mem_eCa", 60.0)
        for j in range(c["ncomp"]):
            cell.branch(0).comp(j).record("v", verbose=False)
        for dt in DTS:
            cell.set("v", -65.0)
            cell.init_states(delta_t=dt)
            site = cell.branch(0).comp(0)
            sim = jax.jit(jax.vmap(lambda a: jx.integrate(cell, data_stimuli=site.data_stimulate(
                jx.step_current(1000.0, 5000.0, a, dt, T)), delta_t=dt)))
            res[f"{name}_dt{dt}"] = np.asarray(sim(jax.numpy.asarray(AMPS)))
            print(name, dt, "jaxley", res[f"{name}_dt{dt}"].shape, flush=True)
    np.savez(out, **res)


def score(R, fig):
    pub, pat, jxv = (np.load(f"{R}/{k}.npz") for k in ("pub", "pat", "jx"))
    assert bool(pat["patched"]) and not bool(pub["patched"])
    rms = lambda a, b: np.sqrt(np.mean((a[..., :min(a.shape[-1], b.shape[-1])] - b[..., :min(a.shape[-1], b.shape[-1])]) ** 2, axis=-1))
    mx = lambda a, b: float(np.max(np.abs(a[..., :min(a.shape[-1], b.shape[-1])] - b[..., :min(a.shape[-1], b.shape[-1])])))
    out = {"K0": {}, "K1": {}, "reported_global_defect": {}}
    for dt in DTS:
        out["K0"][f"S_dt{dt}"] = mx(pat[f"S_dt{dt}"], pub[f"S_dt{dt}"])
        for c in CELLS:
            k = f"{c}_dt{dt}"
            r = rms(jxv[k], pat[k])
            out["K1"][k] = {"worst_rms_mV": float(r.max()), "max_abs_mV": mx(jxv[k], pat[k])}
        k = f"M_dt{dt}"
        out["reported_global_defect"][k] = {"max_abs_mV": mx(pub[k], pat[k]), "worst_rms_mV": float(rms(pub[k], pat[k]).max())}
    out["K2_kcnl_effect_rms_mV"] = float(np.mean(rms(pat["M_dt0.4"][:, 0], pat["M0_dt0.4"][:, 0])))
    out["pass"] = {"K0": all(v <= 1e-9 for v in out["K0"].values()),
                   "K1": all(v["worst_rms_mV"] <= 0.01 for v in out["K1"].values()),
                   "K2": out["K2_kcnl_effect_rms_mV"] >= 1.0}
    print(json.dumps(out, indent=1))
    json.dump(out, open(f"{R}/score.json", "w"), indent=1)
    import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
    f, ax = plt.subplots(1, 3, figsize=(15, 4))
    t = np.arange(pat["M_dt0.1"].shape[-1]) * 0.1 / 1e3
    for j, col in enumerate(["C0", "C1", "C2"]):
        ax[0].plot(t, pat["M_dt0.1"][10, j], col, lw=2, label=f"NEURON patched, comp {j}")
        ax[0].plot(t, jxv["M_dt0.1"][10, j][:len(t)], "k--", lw=0.8)
        ax[0].plot(t, pub["M_dt0.1"][10, j], col, lw=0.6, alpha=0.6)
    ax[0].set(title="M cable, +35 pA (dashed: Jaxley; thin: published mods)", xlabel="s", ylabel="mV"); ax[0].legend(fontsize=7)
    ks = list(out["K1"]); ax[1].bar(range(len(ks)), [max(out["K1"][k]["worst_rms_mV"], 1e-16) for k in ks])
    ax[1].axhline(0.01, color="r"); ax[1].set_yscale("log"); ax[1].set_xticks(range(len(ks))); ax[1].set_xticklabels(ks, rotation=45, fontsize=7)
    ax[1].set(title="K1: Jaxley vs patched NEURON, worst sweep RMS (mV)")
    for j in range(3):
        ax[2].plot(AMPS * 1e3, rms(pub["M_dt0.4"][:, j], pat["M_dt0.4"][:, j]), "o-", label=f"published vs patched, comp {j}")
    ax[2].plot(AMPS * 1e3, rms(pat["M_dt0.4"][:, 0], pat["M0_dt0.4"][:, 0]), "ks-", label="K2: KCNL on vs off, comp 0")
    ax[2].axhline(1.0, color="r", lw=0.6); ax[2].set_yscale("log"); ax[2].set(xlabel="step (pA)", ylabel="RMS (mV)"); ax[2].legend(fontsize=7)
    f.tight_layout(); f.savefig(fig, dpi=110)


if __name__ == "__main__":
    mode = sys.argv[1]
    if mode == "nrn":
        run_nrn(sys.argv[2], os.path.abspath(sys.argv[3]))
    elif mode == "jx":
        run_jx(sys.argv[2], ca_lag="--ca-lag" in sys.argv)
    else:
        score(sys.argv[2], sys.argv[3])
