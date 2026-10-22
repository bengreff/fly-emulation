"""N19 (s19): monoamine pools with per-cell receptor maps and per-pool kinetics.

Switch `neuromodulation:all|receptor_map` (neutral 0: the legacy three-pool path in lif.py, whose
per-type sensitivities are all 0, runs unchanged). When on, for cell i and pool k (DA, OA, 5-HT, TA):

    s_ik = a * sum_r p_ir * sign_r          (a = `neuromodulation:all|receptor_gain`, one shared value)
    g_i  = max(0, 1 + sum_k s_ik * u_k)     (multiplies the cell's arriving synaptic input)
    u_k  = m_k / (m_k + K)                  (occupancy; K = `neuromodulation:all|half_occupancy`)

p_ir is the cell's expression probability for receptor gene r (`receptors.gene_probabilities`: type rows
from Davis 2020 / Ozel 2021, VNC hemilineage rows from Allen 2020, otherwise the population prior).
sign_r is the coupling rule written down before use (DECISIONS 21 Oct 21:56): +1 if every reported arm is
Gs or Gq, -1 if Gi/o, 0 if non-canonical (`docs/research/s18_n19_receptor_coupling.md`).

Each pool is two compartments: a spike of a releasing cell adds 1/N_k to a released compartment c_k, which
passes to the receptor-side level m_k with tau_on and is cleared from m_k with tau_off. m_k is in spikes per
releasing cell (an impulse of one spike per cell peaks near 1); tonic firing at f Hz gives m_k = f tau_off.

Tyramine is a fourth pool held at 0: the EM transmitter classifier has no tyramine class (no releasing
cells) and no transcript table carries a TA receptor (or Octalpha2R), so its sensitivity is 0.

Validity: postsynaptic excitability only (no presynaptic release modulation, where Hige 2015's Dop1R1 acts);
global pools (no spatial gradient); no second-messenger lag beyond the pool kinetics; cells on the population
prior share one s per pool. CPU only: the GPU path refuses this mode until it is ported and matched.
"""
from __future__ import annotations

import numpy as np

POOLS = ("dopamine", "octopamine", "serotonin", "tyramine")

# sign rule (DECISIONS 21 Oct 21:56); genes absent from the transcript tables are not listed
SIGN = {
    "dopamine": {"Dop1R1": 1, "Dop1R2": 1, "Dop2R": -1, "DopEcR": 0},
    "octopamine": {"Oamb": 1, "Octbeta1R": 1, "Octbeta2R": 1, "Octbeta3R": 1},
    "serotonin": {"5-HT2A": 1, "5-HT2B": 1, "5-HT7": 1, "5-HT1A": -1, "5-HT1B": -1},
    "tyramine": {},
}

# pool -> (tau_on ms, tau_off ms, note); values are the registry defaults, owned in parameters.csv
KINETICS = {
    "dopamine": (340.0, 1400.0, "tau_off derived from larval protocerebrum DAT Vmax/Km (Privman & Venton "
                 "2015, secondary read; VNC 2.0 s); tau_on inferred from OA's"),
    "octopamine": (340.0, 5900.0, "measured: Lv et al. 2024 Natl Sci Rev nwae112 Fig. 2J, GRAB-OA1.0, "
                   "single optogenetic pulse, MB gamma3, in vivo"),
    "serotonin": (70.0, 4080.0, "measured: Wan et al. 2021 Nat Neurosci 24:746 Fig. 2h-j, GRAB-5HT1.0 in "
                  "KCs, single electrical stimulus, in vivo"),
    "tyramine": (340.0, 5900.0, "guessed: OA's (no releasing cells, sensitivity 0)"),
}


def net_expression(P) -> np.ndarray:
    """(cells x pools) sum_r p_ir sign_r from a (cells x genes) expression-probability table."""
    net = np.zeros((len(P), len(POOLS)), np.float64)
    for k, pool in enumerate(POOLS):
        for gene, sgn in SIGN[pool].items():
            if sgn:
                net[:, k] += sgn * P[gene].to_numpy()
    return net


def build(reg, conn, timestep_ms: float) -> dict | None:
    """Read the N19 keys (always); the per-cell map when the switch is on, else None."""
    n = conn.n
    on = reg.require("neuromodulation:all", "receptor_map", units="boolean",
                     model_use="N19: per-cell monoamine sensitivities from receptor transcripts, "
                               "four pools with tau_on/tau_off and occupancy (src/flyemu/neuromod.py)",
                     subsystem="neuromodulation", instances=n, minimal=0.0, conventional=0.0,
                     minimal_note="neutral 0: the legacy pools with per-type sensitivities (all 0)")
    a = reg.require("neuromodulation:all", "receptor_gain", units="per unit occupancy per expressed receptor",
                    model_use="s_ik = a sum_r p_ir sign_r, one value shared by every monoamine GPCR",
                    subsystem="neuromodulation", instances=n, minimal=0.0, conventional=0.0,
                    minimal_note="neutral 0; fitted on Strother 2018 Fig. 6F (Mi4 gain under CDM)")
    K = reg.require("neuromodulation:all", "half_occupancy", units="spikes per releasing cell",
                    model_use="u = m/(m+K)", subsystem="neuromodulation", instances=n,
                    minimal=10.0, conventional=10.0,
                    minimal_note="guessed; fixed by GRAB dF/F per pulse against a saturating bath in one prep")
    taus = {}
    for k, (on_ms, off_ms, note) in KINETICS.items():
        taus[k] = (reg.require(f"neuromodulation:{k}", "tau_on", units="ms", model_use="pool rise",
                               subsystem="neuromodulation", instances=n, minimal=on_ms,
                               conventional=on_ms, minimal_note=note),
                   reg.require(f"neuromodulation:{k}", "tau_off", units="ms", model_use="pool clearance",
                               subsystem="neuromodulation", instances=n, minimal=off_ms,
                               conventional=off_ms, minimal_note=note))
    if not on:
        return None
    from . import receptors
    from .registry import Status
    P, src = receptors.gene_probabilities(conn.neurons.type.fillna("untyped").to_numpy(),
                                          conn.neurons.bodyId.to_numpy())
    net = net_expression(P)
    nt = conn.neurons.predictedNt.fillna("").str.lower().to_numpy()
    rel = np.full(n, -1, np.int8)
    for k, pool in enumerate(POOLS):
        rel[nt == pool] = k
    n_rel = np.array([(rel == k).sum() for k in range(len(POOLS))])
    cover = {"type": int((src == 2).sum()), "hemilineage": int((src == 1).sum()),
             "prior": int((src == 0).sum())}
    reg.provide("neuromodulation:all", "receptor_map_coverage", cover, units="neurons",
                model_use="source of each cell's receptor probabilities", status=Status.DERIVED,
                subsystem="neuromodulation", instances=n,
                evidence="Davis 2020 / Ozel 2021 type rows; Allen 2020 VNC hemilineage rows; population prior",
                method="receptors.gene_probabilities")
    return {
        "sens": (float(a) * net).astype(np.float32),
        "net": net.astype(np.float32),
        "release": rel,
        "n_release": n_rel,
        "tau_on_ms": np.array([taus[k][0] for k in POOLS], np.float64),
        "tau_off_ms": np.array([taus[k][1] for k in POOLS], np.float64),
        "K": float(K),
        "source": src,
        "coverage": cover,
    }
