"""The mechanism registry: every brain-side mechanism beyond BAAIWorm's cells and brain_layers' lumped layers.

REGISTRY lists the modules (a bare name is wormemu.mech.<name>, unless a module of that name is already loaded, as
in the tests; a dotted name is imported as given), in call order.
Each module defines

    MECHANISMS  [(id, name, layer, default)]: brain_layers' tuple format. The id is the toggle name; default is "on",
                "off" or a named form (e.g. "well_mixed"); any value other than "off" counts as on.
    SPECS       [brain_layers.Spec]: every number the module's code uses. build_ledger reads them (all_specs), so a
                number exists in the ledger because the code uses it.
    build_cell  optional, build_cell(brain, name, hoc_cell, params, toggles): called while the brain builds each
                cell (after BAAIWorm's biophysics, before pointers and conductance targets exist), so a module can
                insert density mechanisms (mech/channels)
    class Mech  __init__(self, brain, params, toggles): may add NEURON sections, point processes or synapses
                reset(self)
                step(self, ctx, dt_ms) -> dict with any of
                    I_pA     array (n_cells), pA into each soma; summed over mechanisms
                    act_add  array (95, BWM_NAMES order), added to body-wall muscle activation, then clipped to [0, 1];
                             summed over mechanisms
                    g_scale  {name: array (n_cells)}, conductance multipliers, multiplied over mechanisms and applied
                             by the brain before fadvance; the names the brain knows are G_SCALE_NAMES
                    out      {name: value}, named outputs (pumps, eggs, temperature_C, energy, peptide_release, ...);
                             numbers and arrays sum over mechanisms, dicts merge by key with summing. A key that is
                             a BrainToBody field (OVERRIDES) replaces the lumped layer's value in the brain's output.

The brain builds a module's Mech only when one of its MECHANISMS toggles is not "off", and calls every built one each
step in REGISTRY order, after reading v and ca and before fadvance. `params` = {spec id: the ledger's value (template
or this worm's draw; a Series for a table row), or the Spec's template while the ledger has no row for it}. `toggles`
= the brain's whole toggle dict. A module whose MECHANISMS id equals a brain_layers mechanism id takes that toggle
over: the old lumped layer no longer runs (its specs stay in brain_layers until retired there).

ctx (Ctx): t_ms (time at the start of this step), obs (the BodyToBrain fields as a dict), v (mV) and ca (uM) per cell
in brain.cell_names order, names, is_muscle, outputs. ctx.outputs holds every mechanism's `out` from the previous
step, updated in place by each mechanism earlier in REGISTRY order this step, so a module reads another's output
with at most one step of lag (e.g. outputs['coelomocyte_uptake_per_s'], outputs['temperature_C'],
outputs['peptide_release'] = {peptide gene, or "gene@compartment" with a name from
mech.neuromod.COMPARTMENTS: molecules/s}, read by neuromod; outputs['ma_release_scale'] = array (n_cells), a
multiplier on each cell's amine release, read by neuromod; outputs['energy_fraction'] = the energy reserve as a
fraction of a well-fed worm's (0 to 1; absent = fed), read by slow_signalling and learning).
"""
from __future__ import annotations

import importlib
import sys
from dataclasses import dataclass, field

import numpy as np

REGISTRY: list[str] = ["structure_rules", "channels", "channel_forms", "capool", "ca_volume", "k2p_leak", "receptors",
                       "drugs", "plasticity", "slow_signalling", "pathogen", "learning", "neuromod", "noise",
                       "temperature", "senses_chem", "senses_touch", "senses_proprio",
                       "muscle_bwm", "organs_pharynx", "organs_intestine", "organs_egglaying", "glia", "glia_release",
                       "organs_other",
                       "cells_passive",
                       "pumps", "metabolism", "observation"]

# the conductances the brain can scale per cell (g_scale names): each BAAIWorm channel's somatic density
# (BAAIWorm's insert order, wormemu.brain.CHANNELS without the Ca pool), mech/channels' added Nicoletti 2024 channels
# (on the somas that have them) and the somatic leak
CHANNEL_NAMES = ("slo1_unc2", "egl2", "shl1", "kqt3", "unc2", "kvs1", "slo1_egl19", "slo2_unc2", "irk", "egl36",
                 "egl19", "cca1", "shk1", "slo2_egl19", "nca", "kcnl", "kqt1", "unc103", "exp2", "slo1iso", "slo2iso")
# the ionotropic receptor classes (wormemu.mech.receptors.CLASSES, row 7)
RECEPTOR_CLASSES = ("lacr", "acr16", "nachr", "acc", "glr", "nmr", "glucl", "gabacl", "gabacat", "mod1", "lgc55",
                    "lgc53", "acr23")
# also: "release" (per presynaptic cell, multiplies the cleft transmitter of every synapse it makes) and
# "rec_<class>" (per postsynaptic cell, multiplies that receptor class's conductance at its synapses); these act on
# wsyn synapses only (receptor_kinetics not off)
G_SCALE_NAMES = tuple(f"dens_{c}" for c in CHANNEL_NAMES) + ("leak", "release") + tuple(f"rec_{c}" for c in
                                                                                       RECEPTOR_CLASSES)
OVERRIDES = ("pumps", "eggs_laid", "expulsions", "pharynx_activation", "enteric_activation", "sex_muscle_activation",
             "gcamp_dff", "pressure_scale")


@dataclass
class Ctx:
    t_ms: float
    obs: dict
    v: np.ndarray
    ca: np.ndarray
    names: list
    is_muscle: np.ndarray
    outputs: dict = field(default_factory=dict)


def modules(registry=None):
    """The registered modules, imported, in REGISTRY order."""
    out = []
    for name in (REGISTRY if registry is None else registry):
        out.append(sys.modules.get(name) or importlib.import_module(name if "." in name else f"{__name__}.{name}"))
    return out


def all_specs(registry=None):
    """Every registered module's SPECS (for build_ledger)."""
    return [s for m in modules(registry) for s in m.SPECS]


def all_mechanisms(registry=None):
    """Every registered module's MECHANISMS tuples (for build_ledger and the brain's toggle defaults)."""
    return [t for m in modules(registry) for t in m.MECHANISMS]


def is_on(value) -> bool:
    return value not in ("off", False, None)


def merge(acc: dict, out: dict) -> dict:
    """Add one mechanism's `out` into the step's accumulated outputs (numbers and arrays sum; dicts merge)."""
    for k, x in out.items():
        if k not in acc:
            acc[k] = dict(x) if isinstance(x, dict) else x
        elif isinstance(x, dict):
            d = acc[k]
            for kk, xx in x.items():
                d[kk] = d.get(kk, 0.0) + xx
        else:
            acc[k] = acc[k] + x
    return acc


def params_for(module, spec) -> dict:
    """{spec id: value} for one module: the worm's ledger value where the ledger has the row, else the template."""
    return {s.id: spec.values.get(s.id, s.template) for s in module.SPECS}
