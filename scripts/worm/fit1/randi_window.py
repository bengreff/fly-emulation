"""Fit 1, data check: does a short response window keep the information in Randi 2023's 30 s statistic?

From randi_prep's windows: dF/F = (F - F0) / F0. Randi's own statistic (F0 = mean over the 30 s before, mean over
the 30 s after) is recomputed and compared with funatlas.h5's dFF (same pairs); then the trial-averaged time course
of the significant pairs (funatlas q < 0.05) gives where responses peak, and the per-pair correlation between a
short-window mean and the 30 s mean says how much a shorter simulation loses. Autoresponse filter: an event is kept
when the target's own mean dF/F over 0-5 s after onset exceeds `--auto` (Randi used a classifier on dF/F and its
second derivative; its thresholds are not in the parts read, so this is an approximation, checked by how many of
funatlas's pair trial counts it reproduces).

    python randi_window.py randi_wt.npz funatlas.h5 wt out_prefix
"""
import json
import sys

import h5py
import numpy as np

PRE = 60
DT = 0.5


def dff(F, base):
    """dF/F0; a window whose F0 is not finite and positive (an ROI lost or background-level) is NaN throughout."""
    F = np.where(np.isfinite(F), F, np.nan)
    F0 = np.nanmean(F[:, base], axis=1, keepdims=True)
    F0 = np.where(np.isfinite(F0) & (F0 > 1e-3 * np.nanmedian(F0)), F0, np.nan)
    return (F - F0) / F0


def main(npz, h5, strain, out):
    z = np.load(npz, allow_pickle=True)
    F, m = z["F"].astype(float), z["meta"]
    f = h5py.File(h5, "r")
    ids = [n.decode() for n in f["neuron_ids"][:]]
    ix = {n: k for k, n in enumerate(ids)}
    A, Q, O = f[strain]["dFF"][:], f[strain]["q"][:], f[strain]["occ1"][:]
    t = (np.arange(F.shape[1]) - PRE) * DT
    print("non-finite F samples:", int((~np.isfinite(F)).sum()), "of", F.size, "; F<=0:", int((F <= 0).sum()))
    pre30 = (t >= -30) & (t < 0)
    pre5 = (t >= -5) & (t < 0)
    D30 = dff(F, pre30)
    D5 = dff(F, pre5)
    # autoresponse: the target's own window
    ev = np.stack([m["rec"], m["event"]], 1)
    self_ = (m["resp_roi"] == m["stim_roi"])
    auto = {}
    for k in np.flatnonzero(self_):
        auto[(m["rec"][k], m["event"][k])] = float(np.nanmean(D5[k, (t >= 0) & (t < 5)]))
    res = {}
    for thr in (0.0, 0.1, 0.2, 0.3):
        keep = np.array([auto.get((a, b), -np.inf) > thr for a, b in ev])
        pairs = {}
        for k in np.flatnonzero(keep & ~self_):
            pairs.setdefault((m["resp"][k], m["stim"][k]), []).append(k)
        x, y, n_ok, n_tot = [], [], 0, 0
        for (i, j), ks in pairs.items():
            if i not in ix or j not in ix:
                continue
            a = np.nanmean(D30[ks][:, (t >= 0) & (t <= 30)])
            b = A[ix[i], ix[j]]
            if np.isfinite(a) and np.isfinite(b):
                x.append(a)
                y.append(b)
            n_tot += 1
            n_ok += int(O[ix[i], ix[j]] == len(ks))
        x, y = np.array(x), np.array(y)
        res[thr] = dict(events=int(keep.sum()), pairs=len(pairs), r_vs_funatlas=float(np.corrcoef(x, y)[0, 1]),
                        slope=float(np.polyfit(y, x, 1)[0]), trial_count_match=n_ok / max(n_tot, 1))
        print(strain, "auto >", thr, res[thr])
    thr = max(res, key=lambda k: res[k]["r_vs_funatlas"])
    keep = np.array([auto.get((a, b), -np.inf) > thr for a, b in ev])
    pairs = {}
    for k in np.flatnonzero(keep & ~self_):
        pairs.setdefault((m["resp"][k], m["stim"][k]), []).append(k)
    # significant pairs: trial-averaged time course (F0 = 5 s before)
    sig = [(i, j) for (i, j) in pairs if i in ix and j in ix and Q[ix[i], ix[j]] < 0.05]
    tc = np.array([np.nanmean(D5[pairs[p]], axis=0) for p in sig])
    sgn = np.sign(np.array([A[ix[i], ix[j]] for i, j in sig]))
    mean_tc = np.nanmean(tc * sgn[:, None], axis=0)
    post = t >= 0
    peak_t = float(t[post][np.nanargmax(mean_tc[post])])
    # short windows vs the 30 s statistic, over significant pairs
    full = np.array([np.nanmean(D30[pairs[p]][:, (t >= 0) & (t <= 30)]) for p in sig])
    win = {}
    for W in (2, 3, 4, 5, 6, 8, 10, 15, 20):
        s = np.array([np.nanmean(D5[pairs[p]][:, (t >= 0) & (t <= W)]) for p in sig])
        ok = np.isfinite(s) & np.isfinite(full)
        win[W] = dict(r=float(np.corrcoef(s[ok], full[ok])[0, 1]),
                      sign_agree=float(np.mean(np.sign(s[ok]) == np.sign(full[ok]))))
    # target's own response time course (for the actuator)
    st = np.array([D5[k] for k in np.flatnonzero(self_ & keep)])
    self_tc = np.nanmedian(st, axis=0)
    summary = dict(strain=strain, auto_threshold=thr, filters=res, n_sig_pairs_with_trials=len(sig),
                   peak_t_s=peak_t, mean_sig_tc=dict(zip([float(x) for x in t[::2]], [float(x) for x in
                                                                                     mean_tc[::2]])),
                   self_median_tc=dict(zip([float(x) for x in t[::2]], [float(x) for x in self_tc[::2]])),
                   windows=win)
    json.dump(summary, open(out + "_summary.json", "w"), indent=1)
    # per-pair table with the chosen filter: pair, n trials, mean dF/F at 0-W s for several W, funatlas dFF, q
    with open(out + "_pairs.csv", "w") as fo:
        fo.write("resp,stim,n,dff_0_5,dff_0_10,dff_0_30,sd_0_10,funatlas_dff,funatlas_q,funatlas_occ\n")
        for (i, j), ks in sorted(pairs.items()):
            if i not in ix or j not in ix:
                continue
            g = D5[ks]
            a5 = np.nanmean(g[:, (t >= 0) & (t <= 5)], axis=1)
            a10 = np.nanmean(g[:, (t >= 0) & (t <= 10)], axis=1)
            a30 = np.nanmean(D30[ks][:, (t >= 0) & (t <= 30)], axis=1)
            fo.write(f"{i},{j},{len(ks)},{np.nanmean(a5):.5f},{np.nanmean(a10):.5f},{np.nanmean(a30):.5f},"
                     f"{np.nanstd(a10):.5f},{A[ix[i], ix[j]]:.5f},{Q[ix[i], ix[j]]:.5f},{O[ix[i], ix[j]]}\n")
    # per-event self responses (the actuator target)
    with open(out + "_self.csv", "w") as fo:
        fo.write("stim,rec,event,dff_0_5,dff_0_10\n")
        for k in np.flatnonzero(self_):
            fo.write(f"{m['stim'][k]},{m['rec'][k]},{m['event'][k]},{np.nanmean(D5[k, (t >= 0) & (t <= 5)]):.5f},"
                     f"{np.nanmean(D5[k, (t >= 0) & (t <= 10)]):.5f}\n")
    print(json.dumps({k: v for k, v in summary.items() if k not in ("mean_sig_tc", "self_median_tc")}, indent=1))
    print("mean signed sig time course (t, dF/F):", [(float(a), round(float(b), 4)) for a, b in
                                                     zip(t[PRE - 4::4], mean_tc[PRE - 4::4])])
    print("self median time course:", [(float(a), round(float(b), 3)) for a, b in zip(t[PRE - 4::4], self_tc[PRE - 4::4])])


if __name__ == "__main__":
    main(*sys.argv[1:5])
