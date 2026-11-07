"""Fit 1 worker: one worm (parameter vector) on a list of stimulated targets, in its own process (NEURON holds one
simulator per process). Reads a job json, writes the statistic matrix to job['out'] (npz) and a done line.

    python fit1_worker.py job.json
"""
import json
import os
import sys
import time

import numpy as np

import fit1_core as fc


def main(job_path):
    J = json.load(open(job_path))
    t0 = time.time()
    B = fc.bounds()
    vals = fc.to_values(np.array(J["x"], float), B)
    vals.update(J.get("fixed", {}))
    E = fc.Experiment(vals, J["targets"], toggles=J.get("toggles"), shuffle_seed=J.get("shuffle_seed"),
                      h_dt=J["h_dt"], mech_dt=J["mech_dt"], warm_s=J["warm_s"])
    r = E.run(J["targets"], window_s=J["window_s"], pulse_ms=J["pulse_ms"])
    info = dict(build_s=E.build_s, warm_wall=E.warm_wall, run_wall=r["run_wall"], total=time.time() - t0,
                shuffle=getattr(E.b, "shuffle_info", None))
    tmp = J["out"] + ".tmp.npz"                       # written whole, then renamed: a killed job leaves no result
    np.savez(tmp, stat=r["stat"].astype(np.float32), names=np.array(E.b.cell_names),
             targets=np.array(r["targets"]), info=json.dumps(info), vals=json.dumps(vals))
    os.replace(tmp, J["out"])
    print("done", json.dumps(info), flush=True)


if __name__ == "__main__":
    main(sys.argv[1])
