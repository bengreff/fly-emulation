"""s29 (fly2): which fly geoms touch the floor before and during a GF take-off (m10f5, seed 12).

Diagnostic for the B15 lift-off detector (DECISIONS s29 B15 result). Prints every MuJoCo contact pair at t0, after a
100 ms settle, and every 0.5 ms for 15 ms after one GF volley. Output kept at runs/s29/contacts_diag.log (gitignored).

    PYTHONPATH=src python scripts/probes/s29_contacts_diag.py
"""
import sys

import mujoco as mj
import numpy as np

sys.path.insert(0, "src")
from flyemu.organism import Organism  # noqa: E402

np.random.seed(12)
org = Organism(policy="minimal", profile="m10f5", min_synapses=5, seed=12)
m, d = org.body.sim.mj_model, org.body.sim.mj_data
print("contact_names", org.body.contact_names)


def dump(tag):
    rows = []
    for i in range(d.ncon):
        g1, g2 = d.contact[i].geom1, d.contact[i].geom2
        b1, b2 = m.geom_bodyid[g1], m.geom_bodyid[g2]
        rows.append((mj.mj_id2name(m, mj.mjtObj.mjOBJ_BODY, b1), mj.mj_id2name(m, mj.mjtObj.mjOBJ_GEOM, g1),
                     mj.mj_id2name(m, mj.mjtObj.mjOBJ_BODY, b2), mj.mj_id2name(m, mj.mjtObj.mjOBJ_GEOM, g2)))
    print(tag, d.ncon, rows)


dump("t0")
for _ in range(1000):
    org.motor_step(org.net.step())
dump("settled")
print("qpos z", d.qpos[2])
t = org.conn.neurons.type.fillna("").to_numpy()
gf = np.flatnonzero(t == "DNp01")
for s in range(150):
    sp = org.net.step(kick=(gf, 50.0) if s == 0 else None)
    org.motor_step(sp)
    if s % 5 == 0:
        dump(f"s{s/10:.1f}ms z={d.qpos[2]:.3f}")
