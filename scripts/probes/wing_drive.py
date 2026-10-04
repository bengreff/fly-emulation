"""Session 12 B: what moves the wings in the resting closed loop?

Runs the working-profile organism (as scripts/render_organism.py) and logs, per
wing hinge actuator, the torque the motor path writes and the spikes of the
motor neurons mapped to it; plus the wing angles. Arm `--zero-wings` writes 0
torque on the wing hinges (counterfactual: is the drive the cause?).

    uv run python scripts/probes/wing_drive.py --ms 1500 --seed 12 [--zero-wings]
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
sys.path.insert(0, str(Path(__file__).resolve().parent))
from flyemu import profiles  # noqa: E402
from flyemu.organism import Organism  # noqa: E402


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--ms", type=float, default=1500.0)
    ap.add_argument("--seed", type=int, default=12)
    ap.add_argument("--zero-wings", action="store_true")
    ap.add_argument("--set", action="append", default=[], help="key=value override")
    ap.add_argument("--sheet", action="store_true", help="render a contact sheet (4 times x 2 views)")
    ap.add_argument("--tag", default="", help="arm name (default m9 / zero-wings)")
    ap.add_argument("--out", default=str(REPO / "runs" / "s12" / "wings"))
    a = ap.parse_args()
    ov = {"motor_unit:all|force_per_spike": 10.0}       # as the m9 recording and silence check
    for kv in a.set:
        k, v = kv.split("="); ov[k] = float(v)
    org = Organism(policy="minimal", seed=a.seed, overrides=ov, profile=profiles.WORKING_PROFILE,
                   min_synapses=profiles.WORKING_MIN_SYNAPSES)
    b = org.body
    m, d = b.sim.mj_model, b.sim.mj_data
    wact = [i for i, n in enumerate(b.actuator_names) if "_wing-" in n]
    wname = [b.actuator_names[i].split("/")[-1].replace("-motor", "") for i in wact]
    wj = [mj.mj_name2id(m, mj.mjtObj.mjOBJ_JOINT, f"{b.fly.name}/{n}") for n in wname]
    nm = org.nm
    sel = np.isin(nm.actuator_index, wact)
    rows_mn = nm.mn_index[sel]
    types = org.conn.neurons.type.fillna("?").to_numpy() if hasattr(org.conn, "neurons") else None
    mn_act = nm.actuator_index[sel]
    counts = np.zeros(len(rows_mn), int)
    all_counts = np.zeros(org.conn.n, np.int64)
    torques, angles = [], []
    n_steps = int(round(a.ms / org.timestep_ms))
    shots_at = {int(round(f * n_steps)) - 1 for f in (0.25, 0.5, 0.75, 1.0)} if a.sheet else set()
    frames = []
    for step in range(n_steps):
        obs = b.observe()
        spiked = org.net.step(external_mv=org.sense(step, obs))
        if spiked.size:
            counts += np.isin(rows_mn, spiked)
            np.add.at(all_counts, spiked, 1)
        tq = org.motor_step(spiked) if not a.zero_wings else _zeroed(org, spiked, wact)
        if step in shots_at:
            from wing_rest import shot
            frames.append(((step + 1) * org.timestep_ms, shot(m, d, "")))
        if step % 10 == 0:
            torques.append(np.asarray(tq)[wact].copy())
            angles.append(np.degrees(d.qpos[[m.jnt_qposadr[j] for j in wj]]))
    torques, angles = np.array(torques), np.array(angles)
    rate = counts / (a.ms / 1000.0)
    per = {}
    for r, ai, c in zip(rows_mn, mn_act, rate):
        t = str(types[r]) if types is not None else str(r)
        key = f"{b.actuator_names[ai].split('/')[-1].replace('-motor', '')} <- {t}"
        per.setdefault(key, []).append(round(float(c), 1))
    res = dict(arm=a.tag or ("zero-wings" if a.zero_wings else "m9"), seed=a.seed, ms=a.ms, overrides=ov,
               n_wing_mns=int(sel.sum()),
               mean_torque_uNmm=dict(zip(wname, torques.mean(0).round(4).tolist())),
               mean_torque_last_half=dict(zip(wname, torques[len(torques) // 2:].mean(0).round(4).tolist())),
               angle_end_deg=dict(zip(wname, angles[-1].round(1).tolist())),
               angle_max_abs_deg=dict(zip(wname, np.abs(angles).max(0).round(1).tolist())),
               mn_rates_hz=per,
               inputs_to_active_wing_mns=_attribute(org.conn, all_counts / (a.ms / 1000.0),
                                                    np.unique(rows_mn[rate > 5.0])))
    out = Path(a.out); out.mkdir(parents=True, exist_ok=True)
    tag = res["arm"] + f"_seed{a.seed}"
    (out / f"wing_drive_{tag}.json").write_text(json.dumps(res, indent=1))
    if frames:
        from wing_rest import sheet
        sheet(frames, out / f"wing_drive_{tag}_sheet.png")
    np.savez(out / f"wing_drive_{tag}.npz", torques=torques, angles=angles, names=np.array(wname),
             all_rate_hz=all_counts / (a.ms / 1000.0))
    print(json.dumps(res, indent=1))


def _attribute(conn, rate, targets, top=8):
    """Chemical input to each target, as signed synapse count x presynaptic rate
    (synapse*Hz), grouped by presynaptic superclass and by type. Gap junctions
    and the external (sensory) drive are not included."""
    nrn = conn.neurons
    pre_of = np.repeat(np.arange(conn.n), np.diff(conn.indptr))
    out = {}
    for tgt in targets:
        e = np.flatnonzero(conn.indices == tgt)
        pre = pre_of[e]
        drive = conn.sign[pre] * conn.weight_syn[e] * rate[pre]
        df = nrn.iloc[pre][["superclass", "type"]].fillna("?").assign(drive=drive, syn=conn.weight_syn[e])
        sc = df.groupby("superclass").drive.sum().sort_values(key=np.abs, ascending=False)
        ty = df.groupby("type").drive.sum().sort_values(key=np.abs, ascending=False)
        out[f"{nrn.type.iloc[tgt]} {nrn.instance.iloc[tgt]} ({rate[tgt]:.1f} Hz)"] = dict(
            total_syn_hz=round(float(drive.sum()), 1), n_pre=int(len(pre)), in_syn=int(df.syn.sum()),
            by_superclass={k: round(float(v), 1) for k, v in sc.items() if v},
            top_types={k: round(float(v), 1) for k, v in ty.head(top).items()})
    return out


def _zeroed(org, spiked, wact):
    """motor_step with the wing hinge torques replaced by 0 (counterfactual)."""
    real = org.body.actuate
    def act(t):
        t = np.array(t, dtype=np.float32, copy=True); t[wact] = 0.0
        real(t)
    org.body.actuate = act
    try:
        return org.motor_step(spiked)
    finally:
        org.body.actuate = real


if __name__ == "__main__":
    main()
