"""s15c gate 2 (fly, 21 Oct; pre-registered DECISIONS 21 Oct 01:38, operational form 02:17): unitary hand-off of the
morphological walking cells, every network edge onto the 106 T1 cells.

The cells are passive and linear with current synapses, so the s4b kicked-minus-control PSP equals the single-cell
response at rest. By reciprocity one run per recording node (a unit exponential current injected there) gives every
input site's transfer to that node. Each edge (m10f0, min_synapses 5, final lif.Network.w in mV) carries current
w x G_total split equally over its EM sites; an edge with no EM site is spread over all of the cell's input sites.
Isopotential reference: the same edge on a one-compartment cell, same integrator (backward Euler, dt 0.1 ms).

Spike zones: 'arbor_base' (primary, s15b split + 20 um, all cells) and 'trunk_end' (leg-MN sensitivity).
Corners (primary site only, reported): Ri 102 / 311 Ohm cm, radius x0.8 / x1.25.

    .venv/bin/python scripts/probes/s15c_gate2.py --out runs/s15/morph/gate2.json
"""
from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd
import scipy.sparse as sp

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "scripts" / "probes"))
sys.path.insert(0, str(ROOT / "scripts" / "connectome"))
from flyemu import lif, morph, percell  # noqa: E402
from flyemu.gpu.equivalence import build_brain  # noqa: E402
import premotor_mn_geometry as pg  # noqa: E402
import s15c_gate1 as g1  # noqa: E402

DT, WIN_MS = 0.1, 60.0
E2, I1 = "INXXX466", "IN16B036"


def network_edges(profile: str) -> pd.DataFrame:
    """Every edge onto the 106 cells in the built point network (final weights)."""
    reg, conn, params, _ = build_brain({}, profile=profile, min_synapses=5)
    net = lif.Network(conn, params, DT, rng=np.random.default_rng(1))
    n = conn.n
    W = sp.csr_matrix((net.w.astype(np.float64), conn.indices, conn.indptr), shape=(n, n)).tocsc()
    C = sp.csr_matrix((conn.weight_syn.astype(np.float64), conn.indices, conn.indptr), shape=(n, n)).tocsc()
    pp = pd.DataFrame(json.loads(g1.PTS.read_text())["cells"])
    bid = conn.neurons.bodyId.to_numpy()
    typ = conn.neurons.type.fillna("").to_numpy()
    leg = percell.leg_motor_mask(conn)
    core_idx = set(pp.model_idx[pp.cls == "core_premotor"].astype(int))
    rows = []
    for _, r in pp.iterrows():
        j = int(r.model_idx)
        lo, hi = W.indptr[j], W.indptr[j + 1]
        for i, w, c in zip(W.indices[lo:hi], W.data[lo:hi], C.data[lo:hi]):
            rows.append(dict(post=int(r.bodyId), post_type=r.type, post_cls=r.cls, pre=int(bid[i]), pre_type=typ[i],
                             pre_core=i in core_idx, pre_leg=bool(leg[i]), w_mv=float(w), synapses=float(c)))
    print(f"{len(rows)} edges onto {len(pp)} cells; w==0: {sum(r['w_mv'] == 0 for r in rows)}", flush=True)
    return pd.DataFrame(rows)


def iso_peak(tau_m: float, tau_s: float) -> float:
    """Peak of a unit-weight PSP in one compartment, backward Euler as the cable solver."""
    v, best, a = 0.0, 0.0, DT / tau_m
    for n in range(int(WIN_MS / DT)):
        v = (v + a * np.exp(-DT / tau_s) ** n) / (1.0 + a)
        best = max(best, v)
    return best


def edge_peaks(cs, edges: pd.DataFrame, rec_kind: str, ri: float) -> np.ndarray:
    """Peak |PSP| per spike (mV) of every edge at each cell's recording node ('soma' or a spike-zone kind)."""
    out = np.full(len(edges), np.nan)
    for grp, S in g1.cableset(cs, ri=ri):
        gtot = S.g_total_ns()
        ri_, ci_, vi_, eid = [], [], [], []
        rec = np.zeros(len(grp), np.int64)
        for k, c in enumerate(grp):
            cell = c["cell"]
            kind = rec_kind if c["row"].cls == "leg_MN" else "arbor_base"    # core keeps its registered site
            rec[k] = cell.root if rec_kind == "soma" else morph.spike_zone(cell, c["syn_nodes"], kind)["mid"]
            e = edges[edges.post == c["b"]]
            for ix, pre, w in zip(e.index, e.pre, e.w_mv):
                sites = c["syn_nodes"][c["syn_pre"] == pre]
                if sites.size == 0:
                    sites = c["syn_nodes"]
                ri_.append(np.full(sites.size, len(eid)))
                ci_.append(sites + S.off[k])
                vi_.append(np.full(sites.size, abs(w) * gtot[k] / sites.size))
                eid.append(ix)
        M = sp.csr_matrix((np.concatenate(vi_), (np.concatenate(ri_), np.concatenate(ci_))),
                          shape=(len(eid), len(S.E)))
        tau_s = np.array([float(c["row"].tau_s) for c in grp])
        ds = np.exp(-DT / tau_s)
        S.V = S.E.copy()
        i = np.zeros_like(S.V)
        peak = np.zeros(len(eid))
        for n in range(int(WIN_MS / DT)):
            i[S.off[:-1] + rec] = ds ** n                 # 1 pA at t = 0, decaying with tau_s
            V = S.step(i)
            peak = np.maximum(peak, M @ (V - S.E))
        out[np.array(eid)] = peak
    return out


def summarise(e: pd.DataFrame, col: str) -> dict:
    g = e[col].to_numpy()
    wt = e.w_mv.abs().to_numpy()
    if g.size == 0:
        return dict(n=0)
    return dict(n=int(g.size), wmean=float(np.sum(g * wt) / np.sum(wt)), median=float(np.median(g)),
                q10=float(np.quantile(g, .1)), q90=float(np.quantile(g, .9)), max=float(g.max()))


def groups(e: pd.DataFrame) -> dict:
    mn, core = e.post_cls == "leg_MN", e.post_cls == "core_premotor"
    return {"core_to_legMN": e[e.pre_core & mn], "E2_to_I1": e[(e.pre_type == E2) & (e.post_type == I1)],
            "legMN_exc": e[mn & (e.w_mv > 0)], "legMN_inh": e[mn & (e.w_mv < 0)],
            "core_exc": e[core & (e.w_mv > 0)], "core_inh": e[core & (e.w_mv < 0)]}


def gains(e: pd.DataFrame, col: str) -> dict:
    gr = {k: summarise(v, col) for k, v in groups(e).items()}
    ratio = {t: gr[f"{t}_inh"]["wmean"] / gr[f"{t}_exc"]["wmean"] for t in ("legMN", "core")}
    return dict(groups=gr, inh_exc_ratio=ratio)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--profile", default="m10f0")
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    t0 = time.time()
    edges = network_edges(a.profile)
    edges = edges[edges.w_mv != 0].reset_index(drop=True)
    cs = g1.load()
    have = {c["b"]: set(np.unique(c["syn_pre"]).tolist()) for c in cs}
    edges["em_site"] = [p in have[q] for p, q in zip(edges.pre, edges.post)]
    pts = pd.DataFrame(json.loads(g1.PTS.read_text())["cells"]).set_index("bodyId")
    edges["iso"] = [abs(w) * iso_peak(float(pts.tau_m[q]), float(pts.tau_s[q])) for w, q in zip(edges.w_mv, edges.post)]
    for kind in ("soma", "arbor_base", "trunk_end"):
        edges[f"pk_{kind}"] = edge_peaks(cs, edges, kind, g1.RI)
        edges[f"g_{kind}"] = edges[f"pk_{kind}"] / edges.iso
        print(f"{kind} done {time.time() - t0:.0f} s", flush=True)
    corners = {}
    for name, ri, rs in (("ri102", 102.0, 1.0), ("ri311", 311.0, 1.0), ("rad0.8", g1.RI, 0.8), ("rad1.25", g1.RI, 1.25)):
        cc = cs if rs == 1.0 else g1.load(radius_scale=rs)
        edges[f"g_ab_{name}"] = edge_peaks(cc, edges, "arbor_base", ri) / edges.iso
        corners[name] = gains(edges, f"g_ab_{name}")
        print(f"corner {name} done {time.time() - t0:.0f} s", flush=True)

    prim = gains(edges, "g_arbor_base")
    gr = prim["groups"]
    stop = bool(gr["core_to_legMN"]["wmean"] <= 2.0 and gr["E2_to_I1"]["wmean"] <= 2.0
                and all(0.8 <= r <= 1.25 for r in prim["inh_exc_ratio"].values()))
    adm = {}
    for t, m in (("legMN", (edges.post_cls == "leg_MN")), ("core", (edges.post_cls == "core_premotor"))):
        x = edges[m & (edges.w_mv > 0) & ~edges.pre_leg]
        per_syn, per_spk = (x.pk_soma / x.synapses).to_numpy(), x.pk_soma.to_numpy()
        adm[t] = dict(n=int(len(x)), soma_mv_per_syn_median=float(np.median(per_syn)),
                      soma_psp_q90=float(np.quantile(per_spk, .9)),
                      passed=bool(np.median(per_syn) <= 0.3 and 0.4 <= np.quantile(per_spk, .9) <= 10.0))
    e12 = edges[(edges.pre_type.isin([E2, "IN17A001"])) & (edges.post_cls == "leg_MN")]
    e2i1 = edges[(edges.pre_type == E2) & (edges.post_type == I1)]
    gap = dict(E1E2_to_legMN_sz_mv=dict(n=int(len(e12)), median=float(e12.pk_arbor_base.median()),
                                         max=float(e12.pk_arbor_base.max())),
               E2_to_I1_sz_mv=e2i1[["pre", "post", "synapses", "w_mv", "iso", "pk_soma", "pk_arbor_base",
                                    "pk_trunk_end"]].round(4).to_dict("records"))
    no_site = float(edges.w_mv.abs()[~edges.em_site].sum() / edges.w_mv.abs().sum())
    res = dict(gate="2", profile=a.profile, primary_site="arbor_base", edges=int(len(edges)),
               weight_share_no_em_site=no_site, admissibility=adm, primary=prim, soma=gains(edges, "g_soma"),
               trunk_end=gains(edges, "g_trunk_end"), corners=corners, gap_7mv_context=gap, stop_rule_applies=stop,
               runtime_s=round(time.time() - t0))
    Path(a.out).write_text(json.dumps(res, indent=1))
    edges.to_csv(Path(a.out).with_suffix(".edges.csv.gz"), index=False)
    print(json.dumps(dict(adm=adm, primary=prim, trunk_end=gains(edges, "g_trunk_end")["inh_exc_ratio"],
                          stop=stop, no_site=no_site), indent=1))


if __name__ == "__main__":
    main()
