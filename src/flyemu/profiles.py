"""Named parameter profiles, each value with its own evidence label.

A profile is a set of `entity|property` values. Every entry carries a basis
(inferred or guessed) and a justification of its own; nothing borrowed from
another model is ever recorded as measured. Values enter through
`Registry.overrides`, and the registry records the label given here.

    ENTRY = (value, basis, justification)
"""
from __future__ import annotations

from .registry import Registry, Status

SHIU = "Shiu et al. 2024, Nature 634:210 (github.com/philshiu/Drosophila_brain_model)"
_I, _G = Status.INFERRED, Status.GUESSED

SHIU2024 = {
    "cell_type:all|tau_m": (20.0, _I, f"borrowed from {SHIU}: a generic insect neuron value "
                                      "used for every FlyWire neuron; not measured per type"),
    "cell_type:all|v_rest": (-52.0, _I, f"borrowed from {SHIU}; one value for every neuron"),
    "cell_type:all|v_th": (-45.0, _I, f"borrowed from {SHIU}; 7 mV above rest for every neuron"),
    "cell_type:all|v_reset": (-52.0, _I, f"borrowed from {SHIU}"),
    "cell_type:all|t_ref": (2.2, _I, f"borrowed from {SHIU}"),
    "cell_type:all|tau_s": (5.0, _I, f"borrowed from {SHIU}; a lumped synaptic decay"),
    "cell_type:all|conduction_delay": (1.8, _I, f"borrowed from {SHIU}; one delay for every edge"),
    "cell_type:all|background_noise": (0.0, _G, "no membrane noise: a modelling choice (Shiu "
                                                "2024 has none), not a claim that fly neurons are noiseless"),
    "cell_type:all|syn_reset_on_spike": (1.0, _G, f"model structure borrowed from {SHIU} (g reset "
                                                  "on spike); no biological measurement behind it"),
    "connection_class:all|efficacy_per_synapse": (0.275, _I, f"{SHIU}: calibrated on FlyWire "
                                                   "(female brain) to a sensory-to-motor response"),
    "transmitter:glutamate|sign": (-1.0, _I, "GluCl-mediated inhibition is widespread in the fly "
                                             "CNS (Liu & Wilson 2013 PNAS); per-target sign unknown (F-SIGN-1)"),
    "transmitter:dopamine|sign": (1.0, _G, f"treated as fast excitation, the {SHIU} convention; "
                                           "dopamine acts via metabotropic receptors, so this is a placeholder"),
    "transmitter:serotonin|sign": (1.0, _G, "fast excitation placeholder (Shiu convention); "
                                            "serotonin is modulatory"),
    "transmitter:octopamine|sign": (1.0, _G, "fast excitation placeholder (Shiu convention); "
                                             "octopamine is modulatory"),
    "transmitter:unclear|sign": (1.0, _G, "unknown transmitter treated as excitatory (Shiu "
                                          "convention); no evidence either way per cell"),
}

M1 = {
    **SHIU2024,
    "connection_class:all|efficacy_per_synapse": (0.165, _I, "fitted in this project: largest "
        "scale at which activity returns to rest after sugar GRN stimulation (F-GAIN-2), "
        "confirmed under calibration rule v2 with m2 (F-AL-1)"),
    "connection_class:onto_sensory_terminals|included": (0.0, _I, "sensory spikes start in the "
        "periphery; central input onto sensory terminals is presynaptic modulation a point "
        "neuron cannot represent (F-SENS-1). Removes real presynaptic inhibition"),
}

M2 = {
    **M1,
    "connection_class:cholinergic_AL_LN_to_PN_and_eLN|included": (0.0, _I, "eLN->PN "
        "transmission is electrical: unaffected by chemical block, abolished by shakB (Yaksi "
        "& Wilson 2010 Neuron 67:1034). eLN->eLN chemical efficacy unmeasured; removed with it (F-LN-1)"),
    "transmitter:unclear_in_AL_local_neurons|sign": (-1.0, _I, "AL local neurons are "
        "predominantly GABAergic or glutamatergic (Chou et al. 2010; Das et al. 2011); a "
        "class-level prior for 89 cells of unknown transmitter (F-LN-2)"),
}

KICK = 0.275 * 250   # Shiu 2024 Poisson input: w_syn x f_poi mV, forces a spike

PROFILES: dict[str, dict] = {
    "shiu2024": {"values": SHIU2024, "kick_mv": KICK},
    "m1": {"values": M1, "kick_mv": KICK},
    "m2": {"values": M2, "kick_mv": KICK},
}


def apply(reg: Registry, name: str) -> dict:
    prof = PROFILES[name]
    for k, (v, status, why) in prof["values"].items():
        reg.overrides.setdefault(k, v)
        reg.override_notes.setdefault(k, (status, f"profile {name}: {why}"))
    return prof
