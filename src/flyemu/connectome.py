"""Structure: the male-cns:v1.0 graph as a signed, weighted, sparse network.

Structure is per neuron, which is what the connectome gives. Physiology is per
cell type. Two things are read straight out of the dataset and are `measured` or
`derived`:

  - who connects to whom, and with how many synapses
  - each neuron's identity, region, cell type and predicted transmitter

Everything that turns that into a dynamical system is not in the dataset:

  - the SIGN of a glutamatergic connection is a postsynaptic receptor property
    and the connectome has no receptor identity (F-SIGN-1). Unresolved.
  - the EFFICACY of one anatomical synapse in millivolts. Unresolved.
  - conduction DELAY per connection. Unresolved.

Those pass through the registry so they cannot be mistaken for data.
"""
from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

import numpy as np
import pandas as pd

from .registry import Policy, Registry, Status

CACHE = Path(__file__).resolve().parents[2] / "data" / "cache"
DATASET = "male-cns:v1.0"

# Sign by predicted transmitter. Only the first two are settled for the fly.
SIGN_BY_NT: dict[str, float | None] = {
    "acetylcholine": +1.0,   # excitatory, nicotinic; standard
    "gaba": -1.0,            # inhibitory; standard
    "glutamate": None,       # receptor-dependent: GluCl inhibits, others excite
    "histamine": -1.0,       # photoreceptor transmitter, inhibitory via HisCl
    "dopamine": None,        # modulatory; not a fast sign in M v1
    "serotonin": None,
    "octopamine": None,
    "unclear": None,
}


@dataclass
class Connectome:
    """Neurons, edges, and the signed weight matrix in CSR form."""

    neurons: pd.DataFrame
    indptr: np.ndarray        # CSR over presynaptic neuron index
    indices: np.ndarray       # postsynaptic neuron index
    weight_syn: np.ndarray    # anatomical synapse count per edge (measured)
    sign: np.ndarray          # per-presynaptic-neuron sign, +1/-1/0
    efficacy_mv: np.ndarray   # per-edge PSP amplitude, mV (assumed)
    # Efficacy factored as psp_mv * post_gain[post]: every postsynaptic-side
    # adjustment lives in post_gain, so a rewired control recomputes it for
    # the NEW target instead of carrying the old target's factor.
    psp_mv: float = 0.0
    post_gain: np.ndarray | None = None

    @property
    def n(self) -> int:
        return len(self.neurons)

    @property
    def n_edges(self) -> int:
        return len(self.indices)

    def index_of(self, body_ids: np.ndarray) -> np.ndarray:
        """Map dataset bodyIds to model row indices; -1 where absent."""
        lut = pd.Series(np.arange(self.n), index=self.neurons.bodyId.values)
        return lut.reindex(body_ids).fillna(-1).astype(np.int64).to_numpy()


@lru_cache(maxsize=1)
def load_tables() -> tuple[pd.DataFrame, pd.DataFrame]:
    neurons = pd.read_parquet(CACHE / "male_cns_neurons.parquet")
    edges = pd.read_parquet(CACHE / "male_cns_edges.parquet")
    return neurons, edges


def build(
    reg: Registry,
    *,
    neurons: pd.DataFrame | None = None,
    edges: pd.DataFrame | None = None,
    min_synapses: int = 1,
    statuses: tuple[str, ...] | None = ("Traced",),
    keep_typed: bool = True,
) -> Connectome:
    """Assemble the network. Records every non-anatomical quantity it needs.

    `statuses` filters :Neuron nodes by proofreading status; None keeps all.
    `keep_typed` also keeps any body with a cell-type label whatever its
    status. The default is therefore 165,122 `Traced` bodies plus 1,989 typed
    ones, 1,983 of them R1-R6 photoreceptors with no status set. The 9,311
    dropped are untyped fragments - median 23 presynapses against 145 for
    traced neurons - and simulating each as a whole neuron with its own
    threshold would be wrong (F-COUNT-2).
    """
    if neurons is None or edges is None:
        neurons, edges = load_tables()
    n_all = len(neurons)
    if statuses is not None:
        keep = neurons.status.isin(statuses)
        if keep_typed:
            keep |= neurons.type.notna()
        neurons = neurons[keep]

    # --- inclusion policy, stated rather than assumed ------------------------
    reg.provide(
        "graph:male-cns",
        "inclusion_policy",
        (f"status in {list(statuses)}"
         + (" or typed" if keep_typed else "") if statuses is not None
         else "all :Neuron nodes")
        + f" ({len(neurons):,} of {n_all:,}); edges with weight >= "
          f"{min_synapses} between included nodes",
        units="dimensionless",
        model_use="which neurons and connections exist in the model at all",
        status=Status.DERIVED,
        evidence=f"{DATASET}, neuPrint; :Neuron is itself a threshold-based "
                 "inclusion decision by the dataset authors",
        subsystem="identity",
        instances=len(neurons),
        uncertainty="node counts are policy-dependent; see F-DATA-2",
    )

    neurons = neurons.reset_index(drop=True).copy()
    pos = pd.Series(np.arange(len(neurons)), index=neurons.bodyId.values)

    e = edges[edges.weight >= min_synapses]
    pre = pos.reindex(e.pre.values).to_numpy()
    post = pos.reindex(e.post.values).to_numpy()
    keep = ~(np.isnan(pre) | np.isnan(post))
    pre, post = pre[keep].astype(np.int64), post[keep].astype(np.int64)
    w = e.weight.to_numpy()[keep].astype(np.float32)

    order = np.argsort(pre, kind="stable")
    pre, post, w = pre[order], post[order], w[order]
    indptr = np.zeros(len(neurons) + 1, dtype=np.int64)
    np.cumsum(np.bincount(pre, minlength=len(neurons)), out=indptr[1:])

    reg.provide(
        "graph:male-cns",
        "chemical_connectivity",
        w.sum(),
        units="synapses",
        model_use="synaptic weight matrix W",
        status=Status.MEASURED,
        evidence=f"{DATASET} ConnectsTo weights, {len(w):,} edges",
        subsystem="connectivity",
        instances=len(w),
        uncertainty="anatomical contact count is not functional efficacy",
    )
    reg.provide(
        "graph:male-cns",
        "electrical_coupling",
        None,
        units="nS",
        model_use="omitted from M v1",
        status=Status.UNRESOLVED,
        evidence="these releases provide no comparable electrical "
                 "reconstruction; unknown coupling is not measured absence",
        subsystem="electrical",
        instances=len(neurons),
    )

    # --- sign, per transmitter class ----------------------------------------
    nt = neurons.predictedNt.fillna("unclear").str.lower().to_numpy()
    sign = np.zeros(len(neurons), dtype=np.float32)
    for name, s in SIGN_BY_NT.items():
        m = nt == name
        if not m.any():
            continue
        if s is not None:
            sign[m] = reg.provide(
                f"transmitter:{name}",
                "sign",
                s,
                units="dimensionless",
                model_use="sign of the synaptic weight",
                status=Status.DERIVED,
                evidence="standard fly pharmacology for this transmitter class",
                subsystem="sign",
                instances=int(m.sum()),
            )
        else:
            sign[m] = reg.require(
                f"transmitter:{name}",
                "sign",
                units="dimensionless",
                model_use="sign of the synaptic weight",
                subsystem="sign",
                instances=int(m.sum()),
                minimal=-1.0 if name == "glutamate" else 0.0,
                conventional=-1.0 if name == "glutamate" else 0.0,
                minimal_note="glutamate taken inhibitory, as the published "
                             "precedents do; a receptor property the "
                             "connectome cannot settle (F-SIGN-1)",
                conventional_note="uniform inhibitory glutamate, as in "
                                  "Pugliese/Shiu-style models (F-SIGN-1)",
                uncertainty="sign is set by postsynaptic receptor, not "
                            "transmitter; leverage demonstrated in F-SIGN-1",
                shared_with=("transmitter:glutamate|sign",),
            )

    # --- AL local neurons with unclear transmitter (m2, ii) ------------------
    alln = neurons["class"].fillna("").eq("ALLN").to_numpy()
    al_unclear = alln & (nt == "unclear")
    al_sign = reg.require(
        "transmitter:unclear_in_AL_local_neurons", "sign",
        units="dimensionless", model_use="sign of AL LNs with unclear NT",
        subsystem="sign", instances=int(al_unclear.sum()),
        minimal=float(sign[al_unclear][0]) if al_unclear.any() else 0.0,
        conventional=float(sign[al_unclear][0]) if al_unclear.any() else 0.0,
        minimal_note="declared default: whatever 'unclear' gets globally",
        uncertainty="AL LNs are predominantly GABAergic/glutamatergic "
                    "(Chou et al. 2010; Das et al. 2011); per-cell unknown",
    )
    sign[al_unclear] = al_sign

    # --- efficacy: one number standing in for every synapse in the animal ----
    psp = reg.require(
        "connection_class:all",
        "efficacy_per_synapse",
        units="mV",
        model_use="synaptic current injected per presynaptic spike",
        subsystem="synaptic_efficacy",
        instances=len(w),
        minimal=0.1,
        conventional=0.1,
        minimal_note="declared default: one anatomical synapse is worth "
                     "0.1 mV of postsynaptic depolarisation",
        uncertainty="a single shared scalar propagated to every edge in the "
                    "model; this is one inference, not 25 million",
    )
    post_gain = np.ones(len(neurons), dtype=np.float32)

    # --- synapses onto sensory axon terminals --------------------------------
    sensory = neurons.superclass.fillna("").str.contains("sensory").to_numpy()
    onto = sensory[post]
    keep_onto = reg.require(
        "connection_class:onto_sensory_terminals", "included",
        units="boolean",
        model_use="whether central synapses onto sensory neurons drive them",
        subsystem="synaptic_efficacy", instances=int(onto.sum()),
        minimal=1.0, conventional=1.0,
        minimal_note="declared default: treated like any other synapse",
        uncertainty="sensory spikes start in the periphery; input onto "
                    "their central terminals is presynaptic modulation, "
                    "which a single compartment cannot represent. 0 drops "
                    "these edges' effect (F-SENS-1)",
    )
    if not keep_onto:
        post_gain[sensory] = 0.0

    # --- input resistance falling with cell size ------------------------------
    alpha = reg.require(
        "cell_type:all", "size_scaling_exponent",
        units="dimensionless",
        model_use="efficacy onto a neuron x (median size / its size)^alpha",
        subsystem="neuron_biophysics", instances=len(neurons),
        minimal=0.0, conventional=0.0,
        minimal_note="declared default: no size dependence",
        uncertainty="volume as an input-resistance proxy, following "
                    "Pugliese 2025; alpha=1 is their choice, not a measurement",
    )
    if alpha:
        size = neurons["size"].to_numpy(dtype=np.float64)
        med = np.nanmedian(size)
        factor = np.where(np.isfinite(size) & (size > 0), (med / size) ** alpha, 1.0)
        post_gain *= factor.astype(np.float32)
    beta = reg.require(
        "cell_type:all", "input_normalisation_exponent",
        units="dimensionless",
        model_use="efficacy onto a neuron x (median input count / its input count)^beta",
        subsystem="synaptic_efficacy", instances=len(neurons),
        minimal=0.0, conventional=0.0,
        minimal_note="declared default: no input normalisation",
        uncertainty="homeostatic-scaling hypothesis; beta assumed",
    )
    if beta:
        n_in = np.bincount(post, weights=w, minlength=len(neurons))
        med_in = np.median(n_in[n_in > 0])
        post_gain *= np.where(n_in > 0, (med_in / np.maximum(n_in, 1)) ** beta, 1.0).astype(np.float32)
    efficacy = (psp * post_gain[post]).astype(np.float32)

    # --- VNC sensorimotor efficacy (session 6) --------------------------------
    sc = neurons.superclass.fillna("").to_numpy()
    vnc_sm = (np.isin(sc[pre], ["vnc_sensory", "vnc_intrinsic"])
              & np.isin(sc[post], ["vnc_intrinsic", "vnc_motor"]))
    vnc_scale = reg.require(
        "connection_class:vnc_sensorimotor", "efficacy_scale",
        units="dimensionless",
        model_use="multiplies efficacy of VNC sensory/intrinsic -> VNC intrinsic/motor edges",
        subsystem="synaptic_efficacy", instances=int(vnc_sm.sum()),
        minimal=1.0, conventional=1.0,
        minimal_note="neutral default: the brain-calibrated efficacy applies in the VNC too",
        uncertainty="the single efficacy was calibrated on brain stability (rule v2); VNC "
                    "reflex transmission is unconstrained by it (F-STAND-1)",
    )
    if vnc_scale != 1.0:
        efficacy[vnc_sm] *= np.float32(vnc_scale)

    # --- cholinergic AL LN chemical output onto PNs / each other (m2, i) -----
    ach_ln = alln & (nt == "acetylcholine")
    pn = neurons["class"].fillna("").eq("ALPN").to_numpy()
    eln_mask = ach_ln[pre] & (pn[post] | ach_ln[post])
    keep_eln = reg.require(
        "connection_class:cholinergic_AL_LN_to_PN_and_eLN", "included",
        units="boolean", model_use="chemical efficacy of these edges",
        subsystem="synaptic_efficacy", instances=int(eln_mask.sum()),
        minimal=1.0, conventional=1.0,
        minimal_note="declared default: chemical excitation as for any ACh synapse",
        uncertainty="eLN->PN transmission is electrical, unaffected by chemical "
                    "block, abolished by shakB (Yaksi & Wilson 2010); eLN->eLN "
                    "unmeasured (F-LN-1)",
    )
    if not keep_eln:
        efficacy[eln_mask] = 0.0

    return Connectome(
        neurons=neurons, indptr=indptr, indices=post.astype(np.int32),
        weight_syn=w, sign=sign, efficacy_mv=efficacy,
        psp_mv=float(psp), post_gain=post_gain,
    )


def _with_targets(conn: Connectome, indices: np.ndarray) -> Connectome:
    if conn.post_gain is not None:
        eff = (conn.psp_mv * conn.post_gain[indices]).astype(np.float32)
    else:
        eff = conn.efficacy_mv
    return Connectome(
        neurons=conn.neurons, indptr=conn.indptr, indices=indices,
        weight_syn=conn.weight_syn, sign=conn.sign, efficacy_mv=eff,
        psp_mv=conn.psp_mv, post_gain=conn.post_gain,
    )


def shuffled(conn: Connectome, rng: np.random.Generator) -> Connectome:
    """Global rewiring control.

    Permutes the postsynaptic end of every edge across the whole graph, then
    recomputes postsynaptic-side efficacy for the new targets. Kept: each
    neuron's out-degree, outgoing synapse counts and sign, and its in-degree.
    Not kept: per-neuron input synapse totals and E/I input balance; self-
    loops and multi-edges can appear. Destroys locality, reciprocity and
    type structure, so failing it shows only that SOME wiring structure matters.
    """
    return _with_targets(conn, rng.permutation(conn.indices))


def type_shuffled(conn: Connectome, rng: np.random.Generator) -> Connectome:
    """Cell-type block-preserving null.

    Within every (presynaptic type, postsynaptic type) block, permutes which
    postsynaptic neuron each edge lands on. Kept exactly: type-to-type edge
    counts and synapse counts, every neuron's out-degree and outgoing synapse
    counts, every neuron's in-degree within each block. Destroyed: which
    individual neuron of a type connects to which. Untyped neurons are their
    own type, so their edges do not move. Passing it means the result needs
    only type-level wiring.
    """
    t = conn.neurons.type.fillna("").to_numpy()
    uid = np.where(t == "", "#" + conn.neurons.bodyId.astype(str).to_numpy(), t)
    codes = pd.factorize(uid)[0].astype(np.int64)
    pre = np.repeat(np.arange(conn.n), np.diff(conn.indptr))
    post = conn.indices.astype(np.int64)
    block = codes[pre] * (codes.max() + 1) + codes[post]
    # Both orderings group edges by block; the second is random within each
    # block, so pairing them position-by-position permutes within blocks.
    order = np.argsort(block, kind="stable")
    perm = np.lexsort((rng.random(len(block)), block))
    new = post.copy()
    new[order] = post[perm]
    return _with_targets(conn, new.astype(conn.indices.dtype))
