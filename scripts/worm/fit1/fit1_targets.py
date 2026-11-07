"""Fit 1 targets (docs/worm/FIT1.md, pre-registered): Randi et al. 2023's published atlas statistics (funatlas.h5,
wormneuroatlas) split by stimulated neuron with a fixed seed. Writes

    train.npz                 the training terms the fit sees (stimulated neuron in the training set)
    sealed/wt_heldout.npz     the held-out stimulated neurons' columns (all their responses and their own)
    sealed/unc31.npz          every unc-31 term
    split.json                the split (names only), the noise model, counts and the sealed files' sha256

Only counts and the training noise model are printed; no held-out or unc-31 value is printed.
A term is (responder i, stimulated j): y = dFF[i, j] (the trial- and animal-averaged mean dF/F over 30 s), its trial
count n = occ1[i, j], its q. sigma^2 = s_trial^2 / n + s_floor^2, s_trial the robust within-pair SD of the per-trial
values (dFF_all) over non-significant training pairs (1.4826 x the median absolute deviation of each trial from its
pair's mean, scaled by sqrt(n / (n - 1)); a pooled variance is driven by a few huge trials), s_floor the median |dFF| of non-significant training pairs
(both from training data only). i = j is the autoresponse term (the actuator's calibration).

    python fit1_targets.py funatlas.h5 outdir
"""
import hashlib
import json
import re
import sys
from pathlib import Path

import h5py
import numpy as np

import fit1_core as fc

SEED = 20261106
HOLD = 0.2


def to_model(n, model):
    """funatlas id -> model cell name: the same name, or a ventral cord number zero-padded (VB1 -> VB01); AWCON /
    AWCOFF stay unmatched (which of AWCL / AWCR is ON differs between animals)."""
    if n in model:
        return n
    m = re.fullmatch(r"([A-Z]+)(\d)", n)
    if m and f"{m[1]}0{m[2]}" in model:
        return f"{m[1]}0{m[2]}"
    return None


def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def terms(f, strain, ids, cols, model):
    D, Q, O, A = (f[strain][k][:] for k in ("dFF", "q", "occ1", "dFF_all"))
    ix = {n: k for k, n in enumerate(ids)}
    rows, res = [], []
    for j in cols:
        for i in ids:
            if to_model(i, model) is None:
                continue
            a, b = ix[i], ix[j]
            if O[a, b] < 1 or not np.isfinite(D[a, b]):
                continue
            tr = np.asarray(A[a, b], float).ravel() if A[a, b] is not None else np.zeros(0)
            tr = tr[np.isfinite(tr)]
            if tr.size > 1 and i != j and (not np.isfinite(Q[a, b]) or Q[a, b] >= 0.05):
                res.append((tr - tr.mean()) * np.sqrt(tr.size / (tr.size - 1)))
            rows.append((to_model(i, model), to_model(j, model), float(D[a, b]), float(Q[a, b]) if np.isfinite(Q[a, b]) else 1.0, int(O[a, b]),
                         float(np.var(tr, ddof=1)) if tr.size > 1 else np.nan, tr.size))
    dt = [("resp", "U8"), ("stim", "U8"), ("y", "f8"), ("q", "f8"), ("n", "i4"), ("var", "f8"), ("ntr", "i4")]
    return np.array(rows, dtype=dt), (np.concatenate(res) if res else np.zeros(0))


def main(h5, out):
    out = Path(out)
    (out / "sealed").mkdir(parents=True, exist_ok=True)
    f = h5py.File(h5, "r")
    ids = [n.decode() for n in f["neuron_ids"][:]]
    model = set(fc.neurons())
    O = f["wt"]["occ1"][:]
    stim = sorted(j for k, j in enumerate(ids) if O[:, k].sum() > 0 and to_model(j, model))   # funatlas ids
    unmatched = sorted(j for k, j in enumerate(ids) if O[:, k].sum() > 0 and not to_model(j, model))
    rng = np.random.default_rng(SEED)
    perm = list(rng.permutation(stim))
    n_hold = int(round(HOLD * len(stim)))
    held, train = sorted(perm[:n_hold]), sorted(perm[n_hold:])
    T, resid = terms(f, "wt", ids, train, model)
    H, _ = terms(f, "wt", ids, held, model)
    O31 = f["unc31"]["occ1"][:]
    stim31 = sorted(j for k, j in enumerate(ids) if O31[:, k].sum() > 0 and to_model(j, model))
    U, _ = terms(f, "unc31", ids, stim31, model)
    off = T["resp"] != T["stim"]
    ns = off & (T["q"] >= 0.05) & (T["ntr"] > 1)
    s_trial = float(1.4826 * np.median(np.abs(resid)))
    s_trial_pooled = float(np.sqrt(np.sum(T["var"][ns] * (T["ntr"][ns] - 1)) / np.sum(T["ntr"][ns] - 1)))
    s_floor = float(np.median(np.abs(T["y"][off & (T["q"] >= 0.05)])))
    train_m, held_m = [to_model(j, model) for j in train], [to_model(j, model) for j in held]
    np.savez(out / "train.npz", terms=T, s_trial=s_trial, s_floor=s_floor, train=np.array(train_m))
    np.savez(out / "sealed" / "wt_heldout.npz", terms=H, held=np.array(held_m))
    np.savez(out / "sealed" / "unc31.npz", terms=U, stim=np.array([to_model(j, model) for j in stim31]))
    info = dict(seed=SEED, hold_fraction=HOLD, stimulated_in_model=len(stim), unmatched_stimulated=unmatched,
                train=train_m, held_out=held_m, unc31_stimulated=len(stim31),
                n_train_terms=int(len(T)), n_train_self=int((~off).sum()), n_train_sig=int((off & (T["q"] < 0.05)).sum()),
                n_held_terms=int(len(H)), n_unc31_terms=int(len(U)), s_trial=s_trial, s_trial_pooled_not_used=s_trial_pooled,
                s_floor=s_floor, n_residuals=int(resid.size),
                sha256={"train.npz": sha(out / "train.npz"), "sealed/wt_heldout.npz": sha(out / "sealed" / "wt_heldout.npz"),
                        "sealed/unc31.npz": sha(out / "sealed" / "unc31.npz")})
    json.dump(info, open(out / "split.json", "w"), indent=1)
    for p in ("sealed/wt_heldout.npz", "sealed/unc31.npz"):
        (out / p).chmod(0o400)
    print(json.dumps({k: v for k, v in info.items() if k not in ("train",)}, indent=1))


if __name__ == "__main__":
    main(*sys.argv[1:3])
