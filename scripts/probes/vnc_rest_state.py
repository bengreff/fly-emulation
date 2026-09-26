"""Diagnostic: resting state of model VNC interneuron hemilineages vs Agrawal 2020.

Closed loop at rest, 800 ms (last 500 ms scored). For T1 cells of the 13B,
10B and 9A hemilineages (type prefix IN13B/IN10B/IN09A): mean V (absolute,
m2 V_rest = -52 mV), fraction firing > 0.5 Hz, median rate.
"""
import sys

import numpy as np
import pandas as pd

sys.path.insert(0, "src")
from flyemu.organism import Organism  # noqa: E402

org = Organism(policy="minimal", profile="m2", min_synapses=5)
n = org.conn.neurons
t = n.type.fillna("")
groups = {h: np.flatnonzero((t.str.startswith(h) & (n.somaNeuromere == "T1")).to_numpy())
          for h in ["IN13B", "IN10B", "IN09A", "IN13A", "IN21A", "IN03A"]}
cnt = np.zeros(org.conn.n); vs = {h: [] for h in groups}
for s in range(8000):
    obs = org.body.observe(); sp = org.net.step(external_mv=org.sense(s, obs))
    org.body.actuate(org.nm.step(sp, 0.1)); org.body.set_adhesion(org.nm.grip); org.body.step()
    if s >= 3000:
        cnt[sp] += 1
        if s % 20 == 0:
            for h, g in groups.items():
                vs[h].append(org.net.v[g])
hz = cnt / 0.5
rows = []
for h, g in groups.items():
    v = np.array(vs[h]).mean(axis=0)
    rows.append(dict(hemilineage=h, cells=len(g), v_mean=round(float(v.mean()), 1),
                     v_p10_p90=[round(float(x), 1) for x in np.percentile(v, [10, 90])],
                     frac_firing=round(float((hz[g] > 0.5).mean()), 2),
                     median_hz_firing=round(float(np.median(hz[g][hz[g] > 0.5])) if (hz[g] > 0.5).any() else 0.0, 1)))
print(pd.DataFrame(rows).to_string(index=False))
