"""Rung-1 failure diagnosis (session 11): single-cell f-I curves at the channel priors,
all channels vs leak-only vs each spike-triggered channel removed. Unconnected cell,
m4 membrane (tau 20 ms, rest/reset -52, threshold -45, refractory 2.2 ms), dt 0.1 ms,
1 s of constant drive (mV of steady depolarisation). Rates in Hz (measured in the model).

    uv run python scripts/probes/intrinsic_fi.py
"""
import json
import sys

import numpy as np

sys.path.insert(0, "src"); sys.path.insert(0, "tests")
from flyemu import channels  # noqa: E402
from test_channels import _net  # noqa: E402

DRIVES = [7.5, 8, 9, 10, 12, 15, 20, 30]
prior = {c: p for c, (_, _, _, p) in channels.CHANNELS.items()}
variants = {"leak_only": None, "all": prior,
            **{f"all_minus_{c}": {k: (0.0 if k == c else v) for k, v in prior.items()} for c in ("Kv2", "BK", "SK")},
            "subthreshold_only": {k: (0.0 if k in ("Kv2", "BK", "SK") else v) for k, v in prior.items()}}
n = len(DRIVES)
out = {}
for name, g in variants.items():
    net = _net(None if g is None else {c: np.full(n, v) for c, v in g.items()}, n=n)
    cnt = np.zeros(n, int)
    for _ in range(10000):
        cnt[net.step(external_mv=np.asarray(DRIVES, np.float32))] += 1
    out[name] = dict(zip(map(str, DRIVES), cnt.tolist()))
    print(f"{name:20s}", cnt.tolist())
json.dump({"drives_mV": DRIVES, "rates_hz": out}, open("runs/s11/rung1/fi.json", "w"), indent=1)
