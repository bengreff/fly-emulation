"""Fit 1 step 4: compare dtcheck.py runs with the reference (brain.py's own step). For each run and target: the RMS
and largest difference of the statistic over all cells, against the fit's noise scale (s_floor 0.030), and wall time.

    python dtcompare.py ref.npz a.npz b.npz c.npz
"""
import json
import sys

import numpy as np


def main(ref, *runs):
    R = np.load(ref)
    ri = json.loads(str(R["info"]))
    print(ri["label"], "walls", {k: round(v, 1) for k, v in ri["walls"].items()})
    for p in runs:
        Z = np.load(p)
        zi = json.loads(str(Z["info"]))
        d = Z["stat"] - R["stat"]
        rms = np.sqrt(np.mean(d ** 2, axis=0))
        mx = np.abs(d).max(axis=0)
        rr = [float(np.corrcoef(Z["stat"][:, k], R["stat"][:, k])[0, 1]) for k in range(d.shape[1])]
        print(zi["label"], f"h_dt {zi['h_dt']} mech_dt {zi['mech_dt']}", "rms", np.round(rms, 5).tolist(),
              "max", np.round(mx, 5).tolist(), "r", np.round(rr, 4).tolist(),
              "wall per window", round(float(np.mean(list(zi["walls"].values()))), 1))


if __name__ == "__main__":
    main(*sys.argv[1:])
