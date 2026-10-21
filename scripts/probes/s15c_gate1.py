"""s15c gate 1 (fly, 21 Oct; pre-registered DECISIONS 21 Oct 01:38 and addendum): single-cell checks of the
morphological walking cells (flyemu.morph) before any network run.

  (a) the custom solver against NEURON (6 cells: 2 core, 4 leg MN): somatic Rin, and the soma and spike-zone PSP
      peaks for 10 random EM input sites each, within 2%, dt 0.1 ms, backward Euler on both;
  (b) the isopotential limit (all 106 cells): at Ri 1e-3 Ohm cm, spikes off, the soma trace of a 1 s synaptic drive
      (and the cell's tonic drive, spread by membrane area) equals the point cell's within 0.05 mV;
  (c) somatic Rin of the T1 tibia flexors (Ti flexor MN + Acc. ti flexor MN): median inside Azevedo 2020 Fig 3E's
      class means (150-700 MOhm), and the cells' q10-q90 overlaps that range. Sensitivity corners reported.

Membrane: Cm 1 uF/cm2, Rm = the cell's point tau_m / Cm, Ri 200 Ohm cm, E_leak = the point v_leak
(runs/s15/morph/point_params.json from s15c_point_params.py). Synaptic current = point weight (mV) x the point
kernel x G_total (nS) (the isopotential-limit rule), here on one EM site per input.

    .venv/bin/python scripts/probes/s15c_gate1.py {a,b,c} --out runs/s15/morph/gate1_<x>.json
"""
from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "scripts" / "connectome"))
from flyemu import morph  # noqa: E402
import premotor_mn_geometry as pg  # noqa: E402

DT, CM, RI = 0.1, 1.0, 200.0
SYN = ROOT / "data" / "derived" / "walking_morph" / "syn_in.parquet"
PTS = ROOT / "runs" / "s15" / "morph" / "point_params.json"
FLEX = ("Ti flexor MN", "Acc. ti flexor MN")
AZEVEDO = (150.0, 700.0)


def load(bids=None, radius_scale: float = 1.0):
    """Cells, their EM input-site nodes, spike zones and point parameters."""
    pp = pd.DataFrame(json.loads(PTS.read_text())["cells"]).set_index("bodyId")
    if bids is not None:
        pp = pp.loc[list(bids)]
    soma = pd.read_parquet(ROOT / "data" / "cache" / "male_cns_extra2.parquet",
                           columns=["bodyId", "somaLocation"]).set_index("bodyId").somaLocation
    syn = pd.read_parquet(SYN, columns=["bodyId_post", "bodyId_pre", "x_post", "y_post", "z_post"])
    syn = syn[syn.bodyId_post.isin(pp.index)]
    out = []
    for b, r in pp.iterrows():
        s = pd.read_csv(pg.SKEL / f"{b}.csv.gz")
        if radius_scale != 1.0:
            s = s.assign(radius=s.radius * radius_scale)
        loc = soma.get(b)
        c = morph.build_cell(s, None if loc is None else np.asarray(loc, float) * morph.VOXEL_UM, int(b))
        sy = syn[syn.bodyId_post == b]
        sn = c.nearest(sy[["x_post", "y_post", "z_post"]].to_numpy(float) * morph.VOXEL_UM)
        z = morph.spike_zone(c, sn, r.cls)
        out.append(dict(b=int(b), row=r, cell=c, syn_nodes=sn, syn_pre=sy.bodyId_pre.to_numpy(), sz=z))
    return out


def cableset(cs, ri=RI, rm_scale=1.0, cm=CM):
    """One CableSet per call; Rm per cell = tau_m / Cm. Cells with different tau_m go in separate sets."""
    taus = sorted({float(c["row"].tau_m) for c in cs})
    sets = []
    for tau in taus:
        grp = [c for c in cs if float(c["row"].tau_m) == tau]
        rm = tau / cm * 1e3 * rm_scale                      # ms / (uF/cm2) = kOhm cm2 -> Ohm cm2
        S = morph.CableSet([c["cell"] for c in grp], rm, cm, ri, np.array([c["row"].v_leak for c in grp]), DT)
        sets.append((grp, S))
    return sets


def psp_ours(S, k, site, rec, i0_pa, tau_s, n_steps):
    """Peak depolarisation at rec nodes (cell k of S) for an exponential current at node `site`."""
    off = S.off[k]
    S.V = S.E.copy()
    ds = np.exp(-DT / tau_s)
    i = np.zeros_like(S.V)
    peak = np.zeros(len(rec))
    tr = np.zeros((n_steps, len(rec)))
    for n in range(n_steps):
        i[off + site] = i0_pa * ds ** n
        V = S.step(i)
        tr[n] = V[off + np.asarray(rec)] - S.E[off]
        peak = np.maximum(peak, tr[n])
    i[off + site] = 0.0
    return peak, tr


def neuron_cell(c, rm, ri, cm, e_leak):
    """NEURON model with the same compartments: one section per skeleton edge (nseg 1, frustum from its two
    nodes); the soma a sphere-area cylinder (L = diam = 2 r_root) with root edges attached at its centre and given
    no membrane (morph.build_cell: the sphere replaces them). Node v's voltage is sec[v](1)."""
    from neuron import h
    cell = c["cell"]
    soma = h.Section(name=f"soma_{c['b']}")
    soma.L = soma.diam = 2.0 * cell.rad[cell.root]
    secs = {cell.root: soma}
    for v in cell.order[1:]:
        p = int(cell.par[v])
        s = h.Section(name=f"e{v}_{c['b']}")
        a, b = cell.xyz[p], cell.xyz[v]
        if np.linalg.norm(b - a) < morph.DL_MIN_UM:
            b = a + np.array([morph.DL_MIN_UM, 0, 0])
        s.pt3dadd(*a, 2 * cell.rad[p])
        s.pt3dadd(*b, 2 * cell.rad[v])
        s.nseg = 1
        s.connect(secs[p](0.5 if p == cell.root else 1.0), 0.0)
        secs[int(v)] = s
    for s in secs.values():
        s.Ra = ri
        s.cm = cm
        s.insert("pas")
        s.g_pas = 1.0 / rm
        s.e_pas = e_leak
    for v in np.flatnonzero(cell.par == cell.root):
        secs[int(v)].cm = 0.0
        secs[int(v)].g_pas = 0.0

    def seg(v):
        return soma(0.5) if v == cell.root else secs[int(v)](1.0)
    return secs, seg


def gate_a(a):
    from neuron import h
    h.load_file("stdrun.hoc")
    pp = pd.DataFrame(json.loads(PTS.read_text())["cells"]).sort_values("bodyId")
    pick = []
    for t in ("INXXX466", "IN16B036", "Ti flexor MN", "Acc. ti flexor MN", "Tr extensor MN",
              "Sternal anterior rotator MN"):
        pick.append(int(pp[pp.type == t].bodyId.iloc[0]))
    cs = load(pick)
    rng = np.random.default_rng(1)
    res = []
    n_steps = int(60.0 / DT)
    for grp, S in cableset(cs):
        for k, c in enumerate(grp):
            cell, r = c["cell"], c["row"]
            rm = float(r.tau_m) / CM * 1e3
            soma_n, sz_n = cell.root, int(c["sz"]["mid"])
            rin = S.input_resistance_mohm(np.array([S.off[k] + soma_n]))[0]
            secs, seg = neuron_cell(c, rm, RI, CM, float(r.v_leak))
            imp = h.Impedance()
            imp.loc(seg(soma_n))
            imp.compute(0)
            rin_n = imp.input(seg(soma_n))
            g_tot = float(S.GL[S.off[k]:S.off[k + 1]].sum())
            i0 = 1.0 * g_tot                                 # 1 mV point weight -> pA
            sites = rng.choice(np.unique(c["syn_nodes"]), 10, replace=False)
            rows = []
            for site in sites:
                pk, tr = psp_ours(S, k, int(site), [soma_n, sz_n], i0, float(r.tau_s), n_steps)
                ic = h.IClamp(seg(int(site)))
                ic.delay, ic.dur = 0.0, 1e9
                amp = h.Vector(i0 * 1e-3 * np.exp(-DT / float(r.tau_s)) ** np.arange(n_steps + 2))
                tv = h.Vector(np.arange(n_steps + 2) * DT)
                amp.play(ic._ref_amp, tv, 0)
                vs, vz = h.Vector().record(seg(soma_n)._ref_v), h.Vector().record(seg(sz_n)._ref_v)
                h.dt, h.secondorder = DT, 0
                h.finitialize(float(r.v_leak))
                h.continuerun(n_steps * DT)
                ns = np.array(vs)[1:n_steps + 1] - float(r.v_leak)
                nz = np.array(vz)[1:n_steps + 1] - float(r.v_leak)
                lag = int(np.argmax(ns)) - int(np.argmax(tr[:, 0]))
                rows.append(dict(site=int(site), ours_soma=float(pk[0]), nrn_soma=float(ns.max()),
                                 ours_sz=float(pk[1]), nrn_sz=float(nz.max()), peak_lag_steps=lag,
                                 trace_maxdiff_soma=float(np.abs(ns - tr[:, 0]).max())))
                amp.play_remove()
                del ic
            d = pd.DataFrame(rows)
            rel = lambda x, y: float(np.max(np.abs(x / y - 1.0)))  # noqa: E731
            out = dict(bodyId=c["b"], type=r.type, n_nodes=cell.n, rin_ours=float(rin), rin_nrn=float(rin_n),
                       rin_rel=abs(rin / rin_n - 1.0), soma_peak_rel_max=rel(d.ours_soma, d.nrn_soma),
                       sz_peak_rel_max=rel(d.ours_sz, d.nrn_sz), sz=dict(mid=sz_n, fallback=c["sz"]["fallback"]),
                       sites=rows)
            out["pass"] = bool(max(out["rin_rel"], out["soma_peak_rel_max"], out["sz_peak_rel_max"]) <= 0.02)
            res.append(out)
            print(c["b"], r.type, cell.n, f"Rin {rin:.1f} vs {rin_n:.1f}", f"soma {out['soma_peak_rel_max']:.4f}",
                  f"sz {out['sz_peak_rel_max']:.4f}", "lag", sorted(set(d.peak_lag_steps)), "pass", out["pass"],
                  flush=True)
            for s in secs.values():
                h.delete_section(sec=s)
    return dict(gate="1a", tol=0.02, cells=res, passed=all(x["pass"] for x in res))


def gate_b(a):
    cs = load()
    rng = np.random.default_rng(2)
    T = int(1000.0 / DT)
    res = []
    for grp, S in cableset(cs, ri=1e-3):
        n = len(grp)
        tau_m = float(grp[0]["row"].tau_m)
        # per cell: 20 inputs, each one EM site's node drawn from the cell's sites, Poisson 20 Hz, weight +-U(0.5, 3) mV
        site = np.stack([rng.choice(c["syn_nodes"], 20) for c in grp]) + S.off[:-1, None]
        w = rng.uniform(0.5, 3.0, (n, 20)) * rng.choice([1.0, -1.0], (n, 20), p=[0.7, 0.3])
        ev = rng.random((T, n, 20)) < 20.0 * DT * 1e-3
        spont = np.array([float(c["row"].spont_mv) for c in grp])
        tau_s = np.array([float(c["row"].tau_s) for c in grp])
        e = np.array([float(c["row"].v_leak) for c in grp])
        gtot = np.bincount(S.cell_of, S.GL)
        share = S.GL / gtot[S.cell_of]                      # tonic drive by membrane area
        ds, dm = np.exp(-DT / tau_s), np.exp(-DT / tau_m)
        isyn = np.zeros((n, 20))
        vp = e.copy()
        S.V = S.E.copy()
        soma = np.array([c["cell"].root for c in grp]) + S.off[:-1]
        err = np.zeros(n)
        vmin, vmax = vp.copy(), vp.copy()
        t0 = time.time()
        for t in range(T):
            isyn = isyn * ds[:, None] + w * ev[t]
            drive = isyn.sum(1) + spont                     # point: mV
            vinf = e + drive
            vp = vinf + (vp - vinf) * dm
            i = share * (spont * gtot)[S.cell_of]
            np.add.at(i, site.ravel(), (isyn * gtot[:, None]).ravel())
            V = S.step(i)
            err = np.maximum(err, np.abs(V[soma] - vp))
            vmin, vmax = np.minimum(vmin, vp), np.maximum(vmax, vp)
        print(f"tau_m {tau_m}: {n} cells, {time.time() - t0:.0f} s, max |soma - point| {err.max():.4f} mV, "
              f"point V range {float((vmax - vmin).max()):.1f} mV", flush=True)
        for k, c in enumerate(grp):
            res.append(dict(bodyId=c["b"], type=c["row"].type, tau_m=tau_m, spont_mv=float(spont[k]),
                            max_abs_err_mv=float(err[k]), v_range_mv=float(vmax[k] - vmin[k])))
    mx = max(r["max_abs_err_mv"] for r in res)
    return dict(gate="1b", tol_mv=0.05, ri_ohm_cm=1e-3, cells=res, max_err_mv=mx, passed=bool(mx <= 0.05))


def rin_all(cs, **kw):
    out = {}
    for grp, S in cableset(cs, **kw):
        nodes = np.array([c["cell"].root for c in grp]) + S.off[:-1]
        sz = np.array([c["sz"]["mid"] for c in grp]) + S.off[:-1]
        r_s, r_z = S.input_resistance_mohm(nodes), S.input_resistance_mohm(sz)
        g = 1e3 / np.bincount(S.cell_of, S.GL)
        for k, c in enumerate(grp):
            out[c["b"]] = dict(type=c["row"].type, cls=c["row"].cls, rin_soma=float(r_s[k]), rin_sz=float(r_z[k]),
                               rin_iso=float(g[k]))
    return out


def gate_c(a):
    cs = load()
    corners = {"registered": {}, "ri_102": dict(ri=102.0), "ri_311": dict(ri=311.0),
               "gunay_rm26.3k_cm0.77": dict(rm_scale=26.3 / 20.0, cm=0.77)}
    res = {k: rin_all(cs, **kw) for k, kw in corners.items()}
    for sc in (0.8, 1.25):
        res[f"radius_x{sc}"] = rin_all(load(radius_scale=sc))
    summ = {}
    for k, d in res.items():
        df = pd.DataFrame(d).T
        f = df[df.type.isin(FLEX)].rin_soma.astype(float)
        summ[k] = dict(n=int(len(f)), median=float(f.median()), q10=float(f.quantile(0.1)),
                       q90=float(f.quantile(0.9)),
                       by_cls={c: dict(soma_median=float(g.rin_soma.astype(float).median()),
                                       sz_median=float(g.rin_sz.astype(float).median()),
                                       iso_median=float(g.rin_iso.astype(float).median()))
                               for c, g in df.groupby("cls")})
        print(k, {x: round(v, 1) if isinstance(v, float) else v for x, v in summ[k].items() if x != "by_cls"},
              summ[k]["by_cls"])
    r = summ["registered"]
    ok = AZEVEDO[0] <= r["median"] <= AZEVEDO[1] and r["q10"] <= AZEVEDO[1] and r["q90"] >= AZEVEDO[0]
    return dict(gate="1c", range_mohm=AZEVEDO, summary=summ, cells=res["registered"], passed=bool(ok))


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("part", choices=["a", "b", "c"])
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    out = {"a": gate_a, "b": gate_b, "c": gate_c}[a.part](a)
    Path(a.out).write_text(json.dumps(out, indent=1, default=float))
    print("PASSED" if out["passed"] else "FAILED", a.part)


if __name__ == "__main__":
    main()
