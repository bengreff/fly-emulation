"""Femur-tibia resistance reflex in the closed loop (session 11).

The brain/VNC model runs with all senses; the thorax is held --tether-mm up and
one femur-tibia joint is moved by the experimenter (qpos/qvel overwritten each
step: a position clamp, the joint's own muscles cannot move it). From 300 ms the
joint follows q_start + amp sin(2 pi f t); before that it is held at q_start.
Reported: spike rates of the MNs mapped to that joint's +1 and -1 muscles
(Hill mode, org.hill.mn_muscle) while the joint is imposed to flex (q falling;
the -1 muscle is the flexor) and to extend, and during the hold.

A resistance reflex (insect femoral chordotonal organ -> VNC -> tibia MNs)
predicts the +1 (extensor) pool fires more during imposed flexion and the -1
(flexor) pool more during imposed extension.

    uv run python scripts/probes/resistance_reflex.py [--leg lf] [--seed 0] [--out X.json]
"""
import argparse
import json
import sys

import mujoco
import numpy as np

sys.path.insert(0, "src")
from flyemu.organism import Organism  # noqa: E402
from flyemu.profiles import WORKING_PROFILE  # noqa: E402


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--leg", default="lf")
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--f", type=float, default=2.0, help="imposed sine frequency (Hz)")
    ap.add_argument("--amp", type=float, default=0.4, help="imposed sine amplitude (rad)")
    ap.add_argument("--ms", type=float, default=1300.0)
    ap.add_argument("--tether-mm", type=float, default=5.0)
    ap.add_argument("--no-body-afferents", action="store_true", help="control: body mechanosensory drive zeroed")
    ap.add_argument("--set", action="append", default=["motor_unit:all|force_per_spike=10"])
    ap.add_argument("--out", default="")
    a = ap.parse_args()
    ov = {k: float(v) for k, v in (s.split("=") for s in a.set)}
    org = Organism(policy="minimal", profile=WORKING_PROFILE, min_synapses=5, overrides=ov, seed=a.seed)
    assert org.hill is not None, "Hill mode required (muscle:leg|model)"
    dt = org.timestep_ms
    m, d = org.body.sim.mj_model, org.body.sim.mj_data
    pre = org.body.fly.name + "/"
    jn = f"{a.leg}_trochanterfemur-{a.leg}_tibia-pitch"
    j = mujoco.mj_name2id(m, mujoco.mjtObj.mjOBJ_JOINT, pre + jn)
    qa, dv = m.jnt_qposadr[j], m.jnt_dofadr[j]
    h, nm = org.hill, org.nm
    pools = {}
    for sgn in (+1, -1):
        k = np.flatnonzero((h.p.joint == jn) & (h.p.direction == sgn))
        pools[sgn] = np.asarray(nm.mn_index)[np.isin(h.mn_muscle, k)]
    af = org.aff
    st = af.subtype if af.subtype is not None else np.full(len(af.rows), "")
    aff_groups = {g: af.rows[(af.leg == a.leg) & (st == g)] for g in np.unique(st[af.leg == a.leg]) if g}
    acnt = {g: {"hold": 0, "flexing": 0, "extending": 0} for g in aff_groups}
    # relay interneurons: >= 20 synapses from this leg's claw/hook afferents and >= 20 onto either pool
    c = org.conn
    fe = np.concatenate([aff_groups.get(g, np.array([], int)) for g in ("claw", "hook_flex", "hook_ext")])
    syn_in = np.zeros(c.n)
    for i in fe:
        np.add.at(syn_in, c.indices[c.indptr[i]:c.indptr[i + 1]], c.weight_syn[c.indptr[i]:c.indptr[i + 1]])
    allpool = np.concatenate(list(pools.values()))
    relay = []
    for k in np.flatnonzero(syn_in >= 20):
        post, w = c.indices[c.indptr[k]:c.indptr[k + 1]], c.weight_syn[c.indptr[k]:c.indptr[k + 1]]
        so = {sgn: int(w[np.isin(post, ids)].sum()) for sgn, ids in pools.items()}
        if max(so.values()) >= 20 and k not in allpool:
            relay.append((int(k), so))
    rcnt = {k: {"hold": 0, "flexing": 0, "extending": 0} for k, _ in relay}
    typ = org.conn.neurons.type.fillna("").to_numpy()
    if a.no_body_afferents:
        z = np.zeros(org.conn.n, dtype=np.float32)
        org.aff.drive = lambda obs: z
    q0 = d.qpos[:7].copy()
    q0[2] += a.tether_mm
    q_start = None
    lo, hi = m.jnt_range[j]
    bins = {"hold": [0, 0.0], "flexing": [0, 0.0], "extending": [0, 0.0]}
    cnt = {sgn: {b: 0 for b in bins} for sgn in pools}
    for s in range(int(a.ms / dt)):
        t = s * dt
        obs = org.body.observe()
        sp = org.net.step(external_mv=org.sense(s, obs))
        org.motor_step(sp)
        d.qpos[:7] = q0
        d.qvel[:6] = 0.0
        if t >= 200 and q_start is None:
            q_start = float(np.clip(d.qpos[qa], lo + a.amp + 0.05, hi - a.amp - 0.05))
        if q_start is not None:
            ph = 2 * np.pi * a.f * max(t - 300, 0.0) / 1000
            d.qpos[qa] = q_start + (a.amp * np.sin(ph) if t >= 300 else 0.0)
            v = a.amp * 2 * np.pi * a.f * np.cos(ph) if t >= 300 else 0.0
            d.qvel[dv] = v
            b = "hold" if t < 300 else ("flexing" if v < 0 else "extending")
            if t >= 210:
                bins[b][1] += dt
                for sgn, ids in pools.items():
                    cnt[sgn][b] += int(np.isin(sp, ids).sum())
                for g, ids in aff_groups.items():
                    acnt[g][b] += int(np.isin(sp, ids).sum())
                for k in np.intersect1d(sp, [r[0] for r in relay]):
                    rcnt[int(k)][b] += 1
    rate = {sgn: {b: round(1000 * cnt[sgn][b] / max(bins[b][1], 1e-9) / max(len(pools[sgn]), 1), 2)
                  for b in bins} for sgn in pools}
    out = {"leg": a.leg, "joint": jn, "seed": a.seed, "f_hz": a.f, "amp_rad": a.amp,
           "q_start": round(q_start, 3), "no_body_afferents": a.no_body_afferents, "overrides": ov,
           "n_mn": {str(k): int(len(v)) for k, v in pools.items()},
           "rate_hz_per_mn": {("+1 (ext)" if k > 0 else "-1 (flex)"): v for k, v in rate.items()},
           "ext_flexing_over_extending": round((rate[1]["flexing"] + 1e-3) / (rate[1]["extending"] + 1e-3), 2),
           "flex_extending_over_flexing": round((rate[-1]["extending"] + 1e-3) / (rate[-1]["flexing"] + 1e-3), 2),
           "afferent_rate_hz_per_cell": {g: {"n": int(len(aff_groups[g])), **{b: round(1000 * acnt[g][b] / max(bins[b][1], 1e-9) / max(len(aff_groups[g]), 1), 1) for b in bins}} for g in aff_groups},
           "relay_interneurons": [{"type": typ[k], "sign": int(c.sign[k]), "syn_from_feco": int(syn_in[k]),
                                   "syn_to_ext": so[1], "syn_to_flex": so[-1],
                                   **{b: round(1000 * rcnt[k][b] / max(bins[b][1], 1e-9), 1) for b in bins}}
                                  for k, so in relay],
           "rate_max_hz": float(af.rate_max_hz),
           "warnings": int(d.warning.number.sum())}
    print(json.dumps(out))
    if a.out:
        with open(a.out, "w") as f:
            json.dump(out, f, indent=1)


if __name__ == "__main__":
    main()
