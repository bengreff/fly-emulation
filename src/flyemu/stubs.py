"""Registered stubs: template mechanisms that are inventoried but not built.

Session 12 blanks audit (docs/BLANKS_AUDIT.md). Each stub owns a ledger slot in
data/ontology/fly_information.yaml and an entry in data/model/mechanisms.yaml
(status absent). The organism reads every stub switch so the registry inventory
lists it; the neutral value is the current model exactly (nothing is computed).
Any other value is refused: a stub must never be mistaken for a built mechanism.
"""
from __future__ import annotations

# key -> (mechanism id, neutral value, what the non-neutral setting would build)
STUBS = {
    # N29 synapse:all|per_synapse_parameters left the stubs in s12 (rung 8 STP per connection
    # class built, lif._stp_connections); its other per-synapse values are refused there.
    # N30 cell_type:all|n_compartments left in s20 (fly2: two compartments for the cells of
    # two_compartment.csv, lif._two_compartments); it is still read there and refused when set
    # N31 synapse:all|structural_plasticity, N32 cell_type:all|homeostatic_plasticity and N34
    # synapse:other_sites|plasticity left in s29 (fly2: built in lifetime.py, read by lif.default_params)
    "glia:all|astrocyte_model": (
        "N33", 0.0, "astrocyte uptake, OA/TA-gated Ca signalling and glial coupling "
                    "(FIDELITY_LADDER rung 7)"),
    "sense:all|efferent_gain_control": (
        "B24", 0.0, "central (e.g. octopaminergic) control of sense-organ gain"),
    "sense:active|sensor_muscles": (
        "B25", 0.0, "retinal and antennal muscles (active sensing movements)"),
    "body:cuticle|compliance": (
        "B26", 0.0, "segment and thorax elasticity (flight resonance, cuticle strain)"),
    "state:circulation|model": (
        "B27", 0.0, "heart, hemolymph flow and tracheal ventilation"),
    "state:hemolymph|ion_model": (
        "S6", 0.0, "hemolymph ion concentrations setting the reversal potentials"),
    "state:immune|model": (
        "S7", 0.0, "immune state and gut microbiome acting on sleep and feeding"),
    "state:reproductive|model": (
        "S8", 0.0, "male reproductive state, mating history and pheromone production"),
    "development:all|model": (
        "D1", 0.0, "development model: lineage, birth order, maturation and rearing history "
                   "set identity, wiring and intrinsic values (construction time, not lifetime)"),
}


def read(reg) -> None:
    """Read every stub switch at its neutral value; refuse anything else."""
    for key, (mech, neutral, what) in STUBS.items():
        entity, prop = key.split("|")
        v = reg.require(entity, prop, units="enum",
                        model_use=f"{mech} stub (not built): {what}",
                        subsystem="stub", minimal=neutral, conventional=neutral,
                        minimal_note=f"neutral {neutral:g}: the mechanism is absent "
                                     "(registered stub, docs/BLANKS_AUDIT.md)")
        if float(v) != neutral:
            raise NotImplementedError(
                f"{key} = {v}: {mech} is a registered stub, not built ({what})")
