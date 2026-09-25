"""The blank ledger: every parameter a complete possible fly needs, counted.

A "blank" is a parameter slot whose current value is not measured or derived:
it is inferred (a shared default, a borrowed precedent, a fit) or unknown.
The grain is declared per row. It is the finest grain the data could plausibly
constrain, not the grain the model currently uses (which is one shared value
for most rows). So the ledger counts the slots a complete model must fill, and
says how each is filled today.

Declared grain (an assumption, recorded here and in DECISIONS):
  neuron biophysics      per cell type (untyped traced cells count as own type)
  synaptic efficacy      factorised: per presynaptic type (release) x per
                         postsynaptic type (input gain), not per type pair
  glutamate sign         per postsynaptic type receiving glutamate (receptor)
  monoamine action       per modulatory presynaptic type
  electrical coupling    per cell type (partners and conductance)
  sensory transduction   per sensory group in data/derived/sensory_census.csv
  motor                  per motor neuron (target, force, twitch) and per
                         muscle (mechanics)
  body passive mechanics per joint

    uv run python scripts/blank_ledger.py
Writes data/derived/blank_ledger.csv and docs-ready totals.
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

import numpy as np
import pandas as pd

from flyemu import connectome, profiles
from flyemu.registry import Policy, Registry

REPO = Path(__file__).resolve().parents[1]
D = REPO / "data" / "derived"

# Parameters per transduction family (count of free parameters in the model
# form that would be used; an inference about model form, not data).
FAMILY_PARAMS = {
    "graded phototransduction": 4,       # gain, time constant, adaptation, spectrum
    "slow irradiance integrator": 2,
    "receptor tuning + adaptation": 4,   # odour tuning vector counted separately
    "receptor dose-response": 3,
    "dry/moist opponent cells": 3,
    "hot/cold phasic-tonic cells": 4,
    "GRN class dose-response": 3,
    "deflection tuning": 4,
    "band-pass deflection": 4,
    "angle/velocity tuning": 5,
    "strain transduction": 4,
    "threshold deflection": 3,
    "phase-locked strain": 4,
    "phasic deflection": 3,
    "angle tuning": 3,
    "unknown": 4,                        # placeholder size for an unknown model
}


def main() -> None:
    reg = Registry(Policy.MINIMAL)
    profiles.apply(reg, "m2")
    conn = connectome.build(reg, min_synapses=5)
    n = conn.neurons
    t = n.type.fillna("")
    types = np.where(t == "", "#" + n.bodyId.astype(str), t)
    n_types = len(pd.unique(types))
    n_cells = len(n)
    nt = n.predictedNt.fillna("unclear").str.lower()
    pre = np.repeat(np.arange(conn.n), np.diff(conn.indptr))
    post = conn.indices

    rows = []

    def add(subsystem, parameter, grain, n_slots, instances, basis, filled_by, note=""):
        rows.append(dict(subsystem=subsystem, parameter=parameter, grain=grain,
                         slots=int(n_slots), instances=int(instances),
                         basis=basis, filled_by=filled_by, note=note))

    # --- structure (measured/derived, not blanks) ------------------------------
    add("structure", "chemical connectivity (synapse counts)", "per edge",
        conn.n_edges, conn.n_edges, "measured", "male-cns:v1.0")
    add("structure", "cell identity and type", "per neuron", n_cells, n_cells,
        "measured", "male-cns annotation")
    ach_gaba = nt.isin(["acetylcholine", "gaba", "histamine"])
    add("structure", "transmitter sign (ACh, GABA, histamine)", "per presynaptic type",
        pd.unique(types[ach_gaba.to_numpy()]).size, int(ach_gaba.sum()), "derived",
        "predicted NT + standard pharmacology")

    # --- neuron biophysics -----------------------------------------------------
    for p in ["tau_m", "v_rest", "v_th", "v_reset", "t_ref", "tau_syn",
              "spiking vs graded", "adaptation increment", "adaptation tau"]:
        add("neuron", p, "per cell type", n_types, n_cells, "inferred",
            "one shared default (Shiu 2024 / declared)")

    # --- synapses --------------------------------------------------------------
    add("synapse", "release strength", "per presynaptic type", n_types, conn.n_edges,
        "inferred", "one shared value, fitted by return-to-rest (0.165 mV)")
    add("synapse", "postsynaptic input gain", "per postsynaptic type", n_types,
        conn.n_edges, "inferred", "one shared value (with m1/m2 masks)")
    glu_post = pd.unique(types[post[(nt.to_numpy() == "glutamate")[pre]]])
    add("synapse", "glutamate response sign (GluCl vs iGluR)", "per postsynaptic type",
        glu_post.size, int(((nt.to_numpy() == "glutamate")[pre]).sum()), "inferred",
        "all inhibitory (convention, F-SIGN-1)")
    unc = nt.to_numpy() == "unclear"
    add("synapse", "sign of 'unclear'-transmitter cells", "per presynaptic type",
        pd.unique(types[unc]).size, int(unc.sum()), "inferred",
        "excitatory by Shiu convention; AL LNs inhibitory (m2)")
    add("synapse", "conduction delay", "per presynaptic type", n_types, conn.n_edges,
        "inferred", "one shared 1.8 ms", "derivable from skeleton path length")
    add("synapse", "short-term plasticity (U, tau_rec)", "per presynaptic type",
        2 * n_types, conn.n_edges, "unknown", "absent")
    mono = nt.isin(["dopamine", "serotonin", "octopamine"]).to_numpy()
    add("synapse", "monoamine action (targets, receptor, effect, timescale)",
        "per modulatory type", 4 * pd.unique(types[mono]).size, int(mono.sum()),
        "unknown", "treated as fast excitation (Shiu convention)")
    add("synapse", "electrical coupling (partners, conductance)", "per cell type",
        2 * n_types, n_cells, "unknown", "absent except 3 GF pairs (option, off)")
    add("synapse", "long-term plasticity rule", "per synapse class (KC>MBON etc.)",
        1, 1, "unknown", "absent", "slot count to be refined when Tier 2 starts")

    # --- sensory ---------------------------------------------------------------
    cen = pd.read_csv(D / "sensory_census.csv")
    for fam, g in cen.groupby("transduction_family"):
        k = FAMILY_PARAMS.get(fam, 4)
        add("sensory", f"transduction: {fam}", "per sensory group", k * len(g),
            g.n_cells.sum(), "unknown" if fam == "unknown" else "inferred",
            "none" if fam == "unknown" else "family chosen from literature; values not set",
            f"{len(g)} groups x {k} params")
    unk = cen[cen.variable_basis == "unknown"]
    add("sensory", "sensed physical variable", "per sensory group", len(unk),
        unk.n_cells.sum(), "unknown", "none", "modality not identifiable from annotation")
    cov = pd.read_csv(D / "orn_tuning_coverage.csv")
    have = cov[cov.n_units > 0]; miss = cov[cov.n_units == 0]
    add("sensory", "odour tuning vector (relative)", "per ORN type", len(have),
        have.cells.sum(), "measured", "DoOR 2.0 consensus (normalised 0-1)",
        "data/derived/orn_tuning_door.csv")
    add("sensory", "odour tuning vector", "per ORN type", len(miss), miss.cells.sum(),
        "unknown", "none", ", ".join(miss.orn_type))
    add("sensory", "odour response absolute scale (SFR, Rmax)", "per ORN type",
        2 * len(cov), cov.cells.sum(), "inferred",
        "not set; Hallem & Carlson 2006 gives spikes/s for 24 receptors (heterologous)")

    # --- motor -----------------------------------------------------------------
    mn = n[n.superclass.isin(["vnc_motor", "cb_motor"])]
    leg = pd.read_csv(D / "manc_leg_motor_neurons.csv")
    mapped = int(pd.to_numeric(mn.mancBodyid, errors='coerce').isin(leg.bodyId).sum())
    add("motor", "motor neuron -> muscle target", "per motor neuron", len(mn) - mapped,
        len(mn) - mapped, "unknown", "none",
        f"{mapped} leg MNs mapped (derived, F-DATA-1); see MOTOR_TARGETS.md")
    add("motor", "motor neuron -> muscle target (mapped)", "per motor neuron", mapped,
        mapped, "derived", "MANC mapping transferred to male-cns")
    add("motor", "force per spike, twitch rise, twitch decay", "per motor neuron",
        3 * len(mn), len(mn), "inferred", "one shared guess (force_per_spike)")
    n_muscles = leg.muscle.nunique() * 6 + 60   # leg muscles x legs + non-leg estimate
    add("motor", "muscle mechanics (Hill: Fmax, l0, vmax, tau_act, passive)",
        "per muscle", 5 * n_muscles, n_muscles, "inferred",
        "torque motors, one activation tau",
        "muscle count: 22 leg-muscle labels x 6 legs + ~60 non-leg (inferred)")

    # --- body ------------------------------------------------------------------
    add("body", "segment masses and inertias", "per segment", 70, 70, "derived",
        "flybody + 52 weighed flies (F-MASS-1)")
    add("body", "joint ranges", "per joint", 103, 103, "derived", "F-BODY-3")
    add("body", "passive joint stiffness and damping", "per joint", 2 * 103, 103,
        "inferred", "documented guesses (F-STIFF-1)")

    df = pd.DataFrame(rows)
    df.to_csv(D / "blank_ledger.csv", index=False)
    blanks = df[df.basis.isin(["inferred", "unknown"])]
    print(f"cell types (incl. untyped singletons): {n_types:,}; cells {n_cells:,}\n")
    print(df.groupby(["subsystem", "basis"]).slots.sum().unstack(fill_value=0).to_string())
    print(f"\nBLANK SLOTS: {blanks.slots.sum():,}  "
          f"(inferred {df[df.basis=='inferred'].slots.sum():,}, "
          f"unknown {df[df.basis=='unknown'].slots.sum():,})")
    print(f"filled by data (measured+derived): {df[~df.basis.isin(['inferred','unknown'])].slots.sum():,}")
    print("\nlargest blank rows:")
    print(blanks.sort_values("slots", ascending=False)[["subsystem", "parameter", "grain", "slots", "basis"]].head(12).to_string(index=False))


if __name__ == "__main__":
    main()
