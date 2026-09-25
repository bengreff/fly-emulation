"""Apply this project's graph-level model changes to flybench's male-cns build.

Run with flybench's venv on backhouse:
    python scripts/flybench_variants.py

Writes connectomes under ~/.cache/flybench:
  malecns_m1       fragments removed (untyped, non-Traced: rows and columns
                   zeroed), histamine inhibitory (our sign table), no input
                   onto sensory neurons (F-SENS-1)
  malecns_m1_size1 m1 plus efficacy x (median size / post size) (pre-reg)
Everything else is flybench's reference LIF (Shiu 2024 constants x gain).
"""
from __future__ import annotations

import copy
from pathlib import Path

import numpy as np
import pandas as pd
import scipy.sparse as sp
from flybench.connectome import load_connectome

REPO = Path(__file__).resolve().parents[1]
CACHE = Path.home() / ".cache" / "flybench"

base = load_connectome("malecns")
a = base.annotations
size = (pd.read_parquet(REPO / "data" / "cache" / "male_cns_neurons.parquet")
        .set_index("bodyId")["size"].reindex(base.root_ids).to_numpy(float))

frag = ((a.status != "Traced") & (a.cell_type.fillna("") == "")).to_numpy()
hist = (a.nt_type == "HIST").to_numpy()
sens = a.super_class.fillna("").str.contains("sensory").to_numpy()
print(f"fragments {frag.sum():,}  histamine {hist.sum():,}  sensory {sens.sum():,}")

def variant(name: str, alpha: float) -> None:
    W = base.W.tocsr().astype(np.float32)
    row = np.where(frag, 0.0, np.where(hist, -1.0, 1.0)).astype(np.float32)
    # flybench signs HIST +1 (unknown -> excitatory); flip to -1 by row factor
    W = sp.diags(row) @ W
    col = np.where(frag | sens, 0.0, 1.0)
    if alpha:
        med = np.nanmedian(size[~frag])
        f = np.where(np.isfinite(size) & (size > 0), (med / size) ** alpha, 1.0)
        col = col * f
    W = (W @ sp.diags(col.astype(np.float32))).tocsr()
    W.eliminate_zeros()
    c = copy.copy(base)
    c.W, c.name = W, name
    c.meta = {**base.meta, "flyemu_variant": name, "size_alpha": alpha}
    c.save(CACHE / name)
    print(name, f"nnz {W.nnz:,}")

variant("malecns_m1", 0.0)
variant("malecns_m1_size1", 1.0)
