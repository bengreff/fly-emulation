"""Does leg proprioception reach the leg motor neurons with the brain off? (s13 fly2, 13 Oct; F-REFLEX-1 rerun)

DIAGNOSTIC. The reach gate before fly2's proprioceptive stance loop: F-REFLEX-1 (m7, brain on) found the femoral
chordotonal afferents firing and their relay interneurons modulated, but the tibia motor pools unchanged. This reruns
that test in the loop's own configuration:
  - profile m10f0, brain off (every cell outside the VNC set loses its output, as in bypass_s2_descending.py);
  - senses: leg proprioceptors only (chordotonal organ, hair plate, campaniform sensilla rows of sensory.Afferents);
    the bristle ("contact") rows, eyes, chemosenses and organs are not driven;
  - thorax tethered --tether-mm above the standing placement, legs in air.
Two stimuli:
  clamp: the --leg femur-tibia joint is position-clamped (qpos/qvel overwritten each step), held from 200 ms and
         moved q_start + amp sin(2 pi f t) from 300 ms (resistance_reflex.py's protocol);
  load:  the --leg campaniform sensilla get their full signal (1) during [--on-ms, --off-ms); the leg is free.
--zero-afferents is the control: no afferent drive at all.
Recorded: per-MN rate of every motor pool of --leg (one pool per Hill pair muscle and per coxa MN type) in the bins
hold / flexing / extending (clamp) or before / during (load); the afferent rates by subtype; the rates of the tonic
inhibitors F-REFLEX-1 named.

    uv run python scripts/probes/proprio_reach.py --stim clamp --leg lm [--gain-mv 8] [--zero-afferents]
"""
from __future__ import annotations

import argparse
import json
import re
import sys
import time
from pathlib import Path

import mujoco as mj
import numpy as np

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "src"))
from flyemu.deadfly import place_standing  # noqa: E402
from flyemu.organism import Organism  # noqa: E402

VNC_SUPER = ("ascending_neuron", "descending_neuron", "descending_neuron_tbc", "sensory_ascending",
             "sensory_ascending_tbc", "efferent_ascending")
INHIBITORS = ("IN13A006", "IN13A014", "IN08A005", "IN19A005", "IN21A002", "DNg105")   # F-REFLEX-1


def brain_off(org) -> np.ndarray:
    """Silence every cell outside the VNC set (bypass_s2_descending.py); returns the VNC mask."""
    sc = org.conn.neurons.superclass.fillna("").to_numpy().astype(str)
    vnc = np.char.startswith(sc, "vnc_") | np.isin(sc, VNC_SUPER)
    assert vnc[org.aff.rows].all(), "a leg afferent is outside the VNC set"
    org.net.silence(np.flatnonzero(~vnc))
    return vnc


def proprio_drive(org):
    """Leg proprioceptor drive only: sensory.Afferents.drive with the bristle rows zeroed."""
    af = org.aff
    bristle = af.rows[af.channel == "contact"]

    def f(obs):
        v = af.drive(obs)
        v[bristle] = 0.0
        return v
    return f


def leg_pools(org, leg: str) -> list[tuple[str, np.ndarray]]:
    """(name, network rows) per motor pool of one leg: Hill pair muscles by joint and direction, coxa by MN type."""
    h, mn = org.hill, np.asarray(org.nm.mn_index)
    out = []
    for i, (j, s) in enumerate(zip(h.p.joint, h.p.direction)):
        if re.search(r"([lr][fmh])_", j).group(1) == leg:
            out.append((f"{j.replace(leg + '_', '')} {s:+g}", mn[h.mn_muscle == i]))
    if h.coxa is not None:
        seen = set()
        for k in range(len(h.coxa.F0)):
            g = h.coxa_group[k]
            if g >= 0 and g not in seen and h.coxa.leg[k] == leg:
                seen.add(g)
                out.append((f"coxa {h.coxa.mn_type[k]}", mn[h.mn_group == g]))
    return [(nme, r) for nme, r in out if r.size]


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--profile", default="m10f0")
    ap.add_argument("--seed", type=int, default=12)
    ap.add_argument("--stim", choices=("clamp", "load"), default="clamp")
    ap.add_argument("--leg", default="lm")
    ap.add_argument("--gain-mv", type=float, default=None, help="afferent:all|rate_gain (default: profile's)")
    ap.add_argument("--zero-afferents", action="store_true")
    ap.add_argument("--f", type=float, default=2.0)
    ap.add_argument("--amp", type=float, default=0.4)
    ap.add_argument("--on-ms", type=float, default=300.0)
    ap.add_argument("--off-ms", type=float, default=1300.0)
    ap.add_argument("--ms", type=float, default=1300.0)
    ap.add_argument("--tether-mm", type=float, default=1.0)
    ap.add_argument("--set", action="append", default=[], metavar="KEY=V")
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    t0 = time.time()
    ov = {k: float(v) for k, v in (x.split("=") for x in a.set)}
    if a.gain_mv is not None:
        ov["afferent:all|rate_gain"] = a.gain_mv
    org = Organism(policy="minimal", profile=a.profile, min_synapses=5, overrides=ov, seed=a.seed)
    assert org.hill is not None
    dt = org.timestep_ms
    brain_off(org)
    af = org.aff
    drive = proprio_drive(org)
    if a.zero_afferents:
        z = np.zeros(org.conn.n, np.float32)
        drive = lambda obs: z  # noqa: E731
    st = af.subtype if af.subtype is not None else np.full(len(af.rows), "")
    lab = np.where(af.channel == "load", "CS", st)
    on_leg = af.leg == a.leg
    groups = {g: af.rows[on_leg & (lab == g)] for g in np.unique(lab[on_leg]) if g}
    cs_rows = groups.get("CS", np.array([], int))
    cs_i = np.flatnonzero(on_leg & (af.channel == "load"))
    pools = leg_pools(org, a.leg)
    typ = org.conn.neurons.type.fillna("").to_numpy().astype(str)
    inh = {t: np.flatnonzero(typ == t) for t in INHIBITORS}
    b = org.body
    m, d = b.sim.mj_model, b.sim.mj_data
    b.reset(); place_standing(b)
    q0 = d.qpos[:7].copy(); q0[2] += a.tether_mm
    d.qpos[:7] = q0; mj.mj_forward(m, d)
    jn = f"{b.fly.name}/{a.leg}_trochanterfemur-{a.leg}_tibia-pitch"
    j = mj.mj_name2id(m, mj.mjtObj.mjOBJ_JOINT, jn)
    qa, dv = m.jnt_qposadr[j], m.jnt_dofadr[j]
    lo, hi = m.jnt_range[j]
    bins = ("hold", "flexing", "extending") if a.stim == "clamp" else ("before", "during")
    T = dict.fromkeys(bins, 0.0)
    cnt = {nme: dict.fromkeys(bins, 0) for nme, _ in pools}
    acnt = {g: dict.fromkeys(bins, 0) for g in groups}
    icnt = {t: dict.fromkeys(bins, 0) for t in inh}
    q_start = None
    for s in range(int(round(a.ms / dt))):
        t = s * dt
        obs = b.observe()
        x = drive(obs)
        if a.stim == "load" and not a.zero_afferents and a.on_ms <= t < a.off_ms and cs_rows.size:
            x = x.copy(); x[cs_rows] = af.baseline_mv[cs_i] + af.gain_mv[cs_i] * 1.0
        sp = org.net.step(external_mv=x)
        org.motor_step(sp)
        d.qpos[:7] = q0; d.qvel[:6] = 0.0
        b_ = None
        if a.stim == "clamp":
            if t >= 200 and q_start is None:
                q_start = float(np.clip(d.qpos[qa], lo + a.amp + 0.05, hi - a.amp - 0.05))
            if q_start is not None:
                ph = 2 * np.pi * a.f * max(t - 300, 0.0) / 1000
                d.qpos[qa] = q_start + (a.amp * np.sin(ph) if t >= 300 else 0.0)
                v = a.amp * 2 * np.pi * a.f * np.cos(ph) if t >= 300 else 0.0
                d.qvel[dv] = v
                if t >= 210:
                    b_ = "hold" if t < 300 else ("flexing" if v < 0 else "extending")
        elif t >= 100:
            b_ = "during" if a.on_ms <= t < a.off_ms else ("before" if t < a.on_ms else None)
        if b_ is None:
            continue
        T[b_] += dt
        if sp.size:
            for nme, r in pools:
                cnt[nme][b_] += int(np.isin(sp, r).sum())
            for g, r in groups.items():
                acnt[g][b_] += int(np.isin(sp, r).sum())
            for tt, r in inh.items():
                icnt[tt][b_] += int(np.isin(sp, r).sum())
    hz = lambda c, n, k: round(1000 * c / max(T[k], 1e-9) / max(n, 1), 2)  # noqa: E731
    out = {"probe": "proprio_reach", "profile": a.profile, "seed": a.seed, "stim": a.stim, "leg": a.leg,
           "gain_mv": float(np.unique(af.gain_mv)[0]), "zero_afferents": a.zero_afferents, "overrides": ov,
           "q_start": None if q_start is None else round(q_start, 3),
           "pools_hz_per_mn": {nme: {"n": int(r.size), **{k: hz(cnt[nme][k], r.size, k) for k in bins}}
                               for nme, r in pools},
           "afferent_hz_per_cell": {g: {"n": int(r.size), **{k: hz(acnt[g][k], r.size, k) for k in bins}}
                                    for g, r in groups.items()},
           "inhibitor_hz_per_cell": {tt: {"n": int(r.size), **{k: hz(icnt[tt][k], r.size, k) for k in bins}}
                                     for tt, r in inh.items()},
           "warnings": int(d.warning.number.sum()), "wall_s": round(time.time() - t0)}
    Path(a.out).parent.mkdir(parents=True, exist_ok=True)
    Path(a.out).write_text(json.dumps(out, indent=1))
    print(json.dumps(out))


if __name__ == "__main__":
    main()
