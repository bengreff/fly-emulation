"""Raw pull: every male-cns connection into and out of CT1, with its per-ROI synapse counts (fly2, s14).

Ben's condition on the flyvis pair arm (DECISIONS 13 Oct 22:53): CT1 compartmentalised as in flyvis. In
male-cns each ConnectsTo carries roiInfo with synapse counts per optic-lobe column ROI
(<neuropil>_<side>_col_<hex1>_<hex2>, Nern et al. 2025 Nature, the same hex grid as optic-lobe:v1.1) and
per layer ROI. The column counts sum to the connection weight for CT1 (CT1 -> LT33: 288 over 242 columns).
This keeps the roiInfo JSON verbatim (raw) so the compartment split (connectome.ct1_compartments) can be
re-derived. Output under data/raw/ct1_columns_s14/ (outside git) with a manifest of the query, dataset,
row counts and checksum.

    .venv/bin/python scripts/vision/fetch_ct1_columns.py
"""
from __future__ import annotations

import datetime as dt
import hashlib
import json
import sys
from pathlib import Path

import pandas as pd

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "scripts"))
from fetch_male_cns import DATASET, client  # noqa: E402

OUT = REPO / "data" / "raw" / "ct1_columns_s14"
Q = {"out": """MATCH (a:Neuron)-[x:ConnectsTo]->(b:Neuron) WHERE a.type = 'CT1'
RETURN a.bodyId AS pre, b.bodyId AS post, b.type AS partner_type, x.weight AS weight, x.roiInfo AS roiInfo""",
     "in": """MATCH (b:Neuron)-[x:ConnectsTo]->(a:Neuron) WHERE a.type = 'CT1'
RETURN b.bodyId AS pre, a.bodyId AS post, b.type AS partner_type, x.weight AS weight, x.roiInfo AS roiInfo""",
     "cells": """MATCH (a:Neuron) WHERE a.type = 'CT1'
RETURN a.bodyId AS bodyId, a.instance AS instance, a.pre AS pre, a.post AS post, a.size AS size,
       a.roiInfo AS roiInfo"""}


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    c = client()
    man = {"dataset": DATASET, "server": "neuprint.janelia.org", "fetched": dt.datetime.now().astimezone().isoformat(),
           "queries": Q, "files": {}}
    for k, q in Q.items():
        d = c.fetch_custom(q)
        if k != "cells":
            d["direction"] = k
        f = OUT / f"ct1_{k}.parquet"
        d.to_parquet(f, index=False)
        man["files"][f.name] = {"rows": int(len(d)), "sha256": hashlib.sha256(f.read_bytes()).hexdigest()}
        print(k, len(d), "rows" + ("" if k == "cells" else f", {int(d.weight.sum())} synapses"))
    (OUT / "MANIFEST.json").write_text(json.dumps(man, indent=1) + "\n")


if __name__ == "__main__":
    main()
