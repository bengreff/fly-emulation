"""Why DLMn stays silent after the GF spikes (fly2, s13 diagnostic after F-GJ-3).

Builds the GF latency probe's organism (gaps on, extra overrides as in gf_latency.py), prints
the PSI and DLMn rows (transmitter, sign), every PSI->DLMn and GF->DLMn edge (synapse count,
weight, delay) and the DLMn threshold distance, then kicks the GF once and records the DLMn and
PSI membrane potential for the next 10 ms (--window-ms). Measures; not an objective.

s20 (N30): with cell_type:all|two_compartments_where_point_fails = 1 it also records the axon
compartment and the DLMn spikes; --axon-passive raises the DLMn threshold out of reach (the soma
cannot spike under the switch, so only the axon is affected), which is the pre-registered gate:
the soma peak of the passive pair, as the paper measured the EPSP without the spike.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "src"))

from flyemu import profiles  # noqa: E402
from flyemu.organism import Organism  # noqa: E402


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--profile", default="m10f")
    ap.add_argument("--set", action="append", default=[], help="extra override entity|property=value")
    ap.add_argument("--out", type=Path, required=True)
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--window-ms", type=float, default=10.0)
    ap.add_argument("--axon-passive", action="store_true", help="N30 gate: DLMn axon threshold out of reach")
    a = ap.parse_args()
    extra = {k: float(v) for k, v in (s.split("=", 1) for s in a.set)}
    org = Organism(policy="minimal", profile=a.profile, min_synapses=profiles.WORKING_MIN_SYNAPSES, seed=a.seed,
                   overrides={**extra, "electrical:all|gap_conductance": 1.0})
    net, conn, p, dt = org.net, org.conn, org.net.params, org.timestep_ms
    t = conn.neurons.type.fillna("").to_numpy()
    nt = conn.neurons.predictedNt.fillna("").to_numpy()
    cells = {ty: np.flatnonzero(t == ty) for ty in ("DNp01", "PSI", "DLMn a, b", "DLMn c-f", "TTMn")}
    arr = lambda x, i: float(np.broadcast_to(np.asarray(x, np.float64), (conn.n,))[i])
    rep = {"profile": a.profile, "overrides": extra, "seed": a.seed, "window_ms": a.window_ms,
           "axon_passive": a.axon_passive, "cells": {}, "edges": [], "trace": {}}
    for ty, ix in cells.items():
        for i in ix:
            rep["cells"][int(i)] = {"type": ty, "nt": nt[i], "sign": float(conn.sign[i]),
                                    "graded": bool(net.graded[i]) if net.graded is not None else False,
                                    "v_rest": arr(p.v_rest, i), "v_th": arr(p.v_th, i), "tau_m": arr(p.tau_m, i),
                                    "delay_steps": arr(p.delay_steps, i)}
    dlm = np.concatenate([cells["DLMn a, b"], cells["DLMn c-f"]])
    for pre in np.concatenate([cells["DNp01"], cells["PSI"]]):
        for e in range(conn.indptr[pre], conn.indptr[pre + 1]):
            post = conn.indices[e]
            if post in dlm or (t[pre] == "DNp01" and t[post] == "PSI"):
                rep["edges"].append({"pre": t[pre], "pre_i": int(pre), "post": t[post], "post_i": int(post),
                                     "syn": float(conn.weight_syn[e]), "w": float(net.w[e]),
                                     "chan_w": [float(c["w"][e]) for c in net.chan]})
    # in-network response to one GF spike after 200 ms settle
    watch = np.concatenate([cells["PSI"], dlm])
    c2 = getattr(net, "c2", None)
    if a.axon_passive:
        if c2 is None:
            raise SystemExit("--axon-passive needs the N30 switch")
        net.v_th[dlm] = 1e9
    settle, win = int(200 / dt), int(a.window_ms / dt)
    for s in range(settle):
        net.step()
    v0 = net.v[watch].copy()
    tr, ta, spikes = [], [], {int(i): [] for i in watch}
    for s in range(win):
        out = net.step(kick=(cells["DNp01"], 100.0) if s == 0 else None)
        tr.append(net.v[watch].copy())
        if c2 is not None:
            ta.append(c2["v"].copy())
        for i in np.intersect1d(out, watch):
            spikes[int(i)].append(s)
    tr = np.array(tr)
    for j, i in enumerate(watch):
        rep["trace"][int(i)] = {"type": t[i], "v_before": float(v0[j]), "v_max": float(tr[:, j].max()),
                                "step_of_max": int(tr[:, j].argmax()), "v_th": arr(p.v_th, i),
                                "spike_steps": spikes[int(i)], "v_trace": [round(float(x), 4) for x in tr[:, j]]}
        if c2 is not None and c2["is_cell"][i]:
            ax = np.array(ta)[:, c2["pos"][i]]
            rep["trace"][int(i)].update({"axon_v_max": float(ax.max()), "axon_step_of_max": int(ax.argmax()),
                                         "axon_trace": [round(float(x), 4) for x in ax]})
    a.out.parent.mkdir(parents=True, exist_ok=True)
    a.out.write_text(json.dumps(rep, indent=1) + "\n")
    for i, c in rep["cells"].items():
        print("cell", i, c)
    for e in rep["edges"]:
        print("edge", e)
    for i, c in rep["trace"].items():
        print("trace", i, {k: v for k, v in c.items() if not k.endswith("_trace")})


if __name__ == "__main__":
    main()
