"""Fit 1 status, for the morning report: reads each fit's checkpoint (history.csv, mean.json, config.json, DONE)
and prints, per fit, the generation reached, evaluations per hour (measured from the history's times), the
training loss trend (10-generation means of the median, since each generation's batch differs), sigma, values
within 5% of a range end, and the generations left before the deadline at the measured rate. Also the zero
predictor's loss on the same batches (zero_loss_10gen_means), the baseline to read the median against, since one
batch's loss can be twice another's. The same split into off-diagonal terms (responses of other neurons, where
the wiring matters) and autoresponses (the stimulated neuron itself). Reads no sealed data. Needs only numpy and fit1_loss.py, so it runs from any copy.

    python fit1_status.py ~/worm-night/wfit/fit1
"""
import csv
import json
import sys
import time
from pathlib import Path

import numpy as np

import fit1_loss as fl


def zero_losses(d, H):
    """The zero predictor's loss (all, off-diagonal, autoresponse) on each generation's batch, on the terms the
    candidates were scored on (the batch's stimulated neurons, responders that are model cells)."""
    tp, ev = d.parent / "train.npz", sorted((d / "gen_0000").glob("eval_*.npz"))
    if not tp.exists() or not ev:
        return None
    T, s_trial, s_floor = fl.load(tp)
    names = np.load(ev[0])["names"].tolist()
    z = []
    for h in H:
        k = np.isin(T["stim"], h["batch"].split()) & np.isin(T["resp"], names)
        sc = fl.scores(T[k], np.zeros(int(k.sum())), s_trial, s_floor)
        z.append((sc["chi2"], sc["chi2_off"], sc["chi2_self"]))
    return np.array(z)


def means10(a):
    return [round(float(np.mean(a[k:k + 10])), 4) for k in range(0, len(a), 10)]


def status(d):
    d = Path(d)
    cfg = json.load(open(d / "config.json"))
    H = list(csv.DictReader(open(d / "history.csv"))) if (d / "history.csv").exists() else []
    out = dict(fit=d.name, shuffle_seed=cfg.get("shuffle_seed"), commit=cfg.get("commit"), started=cfg.get("started"),
               generations_done=len(H), done=(d / "DONE").read_text().strip() if (d / "DONE").exists() else None)
    if not H:
        return out
    t = [time.mktime(time.strptime(h["time"], "%Y-%m-%d %H:%M:%S")) for h in H]
    med = np.array([float(h["median"]) for h in H])
    best = np.array([float(h["best"]) for h in H])
    wall = np.array([float(h["wall_s"]) for h in H])
    out["last_generation_at"] = H[-1]["time"]
    out["mean_generation_wall_s"] = round(float(wall[-10:].mean()), 1)
    out["evals_per_hour"] = round(cfg["pop"] * 3600.0 / float(wall[-10:].mean()), 1)
    out["median_loss_10gen_means"] = [round(float(med[k:k + 10].mean()), 4) for k in range(0, len(med), 10)]
    out["best_loss_10gen_means"] = [round(float(best[k:k + 10].mean()), 4) for k in range(0, len(best), 10)]
    zero = zero_losses(d, H)
    if zero is not None:
        out["zero_loss_10gen_means"] = means10(zero[:, 0])
    parts = []
    for h in H:
        r = d / f"gen_{int(h['generation']):04d}" / "result.json"
        sc = json.load(open(r))["scores"] if r.exists() else []
        parts.append([np.nanmedian([c.get(key, np.nan) for c in sc]) if sc else np.nan for key in ("chi2_off", "chi2_self")])
    parts = np.array(parts)
    out["median_off_diagonal_10gen_means"] = means10(parts[:, 0])
    if zero is not None:
        out["zero_off_diagonal_10gen_means"] = means10(zero[:, 1])
    out["median_autoresponse_10gen_means"] = means10(parts[:, 1])
    if zero is not None:
        out["zero_autoresponse_10gen_means"] = means10(zero[:, 2])
    out["sigma"] = float(H[-1]["sigma"])
    m = json.load(open(d / "mean.json"))
    B = cfg["bounds"]
    near = {}
    for pid, v in m["mean_vals"].items():
        tmpl, lo, hi, _, tr = B[pid]
        u = (np.log(v) - np.log(lo)) / (np.log(hi) - np.log(lo)) if tr == "log" else (v - lo) / (hi - lo)
        if u < 0.05 or u > 0.95:
            near[pid] = dict(value=round(v, 5), lo=lo, hi=hi, end="low" if u < 0.05 else "high")
    out["mean_vals"] = {k: round(v, 5) for k, v in m["mean_vals"].items()}
    out["near_range_end"] = near
    run = json.load(open(d / "run.json")) if (d / "run.json").exists() else {}
    out["deadline"], out["driver_pid"] = run.get("deadline"), run.get("pid")
    if run.get("deadline") and not out["done"]:
        left = time.mktime(time.strptime(run["deadline"], "%Y-%m-%dT%H:%M")) - time.time()
        out["generations_left_by_deadline"] = int(max(0.0, left) / float(wall[-10:].mean()))
    return out


def main(root):
    for sub in ("main", "shuf"):
        p = Path(root) / sub
        if (p / "config.json").exists():
            print(json.dumps(status(p), indent=1))


if __name__ == "__main__":
    main(sys.argv[1])
