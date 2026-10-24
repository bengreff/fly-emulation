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
    "synapse:all|structural_plasticity": (
        "N31", 0.0, "synapse addition and removal during life (experience, sleep)"),
    "cell_type:all|homeostatic_plasticity": (
        "N32", 0.0, "activity-dependent regulation of channel densities toward a set point"),
    "glia:all|astrocyte_model": (
        "N33", 0.0, "astrocyte uptake, OA/TA-gated Ca signalling and glial coupling "
                    "(FIDELITY_LADDER rung 7)"),
    "synapse:other_sites|plasticity": (
        "N34", 0.0, "plasticity outside the mushroom body and ring (AL, visual, courtship)"),
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
    # S7 state:immune|model and S8 state:reproductive|model left in s23 for CONSTANT_STATES below
    "development:all|model": (
        "D1", 0.0, "development model: lineage, birth order, maturation and rearing history "
                   "set identity, wiring and intrinsic values (construction time, not lifetime)"),
}


# Ruled constant states (Director, 24 Oct 2026 00:55; DECISIONS 24 Oct): the required level of these rows is one
# stated condition held for the whole run, not a dynamic model. key -> (mechanism id, the value, the condition,
# its validity range). Any other value is refused.
CONSTANT_STATES = {
    "state:immune|model": (
        "S7", 0.0, "healthy, uninfected, unparasitised, conventionally reared laboratory fly: no immune activation "
                   "and no microbiome-dependent effect on sleep, feeding, activity or metabolism",
        "flies with infection, immune challenge or axenic rearing are outside the model (Kuo 2014; Schretter "
        "2018); validation data must come from healthy conventionally reared flies"),
    "state:reproductive|model": (
        "S8", 0.0, "naive (virgin) mature male: no mating history and no courtship experience; reproductive state "
                   "held constant (the connectome male was 5 days old, past the 72 h courtship maturation)",
        "mated or courtship-conditioned males and mating-state effects on sleep, feeding and aggression are "
        "outside the model; validation data must come from virgin males"),
}


def read(reg) -> None:
    """Read every stub switch at its neutral value; refuse anything else. Read every ruled constant state at
    its one modelled value; refuse anything else."""
    for key, (mech, value, condition, validity) in CONSTANT_STATES.items():
        entity, prop = key.split("|")
        v = reg.require(entity, prop, units="enum",
                        model_use=f"{mech} constant state (ruled level): {condition}",
                        subsystem="state", minimal=value, conventional=value,
                        minimal_note=f"{value:g}: the one modelled state; validity: {validity}")
        if float(v) != value:
            raise NotImplementedError(
                f"{key} = {v}: {mech} is modelled as one constant state only ({condition})")
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
