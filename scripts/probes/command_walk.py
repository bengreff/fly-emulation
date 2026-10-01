"""Exploratory (not pre-registered): stimulate a descending command type in
closed loop and look for stepping. A reproduction attempt of command-neuron
activation experiments (DNg100: Bidaye et al. 2020; Pugliese et al. 2025).

Kicks every cell of --type at --hz (Poisson, Shiu kick) during 300-1300 ms.
Reports per-leg tarsal-tip fore-aft oscillation (dominant frequency 3-25 Hz and
its power share), the thorax displacement, and the leg MN rates.

    uv run python scripts/probes/command_walk.py --type DNg100 --hz 100

Session 11 options (failure localisation, DECISIONS s11): --no-body-afferents zeroes
the body mechanosensory drive (proprioception and touch; eyes and chemosenses kept);
--replay-hz F bypasses the brain for the legs: mapped leg MNs are forced to spike at
--replay-rate Hz in alternating bursts at F Hz, driving sign +1 MNs of the tripod
lf/rm/lh in antiphase with those of rf/lm/rh and sign -1 MNs the opposite (a synthetic
motor pattern, not a recording), to test whether the body can step from MN spikes.
"""
import argparse
from pathlib import Path
import re
import json
import sys

import mujoco
import numpy as np

sys.path.insert(0, "src")
from flyemu.organism import Organism  # noqa: E402
from flyemu.profiles import WORKING_PROFILE  # noqa: E402

LEGS = ["lf", "lm", "lh", "rf", "rm", "rh"]


def x_is_leg(name: str) -> bool:
    return bool(re.search(r"(^|-)(lf|lm|lh|rf|rm|rh)_", name)) and name.count("tarsus") < 2


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--type", default="DNg100")
    ap.add_argument("--hz", type=float, default=100.0)
    ap.add_argument("--set", action="append", default=["motor_unit:all|force_per_spike=10"])
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--no-body-afferents", action="store_true")
    ap.add_argument("--replay-hz", type=float, default=0.0)
    ap.add_argument("--replay-rate", type=float, default=150.0)
    ap.add_argument("--tether", action="store_true",
                    help="hold the thorax 1 mm above its start pose (root reset each step); legs swing free")
    ap.add_argument("--replay-graded", action="store_true",
                    help="size-ordered recruitment: half-sine drive per half-cycle; within each muscle MNs are "
                         "recruited in order of force per spike, thresholds 0 (weakest) to 0.8 (strongest) of the "
                         "drive peak (guessed thresholds; order from Azevedo 2020)")
    ap.add_argument("--replay-fast-only", action="store_true",
                    help="replay drives fast and intermediate units only (Hill mode twitch rise < 100 ms)")
    ap.add_argument("--tether-mm", type=float, default=1.0, help="tether lift above the start pose (mm)")
    ap.add_argument("--twitch-decay", type=float, default=0.0,
                    help="diagnostic: fast/intermediate twitch decay (ms) instead of muscles.TWITCH_MS")
    ap.add_argument("--video", default="", help="write an mp4 (communication only, not evidence)")
    ap.add_argument("--no-fv", action="store_true",
                    help="diagnostic: Hill force-velocity factor set to 1 (not a candidate)")
    ap.add_argument("--out", default="")
    a = ap.parse_args()
    if a.no_fv:
        from flyemu import muscles
        muscles.gain_velocity = lambda V, fvmax: np.ones_like(V)
    if a.twitch_decay > 0:
        from flyemu import muscles
        for c in ("fast", "intermediate"):
            muscles.TWITCH_MS[c] = (muscles.TWITCH_MS[c][0], a.twitch_decay)
    ov = {k: float(v) for k, v in (s.split("=") for s in a.set)}
    org = Organism(policy="minimal", profile=WORKING_PROFILE, min_synapses=5, overrides=ov, seed=a.seed,
                   with_camera=bool(a.video))
    if a.video:
        renderer = org.body.sim.set_renderer(f"{org.body.fly.name}/trackcam", camera_res=(480, 640),
                                             playback_speed=0.1, output_fps=30)
    dt = org.timestep_ms
    n = org.conn.neurons
    stim = np.flatnonzero(n.type.fillna("").eq(a.type).to_numpy())
    m, d = org.body.sim.mj_model, org.body.sim.mj_data
    pre = org.body.fly.name + "/"
    tips = [mujoco.mj_name2id(m, mujoco.mjtObj.mjOBJ_BODY, pre + f"{l}_tarsus5") for l in LEGS]
    th = mujoco.mj_name2id(m, mujoco.mjtObj.mjOBJ_BODY, pre + "c_thorax")
    if a.no_body_afferents:
        z = np.zeros(org.conn.n, dtype=np.float32)
        org.aff.drive = lambda obs: z
    nm = org.nm
    act_names = [m.actuator(int(i)).name.split("/")[-1] for i in nm.actuator_index]
    tri_a = np.array([nm_[:2] in ("lf", "rm", "lh") for nm_ in act_names])
    leg_mn = np.array([nm_[:2] in LEGS for nm_ in act_names])
    if a.tether:
        assert m.jnt_type[0] == mujoco.mjtJoint.mjJNT_FREE
        q0 = d.qpos[:7].copy()
        q0[2] += a.tether_mm
    if a.replay_fast_only:
        assert org.hill is not None and len(org.hill.units.tau_r) == leg_mn.size
        leg_mn = leg_mn & (org.hill.units.tau_r < 100.0)
    thr = np.zeros(leg_mn.size)
    if a.replay_graded:
        h = org.hill
        assert h is not None and len(h.w) == leg_mn.size
        key = np.where(h.mn_muscle >= 0, h.mn_muscle,
                       10000 + (h.mn_group if h.coxa is not None else np.zeros_like(h.mn_muscle)))
        for k in np.unique(key[leg_mn]):
            ix = np.flatnonzero(leg_mn & (key == k))
            if ix.size > 1:
                rk = np.argsort(np.argsort(h.w[ix], kind="stable"), kind="stable")
                thr[ix] = 0.8 * rk / (ix.size - 1)
    legj = [j for j in range(m.njnt) if m.jnt_type[j] == mujoco.mjtJoint.mjJNT_HINGE and m.jnt_limited[j]
            and re.search(r"(^|/|-)(lf|lm|lh|rf|rm|rh)_", m.joint(j).name) and m.joint(j).name.count("tarsus") < 2]
    lq = m.jnt_qposadr[legj]; lr = m.jnt_range[legj]
    Q, C, A, MA, FL, QP = [], [], [], [], [], []
    from flyemu import muscles as muscles_mod
    an = [x.split("/")[-1].removesuffix("-motor") for x in org.body.actuator_names]
    aj = [(i, mujoco.mj_name2id(m, mujoco.mjtObj.mjOBJ_JOINT, pre + x)) for i, x in enumerate(an)]
    aj = [(i, j) for i, j in aj if j >= 0 and x_is_leg(an[i])]
    a_idx = np.array([i for i, _ in aj]); a_q = m.jnt_qposadr[[j for _, j in aj]]
    rng = np.random.default_rng(1)
    X, P, J, T = [], [], [], []
    mn = (n.superclass.fillna("") == "vnc_motor").to_numpy()
    cnt = np.zeros(org.conn.n)
    for s in range(int(1400 / dt)):
        t = s * dt
        obs = org.body.observe()
        kick = None
        if a.hz > 0 and 300 <= t < 1300:
            kick = (stim[rng.random(stim.size) < a.hz * dt / 1000], org.kick_mv)
        sp = org.net.step(external_mv=org.sense(s, obs), kick=kick)
        if a.replay_hz > 0 and 300 <= t < 1300:
            phase = int((t - 300) * a.replay_hz * 2 / 1000) % 2      # half-cycle index
            on = leg_mn & ((nm.drive_sign > 0) == (tri_a ^ bool(phase)))
            if a.replay_graded:
                drive = abs(np.sin(np.pi * ((t - 300) * a.replay_hz * 2 / 1000 % 1.0)))
                on = on & (thr < drive)
            fire = on & (rng.random(on.size) < a.replay_rate * dt / 1000)
            sp = np.union1d(sp, nm.mn_index[fire])
        if 300 <= t < 1300:
            cnt[sp] += 1
        tq = org.motor_step(sp)
        if a.tether:
            d.qpos[:7] = q0
            d.qvel[:6] = 0.0
        if a.video:
            org.body.sim.render_as_needed()
        if s % 10 == 0:                      # 1 kHz sampling
            R = d.xmat[th].reshape(3, 3)
            rel = (d.xpos[tips] - d.xpos[th]) @ R   # body frame
            X.append(rel[:, 0]); P.append(d.xpos[th].copy())
            J.append(np.asarray(obs["joint_angles"]).ravel().copy())
            T.append(np.asarray(tq, dtype=float).ravel().copy())
            Q.append(d.qpos[lq].copy())
            C.append(d.ncon)
            A.append(d.qpos[a_q].copy())
            if org.hill is not None:
                MA.append(org.hill.activation().copy())
                QP.append(d.qpos[org.hill.q_adr].copy())
                FL.append(muscles_mod.gain_length(org.hill.p.lengths(d.qpos[org.hill.q_adr]), org.hill.p.lmin, org.hill.p.lmax))
    X = np.array(X)[300:1300]; P = np.array(P)
    out = {}
    for i, l in enumerate(LEGS):
        x = X[:, i] - X[:, i].mean()
        f = np.fft.rfftfreq(len(x), 1e-3); pw = np.abs(np.fft.rfft(x)) ** 2
        band = (f >= 3) & (f <= 25)
        k = np.argmax(pw * band)
        out[l] = {"f_hz": round(float(f[k]), 1), "band_share": round(float(pw[band].sum() / pw[1:].sum()), 2),
                  "amp_mm": round(float(x.std() * 2), 3)}
    if a.replay_hz > 0:                     # joint-angle power at the drive frequency
        Jm = np.array(J)[300:1300]
        Jm = Jm - Jm.mean(0)
        pj = np.abs(np.fft.rfft(Jm, axis=0)) ** 2
        fj = np.fft.rfftfreq(len(Jm), 1e-3)
        at = (np.abs(fj - a.replay_hz) <= 1.0)
        tot = pj[1:].sum(0)
        moving = tot > 1e-12 * tot.max() if tot.max() > 0 else tot > 0
        share_f = pj[at].sum(0)[moving] / tot[moving]
        hb = (fj >= 3.0) & (fj <= 50.0)       # excludes the slow postural shift at replay onset
        share_hb = pj[at].sum(0)[moving] / np.maximum(pj[hb].sum(0)[moving], 1e-30)
        Tm = np.array(T)[300:1300]
        Tm = Tm - Tm.mean(0)
        pt = np.abs(np.fft.rfft(Tm, axis=0)) ** 2
        tt = pt[1:].sum(0)
        mv = tt > 1e-9 * tt.max()
        st = pt[at].sum(0)[mv] / tt[mv]
        out["torque_at_drive_f"] = {"n": int(mv.sum()), "median_share": round(float(np.median(st)), 3),
                                    "frac_gt_0.3": round(float((st > 0.3).mean()), 3),
                                    "median_p2p": round(float(np.median(2 * Tm.std(0)[mv])), 5)}
        out["joints_at_drive_f"] = {"n": int(moving.sum()), "median_share": round(float(np.median(share_f)), 3),
                                    "frac_gt_0.3": round(float((share_f > 0.3).mean()), 3),
                                    "median_amp_rad": round(float(np.median(2 * Jm.std(0)[moving])), 4),
                                    "median_share_of_3_50hz": round(float(np.median(share_hb)), 3),
                                    "median_amp_3_50hz_rad": round(float(np.median(4 * np.sqrt(pj[hb].sum(0)[moving]) / len(Jm))), 4),
                                    "median_p2p_at_f_rad": round(float(np.median(4 * np.sqrt(pj[at].sum(0)[moving]) / len(Jm))), 4),
                                    "p90_p2p_at_f_rad": round(float(np.percentile(4 * np.sqrt(pj[at].sum(0)[moving]) / len(Jm), 90)), 4)}
    Qm = np.array(Q)[300:1300]
    near = (np.minimum(Qm - lr[:, 0], lr[:, 1] - Qm) < 0.05 * (lr[:, 1] - lr[:, 0]))
    occ = near.mean(0)
    if a.replay_hz > 0:                     # per leg actuator: 10 Hz torque and swing, same joint
        Am = np.array(A)[300:1300]; Am = Am - Am.mean(0)
        Ta = np.array(T)[300:1300][:, a_idx]; Ta = Ta - Ta.mean(0)
        fq = np.fft.rfftfreq(len(Am), 1e-3); at2 = np.abs(fq - a.replay_hz) <= 1.0
        tf = 4 * np.sqrt((np.abs(np.fft.rfft(Ta, axis=0)) ** 2)[at2].sum(0)) / len(Ta)
        qf = 4 * np.sqrt((np.abs(np.fft.rfft(Am, axis=0)) ** 2)[at2].sum(0)) / len(Am)
        ok = tf > 1e-6
        out["per_actuator_at_f"] = {"n": int(ok.sum()), "median_torque_p2p": round(float(np.median(tf[ok])), 3),
                                    "median_joint_p2p_rad": round(float(np.median(qf[ok])), 4),
                                    "median_impedance": round(float(np.median(tf[ok] / np.maximum(qf[ok], 1e-9))), 2)}
    if a.replay_hz > 0 and MA:              # per muscle: activation mean and 10 Hz swing; antagonist phase
        Ma = np.array(MA)[300:1300]
        Fm = np.fft.rfft(Ma - Ma.mean(0), axis=0)
        fq = np.fft.rfftfreq(len(Ma), 1e-3); k = int(np.argmin(np.abs(fq - a.replay_hz)))
        p2p = 4 * np.abs(Fm[k]) / len(Ma)
        MP = org.hill.p
        pairs = {}
        for i, (jn, dr) in enumerate(zip(MP.joint, MP.direction)):
            pairs.setdefault(jn, {})[float(dr)] = i
        W = org.hill.W
        both = [v for v in pairs.values() if len(v) == 2 and W[v[1.0]] > 0 and W[v[-1.0]] > 0]
        dphi = [np.angle(Fm[k, v[1.0]] * np.conj(Fm[k, v[-1.0]])) for v in both]
        # expected 10 Hz net torque per pair (activation swing x F0 x r, opposite signs)
        tq_pair = [abs(MP.F0[v[1.0]] * MP.r[v[1.0]] * 2 * Fm[k, v[1.0]] - MP.F0[v[-1.0]] * MP.r[v[-1.0]] * 2 * Fm[k, v[-1.0]]) * 2 / len(Ma)
                   for v in both]
        Tall = np.array(T)[300:1300]; Tall = Tall - Tall.mean(0)
        acts = [int(org.hill.m_act[v[1.0]]) for v in both]
        qad = [int(org.hill.q_adr[v[1.0]]) for v in both]
        Qall = np.array(QP)[300:1300]; Qall = Qall - Qall.mean(0)
        tf_p = 4 * np.abs(np.fft.rfft(Tall[:, acts], axis=0)[k]) / len(Tall)
        qf_p = 4 * np.abs(np.fft.rfft(Qall[:, [list(org.hill.q_adr).index(q) for q in qad]], axis=0)[k]) / len(Qall)
        out["complete_pair_joints"] = {"joints": [str(MP.joint[v[1.0]]) for v in both],
                                       "torque_p2p": [round(float(x), 3) for x in tf_p],
                                       "swing_p2p_rad": [round(float(x), 3) for x in qf_p],
                                       "act_p2p_pos_neg": [[round(float(p2p[v[1.0]]), 3), round(float(p2p[v[-1.0]]), 3)] for v in both],
                                       "fl_mean_pos_neg": [[round(float(np.array(FL)[300:1300][:, v[1.0]].mean()), 3), round(float(np.array(FL)[300:1300][:, v[-1.0]].mean()), 3)] for v in both],
                                       "q_minus_qref_rad": [round(float(np.array(QP)[300:1300][:, v[1.0]].mean() - MP.q_ref[v[1.0]]), 3) for v in both],
                                       "act_mean_pos_neg": [[round(float(Ma[:, v[1.0]].mean()), 3), round(float(Ma[:, v[-1.0]].mean()), 3)] for v in both]}
        out["muscles_at_f"] = {"n": int(Ma.shape[1]), "median_mean_act": round(float(np.median(Ma.mean(0))), 3),
                               "median_act_p2p": round(float(np.median(p2p)), 3),
                               "n_pairs_with_units": len(dphi), "n_muscles_no_units": int((W == 0).sum()),
                               "median_expected_pair_torque_p2p": round(float(np.median(tq_pair)), 3) if tq_pair else None,
                               "median_FL_gain": round(float(np.median(np.array(FL)[300:1300].mean(0))), 3),
                               "frac_muscles_FL_below_0.2": round(float((np.array(FL)[300:1300].mean(0) < 0.2).mean()), 3),
                               "frac_pairs_antiphase": round(float(np.mean(np.abs(np.asarray(dphi)) > np.pi / 2)), 3),
                               "median_pair_dphi_deg": round(float(np.degrees(np.median(np.abs(dphi)))), 1)}
    out["contacts_mean"] = round(float(np.mean(C[300:1300])), 1)
    out["joint_limits"] = {"n": len(legj), "mean_frac_near": round(float(occ.mean()), 3),
                           "n_joints_gt_half": int((occ > 0.5).sum()),
                           "armature_median": float(np.median(m.dof_armature[m.jnt_dofadr[legj]])),
                           "damping_median": float(np.median(m.dof_damping[m.jnt_dofadr[legj]]))}
    hz = cnt / 1.0
    res = {"type": a.type, "seed": a.seed, "no_body_afferents": a.no_body_afferents,
           "replay_hz": a.replay_hz, "tether": a.tether, "fast_only": a.replay_fast_only, "graded": a.replay_graded, "no_fv": a.no_fv, "twitch_decay": a.twitch_decay, "tether_mm": a.tether_mm if a.tether else None, "n_leg_mn_mapped": int(leg_mn.sum()), "n_stim": int(stim.size), "hz": a.hz,
                      "stim_rate_obs": round(float(hz[stim].mean()), 1),
                      "thorax_dx_mm": round(float(P[1300, 0] - P[300, 0]), 3),
                      "thorax_dy_mm": round(float(P[1300, 1] - P[300, 1]), 3),
           "leg_mn_hz": round(float(hz[mn].mean()), 2), "legs": out}
    res["warnings"] = int(sum(w.number for w in d.warning))
    print(json.dumps(res))
    if a.video:
        renderer.save_video(Path(a.video))
    if a.out:
        with open(a.out, "w") as fh:
            json.dump(res, fh)


if __name__ == "__main__":
    main()
