"""N33 edge count (Director 24 Oct 03:10): how many edges the uptake mechanism modifies in a stage, how many it
would act on with uptake below healthy, and what decay those edges carry (N29 row or the default tau_s).

    uv run python scripts/probes/s23_n33_edge_count.py --profile m10f12 --out runs/s23/n33/edge_count.json
"""
import argparse
import json
import sys

import numpy as np

sys.path.insert(0, "src")
from flyemu import connectome, lif, profiles, stubs  # noqa: E402
from flyemu.registry import Policy, Registry  # noqa: E402


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--profile", default="m10f12")
    ap.add_argument("--out", default="")
    a = ap.parse_args()
    reg = Registry(Policy.MINIMAL)
    profiles.apply(reg, a.profile)
    stubs.read(reg)
    conn = connectome.build(reg, min_synapses=5)
    p = lif.default_params(reg, conn, timestep_ms=0.1)
    pre = np.repeat(np.arange(conn.n), np.diff(conn.indptr))
    glu = lif._stp_cells(conn.neurons, "nt:glutamate")
    e_glu = np.flatnonzero(glu[pre])
    graded = np.asarray(p.graded, bool)
    e_sp = e_glu[~graded[pre[e_glu]]]
    kin = p.kin_edge["idx"] if p.kin_edge is not None else np.array([], np.int64)
    tau_s = np.broadcast_to(np.asarray(p.tau_s, np.float32), (conn.n,))
    out = {
        "profile": a.profile, "n_cells": int(conn.n), "n_edges": int(conn.n_edges),
        "eaat1_uptake": float(reg.inventory().query("property == 'eaat1_uptake'").value.iloc[0]),
        "edges_modified_in_stage": 0 if p.uptake_edge is None else int(len(p.uptake_edge["idx"])),
        "glutamatergic_pre_edges": int(len(e_glu)),
        "glutamatergic_pre_cells": int(glu.sum()),
        "of_which_graded_pre_edges": int(len(e_glu) - len(e_sp)),
        "edges_acted_on_below_healthy": int(len(e_sp)),
        "edges_acted_on_frac_of_all": round(len(e_sp) / conn.n_edges, 4),
        "acted_on_with_n29_row": int(np.isin(e_sp, kin).sum()),
        "n29_rows_edges_total": int(len(kin)),
        "default_tau_s_on_acted_edges_ms": sorted({round(float(t), 3) for t in tau_s[conn.indices[e_sp]]}),
    }
    print(json.dumps(out))
    if a.out:
        json.dump(out, open(a.out, "w"))


if __name__ == "__main__":
    main()
