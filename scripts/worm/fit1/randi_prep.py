"""Fit 1, data: per-trial dF/F windows from Randi et al. 2023's exported recordings (OSF e2syt, exported_data*).

Each recording r has r_gcamp.txt (volumes x ROIs, F), r_labels.txt (NeuroPAL name per ROI, blank = unlabelled),
r_t.txt (s, 2 volumes/s), r_stim_neurons.txt (ROI targeted by each stimulation; negative = no ROI) and
r_stim_volume_i.txt (volume index of each stimulation onset).

For every stimulation with a named target and every named ROI it writes the F trace from -30 s to +30 s around the
onset (121 volumes at 0.5 s), so any baseline and window can be computed later. Names are kept only if they are
one of the 300 funatlas neuron ids (no "?" or numbered placeholders). A recording's ROI may carry the same name twice
(both kept apart, by ROI). Output: one npz per strain.

    python randi_prep.py <exported_data dir> <strain> <out.npz>
"""
import sys
from pathlib import Path

import numpy as np

PRE, POST = 60, 60                     # volumes before / after the onset (30 s each at 2 volumes/s)


def load_rec(d, r):
    F = np.loadtxt(d / f"{r}_gcamp.txt", ndmin=2)
    with open(d / f"{r}_labels.txt") as f:
        lab = [x.strip() for x in f.read().split("\n")][:F.shape[1]]
    t = np.loadtxt(d / f"{r}_t.txt")
    tgt = np.atleast_1d(np.loadtxt(d / f"{r}_stim_neurons.txt", dtype=int))
    vol = np.atleast_1d(np.loadtxt(d / f"{r}_stim_volume_i.txt", dtype=int))
    ds = (d / f"{r}_ds_name.txt").read_text().strip()
    return F, lab, t, tgt, vol, ds


def main(src, strain, out, ids_file):
    d = Path(src)
    ids = set(x.strip() for x in open(ids_file) if x.strip())
    recs = sorted({int(p.name.split("_")[0]) for p in d.glob("*_gcamp.txt")})
    W, meta = [], []                   # W: [event x responder] F windows; meta rows
    names_rec = {}
    for r in recs:
        F, lab, t, tgt, vol, ds = load_rec(d, r)
        dt = np.median(np.diff(t))
        named = [k for k, x in enumerate(lab) if x in ids]
        names_rec[r] = (ds, float(dt), len(lab), len(named))
        for e, (j, v0) in enumerate(zip(tgt, vol)):
            if j < 0 or j >= len(lab) or lab[j] not in ids:
                continue
            if v0 - PRE < 0 or v0 + POST >= F.shape[0]:
                continue
            seg = F[v0 - PRE:v0 + POST + 1]                        # [121, ROIs]
            for i in named:
                W.append(seg[:, i].astype(np.float32))
                meta.append((r, e, lab[j], j, lab[i], i, v0))
    W = np.array(W)
    m = np.array(meta, dtype=[("rec", "i4"), ("event", "i4"), ("stim", "U8"), ("stim_roi", "i4"), ("resp", "U8"),
                              ("resp_roi", "i4"), ("onset_vol", "i4")])
    np.savez_compressed(out, F=W, meta=m, strain=strain,
                        recs=np.array([(r, *names_rec[r]) for r in recs], dtype=object))
    ev = np.unique(np.stack([m["rec"], m["event"]], 1), axis=0)
    print(f"{strain}: {len(recs)} recordings, {len(ev)} stimulations with a named target, {len(W)} event-responder "
          f"windows, {len(np.unique(m['stim']))} stimulated names, {len(np.unique(m['resp']))} responder names, "
          f"dt {np.median([v[1] for v in names_rec.values()]):.3f} s")


if __name__ == "__main__":
    main(*sys.argv[1:5])
