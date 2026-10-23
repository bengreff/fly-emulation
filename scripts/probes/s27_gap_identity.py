"""s27 (fly2): bit-identity of a profile across a code change, with the gap-junction pathways driven.

Builds the organism, drives the giant fibre, the DLM motoneurons and a sparse whole-brain sample with fixed
kicks, and hashes every spike (step, cell), the final membrane potentials and the gap table. Run it before and
after a change: equal hashes mean the change leaves the profile bit-identical on this drive.

    .venv/bin/python scripts/probes/s27_gap_identity.py --tag before
    .venv/bin/python scripts/probes/s27_gap_identity.py --tag dlmn --set "electrical:^DLMn->^DLMn|gap_coupling=0.05"
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path

import numpy as np

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "src"))

from flyemu import profiles  # noqa: E402
from flyemu.organism import Organism  # noqa: E402


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--profile", default="m10f")
    ap.add_argument("--tag", required=True)
    ap.add_argument("--steps", type=int, default=3000)
    ap.add_argument("--seed", type=int, default=12)
    ap.add_argument("--set", action="append", default=[], help="override key=value")
    a = ap.parse_args()
    extra = {k: float(v) for k, v in (s.rsplit("=", 1) for s in a.set)}
    org = Organism(policy="minimal", profile=a.profile, min_synapses=profiles.WORKING_MIN_SYNAPSES,
                   seed=a.seed, overrides=extra)
    net = org.net
    t = org.conn.neurons.type.fillna("").to_numpy()
    gf = np.flatnonzero(t == "DNp01")
    dlmn = np.flatnonzero(np.char.startswith(t.astype(str), "DLMn"))
    sample = np.arange(0, org.conn.n, 997)
    h = hashlib.sha256()
    n_spk, n_dlmn = 0, 0
    for s in range(a.steps):
        kick = None
        if s % 500 == 100:
            kick = (gf, 100.0)
        elif s % 700 == 350:
            kick = (dlmn, 100.0)
        elif s % 250 == 0:
            kick = (sample, 20.0)
        sp = np.asarray(net.step(kick=kick), np.int64)
        n_spk += sp.size
        n_dlmn += int(np.isin(sp, dlmn).sum())
        h.update(np.int64(s).tobytes())
        h.update(np.sort(sp).tobytes())
    hv = hashlib.sha256(np.asarray(net.v, np.float64).tobytes()).hexdigest()
    hg = "none"
    if net.gap is not None:
        g = hashlib.sha256()
        for k in sorted(net.gap):
            g.update(k.encode())
            g.update(np.ascontiguousarray(net.gap[k]).tobytes())
        hg = g.hexdigest()
    out = {"probe": "s27_gap_identity", "profile": a.profile, "tag": a.tag, "overrides": extra,
           "steps": a.steps, "seed": a.seed, "spikes": n_spk, "dlmn_spikes": n_dlmn,
           "spike_hash": h.hexdigest(), "v_hash": hv, "gap_hash": hg,
           "gap_pairs": 0 if net.gap is None else int(len(net.gap["a"]))}
    d = REPO / "runs" / "s27"
    d.mkdir(parents=True, exist_ok=True)
    (d / f"identity_{a.tag}.json").write_text(json.dumps(out, indent=1))
    print(json.dumps(out))


if __name__ == "__main__":
    main()
