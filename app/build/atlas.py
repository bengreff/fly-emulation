"""Build the male-cns brain atlas for the workbench (flyemu-atlas/1).

    .venv/bin/python app/build/atlas.py            # -> app/data/atlas/male-cns-v1.0/

Reads the connectome cache (data/cache/male_cns_*.parquet) and writes:

    atlas.json          counts, vocabularies, coordinate frame, coverage, provenance
    neurons.bin.gz      per neuron: bodyId, position (um), position basis, flow layout,
                        coded superclass/class/type/side/transmitter, synapse counts
    edges/NNN.bin.gz    per shard of SHARD neurons: in- and out-partners (CSR) with
                        synapse counts, edges >= MIN_SYN synapses
    meta/NNN.json.gz    per shard: the strings the inspector shows (instance, crosswalks, ...)

Every derived value carries its basis. Positions: the soma location where the
dataset has one (measured), else the photoreceptor terminal centroid (measured),
else the synapse-weighted mean of positioned partners (derived), else the class
centroid (derived). The flow layer is the Schlegel et al. 2021 probabilistic
traversal from the sensory periphery (derived, display only).
"""
from __future__ import annotations

import argparse
import datetime as dt
import gzip
import json
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd
import pyarrow.parquet as pq
import scipy.sparse as sp

APP = Path(__file__).resolve().parents[1]
ROOT = APP.parent
sys.path.insert(0, str(APP / "server"))
from recfmt import write_blob  # noqa: E402

CACHE = ROOT / "data" / "cache"
VOXEL_UM = 0.008     # male-cns voxel = 8 nm (assumed from the dataset description; to verify)
MIN_SYN = 5
SHARD = 512
BASIS = ["soma (measured)", "photoreceptor terminal centroid (measured)",
         "mean of partners' positions, synapse-weighted (derived)",
         "class centroid (derived)", "none (drawn at the CNS centroid)"]
SENSORY = {"vnc_sensory", "ol_sensory", "cb_sensory", "sensory_ascending", "sensory_descending",
           "vnc_sensory_tbc", "cb_sensory_tbc", "sensory_ascending_tbc"}


def codes(col: pd.Series) -> tuple[np.ndarray, list[str]]:
    s = col.astype(object).where(col.notna(), "").astype(str)
    vocab = sorted(set(s))
    lut = {v: i for i, v in enumerate(vocab)}
    return np.array([lut[v] for v in s], np.uint32), vocab


def traversal_layers(W_in: sp.csr_matrix, seeds: np.ndarray, runs: int, steps: int,
                     threshold: float = 0.3, seed: int = 0) -> np.ndarray:
    """Schlegel et al. 2021 traversal: a cell joins at step t with probability
    min(1, fraction of its input synapses from already-reached cells / threshold).
    W_in[j, i] = synapses i -> j, rows normalised to input fractions. Returns the
    mean step of arrival over `runs` (NaN where never reached)."""
    rng = np.random.default_rng(seed)
    n = W_in.shape[0]
    acc = np.zeros(n)
    hit = np.zeros(n)
    for _ in range(runs):
        layer = np.full(n, np.inf)
        layer[seeds] = 0
        active = np.zeros(n)
        active[seeds] = 1
        for t in range(1, steps + 1):
            frac = W_in @ active
            p = np.minimum(1.0, frac / threshold)
            new = (layer == np.inf) & (rng.random(n) < p)
            if not new.any():
                break
            layer[new] = t
            active[new] = 1
        ok = np.isfinite(layer)
        acc[ok] += layer[ok]
        hit[ok] += 1
    out = np.full(n, np.nan)
    out[hit > 0] = acc[hit > 0] / hit[hit > 0]
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=str(APP / "data" / "atlas" / "male-cns-v1.0"))
    ap.add_argument("--runs", type=int, default=16, help="traversal repeats")
    args = ap.parse_args()
    out = Path(args.out)
    (out / "edges").mkdir(parents=True, exist_ok=True)
    (out / "meta").mkdir(parents=True, exist_ok=True)
    t0 = time.time()

    nr = pd.read_parquet(CACHE / "male_cns_neurons.parquet")
    ex = pd.read_parquet(CACHE / "male_cns_extra.parquet").set_index("bodyId")
    ex2 = pd.read_parquet(CACHE / "male_cns_extra2.parquet").set_index("bodyId")
    hl = pd.read_parquet(CACHE / "male_cns_hemilineage.parquet").set_index("bodyId")
    N = len(nr)
    bid = nr.bodyId.to_numpy().astype(np.int64)
    idx_of = pd.Series(np.arange(N), index=bid)
    print(f"{N:,} neurons")

    # --- positions ----------------------------------------------------------
    pos = np.full((N, 3), np.nan, np.float32)
    basis = np.full(N, 4, np.uint8)
    soma = ex2.somaLocation.reindex(bid)
    has = soma.notna().to_numpy()
    pos[has] = np.stack([np.asarray(v, np.float64) for v in soma[has]]) * VOXEL_UM
    basis[has] = 0
    pt = pd.read_parquet(CACHE / "photoreceptor_terminals.parquet")
    pt = pt[pt.bodyId.isin(idx_of.index)]
    rows = idx_of.reindex(pt.bodyId).to_numpy()
    xyz = pt[["x", "y", "z"]].to_numpy(np.float64)
    free = (basis[rows] == 4) & np.isfinite(xyz).all(1)     # some terminal rows are empty
    pos[rows[free]] = xyz[free] * VOXEL_UM
    basis[rows[free]] = 1

    tb = pq.read_table(CACHE / "male_cns_edges.parquet", filters=[("weight", ">=", MIN_SYN)])
    e = tb.to_pandas()
    pre = idx_of.reindex(e.pre.to_numpy()).to_numpy()
    post = idx_of.reindex(e.post.to_numpy()).to_numpy()
    ok = ~(np.isnan(pre) | np.isnan(post))
    pre, post = pre[ok].astype(np.int64), post[ok].astype(np.int64)
    w = e.weight.to_numpy()[ok].astype(np.float64)
    del e, tb
    print(f"{w.size:,} edges >= {MIN_SYN} synapses")
    W = sp.csr_matrix((w, (pre, post)), shape=(N, N))      # W[i, j] = synapses i -> j
    U = (W + W.T).tocsr()
    for it in range(6):
        known = basis < 4
        todo = np.flatnonzero(~known)
        if todo.size == 0:
            break
        sub = U[todo][:, np.flatnonzero(known)]
        tot = np.asarray(sub.sum(1)).ravel()
        got = tot > 0
        if not got.any():
            break
        P = pos[known].astype(np.float64)
        pos[todo[got]] = (sub[got] @ P) / tot[got, None]
        basis[todo[got]] = 2
        print(f"  partner-mean pass {it}: placed {got.sum():,}")
    cls = nr["class"].fillna(nr.superclass).fillna("").to_numpy()
    for c in np.unique(cls[basis == 4]):
        m = cls == c
        ref = m & (basis < 4)
        if ref.any():
            pos[m & (basis == 4)] = np.nanmean(pos[ref], 0)
            basis[m & (basis == 4)] = 3
    pos[basis == 4] = np.nanmean(pos[basis < 4], 0)
    assert np.isfinite(pos).all(), "position left undefined"
    bc = np.bincount(basis, minlength=len(BASIS))
    print("position basis:", dict(zip(BASIS, bc.tolist())))

    # --- flow layer -----------------------------------------------------------
    sup = nr.superclass.fillna("").to_numpy()
    seeds = np.flatnonzero(np.isin(sup, list(SENSORY)))
    Win = W.T.tocsr().astype(np.float64)
    tot_in = np.asarray(Win.sum(1)).ravel()
    Win = sp.diags(1.0 / np.maximum(tot_in, 1)) @ Win
    layer = traversal_layers(Win.tocsr(), seeds, args.runs, 30)
    print(f"flow layer: {np.isfinite(layer).sum():,} reached, max mean layer {np.nanmax(layer):.1f}")

    # --- coded columns --------------------------------------------------------
    sup_c, sup_v = codes(nr.superclass)
    cls_c, cls_v = codes(nr["class"])
    typ_c, typ_v = codes(nr.type)
    side_c, side_v = codes(nr.somaSide)
    nt_c, nt_v = codes(ex.consensusNt.reindex(bid).where(lambda s: s.notna(), nr.predictedNt.values))
    stat_c, stat_v = codes(nr.status)
    in_model = (nr.status.eq("Traced") | nr.type.notna()).to_numpy().astype(np.uint8)

    arrays = {
        "bodyid": bid, "pos": pos.astype(np.float32), "pos_basis": basis,
        "layer": np.nan_to_num(layer, nan=-1).astype(np.float32),
        "superclass": sup_c.astype(np.uint8), "class": cls_c.astype(np.uint16),
        "type": typ_c, "side": side_c.astype(np.uint8), "nt": nt_c.astype(np.uint8),
        "status": stat_c.astype(np.uint8), "in_model": in_model,
        "n_pre": nr.pre.fillna(0).to_numpy().astype(np.uint32),
        "n_post": nr.post.fillna(0).to_numpy().astype(np.uint32),
    }
    index = write_blob(out / "neurons.bin.gz", arrays)

    # --- edge shards ----------------------------------------------------------
    Wc, Wr = W.tocsr(), W.T.tocsr()          # out-partners, in-partners
    n_sh = (N + SHARD - 1) // SHARD
    eidx, eidx_all = None, []
    for k in range(n_sh):
        a, b = k * SHARD, min(N, (k + 1) * SHARD)
        o, i = Wc[a:b], Wr[a:b]
        eidx = write_blob(out / "edges" / f"{k:03d}.bin.gz", {
            "out_ptr": o.indptr.astype(np.uint32), "out_idx": o.indices.astype(np.uint32),
            "out_w": np.minimum(o.data, 65535).astype(np.uint16),
            "in_ptr": i.indptr.astype(np.uint32), "in_idx": i.indices.astype(np.uint32),
            "in_w": np.minimum(i.data, 65535).astype(np.uint16)})
        eidx_all.append(eidx)
    (out / "edges" / "index.json").write_text(json.dumps(eidx_all, separators=(",", ":")))

    # --- inspector strings ----------------------------------------------------
    def col(df, name):
        return df[name].reindex(bid).to_numpy() if name in df else np.full(N, None)
    meta_cols = {
        "instance": nr.instance.to_numpy(), "subclass": nr.subclass.to_numpy(),
        "somaNeuromere": nr.somaNeuromere.to_numpy(), "size_voxels": nr["size"].to_numpy(),
        "predictedNt (EM classifier)": nr.predictedNt.to_numpy(),
        "predictedNtProb": nr.predictedNtProb.to_numpy(),
        "celltypePredictedNt": nr.celltypePredictedNt.to_numpy(),
        "consensusNt (dataset)": col(ex, "consensusNt"),
        "flywireType": col(ex, "flywireType"), "hemibrainType": col(hl, "hemibrainType"),
        "mancBodyid": nr.mancBodyid.to_numpy(), "entryNerve": col(ex, "entryNerve"),
        "rootSide": col(ex, "rootSide"), "statusLabel": col(ex, "statusLabel"),
        "hemilineage": col(ex2, "hemilineage"), "itoleeHl": col(hl, "itoleeHl"),
        "trumanHl": col(hl, "trumanHl"), "systematicType": col(ex2, "systematicType"),
        "synonyms": col(ex2, "synonyms"),
    }

    def clean(v):
        if v is None or (isinstance(v, float) and v != v):
            return None
        if isinstance(v, np.generic):
            v = v.item()
        if isinstance(v, float) and v.is_integer():
            return int(v)
        return v if isinstance(v, (int, float, str)) else str(v)
    for k in range(n_sh):
        a, b = k * SHARD, min(N, (k + 1) * SHARD)
        recs = [{c: x for c, x in ((c, clean(v[j])) for c, v in meta_cols.items()) if x is not None}
                for j in range(a, b)]
        (out / "meta" / f"{k:03d}.json.gz").write_bytes(
            gzip.compress(json.dumps(recs, separators=(",", ":")).encode(), 6))

    type_counts = np.bincount(typ_c, minlength=len(typ_v))
    atlas = {
        "format": "flyemu-atlas/1", "scan": "male-cns", "version": "v1.0",
        "built": dt.datetime.now().astimezone().isoformat(timespec="seconds"),
        "n": N, "n_in_model_policy": int(in_model.sum()), "n_edges": int(w.size),
        "min_synapses": MIN_SYN, "shard": SHARD, "n_shards": n_sh,
        "frame": {"units": "um", "voxel_um": VOXEL_UM, "voxel_basis": "assumed (to verify)",
                  "axes": "dataset frame: x lateral (fly's left at larger x), y and z as in neuPrint"},
        "arrays": index, "edge_arrays": list(eidx.keys()),
        "vocab": {"superclass": sup_v, "class": cls_v, "type": typ_v, "side": side_v,
                  "nt": nt_v, "status": stat_v, "pos_basis": BASIS},
        "type_counts": type_counts.tolist(),
        "coverage": {"pos_basis_counts": dict(zip(BASIS, bc.tolist())),
                     "flow_reached": int(np.isfinite(layer).sum())},
        "layers": {
            "position": "basis per neuron (pos_basis)",
            "type, class, superclass, side": "annotation in the scan (dataset authors)",
            "nt": "dataset consensus call where present, else the EM classifier prediction",
            "flow layer": "derived: Schlegel 2021 traversal from sensory neurons, threshold 0.3, "
                          f"{args.runs} runs, edges >= {MIN_SYN} synapses (display only)",
        },
        "neuropils": {"available": False,
                      "reason": "no region meshes in the project cache; planned (design section 5)"},
        "provenance": {"source": "data/cache/male_cns_*.parquet (neuPrint male-cns:v1.0 pulls)",
                       "builder": "app/build/atlas.py", "seconds": round(time.time() - t0, 1)},
    }
    (out / "atlas.json").write_text(json.dumps(atlas, separators=(",", ":")))
    sizes = sum(f.stat().st_size for f in out.rglob("*") if f.is_file())
    print(f"wrote {out} ({sizes / 1e6:.1f} MB) in {time.time() - t0:.0f} s")
    return 0


if __name__ == "__main__":
    sys.exit(main())
