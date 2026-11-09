"""How much the interconnect graph localises (weki, 8 Nov 2026; brief item 4; FIT_GENERAL.md section 5): eki.graph_rho
on the real default graph, for the EKI vector (Theta's continuous numbers, scene_* left out) against the vital signs.

Nodes are modules (iograph.record over 20 ms of the default worm). A parameter sits at its mechanism's module
(mech.modules()); brain-layer numbers (channels, synapses, gaps, ions, Ca nanodomain) write the membrane directly.
Two graphs are reported:
  trace         the recorded run only: writers of g_scale, I_pA or act_add feed the node "membrane", which feeds every
                module that read ctx.obs; body numbers reach the ctx.obs readers.
  static        what a 20 ms trace cannot see: a module that wrote nothing in the run is taken to act at build time on
                the membrane (cells_passive, receptors, structure_rules, ...); every
                module whose source reads ctx.v or ctx.ca reads the membrane (static scan; ctx.v and ctx.ca are not
                traced); the membrane drives the body (muscles) and the body feeds every ctx.obs reader (closed loop).
                observation.py's readout numbers (gcamp, neuropal) sit at a readout node that only the GCaMP signs
                read; its opto actuator writes the membrane.
  conservative  static, plus every module with numbers writes the membrane (the trace logs a drive only when it is
                nonzero, so touch and stretch at rest, pump currents and synaptic weights in NEURON are not seen): no
                zero here is false.
Each sign is read from the membrane (every organ's cells are NEURON sections or write it) plus its organ module
(pumps: organs_pharynx; expulsions: organs_intestine; eggs: organs_egglaying) and, for pc3_frac and gcamp_range, the
GCaMP readout.

Usage (fresh process; about 10 s): python scripts/worm/fit/cost_graph.py OUT.json
"""
from __future__ import annotations

import json
import re
import sys
import time
from pathlib import Path

import numpy as np

from wormemu import iograph, mech, params
from wormemu.iograph import SRC
from wormemu.fit import eki, vitals

READ_FROM = {"pump_hz": "organs_pharynx", "pump_hz_off": "organs_pharynx", "dmp_period_s": "organs_intestine",
             "egg_inactive_min": "organs_egglaying", "egg_intra_s": "organs_egglaying",
             "pc3_frac": "readout_gcamp", "gcamp_range": "readout_gcamp"}
READOUT = {"gcamp": "readout_gcamp", "neuropal": "readout_neuropal", "gait_features": "readout_gait"}


def density(pm, obs, signs, scored, edges, hub):
    rho = eki.graph_rho(pm, obs, edges, hub=hub)
    j = [signs.index(s) for s in scored]
    return rho, dict(zero_fraction_all=float(1 - rho.mean()), zero_fraction_scored=float(1 - rho[:, j].mean()),
                     zero_by_sign={s: float(1 - rho[:, i].mean()) for i, s in enumerate(signs)},
                     modules_not_reaching_every_sign=sorted({p for p, r in zip(pm, rho) if not r.all()}))


def main():
    t0 = time.time()
    g = iograph.record(ms=20)
    E = iograph.edges(g)
    writers = sorted(m for m, w in g["writes"].items() if "drive" in w or "g_scale" in w)
    readers = sorted(m for m, r in g["reads"].items() if r["obs"])
    t = params.Theta().table
    t = t[t.active] if "active" in t.columns else t
    t = t[(t["transform"] != "bernoulli") & ~t.pid.astype(str).str.startswith("scene_")]
    mod = {x[0]: m.__name__.rsplit(".", 1)[-1] for m in mech.modules() for x in m.MECHANISMS}
    pm = [mod.get(k) or ("body" if str(k).startswith("body") else "membrane") for k in t.mechanism]
    signs = [s.id for s in vitals.SIGNS]
    scored = [s.id for s in vitals.SIGNS if s.band() is not None]
    obs_trace = [READ_FROM.get(s, "membrane") if READ_FROM.get(s, "").startswith("organs") else "membrane"
                 for s in signs]
    _, trace = density(pm, obs_trace, signs, scored, list(E) + [("body", "obs", r) for r in readers],
                       (writers, readers))
    # conservative closure
    silent = sorted({p for p in pm if p not in g["writes"] and p not in ("membrane", "body", "observation")})
    vca = sorted(f.stem for f in (SRC / "mech").glob("*.py") if re.search(r"ctx\.(v|ca)\b", f.read_text()))
    pm_c = [READOUT.get(k, "membrane") if p == "observation" else p for p, k in zip(pm, t.mechanism)]
    obs_c = [["membrane"] + ([READ_FROM[s]] if s in READ_FROM else []) for s in signs]
    edges_c = list(E) + [("membrane", "muscle", "body")] + [("body", "obs", r) for r in readers]
    _, stat = density(pm_c, obs_c, signs, scored, edges_c, (sorted(set(writers) | set(silent)),
                                                            sorted(set(readers) | set(vca))))
    every = sorted({p for p in pm_c if p not in ("membrane", "body") and not p.startswith("readout")})
    _, cons = density(pm_c, obs_c, signs, scored, edges_c, (every, sorted(set(readers) | set(vca))))
    out = dict(n_params=len(pm), n_signs=len(signs), scored=scored, writers=writers, obs_readers=readers,
               silent_in_trace=silent, reads_v_or_ca=vca, n_edges=len(E), trace=trace, static=stat, conservative=cons,
               params_by_module={m: int(pm.count(m)) for m in sorted(set(pm))}, wall_s=time.time() - t0)
    Path(sys.argv[1]).write_text(json.dumps(out, indent=1))
    print(json.dumps({k: out[k] for k in ("n_params", "silent_in_trace", "reads_v_or_ca", "wall_s")}))
    for k in ("trace", "static", "conservative"):
        print(k, json.dumps({kk: v for kk, v in out[k].items()}, indent=None))


if __name__ == "__main__":
    main()
