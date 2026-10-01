"""Connectome paths from leg chordotonal afferents to that leg's tibia MN pools (session 11).

For the model as built (working profile, min_synapses 5): per FeCO subtype
of --leg, synapse counts onto the femur-tibia +1 (extensor) and -1 (flexor)
MN pools, directly and through one interneuron (the strongest 2-hop paths
ranked by min(syn in, syn out)), with the interneuron's type and sign and the
per-edge PSP (mV) of both hops. Also counts afferents per subtype per leg.

    uv run python scripts/probes/feco_paths.py [--leg lf] [--out X.json]
"""
import argparse
import json
import sys

import numpy as np

sys.path.insert(0, "src")
from flyemu.organism import Organism  # noqa: E402
from flyemu.profiles import WORKING_PROFILE  # noqa: E402


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--leg", default="lf")
    ap.add_argument("--top", type=int, default=8)
    ap.add_argument("--out", default="")
    a = ap.parse_args()
    org = Organism(policy="minimal", profile=WORKING_PROFILE, min_synapses=5,
                   overrides={"motor_unit:all|force_per_spike": 10.0})
    c, h, nm, af = org.conn, org.hill, org.nm, org.aff
    n = c.neurons
    typ = n.type.fillna("").to_numpy()
    st = af.subtype if af.subtype is not None else np.full(len(af.rows), "")
    jn = f"{a.leg}_trochanterfemur-{a.leg}_tibia-pitch"
    pools = {}
    for sgn, nmz in ((1, "ext"), (-1, "flex")):
        k = np.flatnonzero((h.p.joint == jn) & (h.p.direction == sgn))
        pools[nmz] = set(np.asarray(nm.mn_index)[np.isin(h.mn_muscle, k)].tolist())
    eff = c.efficacy_mv

    def out_edges(i):
        s, e = c.indptr[i], c.indptr[i + 1]
        return c.indices[s:e], c.weight_syn[s:e], eff[s:e]

    counts = {}
    for leg in sorted(set(af.leg)):
        m = af.leg == leg
        counts[leg] = {g: int(((st == g) & m).sum()) for g in sorted(set(st[m])) if g}
    res = {"leg": a.leg, "afferents_per_leg": counts, "pool_sizes": {k: len(v) for k, v in pools.items()},
           "paths": {}}
    for g in ("claw", "hook_flex", "hook_ext", "club"):
        rows = af.rows[(af.leg == a.leg) & (st == g)]
        r = {"n_afferents": int(len(rows)), "sign": sorted(set(int(c.sign[i]) for i in rows))}
        hop1 = {}
        for i in rows:
            post, w, e = out_edges(i)
            for p_, w_, e_ in zip(post, w, e):
                hop1.setdefault(int(p_), [0, 0.0])
                hop1[int(p_)][0] += int(w_)
                hop1[int(p_)][1] += float(e_)
        for pool, ids in pools.items():
            r[f"direct_syn_{pool}"] = int(sum(v[0] for k, v in hop1.items() if k in ids))
            two = []
            for k_, (w1, e1) in hop1.items():
                if k_ in ids:
                    continue
                post, w, e = out_edges(k_)
                sel = np.isin(post, list(ids))
                if sel.any():
                    two.append((min(w1, int(w[sel].sum())), typ[k_], int(c.sign[k_]), w1, int(w[sel].sum()),
                                round(e1, 2), round(float(e[sel].sum()), 2)))
            two.sort(reverse=True)
            r[f"n_2hop_interneurons_{pool}"] = len(two)
            r[f"top_2hop_{pool}"] = [dict(zip(("min_syn", "type", "sign", "syn_in", "syn_out", "psp_in_mv",
                                               "psp_out_mv"), t)) for t in two[:a.top]]
        res["paths"][g] = r
    print(json.dumps(res, indent=1))
    if a.out:
        with open(a.out, "w") as f:
            json.dump(res, f, indent=1)


if __name__ == "__main__":
    main()
