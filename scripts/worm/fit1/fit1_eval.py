"""Fit 1 held-out scoring (docs/worm/FIT1.md section 7), run once after both fits are DONE.

    python fit1_eval.py dtcheck FITDIR OUT --cpus 0-1
    python fit1_eval.py run     FITDIR OUT --set heldout|train|unc31 --cpus 0-7 [--limit N]
    python fit1_eval.py score   FITDIR OUT

Every phase first checks that this tree is the one the fits ran (its COMMIT file against the fits' config.json);
--any-tree skips that, for plumbing tests only.

dtcheck (first): main's fitted mean on three training stimulations (AVAL, ASHL, AWAL) at the fit's integration and
at brain.py's own (0.5 ms, mechanisms every 1 ms); passes if the RMS difference is at most 0.003 for every target.
Also reported, not a criterion: the same reference with channel noise on (the fit runs with it off), as the RMS
difference from the reference.

run: simulates, for the chosen set of stimulated neurons, the fit (main's CMA mean, real wiring), shuf-fit (shuf's
mean, shuffled wiring), the template (real wiring); for unc31, main's mean with the peptides toggle on and off at
300 ms pulses. Each model's targets are split into chunks, one worker per CPU (fit1_worker.py), each with its own
control twin. The held-out and training stimulated neurons come from split.json (names only); the unc-31 list
is read from sealed/unc31.npz at this step.
score: opens the data for each simulated set (train.npz, sealed/wt_heldout.npz, sealed/unc31.npz), and writes
OUT/scores.json: L (all, off-diagonal, autoresponse), sign agreement and r on significant off-diagonal pairs, and
the pass criteria P1-P4 and U with 2000 paired bootstrap resamples over stimulated neurons (seed 20261106).
"""
import argparse
import json
import sys
from pathlib import Path

import numpy as np

import fit1_core as fc
import fit1_loss as fl
from fit1_run import cpus, run_jobs, Log

SEED = 20261106
NBOOT = 2000


def check_tree(fitdir):
    """Held-out scoring runs the fits' own frozen tree: the COMMIT file bh_sync.sh wrote next to src/ must match
    the commit in the fits' config. A later tree scores a different model (the catalog merge after worm-v1 moved
    values that are not fitted, and the template's GCaMP6s half-decay)."""
    want = json.load(open(Path(fitdir) / "main" / "config.json"))["commit"]
    f = Path(__file__).resolve().parents[3] / "COMMIT"
    have = f.read_text().strip() if f.exists() else ""
    if have != want:
        sys.exit(f"this tree is {have or 'not a bh_sync.sh copy'}; the fits ran {want}. Run from the fits' tree "
                 "(~/worm-night/wfit/repo_v1 for FIT1), or pass --any-tree for a plumbing test.")


def models(fitdir, which):
    B = fc.bounds()
    tmpl = {pid: B[pid][0] for pid in fc.IDS}
    mv = json.load(open(Path(fitdir) / "main" / "mean.json"))["mean_vals"]
    if which == "unc31":
        return {"fit_pep_on": (mv, None, {}, 300.0), "fit_pep_off": (mv, None, {"peptides": "off"}, 300.0)}
    sv = json.load(open(Path(fitdir) / "shuf" / "mean.json"))["mean_vals"]
    seed = json.load(open(Path(fitdir) / "shuf" / "config.json"))["shuffle_seed"]
    return {"fit": (mv, None, {}, 500.0), "shuf_fit": (sv, seed, {}, 500.0), "template": (tmpl, None, {}, 500.0)}


def stims(fitdir, which):
    if which == "unc31":
        return sorted(np.load(Path(fitdir) / "sealed" / "unc31.npz")["stim"].tolist())
    sp = json.load(open(Path(fitdir) / "split.json"))
    return sorted(sp["held_out"] if which == "heldout" else sp["train"])


def dtcheck(a):
    out = Path(a.out) / "dtcheck"
    out.mkdir(parents=True, exist_ok=True)
    log = Log(out / "eval.log")
    cfg = json.load(open(Path(a.fitdir) / "main" / "config.json"))
    mv = json.load(open(Path(a.fitdir) / "main" / "mean.json"))["mean_vals"]
    tg = ["AVAL", "ASHL", "AWAL"]
    jobs = []
    for name, hd, md, tog in (("fit", cfg["h_dt"], cfg["mech_dt"], {}), ("ref", 0.5, 1.0, {}),
                              ("ref_chnoise", 0.5, 1.0, {"channel_noise": "diffusion"})):
        jp, op = out / f"{name}.json", out / f"{name}.npz"
        json.dump(dict(x=[0.0] * len(fc.IDS), fixed=mv, targets=tg, shuffle_seed=None, h_dt=hd, mech_dt=md,
                       window_s=cfg["window_s"], warm_s=cfg["warm_s"], pulse_ms=cfg["pulse_ms"],
                       toggles={**cfg["toggles"], **tog}, out=str(op)), open(jp, "w"))
        jobs.append((jp, op))
    run_jobs(jobs, cpus(a.cpus), out, log)
    F, R = np.load(out / "fit.npz")["stat"], np.load(out / "ref.npz")["stat"]
    N = np.load(out / "ref_chnoise.npz")["stat"]
    rms = np.sqrt(np.mean((F - R) ** 2, axis=0))
    res = dict(targets=tg, rms=rms.tolist(), max=np.abs(F - R).max(axis=0).tolist(), passed=bool((rms <= 0.003).all()),
               chnoise_rms=np.sqrt(np.mean((N - R) ** 2, axis=0)).tolist())
    json.dump(res, open(out / "dtcheck.json", "w"), indent=1)
    log(json.dumps(res))


def run(a):
    out = Path(a.out) / a.set
    out.mkdir(parents=True, exist_ok=True)
    log = Log(out / "eval.log")
    cfg = json.load(open(Path(a.fitdir) / "main" / "config.json"))
    S = stims(a.fitdir, a.set)[:a.limit or None]
    cl = cpus(a.cpus)
    jobs = []
    for name, (vals, seed, tog, pulse) in models(a.fitdir, a.set).items():
        chunks = np.array_split(np.array(S), max(1, min(len(cl), len(S))))
        for k, ch in enumerate(chunks):
            jp, op = out / f"{name}_{k:02d}.json", out / f"{name}_{k:02d}.npz"
            json.dump(dict(x=[0.0] * len(fc.IDS), fixed=vals, targets=ch.tolist(), shuffle_seed=seed,
                           h_dt=cfg["h_dt"], mech_dt=cfg["mech_dt"], window_s=cfg["window_s"], warm_s=cfg["warm_s"],
                           pulse_ms=pulse, toggles={**cfg["toggles"], **tog}, out=str(op)), open(jp, "w"))
            jobs.append((jp, op))
    log(f"{a.set}: {len(S)} stimulated neurons, {len(jobs)} jobs on {len(cl)} CPUs")
    run_jobs(jobs, cl, out, log)
    log("run done")


def gather(d, name):
    """stat over all chunks of one model: {(resp, stim): value}."""
    vals = {}
    for p in sorted(d.glob(f"{name}_*.npz")):
        z = np.load(p)
        names, tg = z["names"].tolist(), z["targets"].tolist()
        for j, t in enumerate(tg):
            for i, n in enumerate(names):
                vals[(n, t)] = float(z["stat"][i, j])
    return vals


def per_stim(T, m, s_trial, s_floor):
    """Per stimulated neuron: sum of squared normalised residuals and term count (for the bootstrap)."""
    r2 = ((m - T["y"]) / fl.sigma(T, s_trial, s_floor)) ** 2
    ok = np.isfinite(r2)
    u = sorted(set(T["stim"][ok].tolist()))                 # only stimulated neurons that were simulated
    ix = {s: k for k, s in enumerate(u)}
    k = np.array([ix.get(s, -1) for s in T["stim"]])
    ok &= k >= 0
    return u, np.bincount(k[ok], r2[ok], len(u)), np.bincount(k[ok], None, len(u))


def boot_diff(A, B, rng):
    """Paired bootstrap over stimulated neurons of L(A) - L(B); A, B = (sum r2, count) per stim."""
    n = len(A[0])
    d = np.empty(NBOOT)
    for b in range(NBOOT):
        w = np.bincount(rng.integers(0, n, n), minlength=n)
        d[b] = (w @ A[0]) / (w @ A[1]) - (w @ B[0]) / (w @ B[1])
    return dict(mean=float(np.mean(d)), lo=float(np.percentile(d, 2.5)), hi=float(np.percentile(d, 97.5)))


def score(a):
    fd, out = Path(a.fitdir), Path(a.out)
    _, s_trial, s_floor = fl.load(fd / "train.npz")
    data = {"train": fd / "train.npz", "heldout": fd / "sealed" / "wt_heldout.npz", "unc31": fd / "sealed" / "unc31.npz"}
    res = {}
    for st, path in data.items():
        d = out / st
        if not d.exists():
            continue
        T = np.load(path)["terms"]
        names = sorted({p.name.rsplit("_", 1)[0] for p in d.glob("*.npz")})
        M, stims = {}, None
        for nm in names:
            v = gather(d, nm)
            M[nm] = np.array([v.get((i, j), np.nan) for i, j in zip(T["resp"], T["stim"])])
            sn = sorted({t for _, t in v})
            assert stims is None or sn == stims, "models simulated different stimulated neurons"
            stims, cells = sn, sorted({n for n, _ in v})
        sim = np.isin(T["stim"], stims) & np.isin(T["resp"], cells)     # the terms every model must give
        bad = {nm: int((sim & ~np.isfinite(m)).sum()) for nm, m in M.items()}
        M["zero"] = np.where(sim, 0.0, np.nan)
        res[st] = {nm: fl.scores(T, m, s_trial, s_floor) for nm, m in M.items()}
        res[st]["non_finite_terms"] = bad            # any > 0 voids the verdict (FIT1.md Amendment 3)
        rng = np.random.default_rng(SEED)
        PS = {nm: per_stim(T, m, s_trial, s_floor) for nm, m in M.items()}
        assert all(v[0] == PS["zero"][0] for v in PS.values()), "models simulated different stimulated neurons"
        P = {nm: v[1:] for nm, v in PS.items()}
        res[st]["n_stim"] = len(PS["zero"][0])
        if st == "unc31":
            res[st]["U_diff_off_minus_on"] = boot_diff(P["fit_pep_off"], P["fit_pep_on"], rng)
        else:
            res[st]["diff_fit_minus_template"] = boot_diff(P["fit"], P["template"], rng)
            res[st]["diff_fit_minus_zero"] = boot_diff(P["fit"], P["zero"], rng)
            res[st]["diff_fit_minus_shuf"] = boot_diff(P["fit"], P["shuf_fit"], rng)
    h = res.get("heldout")
    if h:
        f, s = h["fit"], h["shuf_fit"]
        P1 = h["diff_fit_minus_template"]["hi"] < 0 and h["diff_fit_minus_zero"]["hi"] < 0
        P2 = h["diff_fit_minus_shuf"]["hi"] < 0
        P3 = f.get("sign_agree_sig", 0) > 0.5 and f.get("sign_agree_sig", 0) > s.get("sign_agree_sig", 0)
        res["verdict"] = dict(P1=P1, P2=P2, P3=P3, P4=dict(r_fit=f.get("r_sig"), r_shuf=s.get("r_sig")),
                              result="PASS" if P1 and P2 and P3 else "PARTIAL" if P1 else "FAIL")
        if any(h["non_finite_terms"].values()):
            res["verdict"]["result"] = "VOID: non-finite values " + json.dumps(h["non_finite_terms"])
    u = res.get("unc31")
    if u:
        dd = u["U_diff_off_minus_on"]
        res["U"] = ("not tested by this data" if abs(u["fit_pep_off"]["chi2"] - u["fit_pep_on"]["chi2"]) < 0.01
                    else "PASS" if dd["hi"] < 0 else "FAIL")
        if any(u["non_finite_terms"].values()):
            res["U"] = "VOID: non-finite values " + json.dumps(u["non_finite_terms"])
    json.dump(res, open(out / "scores.json", "w"), indent=1)
    print(json.dumps(res, indent=1))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("phase", choices=["dtcheck", "run", "score"])
    ap.add_argument("fitdir")
    ap.add_argument("out")
    ap.add_argument("--set", default="heldout", choices=["heldout", "train", "unc31"])
    ap.add_argument("--cpus", default="0-7")
    ap.add_argument("--limit", type=int, default=0, help="first N stimulated neurons only (plumbing tests)")
    ap.add_argument("--any-tree", action="store_true", help="skip the frozen-tree check (plumbing tests only)")
    a = ap.parse_args()
    if not a.any_tree:
        check_tree(a.fitdir)
    {"dtcheck": dtcheck, "run": run, "score": score}[a.phase](a)


if __name__ == "__main__":
    main()
