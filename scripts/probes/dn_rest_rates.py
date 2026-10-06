"""Tonic descending drive at rest (Director lead, 5 Oct 03:00; F-STAND-3): does the model have any?

Runs the organism as the silence gate does (all senses on, the fly lying where it settles), counts
spikes from 200 ms to --ms, then removes all afferent drive for --silent-ms and counts again over the
last 200 ms. Reports, for descending neurons (circuit class DN): how many fire, their rates, the
named types with published recordings, and for each active DN the drive it receives by presynaptic
class and type (spikes x signed efficacy, summed over the window). Also lists which cell types
carry an intrinsic spontaneous drive (`spontaneous_drive` > 0); only those fire without input.

    PYTHONPATH=src uv run python scripts/probes/dn_rest_rates.py [--seed 12 --ms 1200]
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "src"))
# DN types with published electrophysiology or imaging (names as in the male-cns type column)
NAMED = ("DNa01", "DNa02", "DNp01", "DNp02", "DNp07", "DNp09", "DNp10", "DNg02", "DNb02", "DNa05",
         "DNg11", "DNp42", "DNp50", "MDN", "DNb05", "DNb06", "DNa15", "DNg13")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--ms", type=float, default=1200.0)
    ap.add_argument("--silent-ms", type=float, default=300.0)
    ap.add_argument("--seed", type=int, default=12)
    ap.add_argument("--set", action="append", default=[])
    ap.add_argument("--out", default=str(REPO / "runs" / "s12" / "dnrest"))
    a = ap.parse_args()
    from flyemu.lif import circuit_classes
    from flyemu.organism import Organism
    from flyemu.profiles import WORKING_PROFILE
    ov = {"motor_unit:all|force_per_spike": 10.0}
    ov.update({k: float(v) for k, v in (s.split("=") for s in a.set)})
    org = Organism(policy="minimal", profile=WORKING_PROFILE, min_synapses=5, seed=a.seed, overrides=ov)
    conn, n = org.conn, org.conn.neurons
    cls = circuit_classes(conn)
    ty = n.type.fillna("untyped").to_numpy().astype(str)
    dn = cls == "DN"
    dt = org.timestep_ms
    cnt = np.zeros(conn.n)
    z = []
    for s in range(int(a.ms / dt)):
        obs = org.body.observe()
        sp = org.net.step(external_mv=org.sense(s, obs))
        if s * dt >= 200:
            cnt[sp] += 1
        org.motor_step(sp)
        if s % 100 == 0:
            z.append(float(obs["body_positions"][0, 2]))
    scnt = np.zeros(conn.n)
    ns = int(a.silent_ms / dt)
    for s in range(ns):
        org.body.observe()
        sp = org.net.step(external_mv=np.zeros(conn.n, np.float32))
        if s >= ns - int(200 / dt):
            scnt[sp] += 1
        org.motor_step(sp)
    hz = cnt / ((a.ms - 200) / 1e3)
    spont = np.broadcast_to(np.asarray(org.net.params.spont_mv, np.float32), (conn.n,))
    # drive into each active DN by presynaptic class: sum over edges of pre spikes x efficacy
    act = np.flatnonzero(dn & (hz > 0))
    pre_of = np.repeat(np.arange(conn.n), np.diff(conn.indptr))
    eff = np.asarray(conn.efficacy_mv, np.float64) * np.asarray(conn.sign, np.float64)[pre_of]
    contrib, contrib_t = {}, {}
    sel = np.isin(conn.indices, act)
    for p, q, e in zip(pre_of[sel], conn.indices[sel], eff[sel]):
        if cnt[p] == 0:
            continue
        d = contrib.setdefault(int(q), {})
        d[cls[p]] = d.get(cls[p], 0.0) + float(cnt[p] * e)
        d2 = contrib_t.setdefault(int(q), {})
        d2[ty[p]] = d2.get(ty[p], 0.0) + float(cnt[p] * e)
    hzd = hz[dn]
    res = dict(
        seed=a.seed, profile=WORKING_PROFILE, overrides=ov, ms=a.ms, thorax_z_mm_final=round(z[-1], 3),
        n_dn=int(dn.sum()), n_dn_types=int(len(set(ty[dn]))),
        dn_frac_active=round(float((hzd > 0).mean()), 4), dn_n_active=int((hzd > 0).sum()),
        dn_hz_mean=round(float(hzd.mean()), 3), dn_hz_median=round(float(np.median(hzd)), 3),
        dn_hz_mean_of_active=round(float(hzd[hzd > 0].mean()), 2) if (hzd > 0).any() else 0.0,
        dn_silent_spikes_last200ms=int(scnt[dn].sum()),
        dn_with_spont_drive=int((spont[dn] > 0).sum()),
        types_with_spont_drive=sorted(set(ty[spont > 0])),
        n_cells_with_spont_drive=int((spont > 0).sum()),
        named={t: dict(n=int(((ty == t) & dn).sum()), hz=np.round(hz[(ty == t) & dn], 1).tolist())
               for t in NAMED if ((ty == t) & dn).any()},
        named_absent=[t for t in NAMED if not ((ty == t) & dn).any()],
        active=[dict(row=int(r), bodyId=int(n.bodyId.iloc[r]), type=ty[r], hz=round(float(hz[r]), 1),
                     drive_mv_by_class={k: round(v, 1) for k, v in
                                        sorted(contrib.get(int(r), {}).items(), key=lambda kv: -abs(kv[1]))[:5]},
                     drive_mv_by_type={k: round(v, 1) for k, v in
                                       sorted(contrib_t.get(int(r), {}).items(), key=lambda kv: -abs(kv[1]))[:5]})
                for r in act[np.argsort(-hz[act])]],
    )
    out = Path(a.out); out.mkdir(parents=True, exist_ok=True)
    (out / f"dn_rest_s{a.seed}.json").write_text(json.dumps(res, indent=1))
    print(json.dumps({k: v for k, v in res.items() if k != "active"}, indent=1))
    for r in res["active"][:30]:
        print(r)


if __name__ == "__main__":
    main()
