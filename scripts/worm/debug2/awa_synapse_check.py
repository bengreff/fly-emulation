"""AWA's synapses under Liu's membrane (wbrain2, 9 Nov 2026; check pre-registered in docs/worm/night/2026-11-08_wbrain2.md,
"AWA's synapses silenced by its membrane swap").

At the ledger, sub-brain AWAL, AIYL, AWCL, AIAL: (1) the release scale of every synapse from AWAL and the receptor
scale of every synapse onto AWAL; (2) AWAL's channel and leak scales; (3) AIYL's mean V over a 1 s 20 pA step into
AWAL, with AWAL's release as now and cut to 0 (the behaviour before the fix, by patching _awa_gscale).

  python scripts/worm/debug2/awa_synapse_check.py [--out file.json]
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np

CELLS = ["AWAL", "AIYL", "AWCL", "AIAL"]


def run(cut: bool):
    from wormemu import brain as B
    from wormemu.mech import G_SCALE_NAMES, senses_chem
    orig = senses_chem.Mech._awa_gscale
    if cut:
        def old(self):
            if not hasattr(self, "_gsc"):
                self._gsc = {}
                for nm in G_SCALE_NAMES:
                    x = np.ones(self.n)
                    x[self.awa_idx] = 0.0
                    self._gsc[nm] = x
            return self._gsc
        senses_chem.Mech._awa_gscale = old
    try:
        b = B.Brain(cells=CELLS)
        b.reset()
        a, y = b.idx["AWAL"], b.idx["AIYL"]
        for _ in range(1000):
            b.step()
        pre, post, cls, rel, rec, crel, crec = b._sg
        scales = dict(release_from_awal=sorted(set(np.round(crel[pre == a], 6).tolist())),
                      receptor_onto_awal=sorted(set(np.round(crec[post == a], 6).tolist())),
                      n_from=int((pre == a).sum()), n_onto=int((post == a).sum()))
        mem = {}
        for nm, (cells, pv, base, cur) in b._gt.items():
            k = np.flatnonzero(np.asarray(cells) == a)
            if len(k):
                mem[nm] = float(cur[k[0]])
        base_v = []
        for _ in range(1000):
            base_v.append(float(b.step().v_mV[y]))
        v = []
        for _ in range(1000):
            b.extra_pA[a] = 20.0
            out = b.step()
            v.append((float(out.v_mV[a]), float(out.v_mV[y])))
        b.extra_pA[a] = 0.0
        v = np.array(v)
        return dict(cut=cut, scales=scales, awal_membrane_scales=mem, aiyl_base_mV=float(np.mean(base_v)),
                    aiyl_step_mV=float(v[:, 1].mean()), awal_peak_mV=float(v[:, 0].max()))
    finally:
        senses_chem.Mech._awa_gscale = orig


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default="")
    a = ap.parse_args()
    now, cut = run(False), run(True)
    s = now["scales"]
    p1 = s["release_from_awal"] == [1.0] and s["receptor_onto_awal"] == [1.0]
    p2 = all(x == 0.0 for nm, x in now["awal_membrane_scales"].items() if nm.startswith("dens_") or nm == "leak")
    dv = now["aiyl_step_mV"] - cut["aiyl_step_mV"]
    res = dict(now=now, cut=cut, aiyl_dv_mV=dv, passes=dict(scales=p1, membrane_zero=p2, aiyl_moves=abs(dv) > 0.1))
    print(json.dumps(res, indent=1))
    if a.out:
        Path(a.out).parent.mkdir(parents=True, exist_ok=True)
        Path(a.out).write_text(json.dumps(res, indent=1))


if __name__ == "__main__":
    main()
