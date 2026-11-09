"""wneuro session 6, for the rec_tmax request to wbrain2 (a derived table, no bar; written Mon 9 Nov 2026 03:27 CST).

The brain's synapse layer holds the mean cleft amine at full graded release as one guessed number per amine
(receptors.py, rec_tmax_<amine>_uM, 10 uM, range 1-100). Neuromod's near field (mech/neuromod near_nM with post, the
generic Cook route rule) gives the same quantity per synapse from the release rate and Cook et al. 2019's counts.
This tabulates neuromod's value over every Cook chemical connection whose pre cell releases an amine (neuromod's
ma_rel), at full drive and a full store (J = ma_release_per_s, the ledger's 1e5 molecules/s), at two receptor
distances: 0.02 um (a cleft) and the template 0.1 um; the other geometry at the template. Per amine: the median and
range over connections, and the fraction of connections at or above the brain's lower bound (1 uM).

A stand-in Mech over Cook's whole cell list (neuromod alone; only near_nM is called), as probe_routes' cross-check.
Usage: python cleft_table.py -> runs/worm/wneuro/cleft_table.json
"""
from __future__ import annotations

import json
import sys
from pathlib import Path
from types import SimpleNamespace

import numpy as np

ROOT = Path(__file__).resolve().parents[3]
for p in ("src", "scripts/worm"):
    sys.path.insert(0, str(ROOT / p))
import at_ledger  # noqa: E402

at_ledger.patch()
from wormemu import brain as B  # noqa: E402
from wormemu.brain_structure import load_structure  # noqa: E402
from wormemu.mech import neuromod as N  # noqa: E402


def main():
    st = load_structure()
    p0 = {**{x.id: x.template for x in N.SPECS}, **dict(B.sample_worm(None).values)}  # Specs not yet in the ledger
    allb = SimpleNamespace(st=st, cell_names=list(st.names), is_muscle=np.array([k != "neuron" for k in st.kind]),
                           spec=SimpleNamespace(values={}), layers=None)
    sm = N.Mech(allb, p0, {"peptides": "off", "monoamines": "compartments", "amine_synaptic": "nicholson"})
    p = sm.p
    J = float(p["ma_release_per_s"])
    cn, out = sm.cook_counts()
    res = dict(J=J, rec_tmax_uM={lg: float(p0.get(f"rec_tmax_{lg}_uM", np.nan)) for lg in ("serotonin", "tyramine",
               "dopamine")}, by_amine={})
    for row, lg in enumerate(N.AMINES):
        rel = np.flatnonzero(sm.ma_rel[:, row] > 0)
        vals = {}
        for r_um in (0.02, float(p["syn_site_receptor_um"])):
            sm.p = {**p, "syn_site_receptor_um": r_um}
            x = [sm.near_nM(lg, [int(a)], J=[J], post=int(c)) for a in rel for c in np.flatnonzero(cn[a] > 0)]
            vals[r_um] = np.array(x) / 1000.0
        sm.p = p
        x2, x1 = vals[0.02], vals[float(p["syn_site_receptor_um"])]
        res["by_amine"][lg] = dict(
            release_cells=[sm.names[a] for a in rel], n_connections=int(len(x2)),
            cleft_0p02_uM=dict(median=float(np.median(x2)), min=float(x2.min()), max=float(x2.max()),
                               frac_ge_1uM=float((x2 >= 1.0).mean())),
            template_0p1_uM=dict(median=float(np.median(x1)), min=float(x1.min()), max=float(x1.max()),
                                 frac_ge_1uM=float((x1 >= 1.0).mean())))
    (ROOT / "runs/worm/wneuro/cleft_table.json").write_text(json.dumps(res, indent=1, default=float))
    print(json.dumps(res, indent=1, default=float))


if __name__ == "__main__":
    main()
