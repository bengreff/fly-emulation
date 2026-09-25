"""Cache the male-cns:v1.0 graph locally: neuron properties and all chemical edges.

Live neuPrint queries are chunked by bodyId so no single query is enormous.
Output is parquet under data/cache/, which is untracked; the manifest records it.
"""
from __future__ import annotations

import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd
from neuprint import Client

DATASET = "male-cns:v1.0"
OUT = Path(__file__).resolve().parents[1] / "data" / "cache"
TOKEN = Path.home() / ".config" / "flyemu" / "neuprint_token"


def client() -> Client:
    return Client("neuprint.janelia.org", dataset=DATASET, token=TOKEN.read_text().strip())


def fetch_neurons(c: Client) -> pd.DataFrame:
    q = """
    MATCH (n:Neuron)
    RETURN n.bodyId AS bodyId, n.type AS type, n.instance AS instance,
           n.superclass AS superclass, n.class AS class, n.subclass AS subclass,
           n.somaSide AS somaSide, n.somaNeuromere AS somaNeuromere,
           n.status AS status, n.size AS size,
           n.predictedNt AS predictedNt, n.predictedNtProb AS predictedNtProb,
           n.celltypePredictedNt AS celltypePredictedNt,
           n.celltypePredictedNtConfidence AS celltypePredictedNtConfidence,
           n.acetylcholineProb AS achProb, n.gabaProb AS gabaProb,
           n.glutamateProb AS glutProb, n.dopamineProb AS daProb,
           n.serotoninProb AS serProb, n.octopamineProb AS octProb,
           n.histamineProb AS hisProb,
           n.mancBodyid AS mancBodyid, n.target AS target,
           n.synweight AS synweight, n.pre AS pre, n.post AS post
    """
    return c.fetch_custom(q)


def fetch_edges(c: Client, neurons: pd.DataFrame, n_chunks: int = 24) -> pd.DataFrame:
    """Chunk by bodyId quantile so each query returns a similar number of edges.

    Each chunk is written to its own parquet, so an interrupted fetch resumes
    instead of restarting. bodyIds are strongly skewed (90% below 8.1e5, then a
    jump to 1.5e9), which is why fixed-width ranges stall on one huge query.
    """
    edges_dir = OUT / "edges_chunks"
    edges_dir.mkdir(parents=True, exist_ok=True)
    bounds = np.unique(
        np.quantile(np.sort(neurons.bodyId.values), np.linspace(0, 1, n_chunks + 1))
    ).astype("int64")
    bounds[-1] = int(bounds[-1]) + 1

    parts = []
    for k, (lo, hi) in enumerate(zip(bounds[:-1], bounds[1:])):
        path = edges_dir / f"chunk_{k:03d}.parquet"
        if path.exists():
            parts.append(pd.read_parquet(path))
            print(f"  chunk {k:03d} cached ({len(parts[-1]):,} edges)", flush=True)
            continue
        for attempt in range(3):
            try:
                t = time.time()
                df = c.fetch_custom(f"""
                MATCH (a:Neuron)-[w:ConnectsTo]->(b:Neuron)
                WHERE a.bodyId >= {lo} AND a.bodyId < {hi}
                RETURN a.bodyId AS pre, b.bodyId AS post, w.weight AS weight
                """)
                break
            except Exception as exc:
                print(f"  chunk {k:03d} attempt {attempt + 1} failed: {exc}", flush=True)
                if attempt == 2:
                    raise
                time.sleep(5)
        df.to_parquet(path, index=False)
        print(f"  chunk {k:03d} [{lo}, {hi}): {len(df):,} edges in "
              f"{time.time() - t:.0f}s", flush=True)
        parts.append(df)
    return pd.concat(parts, ignore_index=True)


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    c = client()
    print(f"{DATASET}, server {c.fetch_version()}", flush=True)

    npath = OUT / "male_cns_neurons.parquet"
    if not npath.exists():
        t = time.time()
        n = fetch_neurons(c)
        n.to_parquet(npath, index=False)
        print(f"neurons: {len(n):,} rows in {time.time()-t:.0f}s -> {npath}", flush=True)
    else:
        print(f"neurons: cached at {npath}", flush=True)

    epath = OUT / "male_cns_edges.parquet"
    if not epath.exists():
        t = time.time()
        e = fetch_edges(c, pd.read_parquet(npath))
        e.to_parquet(epath, index=False)
        print(f"edges: {len(e):,} rows, {e.weight.sum():,} synapses in {time.time()-t:.0f}s -> {epath}", flush=True)
    else:
        print(f"edges: cached at {epath}", flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
