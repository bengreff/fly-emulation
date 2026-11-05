"""Score the spike's fitted AIY models on the held-out data, as pre-registered in docs/worm/SPIKE.md.

1. Held-out voltage clamp (blind): the Nicoletti 2024 AIY protocol (hold -60 mV 1100 ms, step 500 ms, -60 mV
   100 ms), soma clamped, current = total ionic current summed over all compartments (no capacitive term, as
   their AIY_simulation_vclamp.py sums ik + ica + ileak + inca). Steady state = mean over the last 50 ms of the
   step; peak = min (steps <= -60 mV) or max (above) over the first 100 ms. Compared with the population I-V
   (n >= 5 cells): inside mean +/- 2 SD, SD = SEM x sqrt(n). Pass needs >= 80% of voltages, for ss and for peak.
2. Checks on the current-clamp fit: float64 at dt 0.4 and 0.1 ms vs the float32 dt 0.4 traces the fit produced.
3. The published Nicoletti 2024 AIY model (single compartment) as a baseline on the same scores (not a bar).

usage: eval_aiy.py <fitdir> [models=cengen,pub] [refdir]
Writes <fitdir>/eval.json and eval.npz.
"""
import json, math, os, sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "src"))
sys.path.insert(0, os.path.dirname(__file__))
import numpy as np
import jax, jax.numpy as jnp

jax.config.update("jax_enable_x64", True)
import jaxley as jx
from bioemu.jx_membrane import make_membrane
from wormemu import nicoletti as lib
import fit_aiy as F

VC_V = np.arange(-120.0, 50.1, 10.0)
HOLD, STEP, POST = 1100.0, 500.0, 100.0


def vc_trace(vstep, dt):
    t = np.arange(0.0, HOLD + STEP + POST + dt / 2, dt)
    return jnp.where(jnp.asarray((t >= HOLD) & (t < HOLD + STEP)), vstep, -60.0), t


def setup_vc(cell):
    """Record v and every membrane state in every compartment. Returns the compartment areas (cm2)."""
    cell.delete_recordings()
    cell.record("v", verbose=False)
    for s in lib.STATES:
        cell.record(f"Mem_{s}", verbose=False)
    nodes = cell.nodes
    area = 2 * np.pi * nodes["radius"].values * nodes["length"].values * 1e-8  # cm2 per compartment
    return area


def ionic_pA(rec, ncomp, area, g, eL, eCa):
    """rec: (1+nstates)*ncomp x nt recordings in record order. Total ionic current, pA, outward positive."""
    v = rec[:ncomp]
    st = {s: rec[(1 + j) * ncomp:(2 + j) * ncomp] for j, s in enumerate(lib.STATES)}
    i, _ = lib.currents(v, st, g, eL, eCa)
    dens = sum(i.values())  # mA/cm2, per compartment
    return np.asarray(jnp.sum(dens * area[:, None], axis=0)) * 1e9


def iv_from(I, t):
    ss = np.mean(I[:, (t >= HOLD + STEP - 50) & (t < HOLD + STEP)], axis=1)
    w = (t >= HOLD) & (t <= HOLD + 100)
    pk = np.where(VC_V <= -60, np.min(I[:, w], axis=1), np.max(I[:, w], axis=1))
    return ss, pk


def score_iv(pred, data):
    """data rows: mV, n, mean pA, SEM pA. Only voltages with n >= 5."""
    rows = []
    for mv, n, mu, sem in data:
        if n < 5:
            continue
        k = int(np.argmin(np.abs(VC_V - mv)))
        sd = sem * math.sqrt(n)
        rows.append({"mV": float(mv), "n": int(n), "data_pA": round(float(mu), 2), "sd_pA": round(float(sd), 2),
                     "pred_pA": round(float(pred[k]), 2), "inside": bool(abs(pred[k] - mu) <= 2 * sd)})
    frac = float(np.mean([r["inside"] for r in rows])) if rows else float("nan")
    return {"frac_inside": frac, "n_voltages": len(rows), "pass": bool(frac >= 0.8), "rows": rows}


def run_vc(cell, site, params, g, eL, eCa, dt):
    area = setup_vc(cell)
    ncomp = cell.nodes.shape[0]

    def one(vs):
        vt, _ = vc_trace(vs, dt)
        dc = site.data_clamp("v", jnp.asarray(vt))
        return jx.integrate(cell, params=params, data_clamps=dc, delta_t=dt)

    recs = np.asarray(jax.jit(jax.vmap(one))(jnp.asarray(VC_V)))
    _, t = vc_trace(0.0, dt)
    n = min(recs.shape[-1], t.size)
    I = np.stack([ionic_pA(r[:, :n], ncomp, area, g, eL, eCa) for r in recs])
    return I, t[:n]


def fitted_cell(model, phys, dt, v0):
    """The fitted cell, parameters passed exactly as in the fit (trainable list), states initialised at v0."""
    cell, soma, area, names, lo, hi, logp = F.build_cell(2, model)
    cell.set("v", v0)
    cell.init_states(delta_t=dt)
    params = [{n: jnp.asarray([float(x)])} for n, x in zip(names, phys)]
    p = dict(zip(names, phys))
    g = {c: float(p.get(f"Mem_g_{c}", 0.0)) for c in lib.CHANNELS}
    return cell, cell.select(nodes=soma), params, g, float(p["Mem_eL"])


def pub_cell(eCa, dt):
    """The published AIY model: one compartment, cylinder with L = diam (as check_port.build_single)."""
    L = math.sqrt(F.PUB["surf"] / math.pi) * 1e4
    cell = jx.Cell([jx.Branch([jx.Compartment()], ncomp=1)], parents=[-1])
    cell.set("length", L); cell.set("radius", L / 2); cell.set("capacitance", F.PUB["cm"])
    cell.set("axial_resistivity", 100.0)
    cell.insert(make_membrane(lib)())
    g = {c: F.PUB_NS.get(c, 0.0) * 1e-9 / F.PUB["surf"] for c in lib.CHANNELS}
    for c, val in g.items():
        cell.set(f"Mem_g_{c}", val)
    cell.set("Mem_eL", F.PUB["eL"]); cell.set("Mem_sv", F.PUB["surf"] / F.PUB["vol"]); cell.set("Mem_eCa", eCa)
    cell.set("v", -60.0)
    cell.init_states(delta_t=dt)
    return cell, cell.branch(0).comp(0), g, F.PUB["eL"]


def cc_rmse(V, Vd, idx):
    return np.sqrt(np.mean((V[:, idx] - Vd[:, idx]) ** 2, axis=1))


def main():
    fitdir = sys.argv[1]
    models = (sys.argv[2] if len(sys.argv) > 2 else "cengen,pub").split(",")
    refdir = sys.argv[3] if len(sys.argv) > 3 else os.path.expanduser("~/worm-spike/ref")
    iv = F.load_iv()
    grid, Vd = F.load_cc()
    idx = np.where(grid >= F.T0_LOSS)[0][::F.DS]
    out, arrs = {}, {}
    for m in models:
        fj = json.load(open(os.path.join(fitdir, f"fit_{m}.json")))
        fz = np.load(os.path.join(fitdir, f"fit_{m}.npz"))
        phys = fz["phys"]
        r = {"params": fj["params"], "at_bound": fj["at_bound"]}
        # 1. held-out voltage clamp, dt 0.1 (and 0.025 as a convergence check)
        for dt in (0.1, 0.025):
            cell, site, params, g, eL = fitted_cell(m, phys, dt, -60.0)
            I, t = run_vc(cell, site, params, g, eL, lib.E_CA, dt)
            ss, pk = iv_from(I, t)
            key = f"vc_dt{dt}"
            r[key] = {"ss": score_iv(ss, iv["ss"]), "peak": score_iv(pk, iv["peak"])}
            arrs[f"{m}_{key}_ss"], arrs[f"{m}_{key}_pk"] = ss, pk
            if dt == 0.1:
                arrs[f"{m}_vc_I"], arrs["vc_t"] = I[:, ::10], t[::10]
        # 2. precision and step checks on current clamp (float64 here; the fit ran float32 at dt 0.4)
        for dt in (0.4, 0.1):
            cell, site, params, g, eL = fitted_cell(m, phys, dt, F.V_INIT)
            site.record("v", verbose=False)

            def sim(amp):
                ds = site.data_stimulate(jx.step_current(1000.0, 5000.0, amp, dt, F.T))
                return jx.integrate(cell, params=params, data_stimuli=ds, delta_t=dt)[0]

            V = np.asarray(jax.jit(jax.vmap(sim))(jnp.asarray(F.AMPS_PA * 1e-3)))
            step = int(round(F.DT / dt))
            V = V[:, ::step][:, :grid.size]
            d = np.sqrt(np.mean((V[:, idx] - fz["Vfit"][:, idx]) ** 2, axis=1))
            rm = cc_rmse(V, Vd, idx)
            r[f"cc_f64_dt{dt}"] = {"rms_vs_fit_mV": [round(float(x), 3) for x in d],
                                   "train_mean_rmse_mV": round(float(np.mean(rm[F.TRAIN])), 3),
                                   "held_mean_rmse_mV": round(float(np.mean(rm[F.HELD])), 3),
                                   "held_max_rmse_mV": round(float(np.max(rm[F.HELD])), 3)}
        out[m] = r
    # 3. the published model (single compartment), E_Ca 60 (stated) and 127.59 (as the published code ran)
    for eCa in (60.0, 127.59):
        cell, site, g, eL = pub_cell(eCa, 0.1)
        I, t = run_vc(cell, site, [], g, eL, eCa, 0.1)
        ss, pk = iv_from(I, t)
        r = {"vc_dt0.1": {"ss": score_iv(ss, iv["ss"]), "peak": score_iv(pk, iv["peak"])}}
        arrs[f"pub_eca{int(eCa)}_ss"], arrs[f"pub_eca{int(eCa)}_pk"] = ss, pk
        # current clamp from the NEURON reference runs (v_init -65, dt 0.4, same grid)
        ref = {60.0: "aiy_pub.npz", 127.59: "pubP.npz"}[eCa]
        if os.path.exists(os.path.join(refdir, ref)):
            Vn = np.load(os.path.join(refdir, ref))["v"][:, :grid.size]
            rm = cc_rmse(Vn, Vd, idx)
            r["cc"] = {"ref": ref, "rmse_mV": [round(float(x), 3) for x in rm],
                       "train_mean_rmse_mV": round(float(np.mean(rm[F.TRAIN])), 3),
                       "held_mean_rmse_mV": round(float(np.mean(rm[F.HELD])), 3),
                       "held_max_rmse_mV": round(float(np.max(rm[F.HELD])), 3)}
            arrs[f"pub_eca{int(eCa)}_cc"] = Vn
        out[f"published_eCa{eCa}"] = r
    arrs["iv_ss"], arrs["iv_peak"], arrs["vc_v"] = iv["ss"], iv["peak"], VC_V
    with open(os.path.join(fitdir, "eval.json"), "w") as f:
        json.dump(out, f, indent=1)
    np.savez(os.path.join(fitdir, "eval.npz"), **arrs)
    for k, r in out.items():
        v = r["vc_dt0.1"]
        print(k, "VC ss %.2f peak %.2f" % (v["ss"]["frac_inside"], v["peak"]["frac_inside"]),
              {kk: vv for kk, vv in r.items() if kk.startswith("cc")}, flush=True)


if __name__ == "__main__":
    main()
