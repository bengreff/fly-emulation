"""N30 option B (fly2, 21 Oct; pre-registered DECISIONS 21 Oct 00:07): class MN axon share q and soma-axon
coupling rho from the male-CNS skeletons of the DLMn and their PSI synapses.

Per cell (DLMn a, b set the class value; DLMn c-f are reported):
  axon base     walking from the PSI contact nearest the soma toward the soma, the first branch point
                whose off-path subtrees hold >= FRAC of the cell's cable (FRAC 0.05; 0.01 and 0.20 reported)
  contact site  the node of the synapse-weighted median PSI contact (by path distance from the soma)
  R_ax          Ri * sum(dl / (pi r1 r2)) over the skeleton edges from the axon base to the contact site
  rho           Rin / R_ax, Rin 102 MOhm (MN5, Fayyazuddin 2006, measured); Ri 102 / 200 / 311 Ohm cm
  q             A_axon / A_total: frustum lateral areas, the soma a sphere of the root radius; A_axon is the
                subtree distal to the axon base that holds the PSI contacts (inside the volume)
  rho*(q)       where the passive pair's axon peak reaches the 7 mV gap with the soma peak at the measured
                4.71 mV (the model's pair update: tau_m 20, tau_s 5, dt 0.1 ms; Network.psp_peak_per_mv_axon)

Outputs: data/derived/mn_axon_geometry.csv (one row per cell and FRAC), data/derived/mn_axon_geometry.json
(class values and the decision), data/derived/mn_axon_geometry_skel/<bodyId>.csv.gz (the fetched skeletons and
PSI synapses, kept as raw data), docs/media/s21_fly2_mn5_geometry.png.

    .venv/bin/python scripts/connectome/mn_axon_geometry.py [--offline]
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))
from fetch_male_cns import DATASET, TOKEN  # noqa: E402

VOXEL_UM = 0.008
RIN_MOHM = 102.0                       # MN5 whole-cell input resistance (Fayyazuddin 2006), measured
RI_OHM_CM = {"lo": 102.0, "mid": 200.0, "hi": 311.0}   # Gouwens & Wilson 2009 fitted range; 200 as registered
CM_PF = {"fayyazuddin": 43.0, "kadas": 127.0}          # MN5 whole-cell capacitance, measured
GAP_MV, PSP_MV = 7.0, 4.71
FRACS = (0.05, 0.01, 0.20)
OUT = ROOT / "data" / "derived"
SKEL = OUT / "mn_axon_geometry_skel"
TYPES = ("DLMn a, b", "DLMn c-f")


def pair_peaks(q: float, rho: float, tau_m: float = 20.0, tau_s: float = 5.0, dt: float = 0.1):
    """Soma and axon peaks of the passive pair for a unit input on the axon (Network.psp_peak_per_mv_axon's
    update: kappa_a = rho / q, kappa_s = rho / (1 - q), start-of-step voltages)."""
    ka, ks = rho / q, rho / (1.0 - q)
    dv, da, ds = np.exp(-dt / tau_m), np.exp(-dt * (1.0 + ka) / tau_m), np.exp(-dt / tau_s)
    i, va, vs, ps, pa = 1.0, 0.0, 0.0, 0.0, 0.0
    for _ in range(int(np.ceil(200.0 / dt))):
        vinf = (i + ka * vs) / (1.0 + ka)
        va, vs = vinf + (va - vinf) * da, vs * dv + ks * (va - vs) * (1.0 - dv)
        ps, pa = max(ps, vs), max(pa, va)
        i *= ds
    return ps, pa


def rho_star(q: float) -> float:
    """rho at which the axon peak reaches GAP_MV when the soma peak is PSP_MV (the axon/soma peak ratio falls
    with rho)."""
    lo, hi = np.log(0.01), np.log(100.0)
    for _ in range(60):
        mid = 0.5 * (lo + hi)
        ps, pa = pair_peaks(q, float(np.exp(mid)))
        lo, hi = (mid, hi) if PSP_MV * pa / ps >= GAP_MV else (lo, mid)
    return float(np.exp(0.5 * (lo + hi)))


def fetch(bids: list[int], psi: list[int]) -> None:
    from neuprint import Client, NeuronCriteria as NC, fetch_synapse_connections
    c = Client("neuprint.janelia.org", dataset=DATASET, token=TOKEN.read_text().strip())
    SKEL.mkdir(parents=True, exist_ok=True)
    for b in bids:
        s = c.fetch_skeleton(b, format="pandas", heal=True)
        s.to_csv(SKEL / f"{b}.csv.gz", index=False)
        syn = fetch_synapse_connections(NC(bodyId=psi), NC(bodyId=b), client=c)
        syn.to_csv(SKEL / f"{b}_psi.csv.gz", index=False)
        print(b, len(s), "nodes", len(syn), "PSI synapses", flush=True)


def tree(s: pd.DataFrame, soma_um: np.ndarray | None):
    """Parent array re-rooted at the node nearest the soma, edge lengths and radii in um."""
    import scipy.sparse as sp
    from scipy.sparse.csgraph import breadth_first_order
    s = s.reset_index(drop=True)
    idx = {r: i for i, r in enumerate(s.rowId.to_numpy())}
    par0 = np.array([idx.get(l, -1) for l in s.link.to_numpy()])
    xyz = s[["x", "y", "z"]].to_numpy(float) * VOXEL_UM
    rad = s.radius.to_numpy(float) * VOXEL_UM
    ch = np.flatnonzero(par0 >= 0)
    n = len(s)
    g = sp.coo_matrix((np.ones(ch.size), (ch, par0[ch])), shape=(n, n)).tocsr()
    root = int(np.argmin(np.linalg.norm(xyz - soma_um, axis=1))) if soma_um is not None else 0
    order, pred = breadth_first_order(g, root, directed=False, return_predecessors=True)
    if order.size != n:
        raise ValueError(f"skeleton has {n - order.size} nodes outside the root component")
    par = np.where(pred < 0, -1, pred)
    par[root] = -1
    return xyz, rad, par, root, order


def reduce(bid: int, s: pd.DataFrame, soma_um, syn: pd.DataFrame, frac: float) -> dict:
    from scipy.spatial import cKDTree
    xyz, rad, par, root, order = tree(s, soma_um)
    n = len(xyz)
    has = par >= 0
    dl = np.zeros(n)
    dl[has] = np.linalg.norm(xyz[has] - xyz[par[has]], axis=1)
    r1, r2 = rad, np.where(has, rad[np.maximum(par, 0)], rad)
    n_zero_r = int((rad <= 0).sum())
    r1c, r2c = np.maximum(r1, 0.01), np.maximum(r2, 0.01)
    area_e = np.pi * (r1c + r2c) * np.sqrt(dl ** 2 + (r1c - r2c) ** 2)   # edge node -> parent
    area_e[~has] = 0.0
    at_root = has & (par == root)
    area_e[at_root] = 0.0              # the soma sphere replaces the edges touching it
    rax_e = np.where(has, dl / (np.pi * r1c * r2c), 0.0)   # um / um^2, times Ri later
    cable = np.zeros(n)
    area = np.zeros(n)
    for v in order[::-1]:              # children before parents
        cable[v] += dl[v]
        area[v] += area_e[v]
        if par[v] >= 0:
            cable[par[v]] += cable[v]
            area[par[v]] += area[v]
    a_total = area[root] + 4.0 * np.pi * rad[root] ** 2
    dist = np.zeros(n)
    for v in order[1:]:
        dist[v] = dist[par[v]] + dl[v]
    _, near = cKDTree(xyz).query(syn[["x_post", "y_post", "z_post"]].to_numpy(float) * VOXEL_UM)
    d_syn = dist[near]
    n0 = int(near[np.argmin(d_syn)])
    kids = [[] for _ in range(n)]
    for v in np.flatnonzero(has):
        kids[par[v]].append(v)
    prev, p, base, on_path_child = n0, par[n0], None, None
    while p >= 0:
        off = sum(cable[k] for k in kids[p] if k != prev)
        if off >= frac * cable[root]:
            base, on_path_child = p, prev
            break
        prev, p = p, par[p]
    if base is None:
        raise ValueError(f"{bid}: no branch point with {frac:.0%} of the cable off the path")
    # PSI contacts distal to the base (in the on-path child's subtree)
    inside = np.zeros(n, bool)
    inside[on_path_child] = True
    for v in order:
        if par[v] >= 0 and inside[par[v]] and v != on_path_child:
            inside[v] = True
    frac_syn_distal = float(inside[near].mean())
    srt = np.argsort(d_syn)
    site = int(near[srt[len(srt) // 2]])
    path, v = [], site
    while v != base:
        path.append(v)
        v = par[v]
        if v < 0:
            raise ValueError(f"{bid}: the median PSI contact is not distal to the axon base")
    path = np.array(path)
    ell = float(dl[path].sum())
    rsum = float(rax_e[path].sum())            # um^-1
    a_axon = float(area[on_path_child])
    q = a_axon / a_total
    out = {"bodyId": bid, "frac": frac, "n_nodes": n, "n_zero_radius": n_zero_r,
           "cable_um": float(cable[root]), "root_radius_um": float(rad[root]),
           "n_psi_syn": int(len(syn)), "frac_psi_distal_to_base": frac_syn_distal,
           "base_dist_um": float(dist[base]), "site_dist_um": float(dist[site]),
           "psi_dist_p10_um": float(np.percentile(d_syn, 10)), "psi_dist_p90_um": float(np.percentile(d_syn, 90)),
           "ell_um": ell, "path_radius_median_um": float(np.median(rad[path])),
           "d_equiv_um": float(2.0 * np.sqrt(ell / (np.pi * rsum))),
           "a_axon_um2": a_axon, "a_total_um2": float(a_total), "q": q,
           "axon_cable_um": float(cable[on_path_child])}
    for k, c_pf in CM_PF.items():
        out[f"q_cm_{k}"] = a_axon / (c_pf * 100.0)   # 1 uF/cm2: 1 pF per 100 um2
    for k, ri in RI_OHM_CM.items():
        r_ax_ohm = ri * 1e4 * rsum                   # Ohm cm * um / um^2 = 1e4 Ohm
        out[f"gc_nS_{k}"] = 1e9 / r_ax_ohm
        out[f"rho_{k}"] = RIN_MOHM * 1e6 / r_ax_ohm
    out["_plot"] = {"xyz": xyz, "par": par, "base": base, "site": site, "near": near, "path": path,
                    "inside": inside}
    return out


def figure(rows: list[dict], path: Path) -> None:
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    rows = [r for r in rows if r["frac"] == FRACS[0]]
    fig, axs = plt.subplots(2, len(rows), figsize=(4.2 * len(rows), 8), squeeze=False)
    for j, r in enumerate(rows):
        p = r["_plot"]
        xyz, par = p["xyz"], p["par"]
        for i, (a, b) in enumerate(((0, 1), (0, 2))):
            ax = axs[i, j]
            e = np.flatnonzero(par >= 0)
            seg = np.stack([xyz[e][:, [a, b]], xyz[par[e]][:, [a, b]]], 1)
            from matplotlib.collections import LineCollection
            col = np.where(p["inside"][e], "#c0392b", "#7f8c8d")
            ax.add_collection(LineCollection(seg, colors=col, linewidths=0.5))
            pth = p["path"]
            ax.plot(xyz[pth, a], xyz[pth, b], color="#2471a3", lw=2.0, label="base to contact site")
            ax.scatter(xyz[p["near"], a], xyz[p["near"], b], s=4, color="#f39c12", label="PSI synapses", zorder=3)
            ax.scatter(*xyz[p["base"], [a, b]], s=60, marker="s", color="k", label="axon base", zorder=4)
            ax.scatter(*xyz[p["site"], [a, b]], s=60, marker="*", color="#2471a3", label="median contact", zorder=4)
            ax.set_aspect("equal")
            ax.autoscale()
            ax.set_xlabel("xyz"[a] + " (um)")
            ax.set_ylabel("xyz"[b] + " (um)")
            if i == 0:
                ax.set_title(f"{r['type']} {r['bodyId']}\nl {r['ell_um']:.0f} um, d_eq {r['d_equiv_um']:.2f} um, "
                             f"q {r['q']:.3f}, rho(Ri 200) {r['rho_mid']:.2f}", fontsize=9)
            if i == 0 and j == 0:
                ax.legend(fontsize=7, loc="best")
    fig.suptitle("N30 option B: DLMn skeletons (male-cns v1.0); red = axon compartment (distal to the axon base)",
                 fontsize=10)
    fig.tight_layout()
    fig.savefig(path, dpi=130)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--offline", action="store_true", help="use the saved skeletons and synapses")
    a = ap.parse_args()
    n = pd.read_parquet(ROOT / "data" / "cache" / "male_cns_neurons.parquet")
    cells = n[n.type.isin(TYPES)][["bodyId", "type", "instance"]].sort_values(["type", "instance"])
    psi = n[n.type == "PSI"].bodyId.astype(int).tolist()
    bids = cells.bodyId.astype(int).tolist()
    if not a.offline:
        fetch(bids, psi)
    soma = pd.read_parquet(ROOT / "data" / "cache" / "male_cns_extra2.parquet",
                           columns=["bodyId", "somaLocation"]).set_index("bodyId").somaLocation
    rows = []
    for c in cells.itertuples():
        s = pd.read_csv(SKEL / f"{c.bodyId}.csv.gz")
        syn = pd.read_csv(SKEL / f"{c.bodyId}_psi.csv.gz")
        loc = soma.get(c.bodyId)
        soma_um = None if loc is None else np.asarray(loc, float) * VOXEL_UM
        if not len(syn):
            print(f"{c.bodyId} {c.type}: no PSI synapses", flush=True)
            continue
        for f in FRACS:
            try:
                r = reduce(int(c.bodyId), s, soma_um, syn, f)
            except ValueError as e:      # a sensitivity FRAC with no qualifying branch point
                print(f"{c.type} {c.instance}: {e}", flush=True)
                continue
            r.update(type=c.type, instance=c.instance)
            r["rho_star"] = rho_star(r["q"])
            r["shrink_factor_to_cross"] = float(np.sqrt(r["rho_star"] / r["rho_mid"]))
            rows.append(r)
    df = pd.DataFrame([{k: v for k, v in r.items() if k != "_plot"} for r in rows])
    df.to_csv(OUT / "mn_axon_geometry.csv", index=False, float_format="%.4g")
    main_ = df[(df.frac == FRACS[0]) & (df.type == "DLMn a, b")]
    q = float(main_.q.mean())
    rs = rho_star(q)
    rho = {k: float(main_[f"rho_{k}"].mean()) for k in RI_OHM_CM}
    below = [rho[k] < rs for k in RI_OHM_CM]
    verdict = "PASS" if all(below) else "FAIL" if not any(below) else "UNDECIDED"
    summ = {"registration": "DECISIONS 21 Oct 00:07", "dataset": DATASET, "cells": main_.bodyId.tolist(),
            "q": q, "q_cm": {k: float(main_[f"q_cm_{k}"].mean()) for k in CM_PF}, "rho": rho,
            "rho_star": rs, "verdict": verdict, "Rin_MOhm": RIN_MOHM, "Ri_ohm_cm": RI_OHM_CM,
            "ell_um": float(main_.ell_um.mean()), "d_equiv_um": float(main_.d_equiv_um.mean())}
    (OUT / "mn_axon_geometry.json").write_text(json.dumps(summ, indent=1))
    figure(rows, ROOT / "docs" / "media" / "s21_fly2_mn5_geometry.png")
    pd.set_option("display.width", 250)
    print(df[["type", "instance", "bodyId", "frac", "n_psi_syn", "frac_psi_distal_to_base", "base_dist_um",
              "site_dist_um", "ell_um", "path_radius_median_um", "d_equiv_um", "q", "q_cm_fayyazuddin",
              "q_cm_kadas", "rho_lo", "rho_mid", "rho_hi", "rho_star", "shrink_factor_to_cross"]].to_string())
    print(json.dumps(summ, indent=1))


if __name__ == "__main__":
    main()
