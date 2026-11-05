"""THE SPIKE: fit a multicompartment AIY model (CeNGEN channel set, Nicoletti 2024 kinetics) to the Naudin 2022
current-clamp traces with gradients on the GPU, then score it on the held-out data. Pre-registration and bars:
docs/worm/SPIKE.md (do not change the split, windows or bounds here without a new labelled experiment).

usage: fit_aiy.py <outdir> [--model cengen|pub] [--starts 16] [--iters 300] [--ncomp 2]
Writes <outdir>/fit_<model>.json (numbers) and fit_<model>.npz (traces, I-V) plus progress lines on stdout.
"""
import argparse, json, math, os, sys, time
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "src"))
import numpy as np
import jax, jax.numpy as jnp
import optax
import jaxley as jx
from bioemu.morph import nml_to_swc
from bioemu.jx_membrane import make_membrane
from wormemu import nicoletti as lib

HOME = os.path.expanduser("~")
DATA = f"{HOME}/worm-data/ephys/naudin2022_liu_aiy_rim_afd/"
MORPH = f"{HOME}/worm-data/morphologies/CElegansNeuroML/CElegans/generatedNeuroML2/AIYL.cell.nml"
AMPS_PA = np.arange(-15, 36, 5)
TRAIN, HELD = [0, 2, 4, 6, 8, 10], [1, 3, 5, 7, 9]
DT, T, T0_LOSS, DS = 0.4, 8000.0, 200.0, 5  # ms; loss on 0.2-8 s every 2 ms
V_INIT = -54.0  # mV, start of the simulation (data baseline mean is -53.9 mV)

MODELS = {"cengen": ["leak", "nca", "egl19", "unc2", "kqt1", "slo1egl19", "slo1unc2", "slo1iso", "slo2egl19",
                     "slo2unc2", "slo2iso", "kcnl"],
          "pub": ["leak", "nca", "egl19", "kqt1", "shl1", "slo1egl19", "slo1iso"]}
# Upper bounds (S/cm2): 10x the largest density any Nicoletti 2024 neuron uses for the channel or its class
# (inferred). AIY 65.89 um2: slo1iso 1.52e-3, slo1egl19 1.40e-3; RIM egl19 3.2e-4; AIY nca 9.1e-5, leak 2.1e-4.
UB = {"leak": 2.1e-3, "nca": 9.1e-4, "egl19": 3.2e-3, "unc2": 3.2e-3}
LO = 1e-7
PUB_NS = {"leak": 0.14, "slo1iso": 1, "kqt1": 0.2, "egl19": 0.1, "slo1egl19": 0.92, "nca": 0.06, "shl1": 0.5}
PUB = dict(eL=-89.57, cm=1.6, surf=65.89e-8, vol=7.42e-12)


def load_cc():
    a = np.genfromtxt(DATA + "Fig1A_AIY_CC.txt", delimiter="\t", skip_header=3)
    t_ms, V = a[:, 0] * 1e3, a[:, 1:] * (1e3 if np.nanmax(np.abs(a[:, 1:])) < 1 else 1.0)
    grid = np.arange(0.0, T + DT / 2, DT)
    return grid, np.stack([np.interp(grid, t_ms, V[:, k]) for k in range(V.shape[1])])


def load_iv():
    import openpyxl
    ws = openpyxl.load_workbook(DATA + "Fig1_IVcurves_AFD_RIM_AIY.xlsx", data_only=True).active
    rows = [r for r in ws.iter_rows(values_only=True)]
    out, cur = {"peak": [], "ss": []}, "peak"
    for r in rows[2:]:
        if r[0] == "Steady state":
            cur = "ss"; continue
        if isinstance(r[0], (int, float)) and isinstance(r[7], (int, float)):
            out[cur].append((r[0] * 1e3, r[7], r[8] * 1e12, r[9] * 1e12))  # mV, n, pA mean, pA SEM
    return {k: np.array(v) for k, v in out.items()}


def build_cell(ncomp, model):
    swc = "/tmp/AIYL.swc"
    nml_to_swc(MORPH, swc)
    cell = jx.read_swc(swc, ncomp=ncomp)
    cell.insert(make_membrane(lib)())
    nodes = cell.nodes
    nodes["Mem_sv"] = 2.0 / (nodes["radius"].values * 1e-4)  # cylinder S/V, 1/cm, for each compartment's Ca pool
    cell.set("v", V_INIT)
    cell.init_states(delta_t=DT)
    soma = int(np.where(nodes["soma"].values)[0][0]) if "soma" in nodes.columns and nodes["soma"].any() else 0
    area_cm2 = float(np.sum(2 * np.pi * nodes["radius"].values * nodes["length"].values)) * 1e-8
    names = [f"Mem_g_{c}" for c in MODELS[model]] + ["capacitance", "Mem_eL", "axial_resistivity"]
    for n in names:
        cell.make_trainable(n, verbose=False)
    lo = np.array([LO] * len(MODELS[model]) + [0.5, -100.0, 30.0])
    hi = np.array([UB.get(c, 1.5e-2) for c in MODELS[model]] + [2.0, -30.0, 300.0])
    logp = np.array([True] * len(MODELS[model]) + [False, False, True])
    return cell, soma, area_cm2, names, lo, hi, logp


def to_phys(theta, lo, hi, logp):
    s = jax.nn.sigmoid(theta)
    llo, lhi = jnp.where(logp, jnp.log(lo), lo), jnp.where(logp, jnp.log(hi), hi)
    x = llo + (lhi - llo) * s
    return jnp.where(logp, jnp.exp(x), x)


def to_theta(phys, lo, hi, logp):
    np.seterr(invalid="ignore")  # np.where evaluates log() of the linear (negative) entries too; they are discarded
    llo, lhi = np.where(logp, np.log(lo), lo), np.where(logp, np.log(hi), hi)
    x = np.where(logp, np.log(phys), phys)
    s = np.clip((x - llo) / (lhi - llo), 1e-4, 1 - 1e-4)
    return np.log(s / (1 - s))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("outdir"); ap.add_argument("--model", default="cengen"); ap.add_argument("--starts", type=int, default=16)
    ap.add_argument("--iters", type=int, default=300); ap.add_argument("--ncomp", type=int, default=2)
    ap.add_argument("--lr", type=float, default=0.1)
    a = ap.parse_args()
    os.makedirs(a.outdir, exist_ok=True)
    t_start = time.time()
    grid, Vd = load_cc()
    cell, soma, area, names, lo, hi, logp = build_cell(a.ncomp, a.model)
    site = cell.select(nodes=soma)
    site.record("v", verbose=False)
    ncomp_tot = int(cell.nodes.shape[0])
    info = {"model": a.model, "channels": MODELS[a.model], "compartments": ncomp_tot, "area_um2": area * 1e8,
            "soma_node": soma, "device": str(jax.devices()[0]), "dt_ms": DT, "T_ms": T, "starts": a.starts, "iters": a.iters}
    print(json.dumps(info), flush=True)
    nsteps = int(round(T / DT)) + 1
    ck = [int(math.ceil(nsteps ** 0.5))] * 2
    win = (grid >= T0_LOSS)
    idx = np.where(win)[0][::DS]
    target = jnp.asarray(Vd[TRAIN][:, idx])
    amps_tr = jnp.asarray(AMPS_PA[TRAIN] * 1e-3)  # nA
    lo_j, hi_j, logp_j = jnp.asarray(lo), jnp.asarray(hi), jnp.asarray(logp)

    def params_of(phys):
        return [{n: phys[i:i + 1]} for i, n in enumerate(names)]

    def sim(phys, amp, ckpt=None):
        stim = jx.step_current(1000.0, 5000.0, amp, DT, T)
        ds = site.data_stimulate(stim)
        return jx.integrate(cell, params=params_of(phys), data_stimuli=ds, delta_t=DT, checkpoint_lengths=ckpt)[0]

    def loss_one(theta):
        phys = to_phys(theta, lo_j, hi_j, logp_j)
        V = jax.vmap(lambda amp: sim(phys, amp, ck))(amps_tr)[:, idx]
        return jnp.mean((V - target) ** 2)

    def total(thetas):
        ls = jax.vmap(loss_one)(thetas)
        ok = jnp.isfinite(ls)
        return jnp.sum(jnp.where(ok, ls, 0.0)), ls

    vg = jax.jit(jax.value_and_grad(total, has_aux=True))
    # starts: 0 = published AIY densities rescaled to this morphology's area (same total conductance), rest random
    rng = np.random.default_rng(0)
    th0 = rng.normal(0.0, 1.5, size=(a.starts, len(names)))
    pub_phys = [PUB_NS.get(c, 0.0) * 1e-9 / area if PUB_NS.get(c, 0.0) > 0 else 1e-6 for c in MODELS[a.model]]
    pub_phys += [PUB["cm"], PUB["eL"], 100.0]
    th0[0] = to_theta(np.array(pub_phys), lo, hi, logp)
    thetas = jnp.asarray(th0)
    opt = optax.chain(optax.zero_nans(), optax.clip(5.0), optax.adam(optax.cosine_decay_schedule(a.lr, a.iters, alpha=0.1)))
    st = opt.init(thetas)
    best_l = np.full(a.starts, np.inf); best_th = np.array(th0)
    hist, t_iter = [], []
    for it in range(a.iters):
        t0 = time.time()
        (tot, ls), g = vg(thetas)
        ls = np.array(ls)
        dt_it = time.time() - t0
        if it > 0:
            t_iter.append(dt_it)
        better = np.isfinite(ls) & (ls < best_l)
        best_l[better] = ls[better]; best_th[better] = np.array(thetas)[better]
        upd, st = opt.update(g, st, thetas)
        thetas = optax.apply_updates(thetas, upd)
        hist.append(ls.tolist())
        if it % 10 == 0 or it == a.iters - 1:
            print(json.dumps({"it": it, "s_per_iter": round(dt_it, 3), "best_rmse_mV": round(float(np.sqrt(np.nanmin(best_l))), 3),
                              "median_rmse_mV": round(float(np.sqrt(np.nanmedian(ls))), 3), "n_nan": int((~np.isfinite(ls)).sum())}), flush=True)
    fit_wall = time.time() - t_start
    b = int(np.nanargmin(best_l))
    phys = np.array(to_phys(jnp.asarray(best_th[b]), lo_j, hi_j, logp_j))
    s_it = float(np.median(t_iter)) if t_iter else float("nan")
    grad_sims_per_s = a.starts * len(TRAIN) / s_it

    # ---- scoring on all 11 steps (forward), float32 as fitted --------------------------------------------
    allamps = jnp.asarray(AMPS_PA * 1e-3)
    fwd = jax.jit(jax.vmap(lambda amp: sim(jnp.asarray(phys), amp)))
    Vall = np.array(fwd(allamps)); jax.block_until_ready(Vall)
    t0 = time.time(); Vall = np.array(jax.block_until_ready(fwd(allamps))); t_fwd = time.time() - t0
    rm = np.sqrt(np.mean((Vall[:, idx] - Vd[:, idx]) ** 2, axis=1))
    xs = np.where(logp, np.log(phys), phys)
    frac = (xs - np.where(logp, np.log(lo), lo)) / (np.where(logp, np.log(hi), hi) - np.where(logp, np.log(lo), lo))
    res = dict(info, best_start=b, train_loss_mse=float(best_l[b]),
               params={n: float(v) for n, v in zip(names, phys)},
               at_bound=[n for n, f in zip(names, frac) if f < 0.01 or f > 0.99],
               rmse_mV={int(AMPS_PA[k]): round(float(rm[k]), 3) for k in range(11)},
               train_mean_rmse_mV=float(np.mean(rm[TRAIN])), held_mean_rmse_mV=float(np.mean(rm[HELD])),
               held_max_rmse_mV=float(np.max(rm[HELD])), start_train_rmse_mV=[round(float(np.sqrt(x)), 3) for x in best_l],
               fit_wall_s=fit_wall, s_per_grad_iter=s_it, grad_sims_per_s=grad_sims_per_s,
               fwd_11_s=t_fwd, fwd_sims_per_s=11 / t_fwd, bio_s_per_sim=T / 1e3)
    print(json.dumps({k: res[k] for k in ["train_mean_rmse_mV", "held_mean_rmse_mV", "held_max_rmse_mV", "fit_wall_s", "grad_sims_per_s"]}), flush=True)
    np.savez(os.path.join(a.outdir, f"fit_{a.model}.npz"), grid=grid, Vd=Vd, Vfit=Vall, hist=np.array(hist), phys=phys)
    with open(os.path.join(a.outdir, f"fit_{a.model}.json"), "w") as f:
        json.dump(res, f, indent=1)


if __name__ == "__main__":
    main()
