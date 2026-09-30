"""The blank ledger, v3: every measurable quantity of a fly, counted.

Reads data/ontology/fly_information.yaml, which lists everything about the
animal's biology that could in principle be measured, whether or not the
model uses it. Counts instances from the modelled graph and body where
possible; estimated counts are labelled (count_basis).

A slot is filled when its value is measured or derived. It is a blank when
inferred, guessed, unknown or absent. The model state per slot is
  simulated  the model uses the value
  default    the model runs on a placeholder (guessed) or borrowed value
  absent     the mechanism is not simulated at all

v3 (session 11): every row names the mechanism that carries it (mech, from
data/model/mechanisms.yaml) and the grain at which the model's value actually
varies (fidelity). Each slot gets a source level, most to least informative:
measured > derived > rule (inferred per element) > prior (inferred per class
or globally) > mixed > guessed > absent. The headline metric is the share of
slots at each level, per grain and per mechanism.

    uv run python scripts/blank_ledger.py
Writes data/derived/blank_ledger.csv and data/derived/ledger_levels.csv.
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

import numpy as np
import pandas as pd
import yaml

from flyemu import connectome, model_data, profiles
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
    profiles.apply(reg, profiles.WORKING_PROFILE)
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


def filled_types(f: dict) -> set:
    """Distinct types (or cells, for bodyId-keyed files) with a row in a fill table."""
    t = pd.read_csv(REPO / f["file"], comment="#")
    if "param" in f:
        t = t[t.param == f["param"]]
    for col in ("male_cns_type", "type", "bodyId"):
        if col in t:
            return set(t[col].dropna().astype(str))
    return set(map(str, range(len(t))))


LEVELS = ["measured", "derived", "rule", "prior", "mixed", "guessed", "absent",
          "measured (unused)", "derived (unused)"]
GRAIN_GROUP = {
    "synapse": "synapse", "edge": "edge",
    "neuron": "cell", "motor neuron": "cell", "photoreceptor": "cell",
    "cell type": "type", "presynaptic type": "type", "postsynaptic type": "type",
    "transmitter x postsynaptic type": "type", "ORN type": "type", "photoreceptor type": "type",
    "clock neuron type": "type", "modulatory type": "type", "sensory group": "type",
    "synapse class": "class", "electrical pair class": "class", "organ type": "class",
    "glial type": "class", "peptide": "class", "peptide x target type class": "class",
    "tissue class": "class", "eye region": "class",
    "organism": "organism/world", "world": "organism/world",
}


def level(basis: str, fidelity: str) -> str:
    """Source level of one ledger row (see data/ontology/fly_information.yaml)."""
    if basis in ("measured", "derived"):
        return basis if fidelity != "none" else f"{basis} (unused)"
    if fidelity == "none":
        return "absent"
    if basis == "inferred":
        return "rule" if fidelity == "element" else "prior"
    if basis == "mixed":
        return "mixed"
    return "guessed"


def main() -> None:
    c, cbasis = counts()
    onto = yaml.safe_load((REPO / "data" / "ontology" / "fly_information.yaml").read_text())
    rows = []
    for e in onto:
        n_inst = int(eval(str(e["count"]), {}, c))
        cb = e.get("count_basis") or cbasis.get(str(e["count"]), "measured")
        base = dict(domain=e["domain"], quantity=e["quantity"], grain=e["grain"],
                    per=int(e["per"]), model=e["model"], basis=e["basis"],
                    measure_by=e.get("measure_by"), count_basis=cb, note=e.get("note"),
                    mech=e["mech"], fidelity=e["fidelity"])
        # per-type fills (session 8): {file, param?, basis, model?} -> split the entry
        left, seen = n_inst, set()
        for f in e.get("fills", []):
            keys = filled_types(f) - seen      # a type filled by an earlier table counts once
            seen |= keys
            k = min(len(keys), left)
            if k:
                rows.append({**base, "quantity": base["quantity"] + f" [filled: {Path(f['file']).name}]",
                             "instances": k, "slots": k * base["per"], "basis": f["basis"],
                             "model": f.get("model", base["model"]), "count_basis": "derived",
                             "fidelity": f.get("fidelity", "element")})
                left -= k
        rows.append({**base, "instances": left, "slots": left * base["per"]})
    df = pd.DataFrame(rows)
    # per-synapse / per-neuron / per-edge quantities are structural data
    # (measurable from EM in principle); everything else is a parameter slot
    df["scale"] = np.where(df.grain.isin(["synapse", "edge", "neuron", "photoreceptor"]),
                           "per-element", "parameter")
    df["level"] = [level(b, f) for b, f in zip(df.basis, df.fidelity)]
    df["grain_group"] = df.grain.map(GRAIN_GROUP).fillna("body part")
    df.to_csv(D / "blank_ledger.csv", index=False)
    levels_report(df)

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


def levels_report(df: pd.DataFrame) -> None:
    """Ledger v3: slots by source level, per grain and per mechanism."""
    mech = pd.DataFrame(yaml.safe_load((REPO / "data" / "model" / "mechanisms.yaml").read_text()))
    status = dict(zip(mech.id, mech.status))
    tot = df.slots.sum()
    lv = df.groupby("level").slots.sum().reindex(LEVELS, fill_value=0)
    print("=== ledger v3: slots by source level (all grains) ===")
    for k, v in lv.items():
        print(f"  {k:18s} {v:>13,}  {100 * v / tot:6.2f}%")
    data = lv[["measured", "derived"]].sum()
    print(f"  data in the model (measured+derived): {100 * data / tot:.2f}%; "
          f"+ rule-inferred: {100 * (data + lv['rule']) / tot:.2f}%; "
          f"data held but unused: {100 * lv[['measured (unused)', 'derived (unused)']].sum() / tot:.2f}%")
    # the slot count is dominated by per-synapse quantities (96%); also report each
    # measurable quantity with equal weight, and the slots outside the synapse grain
    q = df.assign(q=df.quantity.str.replace(r" \[filled: .*\]$", "", regex=True))
    w = q.pivot_table(index="q", columns="level", values="slots", aggfunc="sum", fill_value=0)
    w = w.div(w.sum(axis=1), axis=0).mean().reindex(LEVELS, fill_value=0)
    ns = df[df.grain_group != "synapse"].groupby("level").slots.sum().reindex(LEVELS, fill_value=0)
    print("  per quantity (each of %d quantities weighs 1): " % len(q.q.unique())
          + ", ".join(f"{k} {100 * v:.1f}%" for k, v in w.items() if v))
    print("  slots outside the synapse grain (%s): " % f"{ns.sum():,}"
          + ", ".join(f"{k} {100 * v / ns.sum():.1f}%" for k, v in ns.items() if v))
    print("\nshare of slots per grain (rows: grain; columns: level; %):")
    g = df.pivot_table(index="grain_group", columns="level", values="slots", aggfunc="sum", fill_value=0)
    g = g.reindex(columns=[c for c in LEVELS if c in g.columns])
    pct = (100 * g.div(g.sum(axis=1), axis=0)).round(1)
    pct.insert(0, "slots", g.sum(axis=1))
    print(pct.to_string())
    print("\nslots per mechanism (status from mechanisms.yaml):")
    m = df.pivot_table(index="mech", columns="level", values="slots", aggfunc="sum", fill_value=0)
    m = m.reindex(columns=[c for c in LEVELS if c in m.columns])
    m.insert(0, "status", [status.get(i, "-") for i in m.index])
    p = pd.read_csv(REPO / "data" / "model" / "parameters.csv", dtype=str, keep_default_na=False)
    p["data_bound"] = p.bound_basis.isin(list(model_data.BOUND_FROM_DATA))
    pu = p.groupby("mechanism_id").agg(unknowns=("param_id", "size"), bounded=("data_bound", "sum"))
    m = m.join(pu, how="left").fillna({"unknowns": 0, "bounded": 0}).astype({"unknowns": int, "bounded": int})
    print(m.to_string())
    bad = df[(df.fidelity == "none") != (df.model == "absent")]
    if len(bad):
        print(f"\nINCONSISTENT rows (fidelity none <=> model absent): {len(bad)}")
    # the per-session metric table: level x grain slots (appended by date)
    out = df.groupby(["grain_group", "level"]).slots.sum().rename("slots").reset_index()
    out.to_csv(D / "ledger_levels.csv", index=False)


def construction_report() -> None:
    """The construction state (CONSTRUCTION.md task 14) from data/model/."""
    md = model_data.load()
    bad = model_data.validate(md)
    st = model_data.construction_state(md)
    print("\n=== construction state (data/model/) ===")
    print(f"mechanisms: {st['n_mechanisms']} (have/partial/absent per tier)")
    print(st["mechanisms"].to_string())
    print(f"unknowns: {st['n_unknowns']}; bounds from data {st['bounded_by_data']} "
          f"(source read: {st['bounds_verified']}), guessed {st['n_unknowns'] - st['bounded_by_data']}; "
          f"fixed by measurement {st['fixed_by_measurement']}; wired to the model {st['wired']}")
    print("released by stage: " + ", ".join(f"{k}: {v}" for k, v in st["by_stage"].items()))
    print("prior labels: " + ", ".join(f"{k}: {v}" for k, v in st["by_label"].items()))
    print(f"legacy m4 body values outside biological bounds: {st['legacy_outside_bounds']}")
    print(f"validation problems: {len(bad)}" + ("" if not bad else "\n  " + "\n  ".join(bad)))


if __name__ == "__main__":
    main()
    construction_report()
