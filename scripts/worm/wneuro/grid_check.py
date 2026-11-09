"""wneuro Open 7, the pool grid against the exact 1D solution (written Mon 9 Nov 2026 01:00 CST, before running).

Question: does pc_grid=bins (pc_bin_um 15) solve neuromod's own transport law, dc/dt = D d2c/dy2 - k c + J / A with
reflecting ends, and how far does the four-compartment form (pc_grid=four) sit from it near a source?

Method. The template worm's neuromod Mech (ledger values, the stand-in brain: every neuron of the atlas, no NEURON),
peptides off, monoamines on. Its own pool object is stepped exactly as Mech.step steps it (N = (N + src dt) exp(-k dt),
then mix(dt)), dt 10 ms, for 12 / k (steady state to e^-12), with one constant source J = 1e4 molecules/s in the bin
holding the source's soma y and first-order loss k only (no uptake, no release law: the test is the transport).
Exact reference: the 1D Green's function on the same domain [first neuron soma y, last], reflecting ends,
G(y, s) = cosh(kap (min(y,s) - y0)) cosh(kap (y1 - max(y,s))) / (A D kap sinh(kap L)), kap = sqrt(k / D), with the
source spread uniformly over the source bin of the bins grid (what the representation says about where the release
is), averaged over each bin (Gauss-Legendre, 40 points per bin in y and s).

Cases (D, k at the template; A = pc_cross_section_um2 400):
  vulva_5ht  5-HT, source at HSNL's soma, k = 1 / ma_degrade_tau_s (5 s): lambda 54.8 um (derived)
  head_5ht   5-HT, source at NSML's soma, k = 1 / 1.7 s (MOD-5's effective lifetime in the head, item 6): 31.9 um
  tail_pep   a peptide, source at DVB's soma, D 50, k = 1 / 100 s + 0.001: 67.4 um

Bars (written before running):
  1. bins: in every case, max over bins whose exact mean is >= 1% of the peak bin's of |FV / exact - 1| <= 0.05.
  2. four (expected to fail, the defect): the four-compartment value at the source's compartment divided by the
     exact mean over the source bin of the bins grid (15 um around the source) is reported; the derived bound says
     dilution up to 1.9-2.5x. Not a pass/fail bar: it measures the defect.
  3. conservation, both grids: total molecules at steady state equal J / k within 1e-6 relative.
Falsifier for "bins fixes the representation": bar 1 fails in any case.

Result of the first run (01:01, measured): bar 1 FAILED at 15 um in both 5-HT cases (max error 0.075 vulva, 0.076
head) and passed for the peptide (0.036); every failing bin is the source bin (all other bins within 0.015, the
diagnostic /tmp run). Bar 3 FAILED by 1e-3 in all cases, both grids identically (0.998994 at k 0.2): the time step's
own steady state, J dt / (e^(k dt) - 1) = (J / k)(1 - k dt / 2 + ...), not the grid; the bar's prediction was wrong.
Addendum (01:06 CST, after that run, before the next): the source bin's error is first order in h / lambda (a source
spread over one well-mixed bin; derived bound about h / (3 lambda)). So pc_bin_um is chosen by convergence, not
argued: run bins of 15, 8, 4 and 2 um (argv: --conv), report the source-bin error and the maximum error per case, and
set the template to the largest of these at which bar 1 (unchanged, 5%) passes in all three cases. Bar 3 is re-scored
against the scheme's own steady state J dt / (e^(k dt) - 1), within 1e-6 (bar 3b), and reported as failed as written.

Usage: python grid_check.py [--conv] -> runs/worm/wneuro/grid_check.json (and grid_check.png)
"""
from __future__ import annotations

import json
from pathlib import Path
from types import SimpleNamespace

import numpy as np

from wormemu.brain_structure import load_structure
from wormemu.mech import neuromod as N

ROOT = Path(__file__).resolve().parents[3]
OUT = ROOT / "runs" / "worm" / "wneuro"


def mech(grid):
    st = load_structure()
    neurons = [n for n, k in zip(st.names, st.kind) if k == "neuron"]
    brain = SimpleNamespace(st=st, cell_names=neurons, is_muscle=np.zeros(len(neurons), bool),
                            spec=SimpleNamespace(values={}), layers=None)
    T = {s.id: s.template for s in N.SPECS}
    return N.Mech(brain, T, {"peptides": "off", "monoamines": "compartments", "pc_grid": grid}), T


def fv(m, D, k, cell, J=1e4, dt=0.01):
    """Steady state of one ligand on the Mech's own grid (a fresh _Pool with D, built as Mech._pool builds it)."""
    comp, pool = m._pool(False, 1, D - float(m.p["pc_stirring_um2_per_s"]))
    j = comp[m.names.index(cell)]
    src = np.zeros_like(pool.N)
    src[0, j] = J
    for _ in range(int(round(12.0 / k / dt))):
        pool.N = (pool.N + src * dt) * np.exp(-dt * k)
        pool.mix(dt)
    return pool, j


def exact(edges, D, k, A, s1, s2, J=1e4, nq=40):
    y0, y1 = edges[0], edges[-1]
    L, kap = y1 - y0, np.sqrt(k / D)
    x, w = np.polynomial.legendre.leggauss(nq)
    s = (s1 + s2) / 2 + (s2 - s1) / 2 * x
    ws = w / 2                                                   # mean over the source bin
    out = []
    for a, b in zip(edges[:-1], edges[1:]):
        y = (a + b) / 2 + (b - a) / 2 * x
        lo, hi = np.minimum(y[:, None], s[None, :]), np.maximum(y[:, None], s[None, :])
        G = np.cosh(kap * (lo - y0)) * np.cosh(kap * (y1 - hi)) / (A * D * kap * np.sinh(kap * L))
        out.append(float((w / 2) @ G @ ws) * J)                  # molecules per um3
    return np.array(out)


def conv():
    """Source-bin and maximum error against the exact reference, per case and bin size (the addendum)."""
    out = {}
    for h in (15.0, 8.0, 4.0, 2.0):
        st = load_structure()
        neurons = [n for n, k in zip(st.names, st.kind) if k == "neuron"]
        brain = SimpleNamespace(st=st, cell_names=neurons, is_muscle=np.zeros(len(neurons), bool),
                                spec=SimpleNamespace(values={}), layers=None)
        T = {s.id: s.template for s in N.SPECS}
        T["pc_bin_um"] = h
        m = N.Mech(brain, T, {"peptides": "off", "monoamines": "compartments", "pc_grid": "bins"})
        D5 = float(T["ma_diffusion_um2_per_s"])
        cases = {"vulva_5ht": (D5, 1.0 / T["ma_degrade_tau_s"], "HSNL"), "head_5ht": (D5, 1.0 / 1.7, "NSML"),
                 "tail_pep": (float(T["pep_diffusion_um2_per_s"]), 1.0 / T["pep_degrade_tau_s"] +
                              T["pc_coelomocyte_uptake_per_s"], "DVB")}
        row = {}
        for name, (D, k, cell) in cases.items():
            p, j = fv(m, D, k, cell)
            ex = exact(m.edges, D, k, float(T["pc_cross_section_um2"]), m.edges[j], m.edges[j + 1])
            c = p.N[0] / p.V
            keep = ex >= 0.01 * ex.max()
            r = c / ex - 1.0
            dt = 0.01
            row[name] = dict(source_bin_err=float(r[j]), max_err=float(np.abs(r[keep]).max()),
                             max_err_off_source=float(np.abs(np.delete(r, j)[np.delete(keep, j)]).max()),
                             bar1_pass=bool(np.abs(r[keep]).max() <= 0.05),
                             bar3b=float(p.N.sum() / (1e4 * dt / np.expm1(k * dt)) - 1.0), n_bins=int(len(m.edges) - 1))
        out[h] = row
        print(h, json.dumps(row))
    (OUT / "grid_check_conv.json").write_text(json.dumps(out, indent=1))


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    mb, T = mech("bins")
    m4, _ = mech("four")
    A = float(T["pc_cross_section_um2"])
    D5 = float(T["ma_diffusion_um2_per_s"])
    cases = {"vulva_5ht": (D5, 1.0 / T["ma_degrade_tau_s"], "HSNL"),
             "head_5ht": (D5, 1.0 / 1.7, "NSML"),
             "tail_pep": (float(T["pep_diffusion_um2_per_s"]), 1.0 / T["pep_degrade_tau_s"] +
                          T["pc_coelomocyte_uptake_per_s"], "DVB")}
    res = dict(bin_um=float(T["pc_bin_um"]), n_bins=int(len(mb.edges) - 1), edges_four=m4.edges.tolist(), cases={})
    figs = {}
    for name, (D, k, cell) in cases.items():
        pb, jb = fv(mb, D, k, cell)
        p4, j4 = fv(m4, D, k, cell)
        s1, s2 = mb.edges[jb], mb.edges[jb + 1]
        ex = exact(mb.edges, D, k, A, s1, s2)
        cb = pb.N[0] / pb.V                                      # molecules per um3, bin means
        keep = ex >= 0.01 * ex.max()
        err = np.abs(cb[keep] / ex[keep] - 1.0)
        c4 = p4.N[0, j4] / p4.V[j4]
        res["cases"][name] = dict(
            D_um2_per_s=D, k_per_s=k, lambda_um=float(np.sqrt(D / k)), source=cell,
            source_y_um=float(mb.y[mb.names.index(cell)]), source_bin=[float(s1), float(s2)],
            bins_max_rel_err=float(err.max()), bins_bins_scored=int(keep.sum()), bar1_pass=bool(err.max() <= 0.05),
            four_over_exact_at_source=float(c4 / ex[jb]), exact_source_bin_nM=float(ex[jb] / N.NA_PL * 1e3),
            four_source_comp_nM=float(c4 / N.NA_PL * 1e3),
            conservation_bins=float(pb.N.sum() / (1e4 / k)), conservation_four=float(p4.N.sum() / (1e4 / k)),
            bar3_pass=bool(abs(pb.N.sum() / (1e4 / k) - 1) < 1e-6 and abs(p4.N.sum() / (1e4 / k) - 1) < 1e-6))
        figs[name] = (mb.edges, cb, ex, m4.edges, p4.N[0] / p4.V, cell)
        print(name, json.dumps(res["cases"][name]))
    (OUT / "grid_check.json").write_text(json.dumps(res, indent=1))
    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
        fig, ax = plt.subplots(1, 3, figsize=(15, 4))
        for a, (name, (eb, cb, ex, e4, c4, cell)) in zip(ax, figs.items()):
            mid = (eb[:-1] + eb[1:]) / 2
            to_nM = 1e3 / N.NA_PL
            a.step(e4, np.r_[c4, c4[-1]] * to_nM, where="post", color="#888888", label="four compartments")
            a.plot(mid, ex * to_nM, "-", color="#1f4e9c", lw=2, label="exact 1D (bin means)")
            a.plot(mid, cb * to_nM, "o", ms=3, color="#d1495b", label=f"bins ({res['bin_um']:.0f} um)")
            a.set_title(f"{name}: source {cell}, lambda {res['cases'][name]['lambda_um']:.0f} um")
            a.set_xlabel("soma y (um)")
            a.set_ylabel("nM at steady state (J = 1e4 /s)")
            a.set_yscale("log")
            a.set_ylim(ex.max() * to_nM * 1e-4, ex.max() * to_nM * 2)
        ax[0].legend(fontsize=8)
        fig.tight_layout()
        fig.savefig(OUT / "grid_check.png", dpi=110)
    except ImportError:
        pass


if __name__ == "__main__":
    import sys
    conv() if "--conv" in sys.argv else main()
