"""Leg sugar GRNs to MN9 (proboscis extension): the connectome path and where activity dies in the model.

Real flies extend the proboscis when a tarsus touches sugar (tarsal PER, e.g. Dethier 1976). The model's
MN9 stays at 0 Hz with leg sugar at 1 M (`leg_taste_dose.py`, F-TASTE-LEG-1). This probe answers:

  structure  shortest directed path(s) in the model connectome (min 5 synapses per edge, as the
             organism) from the leg sugar GRNs (LgLG4, LgAG2; `extrasenses.LEG_MODALITY`) to MN9_L/R:
             hop count, the cells and types on shortest paths by layer, and synapses per hop. Also the
             hop count in the full male-cns edge table (min 1 synapse).
  run        one simulated condition (sugar patch at --conc, or 0 as control), saving per-neuron spike
             counts and peak depolarisation as a fraction of the threshold gap.
  report     structure plus the two runs: per layer of the shortest paths, and per BFS distance from the
             GRNs, how many cells fire more with sugar than in the control.
  run --inject all|fore|labellar
             contact-independent test, no food patch: each chosen sugar GRN gets, every step, the drive it
             would get touching 1 M sugar (gain x saturation x modality weight, the channel's own
             constants), added after adaptation so it does not decay. all = every leg sugar GRN, fore =
             foreleg ones (lf, rf), labellar = LB3b/c (positive control: the labellar path to MN9).
             Separates "the touching legs are the wrong legs" from "the circuit does not carry it".

    PYTHONPATH=src uv run python scripts/probes/legsugar_mn9_trace.py structure
    PYTHONPATH=src uv run python scripts/probes/legsugar_mn9_trace.py run --conc 1.0   (and --conc 0)
    PYTHONPATH=src uv run python scripts/probes/legsugar_mn9_trace.py report
"""
from __future__ import annotations

import argparse
import json
import sys
from collections import deque
from pathlib import Path

import numpy as np
import pandas as pd
import scipy.sparse as sp

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "src"))
OUT = REPO / "runs" / "s12" / "legsugar"
SUGAR_LEG = ("LgLG4", "LgAG2")


def build(conc: float, seed: int, camera: bool = False):
    from flyemu.extrasenses import FoodPatch
    from flyemu.organism import Organism
    from flyemu.profiles import WORKING_PROFILE
    org = Organism(policy="minimal", profile=WORKING_PROFILE, min_synapses=5, seed=seed, with_camera=camera,
                   overrides={"motor_unit:all|force_per_spike": 10.0, "sense:taste_leg|modality_source": 1})
    org.world.food = [FoodPatch(np.zeros(3), 100.0, {"sugar": conc})] if conc > 0 else []
    return org


def bfs(indptr: np.ndarray, indices: np.ndarray, src: np.ndarray, n: int) -> np.ndarray:
    d = np.full(n, -1, np.int64)
    d[src] = 0
    q = deque(src.tolist())
    while q:
        u = q.popleft()
        for v in indices[indptr[u]:indptr[u + 1]]:
            if d[v] < 0:
                d[v] = d[u] + 1
                q.append(v)
    return d


def structure(org) -> dict:
    c = org.conn
    n = c.n
    nn = c.neurons.reset_index(drop=True)
    ty = nn.type.fillna("untyped").astype(str).to_numpy()
    tl = org.extra.channels["taste_leg"].rows
    src = tl[np.isin(ty[tl], SUGAR_LEG)]
    mn9 = np.flatnonzero(nn.instance.eq("MN9_L").to_numpy() | nn.instance.eq("MN9_R").to_numpy())
    pre = np.repeat(np.arange(n), np.diff(c.indptr))
    T = sp.csr_matrix((np.ones(len(pre)), (c.indices, pre)), shape=(n, n))      # reversed graph
    df = bfs(c.indptr, c.indices, src, n)
    db = bfs(T.indptr, T.indices, mn9, n)
    D = int(df[mn9][df[mn9] >= 0].min()) if (df[mn9] >= 0).any() else -1
    on = (df >= 0) & (db >= 0) & (df + db == D)
    syn = np.asarray(c.weight_syn, np.float64)
    sgn = np.asarray(c.sign, np.float64)[pre]
    layers, hops = [], []
    for k in range(D + 1):
        r = np.flatnonzero(on & (df == k))
        tc = pd.Series(ty[r]).value_counts()
        layers.append(dict(k=k, n=int(len(r)), types=tc.head(12).to_dict(), n_types=int(len(tc))))
    for k in range(D):
        e = on[pre] & on[c.indices] & (df[pre] == k) & (df[c.indices] == k + 1)
        s = syn[e]
        hops.append(dict(hop=f"{k}->{k + 1}", n_edges=int(e.sum()), syn_total=int(s.sum()),
                         syn_median=float(np.median(s)) if len(s) else 0.0, syn_max=int(s.max()) if len(s) else 0,
                         frac_inhibitory_edges=round(float((sgn[e] < 0).mean()), 3) if len(s) else 0.0))
    # widest shortest paths: best bottleneck (min synapses along the path), by dynamic programming
    best = np.full(n, -1.0); best[src] = np.inf
    prev = np.full(n, -1, np.int64)
    for k in range(D):
        e = np.flatnonzero(on[pre] & on[c.indices] & (df[pre] == k) & (df[c.indices] == k + 1))
        for i in e[np.argsort(-syn[e])]:
            u, v = pre[i], c.indices[i]
            b = min(best[u], syn[i])
            if b > best[v]:
                best[v], prev[v] = b, u
    paths = []
    for m in mn9:
        if best[m] < 0:
            continue
        p, v = [], m
        while v >= 0:
            p.append(int(v)); v = prev[v]
        p = p[::-1]
        s = []
        for u, v in zip(p[:-1], p[1:]):
            j = c.indptr[u] + np.flatnonzero(c.indices[c.indptr[u]:c.indptr[u + 1]] == v)[0]
            s.append(int(syn[j]) * int(np.sign(sgn[j])))
        paths.append(dict(target=nn.instance.iloc[m], cells=[f"{ty[u]}|{nn.bodyId.iloc[u]}" for u in p],
                          signed_syn_per_hop=s, bottleneck=int(best[m])))
    # every on-path cell in the middle layers: sign, synapses in from the previous layer and out to the
    # next layer (unsigned; the cell's sign is its own field), and the excitatory-only hop count
    cells = []
    for k in range(1, D):
        for r in np.flatnonzero(on & (df == k)):
            e_in = (c.indices == r) & on[pre] & (df[pre] == k - 1)
            lo, hi = c.indptr[r], c.indptr[r + 1]
            post = c.indices[lo:hi]
            e_out = on[post] & (df[post] == k + 1)
            cells.append(dict(row=int(r), layer=k, type=ty[r], bodyId=int(nn.bodyId.iloc[r]),
                              sign=int(np.sign(c.sign[r])), syn_in_prev=int(syn[e_in].sum()),
                              syn_out_next=int(syn[lo:hi][e_out].sum()),
                              syn_to_mn9=int(syn[lo:hi][np.isin(post, mn9)].sum())))
    exc = sgn > 0
    Ae = sp.csr_matrix((np.ones(exc.sum()), (pre[exc], c.indices[exc])), shape=(n, n))
    de = bfs(Ae.indptr, Ae.indices, src, n)
    res = dict(n_src=int(len(src)), src_types={t: int((ty[src] == t).sum()) for t in SUGAR_LEG},
               n_mn9=int(len(mn9)), hops_to_mn9=D, n_on_shortest_paths=int(on.sum()),
               hops_to_mn9_excitatory_only=int(de[mn9][de[mn9] >= 0].min()) if (de[mn9] >= 0).any() else -1,
               layers=layers, hops=hops, widest_shortest_paths=paths, cells=cells,
               reach_by_distance={int(k): int((df == k).sum()) for k in range(int(df.max()) + 1)})
    # sugar GRNs by leg (extrasenses assigns the leg from the cell's neuropil; 6 = none)
    legs = ("lf", "lm", "lh", "rf", "rm", "rh", "none")
    side = org.extra.channels["taste_leg"].side[np.isin(ty[tl], SUGAR_LEG)]
    res["grn_leg"] = [legs[i] for i in side]
    res["grn_on_path_by_leg"] = {L: [int((side == i).sum()), int((on[src] & (side == i)).sum())]
                                 for i, L in enumerate(legs)}
    # full male-cns table (min 1 synapse): hop count only
    e = pd.read_parquet(REPO / "data/cache/male_cns_edges.parquet")
    ids = pd.Index(np.unique(np.concatenate([e.pre.to_numpy(), e.post.to_numpy()])))
    a = ids.get_indexer(e.pre.to_numpy()); b = ids.get_indexer(e.post.to_numpy())
    A = sp.csr_matrix((np.ones(len(a)), (a, b)), shape=(len(ids), len(ids)))
    s1 = ids.get_indexer(nn.bodyId.to_numpy()[src]); t1 = ids.get_indexer(nn.bodyId.to_numpy()[mn9])
    d1 = bfs(A.indptr, A.indices, s1[s1 >= 0], len(ids))
    res["hops_to_mn9_full_table_min1"] = int(d1[t1].min()) if (d1[t1] >= 0).any() else -1
    for w in (2, 3):
        k = e.weight.to_numpy() >= w
        A = sp.csr_matrix((np.ones(k.sum()), (a[k], b[k])), shape=(len(ids), len(ids)))
        dw = bfs(A.indptr, A.indices, s1[s1 >= 0], len(ids))
        res[f"hops_to_mn9_full_table_min{w}"] = int(dw[t1].min()) if (dw[t1] >= 0).any() else -1
    return res, df, db, on, src, mn9


def inject_vector(org, which: str) -> np.ndarray:
    from flyemu.extrasenses import TASTANTS
    ty = org.conn.neurons.type.fillna("untyped").astype(str).to_numpy()
    g = org.extra.gain
    conc = np.array([1.0 if t == "sugar" else 0.0 for t in TASTANTS])
    sat = conc / (conc + g["taste_K"])
    ch = org.extra.channels["taste_labellar" if which == "labellar" else "taste_leg"]
    mv = g["taste"] * (sat * ch.extra).sum(1)
    pick = np.isin(ty[ch.rows], ("LB3b", "LB3c") if which == "labellar" else SUGAR_LEG)
    if which == "fore":
        pick &= np.isin(ch.side, (0, 3))
    v = np.zeros(org.conn.n)
    v[ch.rows[pick]] = mv[pick]
    return v


def run(a) -> None:
    org = build(0.0 if a.inject else a.conc, a.seed)
    net = org.net
    n = org.conn.n
    inj = inject_vector(org, a.inject) if a.inject else 0.0
    if a.inject:
        print("inject", a.inject, "cells", int((inj > 0).sum()), "mV", float(inj[inj > 0].min()), float(inj.max()))
    steps = int(a.ms / org.timestep_ms); settle = int(a.settle_ms / org.timestep_ms)
    cnt = np.zeros(n); vmax = np.full(n, -np.inf, np.float32)
    for s in range(steps):
        obs = org.body.observe()
        spk = net.step(external_mv=org.sense(s, obs) + inj)
        if s >= settle:
            cnt[spk] += 1
            np.maximum(vmax, net.v, out=vmax)
        org.motor_step(spk)
    gap = np.broadcast_to(np.asarray(net.v_th - net.v_rest, np.float32), (n,))
    frac = (vmax - net.v_rest) / gap
    frac[cnt > 0] = 1.0                       # v resets on a spike, so peak v understates firing cells
    OUT.mkdir(parents=True, exist_ok=True)
    f = OUT / (f"run_inj_{a.inject}_s{a.seed}.npz" if a.inject else f"run_c{a.conc:g}_s{a.seed}.npz")
    np.savez_compressed(f, hz=cnt / ((a.ms - a.settle_ms) / 1e3), peak_frac=frac, ms=a.ms, settle_ms=a.settle_ms)
    print("saved", f)


def report(a) -> None:
    org = build(1.0, a.seed)
    res, df, db, on, src, mn9 = structure(org)
    ty = org.conn.neurons.type.fillna("untyped").astype(str).to_numpy()
    fs = OUT / f"run_c{a.conc:g}_s{a.seed}.npz"; f0 = OUT / f"run_c0_s{a.seed}.npz"
    if fs.exists() and f0.exists():
        S, C = np.load(fs), np.load(f0)
        up = S["hz"] > C["hz"] + 2.5         # 1 extra spike in a 300 ms window is 3.3 Hz
        res["dynamics"] = dict(
            conc_M=a.conc, criterion="rate with sugar > control + 2.5 Hz",
            mn9_hz=dict(sugar=S["hz"][mn9].round(1).tolist(), control=C["hz"][mn9].round(1).tolist(),
                        peak_frac_sugar=S["peak_frac"][mn9].round(3).tolist(),
                        peak_frac_control=C["peak_frac"][mn9].round(3).tolist()),
            shortest_path_layers=[], by_distance=[])
        for k in range(res["hops_to_mn9"] + 1):
            r = np.flatnonzero(on & (df == k))
            u = r[up[r]]
            res["dynamics"]["shortest_path_layers"].append(dict(
                k=k, n=int(len(r)), n_up=int(len(u)), up_types=pd.Series(ty[u]).value_counts().head(10).to_dict(),
                hz_sugar_mean=round(float(S["hz"][r].mean()), 2), hz_control_mean=round(float(C["hz"][r].mean()), 2),
                peak_frac_sugar_median=round(float(np.median(S["peak_frac"][r])), 3),
                peak_frac_control_median=round(float(np.median(C["peak_frac"][r])), 3)))
        for cl in res["cells"]:
            r = cl["row"]
            cl.update(hz_sugar=round(float(S["hz"][r]), 1), hz_control=round(float(C["hz"][r]), 1),
                      peak_frac_sugar=round(float(S["peak_frac"][r]), 3),
                      peak_frac_control=round(float(C["peak_frac"][r]), 3))
        g = S["hz"][src] - C["hz"][src]
        res["dynamics"]["grn_hz"] = dict(sugar_mean=round(float(S["hz"][src].mean()), 2),
                                         control_mean=round(float(C["hz"][src].mean()), 2),
                                         n_up=int((g > 2.5).sum()), n=int(len(src)))
        lg = np.array(res["grn_leg"])
        res["dynamics"]["grn_by_leg"] = {
            L: dict(n=int((lg == L).sum()), n_on_path=int((on[src] & (lg == L)).sum()),
                    hz_sugar_mean=round(float(S["hz"][src][lg == L].mean()), 1),
                    hz_on_path_mean=round(float(S["hz"][src][(lg == L) & on[src]].mean()), 1)
                    if (on[src] & (lg == L)).any() else None)
            for L in dict.fromkeys(lg)}
        for k in range(min(int(df.max()), 8) + 1):
            r = np.flatnonzero(df == k)
            u = r[up[r]]
            res["dynamics"]["by_distance"].append(dict(
                k=k, n=int(len(r)), n_up=int(len(u)), up_types=pd.Series(ty[u]).value_counts().head(10).to_dict()))
    f0 = OUT / f"run_c0_s{a.seed}.npz"
    for w in ("all", "fore", "labellar"):
        fi = OUT / f"run_inj_{w}_s{a.seed}.npz"
        if not (fi.exists() and f0.exists()):
            continue
        S, C = np.load(fi), np.load(f0)
        up = S["hz"] > C["hz"] + 2.5
        d = dict(mn9_hz=S["hz"][mn9].round(1).tolist(), mn9_peak_frac=S["peak_frac"][mn9].round(3).tolist(),
                 n_injected=int((inject_vector(org, w) > 0).sum()), layers=[])
        for k in range(res["hops_to_mn9"] + 1):
            r = np.flatnonzero(on & (df == k))
            u = r[up[r]]
            d["layers"].append(dict(k=k, n=int(len(r)), n_up=int(len(u)),
                                    up_types=pd.Series(ty[u]).value_counts().head(10).to_dict(),
                                    peak_frac_median=round(float(np.median(S["peak_frac"][r])), 3)))
        d["cells_up"] = [dict(layer=cl["layer"], type=cl["type"], bodyId=cl["bodyId"], sign=cl["sign"],
                              hz=round(float(S["hz"][cl["row"]]), 1), hz_control=round(float(C["hz"][cl["row"]]), 1))
                         for cl in res["cells"] if up[cl["row"]]]
        # MN9's direct presynaptic cells (any route), which fire more than in the control
        c = org.conn
        pre = np.repeat(np.arange(c.n), np.diff(c.indptr))
        for m in mn9:
            e = np.flatnonzero(c.indices == m)
            pu = pre[e][up[pre[e]]]
            d.setdefault("mn9_inputs_up", {})[org.conn.neurons.instance.iloc[m]] = [
                dict(type=ty[u], sign=int(np.sign(c.sign[u])), syn=int(c.weight_syn[e][pre[e] == u].sum()),
                     hz=round(float(S["hz"][u]), 1)) for u in pu]
        res.setdefault("inject", {})[w] = d
    out = OUT / f"trace_s{a.seed}.json"
    OUT.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(res, indent=1, default=str))
    print(json.dumps(res, indent=1, default=str))


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("mode", choices=("structure", "run", "report"))
    ap.add_argument("--conc", type=float, default=1.0)
    ap.add_argument("--seed", type=int, default=12)
    ap.add_argument("--ms", type=float, default=400.0)
    ap.add_argument("--settle-ms", type=float, default=100.0)
    ap.add_argument("--inject", choices=("all", "fore", "labellar"), default=None)
    a = ap.parse_args()
    if a.mode == "run":
        run(a)
    elif a.mode == "report":
        report(a)
    else:
        res = structure(build(1.0, a.seed))[0]
        OUT.mkdir(parents=True, exist_ok=True)
        (OUT / "structure.json").write_text(json.dumps(res, indent=1, default=str))
        print(json.dumps(res, indent=1, default=str))


if __name__ == "__main__":
    main()
