"""s22 MB type spread (Director item 3), no simulation: the m10f3 network built as in `s20_mb_rest.py` (fitted class
noise, plasticity off), then for each Huang type the mean synaptic drive at rest, split by source.

Drive = sum over incoming edges of the network's final signed weight (mV per presynaptic spike) x the presynaptic
rate at rest (Hz), in mV/s. Rates: MB types from the s21 confirm run (`runs/s20/mb/confirm_s12.json`, seed 12);
every other cell at that run's whole-brain mean. Also the per-cell intrinsic rows (tau_m, threshold gap) and the
drive the KCs would add per 1 Hz of KC firing (candidate 1 of `docs/research/s22_mb_type_spread.md`).

    PYTHONPATH=src python scripts/probes/s22_mb_rest_drive.py
"""
from __future__ import annotations

import json
import sys
import time
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))
from flyemu import connectome, lif, profiles  # noqa: E402
from flyemu.registry import Policy, Registry  # noqa: E402

DT = 0.1
CONFIRM = Path("runs/s20/mb/confirm_s12.json")
OUT = Path("runs/s20/mb/rest_drive.json")
TYPES = ["MBON11", "PPL101", "PPL106", "MBON12", "PPL103", "MBON13", "MBON14", "PPL105", "MBON17", "MBON18", "PPL104"]


def main() -> None:
    t0 = time.time()
    c = json.loads(CONFIRM.read_text())
    reg = Registry(Policy.MINIMAL)
    reg.overrides["class:DAN|noise"] = c["dan_noise"]
    reg.overrides["class:MBON|noise"] = c["mbon_noise"]
    profiles.apply(reg, c["profile"])
    assert float(reg.overrides.get("cell_type:all|kc_mbon_forgetting", 0.0)) == 0.0, "N22 must be off"
    assert not any("kc_mbon" in k and float(v) for k, v in reg.overrides.items()), "KC->MBON plasticity must be off"
    conn = connectome.build(reg, min_synapses=profiles.WORKING_MIN_SYNAPSES)
    params = lif.default_params(reg, conn, timestep_ms=DT)
    net = lif.Network(conn, params, DT, rng=np.random.default_rng(c["seed"]))
    print(f"built {conn.n} cells, {time.time() - t0:.0f} s", flush=True)
    types = conn.neurons.type.fillna("").to_numpy(str)
    rate = np.full(conn.n, float(c["whole_brain_hz"]))
    for t, hz in c["type_hz"].items():
        rate[types == t] = hz
    is_kc = np.char.startswith(types, "KC")
    is_mb = np.isin(types, list(c["type_hz"]))
    pre = np.repeat(np.arange(conn.n), np.diff(conn.indptr))
    post = conn.indices
    w = np.asarray(net.w, np.float64)
    out = {"profile": c["profile"], "dan_noise": c["dan_noise"], "mbon_noise": c["mbon_noise"],
           "units": "mV/s (signed weight x presynaptic Hz), per cell", "types": {}}
    for t in TYPES:
        cells = np.flatnonzero(types == t)
        e = np.isin(post, cells)
        we, pe = w[e], pre[e]
        d = we * rate[pe]
        k = len(cells)
        row = {
            "cells": k,
            "model_hz": c["type_hz"].get(t),
            "exc_mb": float(d[(we > 0) & is_mb[pe]].sum() / k),
            "inh_mb": float(d[(we < 0) & is_mb[pe]].sum() / k),
            "exc_other": float(d[(we > 0) & ~is_mb[pe]].sum() / k),
            "inh_other": float(d[(we < 0) & ~is_mb[pe]].sum() / k),
            "kc_per_hz": float(we[is_kc[pe]].sum() / k),
            "kc_syn_weight_mean": float(we[is_kc[pe]].mean()) if is_kc[pe].any() else 0.0,
            "tau_m_ms": float(np.mean(net.tau_m[cells])),
            "gap_mv": float(np.mean(net.v_th[cells] - net.v_rest[cells])),
            "input_gain": float(np.mean(net.input_gain[cells])),
        }
        row["net"] = row["exc_mb"] + row["inh_mb"] + row["exc_other"] + row["inh_other"]
        out["types"][t] = row
        print(t, json.dumps({kk: round(v, 3) if isinstance(v, float) else v for kk, v in row.items()}), flush=True)
    OUT.write_text(json.dumps(out, indent=1))
    print(f"wall {time.time() - t0:.0f} s")


if __name__ == "__main__":
    main()
