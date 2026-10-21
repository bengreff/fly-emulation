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


CT1_RAW = CACHE.parent / "raw" / "ct1_columns_s14"
CT1_LAYER = {"ME": "M10", "LO": "Lo1"}


def ct1_compartments(reg: Registry, neurons: pd.DataFrame, e: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    """s14 (fly2): each CT1 as independent graded compartments, one per (cell, neuropil, column).

    CT1's terminals respond as independent units (Meier & Borst 2019 Curr Biol 29:1545, calcium imaging;
    abstract only here) and flyvis models them as per-column types CT1(M10) and CT1(Lo1) (Lappalainen et
    al. 2024). Each CT1 connection kept at the cell-level threshold is split over the optic-lobe column ROIs
    its synapses lie in (male-cns ConnectsTo roiInfo, Nern et al. 2025 hex grid; raw pull
    data/raw/ct1_columns_s14 by scripts/vision/fetch_ct1_columns.py): ME columns -> an M10 compartment,
    LO columns -> an Lo1 compartment. Synapses outside ME/LO column ROIs (about 2%) stay on the original
    node, kept as the trunk. A compartment copies its CT1 row (type, transmitter, per-type parameters),
    gets a synthetic negative bodyId, instance <cell instance>/<M10|Lo1>/<column ROI>, and a size scaled by
    its share of the cell's kept synapses (derived). Compartments are not coupled to each other or to the
    trunk. Validity: no spread between neighbouring terminals or between M10 and Lo1; a compartment edge
    can hold fewer synapses than the threshold (the connection passed it). CT1 -> CT1 connections stay on
    the trunks.
    """
    import json
    ct1 = neurons.type.eq("CT1").to_numpy()
    if not reg.require(
            "cell_type:CT1", "compartments_by_column", units="boolean",
            model_use="CT1 as one independent graded compartment per (cell, M10/Lo1, column), edges split "
                      "by the column ROIs of their synapses",
            subsystem="connectivity", instances=int(ct1.sum()), minimal=0.0, conventional=0.0,
            minimal_note="neutral 0: each CT1 is one point cell",
            uncertainty="terminal independence from calcium imaging (Meier & Borst 2019, abstract); "
                        "no coupling between compartments") or not ct1.any():
        return neurons, e
    raw = pd.concat([pd.read_parquet(CT1_RAW / f"ct1_{d}.parquet") for d in ("out", "in")])
    info = raw.drop_duplicates(["pre", "post"]).set_index(["pre", "post"]).roiInfo
    cells = neurons.loc[ct1].set_index("bodyId")
    ids = set(cells.index)
    touch = e.pre.isin(ids) | e.post.isin(ids)
    both = e.pre.isin(ids) & e.post.isin(ids)
    rows, missing = [], 0
    for r in e[touch & ~both].itertuples(index=False):
        cell = r.pre if r.pre in ids else r.post
        if (r.pre, r.post) not in info.index:
            missing += 1
            rows.append((r.pre, r.post, r.weight, None))
            continue
        left = int(r.weight)
        for k, v in json.loads(info[(r.pre, r.post)]).items():
            npl, c = k.split("_", 1)[0], int(v.get("post", 0))
            if "_col_" in k and npl in CT1_LAYER and c:
                rows.append((r.pre, r.post, c, (cell, CT1_LAYER[npl], k)))
                left -= c
        if left < 0:
            raise ValueError(f"CT1 column counts exceed the cached weight on {r.pre}->{r.post}")
        if left:
            rows.append((r.pre, r.post, left, None))
    sp = pd.DataFrame(rows, columns=["pre", "post", "weight", "comp"])
    keys = sorted({k for k in sp.comp if k is not None})
    sid = {k: -(i + 1) for i, k in enumerate(keys)}            # synthetic, not neuPrint bodies
    c = sp.comp.map(lambda k: sid.get(k, 0) if k is not None else 0).to_numpy()
    out = (sp.pre.isin(ids) & (c != 0)).to_numpy()
    sp["pre"] = np.where(out, c, sp.pre)
    sp["post"] = np.where(~out & (c != 0), c, sp.post)
    syn = (sp.groupby("pre").weight.sum().add(sp.groupby("post").weight.sum(), fill_value=0)
           .add(e[both].groupby("pre").weight.sum(), fill_value=0).add(e[both].groupby("post").weight.sum(),
                                                                       fill_value=0))
    total = {b: sum(syn.get(sid[k], 0) for k in keys if k[0] == b) + syn.get(b, 0) for b in ids}
    new = []
    for k in keys:
        row = cells.loc[k[0]].copy()
        row["instance"] = f"{row['instance']}/{k[1]}/{k[2]}"
        row["ct1_compartment"], row["compartment_of"] = k[1], k[0]
        row["size"] = row["size"] * syn.get(sid[k], 0) / total[k[0]]
        new.append(row.rename(sid[k]))
    neurons = neurons.copy()
    neurons["ct1_compartment"] = np.where(ct1, "trunk", "")
    neurons["compartment_of"] = np.where(ct1, neurons.bodyId, 0)
    neurons.loc[ct1, "size"] = [s * syn.get(b, 0) / total[b] for b, s in zip(neurons.bodyId[ct1], neurons["size"][ct1])]
    comp = pd.DataFrame(new).rename_axis("bodyId").reset_index().infer_objects()
    neurons = pd.concat([neurons, comp[neurons.columns]], ignore_index=True)
    e = pd.concat([e[~touch | both], sp[["pre", "post", "weight"]]], ignore_index=True)
    n_out = int(sp.weight[sp.comp.isna()].sum())
    reg.provide("cell_type:CT1", "column_compartments", len(keys), units="compartments",
                model_use="independent CT1 compartments (M10 and Lo1 terminals per column)",
                status=Status.DERIVED, evidence=f"{DATASET} ConnectsTo roiInfo column ROIs (Nern et al. 2025 hex "
                "grid); data/raw/ct1_columns_s14 (scripts/vision/fetch_ct1_columns.py)",
                subsystem="connectivity", instances=len(keys),
                uncertainty=f"{n_out} of {int(sp.weight.sum())} split synapses outside ME/LO column ROIs stay on "
                            f"the trunks; {missing} connections absent from the raw pull stay whole; "
                            f"{int(both.sum())} CT1->CT1 connections stay on the trunks")
    return neurons, e


T1_FILL = CACHE.parent / "params" / "t1_fill.csv.gz"


def _side(s) -> str:
    s = str(s).strip().upper()
    return "L" if s.startswith("L") else "R" if s.startswith("R") else "?"


def t1_fill(reg: Registry, neurons: pd.DataFrame, e: pd.DataFrame) -> pd.DataFrame:
    """s20 (fly2, T1F; DECISIONS 20 Oct 22:02): fill the male-CNS prothoracic input deficit from MANC and BANC.

    The male-CNS T1 neuromere has 0.58 of MANC's per-cell matched input (T2 0.69, T3 0.82; BANC sits with MANC;
    F-XCONN-1, read as a reconstruction undercount, inferred). Per (presynaptic type A, T1 post type B, post side)
    the table holds factor = median(male CNS, MANC, BANC) / male CNS of the synapses per B cell from type A, where
    the male CNS is below that median and MANC has the pair (scripts/connectome/t1_fill_table.py, sources pinned
    in t1_fill.json). Each kept edge from an A cell onto a T1 B cell on that side is multiplied by its factor.
    Validity: T1 post cells only; no edge is added or removed (edges below the synapse cut stay out even where the
    filled count would cross it), no sign changes; assumes per-cell input by type is conserved across animals.
    """
    nm = neurons.somaNeuromere if "somaNeuromere" in neurons else pd.Series("", index=neurons.index)
    t1 = nm.astype(str).eq("T1") & neurons.type.notna()
    if not reg.require(
            "connectome:T1", "fill_from_other_animals", units="boolean",
            model_use="scale male-CNS edges onto T1 cells toward the cross-animal median (MANC, BANC) by "
                      "presynaptic type, post type and side; never adds a partner",
            subsystem="connectivity", instances=int(t1.sum()), minimal=0.0, conventional=0.0,
            minimal_note="neutral 0: male-CNS counts as reconstructed",
            uncertainty="the T1 deficit is read as reconstruction (F-XCONN-1, inferred); pair counts vary "
                        "between animals; the fill-only rule raises T1 above the median of totals") \
            or not T1_FILL.exists() or not t1.any():
        return e
    f = pd.read_csv(T1_FILL, comment="#").set_index(["pre_type", "post_type", "post_side"]).factor
    ty = neurons.set_index("bodyId").type
    post = neurons[t1].set_index("bodyId")
    on = e.post.isin(post.index).to_numpy()
    k = pd.MultiIndex.from_arrays([e.pre[on].map(ty).to_numpy(), e.post[on].map(post.type).to_numpy(),
                                   e.post[on].map(post.somaSide.map(_side)).to_numpy()])
    fac = f.reindex(k).fillna(1.0).to_numpy()
    w = e.weight.to_numpy(dtype=np.float32, copy=True)
    before = float(w[on].sum())
    w[on] *= fac.astype(np.float32)
    e = e.assign(weight=w)
    reg.provide("connectome:T1", "fill_factor", float(np.median(fac[fac > 1])) if (fac > 1).any() else 1.0,
                units="dimensionless", model_use="median factor over the filled edges onto T1 cells",
                status=Status.INFERRED, evidence="cross-animal median of synapses per post cell by type: male-cns "
                "v1.0, MANC (Pugliese_cpg_2025 W_20260522), BANC (W_20260217 T1 premotor extract); "
                "data/params/t1_fill.csv.gz", subsystem="connectivity", instances=int((fac > 1).sum()),
                uncertainty=f"{int((fac > 1).sum())} of {int(on.sum())} kept edges onto T1 cells scaled; T1 "
                            f"synapses {before:.0f} -> {float(w[on].sum()):.0f}")
    return e


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

    # --- transmitter source (session 8) ---------------------------------------
    # predictedNt is the per-neuron EM classifier call; consensusNt is the
    # dataset's curated call. They disagree on ~20k neurons, e.g. every Kenyon
    # cell is predictedNt "dopamine" but consensusNt "acetylcholine" (Davis 2020
    # transcripts: ChAT+, no ple), and ~3.3k "unclear" cells are GABA or glutamate.
    if reg.require(
            "connectome:all", "nt_source_consensus", units="boolean",
            model_use="which transmitter call sets synaptic sign and modulator release",
            subsystem="sign", instances=len(neurons), minimal=0.0, conventional=0.0,
            minimal_note="0: EM classifier predictedNt (sessions 1-7); 1: male-cns consensusNt",
            uncertainty="consensusNt disagrees with predictedNt on 20,169 neurons; "
                        "transcripts (69 types) agree with consensus for KCs") and (
            CACHE / "male_cns_extra.parquet").exists():
        extra = pd.read_parquet(CACHE / "male_cns_extra.parquet", columns=["bodyId", "consensusNt"])
        cons = neurons.bodyId.map(extra.set_index("bodyId").consensusNt)
        neurons["predictedNt_em"] = neurons.predictedNt
        neurons["predictedNt"] = cons.where(cons.notna(), neurons.predictedNt)
        # session 11: fast transmitter of consensus-"unclear" cells from development
        # (hemilineage majority, leave-one-type-out accuracy 0.989 at purity >= 0.9;
        # VNC motor neurons glutamate by class): scripts/infer_nt_hemilineage.py
        fill_path = CACHE.parent / "derived" / "nt_hemilineage_fill.csv"
        if reg.require(
                "connectome:unclear", "nt_by_development", units="boolean",
                model_use="fast transmitter of unclear cells from hemilineage / motor class",
                subsystem="sign", instances=int(neurons.predictedNt.eq("unclear").sum()),
                minimal=0.0, conventional=0.0,
                minimal_note="neutral 0: unclear cells keep sign 0 (they transmit nothing)",
                uncertainty="hemilineage rule (Lacin 2019, VNC; lead for the brain) tested "
                            "leave-one-type-out on male-cns; per-cell calls are inferred") \
                and fill_path.exists():
            f = pd.read_csv(fill_path).set_index("bodyId").nt
            new = neurons.bodyId.map(f)
            m = new.notna() & neurons.predictedNt.fillna("unclear").eq("unclear")
            neurons.loc[m, "predictedNt"] = new[m]
    # s13 (fly2, F-GJ-3): identified types whose transmitter is known from physiology or pharmacology
    # (data/params/transmitter_physiology.csv); the row wins over the EM and development calls
    tp = CACHE.parent / "params" / "transmitter_physiology.csv"
    if reg.require(
            "connectome:identified", "nt_from_physiology", units="boolean",
            model_use="fast transmitter of identified types from physiology (per-type table with sources)",
            subsystem="sign", instances=len(neurons), minimal=0.0, conventional=0.0,
            minimal_note="neutral 0: transmitter from the EM classifier / consensus / development calls",
            uncertainty="one row per identified type; each row cites the recording or pharmacology") \
            and tp.exists():
        for r in pd.read_csv(tp, comment="#").itertuples():
            m = neurons.type.eq(r.type)
            reg.provide(f"cell_type:{r.type}", "transmitter", r.nt, units="category",
                        model_use="fast transmitter (sets the synaptic sign)", status=Status(r.basis),
                        evidence=r.source, subsystem="sign", instances=int(m.sum()), uncertainty=r.note)
            neurons.loc[m, "predictedNt"] = r.nt
    e = edges[edges.weight >= min_synapses]
    neurons, e = ct1_compartments(reg, neurons, e)   # s14 (fly2); unchanged at neutral
    e = t1_fill(reg, neurons, e)                     # s20 (fly2, T1F); unchanged at neutral
    pos = pd.Series(np.arange(len(neurons)), index=neurons.bodyId.values)
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

    # --- inhibitory AL LN -> PN postsynaptic share (session 6c) ---------------
    inh_ln = alln & np.isin(nt, ["gaba", "glutamate", "unclear"])   # m2: unclear AL LNs inhibitory
    pn_all = neurons["class"].fillna("").eq("ALPN").to_numpy()
    ln_pn = inh_ln[pre] & pn_all[post]
    ln_pn_scale = reg.require(
        "connection_class:inhibitory_AL_LN_to_PN", "postsynaptic_scale",
        units="dimensionless", model_use="efficacy multiplier of GABA/Glu AL LN -> PN edges",
        subsystem="synaptic_efficacy", instances=int(ln_pn.sum()),
        minimal=1.0, conventional=1.0,
        minimal_note="neutral default: all LN inhibition of PNs acts postsynaptically",
        uncertainty="much LN inhibition is presynaptic on ORN terminals (Olsen & Wilson 2008); "
                    "the split is unmeasured per LN type (F-AL-2)",
    )
    if ln_pn_scale != 1.0:
        efficacy[ln_pn] *= np.float32(ln_pn_scale)

    # --- ORN -> uniglomerular PN transmission (session 7) ---------------------
    # uPN as in scripts/probes/pn_silence.py: class ALPN, type ending "PN".
    ctype = neurons.type.fillna("").to_numpy().astype(str)
    upn = pn_all & np.char.endswith(ctype, "PN")
    orn_upn = np.char.startswith(ctype, "ORN_")[pre] & upn[post]
    orn_scale = reg.require(
        "connection_class:ORN_to_uPN", "efficacy_scale",
        units="dimensionless", model_use="efficacy multiplier of ORN -> uPN edges",
        subsystem="synaptic_efficacy", instances=int(orn_upn.sum()),
        minimal=1.0, conventional=1.0,
        minimal_note="neutral default: the brain-calibrated efficacy applies",
        uncertainty="measured unitary EPSP 6.19 +/- 0.45 mV (Kazama & Wilson 2008, n=23) "
                    "implies ~10.9 at the median 22-synapse connection (session 7)",
    )
    matching = reg.require(
        "connection_class:ORN_to_uPN", "homeostatic_matching",
        units="boolean", model_use="normalise each uPN's ORN edges so its median "
                                   "ORN connection has the same unitary EPSP",
        subsystem="synaptic_efficacy", instances=int(upn.sum()),
        minimal=0.0, conventional=0.0,
        minimal_note="off: unitary EPSP proportional to synapse count",
        uncertainty="uEPSP similar across glomeruli despite different uEPSCs "
                    "(Kazama & Wilson 2008 Fig 4); mechanism is PN input resistance",
    )
    if orn_scale != 1.0 or matching:
        f = np.full(len(w), orn_scale, dtype=np.float64)
        if matching:
            idx = np.flatnonzero(orn_upn)
            s = pd.Series(w[idx].astype(np.float64)).groupby(post[idx]).median()
            ref = float(np.median(w[idx]))
            f[idx] *= ref / s.reindex(post[idx]).to_numpy()
        efficacy[orn_upn] = (efficacy[orn_upn] * f[orn_upn]).astype(np.float32)

    # --- leg proprioceptor output: transferred first-order synapse (session 7) --
    leg_types = leg_proprioceptor_types()
    leg_out = np.isin(ctype, leg_types)[pre]
    leg_scale = reg.require(
        "connection_class:leg_proprioceptor_output", "efficacy_scale",
        units="dimensionless", model_use="efficacy multiplier of all output edges of "
                                         "driven leg proprioceptor types",
        subsystem="synaptic_efficacy", instances=int(leg_out.sum()),
        minimal=1.0, conventional=1.0,
        minimal_note="neutral default: the brain-calibrated efficacy applies",
        uncertainty="no adult leg-afferent unitary PSP found; 10.9 transfers the measured "
                    "ORN->PN first-order synapse (session 7, inferred)",
    )
    if leg_scale != 1.0:
        efficacy[leg_out] *= np.float32(leg_scale)

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


def leg_proprioceptor_types() -> list[str]:
    """Leg proprioceptor types the sensory model drives (non-empty subtype)."""
    t = pd.read_csv(Path(__file__).resolve().parents[2] / "data" / "params" / "proprio_assignment.csv",
                    comment="#")
    return sorted(t[t.subtype.fillna("") != "" ].type.astype(str))


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
