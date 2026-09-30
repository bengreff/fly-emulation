"""Fast transmitter from hemilineage for cells whose transmitter is unclear (session 11).

Development rule: neurons of one hemilineage share their fast transmitter
(Lacin et al. 2019 eLife 8:e43701, VNC; lead for the central brain). The model
gives cells with consensusNt "unclear" or missing a sign of 0 (they transmit
nothing). This script

  1. tests the rule on cells whose transmitter is known: leave-one-TYPE-out,
     predict each typed cell's consensusNt as the majority of the other types
     of its hemilineage (so a type never predicts itself); accuracy by
     hemilineage purity;
  2. writes the hemilineage table: majority fast transmitter, purity, n known,
     n types -> data/derived/nt_by_hemilineage.csv;
  3. lists the unclear cells the rule would fill (purity >= PURITY and >= MIN_N
     known cells from >= MIN_TYPES other types), plus unclear motor neurons as
     glutamate (VNC motor neurons are glutamatergic; they are an exception to the
     hemilineage rule) -> data/derived/nt_hemilineage_fill.csv.

Hemilineage: male-cns trumanHl (VNC, Truman nomenclature) else itoleeHl (brain,
Ito-Lee). Only acetylcholine / GABA / glutamate are predicted (fast transmitters).

    uv run python scripts/infer_nt_hemilineage.py
"""
from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[1]
CACHE = REPO / "data" / "cache"
OUT = REPO / "data" / "derived"
FAST = ["acetylcholine", "gaba", "glutamate"]
PURITY, MIN_N, MIN_TYPES = 0.9, 10, 2


def load() -> pd.DataFrame:
    n = pd.read_parquet(CACHE / "male_cns_neurons.parquet")
    n = n[(n.status == "Traced") | n.type.notna()]
    e = pd.read_parquet(CACHE / "male_cns_extra.parquet", columns=["bodyId", "consensusNt"])
    h = pd.read_parquet(CACHE / "male_cns_hemilineage.parquet", columns=["bodyId", "itoleeHl", "trumanHl"])
    n = n.merge(e, on="bodyId", how="left").merge(h, on="bodyId", how="left")
    n["hl"] = n.trumanHl.fillna(n.itoleeHl)
    n["tkey"] = n.type.fillna("#" + n.bodyId.astype(str))
    return n


def main() -> None:
    n = load()
    known = n[n.consensusNt.isin(FAST) & n.hl.notna()]
    # counts per (hemilineage, type, transmitter)
    c = known.groupby(["hl", "tkey", "consensusNt"]).size().rename("k").reset_index()
    tot = c.groupby(["hl", "consensusNt"]).k.sum().rename("K").reset_index()
    # leave-one-type-out prediction for every known typed cell
    rows = []
    for (hl, t), g in c.groupby(["hl", "tkey"]):
        own = g.set_index("consensusNt").k
        rest = tot[tot.hl == hl].set_index("consensusNt").K.sub(own, fill_value=0)
        rest = rest[rest > 0]
        n_types = c[(c.hl == hl) & (c.tkey != t)].tkey.nunique()
        if rest.sum() < MIN_N or n_types < MIN_TYPES:
            continue
        pred, pur = rest.idxmax(), rest.max() / rest.sum()
        for nt, k in own.items():
            rows.append(dict(hl=hl, tkey=t, true=nt, pred=pred, purity=pur, cells=int(k)))
    cv = pd.DataFrame(rows)
    ok = cv.true == cv.pred
    print(f"leave-one-type-out over {cv.tkey.nunique():,} types ({cv.cells.sum():,} cells) in "
          f"{cv.hl.nunique()} hemilineages")
    for lo in (0.0, 0.8, 0.9, 0.95):
        m = cv.purity >= lo
        print(f"  purity >= {lo:.2f}: types {m.sum():>5} accuracy (types) {ok[m].mean():.3f}; "
              f"(cells) {(cv.cells[m] * ok[m]).sum() / cv.cells[m].sum():.3f}")
    base = cv.groupby("true").cells.sum().max() / cv.cells.sum()
    print(f"  majority-class baseline (cells): {base:.3f}")
    cv.to_csv(OUT / "nt_hemilineage_cv.csv", index=False)

    table = (tot.pivot_table(index="hl", columns="consensusNt", values="K", fill_value=0)
             .reindex(columns=FAST, fill_value=0))
    table["n_known"] = table[FAST].sum(axis=1)
    table["majority"] = table[FAST].idxmax(axis=1)
    table["purity"] = table[FAST].max(axis=1) / table.n_known
    table["n_types"] = c.groupby("hl").tkey.nunique()
    table.reset_index().to_csv(OUT / "nt_by_hemilineage.csv", index=False)

    unclear = n[~n.consensusNt.isin(FAST + ["dopamine", "serotonin", "octopamine",
                                            "histamine", "tyramine"])]
    t = table[(table.purity >= PURITY) & (table.n_known >= MIN_N) & (table.n_types >= MIN_TYPES)]
    # VNC motor neurons are glutamatergic whatever their hemilineage's interneurons
    # use (NMJ glutamate; in male-cns 302 of 318 VNC MNs with a known consensusNt are
    # glutamate), so they are filled by class. Brain MNs are not (23 ACh, 4 glutamate
    # known): left unclear, as are neuromodulatory efferents.
    motor = unclear.superclass.eq("vnc_motor")
    skip = unclear.superclass.isin(["cb_motor", "vnc_efferent"])
    fill = unclear[~motor & ~skip & unclear.hl.isin(t.index)].assign(
        nt=lambda d: d.hl.map(t.majority), purity=lambda d: d.hl.map(t.purity), rule="hemilineage")
    fill = pd.concat([fill, unclear[motor].assign(nt="glutamate", purity=np.nan, rule="motor class")])
    fill[["bodyId", "type", "superclass", "hl", "consensusNt", "nt", "purity", "rule"]].to_csv(
        OUT / "nt_hemilineage_fill.csv", index=False)
    print(f"unclear/missing cells: {len(unclear):,}; with a hemilineage: {unclear.hl.notna().sum():,}; "
          f"filled at purity >= {PURITY}: {len(fill):,} ({fill.nt.value_counts().to_dict()})")
    print(fill.superclass.value_counts().head(8).to_dict())


if __name__ == "__main__":
    main()
