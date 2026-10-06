"""Visual columns for the fly's-eye view (M3): where each columnar cell of the motion
pathway sits in the eye mosaic, placed from connectivity alone.

    .venv/bin/python app/build/columns.py      # -> app/data/body/flybody/columns.json

Method (derived; the scan carries no column labels for these cells):
- Anchors: every photoreceptor with an ommatidium in app/data/body/flybody/eye.json
  (from data/derived/retinotopy.csv: derived topology, inferred global alignment) sits
  at that ommatidium's centroid in the mosaic.
- Every other cell of the listed types takes the synapse-weighted mean position of its
  placed presynaptic partners, in the eye that gives it the most placed input, and the
  mean is iterated until no cell moves by more than 0.01 ommatidium spacings. The
  anchors stay fixed, so the result is a weighted harmonic extension of the
  photoreceptor map through the network (edges of `MIN_SYN` synapses or more).
- Per cell it reports: the eye; x, y in the mosaic's pixel units; the nearest
  ommatidium (its column); `hops`, the fewest synapses from a photoreceptor; `share`,
  the fraction of its input synapses that come from placed cells; and `spread`, the
  weighted RMS distance of those inputs from its position, in ommatidium spacings.

Checks written with the output, not used for placing:
- eye against the cell's annotated soma side;
- neighbourhoods: for a type, how many of a cell's 6 nearest cells by soma position are
  within 2 spacings of it in the mosaic, against the same count with placements
  shuffled within the type (somata are measured, from the scan's :Neuron records via
  the atlas cache; lamina and medulla somata lie roughly over their columns).

Sources, read only: app/data/body/flybody/eye.json, data/cache/male_cns_neurons.parquet,
data/cache/male_cns_edges.parquet, and the soma positions in data/cache/male_cns_extra2.parquet.
"""
from __future__ import annotations

import datetime as dt
import json
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd
import pyarrow.parquet as pq
from scipy import sparse
from scipy.spatial import cKDTree

APP = Path(__file__).resolve().parents[1]
REPO = APP.parent
CACHE = REPO / "data" / "cache"
MIN_SYN = 3
# the motion pathway's columnar cells (design section 8): lamina monopolar cells,
# the ON (Mi1, Tm3, Mi4, Mi9, C3) and OFF (Tm1, Tm2, Tm4, Tm9) inputs, T4 and T5
TYPES = ["L1", "L2", "L3", "L4", "L5", "Mi1", "Tm3", "Mi4", "Mi9", "C3", "Tm1", "Tm2", "Tm4", "Tm9",
         "T4a", "T4b", "T4c", "T4d", "T5a", "T5b", "T5c", "T5d"]


def soma_positions(ids: np.ndarray) -> np.ndarray:
    """Soma location per bodyId (x, y, z in the scan's voxels), NaN where none."""
    ex = pd.read_parquet(CACHE / "male_cns_extra2.parquet", columns=["bodyId", "somaLocation"]).set_index("bodyId")
    loc = ex["somaLocation"].reindex(ids)
    out = np.full((len(ids), 3), np.nan)
    for i, v in enumerate(loc.to_numpy()):
        if v is None or (isinstance(v, float) and np.isnan(v)):
            continue
        a = v.get("coordinates") if isinstance(v, dict) else v
        if a is not None and len(a) == 3:
            out[i] = np.asarray(a, float)
    return out


def main() -> int:
    t0 = time.time()
    eye = json.loads((APP / "data" / "body" / "flybody" / "eye.json").read_text())
    cx, cy = np.asarray(eye["centroid"]["x"]), np.asarray(eye["centroid"]["y"])
    omm = np.c_[cx, cy]
    tree_o = cKDTree(omm)
    spacing = float(np.median(tree_o.query(omm, k=2)[0][:, 1]))

    nr = pd.read_parquet(CACHE / "male_cns_neurons.parquet", columns=["bodyId", "type", "somaSide"])
    cells = nr[nr["type"].isin(TYPES)].reset_index(drop=True)
    pr_ids, pr_eye, pr_om = [], [], []
    for e, k in enumerate(("L", "R")):
        p = eye["photoreceptors"].get(k) or {"bodyId": [], "ommatidium": []}
        pr_ids += p["bodyId"]; pr_eye += [e] * len(p["bodyId"]); pr_om += p["ommatidium"]
    ids = np.r_[np.asarray(pr_ids, np.int64), cells["bodyId"].to_numpy(np.int64)]
    n_pr, n = len(pr_ids), len(ids)
    row = pd.Series(np.arange(n), index=ids)

    tb = pq.read_table(CACHE / "male_cns_edges.parquet", columns=["pre", "post", "weight"],
                       filters=[("weight", ">=", MIN_SYN)]).to_pandas()
    tin = tb[tb["post"].isin(cells["bodyId"])]
    total_in = tin.groupby("post")["weight"].sum()               # every input, placed or not
    e_ = tin[tin["pre"].isin(ids)]
    W = sparse.csr_matrix((e_["weight"].to_numpy(float), (row[e_["post"]].to_numpy(), row[e_["pre"]].to_numpy())),
                          shape=(n, n))
    del tb, tin

    # anchors
    pos = np.full((n, 2), np.nan)
    eye_of = np.full(n, -1)
    pos[:n_pr] = omm[np.asarray(pr_om)]
    eye_of[:n_pr] = pr_eye
    fixed = np.zeros(n, bool); fixed[:n_pr] = True
    # hops: breadth-first from the anchors along W
    hops = np.full(n, -1); hops[:n_pr] = 0
    frontier = fixed.copy(); k = 0
    while frontier.any():
        k += 1
        reach = (W @ frontier.astype(float)) > 0
        new = reach & (hops < 0)
        hops[new] = k
        frontier = new
    # iterate the weighted mean, per eye
    for it in range(500):
        old = pos.copy()
        sw = np.zeros((n, 2)); sp = np.zeros((n, 2, 2))
        for e in (0, 1):
            m = (eye_of == e) & ~np.isnan(pos[:, 0])
            sw[:, e] = W @ m.astype(float)
            sp[:, e] = W @ np.where(m[:, None], np.nan_to_num(pos), 0.0)
        best = np.argmax(sw, axis=1)
        has = sw.max(axis=1) > 0
        upd = has & ~fixed
        eye_of[upd] = best[upd]
        pos[upd] = sp[upd, best[upd]] / sw[upd, best[upd], None]
        moved = np.nanmax(np.hypot(*(pos[upd] - old[upd]).T)) if it and upd.any() else np.inf
        if moved < 0.01 * spacing:
            break
    iters = it + 1
    placed = ~np.isnan(pos[:, 0]) & ~fixed

    # quality per cell
    sw_e = np.zeros(n); s2 = np.zeros(n)
    for e in (0, 1):
        m = (eye_of == e) & ~np.isnan(pos[:, 0])
        w_in = W @ m.astype(float)
        r2 = W @ np.where(m, np.nansum(np.nan_to_num(pos) ** 2, axis=1), 0.0)
        on = eye_of == e
        sw_e[on] = w_in[on]; s2[on] = r2[on]
    spread = np.sqrt(np.maximum(s2 / np.maximum(sw_e, 1e-9) - np.nansum(np.nan_to_num(pos) ** 2, axis=1), 0)) / spacing
    tot = total_in.reindex(ids).fillna(0).to_numpy()
    share = np.where(tot > 0, (W.sum(axis=1).A1) / np.maximum(tot, 1e-9), 0)

    c = np.flatnonzero(placed)
    column = np.full(n, -1)
    column[c] = tree_o.query(pos[c])[1]

    # checks, not used for placing
    side = cells["somaSide"].reindex(range(n - n_pr)).to_numpy()
    side = np.r_[np.full(n_pr, None), side]
    soma = np.r_[np.full((n_pr, 3), np.nan), soma_positions(cells["bodyId"].to_numpy(np.int64))]
    tnames = np.r_[np.full(n_pr, ""), cells["type"].to_numpy()]
    rng = np.random.default_rng(0)
    per_type = []
    for t in TYPES:
        m = placed & (tnames == t)
        nt = int((tnames == t).sum())
        sd = side[m]
        known = np.isin(sd, ["L", "R"])
        agree = float(np.mean(np.where(eye_of[m][known] == 0, "L", "R") == sd[known])) if known.any() else None
        nb = nb_shuf = tot_pairs = 0
        for e in (0, 1):
            me = m & (eye_of == e) & ~np.isnan(soma[:, 0])
            if me.sum() < 20:
                continue
            S, P = soma[me], pos[me]
            idx = cKDTree(S).query(S, k=7)[1][:, 1:]          # 6 nearest by soma, self excluded
            Ps = P[rng.permutation(len(P))]
            nb += int((np.linalg.norm(P[idx] - P[:, None, :], axis=2) < 2 * spacing).sum())
            nb_shuf += int((np.linalg.norm(Ps[idx] - Ps[:, None, :], axis=2) < 2 * spacing).sum())
            tot_pairs += idx.size
        occ = [np.bincount(column[m & (eye_of == e)], minlength=len(omm)) for e in (0, 1)]
        occ = np.concatenate([o[o > 0] for o in occ])
        per_type.append({
            "type": t, "n_scan": nt, "n_placed": int(m.sum()),
            "n_columns": [int(len(np.unique(column[m & (eye_of == e)]))) for e in (0, 1)],
            "per_column_median": float(np.median(occ)) if occ.size else None,
            "per_column_max": int(occ.max()) if occ.size else None,
            "hops_median": float(np.median(hops[m])) if m.any() else None,
            "share_median": round(float(np.median(share[m])), 3) if m.any() else None,
            "spread_median": round(float(np.median(spread[m])), 2) if m.any() else None,
            "eye_matches_soma_side": None if agree is None else round(agree, 3),
            "soma_neighbours_near": None if not tot_pairs else round(nb / tot_pairs, 3),
            "soma_neighbours_near_shuffled": None if not tot_pairs else round(nb_shuf / tot_pairs, 3),
        })
    doc = {
        "format": "flyemu-columns/1",
        "scan": "male-cns:v1.0", "body": "flybody",
        "created": dt.datetime.now().astimezone().isoformat(timespec="seconds"),
        "basis": "derived: synapse-weighted mean of placed presynaptic partners, iterated from the photoreceptors' "
                 "ommatidia (themselves derived topology with an inferred global alignment)",
        "min_synapses": MIN_SYN, "iterations": iters, "spacing_px": round(spacing, 3),
        "types": TYPES, "per_type": per_type,
        "cells": {
            "bodyId": ids[c].tolist(), "type": [TYPES.index(t) for t in tnames[c]],
            "eye": eye_of[c].tolist(), "x": np.round(pos[c, 0], 2).tolist(), "y": np.round(pos[c, 1], 2).tolist(),
            "column": column[c].tolist(), "hops": hops[c].tolist(),
            "share": np.round(share[c], 3).tolist(), "spread": np.round(spread[c], 2).tolist(),
        },
        "fields": {"x, y": "mosaic position, the eye render's pixel units (as eye.json centroids)",
                   "column": "nearest ommatidium to x, y", "hops": "fewest synapses from a placed photoreceptor",
                   "share": "fraction of the cell's input synapses (edges of >= min_synapses) that come from "
                            "photoreceptors and the listed types, the cells the placement reads",
                   "spread": "weighted RMS distance of those inputs from x, y, in ommatidium spacings"},
        "sources": ["app/data/body/flybody/eye.json", "data/cache/male_cns_neurons.parquet",
                    "data/cache/male_cns_edges.parquet", "data/cache/male_cns_extra2.parquet (somaLocation, checks only)"],
        "seconds": round(time.time() - t0, 1),
    }
    out = APP / "data" / "body" / "flybody" / "columns.json"
    out.write_text(json.dumps(doc, separators=(",", ":")) + "\n")
    print(f"{out.relative_to(REPO)}: {len(c)} cells placed in {iters} iterations, {doc['seconds']} s, "
          f"{out.stat().st_size / 1e6:.1f} MB")
    for p in per_type:
        print("  ", p)
    return 0


if __name__ == "__main__":
    sys.exit(main())
