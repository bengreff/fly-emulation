"""s20 N3: mushroom-body resting rates under class noise, plasticity off (pre-registered DECISIONS 22 Oct 22:23).

Isolated CNS, no body, no stimulus. `class:DAN|noise` and `class:MBON|noise` (mV/sqrt(ms)) are set by override;
everything else is the profile (m10f3: no N21 KC->MBON learning in this checkout; N22 forgetting asserted off).
Settle, then read: per-cell spike counts, per-type rates for the MB types, class means, whole-brain mean rate and
active fraction, and the membrane SD (spike steps excluded) of the fit-target cells.

    .venv/bin/python scripts/probes/s20_mb_rest.py --dan 1.0 --mbon 1.0 --seed 12 --out runs/s20/mb/g1.0_s12.json
"""
from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))
from flyemu import connectome, electrical, lif, profiles  # noqa: E402
from flyemu.registry import Policy, Registry  # noqa: E402

DT = 0.1
# Huang et al. 2024 Fig. 1 folder name -> male-cns type (instance labels; PPL106 = alpha3 by its 860-synapse
# output onto MBON14, checked s20)
HUANG = {"PPL1-v1": "PPL101", "PPL1-v2": "PPL103", "PPL1-a`3": "PPL104", "PPL1-a2": "PPL105", "PPL1-a3": "PPL106",
         "MBON-v1": "MBON11", "MBON-v2": "MBON12", "MBON-a`2": "MBON13", "MBON-a3": "MBON14",
         "MBON-a`3m": "MBON17", "MBON-a2sc": "MBON18"}
FIT = {"PPL105": (8.0, 6.0, 10.0), "MBON14": (12.1, 12.1 / 1.25, 12.1 * 1.25)}


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--profile", default="m10f3")
    ap.add_argument("--dan", type=float, help="class:DAN|noise, mV/sqrt(ms) (default: the profile's)")
    ap.add_argument("--mbon", type=float, help="class:MBON|noise, mV/sqrt(ms) (default: the profile's)")
    ap.add_argument("--stage", action="store_true",
                    help="s23 stage check: allow N22 forgetting (a no-op without depression); N21 must still be 0")
    ap.add_argument("--seed", type=int, default=12)
    ap.add_argument("--settle-ms", type=float, default=500.0)
    ap.add_argument("--read-ms", type=float, default=4000.0)
    ap.add_argument("--out", type=Path, required=True)
    a = ap.parse_args()
    t0 = time.time()
    reg = Registry(Policy.MINIMAL)
    profiles.apply(reg, a.profile)
    if a.dan is not None:
        reg.overrides["class:DAN|noise"] = a.dan
    if a.mbon is not None:
        reg.overrides["class:MBON|noise"] = a.mbon
    a.dan = float(reg.overrides.get("class:DAN|noise", 0.0))
    a.mbon = float(reg.overrides.get("class:MBON|noise", 0.0))
    allowed = {"cell_type:all|kc_mbon_forgetting", "cell_type:all|kc_mbon_memory_tau_h"} if a.stage else set()
    if not a.stage:
        assert float(reg.overrides.get("cell_type:all|kc_mbon_forgetting", 0.0)) == 0.0, "N22 must be off"
    assert not any("kc_mbon" in k and k not in allowed and float(v) for k, v in reg.overrides.items()), \
        "KC->MBON plasticity must be off"
    conn = connectome.build(reg, min_synapses=profiles.WORKING_MIN_SYNAPSES)
    params = lif.default_params(reg, conn, timestep_ms=DT)
    el = electrical.build(reg, conn)
    net = lif.Network(conn, params, DT, rng=np.random.default_rng(a.seed))
    net.elec = el if len(el[0]) else None
    types = conn.neurons.type.fillna("").to_numpy(str)
    cls = lif.circuit_classes(conn)
    for _ in range(int(a.settle_ms / DT)):
        net.step()
    n_read = int(a.read_ms / DT)
    counts = np.zeros(conn.n, np.int64)
    tgt = np.flatnonzero(np.isin(types, list(FIT)))
    s1 = np.zeros(tgt.size); s2 = np.zeros(tgt.size); nv = np.zeros(tgt.size)
    for _ in range(n_read):
        sp = net.step()
        np.add.at(counts, sp, 1)
        v = np.asarray(net.v[tgt], float)
        ok = ~np.isin(tgt, sp)
        s1[ok] += v[ok]; s2[ok] += v[ok] ** 2; nv[ok] += 1
    hz = counts / (a.read_ms / 1000.0)
    sd = np.sqrt(np.maximum(s2 / nv - (s1 / nv) ** 2, 0.0))
    mb = sorted({t for t in types if t.startswith(("PPL1", "PPL2", "PAM", "MBON", "KC", "APL", "DPM"))})
    out = {"profile": a.profile, "dan_noise": a.dan, "mbon_noise": a.mbon, "seed": a.seed,
           "settle_ms": a.settle_ms, "read_ms": a.read_ms,
           "whole_brain_hz": float(hz.mean()), "active_frac": float((counts > 0).mean()),
           "class_hz": {c: float(hz[cls == c].mean()) for c in ("DAN", "MBON", "KC", "APL", "DPM")},
           "class_active": {c: float((counts[cls == c] > 0).mean()) for c in ("DAN", "MBON", "KC", "APL", "DPM")},
           "type_hz": {t: float(hz[types == t].mean()) for t in mb},
           "huang_types_hz": {k: float(hz[types == v].mean()) for k, v in HUANG.items()},
           "fit_targets": {t: {"model_hz": float(hz[types == t].mean()), "target": FIT[t][0], "band": FIT[t][1:],
                               "membrane_sd_mv": float(sd[types[tgt] == t].mean())} for t in FIT},
           "wall_s": round(time.time() - t0, 1)}
    a.out.parent.mkdir(parents=True, exist_ok=True)
    a.out.write_text(json.dumps(out, indent=1))
    print(json.dumps({k: out[k] for k in ("whole_brain_hz", "class_hz", "fit_targets", "wall_s")}, indent=1))


if __name__ == "__main__":
    main()
