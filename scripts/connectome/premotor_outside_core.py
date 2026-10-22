"""s18: which presynaptic cells OUTSIDE the s15 106-cell "core" give the most synaptic
input to the T1 (front-leg) leg motor neuron pools, grouped by hemilineage.

Core = T1 instances of CORE_TYPES (the s15 oscillator-core premotor set) and T1 leg MNs
= T1 instances of LEG_TYPES, both from scripts/connectome/premotor_mn_geometry.py (reused
unchanged, not copied). This is a connectivity-only query on the local parquet cache: no
neuPrint call, no simulation.

Pool mapping (inferred from LEG_TYPES names + function notes already in the repo, not
re-derived here):
  coxa_promotor    = Tergopleural/Pleural promotor MN, Sternal anterior rotator MN
                     (tests/test_muscles.py: "anterior rotator = forward swing", i.e.
                     functionally promotor-like)
  coxa_remotor     = Pleural remotor/abductor MN, Sternal posterior rotator MN
                     ("posterior = backward", remotor-like)
  trochanter_flexor   = Tr flexor MN, Acc. tr flexor MN
  trochanter_extensor = Tr extensor MN
  tibia_flexor     = Ti flexor MN, Acc. ti flexor MN
  tibia_extensor   = Ti extensor MN
  other            = Sternal adductor MN, Sternotrochanter MN, Tergotr. MN -- no clean
                     flexor/extensor or promotor/remotor axis found in the repo (Tergotr.
                     MN drives the T2-specific jump muscle in general leg anatomy, odd for
                     a "T1" instance; Sternotrochanter's action wasn't pinned down here).
                     Kept in "all T1 leg MNs" totals, excluded from the flexor/extensor
                     reciprocal-inhibition check in step 4c.

Synapse threshold: weight >= 5 per connection, used everywhere in this script (edge
existence, pool totals, DNg100 hop search, core-input check). This matches the s17/F-REFLEX
convention already used elsewhere in the repo (s16/s17 writeups); male_cns_edges.parquet
itself carries all weights >= 1 with no built-in threshold.

Hemilineage: male_cns_hemilineage.parquet.trumanHl (the VNC/Truman-Lacin hemilineage call;
itoleeHl is null for every VNC neuron checked here, it's the optic-lobe/brain naming).

Output: prints the tables below and writes runs/s18/premotor_outside_core.csv (one row per
pool x presynaptic type, outside-core-and-MN only).

    .venv/bin/python scripts/connectome/premotor_outside_core.py
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts" / "connectome"))
from premotor_mn_geometry import CORE_TYPES, LEG_TYPES  # noqa: E402

CACHE = ROOT / "data" / "cache"
OUT_DIR = ROOT / "runs" / "s18"
THRESH = 5

POOL_OF_TYPE = {
    "Tergopleural/Pleural promotor MN": "coxa_promotor",
    "Sternal anterior rotator MN": "coxa_promotor",
    "Pleural remotor/abductor MN": "coxa_remotor",
    "Sternal posterior rotator MN": "coxa_remotor",
    "Tr flexor MN": "trochanter_flexor",
    "Acc. tr flexor MN": "trochanter_flexor",
    "Tr extensor MN": "trochanter_extensor",
    "Ti flexor MN": "tibia_flexor",
    "Acc. ti flexor MN": "tibia_flexor",
    "Ti extensor MN": "tibia_extensor",
    "Sternal adductor MN": "other",
    "Sternotrochanter MN": "other",
    "Tergotr. MN": "other",
}
FLEXOR_POOLS = {"tibia_flexor", "trochanter_flexor"}
EXTENSOR_POOLS = {"tibia_extensor", "trochanter_extensor"}


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    neurons = pd.read_parquet(CACHE / "male_cns_neurons.parquet")
    hl = pd.read_parquet(CACHE / "male_cns_hemilineage.parquet", columns=["bodyId", "trumanHl"])
    neurons = neurons.merge(hl, on="bodyId", how="left")
    edges = pd.read_parquet(CACHE / "male_cns_edges.parquet")
    edges = edges[edges.weight >= THRESH]

    t1 = neurons.somaNeuromere.fillna("").str.startswith("T1")
    core = neurons[t1 & neurons.type.isin(CORE_TYPES)]
    mn = neurons[t1 & neurons.type.isin(LEG_TYPES)]
    core_ids, mn_ids = set(core.bodyId), set(mn.bodyId)
    print(f"T1 core cells: {len(core_ids)} ({sorted(core.type.unique())})")
    print(f"T1 leg MN cells: {len(mn_ids)} ({len(mn.type.unique())} types)")
    print(f"core + MN total: {len(core_ids) + len(mn_ids)} (s15 'about 106' reference)")

    mn_pool = mn.set_index("bodyId").type.map(POOL_OF_TYPE)
    missing_pool = mn_pool[mn_pool.isna()]
    if len(missing_pool):
        print(f"WARNING: {len(missing_pool)} MN cells have no pool mapping: "
              f"{mn.set_index('bodyId').loc[missing_pool.index].type.unique()}")
    pools = {p: set(mn_pool[mn_pool == p].index) for p in mn_pool.dropna().unique()}
    pools["all_T1_leg_MN"] = set(mn_ids)

    type_of = neurons.set_index("bodyId").type
    hl_of = neurons.set_index("bodyId").trumanHl
    nt_by_type = (neurons.dropna(subset=["type"])
                  .groupby("type").celltypePredictedNt
                  .agg(lambda s: s.mode().iat[0] if len(s.mode()) else "unclear"))
    hl_by_type = (neurons.dropna(subset=["type"])
                  .groupby("type").trumanHl
                  .agg(lambda s: s.mode().iat[0] if len(s.mode()) else None))

    csv_rows = []
    all_pool_ids = pools["all_T1_leg_MN"]
    out_of_core_top20 = None
    hemilineage_rows = []

    for pname, ids in pools.items():
        sub = edges[edges.post.isin(ids)]
        total_in = sub.weight.sum()
        core_in = sub[sub.pre.isin(core_ids)].weight.sum()
        by_pre = sub.groupby("pre").weight.sum()
        outside = by_pre[~by_pre.index.isin(core_ids) & ~by_pre.index.isin(mn_ids)]
        outside_df = pd.DataFrame({"weight": outside})
        outside_df["type"] = outside_df.index.map(type_of)
        by_type = outside_df.groupby("type").weight.sum().sort_values(ascending=False)
        top15 = by_type.head(15)
        print(f"\n=== pool {pname}: n_mn={len(ids)}, total_input_syn={total_in}, "
              f"core_share={core_in / total_in:.3f} ===")
        print(f"{'presynaptic type':35s} {'syn':>8s} {'share':>7s} {'nt':12s} hemilineage")
        for ty, w in top15.items():
            nt = nt_by_type.get(ty, "unclear")
            hli = hl_by_type.get(ty, None)
            print(f"{str(ty):35s} {int(w):8d} {w / total_in:7.3f} {str(nt):12s} {hli}")
            csv_rows.append(dict(pool=pname, presynaptic_type=ty, synapses=int(w),
                                  share_of_pool_input=w / total_in, predicted_nt=nt,
                                  hemilineage=hli, n_mn_in_pool=len(ids),
                                  pool_total_input_syn=int(total_in), core_share=core_in / total_in))
        if pname == "all_T1_leg_MN":
            out_of_core_top20 = by_type.head(20)
            hl_agg = outside_df.groupby(outside_df.index.map(hl_of)).weight.sum().sort_values(ascending=False)
            print(f"\n--- out-of-core input by hemilineage, all T1 leg MN (top 10 of "
                  f"{len(hl_agg)}), core_share={core_in / total_in:.3f} ---")
            for h, w in hl_agg.head(10).items():
                print(f"{str(h):15s} {int(w):8d} {w / total_in:7.3f}")
                hemilineage_rows.append(dict(hemilineage=h, synapses=int(w), share_of_total_input=w / total_in))

    pd.DataFrame(csv_rows).to_csv(OUT_DIR / "premotor_outside_core.csv", index=False)
    print(f"\nwrote {OUT_DIR / 'premotor_outside_core.csv'} ({len(csv_rows)} rows)")

    # step 4: top-20 out-of-core candidates, DNg100 hops / core input / reciprocal inhibition
    dn100_ids = set(neurons[neurons.type == "DNg100"].bodyId)
    print(f"\nDNg100 bodyIds: {sorted(dn100_ids)}")
    dn100_direct_post = set(edges[edges.pre.isin(dn100_ids)].post)
    two_hop_post = set(edges[edges.pre.isin(dn100_direct_post)].post)

    cand_ids_by_type = {ty: set(neurons[neurons.type == ty].bodyId) for ty in out_of_core_top20.index}

    flexor_ids = pools.get("tibia_flexor", set()) | pools.get("trochanter_flexor", set())
    extensor_ids = pools.get("tibia_extensor", set()) | pools.get("trochanter_extensor", set())

    def feeds_mainly(ids):
        w_flex = edges[edges.pre.isin(ids) & edges.post.isin(flexor_ids)].weight.sum()
        w_ext = edges[edges.pre.isin(ids) & edges.post.isin(extensor_ids)].weight.sum()
        if w_flex == 0 and w_ext == 0:
            return None
        return "flexor" if w_flex >= w_ext else "extensor"

    cand_group = {ty: feeds_mainly(ids) for ty, ids in cand_ids_by_type.items()}

    print(f"\n=== top-20 out-of-core candidates (over all T1 leg MN): DNg100 hops / core input / flexor-extensor group ===")
    print(f"{'type':35s} {'syn':>8s} {'DNg100<=2hop':>13s} {'core_in':>8s} {'fx/ext':8s}")
    cand_rows = []
    for ty, w in out_of_core_top20.items():
        ids = cand_ids_by_type[ty]
        direct = bool(ids & dn100_direct_post)
        two_hop = bool(ids & two_hop_post)
        from_core = edges[edges.pre.isin(core_ids) & edges.post.isin(ids)].weight.sum()
        grp = cand_group[ty]
        tag = "direct" if direct else ("2-hop" if two_hop else "no")
        print(f"{str(ty):35s} {int(w):8d} {tag:>13s} {int(from_core):8d} {str(grp):8s}")
        cand_rows.append((ty, direct, two_hop, int(from_core), grp))

    flexor_types = [ty for ty, _, _, _, g in cand_rows if g == "flexor"]
    extensor_types = [ty for ty, _, _, _, g in cand_rows if g == "extensor"]
    print(f"\nflexor-leaning candidates: {flexor_types}")
    print(f"extensor-leaning candidates: {extensor_types}")

    print("\n=== reciprocal flexor<->extensor connections among top-20 candidates (GABA/glutamate, syn>=5) ===")
    found = []
    for fty in flexor_types:
        fids = cand_ids_by_type[fty]
        for ety in extensor_types:
            eids = cand_ids_by_type[ety]
            fe = edges[edges.pre.isin(fids) & edges.post.isin(eids)].weight.sum()
            ef = edges[edges.pre.isin(eids) & edges.post.isin(fids)].weight.sum()
            nt_f, nt_e = nt_by_type.get(fty), nt_by_type.get(ety)
            if fe >= THRESH and nt_f in ("gaba", "glutamate"):
                print(f"{fty} ({nt_f}) -> {ety}: {int(fe)} syn")
                found.append((fty, ety, "fwd", int(fe), nt_f))
            if ef >= THRESH and nt_e in ("gaba", "glutamate"):
                print(f"{ety} ({nt_e}) -> {fty}: {int(ef)} syn")
                found.append((ety, fty, "rev", int(ef), nt_e))
    if not found:
        print("none found among the top-20 out-of-core candidates at this threshold")


if __name__ == "__main__":
    main()
