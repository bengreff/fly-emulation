"""wneuro item 6 (written Sun 8 Nov 2026 about 23:38 CST, before running): amine concentrations against receptor potency.

Question (Director): head 5-HT sits about 1 nM on food against SER-7's EC50 of 30 nM; vulval 5-HT 0.4-0.7 nM; full HSN
drive about 15 nM. Does any amine reach its receptors' EC50 anywhere, at rest or under drive, and if not, which part
of the chain sets the gap?

Method. Part A (the worm's own activity): the template worm at the ledger values (at_ledger.patch), all 302 neurons,
default toggles, SECONDS of 1 ms steps, food_OD 0 or 1.02 at the head. Every 100 ms: the four amines in the four
compartments (nM), each release cell's drive q and store. Each (amine, receptor) pair of mech/neuromod (14 GPCR pairs
and the MOD-1, LGC-55, LGC-53 channels outside synapses) is then read at every expressing cell as neuromod reads it
(the cell's membrane weights, ma_W) and set against the pair's EC50 (the ledger value, source in the ledger).
Part B (the ceiling of the release law): the same Mech object, reset, stepped alone (no NEURON) for CEIL_S s at 5 ms
with every release cell of one amine held at 0 mV (drive q -> sigmoid(30 / 5) = 0.998) and every other cell at -80 mV,
stores full at t = 0. This is the most any activity can release under the current law, so a pair that stays below
EC50 here cannot reach it under any published drive. Reported: the peak (full store) and the mean over the last 10 s
(store at its drive steady state), at each pair's expressing cells.

Part C (no run, arithmetic, in the report): the chain's factors at the ledger values, so the gap can be put on one
factor: per-cell release at full store and at the drive steady state, store size, compartment volume (molecules per
nM), clearance time (residual tau and MOD-5/DAT-1 uptake at low concentration: Vmax x cells / (Km x molecules per
nM)).

Classification rule (written before running; item 6 is a tabulation, no pass bar): a pair is "near off" where its
max occupancy over the run is below 0.1. Each near-off amine's gap is then put, with evidence, on: the release units
or store (A if the law's units are inconsistent with its own sources; D with a probe if a guessed value inside its
range closes it), the compartment geometry (A if the representation is outside its validity range for that pair, e.g.
a synaptic or perisynaptic target read from the bulk pool), clearance (as release), the EC50 source (C where two
measured values disagree), or a gap value (D). Where a free source measures endogenous amine content, the model's
store (molecules per release cell) is checked against it; that is the only measurement-based check here.

Usage: python amine_potency.py [SECONDS] [food=0|1.02] [ceil=CEIL_S] [tag=T] -> runs/worm/wneuro/amine_potency_food<f><T>.json
(the 20 s runs of 23:4x used the old shared 1e6 store; `tag=_ceil_newstore` reruns part B with the item 6 stores)
"""
from __future__ import annotations

import json
import sys
import time
from pathlib import Path
from types import SimpleNamespace

import numpy as np

ROOT = Path(__file__).resolve().parents[3]
for p in ("src", "scripts/worm"):
    sys.path.insert(0, str(ROOT / p))
import at_ledger  # noqa: E402

at_ledger.patch()
from wormemu import brain as B  # noqa: E402
from wormemu.interface import default_observation  # noqa: E402
from wormemu.mech import neuromod as N  # noqa: E402


def arg(key, default):
    return next((a.split("=", 1)[1] for a in sys.argv[1:] if a.startswith(key + "=")), default)


def pairs(b, nm):
    """(label, amine row, cells, ec50 nM, hill) for every amine receptor neuromod reads; the expressing cells by
    neuromod's own rule (CeNGEN class, threshold > 0, EXPR_ADD)."""
    st, classes = b.st, set(b.st.cengen_classes)
    cls = [None if m else N.cengen_class(c, classes) for c, m in zip(nm.names, b.is_muscle)]
    out = []
    for lg, rg in N.AMINE_PAIRS:
        cells = [c for c in range(nm.n) if nm.neuron[c] and
                 (1.0 if (cls[c], rg) in N.EXPR_ADD else st.expr(rg, cls[c])) > 0]
        out.append((f"{lg}>{rg}", N.AMINES.index(lg), cells, float(nm.p[f"ma_ec50_{lg}_{rg}_nM"]),
                    float(nm.p["gpcr_hill"])))
    for row, cells, ec, hh, _, _ in nm.extrasyn:
        out.append((f"{N.AMINES[row]}>{N.N_EXTRA[row]} (channel)", row, [int(c) for c in cells], ec, hh))
    return out


def read_table(nm, C, plist):
    """C: (T, amines, compartments) nM. Per pair: what its expressing cells read, mean and max over T, and the max
    occupancy."""
    tab = []
    for lab, row, cells, ec, hh in plist:
        if not cells:
            tab.append(dict(pair=lab, n_cells=0, ec50_nM=ec))
            continue
        r = C[:, row, :] @ nm.ma_W[cells].T                # (T, cells)
        occ = r ** hh / (r ** hh + ec ** hh)
        j = int(np.argmax(r.max(0)))
        tab.append(dict(pair=lab, n_cells=len(cells), ec50_nM=ec, read_mean_nM=float(r.mean()),
                        read_max_nM=float(r.max()), occ_max=float(occ.max()), occ_mean=float(occ.mean()),
                        top_cell=nm.names[cells[j]], ratio_max_to_ec50=float(r.max() / ec)))
    return tab


def part_a(secs, food):
    b = B.Brain(B.sample_worm(None))
    nm = next(m for m in b.mechs if type(m).__module__ == "wormemu.mech.neuromod")
    b.reset()
    C, Q, S = [], [], []
    for k in range(int(round(secs * 1000))):
        obs = default_observation(b.t)
        obs.head["food_OD"] = food
        b.step(obs, 1.0)
        if k % 100 == 99:
            C.append(nm.ma.nM().copy())
            Q.append(nm.q_ma.copy())
            S.append(nm.store.copy())
    return b, nm, np.array(C), np.array(Q), np.array(S)


def part_b(nm, row, secs, dt_ms=5.0):
    rel = nm.ma_rel[:, row] > 0
    v = np.where(rel, 0.0, -80.0)
    nm.reset()
    ctx = SimpleNamespace(v=v, outputs={})
    C = []
    for k in range(int(round(secs * 1000 / dt_ms))):
        nm.step(ctx, dt_ms)
        if k % int(100 / dt_ms) == int(100 / dt_ms) - 1:
            C.append(nm.ma.nM().copy())
    return np.array(C)


def factors(nm):
    p = nm.p
    V_pL = nm.ma.V / 1000.0
    per_nM = N.NA_PL * V_pL                                 # molecules per nM in each compartment
    J0, cap, ts = p["ma_release_per_s"], nm.ma_cap, p["ma_synth_tau_s"]
    s_ss = (1.0 / ts) / (1.0 / ts + J0 * 0.998 / cap)       # store at the full-drive steady state (no reuptake)
    out = dict(V_pL=V_pL.tolist(), molecules_per_nM=per_nM.tolist(), release_full_store=J0,
               store_ss_full_drive=s_ss.tolist(), release_ss_full_drive=(J0 * 0.998 * s_ss).tolist(), store_molecules=cap.tolist(),
               residual_tau_s=p["ma_degrade_tau_s"], uptake={})
    for row, (cells, km) in nm.uptake.items():
        n_k = nm.ma_W[cells].sum(0)                         # transporter cells' membrane in each compartment
        k_up = p["ma_uptake_vmax_per_s"] * n_k / (km * per_nM)   # 1/s at c << Km
        out["uptake"][N.AMINES[row]] = dict(n_cells=len(cells), km_nM=km, cells_per_compartment=n_k.tolist(),
                                            k_low_per_s=k_up.tolist(),
                                            tau_eff_s=(1.0 / (k_up + 1.0 / p["ma_degrade_tau_s"])).tolist())
    rel = {N.AMINES[k]: [nm.names[c] for c in np.flatnonzero(nm.ma_rel[:, k])] for k in range(len(N.AMINES))}
    out["release_cells"] = rel
    out["release_cells_per_compartment"] = {lg: np.bincount(nm.ma_comp[nm.ma_rel[:, k] > 0], minlength=len(V_pL))
                                            .tolist() for k, lg in enumerate(N.AMINES)}
    return out


def main():
    secs = float(sys.argv[1]) if len(sys.argv) > 1 and "=" not in sys.argv[1] else 20.0
    food = float(arg("food", "0"))
    ceil_s = float(arg("ceil", "60"))
    t0 = time.time()
    b, nm, C, Q, S = part_a(secs, food)
    plist = pairs(b, nm)
    rel_q = {lg: dict(q_mean=float(Q[:, nm.ma_rel[:, k] > 0].mean()), q_max=float(Q[:, nm.ma_rel[:, k] > 0].max()),
                      store_min=float(S[:, nm.ma_rel[:, k] > 0].min()))
             for k, lg in enumerate(N.AMINES) if (nm.ma_rel[:, k] > 0).any()}
    res = dict(bio_s=secs, food_OD=food, compartments=list(N.COMPARTMENTS),
               pool_mean_nM={lg: C[:, k, :].mean(0).tolist() for k, lg in enumerate(N.AMINES)},
               pool_max_nM={lg: C[:, k, :].max(0).tolist() for k, lg in enumerate(N.AMINES)},
               release_drive=rel_q, rest=read_table(nm, C, plist), factors=factors(nm), ceiling={})
    print("part A done", round(time.time() - t0), "s", flush=True)
    for k, lg in enumerate(N.AMINES):
        if not (nm.ma_rel[:, k] > 0).any():
            continue
        Cb = part_b(nm, k, ceil_s)
        last = Cb[-100:]
        res["ceiling"][lg] = dict(pool_peak_nM=Cb[:, k, :].max(0).tolist(), pool_last10s_nM=last[:, k, :].mean(0).tolist(),
                                  peak=[r for r in read_table(nm, Cb, plist) if r["pair"].startswith(lg)],
                                  steady=[r for r in read_table(nm, last, plist) if r["pair"].startswith(lg)])
    res["wall_s"] = time.time() - t0
    out = ROOT / f"runs/worm/wneuro/amine_potency_food{food:g}{arg('tag', '')}.json"
    out.write_text(json.dumps(res, indent=1, default=float))
    for r in res["rest"]:
        print({k: (round(v, 4) if isinstance(v, float) else v) for k, v in r.items()})
    print("wall", round(res["wall_s"]), "s")


if __name__ == "__main__":
    main()
