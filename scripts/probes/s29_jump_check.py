"""s29 (fly2) B15: GF escape take-off in the frontier profile against Card & Dickinson 2008 (pre-registered,
DECISIONS 23 Oct, before this probe was run).

One GF (DNp01) spike volley after a 100 ms settle, as tests/test_jump.py does for m4, then 40 ms of body.
Reported: the GF->TTMn latency, lift-off time (no fly-floor contact left), centre-of-mass speed averaged over
the first 2 ms after lift-off, peak COM speed and acceleration, and the middle-leg extension duration (CTr joint
moving in the TTM's depression direction: from 5 % of its peak angular velocity to the end of the movement).

    PYTHONPATH=src python scripts/probes/s29_jump_check.py --profile m10f5 --out runs/s29/jump_m10f5.json
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import mujoco as mj
import numpy as np

from flyemu.organism import Organism


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--profile", default="m10f5")
    ap.add_argument("--seed", type=int, default=12)
    ap.add_argument("--settle-ms", type=float, default=100.0)
    ap.add_argument("--ms", type=float, default=40.0)
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    np.random.seed(a.seed)
    org = Organism(policy="minimal", profile=a.profile, min_synapses=5, seed=a.seed)
    dt = org.timestep_ms
    t = org.conn.neurons.type.fillna("").to_numpy()
    gf, ttmn = np.flatnonzero(t == "DNp01"), np.flatnonzero(t == "TTMn")
    m, d = org.body.sim.mj_model, org.body.sim.mj_data
    root = mj.mj_name2id(m, mj.mjtObj.mjOBJ_BODY, f"{org.body.fly.name}/c_thorax")
    if root < 0:
        root = 1
    if org.ttm is None:
        raise SystemExit("jump:ttm|model is off in this profile")
    dofs, sign = org.ttm.dofs, org.ttm.sign

    # fly geoms touching the world body (the floor), read from MuJoCo's contact list (the body's ground-contact
    # sensors are off). s29 fixes, disclosed with the result: (1) count contacts directly; (2) count every fly
    # body, not only tarsi, because the settled m10f5 fly rests on head, abdomen tip and coxae with one tarsus
    # down (runs/s29/contacts_diag.log), so a tarsus-only detector called lift-off at 0.1 ms
    tars = {mj.mj_name2id(m, mj.mjtObj.mjOBJ_BODY, f"{org.body.fly.name}/{nm}") for nm in org.body.contact_names}
    tars.discard(-1)

    def contact_force(only_tarsi: bool = False) -> float:
        n = 0
        for i in range(d.ncon):
            b1, b2 = m.geom_bodyid[d.contact[i].geom1], m.geom_bodyid[d.contact[i].geom2]
            if (b1 != 0 and b2 != 0) or b1 == b2:
                continue
            fb = b2 if b1 == 0 else b1
            n += (fb in tars) if only_tarsi else 1
        return float(n)

    for _ in range(int(round(a.settle_ms / dt))):
        org.motor_step(org.net.step())
    n_contacts_before, n_tarsal_before = contact_force(), contact_force(only_tarsi=True)
    com0 = d.subtree_com[root].copy()
    rows, first_ttmn = [], None
    for s in range(int(round(a.ms / dt))):
        sp = org.net.step(kick=(gf, 50.0) if s == 0 else None)
        if first_ttmn is None and np.isin(ttmn, sp).any():
            first_ttmn = s * dt
        org.motor_step(sp)
        rows.append(dict(t=s * dt, com=d.subtree_com[root].copy(), z=float(d.qpos[2]),
                         ctr=(sign * d.qpos[[m.jnt_qposadr[m.dof_jntid[k]] for k in dofs]]).copy(),
                         fc=contact_force(), torque=org.ttm.torque().copy()))
    warn = int(sum(w.number for w in d.warning))
    tt = np.array([r["t"] for r in rows])
    com = np.array([r["com"] for r in rows])                  # mm (model units: mm, s, g; body.py)
    vel = np.gradient(com, tt / 1000.0, axis=0) / 1000.0      # m/s
    speed = np.linalg.norm(vel, axis=1)
    acc = np.gradient(vel, tt / 1000.0, axis=0)
    fc = np.array([r["fc"] for r in rows])
    off = np.flatnonzero(fc == 0)
    first_free = float(tt[off[0]]) if off.size else None
    # lift-off: start of the first 5 ms with no fly-floor contact (the pushing tarsus touches and leaves for a few
    # ms first; contacts_diag.log)
    run = int(round(5.0 / dt))
    free = fc == 0
    lift = next((float(tt[i]) for i in range(len(free) - run + 1) if free[i:i + run].all()), None)
    v2 = None
    if lift is not None:
        w = (tt >= lift) & (tt < lift + 2.0)
        v2 = float(speed[w].mean())
    ctr = np.array([r["ctr"] for r in rows])                  # depression-positive angle, per middle leg
    ext = []
    for k in range(ctr.shape[1]):
        om = np.gradient(ctr[:, k], tt)
        pk = int(np.argmax(om))
        if om[pk] <= 0:
            ext.append(None)
            continue
        thr = 0.05 * om[pk]
        i0 = pk
        while i0 > 0 and om[i0 - 1] > thr:
            i0 -= 1
        i1 = pk
        while i1 < len(om) - 1 and om[i1 + 1] > thr:
            i1 += 1
        ext.append(dict(start_ms=float(tt[i0]), end_ms=float(tt[i1]), duration_ms=float(tt[i1] - tt[i0]),
                        angle_change_deg=float(np.degrees(ctr[i1, k] - ctr[i0, k]))))
    res = dict(profile=a.profile, seed=a.seed, dt_ms=dt, gf_cells=len(gf), ttmn_cells=len(ttmn),
               gf_to_ttmn_ms=first_ttmn, mujoco_warnings=warn, floor_contacts_before=n_contacts_before,
               tarsal_contacts_before=n_tarsal_before, first_contact_free_ms=first_free, lift_off_ms=lift, com_speed_first_2ms=v2,
               peak_com_speed=float(speed.max()), peak_com_speed_ms=float(tt[int(np.argmax(speed))]),
               peak_vertical_acc=float(acc[:, 2].max()), peak_horizontal_acc=float(np.linalg.norm(acc[:, :2],
                                                                                                   axis=1).max()),
               com_rise_mm=float(com[:, 2].max() - com0[2]),
               thorax_z_rise_mm=float(max(r["z"] for r in rows) - rows[0]["z"]),
               peak_ttm_torque_uNmm=float(np.abs([r["torque"] for r in rows]).max()), leg_extension=ext,
               units="speeds m/s, accelerations m/s^2, lengths mm, times ms")
    Path(a.out).parent.mkdir(parents=True, exist_ok=True)
    Path(a.out).write_text(json.dumps(res, indent=1))
    print(json.dumps({k: v for k, v in res.items() if k != "leg_extension"}, indent=1))
    print("leg_extension", ext)


if __name__ == "__main__":
    main()
