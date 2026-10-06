"""Do the neck-position rest-DN candidates reach the leg motor pools within two synapses? (F-STAND-3)

Structure only, no simulation. Reads the candidate types from `neck_rest_dn_match.py`
(runs/s12/dnrest/neck_rest_match.json), finds their cells in the model connectome by male-cns type,
and for every descending neuron (circuit class DN) sums signed synapse counts onto leg motor neurons
(motor_forces.csv): direct (DN -> MN) and two-hop (DN -> interneuron -> MN, each path weighted by the
DN's share of the interneuron's input, as in load_reflex_paths.py). Each candidate type is then ranked
against all DNs, so "reaches the legs" means more than a typical DN does.

    PYTHONPATH=src uv run python scripts/probes/rest_dn_reach.py
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import scipy.sparse as sp

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "src"))
from flyemu import neuromuscular  # noqa: E402
from flyemu.lif import circuit_classes  # noqa: E402
from flyemu.organism import Organism  # noqa: E402
from flyemu.profiles import WORKING_PROFILE  # noqa: E402

MATCH = REPO / "runs/s12/dnrest/neck_rest_match.json"
OUT = REPO / "runs/s12/dnrest/rest_dn_reach.json"


def main() -> None:
    org = Organism(policy="minimal", profile=WORKING_PROFILE, min_synapses=5, seed=0, with_camera=False)
    c = org.conn
    n = c.n
    ty = c.neurons.type.fillna("untyped").astype(str).to_numpy()
    dn = np.flatnonzero(circuit_classes(c) == "DN")
    pre = np.repeat(np.arange(n), np.diff(c.indptr))
    w = c.sign[pre].astype(np.float64) * c.weight_syn
    W = sp.csr_matrix((w, (pre, c.indices)), shape=(n, n))
    in_tot = np.bincount(c.indices, weights=c.weight_syn, minlength=n)
    S = sp.csr_matrix((c.weight_syn / np.maximum(in_tot[c.indices], 1), (pre, c.indices)), shape=(n, n))
    mf = pd.read_csv(neuromuscular.FORCE_TABLE, comment="#")
    mf["row"] = c.index_of(mf.bodyId.to_numpy())
    mf = mf[mf.row >= 0]
    mn = mf.row.to_numpy()
    d1 = np.asarray(W[dn][:, mn].todense())                       # DN x MN, signed synapses
    d2 = np.asarray((S[dn] @ W[:, mn]).todense())                 # DN x MN, two-hop share-weighted
    tot1, tot2 = d1.sum(1), d2.sum(1)
    abs2 = np.abs(d2).sum(1)
    joints = mf.joint.to_numpy()

    def pct(v: np.ndarray, x: float) -> float:
        return round(float((v < x).mean() * 100), 1)

    m = json.loads(MATCH.read_text())
    out = []
    for r in m["rows"]:
        if r["confidence"] not in ("low", "very low"):
            continue
        names = {t.removeprefix("auto:") for t in r["malecns"]}
        k = np.flatnonzero(np.isin(ty[dn], list(names)))
        if not len(k):
            out.append(dict(band=r["band"], banc_type=r["banc_type"], confidence=r["confidence"], n_model=0))
            continue
        bj = {j: round(float(d2[k][:, joints == j].sum()), 2) for j in sorted(set(joints))}
        out.append(dict(
            band=r["band"], banc_type=r["banc_type"], confidence=r["confidence"], malecns=sorted(names),
            n_model=int(len(k)),
            direct_syn_per_cell=round(float(tot1[k].mean()), 1),
            two_hop_net_per_cell=round(float(tot2[k].mean()), 2),
            two_hop_abs_per_cell=round(float(abs2[k].mean()), 2),
            pct_abs_among_dns=pct(abs2, float(abs2[k].mean())),
            two_hop_by_joint=bj))
    res = dict(profile=WORKING_PROFILE, n_dn=int(len(dn)), n_leg_mn=int(len(mn)),
               dn_two_hop_abs_median=round(float(np.median(abs2)), 2),
               dn_two_hop_abs_p90=round(float(np.percentile(abs2, 90)), 2),
               dn_direct_any_frac=round(float((np.abs(d1).sum(1) > 0).mean()), 3),
               rows=out)
    OUT.write_text(json.dumps(res, indent=1))
    print(json.dumps({k: v for k, v in res.items() if k != "rows"}))
    for r in out:
        if r.get("n_model"):
            print(f"{r['band']:16s} {r['confidence']:9s} {r['banc_type']:12s} n={r['n_model']} "
                  f"direct={r['direct_syn_per_cell']:7.1f} 2hop_net={r['two_hop_net_per_cell']:7.2f} "
                  f"2hop_abs={r['two_hop_abs_per_cell']:7.2f} pct={r['pct_abs_among_dns']:5.1f}")
        else:
            print(f"{r['band']:16s} {r['confidence']:9s} {r['banc_type']:12s} not in model")


if __name__ == "__main__":
    main()
