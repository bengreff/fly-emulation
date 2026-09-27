"""Closed loop: the fly lands on a sugar patch. Do taste channels fire, and MN9?"""
import sys; sys.path.insert(0, 'src')
import numpy as np
from flyemu.organism import Organism
from flyemu.profiles import WORKING_PROFILE  # noqa: E402
from flyemu.extrasenses import FoodPatch
for label, food in (("no food", []), ("sugar patch", [FoodPatch(np.zeros(3), 100.0, {"sugar": 0.5})])):
    org = Organism(policy="minimal", profile=WORKING_PROFILE, min_synapses=5,
                   overrides={"motor_unit:all|force_per_spike": 10.0})
    org.world.food = food
    n = org.conn.neurons; mn9 = np.flatnonzero(n.instance.eq("MN9_L").to_numpy())
    counts = np.zeros(org.conn.n); tl = org.extra.channels["taste_leg"].rows
    lab = org.extra.channels["taste_labellar"].rows; drv_leg = 0.0
    for step in range(5000):
        obs = org.body.observe(); d = org.sense(step, obs)
        drv_leg = max(drv_leg, float(d[tl].max()))
        spk = org.net.step(external_mv=d); counts[spk] += 1
        org.motor_step(spk)
    hz = counts / 0.5
    print(f"{label:12s} leg-GRN max drive {drv_leg:5.1f} mV, leg GRN mean {hz[tl].mean():.2f} Hz, "
          f"labellar {hz[lab].mean():.2f} Hz, MN9_L {hz[mn9].mean():.1f} Hz, brain {hz.mean():.2f} Hz")
