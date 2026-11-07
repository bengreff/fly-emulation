"""FIT2's held-out score (docs/worm/FIT2.md sections 3 and 4). The only code that opens the sealed class (RIM). It
runs once, after every registered fit is done, and refuses a second run.

    python scripts/worm/fit2_eval.py OUTDIR --open-sealed [--workers=8]
    python scripts/worm/fit2_eval.py OUTDIR --dry          # the code check: AIY stands in for RIM, nothing sealed

Scores on RIM's six FIT2 sweeps (indices 0, 2, ..., 10): each registered model at its best training parameters, the
optional generic cell if it finished, the brain as it stands (expression_map=on) and BAAIWorm as ported
(expression_map=off). The loss is fit2's (mean absolute feature error, mV); the RMSE over 1.2-7.0 s is reported
beside it. The falsifier (section 4): the true map is supported only if its RIM loss is below all four shuffles'.
Also reported, consistency only: the true fit's loss on AIY's odd sweeps (spent data). Writes OUTDIR/eval.json.
"""
from __future__ import annotations

import os

for _v in ("OMP_NUM_THREADS", "MKL_NUM_THREADS", "OPENBLAS_NUM_THREADS", "NUMBA_NUM_THREADS", "LP_NUM_THREADS",
           "VECLIB_MAXIMUM_THREADS", "NUMEXPR_NUM_THREADS"):
    os.environ.setdefault(_v, "1")

import json  # noqa: E402
import sys  # noqa: E402
import time  # noqa: E402
from pathlib import Path  # noqa: E402

import numpy as np  # noqa: E402

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "scripts" / "worm"))
import fit2 as F  # noqa: E402

HELD_OUT = "RIM"
RIM_FILE = "Fig1A_RIM_CC.txt"
ODD = [1, 3, 5, 7, 9]
RMSE_WIN = (1200, 7000)                                # ms


def read_naudin(f):
    """all 11 sweeps of a Naudin 2022 Fig 1A file on fit2's 0.4 ms grid (fit2.load_train's parser, no bins)"""
    a = np.genfromtxt(F.NAUDIN + f, delimiter="\t", skip_header=3)
    t_ms, V = a[:, 0] * 1e3, a[:, 1:] * (1e3 if np.nanmax(np.abs(a[:, 1:])) < 1 else 1.0)
    assert V.shape[1] == 11, (f, V.shape)
    grid = np.arange(0.0, F.T_END, F.DT_DATA)
    return grid, np.stack([np.interp(grid, t_ms, V[:, k]) for k in range(11)])


def rmse(t_data, V_data, V_model):
    """RMSE (mV) over RMSE_WIN; both smoothed 2 ms, the data taken at the model's 1 ms times"""
    t = np.arange(1, F.T_END + 1, dtype=float)
    Vd = F.smooth(V_data, t_data[1] - t_data[0])
    Vm = F.smooth(V_model, 1.0)
    w = (t >= RMSE_WIN[0]) & (t < RMSE_WIN[1])
    d = np.stack([np.interp(t[w], t_data, v) for v in Vd])
    return float(np.sqrt(np.mean((Vm[:, w] - d) ** 2)))


def score(feats, t_data, V_data, V_model, amps):
    fm = F.features(np.arange(1, F.T_END + 1, dtype=float), V_model, amps) if np.isfinite(V_model).all() else None
    if fm is None or not np.isfinite(fm).all():
        return dict(loss_mV=F.BAD, rmse_mV=None, features=None)
    return dict(loss_mV=float(np.mean(np.abs(fm - feats))), rmse_mV=rmse(t_data, V_data, V_model),
                features=np.round(fm, 2).tolist())


def job(args):
    """one simulation in a fresh process: a model's cell on the given sweeps"""
    name, cls, P, data, idx = args
    amps = F.AMPS_PA[idx]
    if name in ("on", "off"):
        import single_cell_sanity as S
        br = S.build(cells=[F.CELL[cls]], extra={"expression_map": name})
    else:
        F._init(name, [cls])
        br = F._W["br"]
        F.apply(br, F._W["map"], P)
    return score(data["feats"], data["t"], data["V"], F.simulate(br, amps)[0], amps)


def main(out, workers, dry=False):
    """dry: AIY's FIT2 sweeps stand in for RIM (training data, nothing sealed is read), template parameters stand in
    for unfinished fits, and nothing is marked spent; a check of this code before the one real run"""
    import multiprocessing as mp
    from wormemu import brain as B, excite_map as X
    from wormemu.brain_structure import load_structure
    missing = [m for m in F.MODELS if not (out / m / "best.json").exists()]
    if not dry and (missing or not (out / "ALL_DONE").exists()):
        sys.exit(f"not every registered fit is done (missing {missing}); RIM stays sealed")
    marker = out / "EVAL_OPENED"
    if not dry and marker.exists():
        sys.exit(f"the held-out class was already opened ({marker.read_text().strip()}); it is spent once")
    best = {m: json.loads((out / m / "best.json").read_text()) for m in F.MODELS + F.OPTIONAL
            if (out / m / "best.json").exists()}
    if dry:
        tmpl = X.Map(B.sample_worm(None).led, load_structure()).template()
        best = {m: best.get(m, dict(params=tmpl, train_loss_mV=None)) for m in F.MODELS}

    # the parser is fit2's: check it on AIY's FIT2 sweeps before it touches RIM
    t, V = read_naudin(F.TRAIN_CC["AIY"][1])
    assert np.array_equal(V[F.FIT2_SWEEPS], F.load_train("AIY")[1])
    aiy = dict(t=t, V=V[ODD], feats=F.features(t, V[ODD], F.AMPS_PA[ODD]))

    B._neuron()                                        # compile the mods once, before the workers spawn
    if dry:
        held, Vh = "AIY", V[F.FIT2_SWEEPS]
    else:
        marker.write_text(f"{time.ctime()} by fit2_eval.py\n")
        held = HELD_OUT
        t, V = read_naudin(RIM_FILE)
        Vh = V[F.FIT2_SWEEPS]                          # FIT2 may use only these; the odd sweeps stay sealed for W1
    rim = dict(t=t, V=Vh, feats=F.features(t, Vh, F.AMPS_PA[F.FIT2_SWEEPS]))

    keys = [(m, "RIM") for m in best] + [("on", "RIM"), ("off", "RIM"), ("true", "AIY_odd")]
    jobs = [(m, held, best[m]["params"] if m in best else None, rim, F.FIT2_SWEEPS) for m, _ in keys[:-1]] + \
           [("true", "AIY", best["true"]["params"], aiy, ODD)]
    ctx = mp.get_context("spawn")
    with ctx.Pool(min(workers, len(jobs)), maxtasksperchild=1) as pool:
        res = dict(zip(keys, pool.map(job, jobs)))

    loss = {m: r["loss_mV"] for (m, part), r in res.items() if part == "RIM"}
    shuf = [loss[m] for m in F.MODELS[1:]]
    supported = all(loss["true"] < v for v in shuf)
    verdict = ("supported: the true map's RIM loss is below all four shuffles'" if supported else
               "expression did not predict the held-out class better than shuffled expression; not adopted on this")
    rec = dict(held_out=held, dry=dry, sweeps=F.FIT2_SWEEPS, scored=time.ctime(), verdict=verdict,
               supported=supported, rim_loss_mV=loss,
               rim_rmse_mV={m: r["rmse_mV"] for (m, part), r in res.items() if part == "RIM"},
               rim_features_data=np.round(rim["feats"], 2).tolist(),
               rim_features_model={m: r["features"] for (m, part), r in res.items() if part == "RIM"},
               train_loss_mV={m: b["train_loss_mV"] for m, b in best.items()},
               aiy_odd_true=res[("true", "AIY_odd")])
    (out / ("eval_dry.json" if dry else "eval.json")).write_text(json.dumps(rec, indent=1))
    print(f"FIT2 held-out ({held}{', DRY: training data' if dry else ''}) loss, mV:")
    for m, v in loss.items():
        print(f"  {m:14s} {v:8.3f}   RMSE {rec['rim_rmse_mV'][m]}")
    print(f"  true map, AIY odd sweeps (spent, consistency): {rec['aiy_odd_true']['loss_mV']:.3f} mV")
    print("  " + verdict)


if __name__ == "__main__":
    opts = dict(a[2:].split("=", 1) for a in sys.argv if a.startswith("--") and "=" in a)
    dry = "--dry" in sys.argv
    if len(sys.argv) < 3 or not (dry or "--open-sealed" in sys.argv):
        sys.exit(__doc__)
    out = Path(sys.argv[1])
    out.mkdir(parents=True, exist_ok=True)
    main(out, int(opts.get("workers", 8)), dry=dry)
