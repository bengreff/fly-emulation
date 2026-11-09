"""How much the interconnect graph localises (weki, 8 Nov 2026; brief item 4; FIT_GENERAL.md section 5): eki.graph_rho
on the real default graph, for the EKI vector (Theta's continuous numbers, scene_* left out) against the vital signs.

Nodes are modules (iograph.record over 20 ms of the default worm). A parameter sits at its mechanism's module
(mech.modules()); brain-layer numbers (channels, synapses, gaps, ions, Ca nanodomain) write the membrane directly, and
body numbers reach every module that reads ctx.obs (the conservative choice: no zeros from them). Hub: modules that
write g_scale, I_pA or act_add feed the node "membrane"; every module that reads ctx.obs reads it. Each sign is read
from: the membrane (voltages, Ca, GCaMP), organs_pharynx (pumps), organs_intestine (expulsions), organs_egglaying (eggs).

Usage (backhouse, fresh process): python scripts/worm/fit/cost_graph.py OUT.json
"""
from __future__ import annotations

import json
import sys
import time
from pathlib import Path

import numpy as np

from wormemu import iograph, mech, params
from wormemu.fit import eki, vitals

READ_FROM = {"pump_hz": "organs_pharynx", "pump_hz_off": "organs_pharynx", "dmp_period_s": "organs_intestine",
             "egg_inactive_min": "organs_egglaying", "egg_intra_s": "organs_egglaying"}


def main():
    t0 = time.time()
    g = iograph.record(ms=20)
    E = iograph.edges(g)
    writers = sorted(m for m, w in g["writes"].items() if "drive" in w or "g_scale" in w)
    readers = sorted(m for m, r in g["reads"].items() if r["obs"])
    t = params.Theta().table
    t = t[t.active] if "active" in t.columns else t
    t = t[(t.transform != "bernoulli") & ~t.pid.astype(str).str.startswith("scene_")]
    mod = {x[0]: m.__name__.rsplit(".", 1)[-1] for m in mech.modules() for x in m.MECHANISMS}
    edges = list(E) + [("body", "obs", r) for r in readers]
    pm = [mod.get(k) or ("body" if str(k).startswith("body") else "membrane") for k in t.mechanism]
    signs = [s.id for s in vitals.SIGNS]
    scored = [s.id for s in vitals.SIGNS if s.band() is not None]
    obs = [READ_FROM.get(s, "membrane") for s in signs]
    rho = eki.graph_rho(pm, obs, edges, hub=(writers, readers))
    j = [signs.index(s) for s in scored]
    unreached = sorted({p for p, r in zip(pm, rho) if not r.all()})
    out = dict(n_params=len(pm), n_signs=len(signs), scored=scored, writers=writers, readers=readers,
               n_edges=len(E), zero_fraction_all=float(1 - rho.mean()), zero_fraction_scored=float(1 - rho[:, j].mean()),
               zero_by_sign={s: float(1 - rho[:, i].mean()) for i, s in enumerate(signs)},
               modules_not_reaching_every_sign=unreached,
               params_by_module={m: int(pm.count(m)) for m in sorted(set(pm))}, wall_s=time.time() - t0)
    Path(sys.argv[1]).write_text(json.dumps(out, indent=1))
    print(json.dumps({k: v for k, v in out.items() if k not in ("params_by_module",)}, indent=1))


if __name__ == "__main__":
    main()
