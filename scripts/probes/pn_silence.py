"""Diagnostic: why are most uniglomerular PNs silent with Hallem ORN input?

Network only (no body stepping needed beyond sensing at rest). Default 600 ms,
rates from the last 400 ms; `dur_ms=` and `seed=` arguments change this (rates
then over the second half; session 7 uses dur_ms=2000 because ORN depression
recovers with tau 893 ms). Per glomerulus: ORN rate, ORN->PN synapses per PN,
PN rate, and the PN's mean steady excitatory/inhibitory input.
"""
import sys

import numpy as np
import pandas as pd

sys.path.insert(0, "src")
from flyemu.organism import Organism  # noqa: E402
from flyemu.profiles import WORKING_PROFILE  # noqa: E402

ov = {k: float(v) for k, v in (a.split("=") for a in sys.argv[1:])}
dur = int(ov.pop("dur_ms", 600)); seed = int(ov.pop("seed", 0))
steps = int(round(dur / 0.1)); start = 2000 if dur == 600 else steps // 2
org = Organism(policy="minimal", profile=WORKING_PROFILE, min_synapses=5, overrides=ov, seed=seed)
n = org.conn.neurons
t = n.type.fillna("").to_numpy().astype(str)
cnt = np.zeros(org.conn.n)
for s in range(steps):
    obs = org.body.observe()
    sp = org.net.step(external_mv=org.sense(s, obs))
    org.motor_step(sp)
    if s >= start:
        cnt[sp] += 1
hz = cnt / ((steps - start) * 1e-4)
ip, ix = org.conn.indptr, org.conn.indices
pre = np.repeat(np.arange(org.conn.n), np.diff(ip))
upn = np.flatnonzero((n["class"].fillna("") == "ALPN").to_numpy() & np.char.endswith(t, "PN"))
rows = []
for c in upn:
    m = ix == c
    w, pr = org.net.w[m], pre[m]
    contrib = w * hz[pr] * 5.0 / 1000.0
    orn = np.char.startswith(t[pr], "ORN_")
    rows.append(dict(pn=t[c], hz=hz[c], orn_syn=org.conn.weight_syn[m][orn].sum(),
                     orn_hz=hz[pr][orn].mean() if orn.any() else np.nan,
                     exc_mV=contrib[contrib > 0].sum(), inh_mV=contrib[contrib < 0].sum(),
                     orn_mV=contrib[orn].sum()))
df = pd.DataFrame(rows)
print("overrides", ov, "dur_ms", dur, "seed", seed)
print(f"{len(df)} uPNs; active {(df.hz > 0.5).mean():.2f}; rate median {df.hz.median():.1f}, mean {df.hz.mean():.1f}")
df["active"] = df.hz > 0.5
print(df.groupby("active")[["orn_syn", "orn_hz", "orn_mV", "exc_mV", "inh_mV", "hz"]].median().round(2))
print("\nPNs with zero ORN synapses (>=5-syn edges):", int((df.orn_syn == 0).sum()))
# top inhibitors of silent PNs
sil = df[~df.active].index
inh = []
for k in sil:
    c = upn[k]; m = ix == c; w, pr = org.net.w[m], pre[m]
    contrib = w * hz[pr] * 5.0 / 1000.0
    inh.append(pd.DataFrame({"type": t[pr], "mV": contrib}))
inh = pd.concat(inh).groupby("type").mV.sum().sort_values() / len(sil)
print("\nmean input to a silent PN by presynaptic type (mV):"); print(inh.head(8).round(3)); print(inh.tail(5).round(3))
