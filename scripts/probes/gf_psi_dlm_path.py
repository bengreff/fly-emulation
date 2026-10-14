"""Why DLMn stays silent after the GF spikes (fly2, s13 diagnostic after F-GJ-3).

Builds the GF latency probe's organism (gaps on, extra overrides as in gf_latency.py), prints
the PSI and DLMn rows (transmitter, sign), every PSI->DLMn and GF->DLMn edge (synapse count,
weight, delay) and the DLMn threshold distance, then kicks the GF once and records the DLMn and
PSI membrane potential for the next 10 ms. Measures; not an objective.
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
    a = ap.parse_args()
    extra = {k: float(v) for k, v in (s.split("=", 1) for s in a.set)}
    org = Organism(policy="minimal", profile=a.profile, min_synapses=profiles.WORKING_MIN_SYNAPSES, seed=0,
                   overrides={**extra, "electrical:all|gap_conductance": 1.0})
    net, conn, p, dt = org.net, org.conn, org.net.params, org.timestep_ms
    t = conn.neurons.type.fillna("").to_numpy()
    nt = conn.neurons.predictedNt.fillna("").to_numpy()
    cells = {ty: np.flatnonzero(t == ty) for ty in ("DNp01", "PSI", "DLMn a, b", "DLMn c-f", "TTMn")}
    arr = lambda x, i: float(np.broadcast_to(np.asarray(x, np.float64), (conn.n,))[i])
    rep = {"profile": a.profile, "overrides": extra, "cells": {}, "edges": [], "trace": {}}
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
    settle, win = int(200 / dt), int(10 / dt)
    for s in range(settle):
        net.step()
    v0 = net.v[watch].copy()
    tr = []
    for s in range(win):
        net.step(kick=(cells["DNp01"], 100.0) if s == 0 else None)
        tr.append(net.v[watch].copy())
    tr = np.array(tr)
    for j, i in enumerate(watch):
        rep["trace"][int(i)] = {"type": t[i], "v_before": float(v0[j]), "v_max": float(tr[:, j].max()),
                                "step_of_max": int(tr[:, j].argmax()), "v_th": arr(p.v_th, i)}
    a.out.parent.mkdir(parents=True, exist_ok=True)
    a.out.write_text(json.dumps(rep, indent=1) + "\n")
    for i, c in rep["cells"].items():
        print("cell", i, c)
    for e in rep["edges"]:
        print("edge", e)
    for i, c in rep["trace"].items():
        print("trace", i, c)


if __name__ == "__main__":
    main()
