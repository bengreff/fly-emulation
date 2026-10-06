"""Rung 8 (N29) probe: antennal-lobe rates around an odour step, with and without
short-term plasticity per connection class.

Closed loop, working profile, fly at rest. Clean air for --pre-ms, then the most
broadly activating DoOR odour at the antennae (as odour_closed_loop.py) until
--ms. Rates of ORNs, uniglomerular PNs (class ALPN, type ending PN) and AL local
neurons (class ALLN) in 50 ms bins. Transience = (late - base) / (peak - base):
base = last 500 ms of clean air, peak = highest bin in the first 300 ms of odour,
late = last 500 ms. Writes <out>.npz (bins) and <out>.json (summary).

    uv run python scripts/probes/stp_al.py --set 'synapse:all|per_synapse_parameters=1' --out runs/s12/stp/on_s12
"""
import argparse
import json
import sys
import time

import numpy as np

sys.path.insert(0, "src")
from flyemu.organism import Organism  # noqa: E402
from flyemu.profiles import WORKING_PROFILE  # noqa: E402
from flyemu.world import OdourSource  # noqa: E402

DT, BIN = 0.1, 50.0


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--set", action="append", default=[])
    ap.add_argument("--seed", type=int, default=12)
    ap.add_argument("--pre-ms", type=float, default=1500.0)
    ap.add_argument("--ms", type=float, default=3500.0)
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    ov = {k: float(v) for k, v in (s.rsplit("=", 1) for s in a.set)}
    t0 = time.time()
    org = Organism(policy="minimal", profile=WORKING_PROFILE, min_synapses=5, overrides=ov,
                   seed=a.seed)
    n = org.conn.neurons
    cls, typ = n["class"].fillna("").to_numpy(), n.type.fillna("").to_numpy().astype(str)
    groups = {"ORN": np.char.startswith(typ, "ORN_"),
              "uPN": (cls == "ALPN") & np.char.endswith(typ, "PN"),
              "LN": cls == "ALLN"}
    tun = org.chem.tuning
    odour = tun.columns[tun.astype(bool).sum().argmax()]
    steps, on, per = int(a.ms / DT), int(a.pre_ms / DT), int(BIN / DT)
    rates = {g: np.zeros(steps // per) for g in groups}
    for s in range(steps):
        if s == on:
            head = org.body.sim.mj_data.xpos[org.chem.antenna_bodies[0]]
            org.world.odours = [OdourSource(odour, head.copy(), 1e-2, 5.0)]
        obs = org.body.observe()
        spk = org.net.step(external_mv=org.sense(s, obs))
        org.motor_step(spk)
        hit = np.zeros(org.conn.n, bool)
        hit[spk] = True
        for g, m in groups.items():
            rates[g][s // per] += hit[m].sum()
    t = (np.arange(steps // per) + 0.5) * BIN
    out = {"odour": odour, "seed": a.seed, "overrides": ov, "wall_s": round(time.time() - t0)}
    for g, m in groups.items():
        r = rates[g] / m.sum() / (BIN / 1000.0)            # mean Hz per cell
        rates[g] = r
        base = r[(t >= a.pre_ms - 500) & (t < a.pre_ms)].mean()
        peak = r[(t >= a.pre_ms) & (t < a.pre_ms + 300)].max()
        late = r[t >= a.ms - 500].mean()
        out[g] = {"n": int(m.sum()), "base_hz": round(float(base), 3), "peak_hz": round(float(peak), 3),
                  "late_hz": round(float(late), 3),
                  "transience": round(float((late - base) / (peak - base)), 3) if peak > base else None}
    np.savez(a.out + ".npz", t_ms=t, **rates)
    with open(a.out + ".json", "w") as f:
        json.dump(out, f, indent=1)
    print(json.dumps(out))


if __name__ == "__main__":
    main()
