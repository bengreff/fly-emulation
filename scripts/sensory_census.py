"""Sensory census: every sensory neuron in the modelled graph, assigned a
modality, body region, sensed physical variable and transduction model family.

One row per sensory cell type (untyped cells grouped by class/subclass).
Every assignment carries a basis label, following the project rule:

  measured   observed directly (e.g. an immunostained transmitter)
  derived    computed from measured annotation by a stated rule
  inferred   from literature priors, homology or naming, not this dataset
  unknown    no assignment possible yet (a counted blank)

    uv run python scripts/sensory_census.py
Writes data/derived/sensory_census.csv and prints the blank count.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

import numpy as np
import pandas as pd

from flyemu.sensory import ENCODES

REPO = Path(__file__).resolve().parents[1]
C = REPO / "data" / "cache"

# (match on class, subclass, type regex) -> (modality, organ, physical variable,
# transduction family, where parameters would come from, implemented now,
# basis of the VARIABLE assignment). First match wins; order matters.
RULES = [
    # --- vision
    (dict(cls="visual", typ=r"^R[1-6]|^R1-R6"), ("vision", "compound eye R1-R6",
     "irradiance per ommatidium, Rh1 spectrum", "graded phototransduction",
     "opsin spectra; Juusola/Hardie recordings", "partial: luminance, retinotopic (derived)", "derived")),
    (dict(cls="visual", typ=r"^R7d|^R8d"), ("vision", "dorsal rim R7/R8",
     "polarised skylight, UV/blue", "graded phototransduction",
     "Weir/Wernet recordings", "partial: luminance only", "derived")),
    (dict(cls="visual", typ=r"^R7|^R8"), ("vision", "compound eye R7/R8",
     "irradiance per ommatidium, Rh3-Rh6 spectra", "graded phototransduction",
     "opsin spectra", "partial: luminance, retinotopic (derived)", "derived")),
    (dict(cls="visual", typ=r"HBeyelet"), ("vision", "Hofbauer-Buchner eyelet",
     "ambient light (circadian)", "slow irradiance integrator", "Helfrich-Förster",
     "none", "derived")),
    (dict(cls="visual"), ("vision", "compound eye, unassigned photoreceptor",
     "irradiance", "graded phototransduction", "opsin spectra", "partial", "derived")),
    # --- olfaction and chemical senses
    (dict(cls="olfactory", typ=r"^ORN_V$"), ("olfaction", "antenna ab1C",
     "CO2 concentration", "receptor dose-response", "Jones 2007; Suh 2004",
     "none", "derived")),
    (dict(cls="olfactory"), ("olfaction", "antenna / maxillary palp ORN",
     "odorant concentrations (receptor-specific)", "receptor tuning + adaptation",
     "DoOR; Hallem & Carlson 2006; Nagel & Wilson 2011", "none", "derived")),
    # male-cns class labels for these two are the reverse of their putative
    # modalities (Marin et al. 2020; docs/SENSORS_CHEMO.md)
    (dict(typ=r"^HRN_VP1l$"), ("thermosensation", "sacculus VP1l (cooling, putative)",
     "temperature decrease", "hot/cold phasic-tonic cells", "Marin 2020",
     "none", "inferred")),
    (dict(typ=r"^TRN_VP1m$"), ("hygrosensation", "VP1m (humid, putative)",
     "relative humidity", "dry/moist opponent cells", "Marin 2020",
     "none", "inferred")),
    (dict(cls="hygrosensory"), ("hygrosensation", "sacculus / arista",
     "relative humidity", "dry/moist opponent cells", "Enjin 2016; Knecht 2016",
     "none", "derived")),
    (dict(cls="thermosensory"), ("thermosensation", "arista / sacculus",
     "temperature and its rate of change", "hot/cold phasic-tonic cells",
     "Gallio 2011; Budelli 2019", "none", "derived")),
    (dict(cls="gustatory", sub=r"labellar bristle|taste peg|pharyngeal"), ("taste",
     "labellum / pharynx", "tastant concentrations at contact",
     "GRN class dose-response", "LB/PhG types by receptor line (Cell 2026)",
     "none", "derived")),
    (dict(cls="gustatory"), ("taste", "leg / wing taste bristle",
     "tastant concentrations at contact", "GRN class dose-response",
     "Ling 2014; Thoma 2016", "none", "derived")),
    (dict(sub=r"taste bristle"), ("taste", "taste bristle",
     "tastant concentrations at contact", "GRN class dose-response",
     "taste literature", "none", "derived")),
    (dict(cls="chemosensory"), ("chemosensation", "body chemosensor",
     "unknown chemical", "unknown", "none", "none", "inferred")),
    # --- mechanosensation
    (dict(sub=r"wind_gravity"), ("mechanosensation", "Johnston's organ C/E",
     "antennal a2-a3 sustained deflection (wind, gravity)", "deflection tuning",
     "Kamikouchi 2009; Yorozu 2009", "none", "derived")),
    (dict(sub=r"auditory"), ("mechanosensation", "Johnston's organ A/B",
     "antennal vibration (near-field sound)", "band-pass deflection",
     "Kamikouchi 2009; Matsuo 2014", "none", "derived")),
    (dict(typ=r"^JO-"), ("mechanosensation", "Johnston's organ",
     "antennal a2-a3 deflection", "deflection tuning", "Kamikouchi 2009",
     "none", "derived")),
    (dict(sub=r"chordotonal organ"), ("proprioception", "leg chordotonal organ",
     "joint angle and velocity (claw/hook/club)", "angle/velocity tuning",
     "Mamiya 2018, 2023", "partial: tanh(angle)", "derived")),
    (dict(sub=r"campaniform sensilla"), ("proprioception", "campaniform sensilla",
     "cuticular strain (load)", "strain transduction", "Dinges 2021; Zill",
     "partial: segment load proxy", "derived")),
    (dict(sub=r"hair plate"), ("proprioception", "hair plate",
     "joint angle near limit", "threshold deflection", "Pratt 2023 (unverified)",
     "partial: tanh(angle)", "derived")),
    (dict(sub=r"haltere"), ("proprioception", "haltere campaniforms",
     "haltere base strain (Coriolis, body rotation)", "phase-locked strain",
     "Dickinson 1999; Fayyazuddin & Dickinson", "none (haltere passive)", "derived")),
    (dict(cls="mechanosensory_proprioceptive", sub=r"wing"), ("proprioception",
     "wing campaniforms / tegula", "wing load and bending", "phase-locked strain",
     "Dickerson 2014", "none", "derived")),
    (dict(cls="mechanosensory_proprioceptive", sub=r"neck|notum"), ("proprioception",
     "neck / notum proprioceptor", "head-thorax angle or cuticle strain",
     "angle tuning", "prosternal organ literature", "none", "inferred")),
    (dict(cls="mechanosensory_proprioceptive", sub=r"abdomen"), ("proprioception",
     "abdominal proprioceptor", "abdominal segment stretch/angle", "unknown",
     "none located", "none", "inferred")),
    (dict(cls="mechanosensory_proprioceptive", sub=r"^leg$"), ("proprioception",
     "leg proprioceptor, organ unassigned", "joint angle/load (organ unknown)",
     "unknown", "none", "none", "inferred")),
    (dict(typ=r"^BM"), ("touch", "head bristle (BM_*: interommatidial, vibrissae, "
     "palp, haustellum, occipital)", "bristle deflection at contact",
     "phasic deflection", "Eichler et al. head bristle atlas; Hampel 2015",
     "none", "derived")),
    (dict(typ=r"^TPMN"), ("mechanosensation", "taste peg mechanosensory neuron",
     "labellar taste-peg deflection (food contact/texture)", "phasic deflection",
     "Zhou 2019 (unverified)", "none", "derived")),
    (dict(sub=r"mechanosensory bristle|^leg$|notum|wing"), ("touch",
     "mechanosensory bristle", "bristle deflection at contact", "phasic deflection",
     "Walker 2000; Corfas & Dudai", "partial: leg contact force", "derived")),
    (dict(sub=r"grooming"), ("touch", "grooming-relevant bristles (head)",
     "bristle deflection at contact", "phasic deflection", "Hampel 2015",
     "none", "derived")),
    (dict(sub=r"pharyngeal"), ("mechanosensation", "pharyngeal mechanosensor",
     "food flow / pharyngeal stretch", "unknown", "none", "none", "derived")),
    (dict(cls="mechanosensory"), ("mechanosensation", "mechanosensor, organ unassigned",
     "unknown mechanical variable", "unknown", "none", "none", "inferred")),
    (dict(cls="unknown_sensory", sub=r"abdomen"), ("unknown", "abdominal sensory",
     "unknown (candidates: stretch, chemical, reproductive)", "unknown",
     "none", "none", "unknown")),
    (dict(cls="unknown_sensory"), ("unknown", "sensory, modality unknown",
     "unknown", "unknown", "none", "none", "unknown")),
]


def match(row, spec) -> bool:
    cls = row["class"] if isinstance(row["class"], str) else ""
    sub = row.subclass if isinstance(row.subclass, str) else ""
    typ = row.type if isinstance(row.type, str) else ""
    if "cls" in spec and cls != spec["cls"]:
        return False
    if "sub" in spec and not re.search(spec["sub"], sub):
        return False
    if "typ" in spec and not re.search(spec["typ"], typ):
        return False
    return True


def main() -> None:
    n = pd.read_parquet(C / "male_cns_neurons.parquet").merge(
        pd.read_parquet(C / "male_cns_extra.parquet"), on="bodyId")
    n = n[(n.status == "Traced") | n.type.notna()]
    s = n[n.superclass.fillna("").str.contains("sensory")].copy()
    s["group"] = s.type.fillna("untyped:" + s["class"].fillna("?") + "/" +
                               s.subclass.fillna("?"))
    rows = []
    for g, grp in s.groupby("group"):
        r0 = grp.iloc[0]
        spec = next((out for m, out in RULES if match(r0, m)), None)
        if spec is None:
            spec = ("unknown", "unassigned", "unknown", "unknown", "none", "none", "unknown")
        modality, organ, var, family, source, impl, basis = spec
        # What M v1 actually drives is decided by sensory.ENCODES (subclass
        # match), not by the rule table's intent.
        sub = r0.subclass if isinstance(r0.subclass, str) else ""
        if sub in ENCODES:
            impl = f"driven as {ENCODES[sub]}"
            if modality not in ("touch", "proprioception"):
                impl = f"WRONG: {modality} cells driven as {ENCODES[sub]}"
        else:
            impl = "none" if not impl.startswith("partial") or modality != "vision" else impl
        rows.append(dict(
            group=g, n_cells=len(grp), superclass=r0.superclass, cls=r0["class"],
            subclass=r0.subclass, entry_nerves=";".join(sorted(grp.entryNerve.dropna().unique())[:4]),
            sides=";".join(f"{k}{v}" for k, v in grp.somaSide.fillna("?").value_counts().items()),
            modality=modality, organ=organ, physical_variable=var,
            transduction_family=family, parameter_source=source,
            implemented=impl, variable_basis=basis,
            parameters_basis="unknown" if family == "unknown" else "inferred",
        ))
    df = pd.DataFrame(rows).sort_values(["modality", "n_cells"], ascending=[True, False])
    out = REPO / "data" / "derived" / "sensory_census.csv"
    df.to_csv(out, index=False)

    cells = df.n_cells.sum()
    print(f"{cells:,} sensory neurons in {len(df):,} groups -> {out.relative_to(REPO)}")
    by = df.groupby("modality").agg(groups=("group", "size"), cells=("n_cells", "sum"))
    by["implemented_cells"] = df[~df.implemented.isin(["none"]) & ~df.implemented.str.startswith("WRONG")].groupby("modality").n_cells.sum()
    by["wrongly_driven"] = df[df.implemented.str.startswith("WRONG")].groupby("modality").n_cells.sum()
    print(by.fillna(0).astype(int).sort_values("cells", ascending=False).to_string())
    print("\nvariable assignment basis (cells):")
    print(df.groupby("variable_basis").n_cells.sum().to_string())
    unk = df[df.variable_basis == "unknown"]
    print(f"\nBLANK: {unk.n_cells.sum():,} cells in {len(unk)} groups have no sensed "
          f"variable; every one of {len(df)} groups needs transduction parameters "
          f"({(df.parameters_basis != 'measured').sum()} not yet measured).")


if __name__ == "__main__":
    main()
