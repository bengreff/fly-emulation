"""Unitary premotor -> leg-MN PSPs in the model at a given leg-MN synaptic_input_scale (diagnostic, s13 S4b).

The S4b plausibility check (Director, 14 Oct): convert a scale into the peak PSP one premotor spike gives a leg MN
(mV per spike, and per synapse) so it can be set against measured insect unitary PSPs. Method as unitary_psp.py:
settle the network, copy it, force one presynaptic spike in the copy (Shiu kick) and subtract the unkicked copy
(same random state). Pairs where the MN spikes in either copy within the window are dropped. Excitatory
(cholinergic) premotor cells only, sampled across connection sizes.

    uv run python scripts/probes/s4b_unitary_psp.py --scales 1,25 --out runs/s13/bypass/s4b/unitary_psp.json

s15 (fly, 21 Oct): --set k=v (repeatable) adds registry overrides (the two-compartment switch and arm controls);
--post core measures excitatory inputs onto the oscillator core instead of leg MNs; when the post cell has an N30
spike-zone compartment (net.c2) its peak is reported too (sz_psp_mv), the soma peak stays psp_mv.
"""
from __future__ import annotations

import argparse
import copy
import json
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))
from flyemu import lif, percell  # noqa: E402
from flyemu.gpu.equivalence import build_brain  # noqa: E402

DT = 0.1
KEY = "cell_type:leg_motor|synaptic_input_scale"


CORE = r"^(IN17A001|INXXX466|IN16B036|IN19A007|IN19A004|IN19A002)$"


def run(scale: float, a) -> dict:
    ov = {KEY: scale} if scale != 1.0 else {}
    for kv in a.set:
        k, _, v = kv.rpartition("=")
        ov[k] = float(v)
    reg, conn, params, kick_mv = build_brain(ov, profile=a.profile, min_synapses=5)
    leg = percell.leg_motor_mask(conn)
    if a.post == "core":
        tgt = conn.neurons.type.fillna("").str.contains(CORE, regex=True).to_numpy()
        excl = np.zeros(conn.n, bool)
    else:
        tgt, excl = leg, leg
    rows_pre = {}
    for i in range(conn.n):
        lo, hi = conn.indptr[i], conn.indptr[i + 1]
        js, cs = conn.indices[lo:hi], conn.weight_syn[lo:hi]
        m = tgt[js] & (js != i)
        if conn.sign[i] > 0 and m.any() and not excl[i]:   # sign is per presynaptic cell
            rows_pre[i] = dict(zip(js[m].tolist(), cs[m].astype(float).tolist()))
    pre = sorted(rows_pre, key=lambda i: max(rows_pre[i].values()))
    pick = sorted({pre[int(q)] for q in np.linspace(0, len(pre) - 1, a.n_pre)})
    net = lif.Network(conn, params, DT, rng=np.random.default_rng(1))
    c2 = getattr(net, "c2", None)
    for _ in range(int(a.settle_ms / DT)):
        net.step()
    memo = {id(conn): conn, id(params): params}
    nw, out = int(a.window_ms / DT), []
    t = conn.neurons.type.fillna("")
    for i in pick:
        post = np.array(sorted(rows_pre[i]))
        ctrl, kick = copy.deepcopy(net, dict(memo)), copy.deepcopy(net, dict(memo))
        vc, vk = np.zeros((nw, len(post))), np.zeros((nw, len(post)))
        jz = c2["pos"][post] if c2 is not None else np.full(len(post), -1)
        zc, zk = np.zeros((nw, len(post))), np.zeros((nw, len(post)))
        spk_post, pre_spk = np.zeros(len(post), bool), 0
        for s in range(nw):
            sc = ctrl.step()
            sk = kick.step(kick=(np.array([i]), kick_mv) if s == 0 else None)
            pre_spk += int(i in set(sk.tolist())) - int(i in set(sc.tolist()))
            spk_post |= np.isin(post, sc) | np.isin(post, sk)
            vc[s], vk[s] = ctrl.v[post], kick.v[post]
            if (jz >= 0).any():
                zc[s, jz >= 0], zk[s, jz >= 0] = ctrl.c2["v"][jz[jz >= 0]], kick.c2["v"][jz[jz >= 0]]
        d, dz = vk - vc, zk - zc
        for k, j in enumerate(post):
            if spk_post[k] or pre_spk != 1:
                continue
            n = rows_pre[i][int(j)]
            out.append(dict(pre=int(conn.neurons.bodyId.iat[i]), pre_type=t.iat[i], post=int(conn.neurons.bodyId.iat[j]),
                            post_type=t.iat[j], synapses=n, psp_mv=round(float(d[:, k].max()), 4),
                            t_peak_ms=round(float(d[:, k].argmax() * DT), 1),
                            mv_per_syn=round(float(d[:, k].max() / n), 5),
                            sz_psp_mv=round(float(dz[:, k].max()), 4) if jz[k] >= 0 else None))
    psp = np.array([r["psp_mv"] for r in out])
    per = np.array([r["mv_per_syn"] for r in out])
    syn = np.array([r["synapses"] for r in out])
    all_conn = np.array([c for v in rows_pre.values() for c in v.values()])
    summ = dict(scale=scale, pairs=len(out), pre_cells=len(pick),
                psp_mv_median=float(np.median(psp)), psp_mv_q10_q90=[float(np.quantile(psp, .1)), float(np.quantile(psp, .9))],
                psp_mv_max=float(psp.max()), mv_per_syn_median=float(np.median(per)),
                mv_per_syn_q10_q90=[float(np.quantile(per, .1)), float(np.quantile(per, .9))],
                sampled_synapses_median=float(np.median(syn)),
                all_exc_premotor_connections=int(all_conn.size),
                all_exc_connection_synapses_median=float(np.median(all_conn)),
                all_exc_connection_synapses_q90=float(np.quantile(all_conn, .9)))
    sz = np.array([r["sz_psp_mv"] for r in out if r["sz_psp_mv"] is not None])
    if sz.size:
        summ.update(sz_psp_mv_median=float(np.median(sz)), sz_psp_mv_q10_q90=[float(np.quantile(sz, .1)),
                                                                              float(np.quantile(sz, .9))])
    summ.update(post=a.post, overrides={k: v for k, v in ov.items()})
    print(json.dumps(summ), flush=True)
    return dict(summary=summ, rows=out)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--profile", default="m10f0")
    ap.add_argument("--scales", default="1,25")
    ap.add_argument("--n-pre", type=int, default=24, help="excitatory premotor cells, spread over connection size")
    ap.add_argument("--settle-ms", type=float, default=300.0)
    ap.add_argument("--window-ms", type=float, default=40.0)
    ap.add_argument("--out", default="")
    ap.add_argument("--set", action="append", default=[], help="registry override k=v (repeatable)")
    ap.add_argument("--post", choices=("leg", "core"), default="leg")
    a = ap.parse_args()
    res = [run(float(s), a) for s in a.scales.split(",")]
    if a.out:
        Path(a.out).parent.mkdir(parents=True, exist_ok=True)
        Path(a.out).write_text(json.dumps(dict(profile=a.profile, key=KEY, results=res), indent=1))


if __name__ == "__main__":
    main()
