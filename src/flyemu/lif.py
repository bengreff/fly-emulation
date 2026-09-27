"""Neural dynamics: model family M2, per-type leaky integrate-and-fire.

For neuron i, with membrane potential V (mV) and synaptic drive I (mV):

    tau_m,i dV_i/dt = -(V_i - V_rest,i) + I_i + S_i - A_i
    tau_s,i dI_i/dt = -I_i + sum over arriving input of
                         sign_j * eff * n_ij * release_j * input_i * mod_i(t)
    spike when V_i >= V_th,i, then V_i <- V_reset,i, held for t_ref,i

Every symbol with a subscript is a per-neuron array expanded from its cell
type: the shared default (registry, labelled) or a type-specific row in
data/params/cell_types.csv (labelled). S is a tonic drive (spontaneous
activity), A spike-frequency adaptation. Mechanisms, each simulated with its
own values even where the values are guessed:

  - per-presynaptic-type conduction delay (ring buffer of the maximum delay)
  - per-type release strength and per-type input gain
  - short-term depression (Tsodyks-Markram resource per presynaptic neuron)
  - graded (non-spiking) transmission: graded cells transmit continuously at
    a rate-equivalent r = r_max * clip((V - V_rest)/(V_th - V_rest), 0, 1)
  - identified electrical synapses (spike-triggered kicks; electrical.py)
  - neuromodulation: volume-transmitted pools of dopamine, octopamine and
    serotonin, raised by spikes of cells releasing them, decaying with tau;
    each target type's input gain is scaled by (1 + sum_k s_ik m_k), with
    sensitivity s_ik per type
  - optional conductance-based synapses

Still omitted (ledger domains marked absent): dendritic compartments,
explicit ion channels (represented only by these effective parameters),
glia, long-term plasticity.

Propagation is event-driven for spiking cells; graded cells use a sparse
matrix-vector product each step.
"""
from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np
import pandas as pd
import scipy.sparse as sp

from . import params as ptable
from .connectome import Connectome
from .registry import Registry, Status

MODULATORS = ("dopamine", "octopamine", "serotonin")


@dataclass
class LIFParams:
    """Per-neuron physiology, expanded from per-cell-type rows.

    The first eight fields keep their original positional order; scalars are
    broadcast to per-neuron arrays by Network.
    """

    tau_m: np.ndarray       # ms
    v_rest: np.ndarray      # mV
    v_th: np.ndarray        # mV
    v_reset: np.ndarray     # mV
    t_ref: np.ndarray       # ms
    tau_s: float | np.ndarray        # ms, synaptic decay (postsynaptic)
    delay_steps: int | np.ndarray    # conduction delay in timesteps (presynaptic)
    noise_mv: float         # mV per sqrt(ms), background drive
    reset_syn: bool = False  # zero the synaptic current on a spike (Shiu 2024)
    adapt_mv: float | np.ndarray = 0.0   # adaptation increment per spike, mV
    tau_adapt: float | np.ndarray = 200.0  # adaptation decay, ms
    std_u: float | np.ndarray = 0.0        # short-term depression per spike
    std_tau_rec: float | np.ndarray = 500.0  # ms
    cond: bool = False       # conductance-based synapses
    e_exc: float = 0.0       # mV
    e_inh: float = -70.0     # mV
    graded: np.ndarray | None = None       # bool per neuron
    graded_rmax_hz: float = 100.0          # rate-equivalent at threshold
    spont_mv: float | np.ndarray = 0.0     # tonic drive
    release_gain: float | np.ndarray = 1.0  # presynaptic
    input_gain: float | np.ndarray = 1.0    # postsynaptic
    mod_release: np.ndarray | None = None   # (n,) index into MODULATORS or -1
    mod_sensitivity: np.ndarray | None = None  # (n, 3)
    mod_tau_ms: float = 1000.0
    mod_increment: float = 0.01
    # session 6: absent mechanisms, simulated with neutral defaults
    glu_sign_post: float | np.ndarray = 0.0    # per postsynaptic cell; 0 = transmitter default
    gabab_fraction: float | np.ndarray = 0.0   # per postsynaptic cell
    gabab_tau_ms: float = 150.0
    presyn_inh_gain: float = 0.0               # per mV of inhibitory input onto a sensory terminal
    kc_mbon_eta: float = 0.0                   # DAN-gated KC->MBON depression rate
    dan_tau_ms: float = 500.0
    ring_class_norm: bool = False             # session 8: per-class input normalisation in the CX ring


def _morph_delays(reg: Registry, conn: Connectome, delay_ms: np.ndarray) -> np.ndarray:
    from pathlib import Path
    import pandas as pd
    path = Path(__file__).resolve().parents[2] / "data" / "params" / "conduction_delays.csv"
    if not path.exists():
        return delay_ms
    t = pd.read_csv(path, comment="#").set_index("type")
    types = conn.neurons.type.to_numpy()
    d = pd.Series(types).map(t.delay_ms).to_numpy(float)
    # untyped cells: per-cell inferred delay (scripts/infer_delays.py, session 8)
    upath = path.with_name("conduction_delays_untyped.csv")
    n_untyped = 0
    if upath.exists() and reg.require(
            "cell_type:untyped", "inferred_conduction_delay", units="boolean",
            model_use="per-cell delay for untyped cells from predicted path length",
            subsystem="neuron_biophysics", instances=conn.n, minimal=1.0, conventional=1.0,
            minimal_note="on (session 8): 0.5 ms + L/v with L predicted from volume, synapse "
                         "counts and superclass; 0 restores the borrowed shared default",
            uncertainty="10-fold CV delay error median 0.14 ms, p90 0.38 ms on typed cells; "
                        "untyped cells are often fragments (distribution shift)"):
        u = pd.read_csv(upath, comment="#").set_index("bodyId").delay_ms
        du = conn.neurons.bodyId.map(u).to_numpy(float)
        take = ~np.isfinite(d) & np.isfinite(du)
        d = np.where(take, du, d)
        n_untyped = int(take.sum())
    has = np.isfinite(d)
    out = np.where(has, d, delay_ms).astype(np.float32)
    gf = types == "DNp01"
    reg.provide("cell_type:with_skeleton", "conduction_delay", "data/params/conduction_delays.csv",
                units="ms", model_use="spike arrival time per presynaptic type",
                status=Status.DERIVED, subsystem="neuron_biophysics", instances=int(has.sum()),
                method="0.5 ms + L/v; L = median soma->presynapse geodesic path on one "
                       "neuPrint skeleton per type; v = 0.5 m/s (inferred), GF 2.07 m/s (measured)",
                evidence="male-cns v1.0 skeletons; Kadas et al. 2019 eNeuro (GF velocity); "
                         "sqrt(d) scaling to central axons 0.3-1 um (inferred)",
                uncertainty="v uncertain ~0.2-1 m/s per type (calibre not resolved by skeleton "
                            "radii); t_syn unmeasured centrally; one skeleton per type; sensory "
                            "peripheral segment outside the volume omitted")
    reg.provide("sensory:peripheral_axon", "conduction_delay", None, units="ms",
                model_use="omitted: sensor-to-CNS conduction outside the imaged volume",
                status=Status.UNRESOLVED, subsystem="neuron_biophysics",
                instances=int(conn.neurons.superclass.fillna("").str.contains("sensory").sum()),
                evidence="peripheral nerve lengths not in the connectome")
    return out


def default_params(reg: Registry, conn: Connectome, *, timestep_ms: float) -> LIFParams:
    """Shared defaults (registry-labelled) overwritten by per-type table rows."""
    n = conn.n
    types = conn.neurons.type.fillna("untyped")
    n_types = int(types.nunique())
    table = ptable.load()

    def one(prop: str, units: str, use: str, minimal: float, note: str) -> float:
        return reg.require(
            "cell_type:all", prop, units=units, model_use=use,
            subsystem="neuron_biophysics", instances=n, minimal=minimal,
            conventional=minimal, minimal_note=note,
            uncertainty=f"one default shared across all {n_types:,} cell types "
                        "except rows in data/params/cell_types.csv",
        )

    def per(prop: str, units: str, use: str, minimal: float, note: str) -> np.ndarray:
        return ptable.per_neuron(reg, conn, prop, one(prop, units, use, minimal, note),
                                 units=units, table=table)

    tau_m = per("tau_m", "ms", "LIF membrane equation", 20.0,
                "declared default membrane time constant for every neuron")
    v_rest = per("v_rest", "mV", "LIF membrane equation", -60.0,
                 "declared default resting potential")
    v_th = per("v_th", "mV", "LIF spike condition", -45.0,
               "declared default spike threshold, 15 mV above rest")
    v_reset = per("v_reset", "mV", "LIF reset", -60.0, "declared default reset to rest")
    t_ref = per("t_ref", "ms", "LIF refractory period", 2.0,
                "declared default absolute refractory period")
    tau_s = per("tau_s", "ms", "synaptic current decay", 5.0,
                "declared default synaptic decay, a lumped stand-in for "
                "receptor kinetics that are per receptor subtype")
    delay_ms = per("conduction_delay", "ms", "spike arrival time", 1.0,
                   "declared default conduction delay for every connection; "
                   "real delays depend on path length and calibre")
    if one("morphological_delays", "boolean", "per-type delay from skeleton path length",
           1.0, "modelling choice (session 6): delay = 0.5 ms + L/v per presynaptic type, "
                "data/params/conduction_delays.csv; 0 keeps the shared default"):
        delay_ms = _morph_delays(reg, conn, delay_ms)
    noise = one("background_noise", "mV/sqrt(ms)", "stochastic membrane drive",
                1.5, "declared default background noise amplitude, standing in "
                     "for all unmodelled input to the CNS")
    reset_syn = one("syn_reset_on_spike", "boolean", "LIF reset",
                    0.0, "declared default: a spike resets the membrane only, "
                         "leaving synaptic current to decay")
    adapt = per("adaptation_increment", "mV", "spike-frequency adaptation",
                0.0, "declared default: no adaptation (guessed zero; F-SFA-1)")
    tau_adapt = per("adaptation_tau", "ms", "spike-frequency adaptation",
                    200.0, "declared default adaptation decay")
    std_u = per("std_release_fraction", "dimensionless", "short-term depression",
                0.0, "declared default: no short-term depression (guessed zero; F-STD-1)")
    std_tau = per("std_tau_rec", "ms", "short-term depression",
                  500.0, "declared default recovery")
    # ORN output depression (session 7): Nagel, Hong & Wilson 2015 Nat Neurosci
    # 18:56, single-component fit to 10 Hz antennal-nerve trains, DM6/VM2 PNs
    # (n=19): amplitude x f=0.78 per spike, recovery tau 893 ms. Applied to all
    # ORN output synapses (ORN->LN unmeasured; the model's resource is per cell).
    if reg.require("afferent:ORN", "measured_depression", units="boolean",
                   model_use="ORN presynaptic short-term depression, U=0.22, tau_rec=893 ms",
                   subsystem="synaptic_efficacy", instances=n, minimal=0.0, conventional=0.0,
                   minimal_note="off: ORN synapses do not depress",
                   uncertainty="fitted by Nagel 2015 on ORN->PN (inferred for other targets)"):
        orn = conn.neurons.type.fillna("").str.startswith("ORN_").to_numpy()
        std_u = std_u.copy(); std_tau = std_tau.copy()
        std_u[orn], std_tau[orn] = 0.22, 893.0
        for prop, val, u in (("std_release_fraction", 0.22, "dimensionless"),
                             ("std_tau_rec", 893.0, "ms")):
            reg.provide("cell_type:^ORN_", prop, val, units=u,
                        model_use="ORN output depression (afferent:ORN|measured_depression)",
                        status=Status.INFERRED,
                        evidence="Nagel, Hong & Wilson 2015 Nat Neurosci 18:56, Fig 1c "
                                 "(f=0.78, tau=893 ms), fitted to ORN->PN EPSC trains",
                        subsystem="neuron_biophysics", instances=int(orn.sum()),
                        uncertainty="fitted in DM6/VM2 only; KW2008 report ~40% depression at 7 Hz",
                        method="published fit")
    if reg.require("afferent:leg_proprioceptors", "transferred_depression", units="boolean",
                   model_use="leg proprioceptor output depression, U=0.22, tau_rec=893 ms",
                   subsystem="synaptic_efficacy", instances=n, minimal=0.0, conventional=0.0,
                   minimal_note="off: leg afferent synapses do not depress",
                   uncertainty="ORN->PN values (Nagel 2015) transferred; no leg-afferent data"):
        from .connectome import leg_proprioceptor_types
        leg = conn.neurons.type.fillna("").isin(leg_proprioceptor_types()).to_numpy()
        std_u = std_u.copy(); std_tau = std_tau.copy()
        std_u[leg], std_tau[leg] = 0.22, 893.0
    graded = per("graded", "boolean", "graded (non-spiking) transmission",
                 0.0, "declared default: spiking; graded types listed in cell_types.csv")
    rmax = one("graded_rmax", "Hz", "graded rate-equivalent at threshold", 100.0,
               "guessed: maps graded depolarisation to spike-equivalent transmission")
    spont = per("spontaneous_drive", "mV", "tonic drive (spontaneous activity)",
                0.0, "declared default: no tonic drive")
    rel = per("release_gain", "dimensionless", "presynaptic release strength",
              1.0, "declared default: every type releases the shared efficacy")
    inp = per("input_gain", "dimensionless", "postsynaptic input sensitivity",
              1.0, "declared default: every type receives the shared efficacy")
    cond = one("conductance_based", "boolean", "synapse model",
               0.0, "declared default: current-based synapses")
    e_exc = one("e_exc", "mV", "excitatory reversal (conductance mode)",
                0.0, "declared default cation reversal")
    e_inh = one("e_inh", "mV", "inhibitory reversal (conductance mode)",
                -70.0, "declared default chloride reversal")

    # --- session 6: absent mechanisms now simulated, defaults neutral ---------
    glu_sign = per("glutamate_receptor_sign", "sign", "sign of glutamatergic input onto this type",
                   0.0, "neutral default 0: use the transmitter-level glutamate sign "
                        "(profile); +1 = excitatory (iGluR), -1 = inhibitory (GluCl) per "
                        "postsynaptic type via cell_types.csv rows")
    gabab = per("gabab_fraction", "dimensionless", "share of GABAergic input that is slow (GABA-B)",
                0.0, "neutral default 0: all GABA fast (GABA-A-like, tau_s); GABA-B slow "
                     "inhibition exists in AL PNs (Wilson & Laurent 2005) but per-type shares "
                     "are unmeasured")
    gabab_tau = one("gabab_tau", "ms", "slow GABA-B inhibitory current decay", 150.0,
                    "guessed: GABA-B IPSPs in fly PNs last hundreds of ms (Wilson & Laurent "
                    "2005, J Neurosci 25:9069); one value for all")
    pi_gain = one("presynaptic_inhibition_gain", "per mV",
                  "divisive output gain on sensory terminals: release x 1/(1 + k I_inh)", 0.0,
                  "neutral default 0 (off): restores what m1 removed (GABAergic "
                  "presynaptic inhibition of sensory terminals, e.g. sugar GRNs, Chu et al. "
                  "2014) as a gain rather than a spike-generating input; k unmeasured")
    kc_eta = one("kc_mbon_ltd_rate", "per unit DAN trace per KC spike",
                 "DAN-gated KC->MBON synaptic depression", 0.0,
                 "off by default: KC->MBON depression when KC activity coincides with "
                 "dopamine in the MBON's compartment (Hige et al. 2015 Neuron 88:985); "
                 "mechanism in place, rate guessed when enabled; no potentiation or "
                 "recovery modelled")
    dan_tau = one("dan_trace_tau", "ms", "dopamine trace decay per DAN", 500.0,
                  "guessed: seconds-scale coincidence window (Handler et al. 2019)")
    ring_norm = reg.require(
        "cell_type:cx_ring", "class_input_normalisation", units="boolean",
        model_use="each EPG/PEN/PEG/Delta7 receives its type-mean summed weight from each "
                  "presynaptic ring class (topology kept, count heterogeneity removed)",
        subsystem="synaptic_efficacy", instances=conn.n, minimal=0.0, conventional=0.0,
        minimal_note="off: raw synapse counts",
        uncertainty="homeostatic equalisation is an inferred mechanism (session 8); "
                    "the real ring's per-cell drive is unmeasured")

    # --- neuromodulation -----------------------------------------------------
    nt = conn.neurons.predictedNt.fillna("").str.lower().to_numpy()
    mod_release = np.full(n, -1, dtype=np.int8)
    for k, name in enumerate(MODULATORS):
        mod_release[nt == name] = k
    sens = np.stack([per(f"mod_sensitivity_{m}", "per unit level",
                         f"input gain change per unit {m} level", 0.0,
                         f"guessed zero: receptor expression and effect of {m} per "
                         "type unknown; mechanism simulated, effect inert until filled")
                     for m in MODULATORS], axis=1)
    mod_tau = one("mod_tau", "ms", "modulator pool decay", 1000.0,
                  "guessed: seconds-scale volume transmission")
    mod_inc = one("mod_increment", "level per spike (per 1000 releasing cells)",
                  "modulator pool increment", 1.0,
                  "guessed scale: a pool reaches ~1 when all its releasing cells "
                  "fire ~1 Hz for ~1 s")
    n_mod_cells = int((mod_release >= 0).sum())
    reg.provide("neuromodulation:pools", "releasing_cells",
                {m: int((mod_release == k).sum()) for k, m in enumerate(MODULATORS)},
                units="neurons", model_use="cells whose spikes raise each pool",
                status=Status.DERIVED, subsystem="neuromodulation", instances=n_mod_cells,
                evidence="predicted transmitter (male-cns EM classifier)",
                method="predictedNt in {dopamine, octopamine, serotonin}")

    reg.require(
        "state:all_neurons", "initial_condition",
        units="mV",
        model_use="membrane potential and synaptic state at t=0",
        subsystem="physiological_initialisation", instances=n,
        minimal=-52.0,
        minimal_note="every neuron starts exactly at rest with zero synaptic "
                     "current, zero pending spikes and no refractory state",
        uncertainty="a real fly's neurons are distributed over their state "
                    "space according to recent history; transients from this "
                    "initial condition are an artefact of it",
    )
    reg.provide(
        "cell_type:all", "type_grouping_policy",
        f"{n_types} distinct `type` labels used as-is; no collapsing",
        units="dimensionless",
        model_use="the grain at which physiology rows are defined",
        status=Status.GUESSED,
        evidence="male-cns `type` label taken as the physiological type; "
                 "some labels are annotation granularity rather than "
                 "established distinct types",
        subsystem="identity", instances=n,
    )

    return LIFParams(
        tau_m=tau_m, v_rest=v_rest, v_th=v_th, v_reset=v_reset, t_ref=t_ref,
        tau_s=tau_s,
        delay_steps=np.maximum(1, np.round(delay_ms / timestep_ms)).astype(np.int64),
        noise_mv=noise, reset_syn=bool(reset_syn), adapt_mv=adapt,
        tau_adapt=tau_adapt, std_u=std_u, std_tau_rec=std_tau, cond=bool(cond),
        e_exc=float(e_exc), e_inh=float(e_inh), graded=graded.astype(bool),
        graded_rmax_hz=float(rmax), spont_mv=spont, release_gain=rel,
        input_gain=inp, mod_release=mod_release, mod_sensitivity=sens,
        mod_tau_ms=float(mod_tau),
        mod_increment=float(mod_inc) / max(1.0, n_mod_cells / 1000.0),
        glu_sign_post=glu_sign, gabab_fraction=gabab, gabab_tau_ms=float(gabab_tau),
        presyn_inh_gain=float(pi_gain), kc_mbon_eta=float(kc_eta), dan_tau_ms=float(dan_tau),
        ring_class_norm=bool(ring_norm),
    )


def _arr(x, n, dtype=np.float32):
    a = np.asarray(x, dtype=dtype)
    return np.full(n, a, dtype=dtype) if a.ndim == 0 else a.astype(dtype)


@dataclass
class Network:
    """State and stepping for the whole CNS."""

    conn: Connectome
    params: LIFParams
    timestep_ms: float
    rng: np.random.Generator = field(default_factory=lambda: np.random.default_rng(0))

    def __post_init__(self) -> None:
        n = self.conn.n
        p = self.params
        dt = self.timestep_ms
        # per-neuron arrays (scalars broadcast)
        self.tau_m = _arr(p.tau_m, n)
        self.v_rest = _arr(p.v_rest, n)
        self.v_th = _arr(p.v_th, n)
        self.v_reset = _arr(p.v_reset, n)
        self.t_ref = _arr(p.t_ref, n)
        self.adapt_mv = _arr(p.adapt_mv, n)
        self.std_u = _arr(p.std_u, n)
        self.spont = _arr(p.spont_mv, n)
        self.input_gain = _arr(p.input_gain, n)
        self.graded = (np.zeros(n, bool) if p.graded is None else np.asarray(p.graded, bool))
        self.delay_steps = _arr(p.delay_steps, n, np.int64)
        self.D = int(self.delay_steps.max())

        # Physiological initialisation: every neuron exactly at rest.
        self.v = self.v_rest.copy()
        self.i_syn = np.zeros(n, dtype=np.float32)
        self.ref_until = np.zeros(n, dtype=np.float32)
        self.t_ms = 0.0
        # Per-edge signed weight: sign x efficacy x count x release_pre x input_post
        counts = np.diff(self.conn.indptr).astype(np.int64)
        pre = np.repeat(np.arange(n), counts)
        rel = _arr(p.release_gain, n)
        self.w = (self.conn.sign[pre] * self.conn.efficacy_mv * self.conn.weight_syn
                  * rel[pre] * self.input_gain[self.conn.indices]).astype(np.float32)
        self._session6_mechanisms(pre, rel)
        if p.ring_class_norm:
            self._ring_class_norm(pre)
        self._edge_scales(pre)
        self.delay = np.zeros((self.D, n), dtype=np.float32)
        if p.cond:
            vr = self.v_rest[self.conn.indices]
            pos = self.w > 0
            self.w = np.where(pos, self.w / (p.e_exc - vr),
                              self.w / (vr - p.e_inh)).astype(np.float32)
            self.delay_i = np.zeros((self.D, n), dtype=np.float32)
            self.g_i = np.zeros(n, dtype=np.float32)
        self.delay_head = 0
        self.decay_v = np.exp(-dt / self.tau_m).astype(np.float32)
        self.decay_s = np.exp(-dt / _arr(p.tau_s, n)).astype(np.float32)
        self.decay_a = np.exp(-dt / _arr(p.tau_adapt, n)).astype(np.float32)
        self.rec_step = (1.0 - np.exp(-dt / _arr(p.std_tau_rec, n))).astype(np.float32)
        self.spike_count = 0
        self.adapt = np.zeros(n, dtype=np.float32)
        self.kick_held = np.zeros(n, dtype=np.float32)
        self.elec = None   # (pre, post, kick_mv): identified electrical synapses
        self.x_res = np.ones(n, dtype=np.float32)
        self._any_adapt = bool(self.adapt_mv.any())
        self._any_std = bool(self.std_u.any())
        self._any_spont = bool(self.spont.any())

        # graded cells: never spike; transmit a rate-equivalent every step
        self.g_idx = np.flatnonzero(self.graded)
        self.W_graded = None
        if self.g_idx.size:
            rows = [np.arange(self.conn.indptr[i], self.conn.indptr[i + 1]) for i in self.g_idx]
            sel = np.concatenate(rows) if rows else np.zeros(0, np.int64)
            gpre = np.repeat(np.arange(self.g_idx.size), [len(r) for r in rows])
            self.W_graded = sp.csr_matrix(
                (self.w[sel], (gpre, self.conn.indices[sel])), shape=(self.g_idx.size, n)).T.tocsr()
            self.w[sel] = 0.0   # graded cells do not also spike-transmit
            self.graded_scale = p.graded_rmax_hz * dt / 1000.0   # spike-equivalents per step

        # neuromodulator pools
        self.mod_release = (np.full(n, -1, np.int8) if p.mod_release is None
                            else np.asarray(p.mod_release, np.int8))
        self.mod_sens = (np.zeros((n, len(MODULATORS)), np.float32) if p.mod_sensitivity is None
                         else np.asarray(p.mod_sensitivity, np.float32))
        self.mod_level = np.zeros(len(MODULATORS), np.float32)
        self.mod_decay = float(np.exp(-dt / p.mod_tau_ms))
        self._mod_active = bool(self.mod_sens.any())

    # --- one timestep --------------------------------------------------------

    def silence(self, idx: np.ndarray) -> None:
        """Remove all output of these neurons, as Shiu 2024 silences cells."""
        for i in np.asarray(idx):
            self.w[self.conn.indptr[i]:self.conn.indptr[i + 1]] = 0.0
        if self.W_graded is not None:
            keep = ~np.isin(self.g_idx, idx)
            self.W_graded = (self.W_graded @ sp.diags(keep.astype(np.float32))).tocsr()

    def step(
        self,
        external_mv: np.ndarray | None = None,
        kick: tuple[np.ndarray, float] | None = None,
    ) -> np.ndarray:
        """Advance by one timestep. Returns the indices of neurons that spiked.

        `kick` is (indices, mV): an instantaneous membrane increment, which is
        how Shiu 2024 delivers Poisson input to stimulated neurons.
        """
        p = self.params
        n = self.conn.n

        arriving = self.delay[self.delay_head]
        if self._mod_active:
            arriving = arriving * (1.0 + self.mod_sens @ self.mod_level)
        self.i_syn = self.i_syn * self.decay_s + arriving
        self.delay[self.delay_head].fill(0.0)
        if p.cond:
            arr_i = self.delay_i[self.delay_head]
            self.g_i = self.g_i * self.decay_s + arr_i
            arr_i.fill(0.0)

        drive = self.i_syn
        if self.w_slow is not None:
            h = self.delay_head % self.delay_slow.shape[0]
            self.i_slow = self.i_slow * self.decay_slow + self.delay_slow[h]
            self.delay_slow[h].fill(0.0)
            drive = drive + self.i_slow
        if self.w_pi is not None:
            self.p_inh *= self.decay_s
        if self.kc_edge is not None:
            self.dan_trace *= self.dan_decay
        if external_mv is not None:
            drive = drive + external_mv
        if self._any_spont:
            drive = drive + self.spont
        if self._any_adapt:
            self.adapt *= self.decay_a
            drive = drive - self.adapt

        if p.cond:
            g_e = self.i_syn
            G = 1.0 + g_e + self.g_i
            extra = drive - self.i_syn
            v_inf = (self.v_rest + extra + g_e * p.e_exc + self.g_i * p.e_inh) / G
            self.v = v_inf + (self.v - v_inf) * np.exp(-self.timestep_ms * G / self.tau_m)
        else:
            # Exponential Euler: `drive` is the steady-state depolarisation
            self.v = self.v_rest + (self.v - self.v_rest) * self.decay_v + drive * (
                1.0 - self.decay_v)
        if p.noise_mv:
            self.v += self.rng.normal(0.0, p.noise_mv * np.sqrt(self.timestep_ms), n
                                      ).astype(np.float32)

        free = self.t_ms >= self.ref_until
        self.v = np.where(free, self.v, self.v_reset)
        if kick is not None and len(kick[0]):
            self.kick_held[kick[0]] += kick[1]
        if self.kick_held.any():
            land = free & (self.kick_held > 0)
            self.v[land] += self.kick_held[land]
            self.kick_held[land] = 0.0
        can_spike = free & ~self.graded
        spiked = np.flatnonzero(can_spike & (self.v >= self.v_th))

        # graded transmission: continuous, delayed by one step
        if self.W_graded is not None:
            g = self.g_idx
            r = np.clip((self.v[g] - self.v_rest[g]) / (self.v_th[g] - self.v_rest[g]), 0.0, 1.0)
            if r.any():
                self.delay[(self.delay_head + 1) % self.D] += (
                    self.W_graded @ (r * self.graded_scale)).astype(np.float32)

        if self._any_std:
            self.x_res += (1.0 - self.x_res) * self.rec_step
        if self._mod_active:
            self.mod_level *= self.mod_decay
        if spiked.size:
            self.v[spiked] = self.v_reset[spiked]
            if p.reset_syn:
                self.i_syn[spiked] = 0.0
                if p.cond:
                    self.g_i[spiked] = 0.0
            if self._any_adapt:
                self.adapt[spiked] += self.adapt_mv[spiked]
            if self._mod_active:
                k = self.mod_release[spiked]
                k = k[k >= 0]
                if k.size:
                    self.mod_level += np.bincount(k, minlength=len(MODULATORS)) * p.mod_increment
            if self.elec is not None and len(self.elec[0]):
                hit = np.isin(self.elec[0], spiked)
                if hit.any():
                    np.add.at(self.kick_held, self.elec[1][hit], self.elec[2][hit])
            self.ref_until[spiked] = self.t_ms + self.t_ref[spiked]
            if self.kc_edge is not None:
                self.dan_trace[spiked[self.is_dan[spiked]]] += 1.0
            self._propagate(spiked)
            self.spike_count += spiked.size

        self.delay_head = (self.delay_head + 1) % self.D
        self.t_ms += self.timestep_ms
        return spiked

    def _session6_mechanisms(self, pre: np.ndarray, rel: np.ndarray) -> None:
        """Glutamate sign per target, GABA-B, presynaptic inhibition, KC->MBON LTD.

        Each is inert at its default (weights and dynamics bit-identical)."""
        p, n, dt = self.params, self.conn.n, self.timestep_ms
        post = self.conn.indices
        gs = _arr(p.glu_sign_post, n)
        f = _arr(p.gabab_fraction, n)
        self.w_slow = self.w_pi = self.kc_edge = None
        if not (np.any(gs != 0) or np.any(f > 0) or p.presyn_inh_gain > 0 or p.kc_mbon_eta > 0):
            return
        nt = self.conn.neurons.get("predictedNt", pd.Series([""] * n)).fillna("").str.lower().to_numpy()
        is_glu, is_gaba = nt == "glutamate", nt == "gaba"
        if np.any(gs != 0):
            m = is_glu[pre] & (gs[post] != 0)
            self.w[m] = (np.abs(self.w[m]) * gs[post][m]).astype(np.float32)
        if np.any(f > 0):
            # graded (non-spiking) presynaptic cells transmit through W_graded,
            # built from the fast weights; they keep all-fast GABA (limitation)
            ws = np.where(is_gaba[pre] & ~self.graded[pre], self.w * f[post], 0.0).astype(np.float32)
            self.w = (self.w - ws).astype(np.float32)
            self.w_slow = ws
            self.delay_slow = np.zeros((int(_arr(p.delay_steps, n, np.int64).max()), n), np.float32)
            self.i_slow = np.zeros(n, dtype=np.float32)
            self.decay_slow = np.float32(np.exp(-dt / p.gabab_tau_ms))
        if p.presyn_inh_gain > 0:
            sens = self.conn.neurons.superclass.fillna("").str.contains("sensory").to_numpy()
            onto = sens[post] & (is_gaba | is_glu)[pre]
            self.w_pi = np.where(onto, self.conn.psp_mv * self.conn.weight_syn * rel[pre],
                                 0.0).astype(np.float32)
            self.p_inh = np.zeros(n, dtype=np.float32)
            self.is_sensory = sens
        if p.kc_mbon_eta > 0:
            t = self.conn.neurons.type.fillna("")
            kc = (self.conn.neurons["class"].fillna("") == "Kenyon_Cell").to_numpy()
            mbon = t.str.startswith("MBON").to_numpy()
            dan = t.str.match(r"^(PAM|PPL1)").to_numpy()
            self.kc_edge = kc[pre] & mbon[post]
            de = dan[pre] & mbon[post]         # DAN->MBON contacts: compartment proxy
            self.M_da = sp.csr_matrix((self.conn.weight_syn[de].astype(np.float32),
                                       (post[de], pre[de])), shape=(n, n))
            self.dan_trace = np.zeros(n, dtype=np.float32)
            self.is_dan = dan
            self.dan_decay = np.float32(np.exp(-dt / p.dan_tau_ms))

    def _edge_scales(self, pre: np.ndarray) -> None:
        """Candidate-only edge-class scaling (session 8): $FLYEMU_EDGE_SCALES is a CSV of
        pre_type_regex, post_type_regex, scale, justification. Never used by default; like
        FLYEMU_EXTRA_PARAMS it tests a hypothesis without touching live tables."""
        import os
        path = os.environ.get("FLYEMU_EDGE_SCALES")
        if not path:
            return
        t = self.conn.neurons.type.fillna("")
        for r in pd.read_csv(path, comment="#").itertuples(index=False):
            a = t.str.match(r.pre_type_regex).to_numpy()
            b = t.str.match(r.post_type_regex).to_numpy()
            m = a[pre] & b[self.conn.indices]
            self.w[m] = (self.w[m] * float(r.scale)).astype(np.float32)
            print(f"edge scale x{r.scale}: {int(m.sum())} edges {r.pre_type_regex} -> {r.post_type_regex}")

    def _ring_class_norm(self, pre: np.ndarray) -> None:
        """Scale ring-internal edges so each post cell gets its type-mean summed weight per pre class."""
        t = self.conn.neurons.type.fillna("").str.replace("EPGt", "EPG", regex=False).to_numpy()
        ring = np.isin(t, ["EPG", "PEN_a(PEN1)", "PEN_b(PEN2)", "PEG", "Delta7"])
        post = self.conn.indices
        m = ring[pre] & ring[post] & (self.w != 0)
        df = pd.DataFrame({"i": np.flatnonzero(m), "pre_t": t[pre[m]], "post": post[m],
                           "post_t": t[post[m]], "w": self.w[m]})
        tot = df.groupby(["post", "pre_t", "post_t"]).w.sum().rename("tot").reset_index()
        tot["target"] = tot.groupby(["pre_t", "post_t"]).tot.transform("mean")
        tot["scale"] = (tot.target / tot.tot).where(tot.tot != 0, 1.0)
        df = df.merge(tot[["post", "pre_t", "scale"]], on=["post", "pre_t"])
        self.w[df.i.to_numpy()] = (df.w * df.scale).to_numpy(np.float32)

    def _propagate(self, spiked: np.ndarray) -> None:
        """Scatter each spike's weights onto its targets, after its own delay."""
        indptr, indices = self.conn.indptr, self.conn.indices
        starts, ends = indptr[spiked], indptr[spiked + 1]
        counts = ends - starts
        total = int(counts.sum())
        if total == 0:
            return
        offsets = np.repeat(starts, counts)
        within = np.arange(total) - np.repeat(np.cumsum(counts) - counts, counts)
        sel = offsets + within
        w = self.w[sel]
        if self.w_pi is not None:
            # divisive presynaptic inhibition of sensory terminals' release
            g = np.where(self.is_sensory[spiked],
                         1.0 / (1.0 + self.params.presyn_inh_gain * self.p_inh[spiked]), 1.0)
            w = w * np.repeat(g.astype(np.float32), counts)
            np.add.at(self.p_inh, indices[sel], self.w_pi[sel])
        if self.kc_edge is not None:
            e = sel[self.kc_edge[sel]]
            if e.size:
                da = self.M_da @ self.dan_trace
                self.w[e] *= np.clip(1.0 - self.params.kc_mbon_eta * da[indices[e]], 0.0, 1.0)
        if self._any_std:
            w = w * np.repeat(self.x_res[spiked], counts)
            self.x_res[spiked] *= (1.0 - self.std_u[spiked])
        # The head slot was consumed and zeroed earlier in this step; a slot
        # (head + d) % D is read d steps from now, so each presynaptic cell's
        # contribution arrives after exactly its own delay.
        slot = np.repeat((self.delay_head + self.delay_steps[spiked]) % self.D, counts)
        tgt = indices[sel]
        if self.params.cond:
            ex = w > 0
            np.add.at(self.delay, (slot[ex], tgt[ex]), w[ex])
            np.add.at(self.delay_i, (slot[~ex], tgt[~ex]), -w[~ex])
        else:
            np.add.at(self.delay, (slot, tgt), w)
        if self.w_slow is not None:
            ws = self.w_slow[sel]
            if self._any_std:
                ws = ws * np.repeat(self.x_res[spiked] / np.maximum(1.0 - self.std_u[spiked], 1e-6), counts)
            np.add.at(self.delay_slow, (slot % self.delay_slow.shape[0], tgt), ws)

    # --- readout -------------------------------------------------------------

    def rates_hz(self, spike_counts: np.ndarray, window_ms: float) -> np.ndarray:
        return spike_counts / (window_ms / 1000.0)
