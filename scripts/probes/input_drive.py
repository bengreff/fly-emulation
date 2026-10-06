"""Mean synaptic drive onto named cells in a finished assay run, split by presynaptic type (diagnostic).

For current-based synapses (cond off) a presynaptic spike adds w mV to i_syn, which decays with tau_s,
and i_syn is the steady-state depolarisation (lif.Network.step). So the mean drive is
sum over input edges of rate_pre (Hz) x w (mV) x tau_s (ms) / 1000 (derived; it ignores the timing of
spikes, the refractory period and the intrinsic currents). Rates come from the run's rates.npz
(mean over trials at one stimulus rate); w is the network's final edge weight under the run's profile.

    uv run python scripts/probes/input_drive.py --run runs/assay-legsugar3_mn9-m9r-ffi_sil --profile m9r \
        --cells 26764,523040 --rate 200 --silence-ids runs/s12/ffi/ids.txt
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))
from flyemu import connectome, lif, profiles  # noqa: E402
from flyemu.registry import Policy, Registry  # noqa: E402


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--run", required=True)
    ap.add_argument("--profile", required=True)
    ap.add_argument("--cells", default="")
    ap.add_argument("--types", default="", help="cell types; all their cells are added to --cells")
    ap.add_argument("--rate", default="200")
    ap.add_argument("--silence-ids", default="", help="cells whose output the run silenced")
    ap.add_argument("--top", type=int, default=8)
    ap.add_argument("--min-synapses", type=int, default=profiles.WORKING_MIN_SYNAPSES)
    ap.add_argument("--out", default="")
    a = ap.parse_args()
    reg = Registry(Policy.MINIMAL)
    profiles.apply(reg, a.profile)
    conn = connectome.build(reg, min_synapses=a.min_synapses)
    p = lif.default_params(reg, conn, timestep_ms=0.1)
    if p.cond:
        raise SystemExit("conductance synapses: the mean-drive formula does not apply")
    net = lif.Network(conn, p, 0.1, rng=np.random.default_rng(0))
    z = np.load(Path(a.run) / "rates.npz")
    ks = sorted(k for k in z.files if k.startswith(f"real_{a.rate}_"))
    rate = pd.Series(np.mean([z[k] for k in ks], axis=0), index=z["body_id"]).reindex(conn.neurons.bodyId).fillna(0).to_numpy().copy()
    if a.silence_ids:
        sil = conn.index_of(np.loadtxt(a.silence_ids, dtype=np.int64, ndmin=1))
        rate[sil[sil >= 0]] = 0.0                     # output removed in the run
    pre_of = np.repeat(np.arange(conn.n), np.diff(conn.indptr))
    tau_s = np.broadcast_to(np.asarray(p.tau_s, np.float32), (conn.n,))
    nrn = conn.neurons
    ptype = nrn.type.fillna("untyped").to_numpy()[pre_of]
    out = {"run": a.run, "profile": a.profile, "rate": a.rate, "trials": len(ks), "cells": {}}
    bids = [int(x) for x in a.cells.split(",") if x]
    bids += [int(x) for t in a.types.split(",") if t for x in nrn.bodyId[nrn.type == t]]
    for b, i in zip(bids, conn.index_of(np.array(bids, dtype=np.int64))):
        m = conn.indices == i
        d = rate[pre_of[m]] * net.w[m] * tau_s[i] / 1000.0
        s = pd.Series(d).groupby(ptype[m]).sum()
        s = s[s != 0].sort_values()
        out["cells"][str(b)] = {"instance": str(nrn.instance.iat[i]), "own_rate_hz": round(float(rate[i]), 2),
                                "exc_mV": round(float(d[d > 0].sum()), 2), "inh_mV": round(float(d[d < 0].sum()), 2),
                                "net_mV": round(float(d.sum()), 2),
                                "top_inh": {k: round(float(v), 2) for k, v in s.head(a.top).items() if v < 0},
                                "top_exc": {k: round(float(v), 2) for k, v in s[::-1].head(a.top).items() if v > 0}}
    print(json.dumps(out, indent=1))
    if a.out:
        Path(a.out).write_text(json.dumps(out, indent=1))


if __name__ == "__main__":
    main()
