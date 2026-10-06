"""Unitary PSPs from leg sugar GRNs onto the route's entry cells, against their distance from threshold
(diagnostic, s12).

The `near` arm puts the leg sugar route 1 mV below rheobase and fires MN9 at 3 Hz of GRN input
(DECISIONS 6 October 00:26 and 00:41). This measures, in the model, the two numbers that decide such a
hair trigger: the peak depolarisation one GRN spike gives each AN01B004 / AN05B106 cell, and how far
below threshold each cell rests. It settles the full network with no stimulus, copies it, kicks one GRN
in the copy and subtracts the unkicked copy (same random state), so noise cancels.

    FLYEMU_EXTRA_PARAMS=runs/s12/rest/route_near.csv uv run python scripts/probes/unitary_psp.py \
        --profile m9c --out runs/s12/margin/unitary_near.json
"""
from __future__ import annotations

import argparse
import copy
import json
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))
from flyemu import connectome, electrical, lif, profiles  # noqa: E402
from flyemu.registry import Policy, Registry  # noqa: E402

DT = 0.1


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--profile", default=profiles.WORKING_PROFILE)
    ap.add_argument("--pre", default="LgLG4,LgAG2")
    ap.add_argument("--post", default="AN01B004,AN05B106")
    ap.add_argument("--settle-ms", type=float, default=300.0)
    ap.add_argument("--window-ms", type=float, default=40.0)
    ap.add_argument("--max-pairs", type=int, default=40, help="GRNs kicked, strongest connections first")
    ap.add_argument("--out", default="")
    a = ap.parse_args()

    reg = Registry(Policy.MINIMAL)
    prof = profiles.apply(reg, a.profile)
    conn = connectome.build(reg, min_synapses=profiles.WORKING_MIN_SYNAPSES)
    params = lif.default_params(reg, conn, timestep_ms=DT)
    el = electrical.build(reg, conn)
    t = conn.neurons.type.fillna("")
    pre = np.flatnonzero(t.isin(a.pre.split(",")).to_numpy())
    post = np.flatnonzero(t.isin(a.post.split(",")).to_numpy())
    # synapse counts pre -> post from the CSR graph (indptr over presynaptic cells)
    syn, ps = {}, set(post.tolist())
    for i in pre:
        lo, hi = conn.indptr[i], conn.indptr[i + 1]
        for j, c in zip(conn.indices[lo:hi], conn.weight_syn[lo:hi]):
            if int(j) in ps:
                syn[(int(i), int(j))] = float(c)
    pairs = sorted(syn, key=lambda k: -syn[k])[: a.max_pairs]
    net = lif.Network(conn, params, DT, rng=np.random.default_rng(1))
    net.elec = el if len(el[0]) else None
    for _ in range(int(a.settle_ms / DT)):
        net.step()
    v_th = np.broadcast_to(np.asarray(net.v_th, np.float32), (conn.n,))
    gap = {int(j): float(v_th[j] - net.v[j]) for j in post}
    rows = []
    nw = int(a.window_ms / DT)
    for i in sorted({p for p, _ in pairs}):
        # share the static graph and parameters; copy the state
        memo = {id(conn): conn, id(params): params}
        ctrl, kick = copy.deepcopy(net, dict(memo)), copy.deepcopy(net, dict(memo))
        vc = np.zeros((nw, len(post)), np.float32)
        vk = np.zeros_like(vc)
        for s in range(nw):
            ctrl.step()
            kick.step(kick=(np.array([i]), prof["kick_mv"]) if s == 0 else None)
            vc[s], vk[s] = ctrl.v[post], kick.v[post]
        dv = (vk - vc).max(axis=0)
        tpk = (vk - vc).argmax(axis=0) * DT
        for k, j in enumerate(post):
            if (int(i), int(j)) in syn:
                rows.append({"pre": int(conn.neurons.bodyId.iat[i]), "pre_type": t.iat[i],
                             "post": int(conn.neurons.bodyId.iat[j]), "post_type": t.iat[j],
                             "synapses": syn[(int(i), int(j))], "psp_peak_mv": round(float(dv[k]), 3),
                             "t_peak_ms": round(float(tpk[k]), 1), "gap_to_threshold_mv": round(gap[int(j)], 2)})
                print(f"{t.iat[i]:7s} -> {t.iat[j]:9s} {syn[(int(i), int(j))]:5.0f} syn  "
                      f"PSP {dv[k]:6.3f} mV at {tpk[k]:4.1f} ms  gap {gap[int(j)]:5.2f} mV", flush=True)
    if a.out:
        Path(a.out).parent.mkdir(parents=True, exist_ok=True)
        Path(a.out).write_text(json.dumps({"profile": a.profile, "kick_mv": prof["kick_mv"], "rows": rows,
                                           "gap_mv": {str(conn.neurons.bodyId.iat[j]): g for j, g in gap.items()}},
                                          indent=1))


if __name__ == "__main__":
    main()
