"""The blank ledger, v2: every measurable quantity of a fly, counted.

Reads data/ontology/fly_information.yaml, which lists everything about the
animal's biology that could in principle be measured, whether or not the
model uses it. Counts instances from the modelled graph and body where
possible; estimated counts are labelled (count_basis).

A slot is filled when its value is measured or derived. It is a blank when
inferred, guessed, unknown or absent. The model state per slot is
  simulated  the model uses the value
  default    the model runs on a placeholder (guessed) or borrowed value
  absent     the mechanism is not simulated at all

    uv run python scripts/blank_ledger.py
Writes data/derived/blank_ledger.csv.
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

import numpy as np
import pandas as pd
import yaml

from flyemu import connectome, profiles
from flyemu.registry import Policy, Registry

REPO = Path(__file__).resolve().parents[1]
D = REPO / "data" / "derived"

# Estimated counts: value, basis, source
ESTIMATES = {
    "n_glia": (lambda c: round(0.1 * c["n_cells"]), "inferred",
               "glia ~10% of cells in the adult fly CNS (Kremer et al. 2017)"),
    "n_glia_types": (lambda c: 6, "inferred",
                     "perineurial, subperineurial, cortex, ensheathing, astrocyte-like, "
                     "wrapping (Freeman 2015)"),
    "n_plastic_classes": (lambda c: 15, "inferred",
                          "15 mushroom body compartments (Aso et al. 2014); other plastic "
                          "sites not counted"),
    "n_peptides": (lambda c: 50, "inferred", "~50 neuropeptide genes (Nässel & Zandawala 2019)"),
    "n_clock_types": (lambda c: 9, "inferred",
                      "s-LNv, l-LNv, 5th-LNv, LNd, LPN, DN1a, DN1p, DN2, DN3 (~150 cells)"),
    "n_mech_organs": (lambda c: 10, "inferred",
                      "JO, FeCO, campaniform fields, hair plates, bristles, haltere, wing, "
                      "neck, abdominal stretch, pharyngeal"),
    "n_muscles": (lambda c: 300, "inferred",
                  "legs ~100, flight ~60 (power + steering, both sides), neck ~16, "
                  "haltere ~14, abdomen ~80, head/proboscis ~30; to be replaced by a "
                  "per-muscle list"),
}


def counts() -> tuple[dict, dict]:
    reg = Registry(Policy.MINIMAL)
    profiles.apply(reg, "m2")
    conn = connectome.build(reg, min_synapses=5)
    n = conn.neurons
    t = n.type.fillna("")
    types = np.where(t == "", "#" + n.bodyId.astype(str), t)
    nt = n.predictedNt.fillna("unclear").str.lower()
    cen = pd.read_csv(D / "sensory_census.csv")
    c = dict(
        n_cells=len(n), n_types=len(pd.unique(types)), n_edges=conn.n_edges,
        n_syn=int(conn.weight_syn.sum()),
        n_mod_types=int(pd.unique(types[nt.isin(["dopamine", "serotonin", "octopamine"]).to_numpy()]).size),
        n_sensory_groups=len(cen), n_orn_types=53,
        n_photoreceptors=len(pd.read_csv(D / "retinotopy.csv")),
        n_motor=int(n.superclass.isin(["vnc_motor", "cb_motor"]).sum()),
        n_segments=70, n_joints=103,
    )
    basis = {k: "measured" for k in c}
    basis.update(n_segments="derived", n_joints="derived", n_photoreceptors="derived",
                 n_sensory_groups="derived")
    for k, (f, b, src) in ESTIMATES.items():
        c[k] = f(c)
        basis[k] = f"{b}: {src}"
    return c, basis


def main() -> None:
    c, cbasis = counts()
    onto = yaml.safe_load((REPO / "data" / "ontology" / "fly_information.yaml").read_text())
    rows = []
    for e in onto:
        n_inst = int(eval(str(e["count"]), {}, c))
        cb = e.get("count_basis") or cbasis.get(str(e["count"]), "measured")
        rows.append(dict(
            domain=e["domain"], quantity=e["quantity"], grain=e["grain"],
            instances=n_inst, per=int(e["per"]), slots=n_inst * int(e["per"]),
            model=e["model"], basis=e["basis"], measure_by=e.get("measure_by"),
            count_basis=cb, note=e.get("note"),
        ))
    df = pd.DataFrame(rows)
    # per-synapse / per-neuron / per-edge quantities are structural data
    # (measurable from EM in principle); everything else is a parameter slot
    df["scale"] = np.where(df.grain.isin(["synapse", "edge", "neuron", "photoreceptor"]),
                           "per-element", "parameter")
    df.to_csv(D / "blank_ledger.csv", index=False)

    filled = df.basis.isin(["measured", "derived"])
    print(f"{len(df)} measurable quantities; {df.slots.sum():,} slots\n")
    print("slots by model state and basis:")
    print(df.pivot_table(index="model", columns="basis", values="slots", aggfunc="sum",
                         fill_value=0).to_string())
    print(f"\nFILLED by data (measured/derived): {df[filled].slots.sum():,}")
    blanks = df[~filled]
    print(f"BLANK: {blanks.slots.sum():,} slots  "
          f"(running on a default: {blanks[blanks.model == 'default'].slots.sum():,}; "
          f"mechanism absent: {blanks[blanks.model == 'absent'].slots.sum():,}; "
          f"simulated but mixed/unknown: {blanks[blanks.model == 'simulated'].slots.sum():,})")
    for sc, g in df.groupby("scale"):
        f = g.basis.isin(["measured", "derived"])
        print(f"  {sc:11s}: {g.slots.sum():>13,} slots; filled {g[f].slots.sum():>12,}; "
              f"blank {g[~f].slots.sum():>12,} (default {g[~f & (g.model == 'default')].slots.sum():,}, "
              f"absent {g[~f & (g.model == 'absent')].slots.sum():,})")
    print("\nblank PARAMETER slots by domain:")
    blanks = blanks[blanks.scale == "parameter"]
    print(blanks.groupby(["domain", "model"]).slots.sum().unstack(fill_value=0).to_string())


if __name__ == "__main__":
    main()
