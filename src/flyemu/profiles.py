"""Named parameter profiles, each value with its own evidence label.

A profile is a set of `entity|property` values. Every entry carries a basis
(inferred or guessed) and a justification of its own; nothing borrowed from
another model is ever recorded as measured. Values enter through
`Registry.overrides`, and the registry records the label given here.

    ENTRY = (value, basis, justification)
"""
from __future__ import annotations

import os

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

M3 = {
    **M2,
    "connectome:all|nt_source_consensus": (1.0, _I, "session 8 (F-NT-1): transmitter identity from "
        "the male-cns curated consensusNt instead of the EM classifier predictedNt; every KC was "
        "'dopamine' and ~3.3k GABA/glutamate cells 'unclear' (excitatory placeholder)"),
    "connection_class:all|efficacy_per_synapse": (0.15675, _I, "fitted in this project: calibration "
        "rule v3 (DECISIONS s8), largest of 1.0/0.95/0.9/0.85 x 0.165 mV with closed-loop return to "
        "rest on seeds 0-2 under consensusNt; sugar->MN9_L 6.3 Hz at 100 Hz (check > 5)"),
}

M4 = {
    **M3,
    "transmitter:dopamine|sign": (0.0, _I, "session 8: monoamines act only through the "
        "neuromodulator pools; all Drosophila DA, 5-HT and OA receptors are GPCRs. Passed the "
        "pre-registered M0 test under m3 (DECISIONS s8)"),
    "transmitter:serotonin|sign": (0.0, _I, "as dopamine (GPCRs only)"),
    "transmitter:octopamine|sign": (0.0, _I, "as dopamine (GPCRs only)"),
}

# m5 (session 10): the construction template adopted as the working model by the
# pre-registered rule (DECISIONS s10, "repair 1 of the template-adoption test"):
# m4 + every walking-template body/state switch + the two class values found by the
# declared class-level search. m4 is frozen as the regression reference.
_T = "template body/state switch adopted s10 (model_data.TEMPLATE_SWITCHES; DECISIONS s10)"
M5 = {
    **M4,
    "joint:leg|passive_stiffness_source": (2.0, _I, _T + ": measured eLife 2025 springs, projected J^T K J"),
    "joint:leg|spring_reference": (1.0, _I, _T + ": rest angles fitted to the eLife weighted protocol"),
    "joint:wing|spring_reference": (1.0, _I, _T + ": folded wings"),
    "muscle:leg|model": (1.0, _I, _T + ": antagonist Hill muscles"),
    "adhesion:leg|detachment": (1.0, _G, _T + ": load/shear adhesion gate (thresholds guessed)"),
    "muscle:leg|coxa_model": (1.0, _I, _T + ": anatomical coxa muscles, 3-axis moment arms"),
    "joint:wing|range_by_function": (1.0, _I, _T + ": wing envelopes by function (F-WING-1)"),
    "sense:antenna|oscillator": (1.0, _G, _T + ": antenna oscillator (f0, Q guessed)"),
    "jump:ttm|model": (1.0, _G, _T + ": TTM jump twitch (guessed)"),
    "state:organs|model": (1.0, _G, _T + ": lumped organs, clock, sleep homeostat (guessed)"),
    "state:crop|pump_gated": (1.0, _G, _T + ": ingestion gated by pump MNs"),
    "class:DN|release_scale": (0.70, _I, "declared class-level search s10 (fit: template seeds 0-2 "
                               "silent + sugar->MN9 > 5 Hz); held out: template seeds 3-8 and m4-body seeds "
                               "0-5 silent, bitter suppression and sugar dose response kept; water->MN9 fails "
                               "as in m4 (F-STAB-4)"),
    "class:MN_other|input_scale": (1.30, _I, "as class:DN|release_scale (paired value)"),
}

# m6 (session 10): m5 + N15 transduction latency at its prior centres (DECISIONS s10,
# "switch N15 latency on"; closed loop silent on seeds 0-11). m5 is kept.
_L = "N15 latency at the prior centre (guessed; leads not read); adopted s10 (DECISIONS)"
M6 = {
    **M5,
    "transducer:photoreceptor|latency_ms": (12.0, _G, _L),
    "transducer:ocellar_photoreceptor|latency_ms": (12.0, _G, _L),
    "transducer:sensory_olfactory|latency_ms": (25.0, _G, _L),
    "transducer:sensory_gustatory|latency_ms": (20.0, _G, _L),
    "transducer:sensory_mechano|latency_ms": (1.0, _G, _L),
    "transducer:sensory_proprioceptive|latency_ms": (1.0, _G, _L),
    "transducer:sensory_other|latency_ms": (5.0, _G, _L),
}

# m7 (session 11, candidate until its pre-registered guardrails pass): m6 + the
# within-type per-cell size rule (percell.py; DECISIONS s11).
_R = ("per-cell rule s11: input gain x (type geometric-mean volume / cell volume)^alpha")
M7 = {
    **M6,
    # the central rule (cell_type:all|within_type_size_exponent 1.0) failed sugar->MN9 on
    # the s10 class values (DECISIONS s11); repair 2 keeps the motor pools only
    "cell_type:motor|within_type_size_exponent": (1.49, _I, _R + "; fitted to Azevedo 2020 Rin vs "
                                                 "EM volume of the flexor classes (inferred)"),
}

# m8 (session 11, adopted 21:47 after G1 and GPU equivalence passed): m7 + rung-1 intrinsic
# conductances. SK/BK/Kv2/h and the Ca pool fitted to Azevedo 2020 slow-MN current steps
# (scripts/fit_spike_channels.py seed 3; DECISIONS 2026-09-30 21:17/21:20); A/M/T/NaP kept
# at the priors used in that fit. Every gbar is the slow-MN value divided by the slow-MN
# expression factor (hemilineage mRNA, beta 0.5), so the recorded class gets the fitted
# value exactly and every other type is scaled from it by its own channel mRNA.
_F = ("fitted to Azevedo 2020 slow-MN current steps (derived at that class); other types "
      "scaled by channel mRNA (inferred)")
_SLOW_F = {"A": 1.067, "M": 0.845, "h": 1.085, "T": 1.21, "NaP": 1.298, "Kv2": 1.258,
           "BK": 1.104, "SK": 1.091, "Ca": 1.246}   # slow flexor MN expression factors
M8 = {
    **M7,
    "cell_type:all|intrinsic_channels": (1.0, _I, "rung 1 on (FIDELITY_LADDER)"),
    "channel:SK|gbar": (round(0.02724 / _SLOW_F["SK"], 5), _I, _F + "; weakly identified (seeds 0.001-2.8)"),
    "channel:BK|gbar": (round(8.692 / _SLOW_F["BK"], 4), _I, _F + "; strong in 3 of 4 seeds"),
    "channel:Kv2|gbar": (round(0.2749 / _SLOW_F["Kv2"], 4), _I, _F),
    "channel:h|gbar": (round(0.05022 / _SLOW_F["h"], 5), _I, _F + "; sag"),
    "channel:Ca|per_spike": (round(1.245 / _SLOW_F["Ca"], 4), _I, _F + "; weakly identified"),
    "channel:Ca|tau_ms": (37.86, _I, _F + "; weakly identified"),
    "channel:A|gbar": (round(3.0 / _SLOW_F["A"], 4), _G, "prior held in the fit, slow-MN normalised"),
    "channel:M|gbar": (round(0.3 / _SLOW_F["M"], 4), _G, "prior held in the fit, slow-MN normalised"),
    "channel:T|gbar": (round(0.3 / _SLOW_F["T"], 4), _G, "prior held in the fit, slow-MN normalised"),
    "channel:NaP|gbar": (round(0.02 / _SLOW_F["NaP"], 5), _G, "prior held in the fit, slow-MN normalised"),
}

# m9 (session 11, adopted 00:27 after all four held-out tests passed): m8 + the class gains
# re-searched on the rung-1 membrane (DECISIONS s11 "joint re-search"; 42 candidates, fit seeds
# 14-16 + sugar->MN9_L; held out seeds 17-19 silent, bitter suppression, dose response, bitter alone).
_RS = "declared class-level re-search s11 on m8 (fit: seeds 14-16 silent + sugar->MN9_L > 5 Hz; DECISIONS)"
M9 = {
    **M8,
    "class:DN|release_scale": (0.85, _I, _RS),
    "class:MN_other|input_scale": (1.6, _I, _RS),
    "class:sensory_gustatory|release_scale": (1.25, _I, _RS),
    "cell_type:all|within_type_size_exponent": (1.0, _I, _RS + "; prior centre, central size rule on"),
}

# m9w (session 12, adopted 17:50 after seeds 12-19 stayed silent; DECISIONS s12 17:35): m9 + the
# wing-muscle role map and nerve-based afferent assignment (F-WING-2, F-SENSE-NERVE-1). Not fitted.
_W = "s12 body fix, not fitted (F-WING-2, F-SENSE-NERVE-1; DECISIONS s12)"
M9W = {
    **M9,
    "motor_map:wing|roles": (1.0, _I, _W + "; wing MN roles from anatomy (data/params/wing_muscle_roles.csv)"),
    "sense:mechano|assign_by_nerve": (1.0, _I, _W + "; leg sensors by census entry nerve (measured), rule inferred"),
}

# m10p (session 11 rung 2 candidate, not adopted until DECISIONS 2026-10-01 00:45 gates pass):
# m9 + conductance synapses + slow-receptor shares from receptor mRNA + inhibitory decay.
_R2 = "rung 2 at prior (DECISIONS 2026-10-01 00:45)"
M10P = {
    **M9,
    "cell_type:all|conductance_based": (1.0, _G, _R2 + "; reversals at the N9 priors"),
    "cell_type:all|receptor_shares_from_rna": (1.0, _I, _R2 + "; shares inferred from mRNA (receptors.py)"),
    "cell_type:all|tau_s_inh": (10.0, _G, _R2 + "; GABA-A/GluCl IPSCs slower than nicotinic EPSCs"),
    "cell_type:all|slow_share_basis": (1.0, _G, _R2 + " repair 1; share s read as share of charge, "
                                       "peak basis tripled cholinergic charge (seed-20 ablation)"),
}

# m10q (s11 fill, DECISIONS 2026-10-01 02:49): m10p + recorded chloride reversal, weights keep
# their effect at threshold (rung 2 repair 2), per-type recorded resting potentials
M10Q = {
    **M10P,
    "cell_type:all|e_inh": (-56.0, _I, "measured in related preparations: GABA reversal -56 +/- 3 mV, larval central "
                            "neurons (Rohrbough & Broadie 2002); PN under GABA -56 +/- 2 (Wilson & Laurent 2005)"),
    "cell_type:all|cond_reference": (1.0, _G, _R2 + " repair 2; efficacies were fitted on spiking outcomes"),
    "cell_type:all|rest_from_recordings": (1.0, _I, "s11 fill F3; Mi1/Tm1/Tm2/Tm4 at -55 mV (Behnia 2014)"),
}

KICK = 0.275 * 250   # Shiu 2024 Poisson input: w_syn x f_poi mV, forces a spike

# The current working model (docs/MODEL.md). Scripts default to it; pass
# --profile none --min-synapses 1 for the session-3 baseline.
WORKING_PROFILE = os.environ.get("FLYEMU_PROFILE", "m9w")   # s10: m5 then m6 (+ latency); s11: m7 (motor size principle) adopted, then m8 (+ rung-1 intrinsic channels), then m9 (+ class gains re-searched on m8); s12: m9w (+ wing roles, nerve-based afferents); FLYEMU_PROFILE=m4 is the regression reference (m2: sessions 5-8)
REGRESSION_PROFILE = "m4"
WORKING_MIN_SYNAPSES = 5

PROFILES: dict[str, dict] = {
    "shiu2024": {"values": SHIU2024, "kick_mv": KICK},
    "m1": {"values": M1, "kick_mv": KICK},
    "m2": {"values": M2, "kick_mv": KICK},
    "m3": {"values": M3, "kick_mv": KICK},
    "m4": {"values": M4, "kick_mv": KICK},
    "m5": {"values": M5, "kick_mv": KICK},
    "m6": {"values": M6, "kick_mv": KICK},
    "m7": {"values": M7, "kick_mv": KICK},
    "m8": {"values": M8, "kick_mv": KICK},
    "m9": {"values": M9, "kick_mv": KICK},
    "m9w": {"values": M9W, "kick_mv": KICK},
    "m10p": {"values": M10P, "kick_mv": KICK},
    "m10q": {"values": M10Q, "kick_mv": KICK},
}


def apply(reg: Registry, name: str) -> dict:
    prof = PROFILES[name]
    for k, (v, status, why) in prof["values"].items():
        reg.overrides.setdefault(k, v)
        reg.override_notes.setdefault(k, (status, f"profile {name}: {why}"))
    return prof
