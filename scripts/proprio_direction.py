"""Infer each leg proprioceptor type's preferred direction from its wiring.

Prior (inferred): leg proprioceptive reflexes at rest are resistance reflexes
(negative feedback), as for FeCO-driven reflexes in stick insect and locust
(Bässler 1993; Büschges 2005) and the tibia-angle sensitivity of Drosophila slow
flexor MNs (Azevedo 2020). Under that prior, a type whose net signed drive
(direct + two-hop, sign by predicted transmitter, >=5-synapse edges) excites the
EXTENSOR more than the flexor pool signals FLEXION, and vice versa.

Applied to claw and hook types (flexion- vs extension-tuned) and hair plates
(which joint limit). Club (vibration/movement, bidirectional) is left alone.
Rewrites the `direction` columns of data/params/proprio_assignment.csv.
Post-hoc: introduced after the first standing run failed (DECISIONS session 6).
"""
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]


def main() -> None:
    n = pd.read_parquet(ROOT / "data/cache/male_cns_neurons.parquet").set_index("bodyId")
    e = pd.read_parquet(ROOT / "data/cache/male_cns_edges.parquet")
    e = e[e.weight >= 5]
    sign = n.predictedNt.fillna("unclear").map({"gaba": -1, "glutamate": -1}).fillna(1)
    typ = n.type.fillna("untyped")

    def drive(src_type, mn_types):
        src = set(n.index[typ == src_type]); dst = set(n.index[typ.isin(mn_types)])
        d1 = e[e.pre.isin(src) & e.post.isin(dst)]
        direct = float((d1.weight * d1.pre.map(sign)).sum())
        mid = e[e.pre.isin(src)].groupby("post").weight.sum()
        h2 = e[e.pre.isin(mid.index) & e.post.isin(dst)]
        two = float((h2.weight * h2.pre.map(sign) * h2.pre.map(mid)).sum() / 1000.0)
        return direct + two

    POOLS = {"FTi": (["Ti extensor MN"], ["Ti flexor MN", "Acc. ti flexor MN"]),
             "CTr": (["Tr extensor MN", "Sternotrochanter MN"], ["Tr flexor MN", "Acc. tr flexor MN"]),
             "ThC": (["Pleural remotor/abductor MN"], ["Tergopleural/Pleural promotor MN"])}
    path = ROOT / "data/params/proprio_assignment.csv"
    t = pd.read_csv(path, comment="#")
    t["subtype"] = t.subtype.fillna("")
    t = t.drop(columns=[c for c in ("direction", "net_drive_ext_minus_flex", "direction_basis") if c in t.columns])
    out = []
    for r in t.itertuples():
        rec = r._asdict(); rec.pop("Index")
        if r.subtype in ("claw", "hook_flex", "hook_ext"):
            ext, flex = (drive(r.type, p) for p in POOLS["FTi"])
            net = ext - flex
            kind = "claw" if r.subtype == "claw" else "hook"
            rec["subtype"] = kind if kind == "claw" else ("hook_flex" if net > 0 else "hook_ext")
            rec["direction"] = "flexion" if net > 0 else "extension"
            rec["net_drive_ext_minus_flex"] = round(net, 1)
        elif r.subtype.startswith("hairplate"):
            best, score = None, 0.0
            for j, lim in (("ThC", "protraction"), ("CTr", "levation")):
                a, b = (drive(r.type, p) for p in POOLS[j])   # a: remotor/depressor side
                if abs(a - b) > abs(score):
                    best, score = (j, lim if a > b else {"protraction": "retraction",
                                                          "levation": "depression"}[lim]), a - b
            rec["subtype"] = f"hairplate_{best[0]}_{best[1]}"
            rec["direction"] = best[1]
            rec["net_drive_ext_minus_flex"] = round(score, 1)
        else:
            rec["direction"] = ""
            rec["net_drive_ext_minus_flex"] = np.nan
        out.append(rec)
    df = pd.DataFrame(out)
    df["direction_basis"] = np.where(df.direction != "", "inferred", "")
    with open(path, "w") as fh:
        fh.write("# Leg proprioceptor subtype per male-cns type. Subtype from the BANC crosswalk (basis column);\n"
                 "# direction inferred from wiring under a resistance-reflex prior (scripts/proprio_direction.py).\n")
        df.to_csv(fh, index=False)
    print(df[["type", "subtype", "direction", "net_drive_ext_minus_flex", "cells"]].to_string())


if __name__ == "__main__":
    main()
