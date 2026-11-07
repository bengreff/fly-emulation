"""Fit 1, pre-launch check on a frozen tree: builds the fit's worm once (so the nrnmech compile happens before the
16 workers start), prints the mechanisms, whether the readout reads the brain's Ca, the state after warm-up, and
the template's response statistics for two stimulations, written to OUT as JSON so two trees can be compared.

    python freeze_check.py OUT.json [h_dt mech_dt window_s]
    python freeze_check.py compare A.json B.json     # what changed between two trees
"""
import json
import sys
import time

import numpy as np

import fit1_core as fc

TOG = {"quantal_noise": "off", "channel_noise": "off"}


def main(out, h_dt="5.0", mech_dt="10", window_s="10"):
    B = fc.bounds()
    vals = {p: B[p][0] for p in fc.IDS}
    t0 = time.time()
    E = fc.Experiment(vals, ["ASHL", "AWAL"], h_dt=float(h_dt), mech_dt=float(mech_dt), warm_s=5.0, toggles=TOG)
    v = np.array([s(0.5).v for s in E.b.soma])
    r = E.run(["ASHL", "AWAL"], window_s=float(window_s), pulse_ms=500.0)
    res = dict(bounds={p: B[p][:3] for p in fc.IDS}, mechs=[type(m).__module__.split(".")[-1] for m in E.b.mechs],
               brain_ca=bool(E.brain_ca), n_above_m20=int((v > -20).sum()), v_median=float(np.median(v)),
               targets=list(r["targets"]), names=list(E.b.cell_names), stat=np.asarray(r["stat"]).tolist(),
               finite=bool(np.isfinite(r["stat"]).all()), wall_s=round(time.time() - t0, 1))
    json.dump(res, open(out, "w"))
    print({k: res[k] for k in ("mechs", "brain_ca", "n_above_m20", "v_median", "finite", "wall_s")})


def compare(a, b):
    A, B = json.load(open(a)), json.load(open(b))
    print("mechs added", sorted(set(B["mechs"]) - set(A["mechs"])), "removed", sorted(set(A["mechs"]) - set(B["mechs"])))
    print("bounds changed", {p: (A["bounds"].get(p), v) for p, v in B["bounds"].items() if A["bounds"].get(p) != v})
    print("brain_ca", A["brain_ca"], B["brain_ca"], "above -20 mV", A["n_above_m20"], B["n_above_m20"])
    if A["names"] == B["names"] and A["targets"] == B["targets"]:
        d = np.abs(np.array(B["stat"]) - np.array(A["stat"]))
        print("stat max |diff|", float(d.max()), "rms", float(np.sqrt((d ** 2).mean())), "cell",
              A["names"][int(np.argmax(d.max(1)))])
    else:
        print("different cells or targets")


if __name__ == "__main__":
    compare(*sys.argv[2:4]) if sys.argv[1] == "compare" else main(*sys.argv[1:5])
