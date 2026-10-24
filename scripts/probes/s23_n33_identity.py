"""N33 check (3) (DECISIONS 24 Oct 02:28): m10f12 (uptake switch on, healthy uptake) builds the same network as
m10f10. Compares the fast weights, the N29 kinetics, the channel list and weights, the graded matrix, and the
spikes of 200 steps under the same kick and seed; reports the N33 registry reads.

    uv run python scripts/probes/s23_n33_identity.py --out runs/s23/n33/identity.json
"""
import argparse
import json
import sys

import numpy as np

sys.path.insert(0, "src")
from flyemu.organism import Organism  # noqa: E402


def build(profile):
    return Organism(policy="minimal", profile=profile, min_synapses=5, seed=12)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--base", default="m10f10")
    ap.add_argument("--stage", default="m10f12")
    ap.add_argument("--steps", type=int, default=200)
    ap.add_argument("--out", default="")
    a = ap.parse_args()
    org = {p: build(p) for p in (a.base, a.stage)}
    x, y = org[a.base].net, org[a.stage].net
    ke = lambda n: None if n.params.kin_edge is None else (n.params.kin_edge["idx"].tolist(),
                                                           n.params.kin_edge["tau"].tolist())
    out = {
        "w_equal": bool(np.array_equal(x.w, y.w)),
        "kin_edge_equal": ke(x) == ke(y),
        "uptake_edge_stage": None if y.params.uptake_edge is None else len(y.params.uptake_edge["idx"]),
        "chan_names": [[c["name"] for c in x.chan], [c["name"] for c in y.chan]],
        "chan_w_equal": len(x.chan) == len(y.chan) and all(np.array_equal(c["w"], d["w"])
                                                           for c, d in zip(x.chan, y.chan)),
        "graded_equal": (x.W_graded is None and y.W_graded is None)
                        or (x.W_graded is not None and y.W_graded is not None
                            and (x.W_graded != y.W_graded).nnz == 0),
    }
    n = org[a.base].conn.n
    same = True
    for s in range(a.steps):
        k = (np.arange(0, n, 997), 20.0)
        same &= bool(np.array_equal(x.step(kick=k), y.step(kick=k)))
    out["spikes_equal_steps"] = [a.steps, same]
    inv = org[a.stage].reg.inventory()
    sel = inv[(inv.entity + "|" + inv.property).str.contains("glia|astrocyte", regex=True)]
    out["n33_reads"] = {f"{r.entity}|{r.property}": [float(r.value), str(r.status)] for r in sel.itertuples()}
    out["pass"] = bool(out["w_equal"] and out["kin_edge_equal"] and out["uptake_edge_stage"] is None
                       and out["chan_w_equal"] and out["graded_equal"] and same)
    print(json.dumps(out))
    if a.out:
        with open(a.out, "w") as f:
            json.dump(out, f)


if __name__ == "__main__":
    main()
