"""Named parameter profiles: borrowed values applied as registry overrides.

A profile is a set of `entity|property` values taken from a published model.
They pass through `Registry.overrides`, so every one is recorded as `assumed`
with its source in the evidence field. A value fitted in another paper to
another specimen is not a measurement of this fly, and must never read back
as one.
"""
from __future__ import annotations

from .registry import Registry

SHIU = ("Shiu et al. 2024, Nature 634:210, default_params in "
        "github.com/philshiu/Drosophila_brain_model; fitted to FlyWire v630/"
        "v783 (female brain), transferred unchanged to male-cns")

PROFILES: dict[str, dict] = {
    "shiu2024": {
        "values": {
            "cell_type:all|tau_m": 20.0,
            "cell_type:all|v_rest": -52.0,
            "cell_type:all|v_th": -45.0,
            "cell_type:all|v_reset": -52.0,
            "cell_type:all|t_ref": 2.2,
            "cell_type:all|tau_s": 5.0,
            "cell_type:all|conduction_delay": 1.8,
            "cell_type:all|background_noise": 0.0,
            "cell_type:all|syn_reset_on_spike": 1.0,
            "connection_class:all|efficacy_per_synapse": 0.275,
            # Shiu: ACh +, GABA -, glutamate -, monoamines and unknown +.
            # Histamine was not a predicted class in FlyWire, so ours (-1,
            # HisCl) stands.
            "transmitter:glutamate|sign": -1.0,
            "transmitter:dopamine|sign": 1.0,
            "transmitter:serotonin|sign": 1.0,
            "transmitter:octopamine|sign": 1.0,
            "transmitter:unclear|sign": 1.0,
        },
        "note": SHIU,
        # Poisson input: each event adds w_syn * f_poi = 0.275 * 250 mV to V,
        # which forces a spike unless refractory.
        "kick_mv": 0.275 * 250,
    },
}

PROFILES["m1"] = {
    "values": {
        **PROFILES["shiu2024"]["values"],
        # fitted here, by return-to-rest on sugar GRNs only (F-GAIN-2)
        "connection_class:all|efficacy_per_synapse": 0.165,
        # structural: no spikes from input onto sensory terminals (F-SENS-1)
        "connection_class:onto_sensory_terminals|included": 0.0,
    },
    "note": SHIU + "; efficacy refitted to 0.165 mV by return-to-rest "
            "(F-GAIN-2); synapses onto sensory terminals dropped (F-SENS-1)",
    "kick_mv": PROFILES["shiu2024"]["kick_mv"],
}


def apply(reg: Registry, name: str) -> dict:
    prof = PROFILES[name]
    for k, v in prof["values"].items():
        reg.overrides.setdefault(k, v)
        reg.override_notes.setdefault(k, f"profile {name}: {prof['note']}")
    return prof
