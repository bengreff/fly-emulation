"""s15c (fly, 21 Oct): the input synapses of the walking-circuit cells with their presynaptic partner and EM
position (raw data for synapses placed at their EM positions on the morphological cells).

Cells: the 106 T1 cells of premotor_mn_geometry (T1 leg MNs in LEG_TYPES and the 12 core cells, both sides).
Output: data/derived/walking_morph/syn_in.parquet (bodyId_pre, bodyId_post, x_post, y_post, z_post in voxels,
confidence_pre/post, roi), one row per synapse; male-cns v1.0 via neuPrint.

    .venv/bin/python scripts/connectome/walking_morph_fetch.py
"""
from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))
from fetch_male_cns import DATASET, TOKEN  # noqa: E402

OUT = ROOT / "data" / "derived" / "walking_morph"


def main() -> None:
    from neuprint import Client, NeuronCriteria as NC, fetch_synapse_connections
    d = pd.read_csv(ROOT / "data" / "derived" / "premotor_mn_split.csv")
    bids = sorted(d.bodyId.unique().astype(int).tolist())
    c = Client("neuprint.janelia.org", dataset=DATASET, token=TOKEN.read_text().strip())
    OUT.mkdir(parents=True, exist_ok=True)
    parts = []
    for i in range(0, len(bids), 10):
        s = fetch_synapse_connections(None, NC(bodyId=bids[i:i + 10]), client=c)
        print(i, len(s), flush=True)
        parts.append(s)
    syn = pd.concat(parts, ignore_index=True)
    syn.to_parquet(OUT / "syn_in.parquet", index=False)
    print(len(syn), "synapses onto", syn.bodyId_post.nunique(), "cells from", syn.bodyId_pre.nunique(), "partners")


if __name__ == "__main__":
    main()
