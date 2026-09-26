"""Per-cell-type axonal path length and calibre from neuPrint skeletons.

One skeleton per cell type (the traced neuron with most presynapses; untyped
cells are skipped), fetched from neuPrint `male-cns` and reduced to:

  cable_um        total cable length
  leaf_p50_um     median geodesic distance root -> leaf
  leaf_p75_um     75th percentile root -> leaf (proxy for soma/SIZ -> output terminals)
  leaf_max_um     farthest leaf
  axon_radius_um  median node radius along the root -> farthest-leaf path,
                  excluding the first 10% of that path (soma and primary neurite)
  root_radius_um  radius of the root node (large when the root is the soma)
  pre_path_p50_um median geodesic distance root -> the cell's own presynaptic
                  sites (300 sampled at random; each mapped to its nearest
                  skeleton node). The conduction-delay length.
  pre_path_p90_um 90th percentile of the same

Units: skeleton coordinates and radii are in 8 nm voxels (male-cns), converted
to micrometres. Resumable: results append to data/derived/skeleton_lengths.csv
and fetched body IDs are skipped on restart.

    uv run python scripts/skeleton_lengths.py [--threads 8] [--limit N]
"""
from __future__ import annotations

import argparse
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from fetch_male_cns import DATASET, TOKEN  # noqa: E402

OUT = ROOT / "data" / "derived" / "skeleton_lengths.csv"
VOXEL_UM = 0.008
COLS = ["bodyId", "type", "superclass", "size", "pre", "rooted", "n_nodes", "n_components",
        "frac_cable_in_root_component", "cable_um", "leaf_p50_um", "leaf_p75_um",
        "leaf_max_um", "axon_radius_um", "root_radius_um", "n_pre_sampled",
        "pre_path_p50_um", "pre_path_p90_um", "error"]


def reduce(s: pd.DataFrame, soma=None, pre=None) -> dict:
    """Geodesic statistics from the soma node (nearest skeleton node to the
    neuPrint soma location); without a soma in the volume (most sensory
    neurons), from one end of the tree's longest path (the nerve entry, in the
    typical case)."""
    import scipy.sparse as sp
    from scipy.sparse.csgraph import dijkstra
    s = s.reset_index(drop=True)
    idx = {r: i for i, r in enumerate(s.rowId.to_numpy())}
    parent = np.array([idx.get(l, -1) for l in s.link.to_numpy()])
    xyz = s[["x", "y", "z"]].to_numpy(float) * VOXEL_UM
    has = parent >= 0
    ch = np.where(has)[0]
    w = np.linalg.norm(xyz[ch] - xyz[parent[ch]], axis=1) + 1e-9
    g = sp.coo_matrix((w, (ch, parent[ch])), shape=(len(s), len(s))).tocsr()
    deg = np.bincount(np.r_[ch, parent[ch]], minlength=len(s))
    if soma is not None:
        root = int(np.argmin(np.linalg.norm(xyz - np.asarray(soma) * VOXEL_UM, axis=1)))
        rooted = "soma"
    else:
        d0 = dijkstra(g, directed=False, indices=0)
        root = int(np.nanargmax(np.where(np.isfinite(d0), d0, -1)))
        rooted = "tree_end"
    dist = dijkstra(g, directed=False, indices=root)
    comp = np.isfinite(dist)
    leaves = np.where((deg <= 1) & comp)[0]
    ld = dist[leaves] if leaves.size else np.array([0.0])
    _, pred = dijkstra(g, directed=False, indices=root, return_predecessors=True)
    far = leaves[np.argmax(ld)] if leaves.size else root
    path, i = [], far
    while i >= 0 and len(path) < len(s):
        path.append(i)
        i = pred[i]
    keep = [j for j in path if dist[j] >= 0.1 * dist[far]]
    rad = s.radius.to_numpy(float) * VOXEL_UM
    pd_ = np.array([np.nan])
    if pre is not None and len(pre):
        from scipy.spatial import cKDTree
        tree = cKDTree(np.where(comp[:, None], xyz, 1e9))
        _, near = tree.query(pre[["x", "y", "z"]].to_numpy(float) * VOXEL_UM)
        pd_ = dist[near]
    return {
        "n_pre_sampled": int(0 if pre is None else len(pre)),
        "pre_path_p50_um": float(np.nanpercentile(pd_, 50)) if np.isfinite(pd_).any() else np.nan,
        "pre_path_p90_um": float(np.nanpercentile(pd_, 90)) if np.isfinite(pd_).any() else np.nan,
        "rooted": rooted, "n_nodes": len(s), "n_components": int((~has).sum()),
        "frac_cable_in_root_component": float(w[comp[ch]].sum() / w.sum()),
        "cable_um": float(w.sum()),
        "leaf_p50_um": float(np.percentile(ld, 50)),
        "leaf_p75_um": float(np.percentile(ld, 75)),
        "leaf_max_um": float(ld.max()),
        "axon_radius_um": float(np.median(rad[keep])) if keep else np.nan,
        "root_radius_um": float(rad[root]),
    }


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--threads", type=int, default=8)
    ap.add_argument("--limit", type=int, default=None)
    a = ap.parse_args()
    from neuprint import Client
    c = Client("neuprint.janelia.org", dataset=DATASET, token=TOKEN.read_text().strip())

    n = pd.read_parquet(ROOT / "data" / "cache" / "male_cns_neurons.parquet")
    n = n[n.type.notna() & (n.status == "Traced")]
    reps = n.sort_values("pre", ascending=False).drop_duplicates("type")
    reps = reps[["bodyId", "type", "superclass", "size", "pre"]]
    soma = pd.read_parquet(ROOT / "data" / "cache" / "male_cns_extra2.parquet",
                           columns=["bodyId", "somaLocation"]).set_index("bodyId").somaLocation
    done = set(pd.read_csv(OUT).bodyId) if OUT.exists() else set()
    todo = reps[~reps.bodyId.isin(done)]
    if a.limit:
        todo = todo.head(a.limit)
    print(f"{len(reps)} types, {len(done)} done, {len(todo)} to fetch", flush=True)

    def presyn(bid: int) -> pd.DataFrame:
        q = (f"MATCH (n:Neuron {{bodyId: {bid}}})-[:Contains]->(:SynapseSet)-[:Contains]->"
             "(s:Synapse {type:'pre'}) WITH s, rand() AS r ORDER BY r LIMIT 300 "
             "RETURN s.location.x AS x, s.location.y AS y, s.location.z AS z")
        return c.fetch_custom(q)

    def one(row):
        try:
            bid = int(row["bodyId"])
            return {**row, **reduce(c.fetch_skeleton(bid, format="pandas"),
                                  soma.get(row["bodyId"]), presyn(bid))}
        except Exception as e:  # noqa: BLE001
            return {**row, "error": str(e)[:120]}

    buf, k = [], 0
    with ThreadPoolExecutor(a.threads) as ex:
        futs = [ex.submit(one, r) for r in todo.to_dict("records")]
        for f in as_completed(futs):
            buf.append(f.result())
            k += 1
            if len(buf) >= 200 or k == len(futs):
                df = pd.DataFrame(buf).reindex(columns=COLS)
                df.to_csv(OUT, mode="a", header=not OUT.exists(), index=False)
                buf = []
                print(f"{k}/{len(futs)}", flush=True)


if __name__ == "__main__":
    main()
