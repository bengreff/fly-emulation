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

import copy
from dataclasses import dataclass, field

import numpy as np
import pandas as pd
import scipy.sparse as sp

from . import channels as ichan
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
    adp_mv: np.ndarray | None = None       # s14 B: after-depolarisation ceiling, mV (None: off)
    tau_adp: float | np.ndarray = 20.0     # s14 B: after-depolarisation decay, ms
    adp_rec_ms: float | np.ndarray = 0.0   # s14 B: recovery of ADP availability after a trigger, ms (0: none)
    std_u: float | np.ndarray = 0.0        # short-term depression per spike
    std_tau_rec: float | np.ndarray = 500.0  # ms
    cond: bool = False       # conductance-based synapses
    e_exc: float = 0.0       # mV
    e_inh: float = -70.0     # mV
    tau_s_inh: float | np.ndarray = 0.0   # s11 rung 2: inhibitory conductance decay (cond); 0 = tau_s
    slow_share_basis: float = 0.0
    cond_reference: float = 0.0     # rung 2 repair 2: 0 = weights keep the PSP at rest, 1 = at threshold
    inh_cond_scale: float = 1.0     # s11 search: inhibitory conductance per unit fitted weight (cond)   # s11 rung 2 repair 1: 0 = share of peak, 1 = share of charge
    graded: np.ndarray | None = None       # bool per neuron
    graded_rmax_hz: float = 100.0          # rate-equivalent at threshold
    graded_r0: np.ndarray | None = None    # release at rest as a fraction of rmax (None: 0, m4)
    graded_range: np.ndarray | None = None  # mV from rest to full release (None: v_th - v_rest)
    graded_k: np.ndarray | None = None      # per-cell release multiplier (None: 1)
    v_leak: np.ndarray | None = None        # mV, leak reversal where it differs from the rest (None: v_rest)
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
    # s10 N21/N22: timing-dependent, bidirectional KC->MBON plasticity and forgetting
    kc_ltd_timing: float = 0.0     # depression per DAN spike x KC eligibility (KC before DA)
    kc_ltp_timing: float = 0.0     # potentiation per KC spike x DA trace (DA before KC)
    kc_elig_tau_ms: float = 1000.0 # KC eligibility trace decay
    kc_w_cap: float = 2.0          # potentiation ceiling, x baseline weight
    kc_recovery_tau_ms: float = 0.0  # N22: relaxation to baseline (0 = none)
    kc_restore: float = 0.0        # s25: DA-only restoration toward baseline per DAN spike
    # s10 N24: ER (ring neuron) -> EPG inhibitory plasticity; N27: lumped glial K+ buffer
    ring_eta: float = 0.0           # depression per ER spike x EPG activity trace
    ring_trace_tau_ms: float = 100.0
    ring_recovery_tau_ms: float = 60000.0
    ring_floor: float = 0.2         # weights never fall below this x baseline
    glia_gain_mv: float = 0.0       # depolarisation per unit class K+ load
    glia_tau_ms: float = 2000.0     # glial clearance
    apl_local: float = 0.0          # N23: 0 point APL (m4) .. 1 fully compartmental
    apl_local_tau_ms: float = 50.0
    dan_tau_ms: float = 500.0
    ring_class_norm: bool = False             # session 8: per-class input normalisation in the CX ring
    noise_class_mv: np.ndarray | None = None  # s10 N3: per-neuron extra noise (class grain); None = none
    tonic_class_mv: np.ndarray | None = None  # s10 N3: the class part of spont_mv (already included)
    # s10 N7/N8: extra slow kinetic components per postsynaptic cell (fraction of the
    # fast weight moved to a slow current with its own decay); 0 = neutral
    mglur_fraction: float | np.ndarray = 0.0    # of glutamatergic input (metabotropic)
    mglur_tau_ms: float = 300.0
    machr_fraction: float | np.ndarray = 0.0    # of cholinergic input (muscarinic)
    machr_tau_ms: float = 300.0
    nmda_fraction: float | np.ndarray = 0.0     # of excitatory glutamatergic input, Mg-blocked
    nmda_tau_ms: float = 80.0
    nmda_mg_mM: float = 1.0
    # s11 ladder rung 1: intrinsic conductances per type (channels.Intrinsic); None = leak-only
    intrinsic: object | None = None
    # s12 ladder rung 8 (N29): per-connection short-term plasticity on the edges a row of
    # data/params/stp_connections.csv matches: {"idx", "U", "tau_rec", "tau_f"} (CSR edge
    # order); None = per-presynaptic-cell depression only
    stp_edge: dict | None = None
    # s13 (fly2, N12): identified gap junctions from electrical.build_gap: pairs (a, b), DC coupling c with
    # rectification r, spike steps k_ab / k_ba and arrival delays d_a / d_b in steps; None = none
    gap: dict | None = None
    # s13 (fly2, N29): fast receptor decay per connection class from data/params/receptor_kinetics.csv:
    # {"idx", "tau"} (CSR edge order); None = every edge decays with its post cell's tau_s
    kin_edge: dict | None = None
    # s14 (fly2): measured unitary PSP per identified connection from data/params/unitary_psp.csv:
    # {"idx", "psp_mv"} (CSR edge order, signed peak mV); None = every edge from the shared scale
    psp_edge: dict | None = None
    # s14 (fly2): flyvis type-pair strengths (data/params/flyvis_pair_strength.csv), fitted to a task:
    # {"idx", "alpha"} (CSR edge order, voltage gain per synapse); None = every edge from the shared scale
    fv_edge: dict | None = None
    # s20 (fly2, N30): an axon compartment where spikes start, for the cells of data/params/two_compartment.csv:
    # {"cells", "edge_idx" (CSR edges that land on the axon), "q", "rho" (per listed cell, from the class)};
    # None = every cell is a point neuron
    two_comp: dict | None = None


STP_TABLE = "stp_connections.csv"
KIN_TABLE = "receptor_kinetics.csv"
PSP_TABLE = "unitary_psp.csv"
FV_PAIR_TABLE = "flyvis_pair_strength.csv"
TWO_COMP_TABLE = "two_compartment.csv"
TWO_COMP_CLASSES = "two_compartment_classes.csv"


def _stp_cells(neurons: pd.DataFrame, sel: str) -> np.ndarray:
    """Cells a stp_connections.csv / receptor_kinetics.csv selector names: type:<regex>,
    instance:<regex> (s14: CT1 compartments, connectome.ct1_compartments), class:<name>,
    nt:<transmitter> (predictedNt as built, lower case) or *."""
    if sel == "*":
        return np.ones(len(neurons), bool)
    kind, _, pat = sel.partition(":")
    if kind == "type":
        return neurons.type.fillna("").str.contains(pat, regex=True).to_numpy()
    if kind == "instance":
        if "instance" not in neurons:
            return np.zeros(len(neurons), bool)
        return neurons.instance.fillna("").str.contains(pat, regex=True).to_numpy()
    if kind == "class" and "class" in neurons:
        return neurons["class"].fillna("").eq(pat).to_numpy()
    if kind == "nt":
        return neurons.predictedNt.fillna("").str.lower().eq(pat).to_numpy()
    raise ValueError(f"{STP_TABLE}: cannot select {sel!r}")


def _receptor_kinetics(reg: Registry, conn: Connectome) -> dict | None:
    """N29 (s13, fly2): fast ionotropic decay per connection class (pre and post selectors), or None.
    The decay belongs to the postsynaptic receptor, so a row is a (transmitter or presynaptic class,
    postsynaptic class) pair; later rows override earlier ones."""
    from pathlib import Path
    if not reg.require(
            "synapse:all", "receptor_kinetics_per_connection", units="boolean",
            model_use="N29: fast receptor decay per connection class (data/params/receptor_kinetics.csv), "
                      "charge per spike kept",
            subsystem="synaptic_efficacy", instances=conn.n_edges, minimal=0.0, conventional=0.0,
            minimal_note="neutral 0: every edge decays with its postsynaptic cell's tau_s"):
        return None
    path = Path(__file__).resolve().parents[2] / "data" / "params" / KIN_TABLE
    tab = pd.read_csv(path, comment="#")
    pre = np.repeat(np.arange(conn.n), np.diff(conn.indptr))
    row = np.full(conn.n_edges, -1, np.int32)
    for i, r in enumerate(tab.itertuples()):
        m = _stp_cells(conn.neurons, r.pre)[pre] & _stp_cells(conn.neurons, r.post)[conn.indices]
        row[m] = i
        reg.provide(f"connection:{r.pre}->{r.post}", "receptor_tau_decay", float(r.tau_decay_ms), units="ms",
                    model_use="fast receptor decay per connection class (N29)", status=Status(r.basis),
                    evidence=r.source, subsystem="synaptic_efficacy", instances=int(m.sum()),
                    uncertainty=r.note, method="published current decay (single exponential)")
    idx = np.flatnonzero(row >= 0)
    return {"idx": idx, "tau": tab.tau_decay_ms.to_numpy(np.float64)[row[idx]]}


def _unitary_psp(reg: Registry, conn: Connectome) -> dict | None:
    """s14 (fly2): the unitary PSP of an identified connection from a recording, or None. A row
    (pre selector, post selector, signed peak mV) replaces sign x efficacy x count x release x input
    gain on its edges by the weight whose passive PSP peak, for one presynaptic spike, equals the
    recorded value (Network._unitary_psp_weights). It is a value for one connection the recording
    names, never a free knob; later rows override earlier ones."""
    from pathlib import Path
    if not reg.require(
            "connectome:identified", "unitary_psp_from_recordings", units="boolean",
            model_use="measured unitary PSP per identified connection (data/params/unitary_psp.csv) "
                      "replaces the shared per-synapse scale on those edges",
            subsystem="synaptic_efficacy", instances=conn.n_edges, minimal=0.0, conventional=0.0,
            minimal_note="neutral 0: every edge from synapse count x the shared efficacy and gains"):
        return None
    path = Path(__file__).resolve().parents[2] / "data" / "params" / PSP_TABLE
    tab = pd.read_csv(path, comment="#")
    pre = np.repeat(np.arange(conn.n), np.diff(conn.indptr))
    row = np.full(conn.n_edges, -1, np.int32)
    for i, r in enumerate(tab.itertuples()):
        m = _stp_cells(conn.neurons, r.pre)[pre] & _stp_cells(conn.neurons, r.post)[conn.indices]
        if not m.any():
            raise ValueError(f"{PSP_TABLE}: row {r.pre} -> {r.post} matches no edge")
        bad = np.sign(conn.sign[pre[m]]) != np.sign(r.psp_mv)
        if bad.any():
            raise ValueError(f"{PSP_TABLE}: {r.pre} -> {r.post} is recorded with sign {np.sign(r.psp_mv):+g} "
                             f"but {int(bad.sum())} edges carry another transmitter sign (PSI needs "
                             "connectome:identified|nt_from_physiology = 1)")
        row[m] = i
        reg.provide(f"connection:{r.pre}->{r.post}", "unitary_psp_peak", float(r.psp_mv), units="mV",
                    model_use="peak PSP of one presynaptic spike (sets the edge weight)",
                    status=Status(r.basis), evidence=r.source, subsystem="synaptic_efficacy",
                    instances=int(m.sum()), uncertainty=r.note, method=r.condition)
    idx = np.flatnonzero(row >= 0)
    return {"idx": idx, "psp_mv": tab.psp_mv.to_numpy(np.float64)[row[idx]]}


def _two_compartments(reg: Registry, conn: Connectome) -> dict | None:
    """N30 first build (s20, fly2; DECISIONS 20 Oct 23:30): an axon compartment for the cells of
    two_compartment.csv, where a finding shows the point neuron fails, or None. The soma is the
    existing cell; the axon has the cell's tau_m, rest, threshold, reset and refractory, takes the
    listed inputs, and is where the cell's spikes start (Network._two_comp_init). The two class
    values (axon membrane share q, coupling rho) come from two_compartment_classes.csv, derived from
    guessed geometry; a run override replaces them for a sensitivity corner."""
    from pathlib import Path
    nc = reg.require("cell_type:all", "n_compartments", units="enum",
                     model_use="N30: compartments per neuron with synapses placed by position (FIDELITY_LADDER "
                               "rung 6; not built)", subsystem="neuron_biophysics", minimal=1.0, conventional=1.0,
                     minimal_note="neutral 1: point neurons except the cells of two_compartment.csv")
    if float(nc) != 1.0:
        raise NotImplementedError("cell_type:all|n_compartments: compartments per neuron with synapses placed by "
                                  "position are not built (N30); only cell_type:all|two_compartments_where_point_"
                                  "fails, for the cells of data/params/two_compartment.csv")
    if not reg.require(
            "cell_type:all", "two_compartments_where_point_fails", units="boolean",
            model_use="N30: an axon compartment where spikes start, with the listed inputs on it, for the "
                      "cells of data/params/two_compartment.csv",
            subsystem="neuron_biophysics", instances=conn.n, minimal=0.0, conventional=0.0,
            minimal_note="neutral 0: every cell is a point neuron"):
        return None
    root = Path(__file__).resolve().parents[2] / "data" / "params"
    tab = pd.read_csv(root / TWO_COMP_TABLE, comment="#").rename(columns={"class": "cls"})
    cls = pd.read_csv(root / TWO_COMP_CLASSES, comment="#").set_index("class")
    # s15 (fly): an arm control leaves a whole class out of a run (cell_class:<class>|two_compartments_in_run=0);
    # neutral 1, read only when set, so the rows of every class are on with the switch
    off = [c for c in tab.cls.unique() if f"cell_class:{c}|two_compartments_in_run" in reg.overrides
           and not float(reg.require(f"cell_class:{c}", "two_compartments_in_run", units="boolean",
                                     model_use="arm control: this two_compartment.csv class is on in this run "
                                               "(s15)", subsystem="neuron_biophysics", minimal=1.0,
                                     conventional=1.0, minimal_note="neutral 1: every class is on"))]
    tab = tab[~tab.cls.isin(off)]
    if tab.empty:
        return None
    pre = np.repeat(np.arange(conn.n), np.diff(conn.indptr))
    cell_row = np.full(conn.n, -1, np.int32)
    edges = []
    for i, r in enumerate(tab.itertuples()):
        cm = _stp_cells(conn.neurons, r.cells)
        em = _stp_cells(conn.neurons, r.axon_inputs)[pre] & cm[conn.indices]
        if not cm.any() or not em.any():
            raise ValueError(f"{TWO_COMP_TABLE}: row {r.cells} <- {r.axon_inputs} matches no cell or no edge")
        if r.cls not in cls.index:
            raise ValueError(f"{TWO_COMP_TABLE}: class {r.cls!r} has no row in {TWO_COMP_CLASSES}")
        cell_row[cm] = i
        edges.append(np.flatnonzero(em))
        reg.provide(f"cell_type:{r.cells}", "spike_initiation_compartment", "axon", units="compartment",
                    model_use="where the cell's spikes start (N30)", status=Status(r.basis), evidence=r.source,
                    subsystem="neuron_biophysics", instances=int(cm.sum()), uncertainty=r.note,
                    method=f"qualitative recording; finding {r.finding}")
        reg.provide(f"connection:{r.axon_inputs}->{r.cells}", "synapse_compartment", "axon",
                    units="compartment", model_use="these inputs land on the axon compartment (N30)",
                    status=Status(r.basis), evidence=r.source, subsystem="neuron_biophysics",
                    instances=int(em.sum()), uncertainty=r.note, method="anatomy of the contact")
    cells = np.flatnonzero(cell_row >= 0)
    ccls = tab.cls.to_numpy()[cell_row[cells]]
    vals = {}
    for c in tab.cls.unique():
        row = cls.loc[c]
        for prop, col, units, use in (
                ("axon_membrane_share", "q", "fraction of whole-cell membrane",
                 "axon compartment's share of the leak conductance and capacitance (N30)"),
                ("soma_axon_coupling", "rho", "coupling conductance x whole-cell input resistance",
                 "soma-axon coupling (N30)")):
            ent = f"cell_class:{c}"
            unc = f"sensitivity bracket {row[col + '_lo']}-{row[col + '_hi']} (pre-registered)"
            if f"{ent}|{prop}" in reg.overrides:   # a sensitivity corner
                v = reg.require(ent, prop, units=units, model_use=use, subsystem="neuron_biophysics",
                                instances=int((ccls == c).sum()), uncertainty=unc)
            else:
                v = reg.provide(ent, prop, float(row[col]), units=units, model_use=use, status=Status.INFERRED,
                                evidence=f"{row.derivation}; {row.source}", subsystem="neuron_biophysics",
                                instances=int((ccls == c).sum()), uncertainty=unc,
                                method=str(row.basis))
            vals[(c, col)] = float(v)
    q = np.array([vals[(c, "q")] for c in ccls])
    rho = np.array([vals[(c, "rho")] for c in ccls])
    if not (np.all((q > 0) & (q < 1)) and np.all(rho > 0)):
        raise ValueError(f"{TWO_COMP_CLASSES}: need 0 < q < 1 and rho > 0")
    return {"cells": cells, "edge_idx": np.unique(np.concatenate(edges)), "q": q, "rho": rho}



def _flyvis_pairs(reg: Registry, conn: Connectome) -> dict | None:
    """s14 (fly2, DECISIONS 13 Oct 22:53): flyvis type-pair strengths (Lappalainen et al. 2024), or None.
    flyvis gives a cell of type t the input sign x n_syn x alpha_st x relu(V_s) from a type-s cell, so
    alpha is a fitted voltage gain per synapse (task-trained, not physiology). Each read row (use = 1) is
    returned per edge between cells of its two types; Network._flyvis_pair_weights converts it for graded
    presynaptic cells. Selectors must be disjoint, so each cell belongs to at most one row type."""
    from pathlib import Path
    if not reg.require(
            "cell_type:all", "optic_lobe_flyvis_pair_strength", units="boolean",
            model_use="flyvis type-pair strengths (fitted, task-trained; data/params/flyvis_pair_strength.csv) "
                      "replace the shared per-synapse scale on optic-lobe edges from graded cells",
            subsystem="synaptic_efficacy", instances=conn.n_edges, minimal=0.0, conventional=0.0,
            minimal_note="neutral 0: every edge from synapse count x the shared efficacy and gains"):
        return None
    path = Path(__file__).resolve().parents[2] / "data" / "params" / FV_PAIR_TABLE
    tab = pd.read_csv(path, comment="#")
    tab = tab[tab.use == 1].reset_index(drop=True)
    sels = sorted(set(tab.pre) | set(tab.post))
    code = np.full(conn.n, -1, np.int32)
    for k, sel in enumerate(sels):
        m = _stp_cells(conn.neurons, sel)
        if (code[m] >= 0).any():
            raise ValueError(f"{FV_PAIR_TABLE}: selector {sel} overlaps {sels[code[m][code[m] >= 0][0]]}")
        code[m] = k
    alpha = np.full((len(sels), len(sels)), np.nan)
    alpha[tab.pre.map(sels.index), tab.post.map(sels.index)] = tab.alpha
    pre = np.repeat(np.arange(conn.n), np.diff(conn.indptr))
    cp, cq = code[pre], code[conn.indices]
    on = (cp >= 0) & (cq >= 0)
    a = np.full(conn.n_edges, np.nan)
    a[on] = alpha[cp[on], cq[on]]
    idx = np.flatnonzero(np.isfinite(a))
    sgn = dict(zip(zip(tab.pre.map(sels.index), tab.post.map(sels.index)), tab.flyvis_sign))
    flip = sum(np.sign(conn.sign[pre[e]]) != sgn[(cp[e], cq[e])] for e in idx)
    reg.provide("cell_type:optic_lobe_pairs", "flyvis_pair_strength", float(np.median(tab.alpha)),
                units="mV/mV per synapse", model_use="voltage gain per synapse per type pair (sets the edge "
                "weight of graded presynaptic cells); the value is the median over read rows",
                status=Status.INFERRED, evidence="Lappalainen et al. 2024 flyvis ensemble (50 networks); "
                + FV_PAIR_TABLE, subsystem="synaptic_efficacy", instances=int(idx.size),
                uncertainty=f"per-row quartiles in the table; {int(on.sum() - idx.size)} edges between mapped "
                f"types have no flyvis pair and keep the shared scale; {int(flip)} edges carry a sign other "
                "than flyvis's (our sign kept)", method="fitted (flyvis, task-trained)")
    return {"idx": idx, "alpha": a[idx]}


def _stp_connections(reg: Registry, conn: Connectome) -> dict | None:
    """Rung 8 (N29, s12): Tsodyks-Markram parameters per connection class, or None."""
    from pathlib import Path
    mode = float(reg.require(
        "synapse:all", "per_synapse_parameters", units="enum",
        model_use="N29 rung 8: short-term plasticity per connection class "
                  "(data/params/stp_connections.csv); other per-synapse values not built",
        subsystem="synaptic_efficacy", instances=conn.n_edges, minimal=0.0, conventional=0.0,
        minimal_note="neutral 0: short-term depression per presynaptic cell only (N10)"))
    if mode == 0.0:
        return None
    if mode != 1.0:
        raise NotImplementedError(
            f"synapse:all|per_synapse_parameters = {mode:g}: only 1 (STP per connection "
            "class) is built; per-synapse weight, release probability, receptor mix and "
            "latency are not")
    path = Path(__file__).resolve().parents[2] / "data" / "params" / STP_TABLE
    tab = pd.read_csv(path, comment="#")
    pre = np.repeat(np.arange(conn.n), np.diff(conn.indptr))
    row = np.full(conn.n_edges, -1, np.int32)
    for i, r in enumerate(tab.itertuples()):
        m = _stp_cells(conn.neurons, r.pre)[pre] & _stp_cells(conn.neurons, r.post)[conn.indices]
        row[m] = i
        for prop, val, u in (("stp_U", r.U, "dimensionless"), ("stp_tau_rec", r.tau_rec_ms, "ms"),
                             ("stp_tau_facil", r.tau_facil_ms, "ms")):
            reg.provide(f"connection:{r.pre}->{r.post}", prop, float(val), units=u,
                        model_use="per-connection short-term plasticity (rung 8, N29)",
                        status=Status(r.basis), evidence=r.source, subsystem="synaptic_efficacy",
                        instances=int(m.sum()), uncertainty=r.note,
                        method="published single-component depression fit; U = 1 - f")
    idx = np.flatnonzero(row >= 0)
    k = row[idx]
    return {"idx": idx, "U": tab.U.to_numpy(np.float64)[k],
            "tau_rec": tab.tau_rec_ms.to_numpy(np.float64)[k],
            "tau_f": tab.tau_facil_ms.to_numpy(np.float64)[k]}


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


CLASS_PROPS = (  # (property, units, neutral, model use)
    ("release_scale", "dimensionless", 1.0, "N5: presynaptic release strength of every cell in the class"),
    ("input_scale", "dimensionless", 1.0, "N5: postsynaptic gain of every cell in the class"),
    ("tonic_drive", "mV", 0.0, "N3: tonic depolarisation (unmodelled background input) per class"),
    ("noise", "mV/sqrt(ms)", 0.0, "N3: class background noise, added in quadrature to the global noise"),
    ("threshold_offset", "mV", 0.0, "N2: spike threshold shift of every cell in the class"),
    ("tau_m_scale", "dimensionless", 1.0, "N2: membrane time constant scale of every cell in the class"),
)


def circuit_classes(conn: Connectome) -> np.ndarray:
    """Per-neuron circuit class from data/model/classes.csv (untyped cells as
    `untyped:<superclass>`, the key build_classes.py uses)."""
    from pathlib import Path
    path = Path(__file__).resolve().parents[2] / "data" / "model" / "classes.csv"
    c = pd.read_csv(path, keep_default_na=False).set_index("type").circuit_class
    n = conn.neurons
    key = np.where(n.type.notna(), n.type, "untyped:" + n.superclass.fillna("none"))
    out = pd.Series(key).map(c)
    return out.fillna("unassigned").to_numpy(str)


def _class_scales(reg: Registry, conn: Connectome, rel, inp, spont):
    """N3/N5 at class grain: one registry value per (circuit class, property),
    owned by rows in data/model/parameters.csv. Neutral values (1, 1, 0, 0) leave
    the per-type arrays bit-identical (x*1.0 and x+0.0 are exact in float32)."""
    cls = circuit_classes(conn)
    names, idx = np.unique(cls, return_inverse=True)
    vals = {}
    for prop, units, neutral, use in CLASS_PROPS:
        v = np.array([reg.require(
            f"class:{c}", prop, units=units, model_use=use, subsystem="neuron_biophysics",
            instances=int((idx == k).sum()), minimal=neutral, conventional=neutral,
            minimal_note=f"neutral ({neutral}): the class adds nothing to the per-type values",
            uncertainty="class grain from data/model/classes.csv circuit_class; value is a "
                        "search parameter bounded in data/model/parameters.csv")
            for k, c in enumerate(names)], dtype=np.float32)
        vals[prop] = v[idx]
    rel = np.asarray(rel, np.float32) * vals["release_scale"]
    inp = np.asarray(inp, np.float32) * vals["input_scale"]
    spont = np.asarray(spont, np.float32) + vals["tonic_drive"]
    noise = vals["noise"] if vals["noise"].any() else None
    tonic = vals["tonic_drive"] if vals["tonic_drive"].any() else None
    return rel, inp, spont, noise, tonic, vals["threshold_offset"], vals["tau_m_scale"]


CLASS_ADAPT_PROPS = (  # s13 (frontier stage 1): N4 at class grain, same keys and bounds file as CLASS_PROPS
    ("adaptation_mv", "mV", 0.0, "N4: spike-frequency adaptation increment per spike, added to the per-type value"),
    ("adaptation_tau_scale", "dimensionless", 1.0, "N4: adaptation decay time scale of every cell in the class"),
)


def _class_adaptation(reg: Registry, conn: Connectome, adapt, tau_adapt):
    """N4 at class grain (s13): one registry value per (circuit class, property), `class:<c>|adaptation_mv`
    added to the per-type increment and `class:<c>|adaptation_tau_scale` multiplying the per-type decay.
    Neutral values (0, 1) return the per-type values unchanged."""
    cls = circuit_classes(conn)
    names, idx = np.unique(cls, return_inverse=True)
    vals = {}
    for prop, units, neutral, use in CLASS_ADAPT_PROPS:
        vals[prop] = np.array([reg.require(
            f"class:{c}", prop, units=units, model_use=use, subsystem="neuron_biophysics",
            instances=int((idx == k).sum()), minimal=neutral, conventional=neutral,
            minimal_note=f"neutral ({neutral}): the class adds nothing to the per-type values",
            uncertainty="class grain from data/model/classes.csv circuit_class; value fitted to a recorded "
                        "adaptation ratio where one exists, bounded in data/model/parameters.csv")
            for k, c in enumerate(names)], dtype=np.float32)[idx]
    if vals["adaptation_mv"].any():
        adapt = np.asarray(adapt, np.float32) + vals["adaptation_mv"]
    if (vals["adaptation_tau_scale"] != 1.0).any():
        tau_adapt = np.asarray(tau_adapt, np.float32) * vals["adaptation_tau_scale"]
    return adapt, tau_adapt


def _class_modes(reg: Registry, conn: Connectome, graded: np.ndarray) -> np.ndarray:
    """N1 (s10): the spiking/graded mode of classes whose mode is unknown
    (classes.csv mode = unknown) is one Bernoulli unknown per group (mode_param
    rows in parameters.csv). Registry key `mode:<param>|graded`: 0 spiking (m4), 1 graded.
    Types with a measured/inferred mode row in cell_types.csv are not changed."""
    from pathlib import Path
    path = Path(__file__).resolve().parents[2] / "data" / "model" / "classes.csv"
    c = pd.read_csv(path, keep_default_na=False)
    unk = c[c["mode"] == "unknown"]
    n = conn.neurons
    key = pd.Series(np.where(n.type.notna(), n.type, "untyped:" + n.superclass.fillna("none")))
    out = np.asarray(graded, bool).copy()
    for prm, grp in unk.groupby("mode_param"):
        m = key.isin(set(grp.type)).to_numpy()
        v = reg.require(f"mode:{prm}", "graded", units="boolean",
                        model_use="N1: graded (1) or spiking (0) transmission for this class group",
                        subsystem="neuron_biophysics", instances=int(m.sum()), minimal=0.0,
                        minimal_note="spiking, as in m4; the mode is a Bernoulli unknown (parameters.csv)")
        if v:
            out[m] = True
    return out


GRADED_CLASSES = ("vnc_local_16B",)   # s14 A: circuit classes with a class-grain mode switch


def _class_graded(reg: Registry, conn: Connectome, graded: np.ndarray) -> np.ndarray:
    """s14 arm A (DIAGNOSTIC): graded (1) or spiking (0) transmission for every unknown-mode type of one
    circuit class, `class:<c>|graded`, finer than the N1 vnc_local group (one hemilineage, not all).
    Types with a recorded mode row still win (mode_from_recordings is applied after this)."""
    from pathlib import Path
    c = pd.read_csv(Path(__file__).resolve().parents[2] / "data" / "model" / "classes.csv",
                    keep_default_na=False)
    cls = circuit_classes(conn)
    n = conn.neurons
    key = np.where(n.type.notna(), n.type, "untyped:" + n.superclass.fillna("none"))
    out = np.asarray(graded, bool).copy()
    for name in GRADED_CLASSES:
        unk = set(c.type[(c.circuit_class == name) & (c["mode"] == "unknown")])
        m = (cls == name) & pd.Series(key).isin(unk).to_numpy()
        v = reg.require(f"class:{name}", "graded", units="boolean",
                        model_use="s14 A: graded (1) or spiking (0) transmission for the unknown-mode "
                                  "types of this circuit class (hemilineage)",
                        subsystem="neuron_biophysics", instances=int(m.sum()), minimal=0.0, conventional=0.0,
                        minimal_note="neutral 0: spiking, as the N1 group default")
        if v:
            out[m] = True
    return out


def _core_rhythm_adp(reg: Registry, conn: Connectome):
    """s14 arm B (DIAGNOSTIC): spike-triggered after-depolarisation of the excitatory cells of the walking
    rhythm core (E1 IN17A001, E2 INXXX466; percell.CORE_RHYTHM_EXC), one value shared by both types and
    all neuromere copies. A spike moves the ADP drive toward `adp_mv` by the available fraction h, so the drive
    saturates at `adp_mv` (a conductance has a ceiling); it decays at `adp_tau_ms`. With `adp_recovery_ms` > 0
    each trigger uses up the availability (h -> 0), which recovers at that time constant, so a plateau ends
    (Hancox & Pitman 1991); 0 = no inactivation. Neutral adp_mv 0: off. Commit e16b3b7 had the additive,
    unbounded form (each spike added adp_mv): it latches (docs/research/s14_burst_ranges.md)."""
    from . import percell as _pc
    m = _pc.core_rhythm_mask(conn)
    amp = reg.require("cell_type:core_rhythm_exc", "adp_mv", units="mV",
                      model_use="after-depolarisation ceiling (E1/E2 types): each spike moves the drive toward it",
                      subsystem="neuron_biophysics", instances=int(m.sum()), minimal=0.0, conventional=0.0,
                      minimal_note="neutral 0: no after-depolarisation")
    tau = reg.require("cell_type:core_rhythm_exc", "adp_tau_ms", units="ms",
                      model_use="decay time constant of the E1/E2 after-depolarisation",
                      subsystem="neuron_biophysics", instances=int(m.sum()), minimal=20.0, conventional=20.0,
                      minimal_note="guessed 20 ms; inert while adp_mv is 0")
    rec = reg.require("cell_type:core_rhythm_exc", "adp_recovery_ms", units="ms",
                      model_use="recovery of the E1/E2 ADP availability after each trigger (0: no inactivation)",
                      subsystem="neuron_biophysics", instances=int(m.sum()), minimal=0.0, conventional=0.0,
                      minimal_note="neutral 0: no inactivation; inert while adp_mv is 0")
    if not amp:
        return None, float(tau), float(rec)
    return np.where(m, np.float32(amp), np.float32(0.0)).astype(np.float32), float(tau), float(rec)


FLYVIS_TABLE = ptable.TABLE.with_name("cell_types_flyvis.csv")


def _optic_lobe_flyvis(reg: Registry, conn: Connectome, table: pd.DataFrame) -> dict:
    """fly2 (s13, DECISIONS 13 Oct): per-type optic-lobe values read out of the 50 published flyvis networks
    (Lappalainen et al. 2024; data/params/cell_types_flyvis.csv, scripts/vision/flyvis_rows.py), all fitted
    (inferred): graded mode, effective time constant and release at rest. Each quantity fills only the cells
    whose type has no row of its own for it in cell_types.csv. Arrays are NaN outside the mapped types; `own_*`
    marks cells with their own row."""
    fvt = ptable.load(FLYVIS_TABLE)
    out = {}
    for prop, own, units in (("graded", "graded", "boolean"), ("tau_m", "tau_m", "ms"),
                             ("release_at_rest", "release_at_rest", "fraction of graded_rmax")):
        out[prop] = ptable.per_neuron(reg, conn, prop + "_flyvis", np.nan, units=units, table=fvt)
        out["own_" + prop] = np.isfinite(ptable.per_neuron(reg, conn, own, np.nan, units=units, table=table))
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
    # s11 fill F3 (DECISIONS 2026-10-01 02:49): recorded resting potentials per type, as a
    # shift from the global rest applied to rest, threshold and reset alike (gap kept)
    if one("rest_from_recordings", "boolean", "per-type recorded resting potentials", 0.0,
           "neutral 0: one resting potential for every neuron"):
        dv = per("v_rest_shift_rec", "mV", "recorded rest minus the global v_rest", 0.0,
                 "neutral 0 for types without a recording")
        v_rest, v_th, v_reset = v_rest + dv, v_th + dv, v_reset + dv
    # s12 vision (DECISIONS 6 Oct, F-VISION-6): a recorded resting potential is the cell's potential in the
    # network, tonic synaptic input included, not its leak reversal. 1 shifts the leak reversal alone by the
    # per-type v_leak_shift_fit rows (fitted in the network, scripts/probes/visual_rest_calibrate.py);
    # threshold, reset, the graded release reference and the conductance reference stay at the rest
    v_leak = None
    if one("leak_from_network_rest", "boolean", "leak reversal fitted so the in-network rest is the recorded one",
           0.0, "neutral 0: the leak reversal is the resting potential"):
        dl = ptable.per_neuron(reg, conn, "v_leak_shift_fit", 0.0, units="mV", table=table)
        v_leak = (np.asarray(v_rest, np.float32) + dl).astype(np.float32)
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
    stp_edge = _stp_connections(reg, conn)   # s12 rung 8 (N29); None at neutral
    kin_edge = _receptor_kinetics(reg, conn)   # s13 (N29); None at neutral
    psp_edge = _unitary_psp(reg, conn)   # s14 (fly2); None at neutral
    two_comp = _two_compartments(reg, conn)   # s20 (fly2, N30); None at neutral
    fv_edge = _flyvis_pairs(reg, conn)   # s14 (fly2); None at neutral
    graded = per("graded", "boolean", "graded (non-spiking) transmission",
                 0.0, "declared default: spiking; graded types listed in cell_types.csv")
    graded = _class_modes(reg, conn, graded)
    graded = _class_graded(reg, conn, graded)
    fv = None
    if one("optic_lobe_flyvis", "boolean", "per-type optic-lobe mode, time constant and release at rest "
           "from the flyvis ensemble", 0.0, "neutral 0: no flyvis rows read"):
        fv = _optic_lobe_flyvis(reg, conn, table)
        graded = graded | ((fv["graded"] > 0.5) & ~fv["own_graded"])   # recorded modes still win below
    # s12 vision blank (DECISIONS 6 Oct): per-type mode from recordings (cell_types.csv
    # graded_rec rows, 1 graded, 0 spiking) overrides the class groups for those types only
    if one("mode_from_recordings", "boolean", "per-type spiking/graded mode from recordings", 0.0,
           "neutral 0: modes from the graded rows and the class-group unknowns"):
        rec = ptable.per_neuron(reg, conn, "graded_rec", np.nan, units="boolean", table=table)
        graded = np.where(np.isnan(rec), graded, rec > 0.5)
    rmax = one("graded_rmax", "Hz", "graded rate-equivalent at threshold", 100.0,
               "guessed: maps graded depolarisation to spike-equivalent transmission")
    # s12 vision blank (DECISIONS 6 Oct): optic-lobe graded synapses release tonically at rest, so a
    # hyperpolarisation lowers release (Juusola et al. 1996 TINS); 0 = release starts at rest (m4)
    ol_graded = graded & conn.neurons.superclass.eq("ol_intrinsic").to_numpy()
    r0 = reg.require("cell_type:ol_graded", "release_at_rest", units="fraction of graded_rmax",
                     model_use="graded release at the resting potential, optic-lobe graded interneurons",
                     subsystem="neuron_biophysics", instances=int(ol_graded.sum()), minimal=0.0,
                     minimal_note="neutral 0: no release at or below rest, as m4")
    graded_r0 = np.where(ol_graded, np.float32(r0), np.float32(0.0)) if r0 else None
    # s12 vision Mi1/Tm3 block (DECISIONS 6 Oct): per-type release at rest (release_at_rest rows)
    # replaces the class value for the graded cells of those types only
    own_r0 = np.zeros(conn.n, bool)
    if one("release_at_rest_per_type", "boolean", "per-type graded release at rest from rows", 0.0,
           "neutral 0: one class value for the optic-lobe graded interneurons"):
        rt = ptable.per_neuron(reg, conn, "release_at_rest", np.nan, units="fraction of graded_rmax",
                               table=table)
        base_r0 = graded_r0 if graded_r0 is not None else np.zeros(conn.n, np.float32)
        graded_r0 = np.where(graded & np.isfinite(rt), rt, base_r0).astype(np.float32)
        own_r0 = np.isfinite(rt)
    if fv is not None:   # flyvis release at rest for graded cells of the mapped types, where no active own row
        use = graded & np.isfinite(fv["release_at_rest"]) & ~own_r0
        if use.any():
            base_r0 = graded_r0 if graded_r0 is not None else np.zeros(conn.n, np.float32)
            graded_r0 = np.where(use, fv["release_at_rest"], base_r0).astype(np.float32)
    spont = per("spontaneous_drive", "mV", "tonic drive (spontaneous activity)",
                0.0, "declared default: no tonic drive")
    rel = per("release_gain", "dimensionless", "presynaptic release strength",
              1.0, "declared default: every type releases the shared efficacy")
    inp = per("input_gain", "dimensionless", "postsynaptic input sensitivity",
              1.0, "declared default: every type receives the shared efficacy")
    intrinsic = ichan.from_registry(reg, conn, timestep_ms=timestep_ms)
    if intrinsic is not None:
        # rung 1 (s11): classes refitted with the channels on replace their LIF-only rows
        # (data/params/cell_types.csv *_rung1; DECISIONS 2026-09-30 21:17 and 21:20)
        for prop, units, arr in (("v_th", "mV", v_th), ("t_ref", "ms", t_ref),
                                 ("spontaneous_drive", "mV", spont)):
            alt = ptable.per_neuron(reg, conn, prop + "_rung1", np.nan, units=units, table=table)
            fin = np.isfinite(alt)
            arr[fin] = alt[fin]
    # --- session 10: per-circuit-class background drive (N3) and synaptic strength (N5)
    rel, inp, spont, noise_class, tonic_class, th_off, tm_scale = _class_scales(reg, conn, rel, inp, spont)
    adapt, tau_adapt = _class_adaptation(reg, conn, adapt, tau_adapt)
    adp_mv, tau_adp, adp_rec_ms = _core_rhythm_adp(reg, conn)
    v_th = (np.asarray(v_th, np.float32) + th_off).astype(np.float32)
    if fv is not None:   # flyvis effective time constant for the mapped types without a tau_m row; class scale kept
        tau_m = np.where(np.isfinite(fv["tau_m"]) & ~fv["own_tau_m"], fv["tau_m"], tau_m)
    tau_m = (np.asarray(tau_m, np.float32) * tm_scale).astype(np.float32)
    # s12 vision gain (DECISIONS 6 Oct): graded release spans the type's recorded response amplitude
    # (cell_types.csv graded_range_rec rows) instead of rest to threshold (7 mV in the optic lobe, guessed)
    # 2: as 1, and each graded synapse keeps its transfer per mV at rest (release x span / (v_th - v_rest)),
    # so only the saturation point moves (derived compensation; tonic release at rest scales with it)
    graded_range, graded_k = None, None
    gmode = one("graded_range_from_recordings", "switch", "per-type graded release range from recordings",
                0.0, "neutral 0: graded release spans rest to threshold; 1 recorded span; 2 recorded span "
                     "with the per-mV transfer at rest kept")
    if gmode:
        gr = ptable.per_neuron(reg, conn, "graded_range_rec", np.nan, units="mV", table=table)
        d0 = v_th - np.asarray(v_rest, np.float32)
        graded_range = np.where(np.isfinite(gr), gr, d0).astype(np.float32)
        if gmode >= 2:
            graded_k = (graded_range / d0).astype(np.float32)
    # --- session 11: per-cell input gain from within-type size/input rules (percell.py)
    from . import percell
    f_cell = percell.input_gain_factors(reg, conn)
    if f_cell is not None:
        inp = (np.asarray(inp, np.float32) * f_cell).astype(np.float32)
    # --- session 10: N7 metabotropic components and N8 NMDA-type excitation ----
    mglur = per("mglur_fraction", "dimensionless", "share of glutamatergic input that is slow "
                "(metabotropic)", 0.0, "neutral 0: DmGluRA is expressed centrally but per-type "
                "shares are unmeasured")
    mglur_tau = one("mglur_tau", "ms", "slow metabotropic glutamate current decay", 300.0,
                    "guessed: GPCR currents last hundreds of ms")
    machr = per("machr_fraction", "dimensionless", "share of cholinergic input that is slow "
                "(muscarinic)", 0.0, "neutral 0: mAChR-A/B expressed in fly central neurons; "
                "per-type shares unmeasured")
    machr_tau = one("machr_tau", "ms", "slow muscarinic current decay", 300.0,
                    "guessed: GPCR currents last hundreds of ms")
    nmda = per("nmda_fraction", "dimensionless", "share of excitatory glutamatergic input carried "
               "by NMDA-type receptors (voltage-dependent Mg block)", 0.0,
               "neutral 0: Nmdar1/2 expressed in fly central neurons; per-type shares unmeasured")
    nmda_tau = one("nmda_tau", "ms", "NMDA-type current decay", 80.0,
                   "guessed: vertebrate NMDA decay 50-150 ms; fly unmeasured")
    nmda_mg = one("nmda_mg", "mM", "extracellular Mg for the NMDA block", 1.0,
                  "guessed: insect saline 4-20 mM Mg; block constants borrowed from vertebrate "
                  "(Jahr & Stevens 1990)")
    cond = one("conductance_based", "boolean", "synapse model",
               0.0, "declared default: current-based synapses")
    e_exc = one("e_exc", "mV", "excitatory reversal (conductance mode)",
                0.0, "declared default cation reversal")
    e_inh = one("e_inh", "mV", "inhibitory reversal (conductance mode)",
                -70.0, "declared default chloride reversal")
    tau_s_inh = per("tau_s_inh", "ms", "fast inhibitory conductance decay (conductance mode)",
                    0.0, "neutral 0: decays with tau_s, as the excitatory conductance")
    cond_ref = one("cond_reference", "boolean", "voltage at which conductance weights keep their effect",
                   0.0, "neutral 0: resting PSP preserved; 1 = effect at threshold preserved "
                        "(DECISIONS 2026-10-01 02:49)")
    inh_scale = one("inh_cond_scale", "dimensionless", "inhibitory conductance per unit fitted weight",
                    1.0, "neutral 1 (conductance mode only); searched (DECISIONS 2026-10-01 03:23)")
    share_basis = one("slow_share_basis", "boolean", "slow-receptor share basis",
                      0.0, "neutral 0: a slow share f moves f of the fast peak to the slow "
                           "pool (m4-m9); 1 = f of the fast charge (peak f tau_s/tau_slow), "
                           "DECISIONS 2026-10-01 01:06")

    # --- session 6: absent mechanisms now simulated, defaults neutral ---------
    glu_sign = per("glutamate_receptor_sign", "sign", "sign of glutamatergic input onto this type",
                   0.0, "neutral default 0: use the transmitter-level glutamate sign "
                        "(profile); +1 = excitatory (iGluR), -1 = inhibitory (GluCl) per "
                        "postsynaptic type via cell_types.csv rows")
    leg_glu = reg.require(
        "cell_type:leg_motor", "glutamate_receptor_sign", units="sign",
        model_use="sign of glutamatergic input onto every leg MN (overrides per-type rows)",
        subsystem="synaptic_efficacy", instances=n, minimal=0.0, conventional=0.0,
        minimal_note="neutral 0: transmitter-level glutamate sign (inhibitory) onto leg MNs",
        uncertainty="S4a arm G (DECISIONS 13 Oct 23:31): +1 inferred from mixed receptor evidence "
                    "(Allen 2020: GluClalpha with NMDA/kainate subunits in MN clusters); no leg-MN "
                    "glutamate PSP recorded")
    if leg_glu:
        from . import percell as _pc
        glu_sign = np.where(_pc.leg_motor_mask(conn), np.float32(leg_glu),
                            np.asarray(glu_sign, np.float32)).astype(np.float32)
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
    kc_ltd_t = one("kc_mbon_ltd_timing_rate", "per DAN spike per unit KC eligibility",
                   "N21: KC->MBON depression when KC activity precedes dopamine", 0.0,
                   "neutral 0; forward pairing depresses (Hige et al. 2015; Handler et al. 2019)")
    kc_ltp_t = one("kc_mbon_ltp_timing_rate", "per KC spike per unit DAN trace",
                   "N21: KC->MBON potentiation when dopamine precedes KC activity", 0.0,
                   "neutral 0; backward pairing potentiates (Handler et al. 2019 Cell)")
    kc_elig = one("kc_eligibility_tau", "ms", "N21: KC eligibility trace decay", 1000.0,
                  "guessed: seconds-scale plasticity window (Handler et al. 2019)")
    kc_cap = one("kc_mbon_weight_cap", "x baseline", "N21: potentiation ceiling", 2.0,
                 "guessed")
    kc_forget = one("kc_mbon_forgetting", "boolean", "N22: KC->MBON weights relax to "
                    "baseline (forgetting)", 0.0, "off in m4")
    kc_mem_h = one("kc_mbon_memory_tau_h", "h", "N22: relaxation time constant", 3.0,
                   "guessed within the n22_memory_tau bounds (aversive STM decays over hours)")
    kc_rec = float(kc_mem_h) * 3.6e6 if kc_forget else 0.0
    kc_res = one("kc_mbon_dan_restore_rate", "per DAN spike",
                 "N21/N22: a DAN spike moves KC->MBON weights in its compartments toward "
                 "baseline, with or without KC activity", 0.0,
                 "neutral 0; unpaired DAN activity restores depressed KC->MBON transmission "
                 "(Cohn et al. 2015 Fig 7I; Hattori et al. 2017 Fig 6F; Berry et al. 2018 Fig 5H-I)")
    ring_eta = one("ring_epg_plasticity_rate", "per ER spike per unit EPG trace",
                   "N24: coactive ER->EPG inhibitory synapses weaken (visual map learning)", 0.0,
                   "neutral 0: Fisher et al. 2019 Nature; Kim et al. 2019 Nature (leads, not read)")
    ring_tt = one("ring_epg_trace_tau", "ms", "N24: EPG activity trace", 100.0, "guessed")
    ring_rec = one("ring_epg_recovery_tau", "ms", "N24: relaxation to baseline", 60000.0, "guessed")
    ring_floor = one("ring_epg_floor", "x baseline", "N24: minimum weight", 0.2, "guessed")
    glia_g = one("glia_k_gain", "mV per unit load", "N27: depolarisation by extracellular K+ "
                 "load per circuit class (lumped glia)", 0.0, "neutral 0: glial K+ buffering "
                 "(lumped; no fly measurement read)")
    glia_tau = one("glia_k_tau", "ms", "N27: glial K+ clearance", 2000.0, "guessed: seconds")
    apl_loc = one("apl_compartmental", "dimensionless", "N23: APL->KC inhibition follows the "
                  "local (KC-subtype lobe) activity instead of whole-APL depolarisation", 0.0,
                  "neutral 0 (point APL, m4); APL Ca2+ is compartmentalised (Amin et al. 2020 "
                  "Neuron, lead); lobe = KC subtype (ab, g, a'b') is a proxy for locality")
    apl_tau = one("apl_local_tau", "ms", "N23: local KC activity estimate", 50.0, "guessed")
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

    # --- session 11 rung 2: slow-receptor shares per cell from receptor mRNA (receptors.py)
    from . import receptors
    rr = receptors.from_registry(reg, conn)
    if rr is not None:
        sh, _src = rr
        gabab, mglur, machr, nmda = (sh["gabab_fraction"], sh["mglur_fraction"],
                                     sh["machr_fraction"], sh["nmda_fraction"])

    # --- s13 (fly2, N12): identified gap junctions (data/params/gap_junctions.csv); None at neutral
    from . import electrical
    gap = electrical.build_gap(reg, conn, tau_m, v_rest, v_th, delay_ms, timestep_ms)

    return LIFParams(
        tau_m=tau_m, v_rest=v_rest, v_leak=v_leak, v_th=v_th, v_reset=v_reset, t_ref=t_ref,
        tau_s=tau_s, slow_share_basis=share_basis, cond_reference=cond_ref, inh_cond_scale=inh_scale,
        delay_steps=np.maximum(1, np.round(delay_ms / timestep_ms)).astype(np.int64),
        noise_mv=noise, reset_syn=bool(reset_syn), adapt_mv=adapt,
        tau_adapt=tau_adapt, adp_mv=adp_mv, tau_adp=tau_adp, adp_rec_ms=adp_rec_ms,
        std_u=std_u, std_tau_rec=std_tau, stp_edge=stp_edge, cond=bool(cond),
        e_exc=float(e_exc), e_inh=float(e_inh), graded=graded.astype(bool),
        graded_rmax_hz=float(rmax), graded_r0=graded_r0, graded_range=graded_range, graded_k=graded_k, spont_mv=spont,
        release_gain=rel,
        input_gain=inp, mod_release=mod_release, mod_sensitivity=sens,
        mod_tau_ms=float(mod_tau),
        mod_increment=float(mod_inc) / max(1.0, n_mod_cells / 1000.0),
        glu_sign_post=glu_sign, gabab_fraction=gabab, gabab_tau_ms=float(gabab_tau),
        presyn_inh_gain=float(pi_gain), kc_mbon_eta=float(kc_eta), dan_tau_ms=float(dan_tau),
        kc_ltd_timing=float(kc_ltd_t), kc_ltp_timing=float(kc_ltp_t), kc_elig_tau_ms=float(kc_elig),
        kc_w_cap=float(kc_cap), kc_recovery_tau_ms=float(kc_rec), kc_restore=float(kc_res),
        ring_eta=float(ring_eta), ring_trace_tau_ms=float(ring_tt), ring_recovery_tau_ms=float(ring_rec),
        ring_floor=float(ring_floor), glia_gain_mv=float(glia_g), glia_tau_ms=float(glia_tau),
        apl_local=float(apl_loc), apl_local_tau_ms=float(apl_tau),
        ring_class_norm=bool(ring_norm), noise_class_mv=noise_class,
        tonic_class_mv=tonic_class,
        mglur_fraction=mglur, mglur_tau_ms=float(mglur_tau), machr_fraction=machr,
        machr_tau_ms=float(machr_tau), nmda_fraction=nmda, nmda_tau_ms=float(nmda_tau),
        nmda_mg_mM=float(nmda_mg),
        intrinsic=intrinsic, tau_s_inh=tau_s_inh, gap=gap, kin_edge=kin_edge, fv_edge=fv_edge,
        psp_edge=psp_edge, two_comp=two_comp,
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
        self.v_leak = self.v_rest if p.v_leak is None else _arr(p.v_leak, n)   # membrane equation only
        self.v_th = _arr(p.v_th, n)
        self.v_reset = _arr(p.v_reset, n)
        self.t_ref = _arr(p.t_ref, n)
        self.adapt_mv = _arr(p.adapt_mv, n)
        self.std_u = _arr(p.std_u, n)
        self.spont = _arr(p.spont_mv, n)
        self.input_gain = _arr(p.input_gain, n)
        self.graded = (np.zeros(n, bool) if p.graded is None else np.asarray(p.graded, bool))
        self.ich = copy.deepcopy(p.intrinsic)   # per-network gate state
        if self.ich is not None:
            self.ich.init(self.v_rest)
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
        self._flyvis_pair_weights(pre)
        self._two_comp_init(pre)
        self._unitary_psp_weights()
        self._slow_channels(pre)
        self._kinetic_channels(pre)
        if p.ring_class_norm:
            self._ring_class_norm(pre)
        self._edge_scales(pre)
        self.delay = np.zeros((self.D, n), dtype=np.float32)
        if p.cond:
            # rung 2 repair 2: the voltage at which a weight keeps its fitted effect
            vr = (self.v_th if p.cond_reference else self.v_rest)[self.conn.indices]
            pos = self.w > 0
            self.w = np.where(pos, self.w / (p.e_exc - vr),
                              p.inh_cond_scale * self.w / (vr - p.e_inh)).astype(np.float32)
            self.delay_i = np.zeros((self.D, n), dtype=np.float32)
            self.g_i = np.zeros(n, dtype=np.float32)
        self.delay_head = 0
        self.decay_v = np.exp(-dt / self.tau_m).astype(np.float32)
        self.decay_s = np.exp(-dt / _arr(p.tau_s, n)).astype(np.float32)
        tsi = _arr(p.tau_s_inh, n)
        self.decay_si = np.where(tsi > 0, np.exp(-dt / np.where(tsi > 0, tsi, 1.0)),
                                 self.decay_s).astype(np.float32)
        self.decay_a = np.exp(-dt / _arr(p.tau_adapt, n)).astype(np.float32)
        self.rec_step = (1.0 - np.exp(-dt / _arr(p.std_tau_rec, n))).astype(np.float32)
        self.spike_count = 0
        self.adapt = np.zeros(n, dtype=np.float32)
        # s14 B: spike-triggered after-depolarisation (drive += adp; a spike moves adp toward adp_mv by the
        # availability h; decays at tau_adp; h -> 0 per trigger, recovering at adp_rec_ms; 0 = h stays 1)
        self.adp_mv = None if p.adp_mv is None or not np.any(p.adp_mv) else _arr(p.adp_mv, n)
        if self.adp_mv is not None:
            self.adp = np.zeros(n, dtype=np.float32)
            self.decay_adp = np.exp(-dt / _arr(p.tau_adp, n)).astype(np.float32)
            rec = _arr(p.adp_rec_ms, n)
            self.adp_h = np.ones(n, dtype=np.float32)
            self.adp_inact = rec > 0
            self.decay_h = np.exp(-dt / np.where(self.adp_inact, rec, 1.0)).astype(np.float32)
        self.kick_held = np.zeros(n, dtype=np.float32)
        self.elec = None   # (pre, post, kick_mv): identified electrical synapses
        # s13 (fly2): gap junctions as DC coupling plus spike steps through their own ring (no chemical delay)
        self.gap = None if p.gap is None else {k: np.array(v) for k, v in p.gap.items()}
        if self.gap is not None:
            self.gap_dc = bool(np.any(self.gap["c"] > 0))
            self.Dg = int(max(self.gap["d_a"].max(), self.gap["d_b"].max())) + 1
            self.gap_ring = np.zeros((self.Dg, n), dtype=np.float32)
            self.gap_head = 0
        self.x_res = np.ones(n, dtype=np.float32)
        self._any_adapt = bool(self.adapt_mv.any())
        self._any_std = bool(self.std_u.any())
        self._any_spont = bool(self.spont.any())
        # rung 8 (N29): per-edge resource x and release fraction u, updated lazily at
        # each presynaptic spike from the time since that cell's previous spike
        self.stp = None
        se = p.stp_edge
        if se is not None and len(se["idx"]):
            pos = np.full(self.conn.n_edges, -1, np.int64)
            pos[se["idx"]] = np.arange(len(se["idx"]))
            self.stp = {"pos": pos, "U": se["U"], "tau_rec": se["tau_rec"], "tau_f": se["tau_f"],
                        "x": np.ones(len(se["idx"])), "u": np.zeros(len(se["idx"])),
                        "t_last": np.full(n, -np.inf)}

        # graded cells: never spike; transmit a rate-equivalent every step
        self.g_idx = np.flatnonzero(self.graded)
        self.W_graded = None
        self.g_r0 = (None if p.graded_r0 is None or not np.any(p.graded_r0)
                     else np.asarray(p.graded_r0, np.float32)[self.g_idx])
        self.g_range = (None if p.graded_range is None
                        else np.asarray(p.graded_range, np.float32)[self.g_idx])
        self.g_k = (None if p.graded_k is None else np.asarray(p.graded_k, np.float32)[self.g_idx])
        if self.g_idx.size:
            rows = [np.arange(self.conn.indptr[i], self.conn.indptr[i + 1]) for i in self.g_idx]
            sel = np.concatenate(rows) if rows else np.zeros(0, np.int64)
            gpre = np.repeat(np.arange(self.g_idx.size), [len(r) for r in rows])
            self.W_graded = sp.csr_matrix(
                (self.w[sel], (gpre, self.conn.indices[sel])), shape=(self.g_idx.size, n)).T.tocsr()
            self.W_graded_i = None
            if p.cond:   # rung 2: graded inhibition is an inhibitory conductance, as spiking
                neg = self.W_graded.copy()
                neg.data = np.where(neg.data < 0, -neg.data, 0.0).astype(np.float32)
                neg.eliminate_zeros()
                self.W_graded.data = np.where(self.W_graded.data > 0, self.W_graded.data,
                                              0.0).astype(np.float32)
                self.W_graded.eliminate_zeros()
                self.W_graded_i = neg
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
        self._s10_ring_glia(pre)          # after W_graded exists (N23 edits it)
        self._two_comp_refusals()

    # --- one timestep --------------------------------------------------------

    def silence(self, idx: np.ndarray) -> None:
        """Remove all output of these neurons, as Shiu 2024 silences cells."""
        for i in np.asarray(idx):
            self.w[self.conn.indptr[i]:self.conn.indptr[i + 1]] = 0.0
            for c in self.chan:
                c["w"][self.conn.indptr[i]:self.conn.indptr[i + 1]] = 0.0
            if self.w_slow is not None:   # s10 fix: silencing also removes slow GABA-B output
                self.w_slow[self.conn.indptr[i]:self.conn.indptr[i + 1]] = 0.0
        if self.W_graded is not None:
            keep = ~np.isin(self.g_idx, idx)
            self.W_graded = (self.W_graded @ sp.diags(keep.astype(np.float32))).tocsr()
            if getattr(self, "W_graded_i", None) is not None:
                self.W_graded_i = (self.W_graded_i @ sp.diags(keep.astype(np.float32))).tocsr()
        if self.gap is not None:   # s13: a silenced cell neither steps nor couples its partners
            g = self.gap
            a_off, b_off = np.isin(g["a"], idx), np.isin(g["b"], idx)
            g["k_ab"][a_off] = 0.0
            g["k_ba"][b_off] = 0.0
            g["c"][a_off | b_off] = 0.0

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
            # elementwise, not a BLAS matvec: a threaded gemv per step oversubscribes CPUs (s8)
            gain = 1.0 + (self.mod_sens[:, 0] * self.mod_level[0] + self.mod_sens[:, 1] * self.mod_level[1]
                          + self.mod_sens[:, 2] * self.mod_level[2])
            arriving = arriving * gain
        self.i_syn = self.i_syn * self.decay_s + arriving
        self.delay[self.delay_head].fill(0.0)
        if p.cond:
            arr_i = self.delay_i[self.delay_head]
            if self._mod_active:
                arr_i = arr_i * gain
            self.g_i = self.g_i * self.decay_si + arr_i
            self.delay_i[self.delay_head].fill(0.0)
        c2 = self.c2
        if c2 is not None:   # N30 (s20): axon-compartment inputs due this step
            arr_a = c2["buf"][self.delay_head]
            if self._mod_active:
                arr_a = arr_a * gain[c2["cells"]]
            c2["i"] = c2["i"] * c2["decay_s"] + arr_a
            c2["buf"][self.delay_head].fill(0.0)

        drive = self.i_syn
        if self.w_slow is not None:
            h = self.delay_head % self.delay_slow.shape[0]
            self.i_slow = self.i_slow * self.decay_slow + self.delay_slow[h]
            self.delay_slow[h].fill(0.0)
            drive = drive + self.i_slow
        for c in self.chan:
            h = self.delay_head
            c["i"] = c["i"] * c["decay"] + c["buf"][h]
            c["buf"][h].fill(0.0)
            if c["vdep"]:
                blk = 1.0 / (1.0 + p.nmda_mg_mM / 3.57 * np.exp(-0.062 * self.v))
                drive = drive + c["i"] * blk.astype(np.float32)
            else:
                drive = drive + c["i"]
        if self.ring_e is not None:
            self.epg_trace *= self.ring_decay
            if int(round(self.t_ms / self.timestep_ms)) % 100 == 0:
                k = 1.0 - np.exp(-100 * self.timestep_ms / p.ring_recovery_tau_ms)
                self.w[self.ring_e] += ((self.ring_w0 - self.w[self.ring_e]) * k).astype(np.float32)
        if self.apl_mask is not None:
            self.kc_sub_rate *= self.apl_decay
            if int(round(self.t_ms / self.timestep_ms)) % 10 == 0:
                r = self.kc_sub_rate
                f = (1 - p.apl_local) + p.apl_local * (r / r.mean() if r.mean() > 0 else np.ones(3))
                self.W_graded.data[self.apl_mask] = (self.apl_base * f[self.apl_sub]).astype(np.float32)
        if self.glia_k is not None:
            self.glia_k *= self.glia_decay
            drive = drive + (p.glia_gain_mv * self.glia_k)[self.glia_idx]
        if self.w_pi is not None:
            self.p_inh *= self.decay_s
        if self.kc_edge is not None:
            self.dan_trace *= self.dan_decay
            self.kc_elig *= self.kc_elig_decay
            if p.kc_recovery_tau_ms > 0 and int(round(self.t_ms / self.timestep_ms)) % 100 == 0:
                k = 1.0 - np.exp(-100 * self.timestep_ms / p.kc_recovery_tau_ms)
                self.w[self.kc_e] += ((self.kc_w0 - self.w[self.kc_e]) * k).astype(np.float32)
        if external_mv is not None:
            drive = drive + external_mv
        if self._any_spont:
            drive = drive + self.spont
        if self._any_adapt:
            self.adapt *= self.decay_a
            drive = drive - self.adapt
        if self.adp_mv is not None:
            self.adp *= self.decay_adp
            self.adp_h = 1.0 - (1.0 - self.adp_h) * self.decay_h
            drive = drive + self.adp
        if self.gap is not None and self.gap_dc:
            # s13: junction current from the start-of-step potentials (explicit; c dt / tau_m << 1)
            g = self.gap
            dv = self.v[g["a"]] - self.v[g["b"]]
            i = np.where(dv > 0, g["c"], g["c"] * g["r"]) * dv
            drive = drive + (np.bincount(g["b"], i, n) - np.bincount(g["a"], i, n)).astype(np.float32)
        if c2 is not None:   # N30: soma-axon coupling and the axon update, both from start-of-step voltages
            cs = c2["cells"]
            vs0, va0 = self.v[cs], c2["v"]
            if drive is self.i_syn:
                drive = drive.copy()
            drive[cs] += c2["kap_s"] * (va0 - vs0)
            vinf = (self.v_leak[cs] + c2["i"] + c2["kap_a"] * vs0) / (1.0 + c2["kap_a"])
            c2["v"] = (vinf + (va0 - vinf) * c2["decay"]).astype(np.float32)

        if p.cond:
            g_e = self.i_syn
            G = 1.0 + g_e + self.g_i
            extra = drive - self.i_syn
            num = self.v_leak + extra + g_e * p.e_exc + self.g_i * p.e_inh
            if self.ich is not None:
                dG, dGE = self.ich.step(self.v)
                G, num = G + dG, num + dGE
            v_inf = num / G
            self.v = v_inf + (self.v - v_inf) * np.exp(-self.timestep_ms * G / self.tau_m)
        elif self.ich is not None:
            # rung 1: leak + intrinsic conductances (channels.py), exponential Euler
            dG, dGE = self.ich.step(self.v)
            G = 1.0 + dG
            v_inf = (self.v_leak + drive + dGE) / G
            self.v = (v_inf + (self.v - v_inf) * np.exp(-self.timestep_ms * G / self.tau_m)).astype(np.float32)
        else:
            # Exponential Euler: `drive` is the steady-state depolarisation
            self.v = self.v_leak + (self.v - self.v_leak) * self.decay_v + drive * (
                1.0 - self.decay_v)
        if p.noise_mv:
            self.v += self.rng.normal(0.0, p.noise_mv * np.sqrt(self.timestep_ms), n
                                      ).astype(np.float32)
        if p.noise_class_mv is not None:   # N3 class noise (s10); separate draw keeps m4 exact
            self.v += (self.rng.standard_normal(n).astype(np.float32)
                       * (p.noise_class_mv * np.float32(np.sqrt(self.timestep_ms))))

        free = self.t_ms >= self.ref_until
        self.v = np.where(free, self.v, self.v_reset)
        if kick is not None and len(kick[0]):
            self.kick_held[kick[0]] += kick[1]
        if self.gap is not None:   # s13: gap-junction spike steps due this step
            self.kick_held += self.gap_ring[self.gap_head]
            self.gap_ring[self.gap_head].fill(0.0)
        if self.kick_held.any():
            land = free & (self.kick_held > 0)
            self.v[land] += self.kick_held[land]
            self.kick_held[land] = 0.0
        can_spike = free & ~self.graded
        ax_sp = None
        if c2 is not None:   # N30: the listed cells spike only from the axon; their soma is never clamped
            can_spike &= ~c2["is_cell"]
            free_a = self.t_ms >= c2["ref_until"]
            c2["v"] = np.where(free_a, c2["v"], self.v_reset[cs])
            hit = free_a & (c2["v"] >= self.v_th[cs])
            if hit.any():
                ax_sp = cs[hit]
                c2["v"][hit] = self.v_reset[ax_sp]
                c2["ref_until"][hit] = self.t_ms + self.t_ref[ax_sp]
        spiked = np.flatnonzero(can_spike & (self.v >= self.v_th))

        # graded transmission: continuous, delayed by one step
        if self.W_graded is not None:
            g = self.g_idx
            r = (self.v[g] - self.v_rest[g]) / (
                self.v_th[g] - self.v_rest[g] if self.g_range is None else self.g_range)
            if self.g_r0 is not None:   # tonic release at rest; floor below rest
                r = self.g_r0 + (1.0 - self.g_r0) * r
            r = np.clip(r, 0.0, 1.0)
            if self.g_k is not None:
                r = r * self.g_k
            if r.any():
                self.delay[(self.delay_head + 1) % self.D] += (
                    self.W_graded @ (r * self.graded_scale)).astype(np.float32)
                if p.cond and self.W_graded_i is not None:
                    self.delay_i[(self.delay_head + 1) % self.D] += (
                        self.W_graded_i @ (r * self.graded_scale)).astype(np.float32)

        if self._any_std:
            self.x_res += (1.0 - self.x_res) * self.rec_step
        if self._mod_active:
            self.mod_level *= self.mod_decay
        if spiked.size:   # soma side: reset, refractory and spike-triggered processes
            self.v[spiked] = self.v_reset[spiked]
            if p.reset_syn:
                self.i_syn[spiked] = 0.0
                if p.cond:
                    self.g_i[spiked] = 0.0
            if self._any_adapt:
                self.adapt[spiked] += self.adapt_mv[spiked]
            if self.adp_mv is not None:
                a = self.adp[spiked]
                self.adp[spiked] = a + np.maximum(self.adp_mv[spiked] - a, 0.0) * self.adp_h[spiked]
                self.adp_h[spiked] = np.where(self.adp_inact[spiked], 0.0, 1.0)
            self.ref_until[spiked] = self.t_ms + self.t_ref[spiked]
            if self.ich is not None:
                self.ich.on_spike(spiked)
        if ax_sp is not None:   # N30: an axon spike is the cell's output spike; the soma does not see it
            spiked = np.union1d(spiked, ax_sp)
        if spiked.size:   # output side
            if self._mod_active:
                k = self.mod_release[spiked]
                k = k[k >= 0]
                if k.size:
                    self.mod_level += np.bincount(k, minlength=len(MODULATORS)) * p.mod_increment
            if self.elec is not None and len(self.elec[0]):
                hit = np.isin(self.elec[0], spiked)
                if hit.any():
                    np.add.at(self.kick_held, self.elec[1][hit], self.elec[2][hit])
            if self.gap is not None:
                g, h = self.gap, self.gap_head
                for src, dst, k, d in ((g["a"], g["b"], g["k_ab"], g["d_a"]),
                                       (g["b"], g["a"], g["k_ba"], g["d_b"])):
                    hit = np.isin(src, spiked) & (k != 0)
                    if hit.any():
                        np.add.at(self.gap_ring, ((h + d[hit]) % self.Dg, dst[hit]), k[hit])
            if self.ring_e is not None or self.glia_k is not None or self.apl_mask is not None:
                self._s10_spikes(spiked)
            if self.kc_edge is not None:
                ds = spiked[self.is_dan[spiked]]
                self.dan_trace[ds] += 1.0
                self.kc_elig[spiked[self.is_kc[spiked]]] += 1.0
                if ds.size and (p.kc_ltd_timing > 0 or p.kc_restore > 0):
                    # KC->MBON edges in the spiking DANs' compartments
                    comp = np.asarray(self.M_da[:, ds].sum(axis=1)).ravel() > 0
                    hit = comp[self.kc_post]
                    if hit.any():
                        e = self.kc_e[hit]
                        if p.kc_restore > 0:     # DA alone: restore toward baseline (s25)
                            self.w[e] += (p.kc_restore * (self.kc_w0[hit] - self.w[e])).astype(np.float32)
                        if p.kc_ltd_timing > 0:  # KC-before-DA: depress
                            self.w[e] *= np.clip(1.0 - p.kc_ltd_timing * self.kc_elig[self.kc_pre[hit]],
                                                 0.0, 1.0).astype(np.float32)
            self._propagate(spiked)
            self.spike_count += spiked.size

        self.delay_head = (self.delay_head + 1) % self.D
        if self.gap is not None:
            self.gap_head = (self.gap_head + 1) % self.Dg
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
        kc_on = p.kc_mbon_eta > 0 or p.kc_ltd_timing > 0 or p.kc_ltp_timing > 0 or p.kc_restore > 0
        if not (np.any(gs != 0) or np.any(f > 0) or p.presyn_inh_gain > 0 or kc_on):
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
            self.w_slow = self._charge_basis(ws, post, p.gabab_tau_ms)
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
        if kc_on:
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
            # s10 N21/N22 state: baseline weights, KC eligibility, edge index lists
            self.kc_e = np.flatnonzero(self.kc_edge)
            self.kc_w0 = self.w[self.kc_e].copy()
            self.kc_pre, self.kc_post = pre[self.kc_e], post[self.kc_e]
            self.kc_elig = np.zeros(n, dtype=np.float32)
            self.kc_elig_decay = np.float32(np.exp(-dt / p.kc_elig_tau_ms))
            self.is_kc = kc

    def w0_of(self, e: np.ndarray) -> np.ndarray:
        """Baseline weight of KC->MBON edges `e` (global edge indices)."""
        return self.kc_w0[np.searchsorted(self.kc_e, e)]

    def _s10_ring_glia(self, pre: np.ndarray) -> None:
        """N24 ER->EPG plasticity and N27 lumped glia (s10); inert at defaults."""
        p, n, dt = self.params, self.conn.n, self.timestep_ms
        self.ring_e = None
        self.glia_k = None
        if p.ring_eta > 0:
            t = self.conn.neurons.type.fillna("")
            er = t.str.match(r"^ER\d").to_numpy()
            epg = t.isin(["EPG", "EPGt"]).to_numpy()
            post = self.conn.indices
            self.ring_e = np.flatnonzero(er[pre] & epg[post] & (self.w != 0))
            self.ring_pre, self.ring_post = pre[self.ring_e], post[self.ring_e]
            self.ring_w0 = self.w[self.ring_e].copy()
            self.is_er, self.is_epg = er, epg
            self.epg_trace = np.zeros(n, np.float32)
            self.ring_decay = np.float32(np.exp(-dt / p.ring_trace_tau_ms))
        self.apl_mask = None
        if p.apl_local > 0 and p.cond:
            raise NotImplementedError("N23 compartmental APL with conductance synapses (APL "
                                      "inhibition sits in W_graded_i, which N23 does not edit)")
        if p.apl_local > 0 and self.W_graded is not None:
            t = self.conn.neurons.type.fillna("")
            apl_cols = np.flatnonzero(t.to_numpy()[self.g_idx] == "APL")
            kc = (self.conn.neurons["class"].fillna("") == "Kenyon_Cell").to_numpy()
            sub = t.str.extract(r"^(KCab|KCg|KCa'b')")[0].fillna("")
            names = ["KCab", "KCg", "KCa'b'"]
            self.kc_sub = np.array([names.index(x) if x in names else -1 for x in sub])
            W = self.W_graded
            rows = np.repeat(np.arange(W.shape[0]), np.diff(W.indptr))
            m = np.isin(W.indices, apl_cols) & kc[rows] & (self.kc_sub[rows] >= 0)
            self.apl_mask = np.flatnonzero(m)
            self.apl_base = W.data[self.apl_mask].copy()
            self.apl_sub = self.kc_sub[rows[self.apl_mask]]
            self.kc_sub_n = np.maximum(np.bincount(self.kc_sub[self.kc_sub >= 0], minlength=3), 1)
            self.kc_sub_rate = np.zeros(3)
            self.apl_decay = float(np.exp(-dt / p.apl_local_tau_ms))
        if p.glia_gain_mv > 0:
            from pathlib import Path   # noqa: F401
            cls = circuit_classes(self.conn)
            _, self.glia_idx = np.unique(cls, return_inverse=True)
            self.glia_n = np.bincount(self.glia_idx).astype(np.float32)
            self.glia_k = np.zeros(len(self.glia_n), np.float32)
            self.glia_decay = np.float32(np.exp(-dt / p.glia_tau_ms))

    def _s10_spikes(self, spiked: np.ndarray) -> None:
        p = self.params
        if self.ring_e is not None:
            self.epg_trace[spiked[self.is_epg[spiked]]] += 1.0
            s_er = spiked[self.is_er[spiked]]
            if s_er.size:
                hit = np.isin(self.ring_pre, s_er)
                if hit.any():
                    e = self.ring_e[hit]
                    f = np.clip(1.0 - p.ring_eta * self.epg_trace[self.ring_post[hit]], p.ring_floor, 1.0)
                    self.w[e] = np.where(np.abs(self.w[e] * f) >= p.ring_floor * np.abs(self.ring_w0[hit]),
                                         self.w[e] * f, p.ring_floor * self.ring_w0[hit]).astype(np.float32)
        if self.apl_mask is not None:
            k = self.kc_sub[spiked]
            self.kc_sub_rate += np.bincount(k[k >= 0], minlength=3) / self.kc_sub_n
        if self.glia_k is not None:
            self.glia_k += np.bincount(self.glia_idx[spiked], minlength=len(self.glia_k)) / self.glia_n

    def _charge_basis(self, ws: np.ndarray, post: np.ndarray, tau_slow: float) -> np.ndarray:
        """Rung 2 repair 1: with slow_share_basis on, the slow pool carries the moved
        fast charge (peak x tau_s / tau_slow) rather than the moved fast peak."""
        if not self.params.slow_share_basis:
            return ws
        k = _arr(self.params.tau_s, self.conn.n)[post] / np.float32(tau_slow)
        return (ws * k).astype(np.float32)

    def _slow_channels(self, pre: np.ndarray) -> None:
        """N7/N8 (s10): mGluR, mAChR and NMDA-type components. Each moves a
        fraction (per postsynaptic cell) of a transmitter's spiking edges' fast
        weight to its own slow current; NMDA is scaled by the Mg block
        B(V) = 1 / (1 + [Mg]/3.57 exp(-0.062 V)). None active = bit-identical."""
        p, n, dt = self.params, self.conn.n, self.timestep_ms
        post = self.conn.indices
        self.chan = []
        spec = [("mglur", p.mglur_fraction, p.mglur_tau_ms, "glutamate", False),
                ("machr", p.machr_fraction, p.machr_tau_ms, "acetylcholine", False),
                ("nmda", p.nmda_fraction, p.nmda_tau_ms, "glutamate", True)]
        if not any(np.any(_arr(f, n) > 0) for _, f, *_ in spec):
            return
        nt = self.conn.neurons.get("predictedNt", pd.Series([""] * n)).fillna("").str.lower().to_numpy()
        for name, f, tau, trans, vdep in spec:
            f = _arr(f, n)
            if not np.any(f > 0):
                continue
            m = (nt[pre] == trans) & ~self.graded[pre]
            if vdep:
                m &= self.w > 0
            ws = np.where(m, self.w * f[post], 0.0).astype(np.float32)
            self.w = (self.w - ws).astype(np.float32)
            ws = self._charge_basis(ws, post, tau)
            self.chan.append(dict(name=name, w=ws, buf=np.zeros((self.D, n), np.float32),
                                  i=np.zeros(n, np.float32), vdep=vdep,
                                  decay=np.float32(np.exp(-dt / tau))))

    def _kinetic_channels(self, pre: np.ndarray) -> None:
        """N29 (s13, fly2): the fast weight of each receptor_kinetics.csv edge moves to a current
        with the row's decay, one current per distinct decay. The charge per spike is kept
        (w (1 - e^(-dt/tau_row)) / (1 - e^(-dt/tau_s,post))), so only the time course changes and
        the shared efficacy keeps its meaning (the peak basis tripled cholinergic charge in the
        slow-share ablation, DECISIONS 2026-10-01 01:06). Spiking presynaptic cells only; graded
        cells transmit through W_graded at tau_s. Current-based synapses only."""
        ke = self.params.kin_edge
        if ke is None or not len(ke["idx"]):
            return
        if self.params.cond:
            raise NotImplementedError("synapse:all|receptor_kinetics_per_connection with conductance "
                                      "synapses is not built (s13)")
        dt, n, post = self.timestep_ms, self.conn.n, self.conn.indices
        keep = ~self.graded[pre[ke["idx"]]]
        idx, tau = ke["idx"][keep], ke["tau"][keep]
        decay_s = np.exp(-dt / _arr(self.params.tau_s, n))
        for t in np.unique(tau):
            e = idx[tau == t]
            dc = np.float32(np.exp(-dt / t))
            ws = np.zeros_like(self.w)
            ws[e] = self.w[e] * (1.0 - dc) / (1.0 - decay_s[post[e]])
            self.w[e] = 0.0
            self.chan.append(dict(name=f"kin{t:g}", w=ws, buf=np.zeros((self.D, n), np.float32),
                                  i=np.zeros(n, np.float32), vdep=False, decay=dc, kin=True))

    def _flyvis_pair_weights(self, pre: np.ndarray) -> None:
        """s14 (fly2): give each flyvis pair edge from a graded cell the weight whose steady-state voltage
        gain (post mV per pre mV, on the linear part of release) is flyvis's alpha x synapse count. Our
        graded release adds w g_k (1 - r0) / range x rmax dt per step per mV, held at tau_s, so
        w = alpha n range (1 - e^(-dt/tau_s,post)) / (g_k (1 - r0) rmax dt). Our sign is kept. Validity:
        presynaptic voltage between rest and the end of its release range (flyvis' relu has no ceiling);
        spiking presynaptic cells keep the shared scale (no voltage-gain reading); release and input
        gains are replaced on these edges. Conductance synapses convert this weight like any other, so
        the gain holds at the reference voltage with no other conductance open; tonic conductance shunts
        it (scripts/vision/flyvis_pair_check.py reports the in-network gain)."""
        fe = self.params.fv_edge
        if fe is None or not len(fe["idx"]):
            return
        p, n, dt = self.params, self.conn.n, self.timestep_ms
        keep = self.graded[pre[fe["idx"]]]
        idx, j = fe["idx"][keep], pre[fe["idx"][keep]]
        post = self.conn.indices[idx]
        rng = (self.v_th - self.v_rest if p.graded_range is None else _arr(p.graded_range, n))[j]
        r0 = np.zeros(idx.size) if p.graded_r0 is None else _arr(p.graded_r0, n, np.float64)[j]
        gk = np.ones(idx.size) if p.graded_k is None else _arr(p.graded_k, n, np.float64)[j]
        ds = np.exp(-dt / _arr(p.tau_s, n, np.float64)[post])
        gain = fe["alpha"][keep] * self.conn.weight_syn[idx]
        self.w[idx] = (np.sign(self.conn.sign[j]) * gain * rng * (1.0 - ds)
                       / (gk * (1.0 - r0) * p.graded_rmax_hz * dt / 1000.0)).astype(np.float32)
        self.fv_spiking_pre = int((~keep).sum())   # flyvis pairs left at the shared scale

    def _two_comp_init(self, pre: np.ndarray) -> None:
        """N30 first build (s20, fly2; DECISIONS 20 Oct 23:30): axon compartments for the cells of
        params.two_comp. The soma is the existing cell (every other input, its channels, noise and gap
        junctions). The axon has the cell's tau_m, leak potential, threshold, reset and refractory, no
        channels or noise of its own, takes the listed edges, and is where the cell's spikes start.
        Coupling both ways from start-of-step voltages: soma drive += kappa_s (Va - Vs), and the axon
        relaxes toward (V_leak + Ia + kappa_a Vs) / (1 + kappa_a) by exponential Euler, with
        kappa_s = rho / (1 - q) and kappa_a = rho / q. An axon spike is the cell's output spike
        (propagation, gap-junction steps, modulator release). The soma is neither reset nor clamped, and
        its spike-triggered processes (adaptation, ADP, channel Ca) do not see the spike, which reaches
        the soma "small and broad" (Fayyazuddin 2006). An axon edge keeps its synaptic charge: its weight
        is divided by q, since the axon's leak is q of the cell's (unitary_psp.csv rows then reset it).
        Validity: one isopotential axon segment and a uniform membrane; the soma's other inputs act on
        (1 - q) of the membrane, so their DC effect is (1 - q) / ((1 - q) + q rho / (q + rho)) of the
        point cell's (0.93 at the class values)."""
        tc = self.params.two_comp
        self.c2 = None
        if tc is None or not len(tc["cells"]):
            return
        if self.params.cond:
            raise NotImplementedError("N30 two compartments with conductance synapses are not built (s20)")
        cells = np.asarray(tc["cells"], np.int64)
        ax = np.zeros(self.conn.n_edges, bool)
        ax[tc["edge_idx"]] = True
        if self.graded[cells].any() or self.graded[pre[ax]].any():
            raise NotImplementedError("N30: graded listed cells or graded axon inputs are not built (s20)")
        pos = np.full(self.conn.n, -1, np.int64)
        pos[cells] = np.arange(cells.size)
        q, rho = np.asarray(tc["q"], np.float64), np.asarray(tc["rho"], np.float64)
        ka = rho / q
        self.w[ax] = (self.w[ax] / q[pos[self.conn.indices[ax]]]).astype(np.float32)
        self.c2 = {"cells": cells, "pos": pos, "ax_edge": ax, "is_cell": pos >= 0,
                   "kap_a": ka.astype(np.float32), "kap_s": (rho / (1.0 - q)).astype(np.float32),
                   "decay": np.exp(-self.timestep_ms * (1.0 + ka) / self.tau_m[cells]).astype(np.float32),
                   "v": self.v_rest[cells].copy(), "i": np.zeros(cells.size, np.float32),
                   "buf": np.zeros((self.D, cells.size), np.float32),
                   "ref_until": np.zeros(cells.size, np.float32)}

    def _two_comp_refusals(self) -> None:
        """N30: refuse what the axon compartment does not carry: a receptor-channel or slow copy on an
        axon edge, or an inhibitory axon edge with its own decay (tau_s_inh)."""
        c2 = self.c2
        if c2 is None:
            return
        e = np.flatnonzero(c2["ax_edge"])
        if (any(np.any(c["w"][e] != 0) for c in self.chan)
                or (self.w_slow is not None and np.any(self.w_slow[e] != 0))):
            raise NotImplementedError("N30: an axon edge with a receptor-channel or slow copy is not built (s20)")
        post = self.conn.indices[e]
        if np.any((self.w[e] < 0) & (self.decay_si[post] != self.decay_s[post])):
            raise NotImplementedError("N30: an inhibitory axon edge with its own decay is not built (s20)")
        c2["decay_s"] = self.decay_s[c2["cells"]]

    def psp_peak_per_mv_axon(self, cells: np.ndarray) -> np.ndarray:
        """N30: soma PSP peak (mV) per mV of synaptic weight arriving on the axon of listed `cells`, in
        the coupled pair's discrete update (as step; axon passive, no threshold)."""
        c2, dt = self.c2, self.timestep_ms
        j = c2["pos"][cells]
        ds = np.exp(-dt / _arr(self.params.tau_s, self.conn.n, np.float64)[cells])
        tau = _arr(self.params.tau_m, self.conn.n, np.float64)[cells]
        ka, ks = c2["kap_a"][j].astype(np.float64), c2["kap_s"][j].astype(np.float64)
        dv, da = np.exp(-dt / tau), np.exp(-dt * (1.0 + ka) / tau)
        i, va, vs, peak = np.ones_like(ds), np.zeros_like(ds), np.zeros_like(ds), np.zeros_like(ds)
        for _ in range(int(np.ceil(200.0 / dt))):
            vinf = (i + ka * vs) / (1.0 + ka)
            va, vs = vinf + (va - vinf) * da, vs * dv + ks * (va - vs) * (1.0 - dv)
            peak = np.maximum(peak, vs)
            i = i * ds
        return peak

    def _unitary_psp_weights(self) -> None:
        """s14 (fly2): set each unitary_psp.csv edge to the weight whose PSP peak in the passive
        membrane (this cell's tau_m and tau_s, this timestep and update order) equals the recorded
        peak. N30 (s20): an edge onto an axon compartment gets the weight whose SOMA peak in the coupled
        pair equals it (where the recording was made). Validity: the cell's intrinsic channels, a slow
        receptor share or an N29 decay on the edge change the peak (the probe reports the in-network
        value); current-based synapses only."""
        pe = self.params.psp_edge
        if pe is None or not len(pe["idx"]):
            return
        if self.params.cond:
            raise NotImplementedError("connectome:identified|unitary_psp_from_recordings with "
                                      "conductance synapses is not built (s14)")
        ke = self.params.kin_edge
        if ke is not None and np.intersect1d(ke["idx"], pe["idx"]).size:
            raise NotImplementedError("a unitary_psp.csv edge also has an N29 decay row (not built)")
        post = self.conn.indices[pe["idx"]]
        per = self.psp_peak_per_mv(post)
        if self.c2 is not None:
            on_ax = self.c2["ax_edge"][pe["idx"]]
            if on_ax.any():
                per[on_ax] = self.psp_peak_per_mv_axon(post[on_ax])
        self.w[pe["idx"]] = (pe["psp_mv"] / per).astype(np.float32)

    def psp_peak_per_mv(self, cells: np.ndarray) -> np.ndarray:
        """Passive PSP peak (mV) per mV of synaptic weight arriving at `cells`, in this model's
        discrete update (I <- I e^(-dt/tau_s) + w, then V relaxes toward I with e^(-dt/tau_m))."""
        dt = self.timestep_ms
        ds = np.exp(-dt / _arr(self.params.tau_s, self.conn.n, np.float64)[cells])
        dv = np.exp(-dt / _arr(self.params.tau_m, self.conn.n, np.float64)[cells])
        i, v, peak = np.ones_like(ds), np.zeros_like(ds), np.zeros_like(ds)
        for _ in range(int(np.ceil(200.0 / dt))):
            v = v * dv + i * (1.0 - dv)
            peak = np.maximum(peak, v)
            i = i * ds
        return peak

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
                if self.params.kc_mbon_eta > 0:
                    self.w[e] *= np.clip(1.0 - self.params.kc_mbon_eta * da[indices[e]], 0.0, 1.0)
                if self.params.kc_ltp_timing > 0:   # DA-before-KC: potentiate toward the cap
                    w0 = self.w0_of(e)
                    k = np.clip(self.params.kc_ltp_timing * da[indices[e]], 0.0, 1.0)
                    self.w[e] += (k * (self.params.kc_w_cap * w0 - self.w[e])).astype(np.float32)
        fac = facc = None    # amplitude factor on w, and on the slow/channel copies
        if self._any_std:
            fac = np.repeat(self.x_res[spiked], counts)
            self.x_res[spiked] *= (1.0 - self.std_u[spiked])
            if self.chan or self.w_slow is not None:
                facc = np.repeat(self.x_res[spiked] / np.maximum(1.0 - self.std_u[spiked], 1e-6),
                                 counts)
        if self.stp is not None:
            fac, facc = self._stp_factor(spiked, counts, sel, fac, facc)
        if fac is not None:
            w = w * fac
        # The head slot was consumed and zeroed earlier in this step; a slot
        # (head + d) % D is read d steps from now, so each presynaptic cell's
        # contribution arrives after exactly its own delay.
        slot = np.repeat((self.delay_head + self.delay_steps[spiked]) % self.D, counts)
        tgt = indices[sel]
        if self.c2 is not None:   # N30: edges onto an axon compartment go to its own buffer
            ax = self.c2["ax_edge"][sel]
            if ax.any():
                np.add.at(self.c2["buf"], (slot[ax], self.c2["pos"][tgt[ax]]), w[ax])
                w = np.where(ax, np.float32(0.0), w)   # channel and slow copies are refused on these edges
        if self.params.cond:
            ex = w > 0
            np.add.at(self.delay, (slot[ex], tgt[ex]), w[ex])
            np.add.at(self.delay_i, (slot[~ex], tgt[~ex]), -w[~ex])
        else:
            np.add.at(self.delay, (slot, tgt), w)
        for c in self.chan:
            wc = c["w"][sel]
            if facc is not None:
                wc = wc * facc
            np.add.at(c["buf"], (slot, tgt), wc)
        if self.w_slow is not None:
            ws = self.w_slow[sel]
            if facc is not None:
                ws = ws * facc
            np.add.at(self.delay_slow, (slot % self.delay_slow.shape[0], tgt), ws)

    def _stp_factor(self, spiked, counts, sel, fac, facc):
        """Rung 8 (N29): Tsodyks-Markram factor u+ x / U on the table's edges (Markram 1998
        form: between spikes x recovers toward 1 with tau_rec and u decays toward 0 with
        tau_facil; at a spike u+ = u + U (1 - u), release u+ x, x -= u+ x). At rest the factor
        is 1, so w keeps its meaning; with tau_facil = 0 it equals the per-cell depression
        rule with this edge's U. Edges without a row keep the per-cell factor."""
        s = self.stp
        k = s["pos"][sel]
        cov = k >= 0
        if not cov.any():
            return fac, facc
        kk = k[cov]
        d = self.t_ms - np.repeat(s["t_last"][spiked], counts)[cov]   # inf at a first spike
        x = 1.0 - (1.0 - s["x"][kk]) * np.exp(-d / s["tau_rec"][kk])
        tf = s["tau_f"][kk]
        um = np.where(tf > 0, s["u"][kk] * np.exp(-d / np.where(tf > 0, tf, 1.0)), 0.0)
        U = s["U"][kk]
        up = um + U * (1.0 - um)
        f = (up * x / U).astype(np.float32)
        s["x"][kk] = x - up * x
        s["u"][kk] = up
        s["t_last"][spiked] = self.t_ms
        total = len(sel)
        fac = np.ones(total, np.float32) if fac is None else fac.astype(np.float32, copy=True)
        facc = np.ones(total, np.float32) if facc is None else facc.astype(np.float32, copy=True)
        fac[cov] = f
        facc[cov] = f
        return fac, facc

    # --- readout -------------------------------------------------------------

    def rates_hz(self, spike_counts: np.ndarray, window_ms: float) -> np.ndarray:
        return spike_counts / (window_ms / 1000.0)
