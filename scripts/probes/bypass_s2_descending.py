"""Motor-pathway bypass assay, stage S2: sustained drive into identified walking DNs, brain off (s13, 13 Oct).

DIAGNOSTIC, forced drive: the DN input is set by hand. A rhythm here would not be emergent walking.

The organism is built as usual. Then:
  - brain off: every neuron outside the VNC set (superclass vnc_*, ascending, descending, sensory_ascending,
    efferent_ascending) loses all output (lif.Network.silence, as Shiu 2024 silences cells);
  - senses off by default: no afferent drive at all. --proprio closes the S4 loop (s17, DECISIONS 21 Oct 03:18): the
    leg proprioceptor drive is computed from the body every step, as proprio_reach.py (bristle rows zeroed), and reaches
    the afferents --proprio-delay-ms later;
  - the thorax is tethered --tether-mm above the standing placement, so the legs move in air;
  - every cell of --type gets a constant external drive of --drive-mv during [--on-ms, --off-ms).
Recorded together, 1 ms bins: the driven DNs, all DNs, premotor cells (VNC intrinsic cells with a direct edge
onto a leg MN), every leg MN pool (one pool per Hill pair muscle or coxa muscle group), muscle activation, and
leg joint angles. Rhythm per MN uses assay_pathways.rhythm_excess (F-RHYTHM-1's score; criterion > 0.10).
Alternation: Pearson r between antagonist pool rates of one joint (20 ms smoothing) and between the same pool on
the left and right leg of a segment, over the drive window after its first 100 ms.

    uv run python scripts/probes/bypass_s2_descending.py --type DNg100 --drive-mv 12
"""
from __future__ import annotations

import argparse
import json
import re
import sys
import time
from collections import deque
from pathlib import Path

import mujoco as mj
import numpy as np

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "src")); sys.path.insert(0, str(REPO / "scripts"))
sys.path.insert(0, str(Path(__file__).resolve().parent))
from flyemu.deadfly import place_standing  # noqa: E402
from flyemu.organism import Organism  # noqa: E402
from assay_pathways import rhythm_excess  # noqa: E402
from standing_rest import shot  # noqa: E402

LEGS = ("lf", "lm", "lh", "rf", "rm", "rh")
VNC_SUPER = ("ascending_neuron", "descending_neuron", "descending_neuron_tbc", "sensory_ascending",
             "sensory_ascending_tbc", "efferent_ascending")
CORE = {"IN17A001": "E1", "INXXX466": "E2", "IN16B036": "I1", "IN19A007": "A007"}    # bypass_s3_chain.ROLE
COXA_ANTAGONIST = (("promotor", "remotor"), ("remotor", "promotor"),
                   ("anterior rotator", "posterior rotator"), ("posterior rotator", "anterior rotator"))


def smooth(x: np.ndarray, k: int) -> np.ndarray:
    return np.convolve(x, np.ones(k) / k, mode="same")


def corr(a: np.ndarray, b: np.ndarray) -> float | None:
    if a.std() == 0 or b.std() == 0:
        return None
    return round(float(np.corrcoef(a, b)[0, 1]), 3)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--profile", default="m10f0")
    ap.add_argument("--seed", type=int, default=12)
    ap.add_argument("--type", default="DNg100", help="DN type(s), comma-separated")
    ap.add_argument("--drive-mv", type=float, default=12.0)
    ap.add_argument("--ms", type=float, default=1500.0)
    ap.add_argument("--on-ms", type=float, default=300.0)
    ap.add_argument("--off-ms", type=float, default=1300.0)
    ap.add_argument("--brain-on", action="store_true", help="keep the brain (default: brain off)")
    ap.add_argument("--tether-mm", type=float, default=1.0)
    ap.add_argument("--set", action="append", default=[], metavar="KEY=V")
    ap.add_argument("--frames-ms", default="0,300,500,700,900,1100,1300")
    ap.add_argument("--proprio", action="store_true", help="S4 closed loop: leg proprioceptor drive from the body")
    ap.add_argument("--proprio-gain-mv", type=float, default=None, help="afferent:all|rate_gain (default: profile's)")
    ap.add_argument("--proprio-delay-ms", type=float, default=3.0)
    ap.add_argument("--tag", default="")
    ap.add_argument("--out", default=str(REPO / "runs" / "s13" / "bypass" / "s2"))
    a = ap.parse_args()
    out = Path(a.out); out.mkdir(parents=True, exist_ok=True)
    tag = a.tag or f"{a.type.replace(',', '+')}_{a.drive_mv:g}mv{'_brain' if a.brain_on else ''}"
    t0 = time.time()
    ov = {k: float(v) for k, v in (x.split("=") for x in a.set)}
    if a.proprio and a.proprio_gain_mv is not None:
        ov["afferent:all|rate_gain"] = a.proprio_gain_mv
    org = Organism(policy="minimal", profile=a.profile, min_synapses=5, overrides=ov, seed=a.seed, with_camera=True)
    dt = org.timestep_ms
    n = org.conn.neurons
    sc = n.superclass.fillna("").to_numpy().astype(str)
    typ = n.type.fillna("").to_numpy().astype(str)
    vnc = np.char.startswith(sc, "vnc_") | np.isin(sc, VNC_SUPER)
    if not a.brain_on:
        org.net.silence(np.flatnonzero(~vnc))
    if a.proprio:
        from proprio_reach import proprio_drive
        af = org.aff
        assert vnc[af.rows].all(), "a leg afferent is outside the VNC set"
        pdrive = proprio_drive(org)
        lab = np.where(af.channel == "load", "CS", af.subtype if af.subtype is not None else af.channel)
        lab = np.where(af.channel == "contact", "", lab)
        aff_grp = {g: af.rows[lab == g] for g in np.unique(lab) if g}
        prop = np.setdiff1d(af.rows, af.rows[af.channel == "contact"])
        src_ = np.repeat(np.arange(org.conn.n), np.diff(org.conn.indptr))
        hit = np.isin(src_, prop)
        w_in = np.bincount(org.conn.indices[hit], weights=org.conn.weight_syn[hit], minlength=org.conn.n)
        first = np.setdiff1d(np.flatnonzero(w_in >= 20), af.rows)
    stim = np.flatnonzero(np.isin(typ, a.type.split(",")))
    if stim.size == 0:
        raise SystemExit(f"no cells of type {a.type}")
    dn = np.flatnonzero(np.char.startswith(sc, "descending_neuron"))
    h = org.hill
    nm = org.nm
    pool_of_mn = np.full(len(nm.mn_index), -1)
    pools = []                                    # (name, leg, joint-or-muscle, direction-or-None)
    for i, (j, s) in enumerate(zip(h.p.joint, h.p.direction)):
        leg = re.search(r"([lr][fmh])_", j).group(1)
        pools.append((f"{j} {s:+g}", leg, j, float(s)))
        pool_of_mn[h.mn_muscle == i] = len(pools) - 1
    if h.coxa is not None:
        inv = {}
        for k in range(len(h.coxa.F0)):
            g = h.coxa_group[k]
            if g >= 0 and g not in inv:
                inv[g] = (h.coxa.leg[k], h.coxa.mn_type[k])
        for g, (leg, t) in sorted(inv.items()):
            pools.append((f"{leg} coxa {t}", leg, f"coxa {t}", None))
            pool_of_mn[h.mn_group == g] = len(pools) - 1
    leg_mn = pool_of_mn >= 0
    mn_rows = np.asarray(nm.mn_index)
    is_legmn = np.zeros(org.conn.n, bool); is_legmn[mn_rows[leg_mn]] = True
    src = np.repeat(np.arange(org.conn.n), np.diff(org.conn.indptr))
    pm = np.zeros(org.conn.n, bool)
    pm[np.unique(src[is_legmn[org.conn.indices]])] = True
    premotor = np.flatnonzero(pm & (sc == "vnc_intrinsic"))
    # body: placed standing, then tethered in air
    b = org.body
    m, d = b.sim.mj_model, b.sim.mj_data
    b.reset(); place_standing(b)
    q0 = d.qpos[:7].copy(); q0[2] += a.tether_mm
    d.qpos[:7] = q0; mj.mj_forward(m, d)
    thorax = mj.mj_name2id(m, mj.mjtObj.mjOBJ_BODY, f"{b.fly.name}/c_thorax")
    steps = int(round(a.ms / dt)); per = int(round(1.0 / dt))
    nb = steps // per
    R = np.zeros((nb, len(mn_rows)), np.uint8)    # leg MN raster, 1 ms bins
    stim_c = np.zeros(nb); dn_c = np.zeros(nb); pm_c = np.zeros(nb)
    act = np.zeros((nb, len(h.p.F0)), np.float32)
    qj = np.zeros((nb, len(h.q_adr)), np.float32)
    frames_at = {int(round(float(x) / dt)) for x in a.frames_ms.split(",")}
    imgs = []
    zero = np.zeros(org.conn.n, np.float32)
    on = zero.copy(); on[stim] = a.drive_mv
    is_stim = np.zeros(org.conn.n, bool); is_stim[stim] = True
    is_dn = np.zeros(org.conn.n, bool); is_dn[dn] = True
    is_pm = np.zeros(org.conn.n, bool); is_pm[premotor] = True
    row_of = np.full(org.conn.n, -1); row_of[mn_rows] = np.arange(len(mn_rows))
    core = np.flatnonzero(np.isin(typ, list(CORE)))
    core_c = np.zeros((2, core.size)); is_core = np.full(org.conn.n, -1); is_core[core] = np.arange(core.size)
    if a.proprio:
        nd = int(round(a.proprio_delay_ms / dt))
        fifo = deque([zero] * nd)                 # drive vectors in flight, body to afferent
        grp_c = {g: np.zeros(2) for g in aff_grp}
        is_first = np.zeros(org.conn.n, bool); is_first[first] = True
        first_c = np.zeros((2, first.size)); first_pos = np.full(org.conn.n, -1); first_pos[first] = np.arange(first.size)
    win = lambda t: 0 if 100 <= t < a.on_ms else (1 if a.on_ms + 100 <= t < a.off_ms else -1)  # noqa: E731
    for s in range(steps):
        t = s * dt
        if s in frames_at:
            imgs.append(shot(m, d, thorax))
        x = on if a.on_ms <= t < a.off_ms else zero
        if a.proprio:
            fifo.append(pdrive(b.observe()))
            x = x + fifo.popleft()
        sp = org.net.step(external_mv=x)
        org.motor_step(sp)
        d.qpos[:7] = q0; d.qvel[:6] = 0.0
        k = s // per
        if sp.size:
            stim_c[k] += is_stim[sp].sum(); dn_c[k] += is_dn[sp].sum(); pm_c[k] += is_pm[sp].sum()
            r = row_of[sp]; r = r[r >= 0]
            R[k, r] += 1
            wi = win(t)
            if wi >= 0:
                c_ = is_core[sp]; np.add.at(core_c[wi], c_[c_ >= 0], 1)
                if a.proprio:
                    for g, rows in aff_grp.items():
                        grp_c[g][wi] += np.isin(sp, rows).sum()
                    f_ = first_pos[sp]; np.add.at(first_c[wi], f_[f_ >= 0], 1)
        if s % per == per - 1:
            act[k] = h.activation(); qj[k] = d.qpos[h.q_adr]
    # ---- analysis over the drive window minus its first 100 ms, and the baseline before it
    w0, w1 = int(a.on_ms) + 100, int(a.off_ms)
    base = slice(100, int(a.on_ms))
    drv = slice(w0, w1)
    hz = lambda c, nn, sl: round(float(c[sl].sum() / max(nn, 1) / ((sl.stop - sl.start) / 1000)), 2)  # noqa: E731
    pool_rate = np.zeros((nb, len(pools)))
    for p_ in range(len(pools)):
        pool_rate[:, p_] = R[:, pool_of_mn == p_].sum(1)
    pool_n = np.bincount(pool_of_mn[leg_mn], minlength=len(pools))
    rx = []
    for c in np.flatnonzero(leg_mn):
        tr = R[drv, c] > 0
        if tr.sum() >= 5:
            e, sd, f = rhythm_excess(tr, 1.0)
            rx.append((c, e, f))
    pool_best = {}
    for c, e, f in rx:
        p_ = pool_of_mn[c]
        if p_ not in pool_best or e > pool_best[p_][0]:
            pool_best[p_] = (e, f)
    sm = np.array([smooth(pool_rate[:, p_], 20) for p_ in range(len(pools))]).T
    pools_out = []
    for p_, (name, leg, jt, s) in enumerate(pools):
        e, f = pool_best.get(p_, (None, None))
        anti = None
        if s is not None:
            q = [k for k, (_, l2, j2, s2) in enumerate(pools) if l2 == leg and j2 == jt and s2 == -s]
        else:                                     # coxa: promotor vs remotor (Pugliese's readout), rotator pair
            want = next((y for x, y in COXA_ANTAGONIST if x in jt), None)
            q = [k for k, (_, l2, j2, _s) in enumerate(pools) if l2 == leg and want and want in j2]
        if q:
            anti = corr(sm[drv, p_], sm[drv, q[0]])
        mate = None
        other = ("r" if leg[0] == "l" else "l") + leg[1]
        q = [k for k, (n2, l2, j2, s2) in enumerate(pools) if l2 == other and j2.replace(other, leg) == jt and s2 == s]
        if q:
            mate = corr(sm[drv, p_], sm[drv, q[0]])
        pools_out.append(dict(pool=name, leg=leg, n_mn=int(pool_n[p_]),
                              base_hz=hz(pool_rate[:, p_], pool_n[p_], base), drive_hz=hz(pool_rate[:, p_], pool_n[p_], drv),
                              best_mn_rhythm_excess=None if e is None else round(float(e), 3),
                              best_mn_rhythm_hz=None if f is None or not np.isfinite(f) else round(float(f), 1),
                              r_antagonist=anti, r_left_right=mate))
    rhythmic = [p for p in pools_out if (p["best_mn_rhythm_excess"] or 0) > 0.10
                and p["best_mn_rhythm_hz"] is not None and 4 <= p["best_mn_rhythm_hz"] <= 25]
    alternating = [p for p in rhythmic if (p["r_antagonist"] is not None and p["r_antagonist"] <= -0.3)
                   or (p["r_left_right"] is not None and p["r_left_right"] <= -0.3)]
    qd = qj[drv] - qj[drv].mean(0)
    tw = np.array([(a.on_ms - 100) / 1000, (a.off_ms - a.on_ms - 100) / 1000])     # window lengths, s
    segs = (n["somaNeuromere"].fillna("") if "somaNeuromere" in n else n.get("soma_neuromere", "")).astype(str)
    side = n["somaSide"].fillna("").astype(str)
    core_out = [dict(role=CORE[typ[i]], neuromere=f"{segs.iloc[i]}{side.iloc[i]}", base_hz=round(float(core_c[0, k] / tw[0]), 2),
                     drive_hz=round(float(core_c[1, k] / tw[1]), 2)) for k, i in enumerate(core)]
    loop = None
    if a.proprio:
        fr = first_c / tw[:, None]
        loop = dict(gain_mv=float(np.unique(org.aff.gain_mv)[0]), delay_ms=a.proprio_delay_ms, delay_steps=nd,
                    afferent_hz_per_cell={g: dict(n=int(r.size), base=round(float(grp_c[g][0] / max(r.size, 1) / tw[0]), 2),
                                                  drive=round(float(grp_c[g][1] / max(r.size, 1) / tw[1]), 2))
                                          for g, r in aff_grp.items()},
                    first_order=dict(n=int(first.size), n_active_drive=int((fr[1] > 0).sum()),
                                     n_active_base=int((fr[0] > 0).sum()),
                                     mean_hz=[round(float(fr[0].mean()), 3), round(float(fr[1].mean()), 3)] if first.size else None))
    res = dict(diagnostic="forced drive (DN input set by hand); not emergent walking",
               profile=a.profile, seed=a.seed, type=a.type, drive_mv=a.drive_mv, brain_off=not a.brain_on,
               senses="leg proprio" if a.proprio else "off", proprio=loop, core=core_out, tether_mm=a.tether_mm, overrides=ov, n_stim=int(stim.size), n_premotor=int(premotor.size),
               n_leg_mn=int(leg_mn.sum()), n_pools=len(pools),
               rates_hz=dict(stim_base=hz(stim_c, stim.size, base), stim_drive=hz(stim_c, stim.size, drv),
                             dn_base=hz(dn_c, dn.size, base), dn_drive=hz(dn_c, dn.size, drv),
                             premotor_base=hz(pm_c, premotor.size, base), premotor_drive=hz(pm_c, premotor.size, drv),
                             leg_mn_base=hz(R.sum(1), leg_mn.sum(), base), leg_mn_drive=hz(R.sum(1), leg_mn.sum(), drv)),
               mns_active_drive=int((R[drv][:, leg_mn].sum(0) > 0).sum()),
               mns_scored=len(rx), mns_rhythmic=int(sum(e > 0.10 for _, e, _ in rx)),
               activation_drive_mean=round(float(act[drv].mean()), 4), activation_drive_max=round(float(act[drv].max()), 4),
               joint_angle_sd_deg_max=round(float(np.degrees(qd.std(0)).max()), 2),
               rhythmic_pools=[p["pool"] for p in rhythmic], alternating_pools=[p["pool"] for p in alternating],
               passes=bool(alternating), pools=pools_out, wall_s=round(time.time() - t0))
    (out / f"s2_{tag}.json").write_text(json.dumps(res, indent=1))
    np.savez_compressed(out / f"s2_{tag}_traces.npz", pool_rate=pool_rate.astype(np.float32), act=act, qj=qj,
                        stim=stim_c, dn=dn_c, premotor=pm_c, pool_names=np.array([p[0] for p in pools]))
    if imgs:
        np.save(out / f"frames_{tag}.npy", np.stack(imgs))
    print(json.dumps({k: v for k, v in res.items() if k != "pools"}, indent=1))


if __name__ == "__main__":
    main()
