"""Write the cached male-cns:v1.0 graph in flybench's Codex layout.

Same schema as flybench.fetch_neuprint.fetch (flybench v0.2.1): all :Neuron
nodes, edges with >= 5 synapses, predicted transmitter, classification,
soma coordinates (nm) and instance labels. Built from our cache because the
anonymous neuPrint fetch runs at ~7 min per chunk. Then:

    flybench build <out> --name malecns
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[1]
C = REPO / "data" / "cache"


def main(out: str) -> None:
    out = Path(out)
    out.mkdir(parents=True, exist_ok=True)
    n = (pd.read_parquet(C / "male_cns_neurons.parquet")
         .merge(pd.read_parquet(C / "male_cns_extra.parquet"), on="bodyId")
         .merge(pd.read_parquet(C / "male_cns_extra2.parquet"), on="bodyId"))
    e = pd.read_parquet(C / "male_cns_edges.parquet")
    e = e[e.weight >= 5].rename(columns={"pre": "pre_root_id", "post": "post_root_id", "weight": "syn_count"})
    e["neuropil"] = "ALL"
    e[["pre_root_id", "post_root_id", "neuropil", "syn_count"]].to_csv(
        out / "connections.csv.gz", index=False, compression="gzip")
    nt = n.predictedNt.fillna("").astype(str).str.upper().replace({
        "ACETYLCHOLINE": "ACH", "GLUTAMATE": "GLUT", "OCTOPAMINE": "OCT",
        "SEROTONIN": "SER", "DOPAMINE": "DA", "HISTAMINE": "HIST"})
    pd.DataFrame({"root_id": n.bodyId, "nt_type": nt}).to_csv(
        out / "neurons.csv.gz", index=False, compression="gzip")
    cls = pd.DataFrame({
        "root_id": n.bodyId, "flow": n.flow, "super_class": n.superclass,
        "class": n["class"], "sub_class": n.subclass, "cell_type": n.type,
        "side": n.somaSide, "hemilineage": n.hemilineage, "instance": n.instance,
        "systematic_type": n.systematicType, "status": n.status,
        "root_side": n.rootSide, "synonyms": n.synonyms})
    cls["hemibrain_type"] = ""
    cls.fillna("").to_csv(out / "classification.csv.gz", index=False, compression="gzip")
    ok = n.somaLocation.map(lambda v: v is not None and len(v) == 3)
    xyz = np.stack(n.somaLocation[ok].to_list()) * 8.0
    pd.DataFrame({"root_id": n.bodyId[ok], "x": xyz[:, 0], "y": xyz[:, 1], "z": xyz[:, 2]}).to_csv(
        out / "coordinates.csv.gz", index=False, compression="gzip")
    lab = n[["bodyId", "instance"]].dropna()
    lab = lab[lab.instance.astype(str) != ""].rename(columns={"bodyId": "root_id", "instance": "label"})
    lab.to_csv(out / "labels.csv.gz", index=False, compression="gzip")
    (out / "fetch_meta.json").write_text(json.dumps({
        "source": "flyemu cache (neuPrint male-cns:v1.0)", "min_synapses": 5,
        "n_neurons": int(len(n)), "n_edges": int(len(e))}, indent=2))
    print(f"{len(n):,} neurons, {len(e):,} edges -> {out}")


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else str(REPO / "external" / "flybench-malecns"))
