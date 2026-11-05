"""Build and run BAAIWorm's network on all 302 neurons and 96 body-wall muscle cells (runs on backhouse).

Ported as published (Zhao et al. 2024, BAAIWorm commit b99ca5a, Apache 2.0): the NEURON morphologies, the per-cell
channel densities (5 shared neuron sets, 1 passive muscle set), the graded synapse and gap-junction mods, and the
seeded connection construction of eworm/network/transform.py:config2detailed (tanh-compressed contact counts,
inverse-Gaussian distances, nearest segment pairs within 1 um). BAAIWorm itself only ever ran the 136-neuron subset;
here cells_id_sim is every neuron plus the muscles, which their code supports but their config lacks
(dir_info['muscle_neuron_con'] and the muscle names are supplied here).

Two changes from the published code, both switchable:
  --sign transmitter (default): a synapse from a neuron whose fast transmitter is GABA only (Wang et al. 2024,
      CeNGEN fallback; syn_sign.csv) is inhibitory, everything else excitatory. Literature over the ported value:
      BAAIWorm builds every synapse excitatory before training. --sign allexc reproduces the published rule.
  The trained 136-neuron weights are not used (they hold 13 of 65 cells at non-physical voltages, down to -1648 mV
      in the shipped v_final_eworm_v4.npy; and they are per-synapse fits).

Output (--out): run.npz (soma V and Ca at 1 ms for every cell, names, timings), connections.csv (every placed
synapse and gap junction), summary.json.
"""
import argparse
import csv
import json
import os
import resource
import sys
import time

import numpy as np

B = os.path.expanduser("~/worm-port/BAAIWorm")
sys.path.insert(0, B)
from neuron import h  # noqa: E402
from eworm.network import transform  # noqa: E402

TOUCH = ["ALML", "ALMR", "AVM", "PLML", "PLMR"]


def muscle_names():
    model = os.path.join(B, "eworm_learn", "components", "model")
    return sorted(f[:-4] for f in os.listdir(model)
                  if f.startswith("MC") and f[:-4] not in ("MCL", "MCR") and f.endswith(".hoc")
                  and f != "MuscleCell.hoc")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--seed", type=int, default=1)
    ap.add_argument("--tstop", type=float, default=6000.0)
    ap.add_argument("--sign", choices=["transmitter", "allexc"], default="transmitter")
    ap.add_argument("--stim_nA", type=float, default=0.02)
    ap.add_argument("--signs", default=os.path.expanduser("~/worm-port/syn_sign.csv"))
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    os.makedirs(a.out, exist_ok=True)

    cfg = json.load(open(os.path.join(B, "eworm", "network", "config.json")))
    names = dict(cfg["cell_info"]["cells_name_dic"])
    mus = muscle_names()
    assert len(names) == 302 and len(mus) == 96, (len(names), len(mus))
    for i, m in enumerate(mus):
        names[str(302 + i)] = m
    cfg["cell_info"]["cells_name_dic"] = names
    cfg["cell_info"]["cells_id_sim"] = [str(i) for i in range(302 + 96)]
    cfg["dir_info"]["model_dir"] = "../eworm_learn/components/model/"
    cfg["dir_info"]["muscle_neuron_con"] = "components/param/connection/muscle_neuron.xlsx"

    np.random.seed(a.seed)                 # their `if seed:` skips seed 0, so seed here
    t0 = time.time()
    circ = transform.config2detailed(cfg, None, None, load_hoc=True, rec_voltage=False, seed=None)
    t_build = time.time() - t0

    sign = {r["cell"]: int(r["sign"]) for r in csv.DictReader(open(a.signs))}
    n_flip = 0
    if a.sign == "transmitter":
        for c in circ.connections:
            if c.category == "syn" and c.pre_cell is not None and not c.pre_cell.is_muscle \
                    and sign[c.pre_cell.name] < 0 and c.weight > 0:
                c.update_info(-c.weight)
                n_flip += 1

    rows, kinds = [], {}
    for c in circ.connections:
        if c.pre_segment is None or c.post_segment is None:
            continue
        pm, qm = c.pre_cell.is_muscle, c.post_cell.is_muscle
        k = ("gj" if c.category == "gj" else "syn") + ("_nmj" if qm and not pm else "_mn" if pm and not qm else "")
        kinds[k] = kinds.get(k, 0) + 1
        rows.append((c.pre_cell.name, c.pre_segment.index, c.post_cell.name, c.post_segment.index, c.category,
                     c.weight))
    with open(os.path.join(a.out, "connections.csv"), "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["pre", "pre_seg", "post", "post_seg", "category", "weight"])
        w.writerows(rows)

    cells = circ.cells
    vrec = [h.Vector().record(c.hoc_obj.Soma(0.5)._ref_v, 1.0) for c in cells]
    carec = [h.Vector().record(c.hoc_obj.Soma(0.5)._ref_cai, 1.0) for c in cells]
    stims = []
    for c in cells:
        if c.name in TOUCH:
            s = h.IClamp(c.hoc_obj.Soma(0.5))
            s.delay, s.dur, s.amp = 2000.0, 2000.0, a.stim_nA
            stims.append(s)

    h.dt, h.secondorder = 0.5, 0
    h.finitialize(-65.0)
    t1, aborted = time.time(), None
    t = 0.0
    while t < a.tstop:
        t = min(t + 100.0, a.tstop)
        h.continuerun(t)
        v_now = np.array([c.hoc_obj.Soma(0.5).v for c in cells])
        if not np.isfinite(v_now).all():
            aborted = f"non-finite V at t={t} ms"
            break
    t_sim = time.time() - t1

    V = np.array([np.array(v) for v in vrec], dtype=np.float32)
    CA = np.array([np.array(x) for x in carec], dtype=np.float32)
    np.savez_compressed(os.path.join(a.out, "run.npz"), V=V, Ca=CA, names=np.array([c.name for c in cells]),
                        is_muscle=np.array([c.is_muscle for c in cells]), dt_rec_ms=1.0)
    n_seg = sum(len(c.segments) for c in cells)
    summary = dict(seed=a.seed, tstop_ms=a.tstop, sign_rule=a.sign, stim_nA=a.stim_nA, stim_cells=TOUCH,
                   stim_window_ms=[2000, 4000], n_cells=len(cells), n_neurons=sum(not c.is_muscle for c in cells),
                   n_muscles=sum(c.is_muscle for c in cells), n_segments=n_seg, connections=kinds,
                   n_syn_made_inhibitory=n_flip, build_s=round(t_build, 1), sim_s=round(t_sim, 1),
                   wall_s_per_bio_s=round(t_sim / (t / 1000.0), 2), maxrss_MB=resource.getrusage(
                       resource.RUSAGE_SELF).ru_maxrss // 1024, aborted=aborted, dt_ms=h.dt)
    json.dump(summary, open(os.path.join(a.out, "summary.json"), "w"), indent=1)
    print(json.dumps(summary))


if __name__ == "__main__":
    main()
