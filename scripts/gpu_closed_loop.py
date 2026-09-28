"""GPU closed loop (docs/GPU.md design, step 2): B organisms whose brains run as
members of one BatchedNetwork on the GPU, bodies (MuJoCo) stepped on the CPU.

Exchange every k steps: each member senses at the window start and its drive is
held for k brain steps (the CPU reference is closed_loop_check.py --hold-k k,
which computes exactly the same thing: sense at s % k == 0, brain step, motor
step each step). Within a window the brain does not see the body, so running k
brain steps first and then replaying the k motor steps is the same computation.

Reports the closed_loop_check metrics per member (active phase --ms, then
--silent-ms with all afferent drive removed), so each member can be compared
with its CPU run. Members differ by their overrides (one JSON list of dicts);
per-neuron brain parameters come from each member's own organism (so class
scales etc. are honoured when they act through the MEMBER_PARAMS arrays).

    .venv-gpu/bin/python scripts/gpu_closed_loop.py members.json --k 10 --ms 1000 --out res.json
"""
import argparse
import json
import sys
import time
from pathlib import Path

import numpy as np

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "src"))

from flyemu import connectome  # noqa: E402
from flyemu.model_data import TEMPLATE_SWITCHES  # noqa: E402

MEMBER_PARAMS = ("release_gain", "input_gain", "spont_mv", "v_rest", "v_th", "v_reset",
                 "tau_m", "t_ref", "tau_s", "adapt_mv", "tau_adapt", "std_u", "std_tau_rec")
from flyemu.organism import Organism  # noqa: E402
from flyemu.profiles import WORKING_PROFILE  # noqa: E402

_build = connectome.build
_cache = {}


def shared_build(reg, min_synapses=1, **kw):
    """One connectome object for all members (read-only after construction);
    each member's registry still records the connectome's requirements."""
    key = (min_synapses, tuple(sorted(kw.items())))
    c = _build(reg, min_synapses=min_synapses, **kw)
    return _cache.setdefault(key, c)


def arrays(net):
    p = net.params
    n = net.conn.n
    b = lambda x: np.broadcast_to(np.asarray(x, np.float32), (n,))  # noqa: E731
    return {"release_gain": b(p.release_gain), "input_gain": b(net.input_gain), "spont_mv": b(net.spont),
            "v_rest": b(net.v_rest), "v_th": b(net.v_th), "v_reset": b(net.v_reset), "tau_m": b(net.tau_m),
            "t_ref": b(net.t_ref), "tau_s": b(p.tau_s), "adapt_mv": b(net.adapt_mv),
            "tau_adapt": b(p.tau_adapt), "std_u": b(net.std_u), "std_tau_rec": b(p.std_tau_rec)}


def worker(conn_pipe, orgs, idx, shm_ext, shm_ras, B, n, nb, kmax, steps, dt):
    """Bodies of members `idx`: sense into the shared ext block; replay motor
    spikes from the shared packed raster; keep the closed_loop_check tallies."""
    from multiprocessing import shared_memory
    se = shared_memory.SharedMemory(name=shm_ext); sr = shared_memory.SharedMemory(name=shm_ras)
    ext = np.ndarray((B, n), np.float32, buffer=se.buf)
    ras = np.ndarray((kmax, nb, B), np.uint8, buffer=sr.buf)
    tal = {b: dict(cnt=np.zeros(n), sil=[], z=[]) for b in idx}
    tonic = {b: (np.broadcast_to(np.asarray(orgs[b].net.params.spont_mv, np.float32), (n,)) -
                 (orgs[b].net.params.tonic_class_mv if orgs[b].net.params.tonic_class_mv is not None else 0)) > 0
             for b in idx}
    while True:
        msg = conn_pipe.recv()
        if msg[0] == "sense":
            s = msg[1]
            for b in idx:
                ext[b] = orgs[b].sense(s, orgs[b].body.observe())
            conn_pipe.send("ok")
        elif msg[0] == "replay":
            s, k = msg[1], msg[2]
            r = np.unpackbits(ras[:k], axis=1, count=n)
            for j in range(k):
                for b in idx:
                    spk = np.flatnonzero(r[j, :, b])
                    o, t = orgs[b], tal[b]
                    if s + j < steps:
                        if (s + j) * dt >= 200:
                            t["cnt"][spk] += 1
                        if (s + j) % 100 == 0:
                            t["z"].append(float(o.body.observe()["body_positions"][0, 2]))
                    else:
                        t["sil"].append(int((~tonic[b][spk]).sum()))
                    o.motor_step(spk)
            conn_pipe.send("ok")
        elif msg[0] == "result":
            conn_pipe.send({b: dict(cnt=tal[b]["cnt"], sil=tal[b]["sil"], z=tal[b]["z"],
                                    warn=int(sum(w.number for w in orgs[b].body.sim.mj_data.warning)))
                            for b in idx})
            return


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("members")
    ap.add_argument("--k", type=int, default=10)
    ap.add_argument("--ms", type=float, default=1000.0)
    ap.add_argument("--silent-ms", type=float, default=300.0)
    ap.add_argument("--template", action="store_true")
    ap.add_argument("--out", default="")
    ap.add_argument("--workers", type=int, default=0, help="body worker processes (0 = in-process)")
    a = ap.parse_args()
    specs = json.loads(Path(a.members).read_text())      # [{"seed": s, "overrides": {...}}, ...]
    connectome.build = shared_build
    orgs = []
    t0 = time.time()
    for sp in specs:
        ov = {"motor_unit:all|force_per_spike": 10.0, **(TEMPLATE_SWITCHES if a.template else {}),
              **sp.get("overrides", {})}
        orgs.append(Organism(policy="minimal", profile=WORKING_PROFILE, min_synapses=5, overrides=ov,
                             seed=sp.get("seed", 0)))
    B, n = len(orgs), orgs[0].conn.n
    ref = orgs[0].net
    mem = {k: np.stack([arrays(o.net)[k] for o in orgs]) for k in MEMBER_PARAMS}
    if a.workers:
        return run_parallel(a, orgs, mem, specs, t0)
    from flyemu.gpu.batched import BatchedNetwork
    bn = BatchedNetwork(ref, B=B, member=mem)
    build_s = time.time() - t0
    dt = orgs[0].timestep_ms
    t = orgs[0].conn.neurons.type.fillna("").to_numpy().astype(str)
    orn = np.char.startswith(t, "ORN_")
    mn = (orgs[0].conn.neurons.superclass.fillna("") == "vnc_motor").to_numpy()
    tonic = [np.broadcast_to(np.asarray(o.net.params.spont_mv, np.float32), (n,)) -
             (o.net.params.tonic_class_mv if o.net.params.tonic_class_mv is not None else 0) > 0 for o in orgs]
    cnt = np.zeros((B, n)); scnt = np.zeros((B, n)); silent = [[] for _ in range(B)]
    z = [[] for _ in range(B)]
    steps, sil_steps = int(a.ms / dt), int(a.silent_ms / dt)
    t1 = time.time()
    s = 0
    while s < steps + sil_steps:
        k = min(a.k, (steps if s < steps else steps + sil_steps) - s)
        if s < steps:
            ext = np.stack([o.sense(s, o.body.observe()) for o in orgs])
        else:
            ext = np.zeros((B, n), np.float32)
        out = bn.run(k, external_mv=ext, record="packed")
        r = np.unpackbits(out["raster"], axis=1, count=n)     # (k, n, B)
        for j in range(k):
            for b, o in enumerate(orgs):
                spk = np.flatnonzero(r[j, :, b])
                if s + j < steps:
                    if (s + j) * dt >= 200:
                        cnt[b, spk] += 1
                    if (s + j) % 100 == 0:
                        z[b].append(float(o.body.observe()["body_positions"][0, 2]))
                else:
                    scnt[b, spk] += 1
                    silent[b].append(int((~tonic[b][spk]).sum()))
                o.motor_step(spk)
        s += k
    run_s = time.time() - t1
    res = []
    dur = (a.ms - 200) / 1000
    for b, o in enumerate(orgs):
        hz = cnt[b] / dur
        last = np.array(silent[b][-int(100 / dt):])
        d = o.body.sim.mj_data
        res.append({"seed": specs[b].get("seed", 0), "overrides": specs[b].get("overrides", {}),
                    "whole_brain_hz": round(float(hz.mean()), 3),
                    "whole_brain_excl_orn_hz": round(float(hz[~orn].mean()), 3),
                    "motor_hz": round(float(hz[mn].mean()), 2),
                    "silent_last100ms_spikes_per_ms": round(float(last.sum() / 100), 2),
                    "thorax_z_mm_final": round(z[b][-1], 3),
                    "mujoco_warnings": int(sum(w.number for w in d.warning))})
    summary = {"B": B, "k": a.k, "build_s": round(build_s), "run_s": round(run_s),
               "wall_s_per_sim_s_per_member": round(run_s / ((a.ms + a.silent_ms) / 1000) / B, 2),
               "members": res}
    print(json.dumps(summary))
    if a.out:
        Path(a.out).write_text(json.dumps(summary))


def run_parallel(a, orgs, mem, specs, t0):
    import multiprocessing as mp
    from multiprocessing import shared_memory
    B, n = len(orgs), orgs[0].conn.n
    nb = (n + 7) // 8
    dt = orgs[0].timestep_ms
    steps, sil_steps = int(a.ms / dt), int(a.silent_ms / dt)
    se = shared_memory.SharedMemory(create=True, size=B * n * 4)
    sr = shared_memory.SharedMemory(create=True, size=a.k * nb * B)
    ext = np.ndarray((B, n), np.float32, buffer=se.buf)
    ras = np.ndarray((a.k, nb, B), np.uint8, buffer=sr.buf)
    ctx = mp.get_context("fork")                      # before JAX initialises
    groups = [list(range(B))[w::a.workers] for w in range(a.workers)]
    pipes, procs = [], []
    for g in groups:
        p1, p2 = ctx.Pipe()
        pr = ctx.Process(target=worker, args=(p2, orgs, g, se.name, sr.name, B, n, nb, a.k, steps, dt))
        pr.start(); pipes.append(p1); procs.append(pr)
    from flyemu.gpu.batched import BatchedNetwork
    bn = BatchedNetwork(orgs[0].net, B=B, member=mem)
    build_s = time.time() - t0
    t1 = time.time()
    s = 0
    while s < steps + sil_steps:
        k = min(a.k, (steps if s < steps else steps + sil_steps) - s)
        if s < steps:
            for p in pipes:
                p.send(("sense", s))
            for p in pipes:
                p.recv()
            e = ext.copy()
        else:
            e = np.zeros((B, n), np.float32)
        out = bn.run(k, external_mv=e, record="packed")
        ras[:k] = out["raster"]
        for p in pipes:
            p.send(("replay", s, k))
        for p in pipes:
            p.recv()
        s += k
    run_s = time.time() - t1
    tal = {}
    for p in pipes:
        p.send(("result",))
        tal.update(p.recv())
    for pr in procs:
        pr.join()
    se.close(); se.unlink(); sr.close(); sr.unlink()
    t = orgs[0].conn.neurons.type.fillna("").to_numpy().astype(str)
    orn = np.char.startswith(t, "ORN_")
    mn = (orgs[0].conn.neurons.superclass.fillna("") == "vnc_motor").to_numpy()
    dur = (a.ms - 200) / 1000
    res = []
    for b in range(B):
        hz = tal[b]["cnt"] / dur
        last = np.array(tal[b]["sil"][-int(100 / dt):])
        res.append({"seed": specs[b].get("seed", 0), "overrides": specs[b].get("overrides", {}),
                    "whole_brain_hz": round(float(hz.mean()), 3),
                    "whole_brain_excl_orn_hz": round(float(hz[~orn].mean()), 3),
                    "motor_hz": round(float(hz[mn].mean()), 2),
                    "silent_last100ms_spikes_per_ms": round(float(last.sum() / 100), 2),
                    "thorax_z_mm_final": round(tal[b]["z"][-1], 3), "mujoco_warnings": tal[b]["warn"]})
    summary = {"B": B, "k": a.k, "workers": a.workers, "build_s": round(build_s), "run_s": round(run_s),
               "wall_s_per_sim_s_per_member": round(run_s / ((a.ms + a.silent_ms) / 1000) / B, 2),
               "members": res}
    print(json.dumps(summary))
    if a.out:
        Path(a.out).write_text(json.dumps(summary))


if __name__ == "__main__":
    main()
