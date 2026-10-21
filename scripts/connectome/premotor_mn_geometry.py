"""s15 (fly, 21 Oct; pre-registered DECISIONS 21 Oct 01:16): class leg_MN and core_premotor axon share q and
soma-axon coupling rho from the male-CNS skeletons, by fly2's option-B method unchanged
(scripts/connectome/mn_axon_geometry.py: its reduce() is imported and run as is).

The only differences from the MN5 run are the cells and the contacts:
  cells     class leg_MN: the T1 (front-leg) tibia and coxa/trochanter MN types in LEG_TYPES, both sides;
            class core_premotor: the T1 oscillator-core cells (E1 IN17A001, E2 INXXX466, I1 IN16B036,
            IN19A007/004/002; roles as bypass_s3_chain), both sides
  contacts  every postsynaptic site of the cell (the arms put all chemical inputs on the spike zone), in place
            of the PSI synapses
  Rin       per class (RIN_MOHM below, with its basis); rho = Rin x the base-to-site coupling conductance, which
            reduce() reports as gc_nS_<Ri> (so its own RIN_MOHM, the MN5 value, is not used)

Outputs: data/derived/premotor_mn_geometry.csv (one row per cell and FRAC), .json (class values and brackets),
data/derived/premotor_mn_geometry_skel/<bodyId>.csv.gz and <bodyId>_post.csv.gz (raw skeletons and synapses).

    .venv/bin/python scripts/connectome/premotor_mn_geometry.py [--offline]
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))
sys.path.insert(0, str(ROOT / "scripts" / "connectome"))
from fetch_male_cns import DATASET, TOKEN  # noqa: E402
import mn_axon_geometry as g  # noqa: E402

OUT = ROOT / "data" / "derived"
SKEL = OUT / "premotor_mn_geometry_skel"
LEG_TYPES = ("Ti flexor MN", "Acc. ti flexor MN", "Ti extensor MN", "Tr flexor MN", "Acc. tr flexor MN",
             "Tr extensor MN", "Tergopleural/Pleural promotor MN", "Pleural remotor/abductor MN",
             "Sternal anterior rotator MN", "Sternal posterior rotator MN", "Sternal adductor MN",
             "Sternotrochanter MN", "Tergotr. MN")
CORE_TYPES = ("IN17A001", "INXXX466", "IN16B036", "IN19A007", "IN19A004", "IN19A002")
# whole-cell Rin (MOhm): lo, mid, hi, basis, source. Filled from the s15 Sonnet scan (HANDOFF / DECISIONS).
RIN_MOHM: dict[str, tuple] = {
    "leg_MN": (150.0, 300.0, 700.0, "measured",
               "Azevedo et al. 2020 eLife 9:e56754 Fig 3E: T1 tibia flexor MNs, fast 150 (n 15), intermediate 300 "
               "(n 11), slow 700 MOhm (n 14); whole-cell at the soma, in vivo; central value = intermediate"),
    "core_premotor": (150.0, 600.0, 1000.0, "guessed",
                      "no adult VNC interneuron Rin found (s15 scan); central value from adult antennal-lobe PNs, "
                      "598 +/- 69 MOhm (Gouwens & Wilson 2009, measured, another class); bracket from the leg-MN "
                      "low end to ~1 GOhm (guessed)")}


def fetch(bids: list[int]) -> None:
    from neuprint import Client, NeuronCriteria as NC, SynapseCriteria as SC, fetch_synapses
    c = Client("neuprint.janelia.org", dataset=DATASET, token=TOKEN.read_text().strip())
    SKEL.mkdir(parents=True, exist_ok=True)
    for b in bids:
        if (SKEL / f"{b}_post.csv.gz").exists():
            continue
        s = c.fetch_skeleton(b, format="pandas", heal=True)
        s.to_csv(SKEL / f"{b}.csv.gz", index=False)
        syn = fetch_synapses(NC(bodyId=b), SC(type="post", primary_only=True), client=c)
        syn.to_csv(SKEL / f"{b}_post.csv.gz", index=False)
        print(b, len(s), "nodes", len(syn), "post synapses", flush=True)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--offline", action="store_true", help="use the saved skeletons and synapses")
    a = ap.parse_args()
    n = pd.read_parquet(ROOT / "data" / "cache" / "male_cns_neurons.parquet")
    t1 = n.somaNeuromere.fillna("").str.startswith("T1")
    cells = n[t1 & (n.type.isin(LEG_TYPES) | n.type.isin(CORE_TYPES))][["bodyId", "type", "instance"]].copy()
    cells["cls"] = np.where(cells.type.isin(CORE_TYPES), "core_premotor", "leg_MN")
    cells = cells.sort_values(["cls", "type", "instance"])
    if not a.offline:
        fetch(cells.bodyId.astype(int).tolist())
    soma = pd.read_parquet(ROOT / "data" / "cache" / "male_cns_extra2.parquet",
                           columns=["bodyId", "somaLocation"]).set_index("bodyId").somaLocation
    rows = []
    for c in cells.itertuples():
        s = pd.read_csv(SKEL / f"{c.bodyId}.csv.gz")
        syn = pd.read_csv(SKEL / f"{c.bodyId}_post.csv.gz").rename(columns={"x": "x_post", "y": "y_post",
                                                                              "z": "z_post"})
        loc = soma.get(c.bodyId)
        soma_um = None if loc is None else np.asarray(loc, float) * g.VOXEL_UM
        for f in g.FRACS:
            try:
                r = g.reduce(int(c.bodyId), s, soma_um, syn, f)
            except ValueError as e:
                print(f"{c.type} {c.instance} frac {f}: {e}", flush=True)
                continue
            r.pop("_plot")
            r.update(type=c.type, instance=c.instance, cls=c.cls)
            rows.append(r)
    df = pd.DataFrame(rows)
    keep = [k for k in df.columns if not k.startswith("rho_") and not k.startswith("q_cm")]
    df[keep].to_csv(OUT / "premotor_mn_geometry.csv", index=False, float_format="%.4g")
    summ = {"registration": "DECISIONS 21 Oct 01:16", "dataset": DATASET, "method": "mn_axon_geometry.reduce, "
            "contacts = all postsynaptic sites", "Ri_ohm_cm": g.RI_OHM_CM, "classes": {}}
    pd.set_option("display.width", 250)
    for cls, d in df[df.frac == g.FRACS[0]].groupby("cls"):
        out = {"n_cells": int(len(d)), "q": float(d.q.mean()), "q_lo": float(d.q.quantile(0.1)),
               "q_hi": float(d.q.quantile(0.9)), "frac_syn_distal_median": float(d.frac_psi_distal_to_base.median()),
               "ell_um_median": float(d.ell_um.median()), "gc_nS_mid_median": float(d.gc_nS_mid.median())}
        if cls in RIN_MOHM:
            lo, mid, hi, basis, src = RIN_MOHM[cls]
            rho = mid * d.gc_nS_mid / 1e3                 # MOhm x nS = 1e-3
            out.update(Rin_MOhm=[lo, mid, hi], Rin_basis=basis, Rin_source=src, rho=float(rho.mean()),
                       rho_cells_q10_q90=[float(rho.quantile(0.1)), float(rho.quantile(0.9))],
                       rho_lo=float(lo * (d.gc_nS_hi.quantile(0.1)) / 1e3),
                       rho_hi=float(hi * (d.gc_nS_lo.quantile(0.9)) / 1e3))
        summ["classes"][cls] = out
        print(cls, d[["type", "instance", "n_psi_syn", "frac_psi_distal_to_base", "base_dist_um", "site_dist_um",
                      "ell_um", "d_equiv_um", "q", "gc_nS_mid"]].describe().loc[["count", "min", "50%", "max"]].to_string())
    (OUT / "premotor_mn_geometry.json").write_text(json.dumps(summ, indent=1))
    print(json.dumps(summ, indent=1))


if __name__ == "__main__":
    main()
