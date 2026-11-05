"""W1: fit a multicompartment RIM or AFD model (CeNGEN channel set, Nicoletti 2024 kinetics) to the Naudin 2022
current-clamp training sweeps, or one of its controls. Pre-registration, split and bars: docs/worm/W1_RIM_AFD.md
(do not change the split, windows or bounds here without a new labelled experiment).

usage: fit_w1.py <outdir> --cell rim|afd --model full|m1|fixed [--fixed <fit json>] [--starts 16] [--iters 300]
  full   the cell's CeNGEN channel set, every density, Cm, leak reversal and Ra fitted
  m1     passive control: leak density, Cm, leak reversal and Ra only
  fixed  M2 / M3 controls: channel densities taken from another fit's json, only Cm, leak reversal and Ra fitted
Writes <outdir>/fit.json (numbers, training sweeps only) and fit.npz (model traces for all 11 steps; no data), and
<outdir>/ckpt.pkl every 10 iterations (rerunning the same command resumes from it).
Scoring on the held-out data is a separate, single step (HANDOFF); nothing here reads or prints held-out values.
"""
import argparse, json, math, os, pickle, sys, time
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "src"))
sys.path.insert(0, os.path.dirname(__file__))
import numpy as np
import jax, jax.numpy as jnp
import optax
import jaxley as jx
from bioemu.morph import nml_to_swc
from bioemu.jx_membrane import make_membrane
from wormemu import nicoletti as lib
from fit_aiy import to_phys, to_theta

HOME = os.path.expanduser("~")
DATA = f"{HOME}/worm-data/ephys/naudin2022_liu_aiy_rim_afd/"
MORPHS = f"{HOME}/worm-data/morphologies/CElegansNeuroML/CElegans/generatedNeuroML2/"
CC = {"rim": ("Fig1A_RIM_CC.txt", 1), "afd": ("Fig1B_AFD_CC-IV_11steps.txt", 4)}  # file, bin (4 x 0.1 ms)
AMPS_PA = np.arange(-15, 36, 5)
TRAIN, HELD = [0, 2, 4, 6, 8, 10], [1, 3, 5, 7, 9]
DT, T, T0_LOSS, DS = 0.4, 8000.0, 200.0, 5  # ms; loss on 0.2-8 s every 2 ms

# Section 3 channel sets. Threshold-1-only genes get the 1e-10 lower bound (1e-10 S/cm2 counts as absent).
SETS = {"rim": ["leak", "egl19", "unc2", "cca1", "nca", "shl1", "kvs1", "egl2", "egl36", "kqt3", "unc103", "irk",
                "slo1egl19", "slo1unc2", "slo1iso", "slo2egl19", "slo2unc2", "slo2iso", "kcnl", "shk1"],
        "afd": ["leak", "egl19", "cca1", "shl1", "shk1", "kvs1", "egl2", "kqt1", "irk", "slo1egl19", "slo1iso",
                "slo2egl19", "slo2iso", "kcnl", "exp2", "kqt3", "egl36"]}  # exp2: amendment 01:58
THR1 = {"rim": {"shk1"}, "afd": {"kqt3", "egl36"}}
# Upper bounds (S/cm2): 10x the largest density any Nicoletti 2024 neuron model uses in the channel's class
# (inferred; read from the published *_simulation*.py files, nS / surface): Ca channels RIM cca1 8.45e-4; K
# channels AIY slo1iso 1.52e-3 (as SPIKE.md); leak AIY 2.1e-4; NCA AIY 9.1e-5.
CA = {"egl19", "unc2", "cca1"}
UB = {"leak": 2.1e-3, "nca": 9.1e-4}
UB_CA, UB_K = 8.45e-3, 1.52e-2
# Published RIM model (RIM_simulation.py; S/cm2 on 103.34 um2), start 0 of the RIM fit after rescaling to area.
RIM_PUB = dict(zip(["shl1", "egl2", "irk", "cca1", "unc2", "egl19", "leak"],
                   [0.0009048750067326097, 0.0001411644285181245, 0.0003272854640954744, 0.0008451919806776876,
                    9.676795045480941e-05, 0.00032005818627638106, 9.676795045480941e-05]))
RIM_SURF, RIM_EL, RIM_CM = 103.34e-8, -50.0, 1.5


def ub(c):
    return UB.get(c, UB_CA if c in CA else UB_K)


def load_cc(cell):
    f, b = CC[cell]
    a = np.genfromtxt(DATA + f, delimiter="\t", skip_header=3)
    t_ms, V = a[:, 0] * 1e3, a[:, 1:] * (1e3 if np.nanmax(np.abs(a[:, 1:])) < 1 else 1.0)
    if b > 1:  # 4-sample bins, 0.1 -> 0.4 ms (section 1)
        n = (len(t_ms) // b) * b
        t_ms, V = t_ms[:n].reshape(-1, b).mean(1), V[:n].reshape(-1, b, V.shape[1]).mean(1)
    grid = np.arange(0.0, T + DT / 2, DT)
    return grid, np.stack([np.interp(grid, t_ms, V[:, k]) for k in range(V.shape[1])])


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("outdir"); ap.add_argument("--cell", required=True); ap.add_argument("--model", default="full")
    ap.add_argument("--fixed"); ap.add_argument("--starts", type=int, default=16); ap.add_argument("--iters", type=int, default=300)
    ap.add_argument("--ncomp", type=int, default=2); ap.add_argument("--lr", type=float, default=0.1)
    a = ap.parse_args()
    os.makedirs(a.outdir, exist_ok=True)
    t_start = time.time()
    grid, Vd = load_cc(a.cell)
    Vd = Vd[TRAIN]  # the held-out sweeps are dropped here and never touched again
    v_init = float(np.mean(Vd[:, (grid >= T0_LOSS) & (grid < 1000.0)]))  # training baseline (inferred start)

    fixed = {}
    if a.model == "full":
        chans, fit_ch = SETS[a.cell], SETS[a.cell]
    elif a.model == "m1":
        chans, fit_ch = ["leak"], ["leak"]
    else:
        src = json.load(open(a.fixed))
        fixed = {k[len("Mem_g_"):]: v for k, v in src["params"].items() if k.startswith("Mem_g_")}
        chans, fit_ch = [c for c in lib.ALL_CHANNELS if c in fixed], []

    swc = f"/tmp/{a.cell}_{os.getpid()}.swc"
    nml_to_swc(MORPHS + ("RIML" if a.cell == "rim" else "AFDL") + ".cell.nml", swc)
    cell = jx.read_swc(swc, ncomp=a.ncomp)
    cell.insert(make_membrane(lib, channels=[c for c in lib.ALL_CHANNELS if c in chans])())
    nodes = cell.nodes
    nodes["Mem_sv"] = 2.0 / (nodes["radius"].values * 1e-4)  # cylinder S/V, 1/cm, each compartment's Ca pool
    for c, v in fixed.items():
        cell.set(f"Mem_g_{c}", v)
    cell.set("v", v_init)
    cell.init_states(delta_t=DT)
    soma = int(np.where(nodes["soma"].values)[0][0]) if "soma" in nodes.columns and nodes["soma"].any() else 0
    area = float(np.sum(2 * np.pi * nodes["radius"].values * nodes["length"].values)) * 1e-8  # cm2
    names = [f"Mem_g_{c}" for c in fit_ch] + ["capacitance", "Mem_eL", "axial_resistivity"]
    for n in names:
        cell.make_trainable(n, verbose=False)
    lo = np.array([1e-10 if c in THR1[a.cell] else 1e-7 for c in fit_ch] + [0.5, -100.0, 30.0])
    hi = np.array([ub(c) for c in fit_ch] + [2.0, -30.0, 300.0])
    logp = np.array([True] * len(fit_ch) + [False, False, True])
    site = cell.select(nodes=soma)
    site.record("v", verbose=False)
    info = {"cell": a.cell, "model": a.model, "fixed_from": a.fixed, "channels": chans, "fitted": names,
            "lo": lo.tolist(), "hi": hi.tolist(), "compartments": int(nodes.shape[0]), "area_um2": area * 1e8,
            "soma_node": soma, "v_init_mV": v_init, "device": str(jax.devices()[0]), "dt_ms": DT, "T_ms": T,
            "starts": a.starts, "iters": a.iters}
    print(json.dumps(info), flush=True)
    nsteps = int(round(T / DT)) + 1
    ck = [int(math.ceil(nsteps ** 0.5))] * 2
    idx = np.where(grid >= T0_LOSS)[0][::DS]
    target = jnp.asarray(Vd[:, idx])
    amps_tr = jnp.asarray(AMPS_PA[TRAIN] * 1e-3)  # nA
    lo_j, hi_j, logp_j = jnp.asarray(lo), jnp.asarray(hi), jnp.asarray(logp)

    def params_of(phys):
        return [{n: phys[i:i + 1]} for i, n in enumerate(names)]

    def sim(phys, amp, ckpt=None):
        ds = site.data_stimulate(jx.step_current(1000.0, 5000.0, amp, DT, T))
        return jx.integrate(cell, params=params_of(phys), data_stimuli=ds, delta_t=DT, checkpoint_lengths=ckpt)[0]

    def loss_one(theta):
        V = jax.vmap(lambda amp: sim(to_phys(theta, lo_j, hi_j, logp_j), amp, ck))(amps_tr)[:, idx]
        return jnp.mean((V - target) ** 2)

    def total(thetas):
        ls = jax.vmap(loss_one)(thetas)
        return jnp.sum(jnp.where(jnp.isfinite(ls), ls, 0.0)), ls

    vg = jax.jit(jax.value_and_grad(total, has_aux=True))
    rng = np.random.default_rng(0)
    th0 = rng.normal(0.0, 1.5, size=(a.starts, len(names)))
    if a.cell == "rim" and a.model == "full":  # start 0: published RIM densities rescaled to this area
        pub = [RIM_PUB[c] * RIM_SURF / area if c in RIM_PUB else 1e-6 for c in fit_ch] + [RIM_CM, RIM_EL, 100.0]
        th0[0] = to_theta(np.array(pub), lo, hi, logp)
    opt = optax.chain(optax.zero_nans(), optax.clip(5.0), optax.adam(optax.cosine_decay_schedule(a.lr, a.iters, alpha=0.1)))
    ckp = os.path.join(a.outdir, "ckpt.pkl")
    if os.path.exists(ckp):
        with open(ckp, "rb") as f:
            c = pickle.load(f)
        it0, thetas, st, best_l, best_th, hist, t_iter = c["it"], jnp.asarray(c["thetas"]), c["st"], c["best_l"], c["best_th"], c["hist"], c["t_iter"]
        t_start -= c["wall"]
        print(json.dumps({"resumed_at_it": it0}), flush=True)
    else:
        it0, thetas = 0, jnp.asarray(th0)
        st = opt.init(thetas)
        best_l, best_th, hist, t_iter = np.full(a.starts, np.inf), np.array(th0), [], []
    for it in range(it0, a.iters):
        t0 = time.time()
        (tot, ls), g = vg(thetas)
        ls = np.array(ls)
        dt_it = time.time() - t0
        if it > it0:
            t_iter.append(dt_it)
        better = np.isfinite(ls) & (ls < best_l)
        best_l[better] = ls[better]; best_th[better] = np.array(thetas)[better]
        upd, st = opt.update(g, st, thetas)
        thetas = optax.apply_updates(thetas, upd)
        hist.append(ls.tolist())
        if it % 10 == 0 or it == a.iters - 1:
            print(json.dumps({"it": it, "s_per_iter": round(dt_it, 3), "best_train_rmse_mV": round(float(np.sqrt(np.nanmin(best_l))), 3),
                              "median_rmse_mV": round(float(np.sqrt(np.nanmedian(ls))), 3), "n_nan": int((~np.isfinite(ls)).sum())}), flush=True)
            tmp = ckp + ".tmp"
            with open(tmp, "wb") as f:
                pickle.dump(dict(it=it + 1, thetas=np.array(thetas), st=jax.device_get(st), best_l=best_l, best_th=best_th,
                                 hist=hist, t_iter=t_iter, wall=time.time() - t_start), f)
            os.replace(tmp, ckp)
    fit_wall = time.time() - t_start
    b = int(np.nanargmin(best_l))
    phys = np.array(to_phys(jnp.asarray(best_th[b]), lo_j, hi_j, logp_j))
    s_it = float(np.median(t_iter)) if t_iter else float("nan")
    # model traces for all 11 steps (a prediction; compared with the held-out data only at scoring)
    fwd = jax.jit(jax.vmap(lambda amp: sim(jnp.asarray(phys), amp)))
    Vall = np.array(jax.block_until_ready(fwd(jnp.asarray(AMPS_PA * 1e-3))))
    rm = np.sqrt(np.mean((Vall[TRAIN][:, idx] - Vd[:, idx]) ** 2, axis=1))
    xs = np.where(logp, np.log(phys), phys)
    frac = (xs - np.where(logp, np.log(lo), lo)) / (np.where(logp, np.log(hi), hi) - np.where(logp, np.log(lo), lo))
    params = {n: float(v) for n, v in zip(names, phys)}
    params.update({f"Mem_g_{c}": float(v) for c, v in fixed.items()})
    res = dict(info, best_start=b, train_loss_mse=float(best_l[b]), params=params,
               at_bound=[n for n, f in zip(names, frac) if f < 0.01 or f > 0.99],
               train_rmse_mV={int(AMPS_PA[k]): round(float(r), 3) for k, r in zip(TRAIN, rm)},
               train_mean_rmse_mV=float(np.mean(rm)), start_train_rmse_mV=[round(float(np.sqrt(x)), 3) for x in best_l],
               fit_wall_s=fit_wall, s_per_grad_iter=s_it, grad_sims_per_s=a.starts * len(TRAIN) / s_it)
    print(json.dumps({k: res[k] for k in ["train_mean_rmse_mV", "fit_wall_s", "grad_sims_per_s", "at_bound"]}), flush=True)
    np.savez(os.path.join(a.outdir, "fit.npz"), grid=grid, Vfit=Vall, hist=np.array(hist), phys=phys, amps_pA=AMPS_PA)
    with open(os.path.join(a.outdir, "fit.json"), "w") as f:
        json.dump(res, f, indent=1)


if __name__ == "__main__":
    main()
