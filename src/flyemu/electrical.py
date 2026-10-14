"""Identified electrical synapses, as spike-triggered rectifying kicks.

The releases contain no electrical reconstruction (connectome.py registers
electrical coupling as unresolved). A few gap junctions are established by
physiology and genetics; they are added here by identity, one pair at a
time, each with its evidence. A LIF neuron has no action potential waveform
for a gap junction to carry, so transmission is modelled as a membrane kick
of `k` mV on the partner when the presynaptic cell spikes (rectifying, no
subthreshold coupling). All strengths are assumed.
"""
from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

from .registry import Registry, Status

GAP_TABLE = Path(__file__).resolve().parents[2] / "data" / "params" / "gap_junctions.csv"
T_SYN_MS = 0.5   # the chemical share of every conduction_delays.csv row (0.5 ms + L/v; inferred)
_BASIS = {"measured": Status.MEASURED, "derived": Status.DERIVED, "inferred": Status.INFERRED,
          "guessed": Status.GUESSED}

# (presynaptic type, postsynaptic type, evidence)
GF_PAIRS = [
    ("DNp01", "TTMn", "GF-TTMn mixed synapse, shakB-dependent; 1:1 following "
                      "(Tanouye & Wyman 1980; Phelan et al. 1996)"),
    ("DNp01", "PSI", "GF-PSI electrical synapse, shakB-dependent "
                     "(Phelan et al. 1996; Allen et al. 2006)"),
]


# s10 N12 curated sites beyond the GF (strength 0 = absent, as for the GF pairs in m4).
# Partner types from male-cns wiring (largest contacts); electrical evidence cited per pair.
CURATED_PAIRS = [
    ("JO-B1_a", "DNp01", "JO-B afferents -> giant fibre mixed synapses, shakB-dependent "
                         "(Pezier et al. 2014 J Neurosci; Lehnert et al. 2013; leads, not read); "
                         "JO-B1_a is DNp01's largest JO input (541 synapses, male-cns)"),
    ("JO-B1_c", "DNp01", "as JO-B1_a (138 synapses)"),
    ("VS", "VS", "neighbouring VS lobula plate tangential cells are electrically coupled "
                 "(Haag & Borst 2004 Nat Neurosci; Cuntz et al. 2003; leads, not read)"),
    ("SNpp25", "b1 MN", "haltere campaniform afferents -> b1 steering MN electrical synapse "
                        "(Fayyazuddin & Dickinson 1996, Calliphora; lead); SNpp25 is a haltere "
                        "campaniform type (sensory census) with 191 synapses onto b1 MN"),
    ("SNpp34", "b1 MN", "as SNpp25 (haltere campaniform, 185 synapses onto b1 MN)"),
]


def build(reg: Registry, conn, pairs=GF_PAIRS + CURATED_PAIRS) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Return (pre_idx, post_idx, kick_mv) for identified electrical pairs.

    Each presynaptic cell couples to the postsynaptic cell of the given type
    with which it has the most chemical contacts (a proxy for apposition).
    """
    nrn = conn.neurons
    t = nrn.type.fillna("").to_numpy()
    pre_all = np.repeat(np.arange(conn.n), np.diff(conn.indptr))
    out_pre, out_post, out_k = [], [], []
    for a, b, ev in pairs:
        k = reg.require(
            f"electrical:{a}->{b}", "spike_coupling", units="mV",
            model_use="membrane kick on the partner per presynaptic spike",
            subsystem="electrical", instances=int((t == a).sum()),
            minimal=0.0, conventional=0.0,
            minimal_note="declared default: absent, as in M v1",
            uncertainty=ev + "; strength assumed (coupling x spike height)",
        )
        if not k:
            continue
        for i in np.flatnonzero(t == a):
            sel = (pre_all == i) & (t[conn.indices] == b)
            if not sel.any():
                continue
            posts = pd.Series(conn.weight_syn[sel]).groupby(conn.indices[sel]).sum()
            out_pre.append(i); out_post.append(int(posts.idxmax())); out_k.append(k)
    return (np.array(out_pre, np.int64), np.array(out_post, np.int64),
            np.array(out_k, np.float32))


# --- s13 (fly2, brief task 2): gap junctions as a conductance, from data/params/gap_junctions.csv ---

def _cells(conn, spec: str) -> np.ndarray:
    """Cell mask for a table entry: exact type, ^regex on type, or class:NAME[@transmitter]."""
    nrn = conn.neurons
    if spec.startswith("class:"):
        cls, _, nt = spec[len("class:"):].partition("@")
        m = nrn["class"].fillna("").eq(cls).to_numpy()
        if nt:
            m = m & nrn.predictedNt.fillna("").str.lower().eq(nt).to_numpy()
        return m
    t = nrn.type.fillna("").astype(str)
    return (t.str.contains(spec, regex=True) if spec.startswith("^") else t.eq(spec)).to_numpy()


def _pairs(conn, am: np.ndarray, bm: np.ndarray, rule: str) -> tuple[np.ndarray, np.ndarray]:
    """Cell pairs (a, b) for one table entry; see the partners column of gap_junctions.csv."""
    nrn = conn.neurons
    if rule in ("same_type", "same_side"):
        key = nrn.somaSide.fillna("?").astype(str)
        if rule == "same_type":
            key = nrn.type.fillna("").astype(str) + "|" + key
        key = key.to_numpy()
        a, b = [], []
        for i in np.flatnonzero(am):
            j = np.flatnonzero(bm & (key == key[i]))
            j = j[j > i] if am[j].all() else j[j != i]   # within one set: each pair once
            a += [i] * len(j)
            b += list(j)
        return np.array(a, np.int64), np.array(b, np.int64)
    if rule not in ("max_contacts", "contacts"):
        return np.zeros(0, np.int64), np.zeros(0, np.int64)
    pre = np.repeat(np.arange(conn.n), np.diff(conn.indptr))
    post = conn.indices.astype(np.int64)
    fwd, rev = am[pre] & bm[post], bm[pre] & am[post]
    e = pd.DataFrame({"a": np.r_[pre[fwd], post[rev]], "b": np.r_[post[fwd], pre[rev]],
                      "n": np.r_[conn.weight_syn[fwd], conn.weight_syn[rev]]})
    e = e[e.a != e.b].groupby(["a", "b"]).n.sum().reset_index()
    if rule == "max_contacts":
        e = e.loc[e.groupby("a").n.idxmax()]
    else:
        e = e.assign(a=np.minimum(e.a, e.b), b=np.maximum(e.a, e.b)).drop_duplicates(["a", "b"])
    return e.a.to_numpy(np.int64), e.b.to_numpy(np.int64)


def build_gap(reg: Registry, conn, tau_m, v_rest, v_th, delay_ms, timestep_ms: float) -> dict | None:
    """Identified gap junctions as a conductance plus a spike step, or None when the switch is off.

    Subthreshold: each pair passes c (V_a - V_b) into b and the opposite into a (leak units, both cells'
    leak conductance taken equal), with c scaled by the rectification when b is the more depolarised.
    Spikes: a LIF spike has no waveform for the junction to carry, so a spike of a steps b by k_ab mV
    after a's axonal conduction time (no chemical delay), and a spike of b steps a by rectification x k_ab.
    Validity: point cells, so the junction sees the somatic potential; junction site and dendritic
    filtering are not represented, which is why spike and DC coupling are separate columns.
    """
    if not reg.require(
            "electrical:all", "gap_conductance", units="boolean",
            model_use="identified gap junctions from data/params/gap_junctions.csv (conductance + spike step)",
            subsystem="electrical", minimal=0.0, conventional=0.0,
            minimal_note="neutral 0 (s13): no gap junctions; the kicks of electrical.build stay as they are"):
        return None
    tab = pd.read_csv(GAP_TABLE, comment="#", dtype=str).fillna("")
    safety = float(reg.require(
        "electrical:one_to_one", "safety_factor", units="dimensionless",
        model_use="spike step = safety x partner threshold distance for one_to_one junctions",
        subsystem="electrical", minimal=2.0, conventional=2.0,
        minimal_note="guessed: the margin by which a 1:1 junction exceeds threshold; unmeasured",
        uncertainty="partial ShakB loss (Rab11 RNAi) already lengthens GF-TTM latency by 0.7 ms "
                    "(Augustin et al. 2017), so the margin is finite"))
    area = float(reg.require(
        "electrical:all", "spike_area", units="mV ms",
        model_use="spike step from DC coupling: coupling x area / tau_m of the partner",
        subsystem="electrical", minimal=50.0, conventional=50.0,
        minimal_note="guessed: an axonal spike of about 70 mV and 0.7 ms effective width"))
    tau_m, v_rest, v_th, delay_ms = (np.broadcast_to(np.asarray(x, np.float64), (conn.n,))
                                     for x in (tau_m, v_rest, v_th, delay_ms))
    d = np.maximum(1, np.round((delay_ms - T_SYN_MS) / timestep_ms)).astype(np.int64)
    cols = {k: [] for k in ("a", "b", "c", "r", "k")}
    for row in tab.itertuples(index=False):
        a, b = _pairs(conn, _cells(conn, row.pre), _cells(conn, row.post), row.partners)
        ent = f"electrical:{row.pre}->{row.post}"
        note = f"{row.evidence}; {row.source}; {row.justification}"
        c = float(row.coupling) if row.coupling else 0.0
        r = float(row.rectification) if row.rectification else 1.0
        if row.coupling:
            reg.provide(ent, "gap_coupling", c, units="junction / partner leak conductance",
                        model_use="DC coupling, both directions (rectification on the reverse)",
                        status=_BASIS[row.coupling_basis], evidence=note, subsystem="electrical",
                        instances=len(a))
        else:
            reg.provide(ent, "gap_coupling", None, units="junction / partner leak conductance",
                        model_use="not simulated: magnitude unmeasured", status=Status.UNRESOLVED,
                        evidence=note, subsystem="electrical", instances=len(a))
        if row.spike == "one_to_one":
            k = safety * (v_th[b] - v_rest[b])
        elif row.spike == "from_coupling":
            k = c * area / tau_m[b]
        else:
            k = np.full(len(b), float(row.spike) if row.spike else 0.0)
        if row.spike:
            reg.provide(ent, "gap_spike", row.spike, units="mV per presynaptic spike (or rule)",
                        model_use="step on the partner after the presynaptic conduction time",
                        status=_BASIS[row.spike_basis], evidence=note, subsystem="electrical",
                        instances=len(a))
        if len(a) and (c > 0 or np.any(k > 0)):
            cols["a"].append(a)
            cols["b"].append(b)
            cols["k"].append(np.asarray(k, np.float64))
            cols["c"].append(np.full(len(a), c))
            cols["r"].append(np.full(len(a), r))
    if not cols["a"]:
        return None
    a, b = np.concatenate(cols["a"]), np.concatenate(cols["b"])
    r, k = np.concatenate(cols["r"]), np.concatenate(cols["k"])
    return {"a": a, "b": b, "c": np.concatenate(cols["c"]).astype(np.float32), "r": r.astype(np.float32),
            "k_ab": k.astype(np.float32), "k_ba": (r * k).astype(np.float32), "d_a": d[a], "d_b": d[b]}
