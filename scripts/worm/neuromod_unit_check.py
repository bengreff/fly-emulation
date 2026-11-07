"""Rows 9, 10, 28 unit and sanity checks for mech/neuromod.py, on the module alone (no NEURON): a stand-in brain
with the 302 neurons, voltages set by hand. Bars are in docs/worm/night/2026-11-06_wbrain.md (written before running).

1. Code check: occupancy 0.5 at c = EC50; MOD-5 / DAT-1 uptake at c = Km runs at half Vmax (through step()).
2. Sanity: a head bolus of FLP-11 with no release or loss is conserved and relaxes with the slowest exchange time.
3. Limit: compartments at huge diffusion = well_mixed.
4. Sanity: RIS held depolarized; FLP-11 plateaus, lower with the DMSR-1 autoreceptor; RIS Gi only with it.

Usage: PYTHONPATH=src .venv/bin/python scripts/worm/neuromod_unit_check.py [out.json]
"""
from __future__ import annotations

import json
import sys
from types import SimpleNamespace

import numpy as np

from wormemu.brain_structure import load_structure
from wormemu.mech import Ctx
from wormemu.mech import neuromod as N

ST = load_structure()
NEURONS = [n for n, k in zip(ST.names, ST.kind) if k == "neuron"]
BRAIN = SimpleNamespace(st=ST, cell_names=NEURONS, is_muscle=np.zeros(len(NEURONS), bool),
                        spec=SimpleNamespace(values={}), layers=None)
T = {s.id: s.template for s in N.SPECS}


def make(pep="compartments", ma="off", expr_add=None, **over):
    return N.Mech(BRAIN, {**T, **over}, {"peptides": pep, "monoamines": ma}, expr_add=expr_add)


def ctx(v, t=0.0):
    return Ctx(t_ms=t, obs={}, v=v, ca=np.zeros(len(v)), names=NEURONS, is_muscle=BRAIN.is_muscle, outputs={})


def main():
    res = {}
    # 1. occupancy at EC50; uptake at Km through step()
    occ = [float(N._hill(np.array([e]), np.array([e]), h)[0]) for e in (0.01, 3.0, 2000.0) for h in (0.5, 1.0, 2.0)]
    up = {}
    for lg, gene in N.TRANSPORTERS.items():
        m = make("off", "compartments", ma_degrade_tau_s=1e15)
        row = N.AMINES.index(lg)
        km = T[f"{gene.replace('-', '')}_km_nM"]
        m.ma.N[row] = km * N.NA_PL * m.ma.V / 1000.0
        before = m.ma.N[row].sum()
        dt = 0.5
        m.step(ctx(np.full(len(NEURONS), -200.0)), dt)
        rate = (before - m.ma.N[row].sum()) / (dt / 1000.0)
        cells = m.uptake[row][0]
        want = len(cells) * T["ma_uptake_vmax_per_s"] / 2.0
        up[lg] = dict(cells=[NEURONS[c] for c in cells], rate_over_half_vmax=float(rate / want))
    res["code_checks"] = dict(occupancy_at_ec50=occ, uptake=up, bar="0.5 and 1 within 1e-9",
                              passed=bool(np.allclose(occ, 0.5, atol=1e-9, rtol=0)
                                          and all(abs(x["rate_over_half_vmax"] - 1) < 1e-9 for x in up.values())))
    # 2. head bolus, no release or loss: conservation and the slowest exchange time
    m = make(dcv_rate_per_s=0.0, pep_degrade_tau_s=1e15, pc_coelomocyte_uptake_per_s=0.0)
    row = N.PRECURSORS.index("flp-11")
    m.pep.N[row, 0] = 1e6
    lam = np.sort(np.linalg.eigvals(m.pep.K).real)
    tau_slow = float(-1.0 / lam[-2])                     # lam[-1] = 0, the conserved total
    v = np.full(len(NEURONS), -200.0)
    ts, ex, tot = [], [], []
    for k in range(20000):
        m.step(ctx(v, k * 1000.0), 1000.0)
        c = m.pep.nM()[row]
        mean = m.pep.N[row].sum() / (N.NA_PL * m.pep.V.sum() / 1000.0)
        ts.append(k + 1.0)
        ex.append(c[0] - mean)
        tot.append(m.pep.N[row].sum())
    ts, ex = np.array(ts), np.array(ex)
    w = (ts > 3 * tau_slow) & (ts < 6 * tau_slow) & (np.abs(ex) > 0)
    slope = np.polyfit(ts[w], np.log(np.abs(ex[w])), 1)[0]
    tau_meas = float(-1.0 / slope)
    cons = float(abs(tot[-1] - 1e6) / 1e6)
    spread = float(np.abs(c / mean - 1).max())
    res["bolus"] = dict(compartments=dict(zip(N.COMPARTMENTS, m.pep.V.tolist())), tau_slow_derived_s=round(tau_slow, 1),
                        tau_measured_s=round(tau_meas, 1), conservation_rel_err=cons, end_spread=spread,
                        bar="conserved 1e-9; tau within 5%; end spread < 1%",
                        passed=bool(cons < 1e-9 and abs(tau_meas / tau_slow - 1) < 0.05 and spread < 0.01))
    # 3. limit: compartments at diffusion 1e11 vs well_mixed, both amines and peptides on
    big = dict(pep_diffusion_um2_per_s=1e11, ma_diffusion_um2_per_s=1e11)
    a, b = make("compartments", "compartments", **big), make("well_mixed", "well_mixed", **big)
    rng = np.random.default_rng(1)
    v0, ph = rng.uniform(-60, 0, len(NEURONS)), rng.uniform(0, 2 * np.pi, len(NEURONS))
    err = 0.0
    for k in range(5000):
        v = v0 + 20 * np.sin(2 * np.pi * k / 1000.0 + ph)
        ra, rb = a.step(ctx(v, float(k)), 1.0), b.step(ctx(v, float(k)), 1.0)
        for x, y in ((a.pep.nM(), b.pep.nM()), (a.ma.nM(), b.ma.nM())):
            err = max(err, float(np.max(np.abs(x - y) / np.maximum(np.abs(y), 1e-30))))
        err = max(err, float(np.max(np.abs(a.G - b.G) / np.maximum(np.abs(b.G), 1e-12))),
                  float(np.max(np.abs(ra["I_pA"] - rb["I_pA"]) / np.maximum(np.abs(rb["I_pA"]), 1e-12))))
    res["limit_well_mixed"] = dict(max_rel_err=err, G_mean=a.G.mean(0).tolist(), bar="1e-6", passed=bool(err < 1e-6))
    # 4. RIS held at 0 mV, everyone else at -80 mV, with and without the RIS DMSR-1 autoreceptor
    ris = NEURONS.index("RIS")
    v = np.full(len(NEURONS), -80.0)
    v[ris] = 0.0
    r4 = {}
    for name, add in (("with", None), ("without", {})):
        m = make(expr_add=add)
        tr = []
        for k in range(6000):
            m.step(ctx(v, k * 100.0), 100.0)
            tr.append(float(m.pep.nM()[row, 0]))
        tr = np.array(tr)
        r4[name] = dict(flp11_head_nM_end=tr[-1], flp11_head_nM_60s=tr[599], change_last_60s=float(abs(tr[-1] / tr[-601]
                        - 1)), ris_gi=float(m.G[ris, 1]), ris_release_factor=float(m.release_factor()[ris]))
    ok = (r4["with"]["change_last_60s"] < 0.01 and r4["without"]["change_last_60s"] < 0.01
          and r4["with"]["flp11_head_nM_end"] < r4["without"]["flp11_head_nM_end"]
          and r4["with"]["ris_gi"] > 0.1 and r4["without"]["ris_gi"] == 0.0)
    res["ris_self_limit"] = dict(**r4, bar="plateau (<1% over last 60 s); lower with; RIS Gi > 0.1 with, 0 without",
                                 passed=bool(ok))
    print(json.dumps(res, indent=1, default=float))
    if len(sys.argv) > 1:
        open(sys.argv[1], "w").write(json.dumps(res, indent=1, default=float))


if __name__ == "__main__":
    main()
