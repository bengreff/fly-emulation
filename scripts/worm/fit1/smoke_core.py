"""Fit 1: smoke test of fit1_core on a small brain (Mac): builds, warms, runs two stimulations and the control,
then the shuffled wiring. Prints the statistic for the targets and a few responders."""
import sys
import time

import numpy as np

import fit1_core as fc

CELLS = ["AVAL", "AVAR", "AVBL", "AVBR", "AVDL", "AVDR", "AVEL", "AVER", "ASHL", "ASHR", "AIBL", "AIBR", "RIML",
         "RIMR", "AIYL", "AIYR", "AIZL", "AIZR", "RIAL", "RIAR", "DVA", "PVCL", "PVCR", "AWCL", "AWCR"]


def main(warm=0.5, win=3.0):
    B = fc.bounds()
    for pid in fc.IDS:
        print(pid, B[pid])
    vals = {pid: B[pid][0] for pid in fc.IDS}
    x = fc.to_x(vals, B)
    back = fc.to_values(x, B)
    print("round trip max rel err", max(abs(back[k] / vals[k] - 1) for k in vals))
    for sh in (None, 7):
        t0 = time.time()
        E = fc.Experiment(vals, ["AVAL", "ASHL"], shuffle_seed=sh, cells=CELLS, warm_s=warm)
        print("shuffle", sh, getattr(E.b, "shuffle_info", None), "build", round(E.build_s, 1), "warm",
              round(E.warm_wall, 1))
        r = E.run(["AVAL", "ASHL"], window_s=win)
        S = r["stat"]
        for k, tg in enumerate(r["targets"]):
            i = E.b.idx[tg]
            top = np.argsort(-np.abs(S[:, k]))[:5]
            print(tg, "self", round(S[i, k], 4), "top", [(E.b.cell_names[j], round(S[j, k], 4)) for j in top],
                  "wall", round(r["wall"][tg], 1))
        print("ctrl F range", float(r["ctrl"].min()), float(r["ctrl"].max()), "vols", r["ctrl"].shape)
        print("total", round(time.time() - t0, 1))


if __name__ == "__main__":
    main(*(float(a) for a in sys.argv[1:3]))
