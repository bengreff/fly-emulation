"""N12/N18 probe (s13, fly2): giant-fibre escape latency with gap junctions off and on.

Both giant fibres (DNp01) are kicked to one spike every --period-ms; the first spike of each
partner motoneuron (TTMn, PSI, DLMn) within --window-ms after the GF spike is recorded. Control
windows half a period later (no kick) give the chance rate of a spontaneous spike.
Latency to muscle = MN spike time - GF spike time + the MN type's conduction_delays.csv delay
(axon L/v with v inferred, plus 0.5 ms for the neuromuscular synapse, inferred), compared with
Augustin et al. 2017 PLoS Biol 15:e2001655 S1 Table (WT, brain stimulation through the eyes,
stimulus artifact to muscle EPSP onset; measured). The stimulus-to-GF-spike time is not
modelled. Isolated CNS: only the network is stepped (no body, no sensory drive; noise on).

    .venv/bin/python scripts/probes/gf_latency.py --profile m10f --trials 20 \\
        --out runs/s13/fly2/gf_latency_m10f.json
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "src"))
from flyemu import profiles  # noqa: E402
from flyemu.organism import Organism  # noqa: E402

MN_TYPES = ["TTMn", "PSI", "DLMn a, b", "DLMn c-f"]
# Augustin et al. 2017 S1 Table, WT brain stimulation, mean latency in ms (SEM where read)
REFERENCE = {"TTM": {"young": 0.926, "young_sem": 0.03, "mid": 1.097, "old": 1.216},
             "DLM": {"young": 1.440, "young_sem": 0.04, "mid": 1.593, "old": 1.849}}
BAND = {k: (round(v["young"] - 2 * v["young_sem"], 3), v["old"]) for k, v in REFERENCE.items()}


def run_arm(profile: str, gap: float, trials: int, period_ms: float, window_ms: float,
            settle_ms: float, seed: int, extra: dict | None = None) -> dict:
    org = Organism(policy="minimal", profile=profile, min_synapses=profiles.WORKING_MIN_SYNAPSES,
                   seed=seed, overrides={**(extra or {}), "electrical:all|gap_conductance": gap})
    net, dt = org.net, org.timestep_ms
    t = org.conn.neurons.type.fillna("").to_numpy()
    gf = np.flatnonzero(t == "DNp01")
    mns = {ty: np.flatnonzero(t == ty) for ty in MN_TYPES}
    delays = pd.read_csv(REPO / "data/params/conduction_delays.csv", comment="#").set_index("type").delay_ms
    settle, period, win = (int(round(x / dt)) for x in (settle_ms, period_ms, window_ms))
    kicks = [settle + i * period for i in range(trials)]
    controls = [k + period // 2 for k in kicks]
    n_steps = kicks[-1] + period
    spikes = []                                   # (step, cell) of every GF / MN spike
    watch = np.zeros(org.conn.n, bool)
    watch[gf] = True
    for ix in mns.values():
        watch[ix] = True
    kick_at = set(kicks)
    for s in range(n_steps):
        sp = net.step(kick=(gf, 100.0) if s in kick_at else None)
        for i in sp[watch[sp]]:
            spikes.append((s, int(i)))
    sp = pd.DataFrame(spikes, columns=["step", "cell"])

    def first_after(cells, s0):
        x = sp[sp.cell.isin(cells) & (sp.step > s0) & (sp.step <= s0 + win)]
        return x.groupby("cell").step.min()

    rows = []
    for trial, (k, c) in enumerate(zip(kicks, controls)):
        g = sp[sp.cell.isin(gf) & (sp.step >= k) & (sp.step <= k + 2)].step
        s_gf = int(g.min()) if len(g) else None
        for ty, ix in mns.items():
            fk = first_after(ix, s_gf) if s_gf is not None else pd.Series(dtype=int)
            fc = first_after(ix, c)
            for cell in ix:
                lat = (fk[cell] - s_gf) * dt if cell in fk.index else None
                rows.append({"trial": trial, "type": ty, "cell": int(cell), "gf_spiked": s_gf is not None,
                             "central_ms": lat,
                             "muscle_ms": None if lat is None else lat + float(delays[ty]),
                             "control_spike": cell in fc.index})
    df = pd.DataFrame(rows)
    out = {"gap_conductance": gap, "gf_cells": gf.tolist(), "trials": trials,
           "gf_spike_fraction": float(df.drop_duplicates("trial").gf_spiked.mean()),
           "mn_delay_ms": {ty: float(delays[ty]) for ty in MN_TYPES}, "types": {}}
    if org.net.gap is not None:
        out["gap_pairs"] = [[t[a], int(a), t[b], int(b), float(k)] for a, b, k in
                            zip(org.net.gap["a"], org.net.gap["b"], org.net.gap["k_ab"])]
    for ty, d in df.groupby("type"):
        lat = d.central_ms.dropna()
        out["types"][ty] = {
            "cells": int(d.cell.nunique()),
            "follow_fraction": float(d.central_ms.notna().mean()),
            "control_fraction": float(d.control_spike.mean()),
            "central_ms_median": float(lat.median()) if len(lat) else None,
            "central_ms_p10_p90": [float(lat.quantile(0.1)), float(lat.quantile(0.9))] if len(lat) else None,
            "muscle_ms_median": float(d.muscle_ms.dropna().median()) if len(lat) else None,
            "per_cell_follow": d.groupby("cell").central_ms.apply(lambda x: float(x.notna().mean())).to_dict(),
        }
    return out


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--profile", default="m10f")
    ap.add_argument("--trials", type=int, default=20)
    ap.add_argument("--period-ms", type=float, default=50.0)
    ap.add_argument("--window-ms", type=float, default=10.0)
    ap.add_argument("--settle-ms", type=float, default=200.0)
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--set", action="append", default=[], help="extra override entity|property=value")
    ap.add_argument("--out", type=Path, required=True)
    a = ap.parse_args()
    extra = {k: float(v) for k, v in (s.split("=", 1) for s in a.set)}
    res = {"probe": "gf_latency", "profile": a.profile, "reference": REFERENCE, "band_ms": BAND,
           "reference_source": "Augustin et al. 2017 PLoS Biol 15:e2001655 S1 Table (WT brain stimulation)",
           "overrides": extra, "arms": {}}
    for name, gap in (("gaps_off", 0.0), ("gaps_on", 1.0)):
        r = run_arm(a.profile, gap, a.trials, a.period_ms, a.window_ms, a.settle_ms, a.seed, extra)
        res["arms"][name] = r
        for ty, v in r["types"].items():
            print(f"{name:9s} {ty:10s} follow {v['follow_fraction']:.2f} (control {v['control_fraction']:.2f})"
                  f"  central {v['central_ms_median']}  muscle {v['muscle_ms_median']}", flush=True)
    for name, r in res["arms"].items():
        ttm, dlm = r["types"]["TTMn"], [r["types"][k] for k in ("DLMn a, b", "DLMn c-f")]
        dlm_ms = [x["muscle_ms_median"] for x in dlm if x["muscle_ms_median"] is not None]
        r["verdict"] = {
            "TTM_in_band": ttm["muscle_ms_median"] is not None
                           and BAND["TTM"][0] <= ttm["muscle_ms_median"] <= BAND["TTM"][1],
            "TTM_follow_ge_0.9": ttm["follow_fraction"] >= 0.9,
            "DLM_in_band": bool(dlm_ms) and all(BAND["DLM"][0] <= x <= BAND["DLM"][1] for x in dlm_ms)}
        print(name, r["verdict"])
    a.out.parent.mkdir(parents=True, exist_ok=True)
    a.out.write_text(json.dumps(res, indent=1, default=str))
    print("wrote", a.out)
