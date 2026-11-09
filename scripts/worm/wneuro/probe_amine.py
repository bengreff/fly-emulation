"""wneuro item 6, feasibility probe (written Sun 8 Nov 2026 about 23:50 CST, before running).

Question: at the worm's own on-food drive, does any point inside the bio ranges of the release law's guessed values
bring an amine at its targets up to the receptor's EC50? If yes, the gap is class D (a gap value; never adopted). If
no point does, the gap is not in those values (geometry, EC50 or drive), and is classified from there.

Method. The template worm's Mech (neuromod) at the ledger values, membrane read, built once in a Brain, then stepped
alone (no NEURON) at 10 ms for 60 s, peptides off. Drive fixed: each release cell's voltage set so that its drive
relaxes to its measured 20 s mean on food (release_drive_food1.02.json), and its G-protein release factor fixed at its
measured mean (same file); every other cell at -80 mV. Stores full at t = 0. Box (log-uniform over each Spec's ledger
bio range; all guessed values): ma_release_per_s 1e3-1e7, ma_store_molecules 1e4-1e8, ma_synth_tau_s 5-600,
ma_degrade_tau_s 0.5-50, ma_uptake_vmax_per_s 1e4-1e7, pc_cross_section_um2 100-1500. 256 Sobol points (scipy, scramble,
seed 0), plus the template point, plus each factor alone at either end of its range (others at the template).

Read: for every (amine, receptor) pair of mech/neuromod, the mean over the last 20 s of what its expressing cells read
(their membrane weights), the maximum over those cells. Reaches = that read >= the pair's EC50 (occupancy >= 0.5 at
Hill 1). Also named: MC's SER-7 (pumping; organs_pharynx reads the head compartment) and the vulva (organs_egglaying
reads HSN's soma compartment) against SER-7 (30 nM, measured) and SER-1 (1000 nM, guessed).

Reported, not adopted: the fraction of box points that reach, per pair; whether reaching points sit at a range edge;
which single factor alone reaches. Drive is held at the template's measured mean, so this says nothing about whether
that drive is right (the release voltage law, ma_vhalf_mV and ma_k_mV, is outside the box on purpose: it is the
activity side, read from the worm).

Addendum (23:53 CST, before running): the 5-HT and DA stores are now their own rows (derived from Weishaupt et
al. 2023, item 6); the template point uses them; a box or single point's ma_store_molecules applies to all four amines,
so the box still spans the guessed 1e4-1e8. The drive file was recorded with the old 1e6 store (stores stayed above
0.95 of full at rest, so the drive is the same to that precision).

Addendum (Mon 9 Nov 2026 01:55 CST, session 5, before running): re-run on pc_grid=bins, the new default (Director
01:40). Two reads were written for the four compartments and are now taken as neuromod reads them: MC's SER-7 is MCL's
membrane read (ma_W, all in the head under four, so the same number there), and the vulva is HSNL's bin (nm.ma_comp,
what organs_egglaying reads). SER-1's EC50 is now 1340 nM measured (code Spec, session 3). The drive file is unchanged
(recorded under four with the old store; bins moves what HSN reads by under 0.2 nM, about 1e-4 of its 5-HT receptors'
occupancy, derived). Same box, seed, rule and LAST window. Output tag=_bins.

Usage: python probe_amine.py [N_POINTS] [tag=T] -> runs/worm/wneuro/probe_amine<T>.json
"""
from __future__ import annotations

import json
import sys
import time
from pathlib import Path
from types import SimpleNamespace

import numpy as np
from scipy.stats import qmc

ROOT = Path(__file__).resolve().parents[3]
for p in ("src", "scripts/worm", "scripts/worm/wneuro"):
    sys.path.insert(0, str(ROOT / p))
import at_ledger  # noqa: E402

at_ledger.patch()
from amine_potency import pairs  # noqa: E402
from wormemu import brain as B  # noqa: E402
from wormemu.mech import neuromod as N  # noqa: E402

BOX = {"ma_release_per_s": (1e3, 1e7), "ma_store_molecules": (1e4, 1e8), "ma_synth_tau_s": (5.0, 600.0),
       "ma_degrade_tau_s": (0.5, 50.0), "ma_uptake_vmax_per_s": (1e4, 1e7), "pc_cross_section_um2": (100.0, 1500.0)}
SECS, DT, LAST = 60.0, 10.0, 20.0


def setup():
    b = B.Brain(B.sample_worm(None))
    nm = next(m for m in b.mechs if type(m).__module__ == "wormemu.mech.neuromod")
    drive = json.loads((ROOT / "runs/worm/wneuro/release_drive_food1.02.json").read_text())
    p0 = dict(nm.p)
    v = np.full(nm.n, -80.0)
    R = np.ones(nm.n)
    for name, d in drive.items():
        c = nm.names.index(name)
        q = min(max(d["q_mean"], 1e-9), 1 - 1e-9)
        v[c] = p0["ma_vhalf_mV"] + p0["ma_k_mV"] * np.log(q / (1 - q))
        R[c] = d["R_mean"]
    nm.on[N.P] = False
    nm.wgc = None
    nm.release_factor = lambda: R
    return b, nm, p0, v, drive


def run(nm, p0, v, point):
    nm.p = {**p0, **point}
    if "ma_store_molecules" in point:
        for lg in N.AMINES:
            if f"ma_store_molecules_{lg}" in nm.p:
                nm.p[f"ma_store_molecules_{lg}"] = point["ma_store_molecules"]
    nm.ma_cap = np.array([float(nm.p.get(f"ma_store_molecules_{lg}", nm.p["ma_store_molecules"])) for lg in N.AMINES])
    nm.ma_comp, nm.ma = nm._pool(False, len(N.AMINES), nm.p["ma_diffusion_um2_per_s"])
    nm.reset()
    ctx = SimpleNamespace(v=v, outputs={})
    acc, n = np.zeros_like(nm.ma.N), 0
    steps = int(round(SECS * 1000 / DT))
    for k in range(steps):
        nm.step(ctx, DT)
        if k >= steps - int(LAST * 1000 / DT):
            acc += nm.ma.nM()
            n += 1
    return acc / n                                         # (amines, compartments) nM, mean over the last LAST s


def score(nm, C, plist, hsn):
    out = {}
    for lab, row, cells, ec, _ in plist:
        if cells:
            r = nm.ma_W[cells] @ C[row]
            out[lab] = float(r.max() / ec)
    s5 = N.AMINES.index("serotonin")
    mc = nm.names.index("MCL")
    out["MC ser-7 (head)"] = float(nm.ma_W[mc] @ C[s5] / float(nm.p["ma_ec50_serotonin_ser-7_nM"]))
    out["vulva ser-7"] = float(C[s5, nm.ma_comp[hsn]] / float(nm.p["ma_ec50_serotonin_ser-7_nM"]))
    out["vulva ser-1"] = float(C[s5, nm.ma_comp[hsn]] / float(nm.p["ma_ec50_serotonin_ser-1_nM"]))
    return out                                             # read / EC50; >= 1 reaches


def main():
    npts = int(sys.argv[1]) if len(sys.argv) > 1 and "=" not in sys.argv[1] else 256
    tag = next((a.split("=", 1)[1] for a in sys.argv[1:] if a.startswith("tag=")), "")
    t0 = time.time()
    b, nm, p0, v, drive = setup()
    plist = pairs(b, nm)
    hsn = nm.names.index("HSNL")
    keys = list(BOX)
    lo, hi = np.log10([BOX[k][0] for k in keys]), np.log10([BOX[k][1] for k in keys])
    U = qmc.Sobol(len(keys), scramble=True, seed=0).random(npts)
    pts = [{k: float(10 ** x) for k, x in zip(keys, lo + u * (hi - lo))} for u in U]
    single = [(k, e, {k: BOX[k][e]}) for k in keys for e in (0, 1)]
    res = dict(template={}, single={}, box=[], box_keys=keys, drive=drive)
    res["template"] = score(nm, run(nm, p0, v, {}), plist, hsn)
    print("template", {k: round(x, 4) for k, x in res["template"].items()}, round(time.time() - t0), "s", flush=True)
    for k, e, pt in single:
        res["single"][f"{k}={BOX[k][e]:g}"] = score(nm, run(nm, p0, v, pt), plist, hsn)
    print("single done", round(time.time() - t0), "s", flush=True)
    for i, pt in enumerate(pts):
        res["box"].append(dict(point=pt, ratio=score(nm, run(nm, p0, v, pt), plist, hsn)))
        if i % 32 == 31:
            print(i + 1, "points", round(time.time() - t0), "s", flush=True)
    labs = list(res["template"])
    summ = {}
    for lab in labs:
        r = np.array([x["ratio"][lab] for x in res["box"]])
        reach = [x["point"] for x in res["box"] if x["ratio"][lab] >= 1.0]
        edge = sum(any(abs(np.log10(p[k] / BOX[k][e])) < 0.05 * (hi[j] - lo[j]) for j, k in enumerate(keys)
                       for e in (0, 1)) for p in reach)
        summ[lab] = dict(template=res["template"][lab], box_reach=len(reach), box_n=len(r),
                         box_max=float(r.max()), reach_near_edge=int(edge),
                         single_reach=[s for s, d in res["single"].items() if d[lab] >= 1.0])
    res["summary"] = summ
    res["wall_s"] = time.time() - t0
    res["grid"] = nm.grid
    (ROOT / f"runs/worm/wneuro/probe_amine{tag}.json").write_text(json.dumps(res, indent=1))
    for lab, s in summ.items():
        print(f"{lab:32s} template {s['template']:.4f} reach {s['box_reach']}/{s['box_n']} max {s['box_max']:.2f} "
              f"edge {s['reach_near_edge']} single {s['single_reach']}")
    print("wall", round(res["wall_s"]), "s")


if __name__ == "__main__":
    main()
