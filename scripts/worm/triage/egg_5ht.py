"""Row 15 cause check (wtriage, 8 Nov 2026; diagnostic, no bar): the 5-HT the vulval muscles see in the row 15 brain
(check_egglaying.py's 8 cells, ledger values), against the SER-1/SER-7 EC50s it is read at. Prints HSN voltage, HSN's
amine drive q, the HSN-compartment 5-HT (nM), the compartment volume, and the steady-state 5-HT if HSN ran at full
drive (q = 1, full store, no uptake), so "HSN never depolarises" and "release too small" can be told apart.

Usage: python egg_5ht.py SECONDS
"""
import json
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "scripts" / "worm"))
sys.path.insert(0, str(ROOT / "scripts" / "worm" / "organs"))
import at_ledger  # noqa: E402

at_ledger.patch()
import check_egglaying as CE  # noqa: E402
from wormemu.brain import Brain  # noqa: E402
from wormemu.mech import neuromod as nmod  # noqa: E402


def main():
    secs = float(sys.argv[1]) if len(sys.argv) > 1 else 20.0
    b = Brain(cells=CE.CELLS, toggles={})
    b.reset()
    eg = next(x for x in b.mechs if type(x).__module__.endswith("organs_egglaying"))
    nm = next((x for x in b.mechs if isinstance(x, nmod.Mech)), None)
    hsn = [b.idx["HSNL"], b.idx["HSNR"]]
    n = int(round(secs * 1000 / CE.DT))
    vs, cs, qs, occ = [], [], [], []
    for k in range(n):
        o = b.step(None, CE.DT)
        vs.append(float(np.mean(o.v_mV[hsn])))
        c5, _ = eg.concentrations()
        cs.append(c5)
        occ.append(b.mech_out["egg_5ht_occ"])
        if nm is not None and nm.on.get(nmod.A):
            qs.append(float(np.mean(nm.q_ma[hsn])))
    out = dict(seconds=secs, neuromod=nm is not None, amines_on=bool(nm and nm.on.get(nmod.A)),
               hsn_v_mean=float(np.mean(vs)), hsn_v_max=float(np.max(vs)), hsn_frac_above_m30=float(np.mean(np.array(vs) > -30)),
               c5_nM_mean=float(np.mean(cs)), c5_nM_max=float(np.max(cs)), occ_max=float(np.max(occ)),
               ec50_nM=eg.ec5.tolist(), q_hsn_mean=float(np.mean(qs)) if qs else None)
    if nm is not None and nm.on.get(nmod.A):
        p = nm.p
        comp = int(nm.ma_comp[hsn[0]])
        V = float(nm.ma.V[comp])
        # full drive, full store, both HSNs, loss by degradation only (no MOD-5 cells in this brain)
        N_ss = 2 * p["ma_release_per_s"] * p["ma_degrade_tau_s"]
        out.update(comp=comp, comp_volume=V, n_comp=int(nm.ma.N.shape[1]),
                   c5_full_drive_nM=float(N_ss / (nmod.NA_PL * V / 1000.0)),
                   ma_vhalf_mV=p["ma_vhalf_mV"], ma_k_mV=p["ma_k_mV"], release_per_s=p["ma_release_per_s"],
                   degrade_tau_s=p["ma_degrade_tau_s"], store=float(np.mean(nm.store[hsn])) if nm.store.ndim == 1
                   else nm.store[hsn].tolist())
    print(json.dumps(out, indent=1, default=float))
    (ROOT / "runs/worm/triage").mkdir(parents=True, exist_ok=True)
    (ROOT / "runs/worm/triage/egg_5ht.json").write_text(json.dumps(out, indent=1, default=float))


if __name__ == "__main__":
    main()
