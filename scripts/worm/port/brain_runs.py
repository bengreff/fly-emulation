"""Neural-only runs of src/wormemu/brain.py (pre-registered in docs/worm/BRAIN_PORT.md section 3).

    python brain_runs.py --run ref|port302b|port302c --out DIR [--ref_npz port302a/run.npz] [--no_stim]

Every lumped layer toggle off; test input +20 pA at ALML, ALMR, AVM, PLML, PLMR from 2 to 4 s; 6 s.
Writes run.npz (soma V and Ca at 1 ms, cell names) and summary.json (bars G1-G3, R1 for ref, reported numbers).
--no_stim gives the matching control (runs are deterministic, so stim minus no-stim is the touch effect alone).
"""
import argparse
import json
import os
import re
import resource
import time

import numpy as np

from wormemu import brain_layers
from wormemu.brain import Brain, sample_worm
from wormemu.brain_structure import bwm_name

TOUCH = ["ALML", "ALMR", "AVM", "PLML", "PLMR"]
RUNS = {"ref": dict(literature_overrides="off", wiring="baaiworm"),
        "port302b": dict(literature_overrides="on", wiring="baaiworm"),
        "port302c": dict(literature_overrides="on", wiring="cook"),
        "port302c_rs": dict(literature_overrides="on", wiring="cook", receptor_sign="on")}     # section 4b, D5


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--run", choices=list(RUNS), required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--ref_npz", default="")
    ap.add_argument("--tstop_ms", type=int, default=6000)
    ap.add_argument("--no_stim", action="store_true")
    ap.add_argument("--scale_chem", type=float, default=1.0)    # diagnosis only (section 4): weight of every
    ap.add_argument("--scale_gap", type=float, default=1.0)     # placed synapse / gap junction point process
    ap.add_argument("--off_until_ms", type=int, default=0)      # every connection x0 before this time
    a = ap.parse_args()
    os.makedirs(a.out, exist_ok=True)
    toggles = dict(RUNS[a.run], sign_rule="transmitter", **{m[0]: "off" for m in brain_layers.MECHANISMS})
    t0 = time.time()
    b = Brain(sample_worm(None), toggles=toggles, keep_mcvl24=a.run == "ref")
    t_build = time.time() - t0
    names = b.cell_names
    stim = np.array([b.idx[n] for n in TOUCH])
    w0 = [(pp, pp.weight, "gapjunction" in pp.hname()) for pp in b.conn]

    def scale(on):
        for pp, w, gap in w0:
            pp.weight = w * (a.scale_gap if gap else a.scale_chem) * on
    scale(0.0 if a.off_until_ms else 1.0)
    b.reset()
    V = np.empty((a.tstop_ms, len(names)), np.float32)
    CA = np.empty_like(V)
    t1 = time.time()
    for k in range(a.tstop_ms):
        if a.off_until_ms and k == a.off_until_ms:
            scale(1.0)
        b.extra_pA[stim] = 20.0 if 2000 <= k < 4000 and not a.no_stim else 0.0
        o = b.step()
        V[k], CA[k] = o.v_mV, o.ca_uM
    t_sim = time.time() - t1
    np.savez_compressed(os.path.join(a.out, "run.npz"), V=V.T, Ca=CA.T, names=np.array(names),
                        is_muscle=b.is_muscle, dt_rec_ms=1.0)

    neur = ~b.is_muscle
    other = neur & ~np.isin(names, TOUCH)
    pre, dur = V[1000:2000].mean(0), V[2000:4000].mean(0)
    d = np.abs(dur - pre)
    s = dict(run=a.run, no_stim=a.no_stim, scale_chem=a.scale_chem, scale_gap=a.scale_gap,
             off_until_ms=a.off_until_ms,
             above_m20_names=[n for n, x, m in zip(names, V[-1], b.is_muscle) if x > -20 and not m],
             toggles=toggles, n_cells=len(names), n_neurons=int(neur.sum()), n_segments=b.n_segments,
             placed=dict(b.placed), build_s=round(t_build, 1), sim_s=round(t_sim, 1),
             wall_s_per_bio_s=round(t_sim / (a.tstop_ms / 1000.0), 2),
             maxrss_MB=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss // 1024,
             G1_finite=bool(np.isfinite(V).all()),
             G2_range_mV=[float(V[100:].min()), float(V[100:].max())],
             G2_pass=bool(V[100:].min() >= -100 and V[100:].max() <= 60),
             G3_n_moved=int((d[other] >= 1.0).sum()), G3_max=[names[int(np.argmax(np.where(other, d, 0)))],
                                                               float(d[other].max())],
             G3_pass=bool((d[other] >= 1.0).any()),
             above_m20_at_6s=int((V[-1, neur] > -20).sum()),
             median_mean_1_2s=float(np.median(pre[neur])), p90_mean_1_2s=float(np.percentile(pre[neur], 90)),
             muscles_moved=int((d[b.is_muscle] >= 1.0).sum()),
             muscle_range_mV=[float(V[100:, b.is_muscle].min()), float(V[100:, b.is_muscle].max())])
    if a.ref_npz:
        r = np.load(a.ref_npz)
        ri = {(bwm_name(n) or n) if re.fullmatch(r"MC[DV][LR]\d\d", n) else n: i for i, n in enumerate(r["names"])}
        ix = np.array([ri[n] for n in names])
        dv = np.abs(r["V"][ix, 1:a.tstop_ms + 1].T - V)          # their record starts at t = 0
        s.update(R1_max_dV_mV=float(np.nanmax(dv)), R1_median_cell_max_dV_mV=float(np.median(dv.max(0))),
                 R1_worst_cell=names[int(np.argmax(dv.max(0)))], R1_pass=bool(np.nanmax(dv) <= 1.0))
    json.dump(s, open(os.path.join(a.out, "summary.json"), "w"), indent=1)
    print(json.dumps(s))


if __name__ == "__main__":
    main()
