"""Session 12 B (non-leg torque per spike): which motor neurons drive the non-leg
joints, how often they fire in the closed loop, and what one spike does.

Per actuator group (head, proboscis, antenna, abdomen, wing, haltere): number of
mapped motor neurons, their torque per spike, their mean rate over the run, the
mean and peak |torque| at the actuator, the fraction of time at the actuator's
force limit, the joint's stiffness (so one spike's static deflection can be read),
and per actuator the mean joint angle and the time spent within 1 deg of a joint limit.

    uv run python scripts/probes/nonleg_motor_census.py --seed 12 --ms 600 --out runs/s12/nonleg/census_s12.json
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import mujoco as mj
import numpy as np

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "src"))
from flyemu.organism import Organism  # noqa: E402
from flyemu.profiles import WORKING_PROFILE  # noqa: E402

GATE = ["motor_unit:all|force_per_spike=10", "motor_map:wing|roles=1", "sense:mechano|assign_by_nerve=2",
        "muscle:leg|midhind_source=1", "jump:ttm|peak_torque=90", "joint:leg|damping_source=1",
        "jump:ttm|exclude_from_hill=1", "contact:floor|noslip_iterations=0"]
GROUPS = (("head", "c_thorax-c_head"), ("proboscis", ("rostrum", "haustellum", "labrum")),
          ("antenna", "antenna"), ("abdomen", "abdomen"), ("wing", "_wing-"), ("haltere", "haltere"))


def group_of(name: str) -> str:
    for g, keys in GROUPS:
        keys = (keys,) if isinstance(keys, str) else keys
        if any(k in name for k in keys):
            return g
    return "leg"


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--seed", type=int, default=12)
    ap.add_argument("--ms", type=float, default=600.0)
    ap.add_argument("--set", action="append", default=[])
    ap.add_argument("--out", default=str(REPO / "runs/s12/nonleg/census.json"))
    ap.add_argument("--sheet", action="store_true", help="contact sheet at half and full run (side, front)")
    a = ap.parse_args()
    ov = {k: float(v) for k, v in (s.split("=") for s in GATE + a.set)}
    org = Organism(policy="minimal", profile=WORKING_PROFILE, min_synapses=5, overrides=ov, seed=a.seed)
    m, d = org.body.sim.mj_model, org.body.sim.mj_data
    nm = org.nm
    names = [mj.mj_id2name(m, mj.mjtObj.mjOBJ_ACTUATOR, i) or "" for i in range(m.nu)]
    motor_names = [n for n in names if n.endswith("-motor")]
    assert len(motor_names) == nm.n_actuators, (len(motor_names), nm.n_actuators)
    grp = np.array([group_of(n) for n in motor_names])
    jstiff = np.array([float(m.jnt_stiffness[m.actuator_trnid[names.index(n), 0]]) for n in motor_names])
    flim = np.array([float(m.actuator_forcerange[names.index(n), 1]) for n in motor_names])
    jid = np.array([m.actuator_trnid[names.index(n), 0] for n in motor_names])
    qadr, jlo, jhi = m.jnt_qposadr[jid], m.jnt_range[jid, 0], m.jnt_range[jid, 1]
    q_sum = np.zeros(nm.n_actuators); at_jlim = np.zeros(nm.n_actuators)
    types = org.conn.neurons.type.fillna("untyped").to_numpy().astype(str)[nm.mn_index]
    steps = int(a.ms / org.timestep_ms)
    cnt = np.zeros(len(nm.mn_index))
    tq_abs = np.zeros(nm.n_actuators); tq_max = np.zeros(nm.n_actuators); at_lim = np.zeros(nm.n_actuators)
    k0 = int(200 / org.timestep_ms)
    shots_at = {steps // 2 - 1, steps - 1} if a.sheet else set()
    frames = []
    for s in range(steps):
        obs = org.body.observe()
        sp = org.net.step(external_mv=org.sense(s, obs))
        tq = org.motor_step(sp)
        if s >= k0:
            cnt += np.isin(nm.mn_index, sp)
            ta = np.abs(np.asarray(tq, float))
            tq_abs += ta; tq_max = np.maximum(tq_max, ta); at_lim += ta >= flim - 1e-6
            q = d.qpos[qadr]; q_sum += q
            at_jlim += (q <= jlo + np.radians(1.0)) | (q >= jhi - np.radians(1.0))
        if s in shots_at:
            sys.path.insert(0, str(Path(__file__).resolve().parent))
            from wing_rest import shot
            frames.append(((s + 1) * org.timestep_ms, shot(m, d, "")))
    n_rec = steps - k0
    hz = cnt / (n_rec * org.timestep_ms / 1000.0)
    act_grp = grp[nm.actuator_index]
    out = {"seed": a.seed, "ms": a.ms, "profile": WORKING_PROFILE, "overrides": ov,
           "activation_tau_ms": float(nm.tau_act_ms), "groups": {}}
    for g, _ in GROUPS:
        sel = act_grp == g
        acts = np.flatnonzero(grp == g)
        out["groups"][g] = {
            "n_actuators": int(len(acts)), "n_mns": int(sel.sum()),
            "n_mns_driven_actuators": int(len(np.unique(nm.actuator_index[sel]))),
            "fps_uNmm": sorted(set(round(float(x), 3) for x in nm.force_per_spike[sel])),
            "mn_types": sorted(set(types[sel])),
            "mn_rate_hz_mean": round(float(hz[sel].mean()), 3) if sel.any() else None,
            "mn_rate_hz_max": round(float(hz[sel].max()), 3) if sel.any() else None,
            "torque_abs_mean_uNmm": round(float(tq_abs[acts].mean() / n_rec), 4),
            "torque_abs_peak_uNmm": round(float(tq_max[acts].max()), 3),
            "frac_time_at_force_limit": round(float(at_lim[acts].max() / n_rec), 4),
            "force_limit_uNmm": sorted(set(flim[acts].round(3).tolist())),
            "joint_stiffness_uNmm_per_rad": sorted(set(jstiff[acts].round(4).tolist())),
            "per_actuator": {motor_names[i].split("/")[-1]: {
                "n_mns": int((nm.actuator_index == i).sum()),
                "rate_hz_sum": round(float(hz[nm.actuator_index == i].sum()), 2),
                "torque_abs_mean": round(float(tq_abs[i] / n_rec), 4),
                "angle_mean_deg": round(float(np.degrees(q_sum[i] / n_rec)), 1),
                "range_deg": [round(float(np.degrees(jlo[i])), 1), round(float(np.degrees(jhi[i])), 1)],
                "frac_time_within_1deg_of_limit": round(float(at_jlim[i] / n_rec), 3)} for i in acts},
        }
    Path(a.out).parent.mkdir(parents=True, exist_ok=True)
    Path(a.out).write_text(json.dumps(out, indent=1))
    if frames:
        from wing_rest import sheet
        sheet(frames, Path(a.out).with_suffix(".png"))
    print(json.dumps({g: {k: v for k, v in r.items() if k != "per_actuator"} for g, r in out["groups"].items()}, indent=1))


if __name__ == "__main__":
    main()
