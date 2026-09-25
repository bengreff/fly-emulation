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

import numpy as np
import pandas as pd

from .registry import Registry

# (presynaptic type, postsynaptic type, evidence)
GF_PAIRS = [
    ("DNp01", "TTMn", "GF-TTMn mixed synapse, shakB-dependent; 1:1 following "
                      "(Tanouye & Wyman 1980; Phelan et al. 1996)"),
    ("DNp01", "PSI", "GF-PSI electrical synapse, shakB-dependent "
                     "(Phelan et al. 1996; Allen et al. 2006)"),
]


def build(reg: Registry, conn, pairs=GF_PAIRS) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
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
