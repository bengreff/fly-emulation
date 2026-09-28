"""Closed-loop regression check (DECISIONS session 6, criterion 2).

Runs the organism for --ms with all senses, then --silent-ms with all
afferent drive removed, and reports rates by group and the return to rest.

    uv run python scripts/probes/closed_loop_check.py [--set K=V ...] [--ms 1000]
"""
import argparse
import json
import sys
import time

import numpy as np

sys.path.insert(0, "src")
from flyemu.organism import Organism  # noqa: E402
from flyemu.profiles import WORKING_PROFILE  # noqa: E402


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--ms", type=float, default=1000.0)
    ap.add_argument("--silent-ms", type=float, default=300.0)
    ap.add_argument("--set", action="append", default=["motor_unit:all|force_per_spike=10"])
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--template", action="store_true",
                    help="all construction-template body switches on (model_data.TEMPLATE_SWITCHES)")
    a = ap.parse_args()
    ov = {k: float(v) for k, v in (s.split("=") for s in a.set)}
    if a.template:
        from flyemu.model_data import TEMPLATE_SWITCHES
        ov = {**TEMPLATE_SWITCHES, **ov}
    org = Organism(policy="minimal", profile=WORKING_PROFILE, min_synapses=5, overrides=ov, seed=a.seed)
    n = org.conn.neurons
    t = n.type.fillna("").to_numpy()
    orn = np.char.startswith(t.astype(str), "ORN_")
    upn = (n["class"].fillna("") == "ALPN").to_numpy() & np.char.endswith(t.astype(str), "PN")
    mn = (n.superclass.fillna("") == "vnc_motor").to_numpy()
    steps = int(a.ms / org.timestep_ms)
    cnt = np.zeros(org.conn.n)
    z, t0 = [], time.time()
    for s in range(steps):
        obs = org.body.observe()
        sp = org.net.step(external_mv=org.sense(s, obs))
        if s * org.timestep_ms >= 200:          # skip the opening transient
            cnt[sp] += 1
        org.motor_step(sp)
        if s % 100 == 0:
            z.append(float(obs["body_positions"][0, 2]))
        if sp.size > 20000:
            print(json.dumps({"runaway_at_ms": s * org.timestep_ms})); return
    dur = (a.ms - 200) / 1000
    hz = cnt / dur
    silent = []
    # cells with intrinsic tonic drive (e.g. slow MNs at their measured rest rate)
    # fire without input by design; the criterion concerns the network
    tonic = np.broadcast_to(np.asarray(org.net.params.spont_mv), (org.conn.n,)) > 0
    scnt = np.zeros(org.conn.n)
    for s in range(int(a.silent_ms / org.timestep_ms)):
        obs = org.body.observe()
        sp = org.net.step(external_mv=np.zeros(org.conn.n, np.float32))
        org.motor_step(sp)
        silent.append(int((~tonic[sp]).sum()))
        scnt[sp] += 1
    last = np.array(silent[-int(100 / org.timestep_ms):])
    out = {
        "whole_brain_hz": round(float(hz.mean()), 3),
        "whole_brain_excl_orn_hz": round(float(hz[~orn].mean()), 3),
        "orn_hz": round(float(hz[orn].mean()), 2),
        "upn_hz_mean": round(float(hz[upn].mean()), 2),
        "upn_hz_median": round(float(np.median(hz[upn])), 2),
        "upn_frac_active": round(float((hz[upn] > 0).mean()), 2),
        "motor_hz": round(float(hz[mn].mean()), 2),
        "cx_hz": {g: round(float(hz[np.char.startswith(t.astype(str), g)].mean()), 2)
                  for g in ("EPG", "PEN_", "PEG", "Delta7", "ER")},
        "silent_last100ms_spikes_per_ms": round(float(last.sum() / 100), 2),
        "thorax_z_mm_final": round(z[-1], 3), "thorax_z_mm_min": round(min(z), 3),
        "wall_s": round(time.time() - t0), "overrides": ov,
    }
    print(json.dumps(out))
    if last.sum() > 0:
        import pandas as pd
        df = pd.DataFrame({"type": n.type.fillna("untyped"), "sc": n.superclass.fillna(""),
                           "nt": n.predictedNt.fillna(""), "spk": scnt})
        g = df[df.spk > 0].groupby(["type", "sc", "nt"]).agg(cells=("spk", "size"), spikes=("spk", "sum"))
        print("SUSTAINED", int((scnt > 0).sum()), "cells")
        print(g.sort_values("spikes", ascending=False).head(25).to_string())


if __name__ == "__main__":
    main()
