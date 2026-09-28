"""Brain-only pathway assay for many class-level candidates at once on the GPU
(the batched simulator, src/flyemu/gpu/batched.py), with exactly the CPU
assay's inputs: scripts/assay_pathways.py run_trial kick schedule (trial t uses
numpy default_rng(t + 10000)), 1000 ms, readout MN9 minus incompletely traced
cells. Each member = one (candidate, trial).

    .venv-gpu/bin/python scripts/gpu_assay.py cands.json --assay sugar_mn9 --trials 10 --out res.json

Candidates: lists of class overrides {"class:<c>|release_scale"|"input_scale"|"tonic_drive": v}.
They are applied as multipliers/offsets on the reference (m4) per-neuron arrays,
which is what lif._class_scales does (neutral reference: all class values neutral).
"""
import argparse
import json
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "src"))
sys.path.insert(0, str(REPO / "scripts"))

from flyemu import lif  # noqa: E402
from flyemu.gpu.batched import BatchedNetwork  # noqa: E402
from flyemu.gpu.equivalence import build_brain  # noqa: E402
import assay_pathways as AP  # noqa: E402


def member_arrays(net, conn, cands):
    cls = lif.circuit_classes(conn)
    rel0 = np.broadcast_to(np.asarray(net.params.release_gain, np.float32), (conn.n,))
    inp0 = np.asarray(net.input_gain, np.float32)
    sp0 = np.broadcast_to(np.asarray(net.spont, np.float32), (conn.n,))
    R, I, S = [], [], []
    for c in cands:
        r, i, s = rel0.copy(), inp0.copy(), sp0.copy()
        for k, v in c.items():
            ent, prop = k.split("|")
            m = cls == ent.removeprefix("class:")
            if prop == "release_scale":
                r[m] *= np.float32(v)
            elif prop == "input_scale":
                i[m] *= np.float32(v)
            elif prop == "tonic_drive":
                s[m] += np.float32(v)
            else:
                raise ValueError(k)
        R.append(r); I.append(i); S.append(s)
    return np.array(R), np.array(I), np.array(S)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("cands")
    ap.add_argument("--assay", default="sugar_mn9")
    ap.add_argument("--trials", type=int, default=10)
    ap.add_argument("--rate", type=float, default=100.0)
    ap.add_argument("--ms", type=float, default=1000.0)
    ap.add_argument("--chunk", type=int, default=40)
    ap.add_argument("--out", default="")
    a = ap.parse_args()
    cands = json.loads(Path(a.cands).read_text())
    reg, conn, params, kick_mv = build_brain()
    net = lif.Network(conn, params, 0.1)
    A = AP.ASSAYS[a.assay]
    nrn = conn.neurons
    stim, read = AP.select(nrn, A["stim"]), AP.select(nrn, A["readout"])
    lab = (pd.read_parquet(REPO / "data/cache/male_cns_extra.parquet", columns=["bodyId", "statusLabel"])
           .set_index("bodyId").statusLabel.reindex(nrn.bodyId).fillna("").to_numpy())
    read = read[~np.array(["Hard to trace" in x or "Partially" in x for x in lab[read]], bool)]
    T = int(round(a.ms / 0.1))
    prob = np.full(stim.size, a.rate * 0.1 / 1000.0)
    masks = []
    for t in range(a.trials):                       # the CPU assay's kick draws, trial by trial
        rng = np.random.default_rng(t + 10_000)
        masks.append(np.stack([rng.random(stim.size) < prob for _ in range(T)]))
    R, I, S = member_arrays(net, conn, cands)
    jobs = [(ci, t) for ci in range(len(cands)) for t in range(a.trials)]
    hz = np.zeros((len(cands), a.trials))
    t0 = time.time()
    for k in range(0, len(jobs), a.chunk):
        part = jobs[k:k + a.chunk]
        ci = np.array([c for c, _ in part]); ti = np.array([t for _, t in part])
        bn = BatchedNetwork(net, B=len(part), member={"release_gain": R[ci], "input_gain": I[ci],
                                                       "spont_mv": S[ci]})
        sched = np.stack([masks[t] for t in ti], axis=1)           # (T, B, k)
        out = bn.run(T, kicks=(stim, sched, kick_mv), record=read)
        cnt = out["raster"].sum(0)                                  # (B, r)
        for j, (c, t) in enumerate(part):
            hz[c, t] = cnt[j].mean() / (a.ms / 1000.0)
    res = {"assay": a.assay, "wall_s": round(time.time() - t0, 1),
           "members": len(jobs), "mean_hz": hz.mean(1).tolist(), "trials_hz": hz.tolist()}
    print(json.dumps({k: v for k, v in res.items() if k != "trials_hz"}))
    if a.out:
        Path(a.out).write_text(json.dumps(res))
