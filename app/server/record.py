"""Run the closed-loop organism and write a flyemu-rec/1 recording.

    .venv/bin/python app/server/record.py --duration-ms 2000 --seed 12 \
        --set 'motor_unit:all|force_per_spike=10' --out runs/app/m9-s12-2000ms
    .venv/bin/python app/server/record.py --protocol my_protocol.json --out runs/app/x

Uses only the model's public loop (Organism.sense -> Network.step ->
Organism.motor_step), the same loop as scripts/record_organism.py, and records
more of it: every neuron's spikes with their exact step, body poses, joint
torque, tarsal contact, the ommatidia values the network received, membrane
potential of watched cells and neuromodulator levels. Bounded by --duration-ms.
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import platform
import subprocess
import sys
import time
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(Path(__file__).resolve().parent))

import mujoco as mj  # noqa: E402

from flyemu import lif, profiles  # noqa: E402
from flyemu.organism import Organism  # noqa: E402
import heldout  # noqa: E402
import live  # noqa: E402
import protocol as proto  # noqa: E402
from recfmt import RecWriter, spikes_to_csr  # noqa: E402
from caveats import generate  # noqa: E402

EYE_SCALE = 255.0   # readouts are stored as uint8 = round(value * EYE_SCALE), clipped


def git_state() -> dict:
    def run(*a):
        try:
            return subprocess.run(["git", *a], cwd=ROOT, capture_output=True, text=True,
                                  timeout=10).stdout.strip()
        except Exception:
            return ""
    commit = run("rev-parse", "HEAD")
    if not commit and os.environ.get("FLYAPP_COMMIT"):
        # a copy without .git (backhouse gets `git archive` of a commit): the launcher declares it
        return {"commit": os.environ["FLYAPP_COMMIT"], "branch": os.environ.get("FLYAPP_BRANCH", ""),
                "dirty_files": None, "source": "declared by the launcher (git archive copy, no .git)"}
    return {"commit": commit, "branch": run("rev-parse", "--abbrev-ref", "HEAD"),
            "dirty_files": len([x for x in run("status", "--porcelain").splitlines() if x.strip()])}


def as_str(col) -> np.ndarray:
    return np.array(["unknown" if (x is None or x != x) else str(x) for x in col], dtype=object)


def nt_source(neurons, nt_used, nt_em) -> np.ndarray:
    """Where each row's transmitter comes from: 0 the EM classifier call, 1 the
    dataset's consensus call (differs from the classifier), 2 the project's
    hemilineage rule (data/derived/nt_hemilineage_fill.csv)."""
    import pandas as pd
    from flyemu.connectome import CACHE
    cons = neurons.bodyId.map(pd.read_parquet(CACHE / "male_cns_extra.parquet",
                                              columns=["bodyId", "consensusNt"])
                              .set_index("bodyId").consensusNt)
    cons = as_str(cons)
    return np.where(nt_used == nt_em, 0, np.where(nt_used == cons, 1, 2)).astype(np.uint8)


def motor_limits(m, names) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Per commanded actuator: the range MuJoCo enforces (control range if
    ctrl-limited, else force range if force-limited, else none)."""
    lo, hi = np.full(len(names), -np.inf, np.float32), np.full(len(names), np.inf, np.float32)
    lim = np.zeros(len(names), bool)
    for i, nm in enumerate(names):
        a = mj.mj_name2id(m, mj.mjtObj.mjOBJ_ACTUATOR, nm)
        if a < 0:
            continue
        if m.actuator_ctrllimited[a]:
            lo[i], hi[i], lim[i] = *m.actuator_ctrlrange[a], True
        elif m.actuator_forcelimited[a]:
            lo[i], hi[i], lim[i] = *m.actuator_forcerange[a], True
    return lo, hi, lim


def profile_status(profile: str | None, overrides: dict) -> str:
    if profile == profiles.WORKING_PROFILE and not overrides:
        return "adopted (working profile)"
    if profile == profiles.WORKING_PROFILE:
        return "adopted profile with overrides: custom, not validated"
    return {"m4": "regression reference", "m10p": "candidate, not adopted",
            "m10q": "candidate, not adopted"}.get(profile or "", "custom, not validated")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--protocol", help="flyemu-protocol/1 JSON; command-line values override its config")
    ap.add_argument("--duration-ms", type=float)
    ap.add_argument("--seed", type=int)
    ap.add_argument("--profile")
    ap.add_argument("--min-synapses", type=int)
    ap.add_argument("--set", action="append", default=[], help="'entity|property=value'")
    ap.add_argument("--watch-type", action="append", default=[],
                    help="record membrane potential of these cell types (repeatable)")
    ap.add_argument("--chunk-ms", type=float, default=250.0)
    ap.add_argument("--web-hz", type=float, default=200.0)
    ap.add_argument("--v-hz", type=float, default=1000.0)
    ap.add_argument("--spend-heldout", action="append", default=[],
                    help="held-out item id (or 'seed') this run may spend; see app/server/heldout.py")
    ap.add_argument("--live", type=Path, metavar="COMMANDS",
                    help="live session: read pause/resume/stop/stim commands from this JSON-lines "
                         "file as the run goes (app/server/live.py); duration_ms is then the maximum")
    ap.add_argument("--poll-ms", type=float, default=10.0, help="live: read commands every this much "
                    "simulated time")
    ap.add_argument("--out", required=True)
    args = ap.parse_args()

    pr = json.loads(Path(args.protocol).read_text()) if args.protocol else {}
    cfg = dict(pr.get("config", {}))
    cfg.setdefault("scan", "male-cns:v1.0")
    cfg.setdefault("body", "flybody")
    for k, v in (("profile", args.profile), ("seed", args.seed),
                 ("min_synapses", args.min_synapses)):
        if v is not None:
            cfg[k] = v
    cfg.setdefault("profile", profiles.WORKING_PROFILE)
    cfg.setdefault("seed", 0)
    cfg.setdefault("min_synapses", profiles.WORKING_MIN_SYNAPSES)
    overrides = dict(cfg.get("overrides", {}))
    for item in args.set:
        k, _, v = item.partition("=")
        overrides[k] = float(v)
    cfg["overrides"] = overrides
    cfg["start"] = "rest"
    duration_ms = args.duration_ms or pr.get("duration_ms", 1000.0)
    pr = {"format": "flyemu-protocol/1", **pr, "config": cfg, "duration_ms": duration_ms}
    if args.watch_type:
        pr.setdefault("record", {})["watch"] = {"type": args.watch_type}
    if cfg["body"] != "flybody":
        raise SystemExit("M1 records flybody only: Organism does not expose the body choice yet")

    out = Path(args.out)
    if out.exists() and any(out.iterdir()):
        raise SystemExit(f"{out} exists and is not empty")
    t_start = time.time()
    org = Organism(policy="minimal", seed=cfg["seed"], overrides=overrides,
                   profile=None if cfg["profile"] in ("none", "") else cfg["profile"],
                   min_synapses=cfg["min_synapses"])
    build_s = time.time() - t_start
    net, conn, body = org.net, org.conn, org.body
    m, d = body.sim.mj_model, body.sim.mj_data
    n = conn.n
    neurons = conn.neurons
    ts = org.timestep_ms

    pr = proto.resolve(pr, neurons, ts)
    pr["heldout"] = heldout.check(pr, neurons)
    heldout.enforce(pr["heldout"], args.spend_heldout, ROOT / "runs" / "app" / "heldout_spent.jsonl",
                    pr.get("title") or out.name)
    pr["heldout"]["spent_here"] = args.spend_heldout
    res = pr["resolved"]
    watch = np.asarray(res["watch"], np.int64)
    if watch.size == 0:   # default: every motor neuron, the cells that move the body
        watch = np.flatnonzero(neurons.superclass.to_numpy() == "vnc_motor")
    watch = watch[:2000]
    for g in res["genotype"]:
        net.silence(np.asarray(g["rows"], np.int64))
    stim = proto.Stimulator(res, n, cfg["seed"], org.kick_mv)
    brain_only = res["preparation"] == "brain_only"

    # The eyes: tap the readout call so the recording holds exactly the values the
    # photoreceptors were driven by, without rendering the eyes a second time.
    eye_frames: list[tuple[int, np.ndarray]] = []
    cur_step = [0]
    if org.vis is not None:
        sim = body.sim
        orig = sim.get_ommatidia_readouts

        def tapped(name, _orig=orig):
            r = _orig(name)
            eye_frames.append((cur_step[0], np.clip(np.rint(np.asarray(r) * EYE_SCALE), 0, 255)
                               .astype(np.uint8)))
            return r
        sim.get_ommatidia_readouts = tapped

    steps_per_ms = max(1, int(round(1.0 / ts)))
    web_stride = max(1, int(round(1000.0 / args.web_hz / ts)))
    v_stride = max(1, int(round(1000.0 / args.v_hz / ts)))
    chunk_steps = int(round(args.chunk_ms / ts))
    n_steps = int(round(duration_ms / ts))
    body_names = [mj.mj_id2name(m, mj.mjtObj.mjOBJ_BODY, i) for i in range(m.nbody)]
    radius = np.zeros(m.nbody, dtype=np.float32)
    for g in range(m.ngeom):
        b = int(m.geom_bodyid[g])
        radius[b] = max(radius[b], float(m.geom_rbound[g]))
    mn_rows = np.flatnonzero(neurons.superclass.to_numpy() == "vnc_motor")
    mn_mapped = np.isin(mn_rows, org.nm.mn_index)
    p = net.params

    def per_row(x, dtype=np.float32):
        return np.broadcast_to(np.asarray(x, dtype=dtype), (n,)).copy()

    graded = per_row(p.graded if p.graded is not None else 0, np.uint8)
    nt_em = as_str(neurons.get("predictedNt_em", neurons.predictedNt))
    nt_used = as_str(neurons.predictedNt)
    static = {
        "row_bodyid": neurons.bodyId.to_numpy().astype(np.int64),
        "tau_m": per_row(p.tau_m), "v_rest": per_row(p.v_rest), "v_th": per_row(p.v_th),
        "v_reset": per_row(p.v_reset), "t_ref": per_row(p.t_ref),
        "spont_mv": per_row(p.spont_mv), "release_gain": per_row(p.release_gain),
        "input_gain": per_row(p.input_gain), "graded": graded,
        "nt_source": nt_source(neurons, nt_used, nt_em),
        "mn_rows": mn_rows.astype(np.int32), "mn_mapped": mn_mapped.astype(np.uint8),
        "watch_rows": watch.astype(np.int32),
        "body_parent": np.asarray(m.body_parentid, np.int32), "body_radius": radius,
    }
    nt_names = sorted(set(nt_used))
    static["nt_used"] = np.array([nt_names.index(x) for x in nt_used], np.uint8)

    manifest = {
        "run_id": out.name,
        "title": pr.get("title"),
        "created": dt.datetime.now().astimezone().isoformat(timespec="seconds"),
        "protocol": pr,
        "config": cfg,
        "timestep_ms": ts,
        "chunk_ms": args.chunk_ms,
        "n_rows": int(n),
        "n_edges": int(conn.n_edges),
        "n_synapses": int(conn.weight_syn.sum()),
        "profile_status": profile_status(cfg["profile"], overrides),
        "preparation": {"coupling": res["preparation"], "kick_rng": res["kick_rng"],
                        "desc": "open loop, brain only: no senses, no motor output, body not stepped "
                                "(as scripts/assay_pathways.py)" if brain_only else
                                "closed loop: senses -> network -> muscles -> body"},
        "names": {
            "bodies": body_names,
            "actuators": [a.removeprefix("nmf/").removesuffix("-motor") for a in body.actuator_names],
            "contacts": list(body.contact_names),
            "modulators": list(lif.MODULATORS),
            "nt": nt_names,
            "nt_source": ["EM classifier", "dataset consensus", "hemilineage rule (project)"],
        },
        "streams": {
            "spikes": {"bin_ms": 1.0, "desc": "every spike of every model row; CSR by 1 ms bin, "
                       "sub = step within the bin", "rows": "model rows (static.row_bodyid)"},
            "xpos": {"rate_hz": 1000.0 / (web_stride * ts), "units": "mm (flygym model units)", "desc": "world position per MuJoCo body"},
            "xquat": {"rate_hz": 1000.0 / (web_stride * ts), "units": "w,x,y,z", "desc": "world orientation per body"},
            "qpos": {"rate_hz": 1000.0 / (web_stride * ts), "desc": "MuJoCo generalised coordinates"},
            "torque": {"rate_hz": 1000.0 / (web_stride * ts), "units": "actuator units (N m)",
                       "desc": "actuator command after the motor model"},
            "contact": {"rate_hz": 1000.0 / (web_stride * ts), "units": "N", "desc": "contact force magnitude per contact segment"},
            "mod_level": {"rate_hz": 1000.0 / (web_stride * ts), "desc": "neuromodulator pool levels (dimensionless)"},
            "v": {"rate_hz": 1000.0 / (v_stride * ts), "units": "mV", "rows": "static.watch_rows",
                  "desc": "membrane potential of watched rows"},
            "eye": {"rate_hz": None, "scale": EYE_SCALE, "desc": "ommatidia readouts (2 eyes, 721, "
                    "yellow/pale), uint8 = value * scale; eye_step = the step it was sampled at"},
        },
        "limits": dict(zip(("lo", "hi", "limited"),
                           (x.tolist() for x in motor_limits(m, body.actuator_names)))),
        "provenance": {
            "git": git_state(), "command": " ".join(sys.argv), "python": platform.python_version(),
            "host": platform.node(), "dataset": "male-cns:v1.0", "build_s": round(build_s, 1),
            "mujoco": mj.__version__,
        },
    }
    out.mkdir(parents=True, exist_ok=True)
    w = RecWriter(out, manifest, static)

    buf = {k: [] for k in ("xpos", "xquat", "qpos", "torque", "contact", "mod_level", "v")}
    sp_steps, sp_rows = [], []
    k_steps, k_rows = [], []
    n_kicks = 0
    t_run = time.time()
    total = 0
    clip_hits = np.zeros(len(body.actuator_names), np.int64)
    n_torque = 0
    lo, hi, limited = motor_limits(m, body.actuator_names)
    chunk0 = 0
    n_eye = 0
    if brain_only:                       # the body is never stepped: one observation, no torque
        obs = body.observe()
        torque = np.zeros(len(body.actuator_names), np.float32)
    def flush(s1: int) -> None:
        nonlocal buf, sp_steps, sp_rows, k_steps, k_rows, chunk0, n_eye
        s0 = chunk0
        nb = int(np.ceil((s1 - s0) / steps_per_ms))
        st = np.concatenate(sp_steps) if sp_steps else np.zeros(0, np.int64)
        rw = np.concatenate(sp_rows) if sp_rows else np.zeros(0, np.int64)
        arrays = spikes_to_csr(st, rw, s0, nb, steps_per_ms)
        for k, v in buf.items():
            arrays[k] = np.stack(v) if v else np.zeros((0,), np.float32)
        ef = [(s, f) for s, f in eye_frames if s0 <= s < s1]
        n_eye += len(ef)
        if ef:
            arrays["eye_step"] = np.array([s for s, _ in ef], np.uint32)
            arrays["eye"] = np.stack([f for _, f in ef])
        # Frame times are explicit so chunks need not be aligned to the strides.
        if k_steps:
            arrays["kick_step"] = np.concatenate(k_steps)
            arrays["kick_row"] = np.concatenate(k_rows)
        arrays["frame_step"] = np.arange(s0 + (-s0) % web_stride, s1, web_stride, dtype=np.uint32)
        arrays["v_step"] = np.arange(s0 + (-s0) % v_stride, s1, v_stride, dtype=np.uint32)
        w.add_chunk(s0 * ts, s1 * ts, arrays)
        eye_frames[:] = [(s, f) for s, f in eye_frames if s >= s1]
        buf = {k: [] for k in buf}
        sp_steps, sp_rows = [], []
        k_steps, k_rows = [], []
        chunk0 = s1
        el = time.time() - t_run
        print(f"  {s1 * ts:8.1f} ms  spikes {total:,}  wall {el:6.0f} s "
              f"({el / (s1 * ts / 1000):.0f} s per sim s)", flush=True)

    session = live.Session(args.live, w, pr, stim, neurons, ts) if args.live else None
    poll_steps = max(1, int(round(args.poll_ms / ts)))
    step = 0
    while step < n_steps:
        if session is not None and step % poll_steps == 0 and not session.poll(step):
            if step > chunk0:
                flush(step)
            break
        cur_step[0] = step
        if brain_only:
            drive = stim.drive(step)
        else:
            stim.world(step, org)        # world events change what the receptors can sense
            obs = body.observe()
            drive = org.sense(step, obs)
            extra = stim.drive(step)
            if extra is not None:
                drive = extra if drive is None else drive + extra
        kick = stim.kick(step, ts)
        if kick is not None:
            k_steps.append(np.full(kick[0].size, step, np.uint32))
            k_rows.append(kick[0].astype(np.uint32))
            n_kicks += int(kick[0].size)
        spiked = net.step(external_mv=drive, kick=kick)
        if not brain_only:
            torque = org.motor_step(spiked)
        if spiked.size:
            sp_steps.append(np.full(spiked.size, step, np.int64))
            sp_rows.append(np.asarray(spiked, np.int64))
            total += int(spiked.size)
        if step % web_stride == 0:
            tq = np.asarray(torque, np.float32)
            buf["xpos"].append(np.array(d.xpos, np.float32))
            buf["xquat"].append(np.array(d.xquat, np.float32))
            buf["qpos"].append(np.array(d.qpos, np.float32))
            buf["torque"].append(tq.copy())
            buf["contact"].append(np.linalg.norm(obs["contact_forces"], axis=-1).astype(np.float32))
            buf["mod_level"].append(np.array(getattr(net, "mod_level", np.zeros(3)), np.float32))
            clip_hits += (limited & ((tq <= lo * 0.999) | (tq >= hi * 0.999))).astype(np.int64)
            n_torque += 1
        if step % v_stride == 0:
            buf["v"].append(np.asarray(net.v, np.float32)[watch])

        step += 1
        if step % chunk_steps == 0 or step == n_steps:
            flush(step)

    wall = time.time() - t_run
    if step < n_steps:                   # a live session stopped early: the run is this long
        duration_ms = step * ts
        pr["duration_ms"] = duration_ms
    if session is not None:
        wall -= session.paused_s         # compute cost excludes time spent paused
        session.state.update(state="stopped" if session.stopped else "finished",
                             end_ms=round(step * ts, 3), paused_s=round(session.paused_s, 1))
    try:
        org.write_inventory(out / "inventory.csv")
    except Exception as exc:          # the inventory is evidence, but not worth losing the run
        print(f"inventory not written: {exc}")
    sim_s = max(duration_ms, ts) / 1000.0
    summary = {"spikes_total": total, "mean_rate_hz": total / n / sim_s,
               "wall_s": round(wall, 1), "wall_s_per_sim_s": round(wall / sim_s, 1),
               "torque_clip_fraction": (clip_hits / max(n_torque, 1)).round(4).tolist(),
               "n_eye_frames": n_eye, "kicks_total": n_kicks}
    w.manifest["protocol"]["resolved"]["world_applied"] = [stim.applied.get(k) for k in range(len(stim.worlds))]
    w.manifest["summary"] = summary
    w.finish("complete", caveats=generate(w.manifest, static, org))
    print(json.dumps({"out": str(out), **{k: v for k, v in summary.items() if k != "torque_clip_fraction"}}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
