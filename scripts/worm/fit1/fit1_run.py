"""Fit 1 driver (docs/worm/FIT1.md): CMA-ES (pycma) over the FIT vector in its unbounded coordinates (fit1_core:
a sigmoid onto each value's ledger range, on log scale for rates and conductances), starting at the template.

Each generation: one seeded mini-batch of training stimulations (the same batches for the main fit and the wrong
model), every candidate evaluated on it by a worker process pinned to one CPU, the reduced chi-square told to CMA.
Checkpointed every generation in OUT: state.pkl (the pickled strategy), gen_NNNN/ (the asked candidates, jobs and
results), history.csv (one line per generation), mean.json (the strategy mean as values). Resumable: rerun the same
command; a generation in progress reuses its asked candidates and finished evaluations. Stops at the stopping rule
(FIT1.md) and writes DONE with the reason; a file OUT/STOP makes it stop after the current generation. PIDs: OUT/driver.pid,
OUT/pids.txt (every worker, with its job).

    python fit1_run.py OUT --train train.npz --cpus 0-7 [--shuffle-seed 1] [--pop 16 --batch 4 ...]
"""
import argparse
import csv
import json
import os
import pickle
import subprocess
import sys
import time
from pathlib import Path

import numpy as np

import cma
import fit1_core as fc
import fit1_loss as fl

HERE = Path(__file__).resolve().parent
CAP = {k: "1" for k in ("OMP_NUM_THREADS", "MKL_NUM_THREADS", "OPENBLAS_NUM_THREADS", "NUMBA_NUM_THREADS",
                        "LP_NUM_THREADS", "VECLIB_MAXIMUM_THREADS", "NUMEXPR_NUM_THREADS")}
KEYS = ("train", "shuffle_seed", "pop", "batch", "sigma0", "seed", "h_dt", "mech_dt", "window_s", "warm_s",
        "pulse_ms", "toggles")


def cpus(s):
    out = []
    for part in s.split(","):
        a, _, b = part.partition("-")
        out += list(range(int(a), int(b or a) + 1))
    return out


class Log:
    def __init__(self, path):
        self.f = open(path, "a")

    def __call__(self, msg):
        line = time.strftime("%Y-%m-%d %H:%M:%S ") + msg
        print(line, flush=True)
        self.f.write(line + "\n")
        self.f.flush()


def run_jobs(jobs, cpu_list, out, log):
    """jobs: [(job json path, result npz path)]; at most one per CPU at once; a failed job is retried once."""
    pending = [j for j in jobs if not Path(j[1]).exists()]
    free, running, tries = list(cpu_list), {}, {}
    env = {**os.environ, **CAP}
    while pending or running:
        while pending and free:
            jp, op = pending.pop(0)
            cpu = free.pop(0)
            lf = open(str(jp) + ".log", "w")
            p = subprocess.Popen(["taskset", "-c", str(cpu), sys.executable, str(HERE / "fit1_worker.py"), str(jp)],
                                 stdout=lf, stderr=subprocess.STDOUT, env=env)
            with open(out / "pids.txt", "a") as f:
                f.write(f"{p.pid} {cpu} {jp}\n")
            running[p.pid] = (p, cpu, jp, op, lf)
        time.sleep(2)
        for pid, (p, cpu, jp, op, lf) in list(running.items()):
            if p.poll() is None:
                continue
            lf.close()
            free.append(cpu)
            del running[pid]
            if p.returncode != 0 or not Path(op).exists():
                tries[jp] = tries.get(jp, 0) + 1
                log(f"job {jp} exit {p.returncode} (try {tries[jp]})")
                if tries[jp] <= 1:
                    pending.append((jp, op))


def batch_for(train, g, k, seed):
    return sorted(np.random.default_rng([seed, g]).choice(train, k, replace=False).tolist())


def stop_reason(a, es, g, hist):
    if Path(a.out, "STOP").exists():
        return "STOP file"
    if g >= a.max_gens:
        return f"generation budget {a.max_gens}"
    if a.deadline and time.time() > time.mktime(time.strptime(a.deadline, "%Y-%m-%dT%H:%M")):
        return f"deadline {a.deadline}"
    st = es.stop()
    if st:
        return "cma: " + json.dumps({k: str(v) for k, v in st.items()})
    W = a.plateau
    if g >= max(a.min_gens, 2 * W) and len(hist) >= 2 * W:
        med = np.array([float(h["median"]) for h in hist])
        last, prev = med[-W:].mean(), med[-2 * W:-W].mean()
        if last > (1.0 - a.plateau_tol) * prev:
            return f"plateau: mean median loss of the last {W} generations {last:.4g} vs the {W} before {prev:.4g}"
    return None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("out")
    ap.add_argument("--train", required=True)
    ap.add_argument("--cpus", default="0-7")
    ap.add_argument("--shuffle-seed", type=int, default=None)
    ap.add_argument("--pop", type=int, default=16)
    ap.add_argument("--batch", type=int, default=4)
    ap.add_argument("--sigma0", type=float, default=1.0)
    ap.add_argument("--seed", type=int, default=20261106)
    ap.add_argument("--h-dt", type=float, default=0.5)
    ap.add_argument("--mech-dt", type=float, default=10.0)
    ap.add_argument("--window-s", type=float, default=30.0)
    ap.add_argument("--warm-s", type=float, default=5.0)
    ap.add_argument("--pulse-ms", type=float, default=500.0)
    ap.add_argument("--toggles", default="{}")
    ap.add_argument("--max-gens", type=int, default=200)
    ap.add_argument("--min-gens", type=int, default=40)
    ap.add_argument("--plateau", type=int, default=10)
    ap.add_argument("--plateau-tol", type=float, default=0.01)
    ap.add_argument("--deadline", default="")
    ap.add_argument("--commit", default="")
    a = ap.parse_args()
    a.toggles = json.loads(a.toggles)
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    log = Log(out / "driver.log")
    (out / "driver.pid").write_text(str(os.getpid()))
    if (out / "DONE").exists():                      # a resumed fit is running again: its old DONE is history
        os.replace(out / "DONE", out / f"DONE.{int(time.time())}")
    T, s_trial, s_floor = fl.load(a.train)
    train = sorted(set(np.load(a.train)["train"].tolist()))
    cfg = {k: getattr(a, k) for k in KEYS}
    cfg["train"] = str(Path(a.train).resolve())
    cp = out / "config.json"
    if cp.exists():
        old = json.load(open(cp))
        diff = {k: (old.get(k), cfg[k]) for k in KEYS if old.get(k) != cfg[k]}
        assert not diff, f"resume with different settings: {diff}"
    else:
        B = fc.bounds()
        json.dump({**cfg, "ids": fc.IDS, "bounds": B, "commit": a.commit, "s_trial": s_trial, "s_floor": s_floor,
                   "n_train_stims": len(train), "started": time.strftime("%Y-%m-%d %H:%M:%S %Z")}, open(cp, "w"),
                  indent=1)
    B = fc.bounds()
    sp = out / "state.pkl"
    if sp.exists():
        es = pickle.load(open(sp, "rb"))
        log(f"resumed at generation {es.countiter}")
    else:
        x0 = fc.to_x({pid: B[pid][0] for pid in fc.IDS}, B)
        es = cma.CMAEvolutionStrategy(x0, a.sigma0, {"popsize": a.pop, "seed": a.seed, "verbose": -9})
        log(f"started: {len(fc.IDS)} values, pop {a.pop}, batch {a.batch}, cpus {a.cpus}, shuffle {a.shuffle_seed}")
    hp = out / "history.csv"
    hist = list(csv.DictReader(open(hp))) if hp.exists() else []
    cpu_list = cpus(a.cpus)
    while True:
        g = es.countiter
        why = stop_reason(a, es, g, hist)
        if why:
            (out / "DONE").write_text(f"{time.strftime('%Y-%m-%d %H:%M:%S %Z')} generation {g}: {why}\n")
            log("DONE: " + why)
            break
        gd = out / f"gen_{g:04d}"
        gd.mkdir(exist_ok=True)
        ask = gd / "ask.npy"
        if ask.exists():
            X = np.load(ask)
        else:
            X = np.array(es.ask())
            np.save(ask, X)
        batch = batch_for(train, g, a.batch, a.seed)
        t0 = time.time()
        jobs = []
        for k, x in enumerate(X):
            jp, op = gd / f"job_{k:02d}.json", gd / f"eval_{k:02d}.npz"
            json.dump(dict(x=x.tolist(), targets=batch, shuffle_seed=a.shuffle_seed, h_dt=a.h_dt, mech_dt=a.mech_dt,
                           window_s=a.window_s, warm_s=a.warm_s, pulse_ms=a.pulse_ms, toggles=a.toggles, out=str(op)),
                      open(jp, "w"))
            jobs.append((jp, op))
        run_jobs(jobs, cpu_list, out, log)
        losses, sc = [], []
        for jp, op in jobs:
            if not op.exists():
                losses.append(np.nan)
                sc.append(None)
                continue
            z = np.load(op)
            m = fl.model_values(T, z["stat"], z["names"].tolist(), z["targets"].tolist())
            s = fl.scores(T, m, s_trial, s_floor)
            losses.append(s["chi2"])
            sc.append(s)
        L = np.array(losses, float)
        bad = ~np.isfinite(L)
        if bad.all():
            log(f"generation {g}: every evaluation failed; stopping")
            (out / "DONE").write_text(f"generation {g}: every evaluation failed\n")
            break
        if bad.any():
            L[bad] = 10.0 * np.nanmax(L)
            log(f"generation {g}: {int(bad.sum())} failed evaluations given 10 x the worst loss")
        es.tell(list(X), L.tolist())
        mean_vals = fc.to_values(es.mean, B)
        k = int(np.nanargmin(L))
        res = dict(generation=g, batch=batch, losses=L.tolist(), scores=sc, wall_s=time.time() - t0,
                   best_k=k, best_vals=fc.to_values(X[k], B), mean_vals=mean_vals, sigma=float(es.sigma))
        json.dump(res, open(gd / "result.json", "w"), indent=1)
        json.dump(dict(generation=g + 1, mean_x=es.mean.tolist(), mean_vals=mean_vals, sigma=float(es.sigma),
                       at_bound=[pid for pid, xx in zip(fc.IDS, es.mean) if abs(xx) > 3.0]),
                  open(out / "mean.json", "w"), indent=1)
        tmp = out / "state.pkl.tmp"
        pickle.dump(es, open(tmp, "wb"))
        os.replace(tmp, sp)
        row = dict(generation=g, time=time.strftime("%Y-%m-%d %H:%M:%S"), wall_s=round(time.time() - t0, 1),
                   best=round(float(L.min()), 5), median=round(float(np.median(L)), 5), sigma=round(float(es.sigma), 5),
                   evals=len(L) * (g + 1), batch=" ".join(batch))
        new = not hp.exists()
        with open(hp, "a", newline="") as f:
            w = csv.DictWriter(f, fieldnames=list(row))
            if new:
                w.writeheader()
            w.writerow(row)
        hist.append({k: str(v) for k, v in row.items()})
        log(f"generation {g}: best {row['best']}, median {row['median']}, sigma {row['sigma']}, {row['wall_s']} s")


if __name__ == "__main__":
    main()
