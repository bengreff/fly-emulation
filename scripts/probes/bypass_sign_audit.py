"""Bypass assay S3 sign audit: what reaches the leg motor neurons, by presynaptic transmitter and model sign (s13).

DIAGNOSTIC, no simulation. Builds the m10f0 network (no camera) and, for the leg MNs used by bypass_s2_descending.py,
tallies the incoming connectome synapses and model weights by presynaptic superclass x predicted transmitter x the
sign the model gives the edge. Also lists the glutamate receptor sign each leg MN type gets (cell_types.csv
`glutamate_receptor_sign` rows; 0 = the transmitter default) and the sign of every loop edge of Pugliese's minimal
oscillator per neuromere. Writes runs/s13/bypass/s3/sign_audit.json.

    uv run python scripts/probes/bypass_sign_audit.py [--set KEY=V]
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "src")); sys.path.insert(0, str(REPO / "scripts"))
sys.path.insert(0, str(Path(__file__).resolve().parent))
from flyemu.organism import Organism  # noqa: E402
from bypass_s3_chain import ROLE  # noqa: E402


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--profile", default="m10f0")
    ap.add_argument("--seed", type=int, default=12)
    ap.add_argument("--set", action="append", default=[], metavar="KEY=V")
    ap.add_argument("--out", default=str(REPO / "runs" / "s13" / "bypass" / "s3" / "sign_audit.json"))
    a = ap.parse_args()
    ov = {k: float(v) for k, v in (x.rsplit("=", 1) for x in a.set)}
    org = Organism(policy="minimal", profile=a.profile, min_synapses=5, overrides=ov, seed=a.seed, with_camera=False)
    conn, net, n = org.conn, org.net, org.conn.neurons
    sc = n.superclass.fillna("").to_numpy().astype(str)
    typ = n.type.fillna("").to_numpy().astype(str)
    nt = n.get("predictedNt", pd.Series([""] * conn.n)).fillna("unknown").str.lower().to_numpy().astype(str)
    h, nm = org.hill, org.nm
    mn_rows = np.asarray(nm.mn_index)
    leg_mn = (h.mn_muscle >= 0) | ((h.mn_group >= 0) if h.coxa is not None else False)
    is_legmn = np.zeros(conn.n, bool); is_legmn[mn_rows[leg_mn]] = True
    pre = np.repeat(np.arange(conn.n), np.diff(conn.indptr))
    post = conn.indices
    syn = np.asarray(conn.weight_syn, float)
    e = is_legmn[post]
    df = pd.DataFrame(dict(pre_super=sc[pre[e]], nt=nt[pre[e]], sign=np.sign(net.w[e]).astype(int),
                           syn=syn[e], w=net.w[e].astype(float)))
    tab = (df.groupby(["pre_super", "nt", "sign"]).agg(edges=("syn", "size"), synapses=("syn", "sum"),
                                                       weight_mv=("w", "sum")).reset_index()
           .sort_values("synapses", ascending=False))
    tot = df.syn.sum()
    tab["share"] = (tab.synapses / tot).round(4)
    gs = np.asarray(net.params.glu_sign_post if np.ndim(net.params.glu_sign_post) else
                    np.full(conn.n, net.params.glu_sign_post), float)
    mn_glu = pd.Series(gs[mn_rows[leg_mn]]).value_counts().to_dict()
    # minimal oscillator edges per neuromere
    seg = (n["somaNeuromere"] if "somaNeuromere" in n else n.get("soma_neuromere", pd.Series([""] * conn.n))).fillna("").astype(str).to_numpy()
    side = n["somaSide"].fillna("").astype(str).to_numpy()
    cells = np.flatnonzero(np.isin(typ, list(ROLE)))
    loop = []
    for i in cells:
        for k in range(conn.indptr[i], conn.indptr[i + 1]):
            j = post[k]
            if typ[j] in ROLE and seg[j] + side[j] == seg[i] + side[i]:
                loop.append(dict(seg=seg[i] + side[i], edge=f"{ROLE[typ[i]]}>{ROLE[typ[j]]}", nt=nt[i],
                                 synapses=float(syn[k]), w_mv=round(float(net.w[k]), 2)))
    res = dict(diagnostic="sign audit, no simulation", profile=a.profile, overrides=ov,
               n_leg_mn=int(leg_mn.sum()), leg_mn_input_synapses=float(tot),
               glutamate_receptor_sign_on_leg_mns=({str(k): int(v) for k, v in mn_glu.items()}),
               by_source=tab.to_dict("records"), oscillator_edges=loop)
    Path(a.out).write_text(json.dumps(res, indent=1, default=float))
    pd.set_option("display.width", 160)
    print(f"leg MNs {res['n_leg_mn']}, input synapses {tot:.0f}, glu receptor sign on leg MNs {res['glutamate_receptor_sign_on_leg_mns']}")
    print(tab.head(20).to_string(index=False))
    sub = df[df.pre_super == "vnc_intrinsic"]
    print("vnc_intrinsic premotor share by transmitter:",
          (sub.groupby("nt").syn.sum() / sub.syn.sum()).round(3).to_dict())
    lp = pd.DataFrame(loop)
    if len(lp):
        print(lp[lp.seg.str.contains("T1")].pivot_table(index="edge", columns="seg", values="synapses").to_string())


if __name__ == "__main__":
    main()
