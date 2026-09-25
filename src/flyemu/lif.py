"""Neural dynamics: model family M v1, leaky integrate-and-fire.

For neuron i, with membrane potential V (mV) and synaptic current I (mV/ms):

    tau_m,i dV_i/dt = -(V_i - V_rest,i) + I_i
    tau_s    dI_i/dt = -I_i + sum over arriving spikes of  sign_j * eff_ij * n_ij
    spike when V_i >= V_th,i, then V_i <- V_reset,i, held for t_ref,i

Spikes arrive after a conduction delay, implemented as a ring buffer.

What M v1 omits, explicitly, so that nothing here is mistaken for the animal:

  - dendrites. Single compartment, no spatial integration.
  - gap junctions. No electrical coupling (and the dataset has none).
  - graded transmission. Fly photoreceptors and many optic-lobe interneurons
    are non-spiking; M v1 makes them spike, which is wrong for the optic lobe.
  - conductance-based synapses. Current-based, so inhibition cannot shunt and
    there are no reversal potentials.
  - short-term plasticity, adaptation, and all neuromodulation as a mechanism.
  - glia.

Propagation is event-driven: cost scales with the number of spikes times the
mean out-degree, not with the 25.8 million edges.
"""
from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np

from .connectome import Connectome
from .registry import Registry, Status


@dataclass
class LIFParams:
    """Per-neuron physiology, expanded from per-cell-type rows."""

    tau_m: np.ndarray       # ms
    v_rest: np.ndarray      # mV
    v_th: np.ndarray        # mV
    v_reset: np.ndarray     # mV
    t_ref: np.ndarray       # ms
    tau_s: float            # ms, synaptic decay
    delay_steps: int        # conduction delay in timesteps
    noise_mv: float         # mV per sqrt(ms), background drive
    reset_syn: bool = False  # zero the synaptic current on a spike (Shiu 2024)
    adapt_mv: float = 0.0    # adaptation increment per spike, mV
    std_u: float = 0.0       # short-term depression: fraction of resource per spike
    cond: bool = False       # conductance-based synapses
    e_exc: float = 0.0       # mV
    e_inh: float = -70.0     # mV
    std_tau_rec: float = 500.0  # ms, recovery of the resource
    tau_adapt: float = 200.0  # adaptation decay, ms


def default_params(reg: Registry, conn: Connectome, *, timestep_ms: float) -> LIFParams:
    """Every field here is a guess. The registry is what says so."""
    n = conn.n
    types = conn.neurons.type.fillna("untyped")
    n_types = int(types.nunique())

    def one(prop: str, units: str, use: str, minimal: float, note: str) -> float:
        return reg.require(
            "cell_type:all", prop, units=units, model_use=use,
            subsystem="neuron_biophysics", instances=n, minimal=minimal,
            conventional=minimal, minimal_note=note,
            uncertainty=f"one value shared across all {n_types:,} cell types; "
                        "a single inference, not a per-type measurement",
        )

    tau_m = one("tau_m", "ms", "LIF membrane equation", 20.0,
                "declared default membrane time constant for every neuron")
    v_rest = one("v_rest", "mV", "LIF membrane equation", -60.0,
                 "declared default resting potential")
    v_th = one("v_th", "mV", "LIF spike condition", -45.0,
               "declared default spike threshold, 15 mV above rest")
    v_reset = one("v_reset", "mV", "LIF reset", -60.0,
                  "declared default reset to rest")
    t_ref = one("t_ref", "ms", "LIF refractory period", 2.0,
                "declared default absolute refractory period")
    tau_s = one("tau_s", "ms", "synaptic current decay", 5.0,
                "declared default synaptic decay, a lumped stand-in for "
                "receptor kinetics that are per receptor subtype")
    delay_ms = one("conduction_delay", "ms", "spike arrival time", 1.0,
                   "declared default conduction delay for every connection; "
                   "real delays depend on path length and calibre")
    noise = one("background_noise", "mV/sqrt(ms)", "stochastic membrane drive",
                1.5, "declared default background noise amplitude, standing in "
                     "for all unmodelled input to the CNS")
    reset_syn = one("syn_reset_on_spike", "boolean", "LIF reset",
                    0.0, "declared default: a spike resets the membrane only, "
                         "leaving synaptic current to decay")

    reg.require(
        "state:all_neurons", "initial_condition",
        units="mV",
        model_use="membrane potential and synaptic state at t=0",
        subsystem="physiological_initialisation", instances=n,
        minimal=v_rest,
        minimal_note="every neuron starts exactly at rest with zero synaptic "
                     "current, zero pending spikes and no refractory state",
        uncertainty="a real fly's neurons are distributed over their state "
                    "space according to recent history; there is no "
                    "measurement of that distribution, and nothing here "
                    "establishes that the at-rest point is reachable or "
                    "typical. Transients from this initial condition are an "
                    "artefact of it",
    )

    reg.provide(
        "cell_type:all", "type_grouping_policy",
        f"{n_types} distinct `type` labels used as-is; no collapsing",
        units="dimensionless",
        model_use="the grain at which physiology rows are defined",
        status=Status.ASSUMED,
        evidence="male-cns `type` label taken as the physiological type; "
                 "some labels are annotation granularity rather than "
                 "established distinct types",
        subsystem="identity", instances=n,
    )

    full = lambda v: np.full(n, v, dtype=np.float32)
    adapt = one("adaptation_increment", "mV", "spike-frequency adaptation",
                0.0, "declared default: no adaptation (M v1 omission)")
    tau_adapt = one("adaptation_tau", "ms", "spike-frequency adaptation",
                    200.0, "declared default adaptation decay; inert while "
                           "the increment is zero")
    std_u = one("std_release_fraction", "dimensionless", "short-term depression",
                0.0, "declared default: no short-term depression")
    std_tau = one("std_tau_rec", "ms", "short-term depression",
                  500.0, "declared default recovery; inert while U is zero")
    cond = one("conductance_based", "boolean", "synapse model",
               0.0, "declared default: current-based synapses (M v1)")
    e_exc = one("e_exc", "mV", "excitatory reversal (conductance mode)",
                0.0, "declared default cation reversal")
    e_inh = one("e_inh", "mV", "inhibitory reversal (conductance mode)",
                -70.0, "declared default chloride reversal")
    return LIFParams(
        tau_m=full(tau_m), v_rest=full(v_rest), v_th=full(v_th),
        v_reset=full(v_reset), t_ref=full(t_ref), tau_s=tau_s,
        delay_steps=max(1, int(round(delay_ms / timestep_ms))), noise_mv=noise,
        reset_syn=bool(reset_syn), adapt_mv=float(adapt),
        tau_adapt=float(tau_adapt), std_u=float(std_u),
        std_tau_rec=float(std_tau), cond=bool(cond), e_exc=float(e_exc),
        e_inh=float(e_inh),
    )


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
        # Physiological initialisation. Every neuron starts exactly at rest
        # with no synaptic history, which is one declared default standing in
        # for 176,422 neurons that each sit somewhere specific in the animal,
        # set by history this model does not have.
        self.v = p.v_rest.copy()
        self.i_syn = np.zeros(n, dtype=np.float32)
        self.ref_until = np.zeros(n, dtype=np.float32)
        self.t_ms = 0.0
        # Per-edge signed weight in mV of postsynaptic drive per spike.
        sign_per_edge = np.repeat(
            self.conn.sign, np.diff(self.conn.indptr).astype(np.int64)
        )
        self.w = (sign_per_edge * self.conn.efficacy_mv
                  * self.conn.weight_syn).astype(np.float32)
        # Delay line: contributions landing on future steps.
        self.delay = np.zeros((p.delay_steps, n), dtype=np.float32)
        if p.cond:
            # Same PSP at rest: excitatory w -> w/(E_e - V_rest) of leak
            # conductance, inhibitory |w| -> |w|/(V_rest - E_i).
            vr = float(p.v_rest[0])
            pos = self.w > 0
            self.w = np.where(pos, self.w / (p.e_exc - vr),
                              self.w / (vr - p.e_inh)).astype(np.float32)
            self.delay_i = np.zeros((p.delay_steps, n), dtype=np.float32)
            self.g_i = np.zeros(n, dtype=np.float32)
        self.delay_head = 0
        self.decay_v = float(np.exp(-self.timestep_ms / p.tau_m[0]))
        self.decay_s = float(np.exp(-self.timestep_ms / p.tau_s))
        self.spike_count = 0
        self.adapt = np.zeros(n, dtype=np.float32)
        self.kick_held = np.zeros(n, dtype=np.float32)
        self.x_res = np.ones(n, dtype=np.float32)      # STD resource per presynaptic neuron
        self.rec_step = float(1.0 - np.exp(-self.timestep_ms / p.std_tau_rec))
        self.decay_a = float(np.exp(-self.timestep_ms / p.tau_adapt))

    # --- one timestep --------------------------------------------------------

    def silence(self, idx: np.ndarray) -> None:
        """Remove all output of these neurons, as Shiu 2024 silences cells."""
        for i in np.asarray(idx):
            self.w[self.conn.indptr[i]:self.conn.indptr[i + 1]] = 0.0

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
        self.i_syn = self.i_syn * self.decay_s + arriving
        arriving.fill(0.0)
        if p.cond:
            arr_i = self.delay_i[self.delay_head]
            self.g_i = self.g_i * self.decay_s + arr_i
            arr_i.fill(0.0)

        drive = self.i_syn
        if external_mv is not None:
            drive = drive + external_mv
        if p.adapt_mv:
            self.adapt *= self.decay_a
            drive = drive - self.adapt

        if p.cond:
            # i_syn holds g_e (>= 0 in this mode, as inhibition goes to g_i);
            # external drive and adaptation stay current-like offsets.
            g_e = self.i_syn
            G = 1.0 + g_e + self.g_i
            extra = drive - self.i_syn
            v_inf = (p.v_rest + extra + g_e * p.e_exc + self.g_i * p.e_inh) / G
            self.v = v_inf + (self.v - v_inf) * np.exp(-self.timestep_ms * G / p.tau_m)
        else:
            # Exponential Euler on the deterministic part: `drive` is the
            # steady-state depolarisation it would hold the neuron at, in mV.
            self.v = p.v_rest + (self.v - p.v_rest) * self.decay_v + drive * (
                1.0 - self.decay_v
            )
        # Noise enters as an increment on the membrane, not as a steady-state
        # offset, so its amplitude is mV per sqrt(ms) and the leak filters it.
        # Stationary std is then noise_mv * sqrt(tau_m / 2).
        if p.noise_mv:
            self.v += self.rng.normal(
                0.0, p.noise_mv * np.sqrt(self.timestep_ms), n
            ).astype(np.float32)

        free = self.t_ms >= self.ref_until
        self.v = np.where(free, self.v, p.v_reset)
        # As Brian2's PoissonInput does, a kick during refractory is not
        # lost: it is held and lands on the first free step.
        if kick is not None and len(kick[0]):
            self.kick_held[kick[0]] += kick[1]
        if self.kick_held.any():
            land = free & (self.kick_held > 0)
            self.v[land] += self.kick_held[land]
            self.kick_held[land] = 0.0
        spiked = np.flatnonzero(free & (self.v >= p.v_th))

        if p.std_u:
            self.x_res += (1.0 - self.x_res) * self.rec_step
        if spiked.size:
            self.v[spiked] = p.v_reset[spiked]
            if p.reset_syn:
                self.i_syn[spiked] = 0.0
                if p.cond:
                    self.g_i[spiked] = 0.0
            if p.adapt_mv:
                self.adapt[spiked] += p.adapt_mv
            self.ref_until[spiked] = self.t_ms + p.t_ref[spiked]
            self._propagate(spiked)
            self.spike_count += spiked.size

        self.delay_head = (self.delay_head + 1) % p.delay_steps
        self.t_ms += self.timestep_ms
        return spiked

    def _propagate(self, spiked: np.ndarray) -> None:
        """Scatter each spike's weights onto its targets, delayed."""
        indptr, indices = self.conn.indptr, self.conn.indices
        starts, ends = indptr[spiked], indptr[spiked + 1]
        counts = ends - starts
        total = int(counts.sum())
        if total == 0:
            return
        # Concatenate the CSR row ranges without a Python loop.
        offsets = np.repeat(starts, counts)
        within = np.arange(total) - np.repeat(
            np.cumsum(counts) - counts, counts
        )
        sel = offsets + within
        # The head slot was consumed and zeroed earlier in this step, and is
        # next read delay_steps steps from now: a delay of exactly
        # delay_steps (was delay_steps - 1 before session 4's review).
        target_slot = self.delay_head
        w = self.w[sel]
        if self.params.std_u:
            w = w * np.repeat(self.x_res[spiked], counts)
            self.x_res[spiked] *= (1.0 - self.params.std_u)
        if self.params.cond:
            ex = w > 0
            np.add.at(self.delay[target_slot], indices[sel][ex], w[ex])
            np.add.at(self.delay_i[target_slot], indices[sel][~ex], -w[~ex])
        else:
            np.add.at(self.delay[target_slot], indices[sel], w)

    # --- readout -------------------------------------------------------------

    def rates_hz(self, spike_counts: np.ndarray, window_ms: float) -> np.ndarray:
        return spike_counts / (window_ms / 1000.0)
