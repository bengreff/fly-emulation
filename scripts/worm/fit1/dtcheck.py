"""Fit 1 step 4: does the fit's integration (h_dt, mech_dt) match brain.py's own path (0.5 ms, mechanisms every
1 ms) on the statistic the fit scores? Full 302-neuron brain, template values except the actuator at 1 nS (so the
responses are not all near zero), three stimulations and the control, 30 s windows. Writes LABEL.npz (stat matrix,
cell names, wall times). No data is read.

    python dtcheck.py h_dt mech_dt label ['{"obs_opto_g_nS": 2.0, ...}']   (optional value overrides)
"""
import json
import sys
import time

import numpy as np

import fit1_core as fc

TARGETS = ["AVAL", "ASHL", "AWAL"]


def main(h_dt, mech_dt, label, over="{}", window_s=30.0):
    B = fc.bounds()
    vals = {pid: B[pid][0] for pid in fc.IDS}
    vals["obs_opto_g_nS"] = 1.0
    vals.update(json.loads(over))
    t0 = time.time()
    E = fc.Experiment(vals, TARGETS, h_dt=float(h_dt), mech_dt=float(mech_dt))
    r = E.run(TARGETS, window_s=float(window_s))
    info = dict(label=label, h_dt=float(h_dt), mech_dt=float(mech_dt), over=json.loads(over), build_s=E.build_s, warm_wall=E.warm_wall,
                walls=r["wall"], total=time.time() - t0)
    np.savez(label + ".npz", stat=r["stat"], names=np.array(E.b.cell_names), ctrl=r["ctrl"],
             F=np.stack([r["F"][t] for t in TARGETS]), info=json.dumps(info))
    print(json.dumps(info), flush=True)
    for k, tg in enumerate(TARGETS):
        S = r["stat"][:, k]
        top = np.argsort(-np.abs(S))[:6]
        print(tg, "self", round(float(S[E.b.idx[tg]]), 4), [(E.b.cell_names[j], round(float(S[j]), 4)) for j in top])


if __name__ == "__main__":
    main(*sys.argv[1:5])
