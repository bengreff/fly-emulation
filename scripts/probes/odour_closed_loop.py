"""Closed-loop check: an odour near the antennae, m2 profile. PN recruitment
and whole-brain rate with vs without the odour."""
import sys; sys.path.insert(0, 'src')
import numpy as np, pandas as pd
from flyemu.organism import Organism
from flyemu.profiles import WORKING_PROFILE  # noqa: E402
from flyemu.world import OdourSource

res = {}
for label in ("clean air", "odour"):
    org = Organism(policy="minimal", profile=WORKING_PROFILE, min_synapses=5,
                   overrides={"motor_unit:all|force_per_spike": 10.0})
    if label == "odour":
        tun = org.chem.tuning
        odour = tun.columns[tun.astype(bool).sum().argmax()]
        head = org.body.sim.mj_data.xpos[org.chem.antenna_bodies[0]]
        org.world.odours = [OdourSource(odour, head.copy(), 1e-2, 5.0)]
    counts = np.zeros(org.conn.n)
    n_steps = 3000
    for step in range(n_steps):
        obs = org.body.observe()
        spk = org.net.step(external_mv=org.sense(step, obs))
        counts[spk] += 1
        org.body.actuate(org.nm.step(spk, org.timestep_ms)); org.body.set_adhesion(org.nm.grip); org.body.step()
    n = org.conn.neurons; cls = n['class'].fillna('')
    hz = counts / 0.3
    res[label] = dict(mean_hz=hz.mean(), orn_hz=hz[org.chem.rows][org.chem.kind == 'orn'].mean(),
                      pn_active=int(((hz > 0) & cls.eq('ALPN').to_numpy()).sum()),
                      pn_hz=hz[cls.eq('ALPN').to_numpy()].mean(),
                      kc_active=int(((hz > 0) & n.type.fillna('').str.startswith('KC').to_numpy()).sum()),
                      active=int((hz > 0).sum()))
    if label == "odour": res[label]['odour'] = odour
print(pd.DataFrame(res).to_string())
