"""The core -> leg-MN hand-off in the model (s14, diagnostic; no simulation, no fitting).

For each oscillator-core cell (E1, E2, I1, IN19A007/004/002; roles as bypass_s3_chain) and each leg MN it contacts
(leg MNs as bypass_s2_descending: those in a Hill pool or coxa group), list the anatomical synapse count, the model
weight on that edge, and the MN's threshold gap (v_th - v_rest). The single-spike PSP is derived as synapses x the
model's measured mV per synapse at scale 1 (s4b_unitary_psp, median 0.0212 mV, q10-q90 0.0094-0.0349;
runs/s13/bypass/s4b/psp/unitary_psp.json). Reported: how many core spikes, arriving together, a target MN needs to
reach threshold from rest (gap / PSP), linear summation assumed, so it is a lower bound.

    uv run python scripts/probes/s14_handoff.py --out runs/s14/handoff.json
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "src"))
sys.path.insert(0, str(Path(__file__).resolve().parent))
from flyemu.organism import Organism  # noqa: E402
from bypass_s2_descending import VNC_SUPER  # noqa: E402,F401
from bypass_s3_chain import ROLE  # noqa: E402

MV_PER_SYN = (0.0212, 0.0094, 0.0349)   # median, q10, q90 (model, scale 1; derived in s13 S4b)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--profile", default="m10f0")
    ap.add_argument("--out", default=str(REPO / "runs" / "s14" / "handoff.json"))
    a = ap.parse_args()
    org = Organism(policy="minimal", profile=a.profile, min_synapses=5, seed=12, with_camera=False)
    conn, net, h, nm = org.conn, org.net, org.hill, org.nm
    n = conn.neurons
    typ = n.type.fillna("").to_numpy().astype(str)
    seg = (n["somaNeuromere"].fillna("") if "somaNeuromere" in n else n.get("soma_neuromere", "")).astype(str).to_numpy()
    side = n["somaSide"].fillna("").astype(str).to_numpy()
    in_pool = np.asarray(h.mn_muscle) >= 0
    if h.coxa is not None:
        in_pool |= np.asarray(h.mn_group) >= 0
    legmn = np.asarray(nm.mn_index)[in_pool]
    is_leg = np.zeros(conn.n, bool); is_leg[legmn] = True
    gap = np.asarray(net.v_th) - np.asarray(net.v_rest)
    rows = []
    for i in np.flatnonzero(np.isin(typ, list(ROLE))):
        for e in range(conn.indptr[i], conn.indptr[i + 1]):
            j = conn.indices[e]
            if not is_leg[j]:
                continue
            syn = float(conn.weight_syn[e])
            psp = syn * MV_PER_SYN[0]
            rows.append(dict(role=ROLE[typ[i]], pre_seg=f"{seg[i]}{side[i]}", post_type=typ[j], post_seg=f"{seg[j]}{side[j]}",
                             synapses=syn, w=round(float(net.w[e]), 4), sign=int(conn.sign[i]), gap_mv=round(float(gap[j]), 2),
                             psp_mv=round(psp, 3), spikes_to_threshold=round(float(gap[j]) / psp, 1) if psp > 0 else None))
    summ = {}
    for r in sorted({x["role"] for x in rows}):
        rr = [x for x in rows if x["role"] == r]
        s = np.array([x["synapses"] for x in rr]); k = np.array([x["spikes_to_threshold"] for x in rr])
        summ[r] = dict(edges=len(rr), mns=len({(x["post_type"], x["post_seg"]) for x in rr}), sign=rr[0]["sign"],
                       syn_median=float(np.median(s)), syn_max=float(s.max()),
                       psp_mv_median=round(float(np.median(s)) * MV_PER_SYN[0], 3), psp_mv_max=round(float(s.max()) * MV_PER_SYN[0], 3),
                       spikes_to_threshold_min=float(k.min()), spikes_to_threshold_median=float(np.median(k)),
                       gap_mv_median=float(np.median([x["gap_mv"] for x in rr])))
    for r, s in summ.items():
        print(r, s)
    out = Path(a.out); out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(dict(profile=a.profile, mv_per_syn=MV_PER_SYN, summary=summ, rows=rows), indent=1))
    print(out)


if __name__ == "__main__":
    main()
