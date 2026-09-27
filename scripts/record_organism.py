"""Record a closed-loop run to disk for replay.

Replay needs no simulation: MuJoCo reconstructs every body pose from `qpos`
alone, so a full-rate recording is 133 floats per timestep. A 3 s run at 0.1 ms
is 30,000 frames, about 16 MB as float32 - small enough to store every step
rather than subsample.

Two outputs:

    recording.npz   full rate, for scripts/replay_mujoco.py
    replay_data.js  downsampled, for the browser visualiser

The browser file carries body poses in the world frame plus the neural and
motor signals that produced them, so the brain and the body can be watched
together. That coupling is the thing worth looking at; the body alone is just
a falling object.
"""
from __future__ import annotations

import argparse
import base64
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

import mujoco as mj
import numpy as np

from flyemu.body import Body
from flyemu import profiles
from flyemu.organism import Organism
from flyemu.provenance import RunRecord
from flyemu import vision, extrasenses, olfaction, neuromuscular, sensory

REPO = Path(__file__).resolve().parents[1]


def b64(a: np.ndarray, dtype) -> str:
    return base64.b64encode(np.ascontiguousarray(a, dtype=dtype).tobytes()).decode()


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--duration-ms", type=float, default=3000.0)
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--set", action="append", default=[])
    ap.add_argument("--web-hz", type=float, default=200.0,
                    help="pose sample rate for the browser visualiser")
    ap.add_argument("--tag", default="replay")
    ap.add_argument("--profile", default=profiles.WORKING_PROFILE,
                    help="parameter profile (default: the working model); 'none' for bare defaults")
    ap.add_argument("--min-synapses", type=int, default=profiles.WORKING_MIN_SYNAPSES)
    args = ap.parse_args()

    overrides = {}
    for item in args.set:
        k, _, v = item.partition("=")
        overrides[k] = float(v)

    run_id = f"organism-record-{args.duration_ms:g}ms-{args.tag}"
    out = REPO / "runs" / run_id
    rec = RunRecord(run_id, out, description="closed-loop recording for replay")
    rec.add_config({**vars(args), "overrides": overrides})
    for k, v in overrides.items():
        rec.declare_scaffold(f"override: {k} = {v}")
    rec.declare_scaffold(
        "initial condition: every neuron exactly at rest with no synaptic "
        "history, body at the model's neutral pose 2 mm above the ground. The "
        "opening fall and the first tens of ms of activity are transients of "
        "that choice, not behaviour"
    )

    org = Organism(policy="minimal", seed=args.seed, overrides=overrides,
                   profile=None if args.profile in ("none", "") else args.profile,
                   min_synapses=args.min_synapses)
    # Rebuild the body with a tracking camera so the same recording can be
    # rendered to video without re-running.
    org.body = Body(model=org.body.model,
                    timestep=org.timestep_ms / 1000.0, with_camera=True)
    org.nm = neuromuscular.build(
        org.reg, org.conn, org.body.actuator_names,
        fly_name=org.body.fly.name, adhesion_names=org.body.adhesion_names,
        model=org.body.model,
    )
    org.aff = sensory.build(org.reg, org.conn, org.body, org.net.params)
    if org.vis is not None:
        vision.install_connectome_mask(org.reg, org.body.sim)
    org.chem = olfaction.build(org.reg, org.conn, org.body, org.net.params,
                               timestep_ms=org.timestep_ms, seed=args.seed)
    org.extra = extrasenses.build(org.reg, org.conn, org.body)

    m, d = org.body.sim.mj_model, org.body.sim.mj_data
    n_steps = int(round(args.duration_ms / org.timestep_ms))
    web_stride = max(1, int(round(1000.0 / args.web_hz / org.timestep_ms)))
    ms_stride = max(1, int(round(1.0 / org.timestep_ms)))   # 1 ms bins

    print(f"network: {org.conn.n:,} neurons, {org.conn.n_edges:,} edges")
    print(f"recording {args.duration_ms:g} ms at {org.timestep_ms} ms "
          f"({n_steps:,} steps); web every {web_stride} steps")

    qpos = np.zeros((n_steps, m.nq), dtype=np.float32)
    web_xpos, web_xquat, web_torque, web_contact = [], [], [], []
    mn_rows = org.conn.neurons.superclass.to_numpy() == "vnc_motor"
    mn_idx = np.flatnonzero(mn_rows)
    mn_lookup = {int(v): i for i, v in enumerate(mn_idx)}
    mn_meta = org.conn.neurons.iloc[mn_idx]
    motor_spikes: list[tuple[int, int]] = []
    pop_rate: list[float] = []
    ms_spikes = 0

    for step in range(n_steps):
        obs = org.body.observe()
        spiked = org.net.step(external_mv=org.sense(step, obs))
        torque = org.motor_step(spiked)

        qpos[step] = d.qpos
        ms_spikes += int(spiked.size)
        for s in spiked:
            hit = mn_lookup.get(int(s))
            if hit is not None:
                motor_spikes.append((step // ms_stride, hit))

        if step % ms_stride == 0:
            # Spikes in this bin over the bin's duration in seconds, per neuron.
            window_s = ms_stride * org.timestep_ms / 1000.0
            pop_rate.append(ms_spikes / org.conn.n / window_s)
            ms_spikes = 0

        if step % web_stride == 0:
            web_xpos.append(np.array(d.xpos, dtype=np.float32).copy())
            web_xquat.append(np.array(d.xquat, dtype=np.float32).copy())
            web_torque.append(torque.astype(np.float32).copy())
            web_contact.append(
                np.linalg.norm(obs["contact_forces"], axis=-1).astype(np.float32)
            )

        if step % 5000 == 0:
            print(f"  {step * org.timestep_ms:7.1f} ms", flush=True)

    # --- full rate, for the MuJoCo replay app -------------------------------
    np.savez_compressed(
        out / "recording.npz",
        qpos=qpos, timestep_ms=org.timestep_ms,
        actuator_names=np.array(org.body.actuator_names),
    )

    # --- downsampled, for the browser ---------------------------------------
    body_names = [mj.mj_id2name(m, mj.mjtObj.mjOBJ_BODY, i) for i in range(m.nbody)]
    parent = np.array(m.body_parentid, dtype=np.int32)
    # A radius per body, from the bounding radius of the geoms attached to it.
    radius = np.zeros(m.nbody, dtype=np.float32)
    for g in range(m.ngeom):
        b = int(m.geom_bodyid[g])
        radius[b] = max(radius[b], float(m.geom_rbound[g]))

    xpos = np.stack(web_xpos)
    xquat = np.stack(web_xquat)
    spikes = np.array(motor_spikes, dtype=np.int32) if motor_spikes else np.zeros((0, 2), np.int32)
    payload = {
        "meta": {
            "run_id": run_id,
            "duration_ms": args.duration_ms,
            "timestep_ms": org.timestep_ms,
            "web_hz": 1000.0 / (web_stride * org.timestep_ms),
            "n_frames": int(xpos.shape[0]),
            "n_bodies": int(m.nbody),
            "n_actuators": int(m.nu),
            "n_neurons": int(org.conn.n),
            "n_edges": int(org.conn.n_edges),
            "n_synapses": int(org.conn.weight_syn.sum()),
            "n_motor_neurons": int(mn_idx.size),
            "n_motor_mapped": int(len(org.nm.mn_index)),
            "n_motor_unmapped": int(len(org.nm.unmapped)),
            "n_afferents": int(org.aff.rows.size),
            "overrides": overrides,
            "total_spikes": int(org.net.spike_count),
            "mean_hz": org.net.spike_count / org.conn.n / (args.duration_ms / 1000.0),
        },
        "body_names": body_names,
        "body_parent": parent.tolist(),
        "body_radius": radius.tolist(),
        "actuator_names": [a.removeprefix("nmf/").removesuffix("-motor")
                           for a in org.body.actuator_names],
        # Which motor neurons actually reach a muscle. Over half do not, and
        # the raster is only honest if it shows which rows drive nothing.
        "motor_mapped": np.isin(mn_idx, org.nm.mn_index).astype(int).tolist(),
        "motor_subclass": mn_meta.subclass.fillna("?").tolist(),
        "motor_type": mn_meta.type.fillna("unnamed").tolist(),
        "contact_names": list(org.body.contact_names),
        "xpos": b64(xpos, np.float32),
        "xquat": b64(xquat, np.float32),
        "torque": b64(np.stack(web_torque), np.float32),
        "contact": b64(np.stack(web_contact), np.float32),
        "pop_rate": b64(np.array(pop_rate, np.float32), np.float32),
        "motor_spikes": b64(spikes, np.int32),
        "n_spike_bins": int(np.ceil(n_steps / ms_stride)),
    }
    js = out / "replay_data.js"
    js.write_text("window.REPLAY = " + json.dumps(payload) + ";\n")

    rec.result("n_steps", n_steps)
    rec.result("web_frames", int(xpos.shape[0]))
    rec.result("total_spikes", int(org.net.spike_count))
    rec.result("motor_spikes_recorded", int(spikes.shape[0]))
    rec.result("recording_mb", round((out / "recording.npz").stat().st_size / 1e6, 2))
    rec.result("replay_js_mb", round(js.stat().st_size / 1e6, 2))
    path = rec.finish()

    print(f"\nrecording.npz   {(out / 'recording.npz').stat().st_size / 1e6:.1f} MB")
    print(f"replay_data.js  {js.stat().st_size / 1e6:.1f} MB "
          f"({xpos.shape[0]} frames)")
    print(f"motor spikes    {spikes.shape[0]:,}")
    print(f"run record      {path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
