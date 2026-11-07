"""FIT2 (docs/worm/FIT2.md): fit the expression-to-excitability map (src/wormemu/excite_map.py) to the training
classes' current clamp (AIY, AFD, AWA; RIM is the sealed held-out class and this script never opens its file).

    python scripts/worm/fit2.py run OUTDIR [--models=true,shuf20261108,...] [--workers=8]
    python scripts/worm/fit2.py status OUTDIR          # training progress only (no held-out data exists here)
    python scripts/worm/fit2.py bench                  # one evaluation's wall time at the template (no data)

Each model is one CMA-ES fit of the 19 map parameters (unit cube), population 16, sigma0 0.25, started at FIT2
section 5's start. The state is pickled every generation (OUTDIR/<model>/state.pkl) and a restart resumes from it;
OUTDIR/<model>/DONE when a fit stops, OUTDIR/ALL_DONE when every model has. Stopping rule (FIT2 section 5): 150
generations, < 0.1 mV best-loss improvement over 20 generations, tolfun 1e-3, tolx 1e-4, or 3 h of wall per fit.

CMA-ES: (mu/mu_w, lambda) with cumulative step-size adaptation and rank-one plus rank-mu covariance updates, as in
Hansen's tutorial (arXiv:1604.00772, Table 1 defaults), in numpy (the `cma` package is installed on neither machine).
Points outside the unit cube are evaluated at the clipped point plus 100 mV per unit squared distance.
"""
from __future__ import annotations

import os

for _v in ("OMP_NUM_THREADS", "MKL_NUM_THREADS", "OPENBLAS_NUM_THREADS", "NUMBA_NUM_THREADS", "LP_NUM_THREADS",
           "VECLIB_MAXIMUM_THREADS", "NUMEXPR_NUM_THREADS"):
    os.environ.setdefault(_v, "1")

import json  # noqa: E402
import pickle  # noqa: E402
import sys  # noqa: E402
import time  # noqa: E402
import zipfile  # noqa: E402
from pathlib import Path  # noqa: E402

import numpy as np  # noqa: E402

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "scripts" / "worm"))

HOME = os.path.expanduser("~")
NAUDIN = f"{HOME}/worm-data/ephys/naudin2022_liu_aiy_rim_afd/"
LIU = f"{HOME}/worm-data/liu2018_awa_ephys/Liu et al Figure 1.zip"
TRAIN_CC = {"AIY": ("naudin", "Fig1A_AIY_CC.txt", 1), "AFD": ("naudin", "Fig1B_AFD_CC-IV_11steps.txt", 4),
            "AWA": ("liu", "Figure 1/Fig 1A_AWA Current-Clamp Trace.txt", 1)}
CELL = {"AIY": "AIYL", "AFD": "AFDL", "AWA": "AWAL", "RIM": "RIML"}
AMPS_PA = np.arange(-15, 36, 5)
FIT2_SWEEPS = [0, 2, 4, 6, 8, 10]                     # FIT2 section 2: the only sweeps FIT2 uses, every class
T_ON, T_OFF, T_END, T_SETTLE = 1000, 6000, 7000, 2000  # ms
WIN = {"base": (500, 1000), "early": (1000, 1500), "ss": (5000, 6000), "post": (6050, 6550)}
DT_DATA, SMOOTH_MS = 0.4, 2.0
BAD = 1000.0                                          # mV, a non-finite trace
POP, SIGMA0, MAX_GEN, PLATEAU, PLATEAU_MV, TOLFUN, TOLX, WALL_S = 16, 0.25, 150, 20, 0.1, 1e-3, 1e-4, 3 * 3600
MODELS = ["true", "shuf20261108", "shuf20261109", "shuf20261110", "shuf20261111"]   # registered order
OPTIONAL = ["generic"]


# --- data (training classes only) -----------------------------------------------------------------------------------
def load_train(cls):
    src, f, b = TRAIN_CC[cls]
    assert cls != "RIM", "RIM is FIT2's sealed held-out class"
    if src == "naudin":
        a = np.genfromtxt(NAUDIN + f, delimiter="\t", skip_header=3)
    else:
        with zipfile.ZipFile(LIU) as z:
            a = np.genfromtxt(z.open(f), delimiter="\t")        # this file has no header rows
    t_ms, V = a[:, 0] * 1e3, a[:, 1:] * (1e3 if np.nanmax(np.abs(a[:, 1:])) < 1 else 1.0)
    if b > 1:                                                # 4-sample bins, 0.1 -> 0.4 ms (as W1)
        n = (len(t_ms) // b) * b
        t_ms, V = t_ms[:n].reshape(-1, b).mean(1), V[:n].reshape(-1, b, V.shape[1]).mean(1)
    assert V.shape[1] == 11, (cls, V.shape)
    grid = np.arange(0.0, T_END, DT_DATA)
    Vg = np.stack([np.interp(grid, t_ms, V[:, k]) for k in FIT2_SWEEPS])
    return grid, Vg


def smooth(V, dt):
    k = max(1, int(round(SMOOTH_MS / dt)))
    if k == 1:
        return V
    ker = np.ones(k) / k
    return np.stack([np.convolve(v, ker, mode="same") for v in V])


def features(t, V, amps):
    """[sweep, 4] features (FIT2 section 3): baseline, early peak in the step's direction, steady state, after-step"""
    V = smooth(V, t[1] - t[0])
    out = np.empty((len(amps), 4))
    for i, a in enumerate(amps):
        def w(name):
            lo, hi = WIN[name]
            return V[i, (t >= lo) & (t < hi)]
        e = w("early")
        out[i] = (w("base").mean(), e.max() if a > 0 else e.min(), w("ss").mean(), w("post").mean())
    return out


# --- the model (one Brain per worker process) ---------------------------------------------------------------------
_W = {}


def _init(model, classes):
    from wormemu import excite_map as X
    import single_cell_sanity as S
    X.INSERT_ALL = True
    X.SHUFFLE = int(model[4:]) if model.startswith("shuf") else None
    X.GENERIC = model == "generic"
    X.PARAMS = None
    br = S.build(cells=[CELL[c] for c in classes], extra={"expression_map": "fit2", "awa_membrane": "baaiworm"})
    m, _ = X.for_brain(br)
    _W.update(br=br, map=m, classes=classes, model=model)


def apply(br, m, P):
    from wormemu import brain as B
    h = br.h
    for name, cell, soma in zip(br.cell_names, br.cells, br.soma):
        d = m.cell(name, P)
        for seg in soma:
            for ch in B.CHANNELS[:-1]:
                setattr(getattr(seg, ch), B.GB.get(ch, f"gb{ch}"), d[ch])
            for ch in ("kqt1", "unc103", "exp2", "slo1iso", "slo2iso"):
                getattr(seg, ch).gbar = d[ch]
        for sec in cell.all:
            part = "soma" if "Soma" in sec.name() else "neurite"
            for seg in sec:
                seg.pas.g, seg.pas.e = d[f"gpas_{part}"], d["epas"]
    for name, (cells, pv, base, cur) in br._gt.items():   # reset() restores these bases: take the new values
        buf = h.Vector(len(cells))
        pv.gather(buf)
        base[:] = buf.as_numpy()


def simulate(br, amps):
    """V [cell, sweep, 7000] at 1 ms, each sweep from a fresh reset after 2 s at 0 pA"""
    n = len(br.cell_names)
    V = np.empty((n, len(amps), T_END))
    for i, a in enumerate(amps):
        br.reset()
        br.extra_pA[:] = 0.0
        for _ in range(T_SETTLE):
            br.step(None, 1.0)
        for k in range(T_END):
            br.extra_pA[:] = a if T_ON <= k < T_OFF else 0.0
            V[:, i, k] = br.step(None, 1.0).v_mV
        br.extra_pA[:] = 0.0
    return V


def model_features(P):
    br, m = _W["br"], _W["map"]
    apply(br, m, P)
    amps = AMPS_PA[FIT2_SWEEPS]
    V = simulate(br, amps)
    t = np.arange(1, T_END + 1, dtype=float)                 # step output at the end of each 1 ms step
    fin = np.isfinite(V).all(axis=(1, 2))
    return [features(t, V[c], amps) if fin[c] else None for c in range(len(br.cell_names))]


def evaluate(args):
    x, data_feats = args
    m = _W["map"]
    xc = np.clip(x, 0.0, 1.0)
    pen = 100.0 * float(np.sum((x - xc) ** 2))
    P = m.from_unit(xc)
    fm = model_features(P)
    per = []
    for c, cls in enumerate(_W["classes"]):
        per.append(BAD if fm[c] is None or not np.isfinite(fm[c]).all()
                   else float(np.mean(np.abs(fm[c] - data_feats[cls]))))
    return float(np.mean(per)) + pen, per


# --- CMA-ES (Hansen's tutorial, Table 1) ----------------------------------------------------------------------------
def cma_new(x0, sigma0, lam, seed):
    n = len(x0)
    mu = lam // 2
    w = np.log(mu + 0.5) - np.log(np.arange(1, mu + 1))
    w /= w.sum()
    mueff = 1.0 / np.sum(w ** 2)
    cc = (4 + mueff / n) / (n + 4 + 2 * mueff / n)
    cs = (mueff + 2) / (n + mueff + 5)
    c1 = 2 / ((n + 1.3) ** 2 + mueff)
    cmu = min(1 - c1, 2 * (mueff - 2 + 1 / mueff) / ((n + 2) ** 2 + mueff))
    damps = 1 + 2 * max(0.0, np.sqrt((mueff - 1) / (n + 1)) - 1) + cs
    return dict(n=n, lam=lam, mu=mu, w=w, mueff=mueff, cc=cc, cs=cs, c1=c1, cmu=cmu, damps=damps,
                chiN=np.sqrt(n) * (1 - 1 / (4 * n) + 1 / (21 * n * n)), mean=np.array(x0, float), sigma=sigma0,
                C=np.eye(n), pc=np.zeros(n), ps=np.zeros(n), gen=0, rng=np.random.default_rng(seed),
                best_x=None, best_f=np.inf, best_per=None, hist=[], evals=0, wall_s=0.0, stop=None)


def cma_ask(s):
    ev, B = np.linalg.eigh(s["C"])
    ev = np.maximum(ev, 1e-20)
    s["_B"], s["_D"] = B, np.sqrt(ev)
    z = s["rng"].standard_normal((s["lam"], s["n"]))
    y = z * s["_D"] @ B.T
    return s["mean"] + s["sigma"] * y


def cma_tell(s, X, f):
    n, mu, w = s["n"], s["mu"], s["w"]
    order = np.argsort(f)
    old = s["mean"].copy()
    xs = X[order[:mu]]
    s["mean"] = w @ xs
    y = (xs - old) / s["sigma"]
    yw = w @ y
    B, D = s["_B"], s["_D"]
    Cinvsqrt = B @ np.diag(1 / D) @ B.T
    s["ps"] = (1 - s["cs"]) * s["ps"] + np.sqrt(s["cs"] * (2 - s["cs"]) * s["mueff"]) * Cinvsqrt @ yw
    hsig = float(np.linalg.norm(s["ps"]) / np.sqrt(1 - (1 - s["cs"]) ** (2 * (s["gen"] + 1))) / s["chiN"]
                 < 1.4 + 2 / (n + 1))
    s["pc"] = (1 - s["cc"]) * s["pc"] + hsig * np.sqrt(s["cc"] * (2 - s["cc"]) * s["mueff"]) * yw
    dh = (1 - hsig) * s["cc"] * (2 - s["cc"])
    s["C"] = ((1 + s["c1"] * dh - s["c1"] - s["cmu"]) * s["C"] + s["c1"] * np.outer(s["pc"], s["pc"])
              + s["cmu"] * (y.T * w) @ y)
    s["C"] = (s["C"] + s["C"].T) / 2
    s["sigma"] *= np.exp((s["cs"] / s["damps"]) * (np.linalg.norm(s["ps"]) / s["chiN"] - 1))
    s["gen"] += 1


def stop_reason(s, fgen):
    if s["gen"] >= MAX_GEN:
        return "max generations"
    b = [h["best_f"] for h in s["hist"]]
    if len(b) > PLATEAU and b[-PLATEAU - 1] - b[-1] < PLATEAU_MV:
        return f"plateau (< {PLATEAU_MV} mV over {PLATEAU} generations)"
    if len(b) > 10 and max(max(fgen), max(b[-10:])) - min(min(fgen), min(b[-10:])) < TOLFUN:
        return "tolfun"
    if s["sigma"] * np.sqrt(np.max(np.diag(s["C"]))) < TOLX:
        return "tolx"
    if s["wall_s"] >= WALL_S:
        return "wall cap"
    return None


def save(path, obj):
    tmp = path.with_suffix(".tmp")
    with open(tmp, "wb") as f:
        pickle.dump(obj, f)
    os.replace(tmp, path)


# --- driver ---------------------------------------------------------------------------------------------------------
def fit_one(out, model, classes, data_feats, workers):
    import multiprocessing as mp
    d = out / model
    d.mkdir(parents=True, exist_ok=True)
    if (d / "DONE").exists():
        print(model, "already done", flush=True)
        return
    from wormemu import brain as B, excite_map as X
    from wormemu.brain_structure import load_structure
    m = X.Map(B.sample_worm(None).led, load_structure(), shuffle=int(model[4:]) if model.startswith("shuf") else None,
              generic=model == "generic")
    if (d / "state.pkl").exists():
        s = pickle.load(open(d / "state.pkl", "rb"))
        print(model, f"resumed at generation {s['gen']}, best {s['best_f']:.3f} mV", flush=True)
    else:
        x0 = m.to_unit({**{n: (m.bounds[n][0] + m.bounds[n][1]) / 2 for n in X.NAMES}, "b": 0.5,
                        "e_leak": m.e_template})
        s = cma_new(x0, SIGMA0, POP, 20261107 + (MODELS + OPTIONAL).index(model))
        (d / "meta.json").write_text(json.dumps(dict(model=model, classes=classes, names=X.NAMES,
                                                     bounds={n: m.bounds[n] for n in X.NAMES}, x0=x0.tolist(),
                                                     pop=POP, sigma0=SIGMA0, started=time.ctime()), indent=1))
    ctx = mp.get_context("spawn")
    with ctx.Pool(workers, initializer=_init, initargs=(model, classes)) as pool:
        while s["stop"] is None:
            t0 = time.time()
            X_ = cma_ask(s)
            res = pool.map(evaluate, [(x, data_feats) for x in X_])
            f = np.array([r[0] for r in res])
            k = int(np.argmin(f))
            if f[k] < s["best_f"]:
                s["best_f"], s["best_x"], s["best_per"] = float(f[k]), np.clip(X_[k], 0, 1).copy(), res[k][1]
            cma_tell(s, X_, f)
            s["evals"] += len(f)
            s["wall_s"] += time.time() - t0
            s["hist"].append(dict(gen=s["gen"], best_f=s["best_f"], gen_min=float(f.min()), gen_median=float(np.median(f)),
                                  sigma=float(s["sigma"]), wall_s=round(s["wall_s"], 1), t=time.ctime()))
            s["stop"] = stop_reason(s, f)
            save(d / "state.pkl", s)
            with open(d / "hist.jsonl", "a") as fh:
                fh.write(json.dumps({**s["hist"][-1], "best_per": s["best_per"]}) + "\n")
            print(f"{model} gen {s['gen']}: best {s['best_f']:.3f} mV {np.round(s['best_per'], 2).tolist()} "
                  f"gen min {f.min():.3f} sigma {s['sigma']:.3f} {time.time() - t0:.0f} s", flush=True)
    P = m.from_unit(s["best_x"])
    (d / "best.json").write_text(json.dumps(dict(model=model, params=P, unit=s["best_x"].tolist(),
                                                 train_loss_mV=s["best_f"],
                                                 train_loss_per_class_mV=dict(zip(classes, s["best_per"])),
                                                 generations=s["gen"], evals=s["evals"], stop=s["stop"],
                                                 wall_s=s["wall_s"], finished=time.ctime()), indent=1))
    (d / "DONE").write_text(time.ctime() + "\n")


def run(out, models, workers):
    from wormemu import brain as B
    B._neuron()                                        # compile the mods once, before the workers spawn
    classes = ["AIY", "AFD", "AWA"]
    data_feats = {}
    for c in classes:
        t, V = load_train(c)
        data_feats[c] = features(t, V, AMPS_PA[FIT2_SWEEPS])
    np.savez(out / "train_features.npz", **data_feats)
    for model in models:
        fit_one(out, model, classes, data_feats, workers)
    if all((out / mdl / "DONE").exists() for mdl in MODELS):
        (out / "ALL_DONE").write_text(time.ctime() + "\n")


def status(out):
    print("FIT2 status", time.ctime(), out)
    for model in MODELS + OPTIONAL:
        d = out / model
        if not (d / "hist.jsonl").exists():
            print(f"  {model:14s} not started")
            continue
        h = [json.loads(x) for x in open(d / "hist.jsonl")][-1]
        st = "DONE " + json.loads((d / "best.json").read_text())["stop"] if (d / "DONE").exists() else "running"
        print(f"  {model:14s} gen {h['gen']:3d}  best train loss {h['best_f']:.3f} mV  per class (AIY, AFD, AWA) "
              f"{[round(v, 2) for v in h['best_per']]}  sigma {h['sigma']:.3f}  wall {h['wall_s'] / 60:.0f} min  {st}  "
              f"(last {h['t']})")
    print("  ALL_DONE" if (out / "ALL_DONE").exists() else "  not all done")


def bench():
    _init("true", ["AIY", "AFD", "AWA"])
    m = _W["map"]
    t0 = time.time()
    fm = model_features(m.template())
    print(f"one evaluation (3 cells x 6 sweeps x 9 s): {time.time() - t0:.1f} s wall")
    for c, f in zip(["AIY", "AFD", "AWA"], fm):
        print(c, None if f is None else np.round(f, 1).tolist())


if __name__ == "__main__":
    cmd = sys.argv[1]
    opts = dict(a[2:].split("=", 1) for a in sys.argv if a.startswith("--") and "=" in a)
    if cmd == "bench":
        bench()
    else:
        out = Path(sys.argv[2])
        out.mkdir(parents=True, exist_ok=True)
        if cmd == "status":
            status(out)
        elif cmd == "run":
            run(out, opts.get("models", ",".join(MODELS)).split(","), int(opts.get("workers", 8)))
