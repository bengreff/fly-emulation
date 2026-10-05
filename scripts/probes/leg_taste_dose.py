"""Leg/wing taste GRNs on a sugar patch: drive and firing rate per census type, for
`sense:taste_leg|modality_source` 0 (every type weak to every tastant, guessed) and
1 (types matched to receptor lines). Held-out check, not a fit: Ling et al. 2014
(J Neurosci 34:7148; secondary read, docs/research/s12_tarsal_grn_physiology.md)
report tarsal sugar GRNs at about 50-55 Hz to 100 mM sucrose, spontaneous below 3 Hz.

    uv run python scripts/probes/leg_taste_dose.py --source 1 --conc 0.1 [--ms 400 --settle-ms 100] [--out runs/s12/legtaste]
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "src"))


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--source", type=int, default=1)
    ap.add_argument("--conc", type=float, default=0.1, help="sucrose, M")
    ap.add_argument("--ms", type=float, default=400.0)
    ap.add_argument("--settle-ms", type=float, default=100.0, help="rates counted after this (fly drops onto the floor)")
    ap.add_argument("--seed", type=int, default=12)
    ap.add_argument("--out", default=str(REPO / "runs" / "s12" / "legtaste"))
    a = ap.parse_args()
    from flyemu.extrasenses import FoodPatch
    from flyemu.organism import Organism
    from flyemu.profiles import WORKING_PROFILE
    org = Organism(policy="minimal", profile=WORKING_PROFILE, min_synapses=5, seed=a.seed,
                   overrides={"motor_unit:all|force_per_spike": 10.0,
                              "sense:taste_leg|modality_source": a.source})
    org.world.food = [FoodPatch(np.zeros(3), 100.0, {"sugar": a.conc})] if a.conc > 0 else []
    n = org.conn.neurons
    tl = org.extra.channels["taste_leg"].rows
    lab = org.extra.channels["taste_labellar"].rows
    mn9 = np.flatnonzero(n.instance.eq("MN9_L").to_numpy() | n.instance.eq("MN9_R").to_numpy())
    steps = int(a.ms / org.timestep_ms); settle = int(a.settle_ms / org.timestep_ms)
    counts = np.zeros(org.conn.n)
    drive_max = np.zeros(len(tl))
    legs = ("lf", "lm", "lh", "rf", "rm", "rh")
    jt = [org.body.contact_names.index(f"{L}_tarsus5") for L in legs]
    touch = np.zeros(len(legs))                     # steps with tarsus 5 in contact, counting window
    for step in range(steps):
        obs = org.body.observe()
        d = org.sense(step, obs)
        drive_max = np.maximum(drive_max, d[tl])
        spk = org.net.step(external_mv=d)
        if step >= settle:
            counts[spk] += 1
            touch += np.linalg.norm(obs["contact_forces"], axis=-1)[jt] > 0
        org.motor_step(spk)
    hz = counts / ((a.ms - a.settle_ms) / 1e3)
    types = n.type.fillna("untyped").to_numpy()[tl]
    side = org.extra.channels["taste_leg"].side
    touch_frac = touch / max(steps - settle, 1)
    # rate per second of contact on the cell's own leg (cells with a leg assignment)
    t_contact = np.where(side < 6, touch[np.clip(side, 0, 5)] * org.timestep_ms / 1e3, np.nan)
    hz_contact = np.where(t_contact > 0, counts[tl] / np.where(t_contact > 0, t_contact, 1), np.nan)
    p = org.net.params
    def arr(x):
        return np.broadcast_to(np.asarray(x, float), (org.conn.n,))
    by_type = {}
    for ty in sorted(set(types)):
        k = types == ty
        r = tl[k]
        by_type[ty] = dict(n=int(k.sum()), drive_max_mv=round(float(drive_max[k].max()), 2),
                           hz_mean=round(float(hz[tl][k].mean()), 2), hz_max=round(float(hz[tl][k].max()), 1),
                           hz_per_contact_s=round(float(np.nanmean(hz_contact[k])), 1) if np.isfinite(hz_contact[k]).any() else None,
                           lif=dict(tau_m=round(float(arr(p.tau_m)[r].mean()), 2),
                                    th_minus_rest=round(float((arr(p.v_th) - arr(p.v_rest))[r].mean()), 2),
                                    reset_minus_rest=round(float((arr(p.v_reset) - arr(p.v_rest))[r].mean()), 2),
                                    t_ref=round(float(arr(p.t_ref)[r].mean()), 2),
                                    adapt_mv=round(float(arr(p.adapt_mv)[r].mean()), 3),
                                    tau_adapt=round(float(arr(p.tau_adapt)[r].mean()), 1)))
    res = dict(source=a.source, conc_M=a.conc, ms=a.ms, settle_ms=a.settle_ms, seed=a.seed, profile=WORKING_PROFILE,
               leg_drive_max_mv=round(float(drive_max.max()), 2), leg_hz_mean=round(float(hz[tl].mean()), 2),
               labellar_hz_mean=round(float(hz[lab].mean()), 2), mn9_hz=round(float(hz[mn9].mean()), 2),
               brain_hz_mean=round(float(hz.mean()), 3),
               tarsus5_contact_frac=dict(zip(legs, np.round(touch_frac, 3).tolist())), by_type=by_type)
    out = Path(a.out); out.mkdir(parents=True, exist_ok=True)
    (out / f"legtaste_src{a.source}_c{a.conc:g}_s{a.seed}.json").write_text(json.dumps(res, indent=1))
    print(json.dumps({k: v for k, v in res.items() if k != "by_type"}))
    for ty, r in by_type.items():
        print(f"  {ty:10s} n={r['n']:4d} drive {r['drive_max_mv']:6.2f} mV  {r['hz_mean']:6.2f} Hz (max {r['hz_max']}), "
              f"{r['hz_per_contact_s']} per contact-s, lif {r['lif']}")


if __name__ == "__main__":
    main()
