"""Whole-CNS equivalence and throughput of the batched JAX simulator (docs/GPU.md).

    # equivalence vs lif.Network, brain only, noise off (writes runs/gpu_equiv/<stim>.json)
    python scripts/gpu_bench.py equiv --ms 500 --stim sugar
    python scripts/gpu_bench.py equiv --ms 500 --stim broad
    # throughput: wall seconds per simulated second for each batch size
    python scripts/gpu_bench.py bench --batch 1,8,32 --ms 1000
    # CPU reference throughput (lif.Network alone, same stimulus)
    python scripts/gpu_bench.py cpu --ms 200

On backhouse use the GPU venv: ~/fly-emulation/.venv-gpu/bin/python.
"""
import argparse
import json
import sys
import time
from dataclasses import replace
from pathlib import Path

import numpy as np

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "src"))

from flyemu import lif  # noqa: E402
from flyemu.gpu.equivalence import build_brain, compare, cpu_run, unpack  # noqa: E402

DT = 0.1


def stimulus(conn, stim: str, T: int, seed: int = 0):
    """Deterministic kick schedule + constant external drive.

    sugar: LB3b/LB3c sugar GRNs, 100 Hz Poisson kicks (the sugar->MN9 assay input).
    broad: sugar + 3% of all cells at 20 Hz Poisson kicks + 4 mV onto every ORN.
    """
    t = conn.neurons.type.fillna("")
    idx = np.flatnonzero(t.isin(["LB3b", "LB3c"]).to_numpy())
    rates = np.full(idx.size, 100.0)
    ext = np.zeros(conn.n, np.float32)
    rng = np.random.default_rng(seed)
    if stim == "broad":
        extra = np.setdiff1d(rng.choice(conn.n, int(0.03 * conn.n), replace=False), idx)
        idx = np.concatenate([idx, extra])
        rates = np.concatenate([rates, np.full(extra.size, 20.0)])
        ext[t.str.startswith("ORN_").to_numpy()] = 4.0
    mask = rng.random((T, idx.size)) < rates * DT / 1000.0
    return idx, mask, ext


def class_gains(conn, seed: int, spread: float = 0.2):
    """A per-cell-type random gain in [1-spread, 1+spread]: a stand-in for a class-level
    search variant (release, input and tonic drive scaled per type)."""
    rng = np.random.default_rng(seed)
    codes, _ = conn.neurons.type.fillna("untyped").factorize()
    k = codes.max() + 1
    return [rng.uniform(1 - spread, 1 + spread, k)[codes].astype(np.float32) for _ in range(3)]


def cmd_equiv(a):
    from flyemu.gpu.batched import BatchedNetwork
    reg, conn, params, kick_mv = build_brain({"cell_type:all|background_noise": 0.0})
    assert params.noise_mv == 0
    T = int(round(a.ms / DT))
    idx, mask, ext = stimulus(conn, a.stim, T)
    kicks = (idx, mask, kick_mv)
    n = conn.n
    fr, fi, fs = class_gains(conn, 7)
    rel = np.stack([lif._arr(params.release_gain, n), lif._arr(params.release_gain, n) * fr])
    inp = np.stack([lif._arr(params.input_gain, n), lif._arr(params.input_gain, n) * fi])
    spont = np.stack([lif._arr(params.spont_mv, n), lif._arr(params.spont_mv, n) * fs])
    t0 = time.time()
    g = BatchedNetwork(lif.Network(conn, params, DT), B=2,
                       member={"release_gain": rel, "input_gain": inp, "spont_mv": spont})
    r = g.run(T, external_mv=ext, kicks=kicks, record="packed")
    gpu_s = time.time() - t0
    v1 = np.asarray(g.state["v"])
    g.reset()                      # determinism: the same run again, bitwise
    g.run(T, external_mv=ext, kicks=kicks)
    out_det = bool(np.array_equal(v1, np.asarray(g.state["v"])))
    import os
    xf = os.environ.get("XLA_FLAGS", "")
    out = {"xla_flags": xf, "gpu_rerun_bitwise_identical_v": out_det, "stim": a.stim, "ms": a.ms, "n": n, "edges_gpu": g.n_edges, "gpu_wall_s": round(gpu_s, 1),
           "backend": __import__("jax").default_backend(), "cfg": g.cfg._asdict()}
    for b, name in ((0, "reference"), (1, "class_gains")):
        pb = params if b == 0 else replace(params, release_gain=rel[1], input_gain=inp[1],
                                           spont_mv=spont[1])
        ref, cpu_s = cpu_run(lif.Network(conn, pb, DT), T, ext, kicks)
        res = compare(ref, unpack(r["raster"], n, b), n, DT)
        res["cpu_wall_s"] = round(cpu_s, 1)
        # where does the first divergence sit, and how many steps are affected
        out[name] = res
        print(name, json.dumps(res), flush=True)
    dest = REPO / "runs" / "gpu_equiv"
    dest.mkdir(parents=True, exist_ok=True)
    tag = "_det" if "deterministic" in xf else ""
    (dest / f"{a.stim}_{int(a.ms)}ms{tag}.json").write_text(json.dumps(out, indent=1, default=str))


def cmd_bench(a):
    import jax
    from flyemu.gpu.batched import BatchedNetwork
    reg, conn, params, kick_mv = build_brain({"cell_type:all|background_noise": 0.0})
    idx, _, ext = stimulus(conn, a.stim, 1)
    t = conn.neurons.type.fillna("")
    rate = np.where(t.isin(["LB3b", "LB3c"]).to_numpy()[idx], 100.0, 20.0)   # as stimulus()
    rows = []
    for B in [int(x) for x in a.batch.split(",")]:
        base = {k: lif._arr(getattr(params, k), conn.n)
                for k in ("release_gain", "input_gain", "spont_mv")}
        var = [class_gains(conn, 100 + m) for m in range(B)]   # distinct members
        g = BatchedNetwork(lif.Network(conn, params, DT), B=B, member={
            k: np.stack([base[k] * v[j] for v in var]) for j, k in enumerate(base)},
            tiers=None if a.tiers is None else json.loads(a.tiers))
        chunk = int(a.chunk_ms / DT)
        t0 = time.time()
        g.run(chunk, external_mv=ext, kicks=(idx, rate, kick_mv))          # compile + first chunk
        jax.block_until_ready(g.state["v"])
        compile_s = time.time() - t0
        n_chunks = max(1, int(round(a.ms / a.chunk_ms)))
        t0 = time.time()
        for _ in range(n_chunks):
            r = g.run(chunk, external_mv=ext, kicks=(idx, rate, kick_mv))
        jax.block_until_ready(g.state["v"])
        wall = time.time() - t0
        sim_s = n_chunks * a.chunk_ms / 1000
        row = {"B": B, "wall_per_sim_s": round(wall / sim_s, 3),
               "wall_per_member_sim_s": round(wall / sim_s / B, 4),
               "ms_per_step": round(wall / (n_chunks * chunk) * 1e3, 4),
               "compile_plus_first_chunk_s": round(compile_s, 1),
               "mean_spikes_per_step": float(r["n_spikes"].mean()),
               "backend": jax.default_backend(), "edges": g.n_edges,
               "stim": a.stim, "tiers": g.cfg.tiers}
        print(json.dumps(row), flush=True)
        rows.append(row)
        del g
    dest = REPO / "runs" / "gpu_equiv"
    dest.mkdir(parents=True, exist_ok=True)
    tag = f"{a.stim}_{a.tag}"
    (dest / f"bench_{jax.default_backend()}_{tag}.json").write_text(json.dumps(rows, indent=1))


def cmd_cpu(a):
    reg, conn, params, kick_mv = build_brain({"cell_type:all|background_noise": 0.0})
    T = int(round(a.ms / DT))
    idx, mask, ext = stimulus(conn, a.stim, T)
    net = lif.Network(conn, params, DT)
    ref, s = cpu_run(net, T, ext, (idx, mask, kick_mv))
    print(json.dumps({"cpu_wall_per_sim_s": round(s / (a.ms / 1000), 2), "ms": a.ms, "stim": a.stim,
                      "spikes": int(sum(x.size for x in ref))}))


def main():
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    e = sub.add_parser("equiv")
    e.add_argument("--ms", type=float, default=500.0)
    e.add_argument("--stim", default="sugar", choices=["sugar", "broad"])
    b = sub.add_parser("bench")
    b.add_argument("--batch", default="1,8,32")
    b.add_argument("--ms", type=float, default=1000.0)
    b.add_argument("--chunk-ms", type=float, default=250.0)
    b.add_argument("--stim", default="sugar", choices=["sugar", "broad"])
    b.add_argument("--tiers", default=None,
                   help="JSON list of [active_cells, edges] event tiers; [] = dense every step")
    b.add_argument("--tag", default="default")
    c = sub.add_parser("cpu")
    c.add_argument("--ms", type=float, default=200.0)
    c.add_argument("--stim", default="sugar", choices=["sugar", "broad"])
    a = ap.parse_args()
    {"equiv": cmd_equiv, "bench": cmd_bench, "cpu": cmd_cpu}[a.cmd](a)


if __name__ == "__main__":
    main()
